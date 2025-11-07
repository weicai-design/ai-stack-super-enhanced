"""
采购管理高级功能模块
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics


class ProcurementAdvancedAnalyzer:
    """采购高级分析器"""
    
    def supplier_performance_scorecard(
        self,
        supplier_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        供应商绩效评分卡（新功能）
        
        综合评估供应商表现
        """
        score = 0
        
        # 质量评分（40分）
        quality_rate = supplier_data.get("quality_rate", 95)
        if quality_rate >= 98:
            score += 40
        elif quality_rate >= 95:
            score += 35
        elif quality_rate >= 90:
            score += 28
        else:
            score += quality_rate / 3
        
        # 交付评分（30分）
        delivery_rate = supplier_data.get("on_time_delivery_rate", 90)
        if delivery_rate >= 95:
            score += 30
        elif delivery_rate >= 90:
            score += 25
        elif delivery_rate >= 85:
            score += 20
        else:
            score += delivery_rate / 4
        
        # 价格竞争力（20分）
        price_competitiveness = supplier_data.get("price_index", 100)
        if price_competitiveness <= 95:
            score += 20
        elif price_competitiveness <= 100:
            score += 15
        elif price_competitiveness <= 105:
            score += 10
        else:
            score += 5
        
        # 服务评分（10分）
        service_rating = supplier_data.get("service_rating", 8)
        score += service_rating
        
        # 评级
        if score >= 90:
            grade = "A+战略供应商"
        elif score >= 80:
            grade = "A优秀供应商"
        elif score >= 70:
            grade = "B合格供应商"
        else:
            grade = "C需改进供应商"
        
        return {
            "success": True,
            "supplier_id": supplier_data.get("supplier_id"),
            "supplier_name": supplier_data.get("supplier_name"),
            "performance_score": round(score, 2),
            "grade": grade,
            "score_breakdown": {
                "quality": f"{quality_rate}%",
                "delivery": f"{delivery_rate}%",
                "price_competitiveness": price_competitiveness,
                "service": service_rating
            },
            "recommendations": self._get_supplier_recommendations(score, supplier_data)
        }
    
    def procurement_cost_optimization(
        self,
        procurement_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        采购成本优化分析（新功能）
        """
        # 分析采购成本构成
        total_cost = sum(p["amount"] for p in procurement_data)
        
        # 按类别统计
        by_category = {}
        for p in procurement_data:
            cat = p.get("category", "其他")
            by_category[cat] = by_category.get(cat, 0) + p["amount"]
        
        # 找出占比最大的类别
        sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
        
        # 优化建议
        suggestions = []
        for cat, amount in sorted_categories[:3]:
            percentage = (amount / total_cost * 100)
            suggestions.append({
                "category": cat,
                "amount": amount,
                "percentage": round(percentage, 2),
                "optimization_potential": round(amount * 0.05, 2),  # 假设5%优化空间
                "actions": ["集中采购降价", "寻找替代供应商", "优化采购批量"]
            })
        
        return {
            "success": True,
            "total_procurement_cost": total_cost,
            "cost_by_category": by_category,
            "optimization_suggestions": suggestions,
            "total_optimization_potential": round(total_cost * 0.05, 2)
        }
    
    def _get_supplier_recommendations(self, score: float, data: Dict) -> List[str]:
        """生成供应商建议"""
        recs = []
        if score < 80:
            recs.append("供应商表现有待提升，建议沟通改进")
        if data.get("quality_rate", 95) < 95:
            recs.append("加强质量管控")
        if data.get("on_time_delivery_rate", 90) < 90:
            recs.append("改善交付准时性")
        return recs


# 创建默认实例
procurement_advanced_analyzer = ProcurementAdvancedAnalyzer()


