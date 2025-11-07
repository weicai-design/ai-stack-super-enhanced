"""
财务管理高级功能模块
为财务管理添加企业级分析能力
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import statistics


class FinanceAdvancedAnalyzer:
    """财务高级分析器"""
    
    def __init__(self):
        self.analysis_history = []
    
    def cash_flow_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        forecast_months: int = 6
    ) -> Dict[str, Any]:
        """
        现金流预测（新功能）
        
        基于历史数据预测未来现金流
        """
        try:
            if len(historical_data) < 3:
                return {
                    "success": False,
                    "error": "历史数据不足，至少需要3个月数据"
                }
            
            # 提取现金流数据
            cash_flows = [d["cash_flow"] for d in historical_data]
            
            # 计算趋势
            avg_cash_flow = statistics.mean(cash_flows)
            
            # 简单移动平均预测
            recent_3_months = cash_flows[-3:]
            recent_avg = statistics.mean(recent_3_months)
            
            # 计算增长率
            if len(cash_flows) >= 2:
                growth_rate = (cash_flows[-1] - cash_flows[0]) / len(cash_flows) / cash_flows[0] if cash_flows[0] != 0 else 0
            else:
                growth_rate = 0
            
            # 生成预测
            forecasts = []
            base_value = recent_avg
            
            for i in range(1, forecast_months + 1):
                # 考虑增长率的预测
                forecast_value = base_value * (1 + growth_rate * i)
                
                forecasts.append({
                    "month": i,
                    "forecast_amount": round(forecast_value, 2),
                    "confidence": "高" if i <= 2 else "中" if i <= 4 else "低",
                    "range_min": round(forecast_value * 0.9, 2),
                    "range_max": round(forecast_value * 1.1, 2)
                })
            
            # 风险评估
            negative_months = sum(1 for f in forecasts if f["forecast_amount"] < 0)
            
            if negative_months > 0:
                risk_level = "高"
                warning = f"预测有{negative_months}个月现金流为负"
            elif forecasts[0]["forecast_amount"] < avg_cash_flow * 0.5:
                risk_level = "中"
                warning = "近期现金流预计下降"
            else:
                risk_level = "低"
                warning = None
            
            return {
                "success": True,
                "historical_average": round(avg_cash_flow, 2),
                "recent_average": round(recent_avg, 2),
                "growth_rate": round(growth_rate * 100, 2),
                "forecasts": forecasts,
                "risk_level": risk_level,
                "warning": warning,
                "recommendations": self._generate_cashflow_recommendations(forecasts, risk_level),
                "forecast_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def financial_health_score(
        self,
        financial_ratios: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        财务健康度评分（新功能）
        
        综合多个财务指标评估企业财务健康状况
        """
        try:
            score = 0
            max_score = 100
            factors = []
            
            # 1. 流动比率（20分）
            current_ratio = financial_ratios.get("current_ratio", 1.0)
            if current_ratio >= 2.0:
                score += 20
                factors.append({"factor": "流动比率", "score": 20, "status": "优秀"})
            elif current_ratio >= 1.5:
                score += 15
                factors.append({"factor": "流动比率", "score": 15, "status": "良好"})
            elif current_ratio >= 1.0:
                score += 10
                factors.append({"factor": "流动比率", "score": 10, "status": "一般"})
            else:
                score += 5
                factors.append({"factor": "流动比率", "score": 5, "status": "偏低"})
            
            # 2. 资产负债率（20分）
            debt_ratio = financial_ratios.get("debt_ratio", 0.5)
            if debt_ratio <= 0.4:
                score += 20
                factors.append({"factor": "资产负债率", "score": 20, "status": "优秀"})
            elif debt_ratio <= 0.6:
                score += 15
                factors.append({"factor": "资产负债率", "score": 15, "status": "良好"})
            elif debt_ratio <= 0.7:
                score += 10
                factors.append({"factor": "资产负债率", "score": 10, "status": "一般"})
            else:
                score += 5
                factors.append({"factor": "资产负债率", "score": 5, "status": "偏高"})
            
            # 3. 净利润率（25分）
            profit_margin = financial_ratios.get("profit_margin", 0.1)
            if profit_margin >= 0.15:
                score += 25
                factors.append({"factor": "净利润率", "score": 25, "status": "优秀"})
            elif profit_margin >= 0.10:
                score += 20
                factors.append({"factor": "净利润率", "score": 20, "status": "良好"})
            elif profit_margin >= 0.05:
                score += 12
                factors.append({"factor": "净利润率", "score": 12, "status": "一般"})
            else:
                score += 5
                factors.append({"factor": "净利润率", "score": 5, "status": "偏低"})
            
            # 4. 资产周转率（20分）
            asset_turnover = financial_ratios.get("asset_turnover", 1.0)
            if asset_turnover >= 2.0:
                score += 20
                factors.append({"factor": "资产周转率", "score": 20, "status": "优秀"})
            elif asset_turnover >= 1.5:
                score += 15
                factors.append({"factor": "资产周转率", "score": 15, "status": "良好"})
            elif asset_turnover >= 1.0:
                score += 10
                factors.append({"factor": "资产周转率", "score": 10, "status": "一般"})
            else:
                score += 5
                factors.append({"factor": "资产周转率", "score": 5, "status": "偏低"})
            
            # 5. 速动比率（15分）
            quick_ratio = financial_ratios.get("quick_ratio", 1.0)
            if quick_ratio >= 1.5:
                score += 15
                factors.append({"factor": "速动比率", "score": 15, "status": "优秀"})
            elif quick_ratio >= 1.0:
                score += 12
                factors.append({"factor": "速动比率", "score": 12, "status": "良好"})
            elif quick_ratio >= 0.8:
                score += 8
                factors.append({"factor": "速动比率", "score": 8, "status": "一般"})
            else:
                score += 4
                factors.append({"factor": "速动比率", "score": 4, "status": "偏低"})
            
            # 健康度等级
            if score >= 90:
                health_grade = "A+优秀"
                health_status = "财务状况非常健康"
                color = "green"
            elif score >= 80:
                health_grade = "A良好"
                health_status = "财务状况良好"
                color = "blue"
            elif score >= 70:
                health_grade = "B一般"
                health_status = "财务状况一般"
                color = "yellow"
            elif score >= 60:
                health_grade = "C偏弱"
                health_status = "财务状况偏弱，需关注"
                color = "orange"
            else:
                health_grade = "D较差"
                health_status = "财务状况较差，需要改善"
                color = "red"
            
            # 建议
            recommendations = self._generate_health_recommendations(financial_ratios, score)
            
            return {
                "success": True,
                "health_score": round(score, 2),
                "health_grade": health_grade,
                "health_status": health_status,
                "color": color,
                "factor_scores": factors,
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def budget_variance_analysis(
        self,
        budget_data: Dict[str, float],
        actual_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        预算差异分析（新功能）
        
        对比预算和实际支出，分析差异原因
        """
        try:
            variance_analysis = []
            total_budget = sum(budget_data.values())
            total_actual = sum(actual_data.values())
            total_variance = total_actual - total_budget
            
            for category in budget_data.keys():
                budget = budget_data[category]
                actual = actual_data.get(category, 0)
                variance = actual - budget
                variance_rate = (variance / budget * 100) if budget > 0 else 0
                
                # 判断差异等级
                if abs(variance_rate) > 20:
                    variance_level = "重大差异"
                    alert = "需要说明"
                elif abs(variance_rate) > 10:
                    variance_level = "显著差异"
                    alert = "需要关注"
                else:
                    variance_level = "正常范围"
                    alert = None
                
                variance_analysis.append({
                    "category": category,
                    "budget": budget,
                    "actual": actual,
                    "variance": round(variance, 2),
                    "variance_rate": round(variance_rate, 2),
                    "variance_level": variance_level,
                    "alert": alert
                })
            
            # 总体评估
            total_variance_rate = (total_variance / total_budget * 100) if total_budget > 0 else 0
            
            if total_variance_rate > 10:
                overall_assessment = "超支严重"
                assessment_color = "red"
            elif total_variance_rate > 5:
                overall_assessment = "轻微超支"
                assessment_color = "orange"
            elif total_variance_rate > -5:
                overall_assessment = "基本持平"
                assessment_color = "green"
            else:
                overall_assessment = "节余"
                assessment_color = "blue"
            
            return {
                "success": True,
                "total_budget": total_budget,
                "total_actual": total_actual,
                "total_variance": round(total_variance, 2),
                "total_variance_rate": round(total_variance_rate, 2),
                "overall_assessment": overall_assessment,
                "assessment_color": assessment_color,
                "variance_by_category": variance_analysis,
                "major_variances": [v for v in variance_analysis if v["variance_level"] == "重大差异"],
                "recommendations": self._generate_variance_recommendations(variance_analysis),
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def working_capital_analysis(
        self,
        current_assets: float,
        current_liabilities: float,
        inventory: float,
        receivables: float,
        payables: float
    ) -> Dict[str, Any]:
        """
        营运资本分析（新功能）
        
        分析企业营运资本效率
        """
        try:
            # 营运资本
            working_capital = current_assets - current_liabilities
            
            # 流动比率
            current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
            
            # 速动比率
            quick_assets = current_assets - inventory
            quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else 0
            
            # 现金比率
            cash = current_assets - inventory - receivables
            cash_ratio = cash / current_liabilities if current_liabilities > 0 else 0
            
            # 营运资本周转天数
            # 假设年销售额为营运资本的4倍
            annual_revenue = working_capital * 4
            working_capital_turnover = annual_revenue / working_capital if working_capital > 0 else 0
            turnover_days = 365 / working_capital_turnover if working_capital_turnover > 0 else 0
            
            # 应收账款周转天数
            receivables_turnover = annual_revenue / receivables if receivables > 0 else 0
            receivables_days = 365 / receivables_turnover if receivables_turnover > 0 else 0
            
            # 应付账款周转天数
            payables_turnover = annual_revenue / payables if payables > 0 else 0
            payables_days = 365 / payables_turnover if payables_turnover > 0 else 0
            
            # 现金循环周期
            cash_conversion_cycle = receivables_days + turnover_days - payables_days
            
            # 健康度评估
            health_issues = []
            
            if current_ratio < 1.5:
                health_issues.append("流动比率偏低，短期偿债能力不足")
            if quick_ratio < 1.0:
                health_issues.append("速动比率偏低，即时偿债能力弱")
            if cash_conversion_cycle > 90:
                health_issues.append("现金循环周期过长，资金占用多")
            if receivables_days > 60:
                health_issues.append("应收账款周转慢，回款压力大")
            
            if len(health_issues) == 0:
                health_status = "健康"
                grade = "A"
            elif len(health_issues) <= 1:
                health_status = "良好"
                grade = "B"
            elif len(health_issues) <= 2:
                health_status = "一般"
                grade = "C"
            else:
                health_status = "需改善"
                grade = "D"
            
            # 建议
            recommendations = []
            if current_ratio < 2.0:
                recommendations.append("增加流动资产或降低短期负债")
            if receivables_days > 60:
                recommendations.append("加强应收账款管理，加快回款")
            if payables_days < 30:
                recommendations.append("适当延长付款周期，优化现金流")
            if cash_conversion_cycle > 90:
                recommendations.append("缩短现金循环周期，提高资金效率")
            
            return {
                "success": True,
                "working_capital_metrics": {
                    "working_capital": round(working_capital, 2),
                    "current_ratio": round(current_ratio, 2),
                    "quick_ratio": round(quick_ratio, 2),
                    "cash_ratio": round(cash_ratio, 2)
                },
                "turnover_metrics": {
                    "working_capital_turnover_days": round(turnover_days, 2),
                    "receivables_turnover_days": round(receivables_days, 2),
                    "payables_turnover_days": round(payables_days, 2),
                    "cash_conversion_cycle": round(cash_conversion_cycle, 2)
                },
                "health_status": health_status,
                "grade": grade,
                "health_issues": health_issues,
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def profitability_deep_analysis(
        self,
        revenue: float,
        costs: Dict[str, float],
        period: str = "月度"
    ) -> Dict[str, Any]:
        """
        盈利能力深度分析（新功能）
        
        多维度分析企业盈利能力
        """
        try:
            # 计算各项利润指标
            total_costs = sum(costs.values())
            gross_profit = revenue - costs.get("cost_of_sales", 0)
            operating_profit = gross_profit - costs.get("operating_expenses", 0)
            net_profit = revenue - total_costs
            
            # 利润率
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            operating_margin = (operating_profit / revenue * 100) if revenue > 0 else 0
            net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
            
            # 成本结构分析
            cost_structure = {}
            for cost_type, amount in costs.items():
                cost_structure[cost_type] = {
                    "amount": amount,
                    "percentage": round((amount / revenue * 100), 2) if revenue > 0 else 0
                }
            
            # 盈利能力评级
            if net_margin >= 15:
                profitability_grade = "A+优秀"
                status = "盈利能力强"
            elif net_margin >= 10:
                profitability_grade = "A良好"
                status = "盈利能力较好"
            elif net_margin >= 5:
                profitability_grade = "B一般"
                status = "盈利能力一般"
            elif net_margin >= 0:
                profitability_grade = "C偏低"
                status = "盈利能力偏低"
            else:
                profitability_grade = "D亏损"
                status = "处于亏损状态"
            
            # 优化建议
            recommendations = []
            
            if gross_margin < 30:
                recommendations.append({
                    "area": "毛利率",
                    "current": f"{gross_margin:.1f}%",
                    "target": "≥30%",
                    "actions": ["优化产品定价", "降低销售成本", "提高产品附加值"],
                    "priority": "高"
                })
            
            if operating_margin < 10:
                recommendations.append({
                    "area": "营业利润率",
                    "current": f"{operating_margin:.1f}%",
                    "target": "≥10%",
                    "actions": ["控制运营费用", "提升运营效率", "优化费用结构"],
                    "priority": "高"
                })
            
            if net_margin < 5:
                recommendations.append({
                    "area": "净利润率",
                    "current": f"{net_margin:.1f}%",
                    "target": "≥5%",
                    "actions": ["全面成本管控", "提升销售收入", "优化业务结构"],
                    "priority": "极高"
                })
            
            return {
                "success": True,
                "period": period,
                "revenue": revenue,
                "profit_metrics": {
                    "gross_profit": round(gross_profit, 2),
                    "operating_profit": round(operating_profit, 2),
                    "net_profit": round(net_profit, 2),
                    "gross_margin": round(gross_margin, 2),
                    "operating_margin": round(operating_margin, 2),
                    "net_margin": round(net_margin, 2)
                },
                "cost_structure": cost_structure,
                "profitability_grade": profitability_grade,
                "status": status,
                "optimization_recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_cashflow_recommendations(
        self,
        forecasts: List[Dict[str, Any]],
        risk_level: str
    ) -> List[str]:
        """生成现金流建议"""
        recommendations = []
        
        if risk_level == "高":
            recommendations.append("现金流风险高，建议：1)加快应收账款回收 2)延缓应付账款支付 3)寻求短期融资")
        elif risk_level == "中":
            recommendations.append("关注现金流变化，做好资金准备")
        
        # 检查波动性
        forecast_values = [f["forecast_amount"] for f in forecasts]
        if len(forecast_values) > 1:
            volatility = statistics.stdev(forecast_values)
            avg = statistics.mean(forecast_values)
            cv = volatility / avg if avg != 0 else 0
            
            if cv > 0.3:
                recommendations.append("现金流波动较大，建议保持充足的现金储备")
        
        return recommendations
    
    def _generate_health_recommendations(
        self,
        ratios: Dict[str, float],
        score: float
    ) -> List[str]:
        """生成健康度建议"""
        recommendations = []
        
        if score < 80:
            recommendations.append("财务健康度有待提升，建议全面审查财务状况")
        
        if ratios.get("current_ratio", 1.5) < 1.5:
            recommendations.append("提高流动比率：增加流动资产或减少短期负债")
        
        if ratios.get("debt_ratio", 0.5) > 0.6:
            recommendations.append("降低负债率：减少借款或增加权益资本")
        
        if ratios.get("profit_margin", 0.1) < 0.1:
            recommendations.append("提升利润率：增收节支，优化业务结构")
        
        return recommendations
    
    def _generate_variance_recommendations(
        self,
        variance_analysis: List[Dict[str, Any]]
    ) -> List[str]:
        """生成差异分析建议"""
        recommendations = []
        
        major_variances = [v for v in variance_analysis if v["variance_level"] == "重大差异"]
        
        if len(major_variances) > 0:
            recommendations.append(f"发现{len(major_variances)}项重大差异，需要深入调查原因")
        
        # 找出超支最多的类别
        overspent = sorted(
            [v for v in variance_analysis if v["variance"] > 0],
            key=lambda x: x["variance"],
            reverse=True
        )
        
        if overspent:
            top_overspent = overspent[0]
            recommendations.append(f"{top_overspent['category']}超支最多（{top_overspent['variance']:.2f}元），需要重点控制")
        
        return recommendations


# 创建默认实例
finance_advanced_analyzer = FinanceAdvancedAnalyzer()


