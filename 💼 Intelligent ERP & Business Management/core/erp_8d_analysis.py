"""
ERP 8维度分析库
提供质量/成本/交期/安全/利润/效率/管理/技术 八大维度的指标与分析函数
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import math


@dataclass
class Metric:
    key: str
    name: str
    value: float
    unit: str = ""
    level: Optional[str] = None  # normal/warning/critical
    note: Optional[str] = None


def _level_by_thresholds(value: float, thresholds: Tuple[float, float], reverse: bool = False) -> str:
    """
    根据阈值返回等级：
    - reverse=False: value <= warn -> normal, <= critical -> warning, else critical
    - reverse=True:  value >= warn -> normal, >= critical -> warning, else critical
    """
    warn, critical = thresholds
    if reverse:
        if value >= warn:
            return "normal"
        if value >= critical:
            return "warning"
        return "critical"
    else:
        if value <= warn:
            return "normal"
        if value <= critical:
            return "warning"
        return "critical"


# 质量维度（示例：不良率、过程能力CPK、缺陷密度）
def analyze_quality(defects: int, total: int, std_dev: Optional[float] = None, spec_width: Optional[float] = None) -> List[Metric]:
    total = max(total, 1)
    defect_rate = defects / total
    level = _level_by_thresholds(defect_rate * 100, (1.0, 3.0))  # 1%正常，3%预警，以上严重
    metrics = [
        Metric(key="defect_rate", name="不良率", value=round(defect_rate * 100, 3), unit="%", level=level),
        Metric(key="dppm", name="百万缺陷数", value=round(defect_rate * 1_000_000, 1), unit="DPPM")
    ]
    if std_dev and spec_width:
        cpk = spec_width / (6.0 * std_dev)
        metrics.append(Metric(
            key="cpk", name="过程能力指数CPK", value=round(cpk, 3),
            level=_level_by_thresholds(cpk, (1.33, 1.0), reverse=True),
            note="参考：CPK≥1.33为稳定可接受"
        ))
    return metrics


# 成本维度（示例：单位成本、ABC占比、降本空间）
def analyze_cost(material_cost: float, labor_cost: float, overhead: float, output_units: int) -> List[Metric]:
    units = max(output_units, 1)
    unit_cost = (material_cost + labor_cost + overhead) / units
    material_ratio = (material_cost / max(material_cost + labor_cost + overhead, 1e-9)) * 100
    return [
        Metric(key="unit_cost", name="单位成本", value=round(unit_cost, 2), unit="元/件"),
        Metric(key="material_ratio", name="材料成本占比", value=round(material_ratio, 2), unit="%")
    ]


# 交期维度（示例：准时交付率、关键路径缓冲、瓶颈利用率）
def analyze_delivery(on_time: int, deliveries: int, critical_buffer_days: float, bottleneck_util_percent: float) -> List[Metric]:
    deliveries = max(deliveries, 1)
    otif = (on_time / deliveries) * 100
    return [
        Metric(key="otif", name="准时交付率", value=round(otif, 2), unit="%", level=_level_by_thresholds(otif, (95.0, 85.0), reverse=True)),
        Metric(key="critical_buffer", name="关键路径缓冲", value=round(critical_buffer_days, 2), unit="天",
               level=_level_by_thresholds(critical_buffer_days, (2.0, 1.0), reverse=True)),
        Metric(key="bottleneck_util", name="瓶颈利用率", value=round(bottleneck_util_percent, 2), unit="%", 
               level=_level_by_thresholds(bottleneck_util_percent, (85.0, 95.0)))  # >95%趋近过载
    ]


# 安全维度（示例：事故率、隐患整改率）
def analyze_safety(incidents: int, work_hours_k: float, hazards_found: int, hazards_closed: int) -> List[Metric]:
    hours = max(work_hours_k, 0.001)
    incident_rate = (incidents / hours)  # 每千小时事故数
    hazard_close_rate = (hazards_closed / max(hazards_found, 1)) * 100
    return [
        Metric(key="incident_rate", name="事故率(每千小时)", value=round(incident_rate, 3), level=_level_by_thresholds(incident_rate, (0.2, 0.5))),
        Metric(key="hazard_close_rate", name="隐患整改率", value=round(hazard_close_rate, 2), unit="%", level=_level_by_thresholds(hazard_close_rate, (95.0, 85.0), reverse=True))
    ]


# 利润维度（示例：毛利率、边际贡献）
def analyze_profit(revenue: float, cost: float, variable_cost: float) -> List[Metric]:
    revenue = max(revenue, 1e-9)
    gross_margin = ((revenue - cost) / revenue) * 100
    contrib_margin = ((revenue - variable_cost) / revenue) * 100
    return [
        Metric(key="gross_margin", name="毛利率", value=round(gross_margin, 2), unit="%", level=_level_by_thresholds(gross_margin, (20.0, 10.0), reverse=True)),
        Metric(key="contribution_margin", name="边际贡献率", value=round(contrib_margin, 2), unit="%")
    ]


# 效率维度（示例：OEE）
def analyze_efficiency(availability: float, performance: float, quality: float) -> List[Metric]:
    # availability/performance/quality 输入为百分数
    oee = (availability / 100.0) * (performance / 100.0) * (quality / 100.0) * 100
    return [
        Metric(key="oee", name="综合设备效率OEE", value=round(oee, 2), unit="%", level=_level_by_thresholds(oee, (65.0, 55.0), reverse=True)),
        Metric(key="availability", name="开动率", value=round(availability, 2), unit="%"),
        Metric(key="performance", name="性能效率", value=round(performance, 2), unit="%"),
        Metric(key="quality_rate", name="质量合格率", value=round(quality, 2), unit="%")
    ]


# 管理维度（示例：流程完备度、制度执行率）
def analyze_management(process_maturity: float, policy_adherence: float) -> List[Metric]:
    # 输入0-100
    return [
        Metric(key="process_maturity", name="流程成熟度", value=round(process_maturity, 1), unit="%", level=_level_by_thresholds(process_maturity, (80.0, 60.0), reverse=True)),
        Metric(key="policy_adherence", name="制度执行率", value=round(policy_adherence, 1), unit="%", level=_level_by_thresholds(policy_adherence, (90.0, 75.0), reverse=True))
    ]


# 技术维度（示例：技术完备度、缺陷修复速度）
def analyze_technology(tech_coverage: float, defects_open_days_avg: float) -> List[Metric]:
    return [
        Metric(key="tech_coverage", name="技术完备度", value=round(tech_coverage, 1), unit="%", level=_level_by_thresholds(tech_coverage, (85.0, 70.0), reverse=True)),
        Metric(key="defect_fix_speed", name="缺陷平均修复天数", value=round(defects_open_days_avg, 2), unit="天", level=_level_by_thresholds(defects_open_days_avg, (5.0, 10.0)))
    ]


def analyze_8d(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一入口：对传入的度量进行8维度分析，缺失项使用保守默认。
    payload示例：
    {
      "quality": {"defects": 20, "total": 5000, "std_dev": 0.8, "spec_width": 1.2},
      "cost": {"material_cost": 120000, "labor_cost": 60000, "overhead": 30000, "output_units": 2000},
      ...
    }
    """
    result: Dict[str, List[Dict[str, Any]]] = {}

    q = payload.get("quality", {})
    result["quality"] = [m.__dict__ for m in analyze_quality(
        defects=int(q.get("defects", 0)),
        total=int(q.get("total", 1)),
        std_dev=q.get("std_dev"),
        spec_width=q.get("spec_width"),
    )]

    c = payload.get("cost", {})
    result["cost"] = [m.__dict__ for m in analyze_cost(
        float(c.get("material_cost", 0.0)),
        float(c.get("labor_cost", 0.0)),
        float(c.get("overhead", 0.0)),
        int(c.get("output_units", 1)),
    )]

    d = payload.get("delivery", {})
    result["delivery"] = [m.__dict__ for m in analyze_delivery(
        int(d.get("on_time", 0)),
        int(d.get("deliveries", 1)),
        float(d.get("critical_buffer_days", 2.0)),
        float(d.get("bottleneck_util_percent", 85.0)),
    )]

    s = payload.get("safety", {})
    result["safety"] = [m.__dict__ for m in analyze_safety(
        int(s.get("incidents", 0)),
        float(s.get("work_hours_k", 1.0)),
        int(s.get("hazards_found", 0)),
        int(s.get("hazards_closed", 0)),
    )]

    p = payload.get("profit", {})
    result["profit"] = [m.__dict__ for m in analyze_profit(
        float(p.get("revenue", 1.0)),
        float(p.get("cost", 0.0)),
        float(p.get("variable_cost", p.get("cost", 0.0))),
    )]

    e = payload.get("efficiency", {})
    result["efficiency"] = [m.__dict__ for m in analyze_efficiency(
        float(e.get("availability", 70.0)),
        float(e.get("performance", 85.0)),
        float(e.get("quality", 98.0)),
    )]

    mgt = payload.get("management", {})
    result["management"] = [m.__dict__ for m in analyze_management(
        float(mgt.get("process_maturity", 75.0)),
        float(mgt.get("policy_adherence", 85.0)),
    )]

    t = payload.get("technology", {})
    result["technology"] = [m.__dict__ for m in analyze_technology(
        float(t.get("tech_coverage", 75.0)),
        float(t.get("defects_open_days_avg", 7.5)),
    )]

    # 计算总览评分（简单平均，后续可做加权）
    overall_scores = []
    for group in result.values():
        # 尝试取第一个百分比型指标作为该维度的代表
        percent_vals = [it["value"] for it in group if it.get("unit") == "%"]
        if percent_vals:
            overall_scores.append(sum(percent_vals) / len(percent_vals))
    overall = round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0.0

    return {
        "success": True,
        "analysis": result,
        "overall_score_percent": overall,
        "timestamp": datetime.now().isoformat()
    }


