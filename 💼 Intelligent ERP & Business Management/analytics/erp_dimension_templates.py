"""
统一的 8 维度指标模板
对每个维度的指标口径、公式、权重、目标做标准化，便于算法库复用
"""

from typing import Dict, Any, List


def target_ratio(value: float) -> float:
    return round(value * 100, 2)


DIMENSION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "quality": {
        "label": "质量",
        "description": "一次合格率、返工率、客户投诉等质量表现",
        "weight": 0.15,
        "indicators": [
            {
                "name": "quality_pass_rate",
                "label": "一次合格率",
                "field": "quality_pass_rate",
                "target": 98,
                "unit": "%",
                "direction": "positive",
                "weight": 0.4,
                "analysis_hint": "合格率",
                "suggestion": "提升QC抽检频率、强化过程质量管控"
            },
            {
                "name": "rework_rate",
                "label": "返工率",
                "field": "rework_rate",
                "target": 2,
                "unit": "%",
                "direction": "negative",
                "weight": 0.25,
                "analysis_hint": "返工率",
                "suggestion": "定位返工主因，进行工艺改进与培训"
            },
            {
                "name": "defect_rate",
                "label": "不良率",
                "field": "defect_rate",
                "target": 1,
                "unit": "%",
                "direction": "negative",
                "weight": 0.2,
                "analysis_hint": "不良率",
                "suggestion": "引入防错机制，在线监控不良趋势"
            },
            {
                "name": "customer_complaint_rate",
                "label": "客户投诉率",
                "field": "customer_complaint_rate",
                "target": 0.5,
                "unit": "%",
                "direction": "negative",
                "weight": 0.15,
                "analysis_hint": "投诉率",
                "suggestion": "建立闭环客诉改善，强化售后响应"
            },
        ],
    },
    "cost": {
        "label": "成本",
        "description": "物料、人工、制造费用等成本结构",
        "weight": 0.15,
        "indicators": [
            {
                "name": "material_cost_ratio",
                "label": "物料成本占比",
                "field": "material_cost_ratio",
                "target": 55,
                "unit": "%",
                "direction": "negative",
                "weight": 0.35,
                "suggestion": "采供协同降价、优化BOM用量"
            },
            {
                "name": "labor_cost_ratio",
                "label": "人工成本占比",
                "field": "labor_cost_ratio",
                "target": 18,
                "unit": "%",
                "direction": "negative",
                "weight": 0.25,
                "suggestion": "推进自动化、调优班制配置"
            },
            {
                "name": "overhead_cost_ratio",
                "label": "制造费用占比",
                "field": "overhead_cost_ratio",
                "target": 15,
                "unit": "%",
                "direction": "negative",
                "weight": 0.2,
                "suggestion": "梳理能源/折旧/维修费用，推行精益"
            },
            {
                "name": "cost_reduction_rate",
                "label": "成本降低率",
                "field": "cost_reduction_rate",
                "target": 6,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "制定年度降本清单，闭环跟踪"
            },
        ],
    },
    "delivery": {
        "label": "交期",
        "description": "准时交付与交期稳定性",
        "weight": 0.15,
        "indicators": [
            {
                "name": "on_time_delivery_rate",
                "label": "准时交付率",
                "field": "on_time_delivery_rate",
                "target": 96,
                "unit": "%",
                "direction": "positive",
                "weight": 0.4,
                "suggestion": "建立产销协同机制，滚动确认交期"
            },
            {
                "name": "delivery_cycle_time",
                "label": "交付周期(天)",
                "field": "delivery_cycle_time",
                "target": 12,
                "unit": "天",
                "direction": "negative",
                "weight": 0.25,
                "suggestion": "优化瓶颈工序，缩短排程与物流时间"
            },
            {
                "name": "delay_rate",
                "label": "延期率",
                "field": "delay_rate",
                "target": 3,
                "unit": "%",
                "direction": "negative",
                "weight": 0.2,
                "suggestion": "强化异常预警，建立交付预案"
            },
            {
                "name": "avg_delay_days",
                "label": "平均延期天数",
                "field": "avg_delay_days",
                "target": 1,
                "unit": "天",
                "direction": "negative",
                "weight": 0.15,
                "suggestion": "设置交期缓冲与客户共识机制"
            },
        ],
    },
    "safety": {
        "label": "安全",
        "description": "事故、培训、合规情况",
        "weight": 0.10,
        "indicators": [
            {
                "name": "accident_count",
                "label": "安全事故数",
                "field": "accident_count",
                "target": 0,
                "unit": "起",
                "direction": "negative",
                "weight": 0.4,
                "suggestion": "执行零事故目标，强化日常巡检"
            },
            {
                "name": "safety_training_hours",
                "label": "安全培训小时",
                "field": "safety_training_hours",
                "target": 60,
                "unit": "小时",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "按岗位增加应急/上岗培训频次"
            },
            {
                "name": "safety_compliance_rate",
                "label": "安全合规率",
                "field": "safety_compliance_rate",
                "target": 98,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "结合内外审结果进行整改闭环"
            },
            {
                "name": "safety_inspection_rate",
                "label": "安全检查完成率",
                "field": "safety_inspection_rate",
                "target": 100,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "固化日常检查计划，形成报表"
            },
        ],
    },
    "profit": {
        "label": "利润",
        "description": "毛利/净利/利润增长",
        "weight": 0.15,
        "indicators": [
            {
                "name": "gross_profit_rate",
                "label": "毛利率",
                "field": "gross_profit_rate",
                "target": 28,
                "unit": "%",
                "direction": "positive",
                "weight": 0.3,
                "suggestion": "关注高毛利品类，优化定价策略"
            },
            {
                "name": "net_profit_rate",
                "label": "净利率",
                "field": "net_profit_rate",
                "target": 12,
                "unit": "%",
                "direction": "positive",
                "weight": 0.3,
                "suggestion": "控制期间费用与财务成本"
            },
            {
                "name": "profit_growth_rate",
                "label": "利润增长率",
                "field": "profit_growth_rate",
                "target": 15,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "通过新品/新增市场驱动利润增长"
            },
            {
                "name": "profit_margin",
                "label": "利润率",
                "field": "profit_margin",
                "target": 18,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "拉通端到端成本，看板化追踪利润率"
            },
        ],
    },
    "efficiency": {
        "label": "效率",
        "description": "生产效率、设备OEE、人工效率",
        "weight": 0.15,
        "indicators": [
            {
                "name": "production_efficiency",
                "label": "生产效率",
                "field": "production_efficiency",
                "target": 90,
                "unit": "%",
                "direction": "positive",
                "weight": 0.3,
                "suggestion": "应用精益工具提升产线节拍"
            },
            {
                "name": "equipment_utilization",
                "label": "设备利用率",
                "field": "equipment_utilization",
                "target": 85,
                "unit": "%",
                "direction": "positive",
                "weight": 0.3,
                "suggestion": "建立TPM保全，减少停机"
            },
            {
                "name": "labor_efficiency",
                "label": "人员效率",
                "field": "labor_efficiency",
                "target": 95,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "实施技能矩阵，提升人均产值"
            },
            {
                "name": "oee",
                "label": "设备综合效率(OEE)",
                "field": "oee",
                "target": 80,
                "unit": "%",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "监控OEE三要素，攻关短板"
            },
        ],
    },
    "management": {
        "label": "管理",
        "description": "流程合规、异常闭环、改进措施",
        "weight": 0.10,
        "indicators": [
            {
                "name": "process_compliance_rate",
                "label": "流程合规率",
                "field": "process_compliance_rate",
                "target": 95,
                "unit": "%",
                "direction": "positive",
                "weight": 0.35,
                "suggestion": "推行标准作业书与审计机制"
            },
            {
                "name": "exception_resolution_rate",
                "label": "异常处理率",
                "field": "exception_resolution_rate",
                "target": 92,
                "unit": "%",
                "direction": "positive",
                "weight": 0.3,
                "suggestion": "构建异常看板，落实责任人"
            },
            {
                "name": "improvement_measures_count",
                "label": "改进措施数",
                "field": "improvement_measures_count",
                "target": 12,
                "unit": "项",
                "direction": "positive",
                "weight": 0.2,
                "suggestion": "保持每月至少1项改善闭环"
            },
            {
                "name": "management_efficiency",
                "label": "管理效率评分",
                "field": "management_efficiency",
                "target": 85,
                "unit": "分",
                "direction": "positive",
                "weight": 0.15,
                "suggestion": "提升跨部门协同效率，缩短审批"
            },
        ],
    },
    "technology": {
        "label": "技术",
        "description": "创新、自动化、技术投入",
        "weight": 0.05,
        "indicators": [
            {
                "name": "innovation_projects_count",
                "label": "创新项目数",
                "field": "innovation_projects_count",
                "target": 6,
                "unit": "个",
                "direction": "positive",
                "weight": 0.25,
                "suggestion": "持续导入数字化/智能化项目"
            },
            {
                "name": "process_improvement_rate",
                "label": "工艺改进率",
                "field": "process_improvement_rate",
                "target": 12,
                "unit": "%",
                "direction": "positive",
                "weight": 0.25,
                "suggestion": "定期开展工艺评审，形成改进计划"
            },
            {
                "name": "automation_level",
                "label": "自动化水平",
                "field": "automation_level",
                "target": 75,
                "unit": "%",
                "direction": "positive",
                "weight": 0.25,
                "suggestion": "分阶段推进自动化/机器人应用"
            },
            {
                "name": "technology_investment_ratio",
                "label": "技术投入占比",
                "field": "technology_investment_ratio",
                "target": 6,
                "unit": "%",
                "direction": "positive",
                "weight": 0.25,
                "suggestion": "保持稳定的技术投入预算"
            },
        ],
    },
}


