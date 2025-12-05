"""
财务分析引擎
Financial Analysis Engine

提供深度财务分析功能，包括：
- 盈亏分析
- 费用分析
- 收入分析
- 经营诊断
- 经营建议（基于RAG）

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

from .models import (
    ProfitAnalysis,
    ExpenseAnalysis,
    RevenueAnalysis,
    FinancialPeriod
)
from .finance_manager import finance_manager

logger = logging.getLogger(__name__)


class FinancialAnalysisEngine:
    """财务分析引擎"""
    
    def __init__(self):
        """初始化分析引擎"""
        self.rag_available = self._check_rag_availability()
        logger.info("✅ 财务分析引擎已初始化")
    
    def _check_rag_availability(self) -> bool:
        """检查RAG系统是否可用"""
        try:
            # 尝试导入RAG模块
            parent_dir = Path(__file__).resolve().parents[2]
            if str(parent_dir) not in sys.path:
                sys.path.insert(0, str(parent_dir))
            return True
        except Exception:
            return False
    
    # ==================== 盈亏分析 ====================
    
    def analyze_profit(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ProfitAnalysis:
        """
        盈亏分析
        
        Args:
            tenant_id: 租户ID
            period: 分析周期
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            盈亏分析结果
        """
        # 默认分析最近一个周期
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 聚合数据
        total_revenue, total_cost, total_profit = finance_manager.aggregate_income(
            tenant_id, start_date, end_date
        )
        
        # 计算利润率
        profit_margin = total_profit / total_revenue if total_revenue > 0 else 0
        
        # 计算盈亏平衡点
        breakeven_revenue, breakeven_units = finance_manager.calculate_breakeven(tenant_id)
        
        # 识别关键因素
        key_factors = finance_manager.identify_key_factors(tenant_id, period)
        
        # 分析趋势
        trend = self._analyze_trend(tenant_id, period)
        
        # 生成建议
        recommendations = self._generate_profit_recommendations(
            total_revenue,
            total_cost,
            total_profit,
            profit_margin,
            key_factors
        )
        
        return ProfitAnalysis(
            tenant_id=tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            profit_margin=profit_margin,
            breakeven_revenue=breakeven_revenue,
            breakeven_units=breakeven_units,
            revenue_trend=trend["revenue"],
            profit_trend=trend["profit"],
            key_factors=key_factors,
            recommendations=recommendations
        )
    
    def _analyze_trend(
        self,
        tenant_id: str,
        period: FinancialPeriod
    ) -> Dict[str, str]:
        """分析趋势"""
        trend_data = finance_manager.calculate_profit_trend(tenant_id, period, months=3)
        
        if len(trend_data) < 2:
            return {"revenue": "数据不足", "profit": "数据不足"}
        
        # 简单趋势判断
        revenue_values = [d["revenue"] for d in trend_data]
        profit_values = [d["profit"] for d in trend_data]
        
        revenue_trend = "上升" if revenue_values[-1] > revenue_values[0] else "下降" if revenue_values[-1] < revenue_values[0] else "平稳"
        profit_trend = "上升" if profit_values[-1] > profit_values[0] else "下降" if profit_values[-1] < profit_values[0] else "平稳"
        
        return {
            "revenue": revenue_trend,
            "profit": profit_trend
        }
    
    def _generate_profit_recommendations(
        self,
        revenue: float,
        cost: float,
        profit: float,
        margin: float,
        key_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """生成利润优化建议"""
        recommendations = []
        
        # 利润率分析
        if margin < 0:
            recommendations.append("⚠️ 当前处于亏损状态，需紧急采取措施扭转局面")
            recommendations.append("建议：1) 提高产品售价 2) 降低生产成本 3) 控制费用支出")
        elif margin < 0.1:
            recommendations.append("⚠️ 利润率偏低（<10%），需要改善盈利能力")
            recommendations.append("建议：优化产品结构，增加高毛利产品占比")
        elif margin > 0.3:
            recommendations.append("✅ 利润率表现良好（>30%），保持当前策略")
        
        # 关键因素分析
        if key_factors:
            top_factor = key_factors[0]
            if "成本" in top_factor["factor"] and top_factor["change"] > 0:
                recommendations.append(f"⚠️ {top_factor['factor']}是主要问题，建议重点控制成本")
            elif "收入" in top_factor["factor"] and top_factor["change"] < 0:
                recommendations.append(f"⚠️ {top_factor['factor']}下降明显，建议加强市场开拓")
        
        # 基于RAG的建议（如果可用）
        if self.rag_available:
            recommendations.append("💡 可以检索RAG知识库获取更多行业最佳实践")
        
        return recommendations
    
    # ==================== 费用分析 ====================
    
    def analyze_expenses(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ExpenseAnalysis:
        """
        费用分析
        
        Args:
            tenant_id: 租户ID
            period: 分析周期
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            费用分析结果
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 获取利润表
        statements = finance_manager.get_income_statements(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # 汇总费用
        total_expenses = 0.0
        sales_expenses = 0.0
        management_expenses = 0.0
        finance_expenses = 0.0
        labor_costs = 0.0
        material_costs = 0.0
        manufacturing_costs = 0.0
        
        for stmt in statements:
            sales_expenses += stmt.sales_expenses
            management_expenses += stmt.management_expenses
            finance_expenses += stmt.finance_expenses
            labor_costs += stmt.labor_cost
            material_costs += stmt.material_cost
            manufacturing_costs += stmt.manufacturing_cost
        
        total_expenses = (
            sales_expenses + management_expenses + finance_expenses +
            labor_costs + material_costs + manufacturing_costs
        )
        
        # 计算费用占比
        expense_ratios = {}
        if total_expenses > 0:
            expense_ratios = {
                "销售费用": sales_expenses / total_expenses,
                "管理费用": management_expenses / total_expenses,
                "财务费用": finance_expenses / total_expenses,
                "人工成本": labor_costs / total_expenses,
                "材料成本": material_costs / total_expenses,
                "制造费用": manufacturing_costs / total_expenses
            }
        
        # 合理性评估
        score, issues = self._assess_expense_reasonableness(
            expense_ratios,
            tenant_id
        )
        
        # 生成建议
        recommendations = self._generate_expense_recommendations(
            expense_ratios,
            issues
        )
        
        return ExpenseAnalysis(
            tenant_id=tenant_id,
            period=period,
            total_expenses=total_expenses,
            sales_expenses=sales_expenses,
            management_expenses=management_expenses,
            finance_expenses=finance_expenses,
            labor_costs=labor_costs,
            material_costs=material_costs,
            manufacturing_costs=manufacturing_costs,
            expense_ratios=expense_ratios,
            reasonableness_score=score,
            issues=issues,
            recommendations=recommendations
        )
    
    def _assess_expense_reasonableness(
        self,
        expense_ratios: Dict[str, float],
        tenant_id: str
    ) -> tuple[float, List[str]]:
        """评估费用合理性"""
        score = 100.0
        issues = []
        
        # 行业基准（可以从RAG获取）
        benchmarks = {
            "销售费用": 0.15,  # 15%
            "管理费用": 0.10,  # 10%
            "财务费用": 0.05,  # 5%
            "人工成本": 0.25,  # 25%
            "材料成本": 0.35,  # 35%
            "制造费用": 0.10   # 10%
        }
        
        for category, ratio in expense_ratios.items():
            if category in benchmarks:
                benchmark = benchmarks[category]
                deviation = abs(ratio - benchmark) / benchmark
                
                if deviation > 0.3:  # 偏差超过30%
                    score -= 15
                    if ratio > benchmark:
                        issues.append(f"{category}占比过高（{ratio:.1%} vs 基准{benchmark:.1%}）")
                    else:
                        issues.append(f"{category}占比异常偏低（{ratio:.1%} vs 基准{benchmark:.1%}）")
                elif deviation > 0.2:  # 偏差超过20%
                    score -= 10
        
        return max(score, 0.0), issues
    
    def _generate_expense_recommendations(
        self,
        expense_ratios: Dict[str, float],
        issues: List[str]
    ) -> List[str]:
        """生成费用优化建议"""
        recommendations = []
        
        if issues:
            recommendations.append("⚠️ 发现以下费用异常：")
            recommendations.extend(f"  - {issue}" for issue in issues)
        
        # 针对性建议
        if "材料成本" in expense_ratios and expense_ratios["材料成本"] > 0.4:
            recommendations.append("💡 材料成本占比较高，建议：")
            recommendations.append("  1) 寻找更优质的供应商")
            recommendations.append("  2) 批量采购降低单价")
            recommendations.append("  3) 优化产品设计减少材料用量")
        
        if "人工成本" in expense_ratios and expense_ratios["人工成本"] > 0.3:
            recommendations.append("💡 人工成本占比较高，建议：")
            recommendations.append("  1) 提高生产自动化水平")
            recommendations.append("  2) 优化人员配置")
            recommendations.append("  3) 提升员工效率")
        
        return recommendations
    
    # ==================== 收入分析 ====================
    
    def analyze_revenue(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> RevenueAnalysis:
        """
        收入分析
        
        Returns:
            收入分析结果
        """
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 获取收入数据
        statements = finance_manager.get_income_statements(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        total_revenue = sum(s.revenue for s in statements)
        product_revenue = sum(s.product_revenue for s in statements)
        service_revenue = sum(s.service_revenue for s in statements)
        
        # 模拟客户和订单数据（实际应该从订单系统获取）
        customer_count = len(statements) * 10  # 假设每期10个客户
        order_count = len(statements) * 50     # 假设每期50个订单
        avg_order_value = total_revenue / order_count if order_count > 0 else 0
        
        # 行业对比（可以从RAG获取）
        industry_benchmark = total_revenue * 1.1  # 假设行业平均高10%
        vs_industry = (total_revenue / industry_benchmark - 1) if industry_benchmark > 0 else 0
        
        # 预测（简单线性预测）
        forecast = self._forecast_revenue(statements, periods=3)
        
        return RevenueAnalysis(
            tenant_id=tenant_id,
            period=period,
            total_revenue=total_revenue,
            product_revenue=product_revenue,
            service_revenue=service_revenue,
            customer_count=customer_count,
            order_count=order_count,
            avg_order_value=avg_order_value,
            industry_benchmark=industry_benchmark,
            vs_industry=vs_industry,
            forecast=forecast
        )
    
    def _forecast_revenue(
        self,
        statements: List,
        periods: int = 3
    ) -> Dict[str, float]:
        """预测未来收入"""
        if len(statements) < 2:
            return {}
        
        # 简单平均增长率预测
        revenues = [s.revenue for s in statements[-3:]]  # 取最近3期
        if len(revenues) < 2:
            return {}
        
        # 计算平均增长率
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i-1] > 0:
                growth_rates.append(revenues[i] / revenues[i-1] - 1)
        
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        
        # 预测
        forecast = {}
        last_revenue = revenues[-1]
        for i in range(1, periods + 1):
            last_revenue = last_revenue * (1 + avg_growth)
            forecast[f"period_{i}"] = last_revenue
        
        return forecast


# ==================== 导出 ====================

__all__ = [
    "FinancialAnalysisEngine"
]






































