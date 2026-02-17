from typing import Dict, Any
import time

class ToolError(Exception):
    pass

class Orchestrator:
    def __init__(self, llm, storage, metrics):
        self.llm = llm
        self.storage = storage
        self.metrics = metrics

    async def run_pipeline(self, document: str) -> Dict[str, Any]:
        start = time.time()
        # Paso 1: resumen
        summary_resp = self.llm.generate(f"Resume el documento: {document}")
        # Paso 2: extracción
        extract_resp = self.llm.generate(f"Extrae campos clave (json) de: {document}")
        # Validación simple
        if "ERROR" in extract_resp["result"]:
            raise ToolError("Extracción fallida")
        record = {
            "summary": summary_resp["result"],
            "extracted": extract_resp["result"],
            "confidence": min(summary_resp["confidence"], extract_resp["confidence"]),
            "duration": time.time() - start
        }
        await self.storage.save(record)
        self.metrics.increment("pipeline.success")
        return record

