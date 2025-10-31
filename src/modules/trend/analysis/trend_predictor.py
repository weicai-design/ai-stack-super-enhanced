from typing import Any, Dict, List

try:
    from src.core.module_registry import get_expert_by_domain
except Exception:
    get_expert_by_domain = None


def predict_trend(series: List[float]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"baseline": True}
    if get_expert_by_domain:
        try:
            expert = get_expert_by_domain("trend")
            if expert:
                out["expert"] = expert.predict({"series": series})
        except Exception as e:
            out["expert_error"] = str(e)
    return out
