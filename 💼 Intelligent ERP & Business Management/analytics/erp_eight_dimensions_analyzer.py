"""
ERP业务流程8维度深度分析系统
针对制造型企业的8个核心维度：质量/成本/交期/安全/利润/效率/管理/技术
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


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
        self.dimensions = {
            "quality": "质量",
            "cost": "成本",
            "delivery": "交期",
            "safety": "安全",
            "profit": "利润",
            "efficiency": "效率",
            "management": "管理",
            "technology": "技术"
        }
    
    def analyze(self, erp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行8维度分析
        
        Args:
            erp_data: ERP业务数据
        
        Returns:
            8维度分析结果
        """
        results = {}
        
        # 1. 质量维度分析
        results["quality"] = self._analyze_quality(erp_data)
        
        # 2. 成本维度分析
        results["cost"] = self._analyze_cost(erp_data)
        
        # 3. 交期维度分析
        results["delivery"] = self._analyze_delivery(erp_data)
        
        # 4. 安全维度分析
        results["safety"] = self._analyze_safety(erp_data)
        
        # 5. 利润维度分析
        results["profit"] = self._analyze_profit(erp_data)
        
        # 6. 效率维度分析
        results["efficiency"] = self._analyze_efficiency(erp_data)
        
        # 7. 管理维度分析
        results["management"] = self._analyze_management(erp_data)
        
        # 8. 技术维度分析
        results["technology"] = self._analyze_technology(erp_data)
        
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
        """维度1：质量分析"""
        # 提取质量指标
        pass_rate = data.get("quality_pass_rate", 95.0)  # 合格率
        rework_rate = data.get("rework_rate", 3.0)  # 返工率
        defect_rate = data.get("defect_rate", 2.0)  # 不良率
        customer_complaint_rate = data.get("customer_complaint_rate", 1.0)  # 客户投诉率
        
        # 计算得分
        score_pass = min(100, pass_rate)
        score_rework = max(0, 100 - rework_rate * 10)  # 返工率越低越好
        score_defect = max(0, 100 - defect_rate * 20)  # 不良率越低越好
        score_complaint = max(0, 100 - customer_complaint_rate * 30)  # 投诉率越低越好
        
        score = (score_pass * 0.4 + score_rework * 0.3 + score_defect * 0.2 + score_complaint * 0.1)
        
        return {
            "dimension": "质量",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "pass_rate": round(pass_rate, 2),
                "rework_rate": round(rework_rate, 2),
                "defect_rate": round(defect_rate, 2),
                "customer_complaint_rate": round(customer_complaint_rate, 2)
            },
            "analysis": f"合格率{pass_rate:.1f}%，返工率{rework_rate:.1f}%，不良率{defect_rate:.1f}%",
            "suggestions": self._get_quality_suggestions(score, pass_rate, rework_rate)
        }
    
    def _analyze_cost(self, data: Dict) -> Dict:
        """维度2：成本分析"""
        # 提取成本指标
        material_cost_ratio = data.get("material_cost_ratio", 0.6)  # 物料成本占比
        labor_cost_ratio = data.get("labor_cost_ratio", 0.2)  # 人工成本占比
        overhead_cost_ratio = data.get("overhead_cost_ratio", 0.2)  # 制造费用占比
        cost_reduction_rate = data.get("cost_reduction_rate", 0.05)  # 成本降低率
        
        # 计算得分（成本占比越低越好，成本降低率越高越好）
        score_material = max(0, 100 - material_cost_ratio * 100)
        score_labor = max(0, 100 - labor_cost_ratio * 200)
        score_overhead = max(0, 100 - overhead_cost_ratio * 200)
        score_reduction = min(100, cost_reduction_rate * 1000)  # 成本降低率越高越好
        
        score = (score_material * 0.4 + score_labor * 0.3 + score_overhead * 0.2 + score_reduction * 0.1)
        
        return {
            "dimension": "成本",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "material_cost_ratio": round(material_cost_ratio * 100, 2),
                "labor_cost_ratio": round(labor_cost_ratio * 100, 2),
                "overhead_cost_ratio": round(overhead_cost_ratio * 100, 2),
                "cost_reduction_rate": round(cost_reduction_rate * 100, 2)
            },
            "analysis": f"物料成本占比{material_cost_ratio*100:.1f}%，人工成本占比{labor_cost_ratio*100:.1f}%",
            "suggestions": self._get_cost_suggestions(score, material_cost_ratio, labor_cost_ratio)
        }
    
    def _analyze_delivery(self, data: Dict) -> Dict:
        """维度3：交期分析"""
        # 提取交期指标
        on_time_delivery_rate = data.get("on_time_delivery_rate", 90.0)  # 准时交付率
        delivery_cycle_time = data.get("delivery_cycle_time", 15)  # 交付周期（天）
        delay_rate = data.get("delay_rate", 5.0)  # 延期率
        avg_delay_days = data.get("avg_delay_days", 2.0)  # 平均延期天数
        
        # 计算得分
        score_on_time = on_time_delivery_rate
        score_cycle = max(0, 100 - (delivery_cycle_time - 10) * 5)  # 周期越短越好
        score_delay = max(0, 100 - delay_rate * 10)  # 延期率越低越好
        score_delay_days = max(0, 100 - avg_delay_days * 20)  # 延期天数越少越好
        
        score = (score_on_time * 0.4 + score_cycle * 0.2 + score_delay * 0.3 + score_delay_days * 0.1)
        
        return {
            "dimension": "交期",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "on_time_delivery_rate": round(on_time_delivery_rate, 2),
                "delivery_cycle_time": round(delivery_cycle_time, 1),
                "delay_rate": round(delay_rate, 2),
                "avg_delay_days": round(avg_delay_days, 1)
            },
            "analysis": f"准时交付率{on_time_delivery_rate:.1f}%，交付周期{delivery_cycle_time:.1f}天",
            "suggestions": self._get_delivery_suggestions(score, on_time_delivery_rate, delay_rate)
        }
    
    def _analyze_safety(self, data: Dict) -> Dict:
        """维度4：安全分析"""
        # 提取安全指标
        accident_count = data.get("accident_count", 0)  # 事故次数
        safety_training_hours = data.get("safety_training_hours", 40)  # 安全培训小时数
        safety_compliance_rate = data.get("safety_compliance_rate", 95.0)  # 安全合规率
        safety_inspection_rate = data.get("safety_inspection_rate", 100.0)  # 安全检查完成率
        
        # 计算得分（事故越少越好，培训越多越好）
        score_accident = max(0, 100 - accident_count * 20)  # 无事故100分
        score_training = min(100, safety_training_hours * 2)  # 培训小时数
        score_compliance = safety_compliance_rate
        score_inspection = safety_inspection_rate
        
        score = (score_accident * 0.4 + score_training * 0.2 + score_compliance * 0.2 + score_inspection * 0.2)
        
        return {
            "dimension": "安全",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "accident_count": accident_count,
                "safety_training_hours": safety_training_hours,
                "safety_compliance_rate": round(safety_compliance_rate, 2),
                "safety_inspection_rate": round(safety_inspection_rate, 2)
            },
            "analysis": f"安全事故{accident_count}次，安全培训{safety_training_hours}小时，合规率{safety_compliance_rate:.1f}%",
            "suggestions": self._get_safety_suggestions(score, accident_count, safety_training_hours)
        }
    
    def _analyze_profit(self, data: Dict) -> Dict:
        """维度5：利润分析"""
        # 提取利润指标
        gross_profit_rate = data.get("gross_profit_rate", 25.0)  # 毛利率
        net_profit_rate = data.get("net_profit_rate", 10.0)  # 净利率
        profit_growth_rate = data.get("profit_growth_rate", 0.15)  # 利润增长率
        profit_margin = data.get("profit_margin", 15.0)  # 利润率
        
        # 计算得分
        score_gross = min(100, gross_profit_rate * 3)  # 毛利率越高越好
        score_net = min(100, net_profit_rate * 8)  # 净利率越高越好
        score_growth = min(100, profit_growth_rate * 500 + 50)  # 增长率越高越好
        score_margin = min(100, profit_margin * 5)  # 利润率越高越好
        
        score = (score_gross * 0.3 + score_net * 0.3 + score_growth * 0.2 + score_margin * 0.2)
        
        return {
            "dimension": "利润",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "gross_profit_rate": round(gross_profit_rate, 2),
                "net_profit_rate": round(net_profit_rate, 2),
                "profit_growth_rate": round(profit_growth_rate * 100, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "analysis": f"毛利率{gross_profit_rate:.1f}%，净利率{net_profit_rate:.1f}%，利润增长率{profit_growth_rate*100:.1f}%",
            "suggestions": self._get_profit_suggestions(score, gross_profit_rate, net_profit_rate)
        }
    
    def _analyze_efficiency(self, data: Dict) -> Dict:
        """维度6：效率分析"""
        # 提取效率指标
        production_efficiency = data.get("production_efficiency", 85.0)  # 生产效率
        equipment_utilization = data.get("equipment_utilization", 80.0)  # 设备利用率
        labor_efficiency = data.get("labor_efficiency", 90.0)  # 人员效率
        oee = data.get("oee", 75.0)  # 设备综合效率
        
        # 计算得分
        score_production = production_efficiency
        score_equipment = equipment_utilization
        score_labor = labor_efficiency
        score_oee = oee
        
        score = (score_production * 0.3 + score_equipment * 0.3 + score_labor * 0.2 + score_oee * 0.2)
        
        return {
            "dimension": "效率",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "production_efficiency": round(production_efficiency, 2),
                "equipment_utilization": round(equipment_utilization, 2),
                "labor_efficiency": round(labor_efficiency, 2),
                "oee": round(oee, 2)
            },
            "analysis": f"生产效率{production_efficiency:.1f}%，设备利用率{equipment_utilization:.1f}%，OEE{oee:.1f}%",
            "suggestions": self._get_efficiency_suggestions(score, production_efficiency, equipment_utilization)
        }
    
    def _analyze_management(self, data: Dict) -> Dict:
        """维度7：管理分析"""
        # 提取管理指标
        process_compliance_rate = data.get("process_compliance_rate", 90.0)  # 流程合规率
        exception_resolution_rate = data.get("exception_resolution_rate", 85.0)  # 异常处理率
        improvement_measures_count = data.get("improvement_measures_count", 10)  # 改进措施数
        management_efficiency = data.get("management_efficiency", 80.0)  # 管理效率
        
        # 计算得分
        score_process = process_compliance_rate
        score_exception = exception_resolution_rate
        score_improvement = min(100, improvement_measures_count * 10)  # 改进措施越多越好
        score_management = management_efficiency
        
        score = (score_process * 0.3 + score_exception * 0.3 + score_improvement * 0.2 + score_management * 0.2)
        
        return {
            "dimension": "管理",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "process_compliance_rate": round(process_compliance_rate, 2),
                "exception_resolution_rate": round(exception_resolution_rate, 2),
                "improvement_measures_count": improvement_measures_count,
                "management_efficiency": round(management_efficiency, 2)
            },
            "analysis": f"流程合规率{process_compliance_rate:.1f}%，异常处理率{exception_resolution_rate:.1f}%，改进措施{improvement_measures_count}项",
            "suggestions": self._get_management_suggestions(score, process_compliance_rate, exception_resolution_rate)
        }
    
    def _analyze_technology(self, data: Dict) -> Dict:
        """维度8：技术分析"""
        # 提取技术指标
        innovation_projects_count = data.get("innovation_projects_count", 5)  # 创新项目数
        process_improvement_rate = data.get("process_improvement_rate", 10.0)  # 工艺改进率
        automation_level = data.get("automation_level", 60.0)  # 自动化水平
        technology_investment_ratio = data.get("technology_investment_ratio", 0.05)  # 技术投入占比
        
        # 计算得分
        score_innovation = min(100, innovation_projects_count * 20)  # 创新项目越多越好
        score_improvement = min(100, process_improvement_rate * 8)  # 改进率越高越好
        score_automation = automation_level  # 自动化水平越高越好
        score_investment = min(100, technology_investment_ratio * 1000)  # 投入占比越高越好
        
        score = (score_innovation * 0.25 + score_improvement * 0.25 + score_automation * 0.3 + score_investment * 0.2)
        
        return {
            "dimension": "技术",
            "score": round(score, 2),
            "level": self._get_level(score),
            "indicators": {
                "innovation_projects_count": innovation_projects_count,
                "process_improvement_rate": round(process_improvement_rate, 2),
                "automation_level": round(automation_level, 2),
                "technology_investment_ratio": round(technology_investment_ratio * 100, 2)
            },
            "analysis": f"创新项目{innovation_projects_count}个，工艺改进率{process_improvement_rate:.1f}%，自动化水平{automation_level:.1f}%",
            "suggestions": self._get_technology_suggestions(score, automation_level, technology_investment_ratio)
        }
    
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
        )
        
        return round(total_score, 2)
    
    def _get_level(self, score: float) -> str:
        """根据得分获取等级"""
        if score >= 90:
            return ERPDimensionLevel.EXCELLENT
        elif score >= 80:
            return ERPDimensionLevel.GOOD
        elif score >= 70:
            return ERPDimensionLevel.AVERAGE
        elif score >= 60:
            return ERPDimensionLevel.POOR
        else:
            return ERPDimensionLevel.CRITICAL
    
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

