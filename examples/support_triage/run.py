#!/usr/bin/env python3
import asyncio, random, time
from typing import Dict, Any, List
class MockLLMAsync:
    async def generate(self, prompt: str) -> Dict[str, Any]:
        await asyncio.sleep(0.05 + random.random() * 0.05)
        confidence = round(random.uniform(0.3, 0.98), 2)
        if "clasifica" in prompt or "clasificación" in prompt:
            label = random.choice(["low", "medium", "high"])
            return {"result": label, "confidence": confidence}
        return {"result": f"Respuesta automática para: {prompt[:60]}", "confidence": confidence}
class Notifier:
    def notify_human(self, ticket_id: str, reason: str):
        print(f"[notifier] Escalado humano: ticket {ticket_id}, motivo: {reason}")
async def process_ticket(llm: MockLLMAsync, notifier: Notifier, ticket: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = ticket["id"]
    text = ticket["text"]
    cls = await llm.generate(f"clasifica prioridad del ticket: {text}")
    if cls["result"] == "high" and cls["confidence"] < 0.9:
        notifier.notify_human(ticket_id, "alta prioridad con confianza baja")
        return {"id": ticket_id, "action": "escalate", "priority": cls["result"], "confidence": cls["confidence"]}
    resp = await llm.generate(f"genera respuesta breve para: {text}")
    if resp["confidence"] >= 0.7:
        return {"id": ticket_id, "action": "auto_respond", "response": resp["result"], "confidence": resp["confidence"]}
    else:
        notifier.notify_human(ticket_id, "respuesta automática con baja confianza")
        return {"id": ticket_id, "action": "escalate", "priority": cls["result"], "confidence": resp["confidence"]}
async def orchestrate_tickets(tickets: List[Dict[str, Any]]):
    llm = MockLLMAsync()
    notifier = Notifier()
    sem = asyncio.Semaphore(8)
    async def guarded(ticket):
        async with sem:
            return await process_ticket(llm, notifier, ticket)
    tasks = [asyncio.create_task(guarded(t)) for t in tickets]
    results = await asyncio.gather(*tasks)
    return results
if __name__ == "__main__":
    sample_tickets = [
        {"id": "T1", "text": "No puedo iniciar sesión en la app."},
        {"id": "T2", "text": "Solicitud de reembolso por cargo duplicado."},
        {"id": "T3", "text": "Error 500 al subir archivo grande."},
        {"id": "T4", "text": "Consulta sobre facturación y descuentos."}
    ]
    out = asyncio.run(orchestrate_tickets(sample_tickets))
    print("Resultados del triage:")
    for r in out:
        print(r)
