from typing import Dict, Any
import random
import time

class LLMAdapter:
    """Interfaz mínima para un LLM: generate(prompt) -> dict(result, confidence)."""
    def generate(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError

class MockLLM(LLMAdapter):
    def generate(self, prompt: str) -> Dict[str, Any]:
        # Simula respuesta y confianza; reemplazar por llamada real (OpenAI, Azure, etc.)
        time.sleep(0.1)
        confidence = round(random.uniform(0.4, 0.98), 2)
        return {"result": f"RESPUESTA_SIMULADA: {prompt[:120]}", "confidence": confidence}
