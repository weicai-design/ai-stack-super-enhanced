#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 八维度分析引擎
维度：质量、成本、交期、安全、利润、效率、管理、技术
每个维度包含一组指标、目标值、方向（越高越好/越低越好）和权重。
输入：payload = {"quality": {"defect_rate": 0.9, ...}, "cost": {...}}
输出：整体得分、维度得分、风险/建议列表
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MetricRule:
    field: str
    name: str
    target: float
    weight: float
    direction: str = "higher"  # higher / lower
    unit: Optional[str] = None
    default: Optional[float] = None


DIMENSION_LIBRARY: Dict[str, Dict[str, Any]] = {
    "quality": {
        "name": "质量",
        "weight": 0.14,
        "metrics": [
            MetricRule("first_pass_rate", "首检合格率", 0.98, 0.45),
            MetricRule("defect_rate", "缺陷率", 0.01, 0.35, direction="lower"),
            MetricRule("customer_return_ppm", "客户退货(PPM)", 250, 0.20, direction="lower"),
        ],
        "playbooks": {
            "risk": ["触发6σ专项", "对高缺陷工序实施100%全检"],
            "watch": ["增加首件审核频次", "抽检覆盖率+15%"],
            "good": ["保持现有SPC监控策略"],
        },
    },
    "cost": {
        "name": "成本",
        "weight": 0.13,
        "metrics": [
            MetricRule("unit_cost", "单位成本", 1.0, 0.35, direction="lower"),
            MetricRule("material_spot_rate", "物料现货比例", 0.3, 0.35),
            MetricRule("budget_variance", "预算偏差", 0.05, 0.30, direction="lower"),
        ],
        "playbooks": {
            "risk": ["启用紧急成本审计", "冻结非关键物料采购"],
            "watch": ["开展成本对标", "扩大框架采购覆盖率"],
            "good": ["继续执行分级采购策略"],
        },
    },
    "delivery": {
        "name": "交期",
        "weight": 0.14,
        "metrics": [
            MetricRule("on_time_delivery", "准时交付率", 0.95, 0.5),
            MetricRule("critical_path_slip", "关键路径偏差", 0.05, 0.3, direction="lower"),
            MetricRule("expedite_ratio", "加急比例", 0.1, 0.2, direction="lower"),
        ],
        "playbooks": {
            "risk": ["触发TOC排程重排", "联合供应链加急"],
            "watch": ["加强关键路径监控", "提升物料齐套预测"],
            "good": ["保持数字化排程节奏"],
        },
    },
    "safety": {
        "name": "安全",
        "weight": 0.12,
        "metrics": [
            MetricRule("incident_rate", "安全事件率", 0.002, 0.5, direction="lower"),
            MetricRule("audit_score", "审计评分", 0.9, 0.3),
            MetricRule("compliance_gap", "合规缺口", 0.05, 0.2, direction="lower"),
        ],
        "playbooks": {
            "risk": ["立即停线整改", "升级EHS红色预警"],
            "watch": ["提高班组巡检频次", "复核关键工位PPE"],
            "good": ["保持双重预防机制"],
        },
    },
    "profit": {
        "name": "利润",
        "weight": 0.12,
        "metrics": [
            MetricRule("gross_margin", "毛利率", 0.32, 0.5),
            MetricRule("cash_flow_days", "现金周转天数", 45, 0.3, direction="lower"),
            MetricRule("new_business_ratio", "新业务占比", 0.25, 0.2),
        ],
        "playbooks": {
            "risk": ["重构产品组合", "启动价格保护策略"],
            "watch": ["审查低毛利订单", "同步成本+价格联动"],
            "good": ["加速新业务投放"],
        },
    },
    "efficiency": {
        "name": "效率",
        "weight": 0.11,
        "metrics": [
            MetricRule("oee", "OEE", 0.82, 0.45),
            MetricRule("changeover_time", "换线时间", 45, 0.3, direction="lower"),
            MetricRule("automation_ratio", "自动化覆盖率", 0.4, 0.25),
        ],
        "playbooks": {
            "risk": ["投入临时产能", "拆解瓶颈站位"],
            "watch": ["开展SMED专项", "提高预测准确度"],
            "good": ["继续推进产线自动化"],
        },
    },
    "management": {
        "name": "管理",
        "weight": 0.12,
        "metrics": [
            MetricRule("process_adherence", "流程遵循度", 0.92, 0.4),
            MetricRule("issue_closure_rate", "问题关闭率", 0.85, 0.35),
            MetricRule("data_latency", "数据延迟", 30, 0.25, direction="lower", unit="min"),
        ],
        "playbooks": {
            "risk": ["立即启动治理专班", "强制执行流程闸门"],
            "watch": ["完善流程度量", "提升跨部门节奏对齐"],
            "good": ["保持自动化回执机制"],
        },
    },
    "technology": {
        "name": "技术",
        "weight": 0.12,
        "metrics": [
            MetricRule("bom_maturity", "BOM成熟度", 0.9, 0.4),
            MetricRule("digital_thread", "数字线程覆盖", 0.6, 0.3),
            MetricRule("tech_risk_score", "技术风险指数", 0.1, 0.3, direction="lower"),
        ],
        "playbooks": {
            "risk": ["冻结风险BOM", "引入技术评审委员会"],
            "watch": ["提升仿真覆盖率", "监控技术债务"],
            "good": ["推进数字孪生扩面"],
        },
    },
}


