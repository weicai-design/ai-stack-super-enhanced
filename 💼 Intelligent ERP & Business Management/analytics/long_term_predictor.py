"""
长期影响预测器
实现三年、五年销售额影响的精确预测
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics
import math


class LongTermPredictor:
    """长期影响预测器"""
    
    def __init__(self):
        """初始化预测器"""
        self.historical_data = []
        self.prediction_models = {}
    
    def predict_project_impact(
        self,
        project_data: Dict[str, Any],
        prediction_years: int = 5
    ) -> Dict[str, Any]:
        """
        预测新项目对未来销售额的影响
        
        Args:
            project_data: 项目数据 {
                "project_id": "",
                "estimated_order_value": 0,
                "recurrence_probability": 0.7,
                "growth_rate": 0.1,
                "market_expansion": 0.05,
                "competitive_factor": 0.9
            }
            prediction_years: 预测年数
        
        Returns:
            预测结果
        """
        base_value = project_data.get("estimated_order_value", 0)
        recurrence_prob = project_data.get("recurrence_probability", 0.7)
        growth_rate = project_data.get("growth_rate", 0.1)
        market_expansion = project_data.get("market_expansion", 0.05)
        competitive_factor = project_data.get("competitive_factor", 0.9)
        
        predictions = {
            "monthly": {},
            "quarterly": {},
            "yearly": {},
            "three_year": {},
            "five_year": {}
        }
        
        # 月度预测（第一年）
        monthly_values = []
        for month in range(1, 13):
            # 考虑季节性因素
            seasonal_factor = self._get_seasonal_factor(month)
            
            # 月度预测 = 基础值 × 重复概率 × 季节因素 / 12
            monthly_value = base_value * recurrence_prob * seasonal_factor / 12
            monthly_values.append(monthly_value)
            
            predictions["monthly"][f"Month_{month}"] = round(monthly_value, 2)
        
        # 季度预测（第一年）
        for quarter in range(1, 5):
            start_month = (quarter - 1) * 3
            quarterly_value = sum(monthly_values[start_month:start_month + 3])
            predictions["quarterly"][f"Q{quarter}"] = round(quarterly_value, 2)
        
        # 年度预测（1-5年）
        yearly_predictions = []
        for year in range(1, prediction_years + 1):
            # 年度预测模型：考虑增长、市场扩张、竞争因素
            year_multiplier = math.pow(1 + growth_rate, year - 1)
            market_multiplier = 1 + (market_expansion * year)
            competition_impact = math.pow(competitive_factor, year - 1)
            
            # 年度销售额 = 基础值 × 重复概率 × 年度增长 × 市场扩张 × 竞争影响
            yearly_value = (
                base_value * 
                recurrence_prob * 
                year_multiplier * 
                market_multiplier * 
                competition_impact
            )
            
            yearly_predictions.append(yearly_value)
            predictions["yearly"][f"Year_{year}"] = round(yearly_value, 2)
        
        # 三年累计影响
        three_year_total = sum(yearly_predictions[:3])
        three_year_avg = three_year_total / 3
        
        predictions["three_year"] = {
            "total": round(three_year_total, 2),
            "average": round(three_year_avg, 2),
            "year_1": round(yearly_predictions[0], 2),
            "year_2": round(yearly_predictions[1], 2),
            "year_3": round(yearly_predictions[2], 2),
            "trend": "增长" if yearly_predictions[2] > yearly_predictions[0] else "下降"
        }
        
        # 五年累计影响
        five_year_total = sum(yearly_predictions[:5])
        five_year_avg = five_year_total / 5
        five_year_cagr = self._calculate_cagr(
            yearly_predictions[0],
            yearly_predictions[4],
            5
        )
        
        predictions["five_year"] = {
            "total": round(five_year_total, 2),
            "average": round(five_year_avg, 2),
            "cagr": round(five_year_cagr, 2),  # 复合年增长率
            "year_1": round(yearly_predictions[0], 2),
            "year_2": round(yearly_predictions[1], 2),
            "year_3": round(yearly_predictions[2], 2),
            "year_4": round(yearly_predictions[3], 2),
            "year_5": round(yearly_predictions[4], 2),
            "trend": "强劲增长" if five_year_cagr > 10 else "稳定增长" if five_year_cagr > 0 else "下降"
        }
        
        # 战略影响分析
        strategic_impact = self._analyze_strategic_impact(
            base_value,
            three_year_total,
            five_year_total,
            five_year_cagr
        )
        
        return {
            "success": True,
            "project_id": project_data.get("project_id"),
            "base_value": base_value,
            "predictions": predictions,
            "strategic_impact": strategic_impact,
            "confidence_level": self._calculate_confidence(project_data)
        }
    
    def _get_seasonal_factor(self, month: int) -> float:
        """
        获取季节性因素
        
        Args:
            month: 月份
        
        Returns:
            季节因子
        """
        # 简化的季节性模型（可根据实际业务调整）
        seasonal_factors = {
            1: 0.85,  # 1月（春节影响）
            2: 0.90,
            3: 1.10,  # 3月（开工旺季）
            4: 1.05,
            5: 1.05,
            6: 1.00,
            7: 0.95,
            8: 0.95,
            9: 1.10,  # 9月（旺季）
            10: 1.10,
            11: 1.05,
            12: 0.90   # 12月（年底放缓）
        }
        return seasonal_factors.get(month, 1.0)
    
    def _calculate_cagr(
        self,
        start_value: float,
        end_value: float,
        years: int
    ) -> float:
        """
        计算复合年增长率
        
        Args:
            start_value: 起始值
            end_value: 结束值
            years: 年数
        
        Returns:
            CAGR百分比
        """
        if start_value <= 0 or years <= 0:
            return 0
        
        cagr = (math.pow(end_value / start_value, 1 / years) - 1) * 100
        return cagr
    
    def _analyze_strategic_impact(
        self,
        base_value: float,
        three_year_total: float,
        five_year_total: float,
        cagr: float
    ) -> Dict[str, Any]:
        """
        分析战略影响
        
        Args:
            base_value: 基础值
            three_year_total: 三年总额
            five_year_total: 五年总额
            cagr: 复合增长率
        
        Returns:
            战略影响分析
        """
        # 计算占比（假设公司当前年销售额为1000万）
        company_annual_sales = 10000000
        
        three_year_contribution = (three_year_total / (company_annual_sales * 3)) * 100
        five_year_contribution = (five_year_total / (company_annual_sales * 5)) * 100
        
        # 战略重要性评级
        if five_year_contribution > 20:
            importance = "战略级（极高）"
        elif five_year_contribution > 10:
            importance = "重要级（高）"
        elif five_year_contribution > 5:
            importance = "一般级（中）"
        else:
            importance = "次要级（低）"
        
        # 投资建议
        if cagr > 15 and five_year_contribution > 10:
            recommendation = "强烈建议投资：高增长+高贡献"
        elif cagr > 10 or five_year_contribution > 10:
            recommendation = "建议投资：有增长潜力"
        elif cagr > 5:
            recommendation = "可以投资：稳定增长"
        else:
            recommendation = "谨慎投资：增长有限"
        
        return {
            "three_year_contribution_percent": round(three_year_contribution, 2),
            "five_year_contribution_percent": round(five_year_contribution, 2),
            "strategic_importance": importance,
            "investment_recommendation": recommendation,
            "risk_assessment": self._assess_risk(cagr, five_year_contribution)
        }
    
    def _assess_risk(self, cagr: float, contribution: float) -> str:
        """
        风险评估
        
        Args:
            cagr: 增长率
            contribution: 贡献度
        
        Returns:
            风险等级
        """
        if cagr > 20:
            return "高风险高回报：增长率过高可能不可持续"
        elif cagr < 0:
            return "高风险：负增长趋势"
        elif contribution > 30:
            return "中风险：过度依赖单一项目"
        else:
            return "低风险：增长稳定，贡献度合理"
    
    def _calculate_confidence(self, project_data: Dict[str, Any]) -> str:
        """
        计算预测置信度
        
        Args:
            project_data: 项目数据
        
        Returns:
            置信度等级
        """
        # 基于数据完整性计算置信度
        data_completeness = 0
        total_fields = 5
        
        if project_data.get("estimated_order_value", 0) > 0:
            data_completeness += 1
        if "recurrence_probability" in project_data:
            data_completeness += 1
        if "growth_rate" in project_data:
            data_completeness += 1
        if "market_expansion" in project_data:
            data_completeness += 1
        if "competitive_factor" in project_data:
            data_completeness += 1
        
        completeness_ratio = data_completeness / total_fields
        
        if completeness_ratio >= 0.9:
            return "高置信度（90%+）"
        elif completeness_ratio >= 0.7:
            return "中等置信度（70-90%）"
        else:
            return "低置信度（<70%）"


# 创建默认实例
long_term_predictor = LongTermPredictor()



































