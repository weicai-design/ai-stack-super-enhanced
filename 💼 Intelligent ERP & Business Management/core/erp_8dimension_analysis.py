"""
ERP 8 维度深度分析算法
提供质量、成本、交期、安全、利润、效率、管理、技术的专业化诊断输出。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
import math


DimensionPayload = Dict[str, Any]


@dataclass
class MetricInsight:
    """单项指标说明"""

    key: str
    name: str
    value: float
    unit: str = ""
    benchmark: Optional[str] = None
    interpretation: Optional[str] = None


@dataclass
class DimensionResult:
    """单个维度的分析结果"""

    dimension: str
    score: float
    status: str
    insight: str
    metrics: List[MetricInsight]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 2),
            "status": self.status,
            "insight": self.insight,
            "metrics": [asdict(m) for m in self.metrics],
        }


def _linear_score(value: float, best: float, worst: float) -> float:
    """
    将指标映射到 0-100 分。best 为理想状态，worst 为不可接受阈值。
    自动判断高/低优。
    """
    if math.isclose(best, worst):
        return 100.0
    if best > worst:
        if value >= best:
            ratio = 1.0
        elif value <= worst:
            ratio = 0.0
        else:
            ratio = (value - worst) / (best - worst)
    else:
        if value <= best:
            ratio = 1.0
        elif value >= worst:
            ratio = 0.0
        else:
            ratio = (worst - value) / (worst - best)
    return round(ratio * 100, 2)


def _avg(values: List[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else 0.0


def _status_from_score(score: float) -> str:
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "stable"
    if score >= 50:
        return "warning"
    return "critical"


def _insight(status: str, positive: str, neutral: str, negative: str) -> str:
    if status in ("excellent", "stable"):
        return positive
    if status == "warning":
        return neutral
    return negative


class ERP8DimensionAnalyzer:
    """
    将输入 payload 转换为八大维度的专业分析结果。
    payload 样例：
    {
        "quality": {"defects": 25, "total_units": 5200, "std_dev": 0.75, "spec_width": 1.8},
        "cost": {"material_cost": 1.2e6, "labor_cost": 4.5e5, "overhead_cost": 2.7e5,
                 "output_units": 18000, "target_unit_cost": 120},
        ...
    }
    """

    DIMENSIONS: Tuple[str, ...] = (
        "quality",
        "cost",
        "delivery",
        "safety",
        "profit",
        "efficiency",
        "management",
        "technology",
    )

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        weights = weights or {d: 1.0 for d in self.DIMENSIONS}
        total = sum(weights.values()) or 1.0
        self.weights = {d: weights.get(d, 0.0) / total for d in self.DIMENSIONS}
        self._handlers: Dict[str, Callable[[DimensionPayload], DimensionResult]] = {
            "quality": self._analyze_quality,
            "cost": self._analyze_cost,
            "delivery": self._analyze_delivery,
            "safety": self._analyze_safety,
            "profit": self._analyze_profit,
            "efficiency": self._analyze_efficiency,
            "management": self._analyze_management,
            "technology": self._analyze_technology,
        }

    # ---------------------- 对外入口 ----------------------
    def analyze(self, payload: Dict[str, DimensionPayload]) -> Dict[str, Any]:
        dimension_results: Dict[str, Dict[str, Any]] = {}
        weighted_scores: List[float] = []

        for dimension in self.DIMENSIONS:
            handler = self._handlers[dimension]
            result = handler(payload.get(dimension, {}))
            dimension_results[dimension] = result.as_dict()
            weighted_scores.append(result.score * self.weights[dimension])

        overall = round(sum(weighted_scores), 2)

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": overall,
            "weighting": self.weights,
            "dimensions": dimension_results,
        }

    # ---------------------- 质量 ----------------------
    def _analyze_quality(self, data: DimensionPayload) -> DimensionResult:
        total = max(float(data.get("total_units") or data.get("total", 0) or 1), 1.0)
        defects = max(float(data.get("defects", 0.0)), 0.0)
        critical = max(float(data.get("critical_defects", 0.0)), 0.0)
        defect_rate = defects / total
        ppm = defect_rate * 1_000_000
        sigma_level = max(0.0, min(6.0, 6 - math.log10(ppm + 1.0)))

        if "first_pass_yield" in data:
            fp_yield = float(data["first_pass_yield"])
        elif "first_pass_good_units" in data:
            fp_yield = (float(data["first_pass_good_units"]) / total) * 100
        else:
            fp_yield = max(50.0, 100 - defect_rate * 12000)

        std = data.get("std_dev")
        spec_width = data.get("spec_width")
        if std and spec_width:
            cpk = spec_width / (6.0 * float(std))
        else:
            cpk = float(data.get("cpk_estimate", 1.1))

        critical_ratio = critical / max(defects, 1.0) if defects else 0.0

        scores = [
            _linear_score(1 - defect_rate, 0.995, 0.95),
            _linear_score(fp_yield, 98.5, 90.0),
            _linear_score(cpk, 1.67, 1.0),
            _linear_score(1 - critical_ratio, 0.99, 0.9),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("defect_rate", "不良率", round(defect_rate * 100, 3), unit="%", benchmark="<1.0%"),
            MetricInsight("ppm", "百万缺陷数", round(ppm, 1), unit="DPPM", benchmark="<1000"),
            MetricInsight("sigma", "过程西格玛", round(sigma_level, 2), interpretation="≥4.5 表示过程稳定"),
            MetricInsight("fp_yield", "一次合格率", round(fp_yield, 2), unit="%", benchmark="≥98%"),
            MetricInsight("cpk", "过程能力 CPK", round(cpk, 3), benchmark="≥1.33"),
            MetricInsight("critical_ratio", "关键缺陷占比", round(critical_ratio * 100, 2), unit="%", benchmark="<5%"),
        ]

        insight = _insight(
            status,
            f"质量过程稳定，CPK {cpk:.2f}、一次合格率 {fp_yield:.1f}% 已达成高水平。",
            f"质量处于可控区间，但建议压降不良率至 {defect_rate * 100:.2f}% 以下并聚焦关键缺陷。",
            "质量波动明显，需优先强化过程能力与根因分析，构建闭环改善计划。",
        )

        return DimensionResult("quality", score, status, insight, metrics)

    # ---------------------- 成本 ----------------------
    def _analyze_cost(self, data: DimensionPayload) -> DimensionResult:
        material = float(data.get("material_cost", 0.0))
        labor = float(data.get("labor_cost", 0.0))
        overhead = float(data.get("overhead_cost") or data.get("overhead", 0.0))
        total_cost = material + labor + overhead
        output_units = max(float(data.get("output_units", 0.0)) or 1.0, 1.0)
        unit_cost = total_cost / output_units
        target_unit_cost = float(data.get("target_unit_cost", unit_cost))
        cost_variance = (unit_cost - target_unit_cost) / max(target_unit_cost, 1e-6)

        value_add_ratio = float(data.get("value_add_ratio", (total_cost - overhead) / max(total_cost, 1e-6)))
        inventory_turns = float(data.get("inventory_turnover", 8.0))
        procurement_savings = float(data.get("procurement_savings_rate", 0.02))

        scores = [
            _linear_score(-cost_variance, 0.05, -0.2),
            _linear_score(value_add_ratio, 0.7, 0.45),
            _linear_score(inventory_turns, 9.0, 5.0),
            _linear_score(procurement_savings, 0.04, 0.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("unit_cost", "单位成本", round(unit_cost, 2), unit="元/件", benchmark=f"目标 {target_unit_cost:.2f}"),
            MetricInsight("cost_variance", "成本偏差", round(cost_variance * 100, 2), unit="%", interpretation="负值代表优于目标"),
            MetricInsight("value_add_ratio", "增值投入占比", round(value_add_ratio * 100, 2), unit="%", benchmark="≥65%"),
            MetricInsight("inventory_turns", "库存周转", round(inventory_turns, 2), benchmark="≥8 次/年"),
            MetricInsight("procurement_savings", "采购降本率", round(procurement_savings * 100, 2), unit="%", benchmark="≥3%"),
        ]

        insight = _insight(
            status,
            f"成本结构健康，单位成本 {unit_cost:.2f} 元，库存周转 {inventory_turns:.1f} 次/年维持高效率。",
            "成本控制整体可接受，但需警惕单位成本偏差与库存资金占用带来的压力。",
            "成本表现承压，建议启动专项降本与库存压缩计划并改善采购谈判策略。",
        )

        return DimensionResult("cost", score, status, insight, metrics)

    # ---------------------- 交期 ----------------------
    def _analyze_delivery(self, data: DimensionPayload) -> DimensionResult:
        deliveries = max(float(data.get("total_deliveries") or data.get("deliveries", 0)) or 1.0, 1.0)
        on_time = float(data.get("on_time_deliveries") or data.get("on_time", 0.0))
        otif = (on_time / deliveries) * 100

        avg_lead = float(data.get("average_lead_time_days", data.get("avg_lead_time", 10.0)))
        commit_lead = float(data.get("commit_lead_time_days", avg_lead))
        lead_variance = abs(avg_lead - commit_lead) / max(commit_lead, 1e-6) * 100

        expedite_orders = float(data.get("expedite_orders", 0.0))
        expedite_ratio = expedite_orders / deliveries * 100
        buffer_days = float(data.get("critical_buffer_days", 1.5))

        scores = [
            _linear_score(otif, 97.0, 85.0),
            _linear_score(buffer_days, 3.0, 0.5),
            _linear_score(expedite_ratio, 5.0, 20.0),
            _linear_score(100 - lead_variance, 95.0, 75.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("otif", "准时交付率", round(otif, 2), unit="%", benchmark="≥95%"),
            MetricInsight("lead_time", "平均交付周期", round(avg_lead, 2), unit="天"),
            MetricInsight("lead_variance", "交付波动率", round(lead_variance, 2), unit="%", benchmark="≤10%"),
            MetricInsight("critical_buffer", "关键路径缓冲", round(buffer_days, 2), unit="天", benchmark="2-4天"),
            MetricInsight("expedite_ratio", "加急订单占比", round(expedite_ratio, 2), unit="%", benchmark="<8%"),
        ]

        insight = _insight(
            status,
            f"交期表现稳定，OTIF {otif:.1f}% 且关键缓冲 {buffer_days:.1f} 天，瓶颈管理有效。",
            "交付可靠性可接受，但加急/波动指标提示需加强产销协同与预测精度。",
            "交期失真明显，需梳理瓶颈产能与计划准确性，构建拉动式排产模型。",
        )

        return DimensionResult("delivery", score, status, insight, metrics)

    # ---------------------- 安全 ----------------------
    def _analyze_safety(self, data: DimensionPayload) -> DimensionResult:
        incidents = float(data.get("recordable_incidents") or data.get("incidents", 0.0))
        lost_time = float(data.get("lost_time_cases", 0.0))
        hours = max(float(data.get("work_hours_k", 0.0)) or float(data.get("total_hours", 0.0)) or 1.0, 1.0)
        trir = (incidents / hours) * 1000  # 每百万工时
        ltir = (lost_time / hours) * 1000

        hazards = float(data.get("hazards_found", 0.0))
        hazards_closed = float(data.get("hazards_closed", 0.0))
        closure_rate = hazards_closed / max(hazards, 1.0) * 100

        near_miss = float(data.get("near_miss_reports", 0.0))
        employees = max(float(data.get("employee_count", 200)), 1.0)
        near_miss_rate = near_miss / employees * 100

        scores = [
            _linear_score(-trir, -1.0, -3.5),
            _linear_score(-ltir, -0.5, -2.0),
            _linear_score(closure_rate, 96.0, 80.0),
            _linear_score(near_miss_rate, 12.0, 3.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("trir", "总可记录事故率", round(trir, 3), unit="(百万工时)", benchmark="<1.2"),
            MetricInsight("ltir", "损失工时事故率", round(ltir, 3), unit="(百万工时)", benchmark="<0.5"),
            MetricInsight("closure_rate", "隐患整改率", round(closure_rate, 2), unit="%", benchmark=">95%"),
            MetricInsight("near_miss", "未遂事件填报率", round(near_miss_rate, 2), unit="%/人", benchmark="10-15%"),
        ]

        insight = _insight(
            status,
            "安全文化成熟，事故率与隐患闭环均维持世界级水平，可持续推行主动安全。",
            "安全表现波动，需提升现场监督与 Near Miss 激励，巩固隐患整改速度。",
            "安全指标超限，建议立即执行零容忍整改与班组级安全 Leadership 行动。",
        )

        return DimensionResult("safety", score, status, insight, metrics)

    # ---------------------- 利润 ----------------------
    def _analyze_profit(self, data: DimensionPayload) -> DimensionResult:
        revenue = max(float(data.get("revenue", 0.0)) or 1.0, 1.0)
        cogs = float(data.get("cogs") or data.get("cost", revenue * 0.7))
        operating_expense = float(data.get("operating_expense", revenue * 0.15))
        ebitda = float(data.get("ebitda", revenue - cogs - operating_expense))

        gross_margin = (revenue - cogs) / revenue * 100
        ebitda_margin = ebitda / revenue * 100
        cash_cycle = float(data.get("cash_conversion_days", 55.0))
        new_business_ratio = float(data.get("new_business_ratio", 0.15)) * 100

        scores = [
            _linear_score(gross_margin, 28.0, 15.0),
            _linear_score(ebitda_margin, 18.0, 8.0),
            _linear_score(-cash_cycle, -45.0, -75.0),
            _linear_score(new_business_ratio, 20.0, 8.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("gross_margin", "毛利率", round(gross_margin, 2), unit="%", benchmark="≥25%"),
            MetricInsight("ebitda_margin", "EBITDA 利润率", round(ebitda_margin, 2), unit="%", benchmark="≥15%"),
            MetricInsight("cash_cycle", "现金转换周期", round(cash_cycle, 1), unit="天", benchmark="<50 天"),
            MetricInsight("new_business_ratio", "新业务占比", round(new_business_ratio, 2), unit="%", benchmark="≥15%"),
        ]

        insight = _insight(
            status,
            "利润率与现金周转表现优秀，具备扩大投资与创新的财务弹性。",
            "盈利能力处于行业平均水平，需要聚焦新业务与成本结构以防利润侵蚀。",
            "利润与现金表现承压，需同步推进提价、组合优化及运营现金释放计划。",
        )

        return DimensionResult("profit", score, status, insight, metrics)

    # ---------------------- 效率 ----------------------
    def _analyze_efficiency(self, data: DimensionPayload) -> DimensionResult:
        availability = float(data.get("availability", 88.0))
        performance = float(data.get("performance", 90.0))
        quality_rate = float(data.get("quality_rate", 97.5))
        oee = availability / 100 * performance / 100 * quality_rate / 100 * 100

        throughput = float(data.get("throughput_units", 0.0))
        planned = float(data.get("planned_throughput_units", throughput or 1.0))
        throughput_rate = throughput / max(planned, 1.0) * 100

        energy = float(data.get("energy_per_unit", 1.8))
        target_energy = float(data.get("target_energy_per_unit", energy))
        energy_gap = energy - target_energy

        changeover = float(data.get("average_changeover_minutes", 45.0))

        scores = [
            _linear_score(oee, 75.0, 55.0),
            _linear_score(throughput_rate, 105.0, 85.0),
            _linear_score(-energy_gap, 0.1, -0.5),
            _linear_score(-changeover, -30.0, -60.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("oee", "综合设备效率 OEE", round(oee, 2), unit="%", benchmark="≥70%"),
            MetricInsight("availability", "开动率", round(availability, 2), unit="%"),
            MetricInsight("performance", "性能效率", round(performance, 2), unit="%"),
            MetricInsight("quality_rate", "质量合格率", round(quality_rate, 2), unit="%"),
            MetricInsight("throughput_rate", "产能达成率", round(throughput_rate, 2), unit="%", benchmark="≥100%"),
            MetricInsight("energy_gap", "单位能耗与目标差", round(energy_gap, 3), unit="kWh/件"),
            MetricInsight("changeover", "平均换型时间", round(changeover, 1), unit="分钟"),
        ]

        insight = _insight(
            status,
            "效率指标表现领先，OEE 与产能达成率稳定在政策目标之上，可复制经验到瓶颈产线。",
            "效率尚可但存在能耗与换型时间机会点，建议启动精益项目以释放产能。",
            "效率低于预期，需聚焦计划稳定性与设备可用性，辅以能耗管理体系。",
        )

        return DimensionResult("efficiency", score, status, insight, metrics)

    # ---------------------- 管理 ----------------------
    def _analyze_management(self, data: DimensionPayload) -> DimensionResult:
        process_maturity = float(data.get("process_maturity", 78.0))
        policy_adherence = float(data.get("policy_adherence", 88.0))
        digital_adoption = float(data.get("digital_adoption_rate", 65.0))
        training_completion = float(data.get("training_completion", 72.0))
        audit_findings = float(data.get("audit_findings", 4.0))

        scores = [
            _linear_score(process_maturity, 85.0, 60.0),
            _linear_score(policy_adherence, 95.0, 75.0),
            _linear_score(digital_adoption, 80.0, 50.0),
            _linear_score(training_completion, 85.0, 60.0),
            _linear_score(-audit_findings, -2.0, -6.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("process_maturity", "流程成熟度", round(process_maturity, 1), unit="%", benchmark="≥80%"),
            MetricInsight("policy_adherence", "制度执行率", round(policy_adherence, 1), unit="%", benchmark="≥92%"),
            MetricInsight("digital_adoption", "数字化覆盖率", round(digital_adoption, 1), unit="%", benchmark="≥75%"),
            MetricInsight("training_completion", "培训完成率", round(training_completion, 1), unit="%", benchmark="≥85%"),
            MetricInsight("audit_findings", "审计问题数量", round(audit_findings, 1), benchmark="≤3 项"),
        ]

        insight = _insight(
            status,
            "管理体系成熟，流程与制度执行力高，可迈向端到端数字化治理与自适应机制。",
            "管理可控但仍需提升数字化 adoption 与干部培训，确保策略下沉。",
            "管理基础薄弱，需重塑流程内控与问责机制，优先补齐人才与数字平台能力。",
        )

        return DimensionResult("management", score, status, insight, metrics)

    # ---------------------- 技术 ----------------------
    def _analyze_technology(self, data: DimensionPayload) -> DimensionResult:
        release_velocity = float(data.get("release_velocity", 8.0))  # 次/季度
        automation = float(data.get("automation_coverage", 62.0))
        tech_debt = float(data.get("tech_debt_ratio", 0.18)) * 100
        mttr = float(data.get("mttr_hours", 4.0))
        cloud_ratio = float(data.get("cloud_migration_ratio", 55.0))

        scores = [
            _linear_score(release_velocity, 10.0, 4.0),
            _linear_score(automation, 80.0, 50.0),
            _linear_score(-tech_debt, -12.0, -25.0),
            _linear_score(-mttr, -2.0, -8.0),
            _linear_score(cloud_ratio, 70.0, 40.0),
        ]
        score = _avg(scores)
        status = _status_from_score(score)

        metrics = [
            MetricInsight("release_velocity", "版本迭代速度", round(release_velocity, 1), unit="次/季度", benchmark="≥9 次"),
            MetricInsight("automation", "自动化覆盖率", round(automation, 1), unit="%", benchmark="≥75%"),
            MetricInsight("tech_debt", "技术债务占比", round(tech_debt, 1), unit="%", benchmark="<15%"),
            MetricInsight("mttr", "平均恢复时间", round(mttr, 2), unit="小时", benchmark="<3h"),
            MetricInsight("cloud_ratio", "云化/平台化覆盖", round(cloud_ratio, 1), unit="%", benchmark="≥65%"),
        ]

        insight = _insight(
            status,
            "技术引擎充足，发布节奏快且自动化深，完全具备支撑业务创新的能力。",
            "技术能力尚可，但需压降技术债与恢复时间，进一步深化自动化覆盖。",
            "技术平台存在结构性风险，须加速云化改造并建立系统韧性治理。",
        )

        return DimensionResult("technology", score, status, insight, metrics)


__all__ = ["ERP8DimensionAnalyzer", "DimensionResult", "MetricInsight"]




