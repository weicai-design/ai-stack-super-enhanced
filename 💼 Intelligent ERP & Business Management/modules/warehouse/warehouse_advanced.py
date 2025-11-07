"""
仓储管理高级功能模块
"""

from typing import Dict, Any, List
from datetime import datetime
import statistics


class WarehouseAdvancedAnalyzer:
    """仓储高级分析器"""
    
    def storage_optimization_analysis(
        self,
        warehouse_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        库位优化分析（新功能）
        
        分析仓库空间利用率并提供优化建议
        """
        total_capacity = warehouse_data.get("total_capacity", 10000)
        used_capacity = warehouse_data.get("used_capacity", 7500)
        
        utilization_rate = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
        
        # 评估
        if utilization_rate > 90:
            status = "接近满仓"
            recommendation = "考虑扩容或优化库存"
            color = "red"
        elif utilization_rate > 75:
            status = "利用率良好"
            recommendation = "保持当前水平"
            color = "green"
        elif utilization_rate > 50:
            status = "利用率适中"
            recommendation = "可适当增加库存"
            color = "blue"
        else:
            status = "利用率偏低"
            recommendation = "考虑减少租赁面积或增加业务"
            color = "yellow"
        
        return {
            "success": True,
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "available_capacity": total_capacity - used_capacity,
            "utilization_rate": round(utilization_rate, 2),
            "status": status,
            "color": color,
            "recommendation": recommendation,
            "optimization_suggestions": [
                "实施ABC分类管理",
                "优化库位分配策略",
                "清理呆滞库存"
            ]
        }
    
    def inventory_turnover_analysis(
        self,
        inventory_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        库存周转分析（新功能）
        """
        slow_moving = []
        fast_moving = []
        
        for item in inventory_data:
            turnover_days = item.get("average_stay_days", 60)
            
            if turnover_days > 90:
                slow_moving.append(item)
            elif turnover_days < 30:
                fast_moving.append(item)
        
        return {
            "success": True,
            "slow_moving_items": len(slow_moving),
            "fast_moving_items": len(fast_moving),
            "recommendations": [
                f"优化{len(slow_moving)}个慢周转物料",
                "增加快周转物料库存"
            ]
        }


# 创建默认实例
warehouse_advanced_analyzer = WarehouseAdvancedAnalyzer()


