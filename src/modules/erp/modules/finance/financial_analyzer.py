from typing import Any, Dict

try:
    from src.core.module_registry import get_expert_by_domain
except Exception:
    get_expert_by_domain = None  # 兼容无专家框架场景


def analyze_financials(metrics: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"baseline": True}
    if get_expert_by_domain:
        try:
            expert = get_expert_by_domain("finance")
            if expert:
                result["expert"] = expert.predict({"metrics": metrics})
        except Exception as e:
            result["expert_error"] = str(e)
    return result
