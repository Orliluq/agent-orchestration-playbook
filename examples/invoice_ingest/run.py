#!/usr/bin/env python3
"""
Ejemplo completo de ingestión de facturas usando patrones de orquestación.
Demuestra: 
- Orquestación secuencial con supervisor
- Manejo de errores y reintentos
- Métricas y logging estructurado
- Desacoplamiento de componentes
"""
import asyncio
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Agregar el path del proyecto para imports relativos
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.llm_adapter import MockLLM
from core.orchestrator import Orchestrator, ToolError
from core.supervisor import Supervisor
from core.tools.storage import FileStorage, MemoryStorage
from core.tools.metrics import MetricsCollector, AgentMetrics
from core.tools.notifier import NotificationManager, ConsoleNotifier, NotificationLevel, notify_info, notify_error, notify_warning

class InvoiceProcessor:
    """Procesador de facturas con orquestación robusta"""
    
    def __init__(self, storage_type: str = "memory"):
        # Componentes desacoplados
        self.llm = MockLLM()
        self.storage = FileStorage() if storage_type == "file" else MemoryStorage()
        self.metrics = MetricsCollector()
        self.agent_metrics = AgentMetrics(self.metrics, "invoice_processor")
        self.supervisor = Supervisor(
            max_retries=3,
            threshold_accept=0.8,
            threshold_escalate=0.4,
            experience_log="invoice_experience.log"
        )
        self.orchestrator = Orchestrator(self.llm, self.storage, self.metrics)
        
        # Configurar notificaciones
        self.notifications = NotificationManager()
        self.notifications.add_channel(ConsoleNotifier(colored=True))
        self.notifications.set_min_level(NotificationLevel.INFO)
    
    async def process_invoice(self, invoice_text: str, invoice_id: str = None) -> Dict[str, Any]:
        """Procesar una factura con orquestación completa"""
        invoice_id = invoice_id or f"INV_{hash(invoice_text) % 10000:04d}"
        
        await notify_info(
            title="Procesando Factura",
            message=f"Iniciando procesamiento de {invoice_id}",
            source="InvoiceProcessor",
            metadata={"invoice_id": invoice_id, "text_length": len(invoice_text)}
        )
        
        self.agent_metrics.task_started("invoice_processing")
        
        try:
            # Orquestación con supervisor
            result = await self._process_with_supervision(invoice_text, invoice_id)
            
            # Registrar éxito
            self.agent_metrics.task_completed(
                "invoice_processing", 
                result.get("duration", 0),
                result.get("confidence", 0)
            )
            
            await notify_info(
                title="Factura Procesada",
                message=f"Factura {invoice_id} procesada exitosamente",
                source="InvoiceProcessor",
                metadata={
                    "invoice_id": invoice_id,
                    "confidence": result.get("confidence"),
                    "extracted_fields": len(result.get("extracted", "{}"))
                }
            )
            
            return result
            
        except Exception as e:
            # Registrar fallo
            self.agent_metrics.task_failed("invoice_processing", type(e).__name__)
            
            await notify_error(
                title="Error en Procesamiento",
                message=f"Fallo procesando factura {invoice_id}: {str(e)}",
                source="InvoiceProcessor",
                metadata={"invoice_id": invoice_id, "error_type": type(e).__name__}
            )
            
            raise
    
    async def _process_with_supervision(self, invoice_text: str, invoice_id: str) -> Dict[str, Any]:
        """Procesamiento con supervisión y reintentos"""
        context = {"invoice_id": invoice_id, "text": invoice_text}
        retry_count = 0
        
        while retry_count <= self.supervisor.max_retries:
            try:
                # Ejecutar orquestación principal
                result = self.orchestrator.run_pipeline(invoice_text)
                
                # Decisión del supervisor
                decision = self.supervisor.decide(result)
                
                if decision == "accept":
                    # Registrar experiencia positiva
                    self.supervisor.record(context, {"result": result, "decision": "accept"})
                    return result
                
                elif decision == "retry" and retry_count < self.supervisor.max_retries:
                    retry_count += 1
                    await notify_warning(
                        title="Reintento",
                        message=f"Reintentando procesamiento de {invoice_id} (intento {retry_count})",
                        source="Supervisor",
                        metadata={"invoice_id": invoice_id, "retry_count": retry_count, "confidence": result.get("confidence")}
                    )
                    continue
                
                else:
                    # Escalar o fallar
                    error_msg = f"Confidence too low: {result.get('confidence')}"
                    self.supervisor.record(context, {"result": result, "decision": "escalate", "error": error_msg})
                    raise ToolError(error_msg)
                    
            except ToolError as e:
                if retry_count >= self.supervisor.max_retries:
                    self.supervisor.record(context, {"error": str(e), "decision": "failed"})
                    raise
                retry_count += 1
                await asyncio.sleep(0.5 * retry_count)  # Backoff exponencial simple
        
        raise ToolError("Max retries exceeded")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del procesador"""
        return {
            "agent_metrics": self.agent_metrics.collector.get_all_metrics(),
            "experience_log": await self._load_experience_log()
        }
    
    async def _load_experience_log(self) -> List[Dict[str, Any]]:
        """Cargar log de experiencia del supervisor"""
        try:
            if os.path.exists(self.supervisor.experience_log):
                async with asyncio.aiofiles.open(self.supervisor.experience_log, 'r') as f:
                    content = await f.read()
                    return [json.loads(line) for line in content.strip().split('\n') if line]
        except Exception:
            pass
        return []

async def demo_invoice_processing():
    """Demostración del procesamiento de facturas"""
    
    # Facturas de ejemplo
    sample_invoices = [
        """
        FACTURA No. 2024-001
        Cliente: Empresa ABC
        RFC: ABC123456789
        
        Concepto: Servicios de consultoría
        Cantidad: 10 horas
        Precio unitario: $150.00
        Subtotal: $1,500.00
        IVA (16%): $240.00
        Total: $1,740.00
        
        Fecha de emisión: 15/01/2024
        Vencimiento: 15/02/2024
        """,
        
        """
        INVOICE #2024-002
        Bill To: Tech Solutions Inc.
        Tax ID: TECH987654321
        
        Item: Software License
        Quantity: 1
        Unit Price: $2,500.00
        Subtotal: $2,500.00
        Tax (8%): $200.00
        Total Due: $2,700.00
        
        Issue Date: 01/15/2024
        Due Date: 02/15/2024
        Payment Terms: NET 30
        """
    ]
    
    print("🚀 Iniciando demostración de procesamiento de facturas\n")
    
    # Crear procesador
    processor = InvoiceProcessor(storage_type="memory")
    
    # Procesar facturas
    results = []
    for i, invoice_text in enumerate(sample_invoices, 1):
        print(f"📄 Procesando factura {i}...")
        try:
            result = await processor.process_invoice(invoice_text, f"DEMO_{i}")
            results.append(result)
            print(f"✅ Factura {i} procesada (confianza: {result.get('confidence', 0):.2f})\n")
        except Exception as e:
            print(f"❌ Error procesando factura {i}: {e}\n")
    
    # Mostrar métricas
    print("📊 Métricas del procesamiento:")
    metrics = await processor.get_metrics()
    
    # Métricas del agente
    agent_metrics = metrics["agent_metrics"]
    for metric_name, metric_data in agent_metrics.items():
        if metric_name.startswith("counter.invoice_processor"):
            print(f"  • {metric_name}: {metric_data.get('value', 0)}")
    
    # Estadísticas de experiencia
    experience = metrics["experience_log"]
    if experience:
        print(f"\n📚 Experiencia acumulada: {len(experience)} decisiones")
        accept_count = sum(1 for exp in experience if exp.get("outcome", {}).get("decision") == "accept")
        print(f"  • Aceptaciones: {accept_count}")
        print(f"  • Reintentos: {len(experience) - accept_count}")
    
    return results

if __name__ == "__main__":
    # Ejecutar demostración
    try:
        results = asyncio.run(demo_invoice_processing())
        print(f"\n🎉 Demostración completada. {len(results)} facturas procesadas.")
    except KeyboardInterrupt:
        print("\n⏹️ Demostración interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error en demostración: {e}")
        sys.exit(1)
