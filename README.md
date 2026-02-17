# Agent Orchestration Playbook

Repositorio de ejemplo que demuestra cómo diseñar y orquestar agentes de IA centrados en el problema, no en el LLM. Incluye tres ejemplos listos para ejecutar: ingestión de facturas, triage de soporte y revisión de código.

## Filosofía

> Un agente de IA no nace del LLM: nace del problema y del diseño del comportamiento. El LLM es una pieza poderosa, pero la orquestación —decidir cuándo actuar, cuándo parar, qué sistemas tocar y qué aprender— es lo que convierte una automatización frágil en un agente robusto y adaptable. **Sin orquestación no hay agentes; solo cadenas que se rompen con el tiempo.**

> **La orquestación es la capa crítica que convierte automatización frágil en agentes robustos y adaptables.**

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

## Ejemplos de Agentes Listos

### 📄 **invoice_ingest/**: Ingestión de Facturas
**Flujo completo**: extracción de campos, validación y persistencia.

- **run.py**: Combina pipeline + supervisor + almacenamiento local (JSON)
- **Características**:
  - Extracción de campos estructurados desde facturas
  - Validación de confianza con umbrales configurables
  - Reintentos automáticos con backoff
  - Persistencia en JSON local
  - Métricas de procesamiento y errores

### 🎫 **support_triage/**: Triage de Soporte
**Clasificación inteligente**: decide si responder automáticamente o escalar a humano.

- **Características**:
  - Clasificación de tickets por prioridad y complejidad
  - Decisión automática vs escalado humano
  - Métricas de SLA y tiempo de respuesta
  - Integración con sistemas de tickets
  - Alertas para casos críticos

### 🔍 **code_review/**: Revisión de Código
**Orquestación de LLM**: genera comentarios, ejecuta pruebas y decide sobre PRs.

- **Características**:
  - Análisis automático de código
  - Generación de comentarios constructivos
  - Ejecución de pruebas unitarias
  - Decisión de abrir PR o pedir revisión humana
  - Métricas de calidad de código

## Componentes Clave

### Core Components

- **LLMAdapter**: Abstracción para diferentes proveedores de LLM
- **Orchestrator**: Ejecuta pipelines de tareas con manejo de errores
- **Supervisor**: Toma decisiones basadas en confianza y experiencia

### Tools

- **Storage**: Almacenamiento desacoplado (archivo/memoria)
- **Metrics**: Colección de métricas con agregaciones
- **Notifier**: Sistema de notificaciones multi-canal

## Métricas y Observabilidad

El sistema incluye métricas integradas para:

- **Tareas**: Iniciadas, completadas, fallidas
- **LLM**: Llamadas, tokens, duración
- **Salud**: Estado general del agente
- **Experiencia**: Decisiones del supervisor

**Métricas mínimas implementadas**:
- Latencia por llamada LLM
- Tasa de aceptación/escalado
- Costo estimado por request
- Errores por tipo

Implementado con `tools/metrics.py` (adaptadores para Prometheus o logs JSON).

## Pruebas y Calidad

### Tests Unitarios
- **tests/test_orchestrator.py**: Cubre flujos felices, reintentos y escalado
- **Framework**: pytest con mocks para LLM
- **Cobertura**: Validación de todos los componentes críticos

### CI/CD Pipeline
- **.github/workflows/ci.yml**: Ejecuta lint, tests y build de Docker en cada PR
- **Validaciones**: 
  - Linting (black, flake8, mypy)
  - Tests unitarios con múltiples versiones de Python
  - Security scanning (bandit, safety)
  - Docker build y publicación

## Buenas Prácticas y Extensiones

### Separación de Responsabilidades
- **LLM Adapter**: Comunicación con proveedores LLM
- **Orchestrator**: Flujo de ejecución
- **Supervisor**: Políticas de decisión
- **Tools**: Sistemas externos desacoplados

### Control de Costos
- **Cache** de prompts/respuestas
- **Batching** y límites de concurrencia
- **Métricas** de consumo y costos

### Observabilidad
- **Traces** distribuidos (OpenTelemetry)
- **Logs** estructurados con correlación
- **Dashboards** en tiempo real

### Feedback Loop
- **Almacenamiento** de experiencias para reentrenamiento
- **Dataset** de fallos para análisis
- **Exportación** de métricas para mejora continua

### Seguridad
- **Validación** estricta de outputs antes de tocar sistemas críticos
- **Políticas** de permisos para acciones automatizadas
- **Sanitización** de datos sensibles

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

# Revisión de código (próximamente)
python examples/code_review/run.py
```

### 3. Docker

```bash
# Construir imagen
docker build -t agent-orchestration -f docker/Dockerfile .

# Ejecutar con compose
docker-compose -f docker/docker-compose.yml up -d
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

## Siguientes Pasos y Personalización

### Conectar tu LLM
Implementa adaptadores reales en `core/llm_adapter.py`:
```python
class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key, model="gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str) -> Dict[str, Any]:
        # Implementar con rate limits y manejo de costos
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "result": response.choices[0].message.content,
            "confidence": self._calculate_confidence(response),
            "tokens": response.usage.total_tokens,
            "cost": self._calculate_cost(response.usage)
        }
```

### Integrar Sistemas Reales
Reemplaza `tools/storage.py` por adaptadores a:
- **S3** para almacenamiento en la nube
- **PostgreSQL/MySQL** para persistencia estructurada
- **Redis** para caché y colas
- **Sistemas internos** vía APIs REST

### Despliegue Producción
```yaml
# Kubernetes con Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-orchestration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-orchestration
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
  - type: Resource
    resource:
      name: memory
```

### Colas para Tareas Largas
```python
# Redis Streams para desacoplar tareas largas
import redis.asyncio as redis

class QueueOrchestrator:
    def __init__(self):
        self.redis = redis.Redis()
    
    async def submit_long_task(self, task_data):
        # Enviar a cola Redis
        await self.redis.xadd('long_tasks', task_data)
    
    async def process_results(self):
        # Procesar resultados asíncronos
        while True:
            events = await self.redis.xread(['long_tasks'], block=1000)
            for event in events:
                await self.handle_result(event)
```

## Testing

```bash
# Ejecutar todas las pruebas
pytest

# Pruebas con cobertura
pytest --cov=core --cov-report=html

# Pruebas específicas
pytest tests/test_orchestrator.py -v

# Tests de integración
pytest tests/ -k "integration"
```

## Contribución

1. Fork del repositorio
2. Crear feature branch: `git checkout -b feature/nuevo-patron`
3. Commit changes: `git commit -am 'Agregar nuevo patrón'`
4. Push: `git push origin feature/nuevo-patron`
5. Pull Request con tests y documentación

## Licencia

MIT License - ver archivo LICENSE para detalles.

## Próximos Pasos

- [ ] Ejemplo completo de triage de soporte con clasificación
- [ ] Ejemplo de code review con análisis estático
- [ ] Integración con LLMs reales (OpenAI, Claude, Azure)
- [ ] Dashboard de métricas en tiempo real con Grafana
- [ ] Testing de carga y estrés con Locust
- [ ] Documentación de patrones avanzados y casos de uso
- [ ] Implementación de circuit breakers y rate limiting

---

**Recuerda**: La orquestación es la capa crítica de producción. Un buen diseño de orquestación convierte un prototipo frágil en un sistema robusto y adaptable. **La orquestación es la capa crítica que convierte automatización frágil en agentes robustos y adaptables.**
