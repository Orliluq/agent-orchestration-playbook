# Agent Orchestration Playbook

Repositorio de ejemplo que demuestra cómo diseñar y orquestar agentes de IA centrados en el problema, no en el LLM. Incluye tres ejemplos listos para ejecutar: ingestión de facturas, triage de soporte y revisión de código.

## Filosofía

> Un agente de IA no nace del LLM: nace del problema y del diseño del comportamiento. El LLM es una pieza poderosa, pero la orquestación —decidir cuándo actuar, cuándo parar, qué sistemas tocar y qué aprender— es lo que convierte una automatización frágil en un agente robusto y adaptable. Sin orquestación no hay agentes; solo cadenas que se rompen con el tiempo.

## Patrones de Orquestación Implementados

### 1. **Orquestación Secuencial con Supervisor**
- **Uso**: Procesos críticos que requieren validación y reintentos
- **Ejemplo**: `examples/invoice_ingest/run.py`
- **Características**: 
  - Supervisor con umbrales de confianza
  - Reintentos con backoff exponencial
  - Registro de experiencia para mejora continua

### 2. **Orquestación Concurrente**
- **Uso**: Procesos que pueden paralelizarse para mejorar rendimiento
- **Ejemplo**: `examples/invoice_ingest/parallel_orchestrator.py`
- **Características**:
  - Ejecución paralela de tareas independientes
  - Manejo de errores por tarea
  - Agregación de resultados

### 3. **Orquestación Multi-Agente**
- **Uso**: Sistemas complejos que requieren especialización
- **Ejemplo**: `examples/support_triage/` (próximamente)
- **Características**:
  - Agentes especializados por dominio
  - Coordinación centralizada
  - Comunicación entre agentes

## Arquitectura

```
agent-orchestration-playbook/
├── core/                          # Componentes fundamentales
│   ├── llm_adapter.py           # Abstracción de LLM
│   ├── orchestrator.py           # Lógica de orquestación
│   └── supervisor.py             # Supervisión y decisiones
├── core/tools/                    # Herramientas desacopladas
│   ├── storage.py                # Almacenamiento persistente
│   ├── metrics.py                # Métricas y observabilidad
│   └── notifier.py               # Sistema de notificaciones
├── examples/                      # Ejemplos prácticos
│   ├── invoice_ingest/           # Procesamiento de facturas
│   ├── support_triage/           # Triage de soporte técnico
│   └── code_review/              # Revisión automática de código
├── tests/                         # Pruebas unitarias
├── docker/                        # Configuración Docker
└── requirements.txt              # Dependencias
```

## Componentes Clave

### Core Components

- **LLMAdapter**: Abstracción para diferentes proveedores de LLM
- **Orchestrator**: Ejecuta pipelines de tareas con manejo de errores
- **Supervisor**: Toma decisiones basadas en confianza y experiencia

### Tools

- **Storage**: Almacenamiento desacoplado (archivo/memoria)
- **Metrics**: Colección de métricas con agregaciones
- **Notifier**: Sistema de notificaciones multi-canal

## Configuración Rápida

### 1. Entorno Virtual

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Windows)
.venv\Scripts\activate

# Activar (Unix/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar Ejemplos

```bash
# Procesamiento de facturas
python examples/invoice_ingest/run.py

# Orquestación paralela
python examples/invoice_ingest/parallel_orchestrator.py

# Triage de soporte (próximamente)
python examples/support_triage/run.py
```

### 3. Docker

```bash
# Construir imagen
docker build -t agent-orchestration -f docker/Dockerfile .

# Ejecutar contenedor
docker run -p 8000:8000 agent-orchestration
```

## Ejemplo: Procesamiento de Facturas

```python
from core.llm_adapter import MockLLM
from core.orchestrator import Orchestrator
from core.supervisor import Supervisor
from core.tools.storage import FileStorage
from core.tools.metrics import MetricsCollector

# Configurar componentes
llm = MockLLM()
storage = FileStorage()
metrics = MetricsCollector()
supervisor = Supervisor(threshold_accept=0.8)
orchestrator = Orchestrator(llm, storage, metrics)

# Procesar factura
invoice_text = "FACTURA #123: Cliente ACME..."
result = orchestrator.run_pipeline(invoice_text)

# Decisión del supervisor
decision = supervisor.decide(result)
if decision == "accept":
    print("Factura procesada exitosamente")
```

## Métricas y Observabilidad

El sistema incluye métricas integradas para:

- **Tareas**: Iniciadas, completadas, fallidas
- **LLM**: Llamadas, tokens, duración
- **Salud**: Estado general del agente
- **Experiencia**: Decisiones del supervisor

Acceso a métricas:

```python
# Exportar métricas
metrics = collector.get_all_metrics()

# Formato Prometheus
prometheus_exporter = PrometheusMetrics(collector)
prometheus_text = prometheus_exporter.export_prometheus()
```

## Patrones de Diseño

### 1. Desacoplamiento
- Cada componente tiene una responsabilidad única
- Interfaces claras entre capas
- Inyección de dependencias

### 2. Resiliencia
- Reintentos con backoff
- Circuit breakers
- Manejo de errores por dominio

### 3. Observabilidad
- Logging estructurado
- Métricas detalladas
- Trazabilidad de decisiones

### 4. Escalabilidad
- Diseño async/await
- Procesamiento paralelo
- Almacenamiento configurable

## Extensión y Personalización

### Agregar Nuevo LLM Provider

```python
from core.llm_adapter import LLMAdapter

class CustomLLM(LLMAdapter):
    def generate(self, prompt: str) -> Dict[str, Any]:
        # Implementación personalizada
        return {"result": "...", "confidence": 0.9}
```

### Agregar Nuevo Canal de Notificación

```python
from core.tools.notifier import NotificationChannel

class SlackNotifier(NotificationChannel):
    async def send(self, notification):
        # Enviar a Slack
        pass
```

### Personalizar Supervisor

```python
class CustomSupervisor(Supervisor):
    def decide(self, output):
        # Lógica personalizada de decisión
        return super().decide(output)
```

## Testing

```bash
# Ejecutar todas las pruebas
pytest

# Pruebas con cobertura
pytest --cov=core

# Pruebas específicas
pytest tests/test_orchestrator.py
```

## Contribución

1. Fork del repositorio
2. Crear feature branch: `git checkout -b feature/nuevo-patron`
3. Commit changes: `git commit -am 'Agregar nuevo patrón'`
4. Push: `git push origin feature/nuevo-patron`
5. Pull Request

## Licencia

MIT License - ver archivo LICENSE para detalles.

## Próximos Pasos

- [ ] Ejemplo completo de triage de soporte
- [ ] Integración con LLMs reales (OpenAI, Claude, etc.)
- [ ] Dashboard de métricas en tiempo real
- [ ] Testing de carga y estrés
- [ ] Documentación de patrones avanzados

---

**Recuerda**: La orquestación es la capa crítica de producción. Un buen diseño de orquestación convierte un prototipo frágil en un sistema robusto y adaptable.
