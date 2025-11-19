"""
ERP业务流程8维度深度分析系统
针对制造型企业的8个核心维度：质量/成本/交期/安全/利润/效率/管理/技术
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

try:
    from analytics.erp_dimension_templates import DIMENSION_TEMPLATES
    from analytics.erp_dimension_algorithms import evaluate_dimension, classify_level
except ImportError:
    # 兼容性导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from analytics.erp_dimension_templates import DIMENSION_TEMPLATES
    from analytics.erp_dimension_algorithms import evaluate_dimension, classify_level


class ERPDimensionLevel(str, Enum):
    """ERP维度评级"""
    EXCELLENT = "excellent"      # 优秀 (90-100分)
    GOOD = "good"               # 良好 (80-89分)
    AVERAGE = "average"         # 一般 (70-79分)
    POOR = "poor"               # 较差 (60-69分)
    CRITICAL = "critical"       # 危险 (<60分)


class ERPEightDimensionsAnalyzer:
    """
    ERP业务流程8维度分析器
    
    8个核心维度：
    1. 质量 (Quality) - 产品质量、合格率、返工率
    2. 成本 (Cost) - 生产成本、物料成本、人工成本
    3. 交期 (Delivery) - 准时交付率、交期达成率
    4. 安全 (Safety) - 安全事故、安全培训、合规性
    5. 利润 (Profit) - 毛利率、净利率、利润率
    6. 效率 (Efficiency) - 生产效率、设备利用率、人员效率
    7. 管理 (Management) - 流程管理、异常处理、改进措施
    8. 技术 (Technology) - 技术创新、工艺改进、自动化水平
    """
    
    def __init__(self):
        """初始化8维度分析器"""
        self.templates = DIMENSION_TEMPLATES
    
    def analyze(self, erp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行8维度分析
        
        Args:
            erp_data: ERP业务数据
        
        Returns:
            8维度分析结果
        """
        results = {}
        
        for dim_key in self.templates.keys():
            results[dim_key] = evaluate_dimension(erp_data, self.templates[dim_key])
        
        # 计算综合得分
        overall_score = self._calculate_overall_score(results)
        
        # 生成综合报告
        report = self._generate_comprehensive_report(results, overall_score)
        
        return {
            "dimensions": results,
            "overall_score": overall_score,
            "overall_level": self._get_level(overall_score),
            "report": report,
            "timestamp": datetime.now().isoformat(),
            "recommendations": self._generate_recommendations(results)
        }
    
    def _analyze_quality(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["quality"])

    def _analyze_cost(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["cost"])

    def _analyze_delivery(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["delivery"])

    def _analyze_safety(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["safety"])

    def _analyze_profit(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["profit"])

    def _analyze_efficiency(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["efficiency"])
    
    def _analyze_management(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["management"])
    
    def _analyze_technology(self, data: Dict) -> Dict:
        return evaluate_dimension(data, self.templates["technology"])
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """计算综合得分"""
        weights = {
            "quality": 0.15,        # 质量 15%
            "cost": 0.15,           # 成本 15%
            "delivery": 0.15,       # 交期 15%
            "safety": 0.10,         # 安全 10%
            "profit": 0.15,         # 利润 15%
            "efficiency": 0.15,    # 效率 15%
            "management": 0.10,    # 管理 10%
            "technology": 0.05     # 技术 5%
        }
        
        total_score = sum(
            results[dim]["score"] * weight
            for dim, weight in weights.items()
            if dim in results
        )
        
        return round(total_score, 2)
    
    def _get_level(self, score: float) -> str:
        """根据得分获取等级"""
        level = classify_level(score)
        return ERPDimensionLevel(level)
    
    def _generate_comprehensive_report(self, results: Dict, overall_score: float) -> str:
        """生成综合分析报告"""
        report = f"# ERP业务流程8维度分析报告\n\n"
        report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**综合得分**: {overall_score:.2f}分\n"
        report += f"**综合评级**: {self._get_level_name(self._get_level(overall_score))}\n\n"
        
        report += "## 📊 各维度得分\n\n"
        for dim_key, dim_data in results.items():
            report += f"### {dim_data['dimension']} - {dim_data['score']:.1f}分 ({self._get_level_name(dim_data['level'])})\n\n"
            report += f"{dim_data['analysis']}\n\n"
        
        return report
    
    def _get_level_name(self, level: str) -> str:
        """获取等级中文名"""
        names = {
            "excellent": "优秀",
            "good": "良好",
            "average": "一般",
            "poor": "较差",
            "critical": "危险"
        }
        return names.get(level, "未知")
    
    def analyze_stage_dimensions(
        self,
        stage_id: str,
        stage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析特定环节的8维度表现
        
        Args:
            stage_id: 环节ID
            stage_data: 环节数据
            
        Returns:
            环节8维度分析结果
        """
        # 根据环节类型调整权重
        stage_weights = self._get_stage_weights(stage_id)
        
        # 执行分析
        results = {}
        for dim_key in self.templates.keys():
            dim_result = evaluate_dimension(stage_data, self.templates[dim_key])
            # 应用环节权重
            dim_result["weighted_score"] = dim_result["score"] * stage_weights.get(dim_key, 1.0)
            results[dim_key] = dim_result
        
        # 计算环节综合得分
        overall_score = sum(
            r["weighted_score"] for r in results.values()
        ) / len(results) if results else 0.0
        
        return {
            "stage_id": stage_id,
            "dimensions": results,
            "overall_score": round(overall_score, 2),
            "overall_level": self._get_level(overall_score),
            "stage_specific_recommendations": self._generate_stage_recommendations(stage_id, results),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _get_stage_weights(self, stage_id: str) -> Dict[str, float]:
        """根据环节类型获取维度权重"""
        # 不同环节关注不同的维度
        weights_map = {
            "market_research": {
                "quality": 0.10, "cost": 0.15, "delivery": 0.10, "safety": 0.05,
                "profit": 0.20, "efficiency": 0.15, "management": 0.15, "technology": 0.10
            },
            "customer_development": {
                "quality": 0.10, "cost": 0.10, "delivery": 0.15, "safety": 0.05,
                "profit": 0.20, "efficiency": 0.15, "management": 0.15, "technology": 0.10
            },
            "production": {
                "quality": 0.25, "cost": 0.20, "delivery": 0.15, "safety": 0.15,
                "profit": 0.10, "efficiency": 0.10, "management": 0.05, "technology": 0.00
            },
            "quality_check": {
                "quality": 0.40, "cost": 0.10, "delivery": 0.10, "safety": 0.10,
                "profit": 0.10, "efficiency": 0.10, "management": 0.05, "technology": 0.05
            },
        }
        
        # 默认权重
        default_weights = {
            "quality": 0.15, "cost": 0.15, "delivery": 0.15, "safety": 0.10,
            "profit": 0.15, "efficiency": 0.15, "management": 0.10, "technology": 0.05
        }
        
        return weights_map.get(stage_id, default_weights)
    
    def _generate_stage_recommendations(
        self,
        stage_id: str,
        results: Dict
    ) -> List[str]:
        """生成环节特定的改进建议"""
        recommendations = []
        
        # 找出得分最低的维度
        min_dim = min(results.items(), key=lambda x: x[1]["score"])
        if min_dim[1]["score"] < 70:
            recommendations.append(
                f"环节 {stage_id} 的 {min_dim[1]['dimension']} 维度得分较低 ({min_dim[1]['score']:.1f}分)，"
                f"建议优先改进：{min_dim[1].get('suggestion', '')}"
            )
        
        # 环节特定建议
        stage_specific = {
            "production": "建议优化生产流程，提升设备利用率",
            "quality_check": "建议加强质量检验标准，降低不良率",
            "procurement_receipt": "建议优化采购周期，提升到料及时率",
        }
        
        if stage_id in stage_specific:
            recommendations.append(stage_specific[stage_id])
        
        return recommendations
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 找出得分最低的3个维度
        sorted_dims = sorted(results.items(), key=lambda x: x[1]['score'])
        
        for dim_key, dim_data in sorted_dims[:3]:
            if dim_data.get('suggestions'):
                recommendations.extend(dim_data['suggestions'][:2])
        
        return recommendations[:5]
    
    # ==================== 建议生成方法 ====================
    
    def _get_quality_suggestions(self, score: float, pass_rate: float, rework_rate: float) -> List[str]:
        """质量改进建议"""
        suggestions = []
        if pass_rate < 95:
            suggestions.append("💡 建议加强质量检验，提高合格率")
        if rework_rate > 5:
            suggestions.append("🔧 建议优化生产工艺，降低返工率")
        return suggestions
    
    def _get_cost_suggestions(self, score: float, material_ratio: float, labor_ratio: float) -> List[str]:
        """成本改进建议"""
        suggestions = []
        if material_ratio > 0.7:
            suggestions.append("💰 建议优化采购策略，降低物料成本")
        if labor_ratio > 0.3:
            suggestions.append("👥 建议提高自动化水平，降低人工成本")
        return suggestions
    
    def _get_delivery_suggestions(self, score: float, on_time_rate: float, delay_rate: float) -> List[str]:
        """交期改进建议"""
        suggestions = []
        if on_time_rate < 90:
            suggestions.append("⏰ 建议优化生产计划，提高准时交付率")
        if delay_rate > 10:
            suggestions.append("📅 建议加强交期管理，减少延期")
        return suggestions
    
    def _get_safety_suggestions(self, score: float, accident_count: int, training_hours: int) -> List[str]:
        """安全改进建议"""
        suggestions = []
        if accident_count > 0:
            suggestions.append("⚠️ 建议加强安全培训，减少安全事故")
        if training_hours < 40:
            suggestions.append("📚 建议增加安全培训时间")
        return suggestions
    
    def _get_profit_suggestions(self, score: float, gross_rate: float, net_rate: float) -> List[str]:
        """利润改进建议"""
        suggestions = []
        if gross_rate < 20:
            suggestions.append("💹 建议提高产品定价或降低成本")
        if net_rate < 8:
            suggestions.append("📊 建议优化费用结构，提高净利率")
        return suggestions
    
    def _get_efficiency_suggestions(self, score: float, production_eff: float, equipment_util: float) -> List[str]:
        """效率改进建议"""
        suggestions = []
        if production_eff < 80:
            suggestions.append("⚙️ 建议优化生产流程，提高生产效率")
        if equipment_util < 75:
            suggestions.append("🔧 建议提高设备利用率")
        return suggestions
    
    def _get_management_suggestions(self, score: float, compliance_rate: float, exception_rate: float) -> List[str]:
        """管理改进建议"""
        suggestions = []
        if compliance_rate < 90:
            suggestions.append("📋 建议加强流程管理，提高合规率")
        if exception_rate < 85:
            suggestions.append("🔍 建议完善异常处理机制")
        return suggestions
    
    def _get_technology_suggestions(self, score: float, automation_level: float, investment_ratio: float) -> List[str]:
        """技术改进建议"""
        suggestions = []
        if automation_level < 60:
            suggestions.append("🤖 建议提高自动化水平")
        if investment_ratio < 0.05:
            suggestions.append("💡 建议增加技术投入")
        return suggestions


    def get_priority_improvements(
        self,
        dimensions_results: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        获取优先级改进建议
        
        Args:
            dimensions_results: 各维度分析结果
            
        Returns:
            优先级改进建议列表
        """
        improvements = []
        
        # 按得分排序，找出需要改进的维度
        sorted_dims = sorted(
            dimensions_results.items(),
            key=lambda x: x[1].get("score", 0)
        )
        
        for dim_key, result in sorted_dims[:3]:  # 取得分最低的3个维度
            dim_name = self.dimensions[dim_key]
            score = result.get("score", 0)
            suggestions = result.get("suggestions", [])
            
            if suggestions:
                improvements.append({
                    "dimension": dim_name,
                    "dimension_key": dim_key,
                    "score": score,
                    "priority": "high" if score < 70 else "medium" if score < 80 else "low",
                    "suggestions": suggestions[:3]  # 取前3条建议
                })
        
        return improvements


# 全局实例
erp_eight_dimensions_analyzer = ERPEightDimensionsAnalyzer()

