"""
关键因素识别器
智能识别对"利润=产出-投入"的关键影响因素
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import statistics


class KeyFactorIdentifier:
    """关键因素识别器"""
    
    def __init__(self):
        """初始化识别器"""
        self.factor_history = []
        self.sensitivity_analysis = {}
    
    def identify_key_factors(
        self,
        business_data: Dict[str, Any],
        analysis_period: str = "年度"
    ) -> Dict[str, Any]:
        """
        识别关键影响因素
        
        Args:
            business_data: 业务数据 {
                "revenue": 10000000,  # 产出
                "costs": {
                    "material": 4000000,
                    "labor": 2000000,
                    "manufacturing": 1000000,
                    "sales_expense": 500000,
                    "admin_expense": 300000,
                    "financial_expense": 200000
                },
                "profit": 2000000,
                "historical_data": []  # 可选：历史数据用于趋势分析
            }
            analysis_period: 分析周期
        
        Returns:
            关键因素分析
        """
        revenue = business_data["revenue"]
        costs = business_data["costs"]
        profit = business_data["profit"]
        
        # 1. 成本结构分析
        cost_structure = self._analyze_cost_structure(revenue, costs, profit)
        
        # 2. 敏感性分析
        sensitivity = self._perform_sensitivity_analysis(revenue, costs)
        
        # 3. 因素重要性排名
        factor_ranking = self._rank_factors_by_importance(
            cost_structure,
            sensitivity
        )
        
        # 4. 关键因素识别
        key_factors = self._identify_critical_factors(
            factor_ranking,
            cost_structure
        )
        
        # 5. 优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            key_factors,
            cost_structure
        )
        
        # 6. 趋势分析（如果有历史数据）
        trend_analysis = None
        if "historical_data" in business_data and business_data["historical_data"]:
            trend_analysis = self._analyze_trends(business_data["historical_data"])
        
        result = {
            "success": True,
            "analysis_period": analysis_period,
            "cost_structure": cost_structure,
            "sensitivity_analysis": sensitivity,
            "factor_ranking": factor_ranking,
            "key_factors": key_factors,
            "optimization_suggestions": optimization_suggestions,
            "trend_analysis": trend_analysis,
            "analyzed_at": datetime.now().isoformat()
        }
        
        self.factor_history.append(result)
        return result
    
    def _analyze_cost_structure(
        self,
        revenue: float,
        costs: Dict[str, float],
        profit: float
    ) -> Dict[str, Any]:
        """分析成本结构"""
        total_costs = sum(costs.values())
        
        # 计算各成本占比
        cost_ratios = {}
        for cost_type, cost_value in costs.items():
            cost_ratios[cost_type] = {
                "amount": cost_value,
                "percent_of_revenue": round((cost_value / revenue * 100), 2) if revenue > 0 else 0,
                "percent_of_total_cost": round((cost_value / total_costs * 100), 2) if total_costs > 0 else 0
            }
        
        # 利润率
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        
        return {
            "total_revenue": revenue,
            "total_costs": total_costs,
            "total_profit": profit,
            "profit_margin_percent": round(profit_margin, 2),
            "cost_breakdown": cost_ratios,
            "cost_ratio": round((total_costs / revenue * 100), 2) if revenue > 0 else 0
        }
    
    def _perform_sensitivity_analysis(
        self,
        revenue: float,
        costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        敏感性分析
        分析各因素变化对利润的影响
        """
        base_profit = revenue - sum(costs.values())
        
        sensitivity_results = {}
        
        # 对每个成本因素进行±10%的敏感性测试
        for cost_type, cost_value in costs.items():
            # 增加10%
            increased_cost = cost_value * 1.1
            new_costs_increased = {k: v for k, v in costs.items()}
            new_costs_increased[cost_type] = increased_cost
            profit_if_increased = revenue - sum(new_costs_increased.values())
            
            # 减少10%
            decreased_cost = cost_value * 0.9
            new_costs_decreased = {k: v for k, v in costs.items()}
            new_costs_decreased[cost_type] = decreased_cost
            profit_if_decreased = revenue - sum(new_costs_decreased.values())
            
            # 计算敏感系数
            profit_change_increase = profit_if_increased - base_profit
            profit_change_decrease = profit_if_decreased - base_profit
            
            # 敏感系数 = (利润变化% / 成本变化%)
            sensitivity_coefficient = abs(
                (profit_change_increase / base_profit) / 0.1
            ) if base_profit != 0 else 0
            
            sensitivity_results[cost_type] = {
                "base_cost": cost_value,
                "increase_10_percent": {
                    "new_cost": increased_cost,
                    "new_profit": round(profit_if_increased, 2),
                    "profit_change": round(profit_change_increase, 2),
                    "profit_change_percent": round((profit_change_increase / base_profit * 100), 2) if base_profit != 0 else 0
                },
                "decrease_10_percent": {
                    "new_cost": decreased_cost,
                    "new_profit": round(profit_if_decreased, 2),
                    "profit_change": round(profit_change_decrease, 2),
                    "profit_change_percent": round((profit_change_decrease / base_profit * 100), 2) if base_profit != 0 else 0
                },
                "sensitivity_coefficient": round(sensitivity_coefficient, 3),
                "sensitivity_level": self._get_sensitivity_level(sensitivity_coefficient)
            }
        
        # 收入敏感性
        revenue_sensitivity = self._analyze_revenue_sensitivity(revenue, sum(costs.values()))
        sensitivity_results["revenue"] = revenue_sensitivity
        
        return {
            "base_profit": base_profit,
            "factors": sensitivity_results
        }
    
    def _get_sensitivity_level(self, coefficient: float) -> str:
        """获取敏感度等级"""
        if coefficient > 2:
            return "极高敏感"
        elif coefficient > 1:
            return "高敏感"
        elif coefficient > 0.5:
            return "中敏感"
        else:
            return "低敏感"
    
    def _analyze_revenue_sensitivity(
        self,
        revenue: float,
        total_costs: float
    ) -> Dict[str, Any]:
        """分析收入敏感性"""
        base_profit = revenue - total_costs
        
        # 收入增加10%
        new_revenue_increase = revenue * 1.1
        profit_increase = new_revenue_increase - total_costs
        
        # 收入减少10%
        new_revenue_decrease = revenue * 0.9
        profit_decrease = new_revenue_decrease - total_costs
        
        return {
            "base_revenue": revenue,
            "increase_10_percent": {
                "new_revenue": new_revenue_increase,
                "new_profit": round(profit_increase, 2),
                "profit_change": round(profit_increase - base_profit, 2),
                "profit_change_percent": round(((profit_increase - base_profit) / base_profit * 100), 2) if base_profit != 0 else 0
            },
            "decrease_10_percent": {
                "new_revenue": new_revenue_decrease,
                "new_profit": round(profit_decrease, 2),
                "profit_change": round(profit_decrease - base_profit, 2),
                "profit_change_percent": round(((profit_decrease - base_profit) / base_profit * 100), 2) if base_profit != 0 else 0
            },
            "sensitivity_level": "极高敏感"  # 收入通常是最敏感的因素
        }
    
    def _rank_factors_by_importance(
        self,
        cost_structure: Dict[str, Any],
        sensitivity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """根据重要性对因素排名"""
        factors = []
        
        # 收入因素
        if "revenue" in sensitivity["factors"]:
            rev_sens = sensitivity["factors"]["revenue"]
            factors.append({
                "factor_name": "收入（产出）",
                "factor_type": "revenue",
                "amount": cost_structure["total_revenue"],
                "percent_of_revenue": 100,
                "sensitivity_level": rev_sens["sensitivity_level"],
                "importance_score": 100  # 收入最重要
            })
        
        # 成本因素
        for cost_type, cost_info in cost_structure["cost_breakdown"].items():
            if cost_type in sensitivity["factors"]:
                sens_info = sensitivity["factors"][cost_type]
                
                # 重要性得分 = 占收入比例 × 敏感系数
                importance_score = (
                    cost_info["percent_of_revenue"] * 
                    sens_info["sensitivity_coefficient"]
                )
                
                factors.append({
                    "factor_name": self._get_factor_name_chinese(cost_type),
                    "factor_type": cost_type,
                    "amount": cost_info["amount"],
                    "percent_of_revenue": cost_info["percent_of_revenue"],
                    "sensitivity_level": sens_info["sensitivity_level"],
                    "sensitivity_coefficient": sens_info["sensitivity_coefficient"],
                    "importance_score": round(importance_score, 2)
                })
        
        # 按重要性得分排序
        factors.sort(key=lambda x: x["importance_score"], reverse=True)
        
        # 添加排名
        for i, factor in enumerate(factors, 1):
            factor["rank"] = i
        
        return factors
    
    def _get_factor_name_chinese(self, factor_type: str) -> str:
        """获取因素中文名"""
        names = {
            "material": "材料费用",
            "labor": "人工费用",
            "manufacturing": "制造费用",
            "sales_expense": "销售费用",
            "admin_expense": "管理费用",
            "financial_expense": "财务费用"
        }
        return names.get(factor_type, factor_type)
    
    def _identify_critical_factors(
        self,
        factor_ranking: List[Dict[str, Any]],
        cost_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """识别关键因素"""
        # 前3名为关键因素
        top_3 = factor_ranking[:3]
        
        # 高占比因素（占收入>10%）
        high_ratio_factors = [
            f for f in factor_ranking
            if f.get("percent_of_revenue", 0) > 10
        ]
        
        # 高敏感因素
        high_sensitivity_factors = [
            f for f in factor_ranking
            if f.get("sensitivity_level") in ["极高敏感", "高敏感"]
        ]
        
        return {
            "top_3_factors": top_3,
            "high_ratio_factors": high_ratio_factors,
            "high_sensitivity_factors": high_sensitivity_factors,
            "critical_count": len(set(
                f["factor_name"] for f in top_3 + high_ratio_factors + high_sensitivity_factors
            ))
        }
    
    def _generate_optimization_suggestions(
        self,
        key_factors: Dict[str, Any],
        cost_structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        suggestions = []
        
        for factor in key_factors["top_3_factors"]:
            if factor["factor_type"] == "revenue":
                suggestions.append({
                    "factor": factor["factor_name"],
                    "priority": "P0",
                    "suggestion": "增加销售收入是提升利润的最直接方式",
                    "actions": [
                        "拓展新客户和新市场",
                        "提高产品单价（在市场可接受范围内）",
                        "增加高利润产品的销量占比",
                        "提升客户复购率"
                    ],
                    "expected_impact": "每增加10%收入，利润可增加约" + 
                                     str(round(factor.get("amount", 0) * 0.1 * 
                                         (cost_structure["profit_margin_percent"] / 100), 2))
                })
            elif factor["factor_type"] == "material":
                suggestions.append({
                    "factor": factor["factor_name"],
                    "priority": "P0",
                    "suggestion": "材料成本是主要成本项，优化空间大",
                    "actions": [
                        "寻找性价比更高的供应商",
                        "批量采购降低单价",
                        "优化材料利用率，减少浪费",
                        "使用替代材料（保证质量前提下）"
                    ],
                    "expected_impact": f"每降低10%材料成本，利润增加{round(factor['amount'] * 0.1, 2)}"
                })
            elif factor["factor_type"] == "labor":
                suggestions.append({
                    "factor": factor["factor_name"],
                    "priority": "P1",
                    "suggestion": "人工成本优化需平衡效率和员工满意度",
                    "actions": [
                        "提升人员效率（培训、自动化）",
                        "优化人员配置结构",
                        "实施绩效激励制度",
                        "外包非核心业务"
                    ],
                    "expected_impact": f"每降低10%人工成本，利润增加{round(factor['amount'] * 0.1, 2)}"
                })
            else:
                suggestions.append({
                    "factor": factor["factor_name"],
                    "priority": "P1",
                    "suggestion": f"关注{factor['factor_name']}的控制和优化",
                    "actions": [
                        "分析费用明细，找出异常项",
                        "制定费用预算和控制标准",
                        "定期审查费用合理性",
                        "寻找降本增效机会"
                    ],
                    "expected_impact": f"预计可优化空间5-15%"
                })
        
        return suggestions
    
    def _analyze_trends(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """趋势分析"""
        if len(historical_data) < 2:
            return {"message": "数据不足，无法进行趋势分析"}
        
        # 分析各因素的变化趋势
        trends = {}
        
        # 示例：分析利润率趋势
        profit_margins = [
            (d["profit"] / d["revenue"] * 100) if d.get("revenue", 0) > 0 else 0
            for d in historical_data
        ]
        
        if len(profit_margins) >= 2:
            trend_direction = "上升" if profit_margins[-1] > profit_margins[0] else "下降"
            avg_margin = statistics.mean(profit_margins)
            
            trends["profit_margin"] = {
                "current": profit_margins[-1],
                "average": round(avg_margin, 2),
                "trend": trend_direction,
                "volatility": round(statistics.stdev(profit_margins), 2) if len(profit_margins) > 1 else 0
            }
        
        return trends


# 创建默认实例
key_factor_identifier = KeyFactorIdentifier()

