def _normalize(value: float, target: float, direction: str) -> float:
    if direction == "higher":
        if target == 0:
            return 1.0
        return max(0.0, min(1.2, value / target))
    # lower is better
    if value == 0:
        return 1.0
    return max(0.0, min(1.2, target / value))


def _dimension_score(payload: Dict[str, Any], dim_id: str) -> Dict[str, Any]:
    config = DIMENSION_LIBRARY[dim_id]
    metrics_payload = payload.get(dim_id, {})
    metric_results: List[Dict[str, Any]] = []
    total = 0.0
    weight_sum = 0.0
    alerts: List[str] = []

    for rule in config["metrics"]:
        actual = metrics_payload.get(rule.field, rule.default if rule.default is not None else rule.target)
        normalized = _normalize(actual, rule.target, rule.direction)
        weighted_score = normalized * rule.weight
        total += weighted_score
        weight_sum += rule.weight
        status = _status_from_score(normalized)
        if status == "risk":
            alerts.append(f"{rule.name} 低于阈值 (当前 {actual}, 目标 {rule.target})")
        metric_results.append(
            {
                "field": rule.field,
                "name": rule.name,
                "actual": actual,
                "target": rule.target,
                "unit": rule.unit,
                "direction": rule.direction,
                "normalized": round(normalized, 3),
                "status": status,
                "weight": rule.weight,
            }
        )

    score = round(total / (weight_sum or 1), 3)
    status = _status_from_score(score)
    recommendation = config["playbooks"].get(status, [])
    return {
        "id": dim_id,
        "name": config["name"],
        "score": score,
        "status": status,
        "metrics": metric_results,
        "recommendations": recommendation,
        "alerts": alerts,
    }


def _status_from_score(score: float) -> str:
    if score >= 0.85:
        return "good"
    if score >= 0.7:
        return "watch"
    return "risk"


def analyze_8d(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行八维度分析
    Args:
        payload: Dict[str, Dict[str, float]]
    Returns:
        Dict 包含 overall_score、dimensions、alerts、timestamp
    """
    dimensions: List[Dict[str, Any]] = []
    overall = 0.0
    overall_weight = 0.0
    global_alerts: List[str] = []

    for dim_id, config in DIMENSION_LIBRARY.items():
        dim_result = _dimension_score(payload, dim_id)
        dimensions.append(dim_result)
        overall += dim_result["score"] * config["weight"]
        overall_weight += config["weight"]
        global_alerts.extend(dim_result["alerts"])

    overall_score = round(overall / (overall_weight or 1), 3)
    return {
        "success": True,
        "overall_score": overall_score,
        "status": _status_from_score(overall_score),
        "dimensions": dimensions,
        "alerts": global_alerts,
        "timestamp": _now(),
    }


__all__ = ["analyze_8d", "DIMENSION_LIBRARY"]


