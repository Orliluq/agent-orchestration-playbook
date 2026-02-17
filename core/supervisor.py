import json
from typing import Dict
class Supervisor:
    def __init__(self, max_retries=2, threshold_accept=0.75, threshold_escalate=0.3, experience_log="experience.log"):
        self.max_retries = max_retries
        self.threshold_accept = threshold_accept
        self.threshold_escalate = threshold_escalate
        self.experience_log = experience_log

    def decide(self, out: Dict) -> str:
        c = out.get("confidence", 0.0)
        if c >= self.threshold_accept:
            return "accept"
        if c <= self.threshold_escalate:
            return "escalate"
        return "retry"

    def record(self, context: Dict, outcome: Dict):
        entry = {"context": context, "outcome": outcome}
        with open(self.experience_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
