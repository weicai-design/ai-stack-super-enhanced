from typing import Any, Dict, List

from .base import Expert
from .registry import register


class TrendExpert(Expert):
    name = "trend_expert"
    domain = "trend"

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        series: List[float] = payload.get("series", [])
        if len(series) < 10:
            return {"direction": "flat", "reason": "insufficient_data"}
        left, right = sum(series[-10:-5]), sum(series[-5:])
        direction = "up" if right >= left else "down"
        return {"direction": direction}


register(TrendExpert.name, TrendExpert)
