"""
设备管理高级功能模块
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class EquipmentAdvancedAnalyzer:
    """设备高级分析器"""
    
    def equipment_health_prediction(
        self,
        equipment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        设备健康度预测（新功能）
        
        基于运行时间、故障历史等预测设备健康度
        """
        running_hours = equipment_data.get("running_hours", 5000)
        max_hours = equipment_data.get("max_design_hours", 10000)
        failure_count = equipment_data.get("failure_count", 2)
        last_maintenance_days = equipment_data.get("days_since_maintenance", 30)
        
        # 健康度评分（100分制）
        score = 100
        
        # 使用时长影响（-40分）
        usage_rate = (running_hours / max_hours * 100)
        if usage_rate > 90:
            score -= 40
        elif usage_rate > 75:
            score -= 25
        elif usage_rate > 50:
            score -= 10
        
        # 故障历史影响（-30分）
        if failure_count > 5:
            score -= 30
        elif failure_count > 3:
            score -= 20
        elif failure_count > 0:
            score -= 10
        
        # 维护状态影响（-30分）
        if last_maintenance_days > 90:
            score -= 30
        elif last_maintenance_days > 60:
            score -= 20
        elif last_maintenance_days > 30:
            score -= 10
        
        # 健康度等级
        if score >= 85:
            health_grade = "优秀"
            prediction = "设备状态良好，可正常使用"
            color = "green"
        elif score >= 70:
            health_grade = "良好"
            prediction = "设备基本正常，建议按计划维护"
            color = "blue"
        elif score >= 50:
            health_grade = "一般"
            prediction = "设备有老化迹象，加强监控"
            color = "yellow"
        else:
            health_grade = "较差"
            prediction = "设备状态不佳，建议大修或更换"
            color = "red"
        
        # 维护建议
        recommendations = []
        if last_maintenance_days > 60:
            recommendations.append(f"距上次维护已{last_maintenance_days}天，建议立即维护")
        if usage_rate > 80:
            recommendations.append("设备使用率高，考虑增加备用设备")
        if failure_count > 3:
            recommendations.append("故障次数较多，需要深入排查问题")
        
        return {
            "success": True,
            "equipment_id": equipment_data.get("equipment_id"),
            "health_score": score,
            "health_grade": health_grade,
            "prediction": prediction,
            "color": color,
            "usage_rate": round(usage_rate, 2),
            "failure_count": failure_count,
            "days_since_maintenance": last_maintenance_days,
            "recommendations": recommendations,
            "prediction_date": datetime.now().isoformat()
        }
    
    def maintenance_cost_optimization(
        self,
        maintenance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        维护成本优化（新功能）
        """
        total_cost = sum(m.get("cost", 0) for m in maintenance_history)
        preventive_cost = sum(m.get("cost", 0) for m in maintenance_history if m.get("type") == "preventive")
        reactive_cost = sum(m.get("cost", 0) for m in maintenance_history if m.get("type") == "reactive")
        
        preventive_ratio = (preventive_cost / total_cost * 100) if total_cost > 0 else 0
        
        # 建议
        if preventive_ratio < 60:
            recommendation = "增加预防性维护，减少故障维修"
            optimization_potential = reactive_cost * 0.3
        else:
            recommendation = "保持当前预防性维护比例"
            optimization_potential = 0
        
        return {
            "success": True,
            "total_cost": total_cost,
            "preventive_cost": preventive_cost,
            "reactive_cost": reactive_cost,
            "preventive_ratio": round(preventive_ratio, 2),
            "recommendation": recommendation,
            "cost_optimization_potential": round(optimization_potential, 2)
        }


# 创建默认实例
equipment_advanced_analyzer = EquipmentAdvancedAnalyzer()


