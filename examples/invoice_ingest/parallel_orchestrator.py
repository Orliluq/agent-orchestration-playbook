#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Agregar el path del proyecto para imports relativos
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.llm_adapter import MockLLM

async def extract_section(llm, section_text):
    resp = llm.generate(f"Extrae datos de: {section_text}")
    return resp

async def orchestrate_parallel(document_sections):
    llm = MockLLM()
    tasks = [asyncio.create_task(extract_section(llm, s)) for s in document_sections]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Manejo de errores y agregación
    aggregated = []
    for r in results:
        if isinstance(r, Exception):
            aggregated.append({"error": str(r)})
        else:
            aggregated.append(r)
    return aggregated

if __name__ == "__main__":
    sections = ["Encabezado factura", "Líneas", "Totales"]
    out = asyncio.run(orchestrate_parallel(sections))
    print(out)
