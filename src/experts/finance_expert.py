from typing import Any, Dict

from .base import Expert
from .registry import register


class FinanceExpert(Expert):
    name = "finance_expert"
    domain = "finance"

    def __init__(self, risk_threshold: float = 0.6) -> None:
        self.risk_threshold = risk_threshold

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        metrics = payload.get("metrics", {})
        debt_ratio = float(metrics.get("debt_ratio", 0.0))
        cash_flow = float(metrics.get("cash_flow", 0.0))
        score = 0.5 * debt_ratio + 0.5 * cash_flow
        risk = "high" if score > self.risk_threshold else "normal"
        return {"score": score, "risk": risk}


register(FinanceExpert.name, FinanceExpert)
