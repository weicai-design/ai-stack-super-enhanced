"""
算法库：根据模板计算8维度指标得分
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


def safe_get(data: Dict[str, Any], field: str, default: float = 0.0) -> float:
    value = data.get(field, default)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except Exception:
        return default


def normalize_score(value: float, target: float, direction: str) -> float:
    if target == 0:
        target = 0.0001
    if direction == "positive":
        score = (value / target) * 100
    else:
        # negative 越低越好
        if value == 0:
            return 100.0
        score = (target / value) * 100
    return max(0.0, min(120.0, score))


def evaluate_indicator(data: Dict[str, Any], indicator: Dict[str, Any]) -> Tuple[float, float]:
    value = safe_get(data, indicator.get("field", ""), 0.0)
    if indicator.get("unit") == "%":
        value = value if value <= 100 else value * 100
    target = indicator.get("target", 0.0)
    direction = indicator.get("direction", "positive")
    score = normalize_score(value, target, direction)
    return value, score


def evaluate_dimension(data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    indicators_result: List[Dict[str, Any]] = []
    weighted_score = 0.0

    for ind in template["indicators"]:
        value, score = evaluate_indicator(data, ind)
        indicator_score = score * ind.get("weight", 0)
        weighted_score += indicator_score
        indicators_result.append(
            {
                "name": ind["name"],
                "label": ind["label"],
                "value": round(value, 2),
                "unit": ind.get("unit", ""),
                "score": round(score, 2),
                "target": ind.get("target"),
                "direction": ind.get("direction"),
                "suggestion": ind.get("suggestion"),
            }
        )

    score = round(weighted_score, 2)
    analysis = build_analysis(template["label"], indicators_result)
    suggestions = [
        ind["suggestion"]
        for ind in indicators_result
        if ind["score"] < 80 and ind.get("suggestion")
    ]
    return {
        "dimension": template["label"],
        "score": score,
        "level": classify_level(score),
        "indicators": indicators_result,
        "analysis": analysis,
        "suggestions": suggestions,
    }


def build_analysis(label: str, indicators: List[Dict[str, Any]]) -> str:
    top = sorted(indicators, key=lambda x: x["score"], reverse=True)[:2]
    summary = ", ".join(
        f"{item['label']}{item['value']}{item.get('unit','')}"
        for item in top
    )
    return f"{label}关键指标：{summary}"


def classify_level(score: float) -> str:
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "good"
    if score >= 70:
        return "average"
    if score >= 60:
        return "poor"
    return "critical"


