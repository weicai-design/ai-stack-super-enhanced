"""
ROI深度分析器
多维度投资回报率分析
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics


class ROIDeepAnalyzer:
    """ROI深度分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.analysis_history = []
    
    def analyze_roi_comprehensive(
        self,
        investment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        综合ROI分析
        
        Args:
            investment_data: 投资数据 {
                "investment_amount": 1000000,
                "returns": [100000, 120000, 150000, 180000, 200000],
                "costs": [20000, 25000, 30000, 32000, 35000],
                "time_periods": ["Year1", "Year2", "Year3", "Year4", "Year5"],
                "investment_type": "设备投资",
                "risk_level": "中"
            }
        
        Returns:
            深度分析结果
        """
        investment_amount = investment_data["investment_amount"]
        returns = investment_data["returns"]
        costs = investment_data.get("costs", [0] * len(returns))
        
        # 1. 基础ROI计算
        basic_roi = self._calculate_basic_roi(investment_amount, returns, costs)
        
        # 2. 时间价值分析（NPV和IRR）
        time_value_analysis = self._calculate_time_value_metrics(
            investment_amount,
            returns,
            costs
        )
        
        # 3. 回报周期分析
        payback_analysis = self._analyze_payback_period(
            investment_amount,
            returns,
            costs
        )
        
        # 4. 多维度ROI分析
        multidimensional_roi = self._analyze_multidimensional_roi(
            investment_data
        )
        
        # 5. 风险调整ROI
        risk_adjusted_roi = self._calculate_risk_adjusted_roi(
            basic_roi["total_roi"],
            investment_data.get("risk_level", "中")
        )
        
        # 6. 对比分析
        benchmark_comparison = self._compare_with_benchmarks(
            basic_roi["total_roi"],
            investment_data.get("investment_type", "通用")
        )
        
        # 7. 投资建议
        investment_recommendation = self._generate_recommendation(
            basic_roi,
            time_value_analysis,
            payback_analysis,
            risk_adjusted_roi
        )
        
        result = {
            "success": True,
            "basic_roi": basic_roi,
            "time_value_analysis": time_value_analysis,
            "payback_analysis": payback_analysis,
            "multidimensional_roi": multidimensional_roi,
            "risk_adjusted_roi": risk_adjusted_roi,
            "benchmark_comparison": benchmark_comparison,
            "investment_recommendation": investment_recommendation,
            "analyzed_at": datetime.now().isoformat()
        }
        
        self.analysis_history.append(result)
        return result
    
    def _calculate_basic_roi(
        self,
        investment: float,
        returns: List[float],
        costs: List[float]
    ) -> Dict[str, Any]:
        """计算基础ROI"""
        total_returns = sum(returns)
        total_costs = sum(costs)
        net_returns = total_returns - total_costs
        
        roi = ((net_returns - investment) / investment) * 100
        
        # 年化ROI
        years = len(returns)
        annualized_roi = roi / years if years > 0 else 0
        
        return {
            "investment_amount": investment,
            "total_returns": total_returns,
            "total_costs": total_costs,
            "net_returns": net_returns,
            "total_roi": round(roi, 2),
            "annualized_roi": round(annualized_roi, 2),
            "years": years
        }
    
    def _calculate_time_value_metrics(
        self,
        investment: float,
        returns: List[float],
        costs: List[float],
        discount_rate: float = 0.10
    ) -> Dict[str, Any]:
        """
        计算时间价值指标
        
        Args:
            investment: 投资额
            returns: 回报列表
            costs: 成本列表
            discount_rate: 折现率
        
        Returns:
            时间价值分析
        """
        # 计算NPV（净现值）
        npv = -investment
        for i, (ret, cost) in enumerate(zip(returns, costs)):
            year = i + 1
            net_cash_flow = ret - cost
            discounted_value = net_cash_flow / pow(1 + discount_rate, year)
            npv += discounted_value
        
        # 计算IRR（内部收益率）简化版
        irr = self._calculate_irr_approximation(investment, returns, costs)
        
        # 计算盈利指数
        pv_returns = sum(
            (ret - cost) / pow(1 + discount_rate, i + 1)
            for i, (ret, cost) in enumerate(zip(returns, costs))
        )
        profitability_index = pv_returns / investment if investment > 0 else 0
        
        return {
            "npv": round(npv, 2),
            "irr_percent": round(irr, 2),
            "profitability_index": round(profitability_index, 3),
            "discount_rate_used": discount_rate,
            "npv_interpretation": "可行" if npv > 0 else "不可行",
            "irr_interpretation": "优秀" if irr > 20 else "良好" if irr > 10 else "一般"
        }
    
    def _calculate_irr_approximation(
        self,
        investment: float,
        returns: List[float],
        costs: List[float]
    ) -> float:
        """
        IRR简化计算（牛顿迭代法）
        
        Returns:
            IRR百分比
        """
        # 初始猜测
        irr = 0.1
        
        # 牛顿迭代
        for _ in range(100):
            npv = -investment
            npv_derivative = 0
            
            for i, (ret, cost) in enumerate(zip(returns, costs)):
                year = i + 1
                net_cash_flow = ret - cost
                npv += net_cash_flow / pow(1 + irr, year)
                npv_derivative -= year * net_cash_flow / pow(1 + irr, year + 1)
            
            if abs(npv) < 0.01:
                break
            
            if npv_derivative == 0:
                break
            
            irr = irr - npv / npv_derivative
        
        return irr * 100
    
    def _analyze_payback_period(
        self,
        investment: float,
        returns: List[float],
        costs: List[float]
    ) -> Dict[str, Any]:
        """分析回报周期"""
        cumulative_return = 0
        payback_period = None
        
        for i, (ret, cost) in enumerate(zip(returns, costs)):
            cumulative_return += (ret - cost)
            if cumulative_return >= investment and payback_period is None:
                # 精确到月
                remaining = investment - (cumulative_return - (ret - cost))
                months_in_period = (remaining / (ret - cost)) * 12 if (ret - cost) > 0 else 0
                payback_period = i + months_in_period / 12
                break
        
        if payback_period is None:
            payback_period = len(returns) + 1
        
        # 折现回报期
        discounted_cumulative = 0
        discounted_payback = None
        
        for i, (ret, cost) in enumerate(zip(returns, costs)):
            year = i + 1
            discounted_flow = (ret - cost) / pow(1.1, year)
            discounted_cumulative += discounted_flow
            
            if discounted_cumulative >= investment and discounted_payback is None:
                discounted_payback = year
                break
        
        return {
            "simple_payback_years": round(payback_period, 2),
            "discounted_payback_years": discounted_payback if discounted_payback else "超出分析期",
            "payback_status": "快速" if payback_period < 2 else "正常" if payback_period < 4 else "缓慢",
            "cumulative_returns": [
                round(sum(r - c for r, c in zip(returns[:i+1], costs[:i+1])), 2)
                for i in range(len(returns))
            ]
        }
    
    def _analyze_multidimensional_roi(
        self,
        investment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """多维度ROI分析"""
        # 财务维度
        financial_roi = self._calculate_basic_roi(
            investment_data["investment_amount"],
            investment_data["returns"],
            investment_data.get("costs", [0] * len(investment_data["returns"]))
        )["total_roi"]
        
        # 效率维度（假设数据）
        efficiency_improvement = investment_data.get("efficiency_improvement", 15)  # 15%
        
        # 质量维度
        quality_improvement = investment_data.get("quality_improvement", 10)  # 10%
        
        # 市场维度
        market_expansion = investment_data.get("market_expansion", 8)  # 8%
        
        # 综合ROI = 加权平均
        comprehensive_roi = (
            financial_roi * 0.4 +
            efficiency_improvement * 0.3 +
            quality_improvement * 0.2 +
            market_expansion * 0.1
        )
        
        return {
            "financial_roi": round(financial_roi, 2),
            "efficiency_improvement_percent": efficiency_improvement,
            "quality_improvement_percent": quality_improvement,
            "market_expansion_percent": market_expansion,
            "comprehensive_roi": round(comprehensive_roi, 2),
            "dimensions": {
                "财务回报": f"{round(financial_roi, 2)}%（权重40%）",
                "效率提升": f"{efficiency_improvement}%（权重30%）",
                "质量改善": f"{quality_improvement}%（权重20%）",
                "市场拓展": f"{market_expansion}%（权重10%）"
            }
        }
    
    def _calculate_risk_adjusted_roi(
        self,
        roi: float,
        risk_level: str
    ) -> Dict[str, Any]:
        """计算风险调整后的ROI"""
        risk_factors = {
            "低": 0.95,
            "中": 0.85,
            "高": 0.70
        }
        
        risk_factor = risk_factors.get(risk_level, 0.85)
        adjusted_roi = roi * risk_factor
        
        return {
            "original_roi": round(roi, 2),
            "risk_level": risk_level,
            "risk_adjustment_factor": risk_factor,
            "risk_adjusted_roi": round(adjusted_roi, 2),
            "risk_premium": round(roi - adjusted_roi, 2)
        }
    
    def _compare_with_benchmarks(
        self,
        roi: float,
        investment_type: str
    ) -> Dict[str, Any]:
        """与基准对比"""
        benchmarks = {
            "设备投资": 15,
            "IT投资": 20,
            "研发投资": 25,
            "营销投资": 18,
            "通用": 15
        }
        
        benchmark = benchmarks.get(investment_type, benchmarks["通用"])
        difference = roi - benchmark
        
        if difference > 10:
            performance = "远超基准"
        elif difference > 0:
            performance = "优于基准"
        elif difference > -5:
            performance = "接近基准"
        else:
            performance = "低于基准"
        
        return {
            "investment_type": investment_type,
            "benchmark_roi": benchmark,
            "actual_roi": round(roi, 2),
            "difference": round(difference, 2),
            "performance": performance
        }
    
    def _generate_recommendation(
        self,
        basic_roi: Dict[str, Any],
        time_value: Dict[str, Any],
        payback: Dict[str, Any],
        risk_adjusted: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成投资建议"""
        score = 0
        reasons = []
        
        # ROI评分
        if basic_roi["total_roi"] > 30:
            score += 30
            reasons.append("ROI超过30%，回报优秀")
        elif basic_roi["total_roi"] > 15:
            score += 20
            reasons.append("ROI在15-30%之间，回报良好")
        elif basic_roi["total_roi"] > 0:
            score += 10
            reasons.append("ROI为正，但回报一般")
        
        # NPV评分
        if time_value["npv"] > 0:
            score += 25
            reasons.append("NPV为正，项目增值")
        
        # IRR评分
        if time_value["irr_percent"] > 20:
            score += 25
            reasons.append("IRR超过20%，内部收益率优秀")
        elif time_value["irr_percent"] > 10:
            score += 15
            reasons.append("IRR在10-20%之间，内部收益率良好")
        
        # 回报期评分
        if payback["simple_payback_years"] < 3:
            score += 20
            reasons.append("3年内回本，回本快")
        elif payback["simple_payback_years"] < 5:
            score += 10
            reasons.append("5年内回本，回本正常")
        
        # 生成建议
        if score >= 80:
            recommendation = "强烈推荐投资"
            level = "A+"
        elif score >= 60:
            recommendation = "推荐投资"
            level = "A"
        elif score >= 40:
            recommendation = "可以考虑投资"
            level = "B"
        else:
            recommendation = "谨慎投资"
            level = "C"
        
        return {
            "recommendation": recommendation,
            "level": level,
            "score": score,
            "reasons": reasons,
            "risk_adjusted_roi": risk_adjusted["risk_adjusted_roi"]
        }


# 创建默认实例
roi_deep_analyzer = ROIDeepAnalyzer()



































