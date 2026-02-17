"""
Métricas y monitoreo para agentes de IA.
Proporciona observabilidad sin acoplamiento a la lógica de negocio.
"""
import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class MetricPoint:
    """Punto de dato métrico con timestamp"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Colector de métricas en memoria con agregaciones básicas"""
    
    def __init__(self, max_points: int = 10000):
        self.max_points = max_points
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._lock = threading.RLock()
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Incrementar un contador"""
        with self._lock:
            self._counters[name] += value
            self._metrics[name].append(MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            ))
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Establecer un gauge (valor actual)"""
        with self._lock:
            self._gauges[name] = value
            self._metrics[name].append(MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            ))
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Registrar un valor para histograma"""
        with self._lock:
            self._metrics[name].append(MetricPoint(
                timestamp=time.time(),
                value=value,
                tags=tags or {}
            ))
    
    def get_counter(self, name: str) -> float:
        """Obtener valor actual de un contador"""
        with self._lock:
            return self._counters.get(name, 0.0)
    
    def get_gauge(self, name: str) -> float:
        """Obtener valor actual de un gauge"""
        with self._lock:
            return self._gauges.get(name, 0.0)
    
    def get_stats(self, name: str, window_seconds: int = 300) -> Dict[str, float]:
        """Obtener estadísticas para una métrica en una ventana de tiempo"""
        with self._lock:
            if name not in self._metrics:
                return {}
            
            cutoff_time = time.time() - window_seconds
            points = [
                p for p in self._metrics[name] 
                if p.timestamp >= cutoff_time
            ]
            
            if not points:
                return {}
            
            values = [p.value for p in points]
            return {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "rate": len(values) / window_seconds
            }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Exportar todas las métricas"""
        with self._lock:
            result = {}
            
            # Contadores
            for name, value in self._counters.items():
                result[f"counter.{name}"] = {
                    "type": "counter",
                    "value": value,
                    "stats": self.get_stats(name)
                }
            
            # Gauges
            for name, value in self._gauges.items():
                result[f"gauge.{name}"] = {
                    "type": "gauge", 
                    "value": value,
                    "stats": self.get_stats(name)
                }
            
            # Histogramas
            histogram_names = set(self._metrics.keys()) - set(self._counters.keys()) - set(self._gauges.keys())
            for name in histogram_names:
                result[f"histogram.{name}"] = {
                    "type": "histogram",
                    "stats": self.get_stats(name)
                }
            
            return result

class PrometheusMetrics:
    """Adaptador para formato Prometheus"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def export_prometheus(self) -> str:
        """Exportar métricas en formato Prometheus"""
        metrics = self.collector.get_all_metrics()
        lines = []
        
        for metric_name, metric_data in metrics.items():
            # Metadata
            metric_type = metric_data["type"]
            lines.append(f"# TYPE {metric_name} {metric_type}")
            
            # Value
            if "value" in metric_data:
                lines.append(f"{metric_name} {metric_data['value']}")
            
            # Stats como métricas adicionales
            if "stats" in metric_data:
                for stat_name, stat_value in metric_data["stats"].items():
                    stat_metric = f"{metric_name}_{stat_name}"
                    lines.append(f"{stat_metric} {stat_value}")
        
        return "\n".join(lines)

class AgentMetrics:
    """Métricas específicas para agentes de IA"""
    
    def __init__(self, collector: MetricsCollector, agent_name: str):
        self.collector = collector
        self.agent_name = agent_name
        self.base_tags = {"agent": agent_name}
    
    def task_started(self, task_type: str):
        """Marcar inicio de tarea"""
        self.collector.increment(
            f"{self.agent_name}.tasks.started",
            tags={**self.base_tags, "task_type": task_type}
        )
    
    def task_completed(self, task_type: str, duration: float, confidence: float):
        """Marcar completado de tarea"""
        self.collector.increment(
            f"{self.agent_name}.tasks.completed",
            tags={**self.base_tags, "task_type": task_type}
        )
        self.collector.histogram(
            f"{self.agent_name}.tasks.duration",
            duration,
            tags={**self.base_tags, "task_type": task_type}
        )
        self.collector.histogram(
            f"{self.agent_name}.tasks.confidence",
            confidence,
            tags={**self.base_tags, "task_type": task_type}
        )
    
    def task_failed(self, task_type: str, error_type: str):
        """Marcar fallo de tarea"""
        self.collector.increment(
            f"{self.agent_name}.tasks.failed",
            tags={**self.base_tags, "task_type": task_type, "error_type": error_type}
        )
    
    def llm_call(self, provider: str, tokens: int, duration: float):
        """Registrar llamada a LLM"""
        self.collector.increment(
            f"{self.agent_name}.llm.calls",
            tags={**self.base_tags, "provider": provider}
        )
        self.collector.histogram(
            f"{self.agent_name}.llm.tokens",
            tokens,
            tags={**self.base_tags, "provider": provider}
        )
        self.collector.histogram(
            f"{self.agent_name}.llm.duration",
            duration,
            tags={**self.base_tags, "provider": provider}
        )
    
    def set_health_status(self, status: str):
        """Establecer estado de salud del agente"""
        status_value = 1.0 if status == "healthy" else 0.0
        self.collector.gauge(
            f"{self.agent_name}.health",
            status_value,
            tags={**self.base_tags, "status": status}
        )
