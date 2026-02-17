#!/usr/bin/env python3
import random, time, json
from typing import Dict, Any
class MockLLM:
    def generate(self, prompt: str) -> Dict[str, Any]:
        time.sleep(0.05)
        confidence = round(random.uniform(0.4, 0.98), 2)
        if "revisa este diff" in prompt or "genera comentarios" in prompt:
            comments = [
                {"line": 12, "comment": "Posible condición de carrera"},
                {"line": 45, "comment": "Falta manejo de error para None"}
            ]
            return {"result": json.dumps(comments), "confidence": confidence}
        return {"result": "OK", "confidence": confidence}
def run_unit_tests() -> Dict[str, Any]:
    time.sleep(0.05)
    passed = random.choice([True, True, False])
    return {"passed": passed, "details": "3 tests, 2 passed" if not passed else "3 tests, all passed"}
class CodeReviewOrchestrator:
    def __init__(self, llm: MockLLM):
        self.llm = llm
    def review_and_decide(self, diff_text: str) -> Dict[str, Any]:
        review = self.llm.generate(f"revisa este diff y genera comentarios: {diff_text}")
        comments = json.loads(review["result"])
        test_res = run_unit_tests()
        if not test_res["passed"]:
            return {"action": "request_human_review", "reason": "tests_failed", "comments": comments, "test": test_res}
        if review["confidence"] >= 0.75:
            return {"action": "auto_approve_and_open_pr", "comments": comments, "confidence": review["confidence"]}
        else:
            return {"action": "request_human_review", "reason": "low_confidence", "comments": comments, "confidence": review["confidence"]}
if __name__ == "__main__":
    llm = MockLLM()
    orchestrator = CodeReviewOrchestrator(llm)
    sample_diff = "diff --git a/app.py b/app.py\n+ def new_feature():\n+    pass\n"
    result = orchestrator.review_and_decide(sample_diff)
    print("Decisión de revisión:", result)
