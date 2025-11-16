"""
财务管理器
Finance Manager

提供财务数据的创建、查询、更新、分析等核心功能

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from .models import (
    FinancialData,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    FinancialPeriod,
    ProfitAnalysis,
    ExpenseAnalysis,
    RevenueAnalysis
)

logger = logging.getLogger(__name__)


class FinanceManager:
    """财务管理器"""
    
    def __init__(self):
        """初始化财务管理器"""
        # 内存存储（生产环境应使用数据库）
        self.income_statements: Dict[str, List[IncomeStatement]] = defaultdict(list)
        self.balance_sheets: Dict[str, List[BalanceSheet]] = defaultdict(list)
        self.cash_flows: Dict[str, List[CashFlowStatement]] = defaultdict(list)
        
        logger.info("✅ 财务管理器已初始化")
    
    # ==================== 数据导入导出 ====================
    
    def import_financial_data(
        self,
        tenant_id: str,
        data: Dict[str, Any],
        data_type: str = "income_statement"
    ) -> FinancialData:
        """
        导入财务数据
        
        Args:
            tenant_id: 租户ID
            data: 财务数据字典
            data_type: 数据类型（income_statement/balance_sheet/cash_flow）
        
        Returns:
            导入的财务数据对象
        """
        try:
            data["tenant_id"] = tenant_id
            
            if data_type == "income_statement":
                statement = IncomeStatement(**data)
                statement.calculate_metrics()
                self.income_statements[tenant_id].append(statement)
                return statement
            
            elif data_type == "balance_sheet":
                sheet = BalanceSheet(**data)
                sheet.calculate_metrics()
                self.balance_sheets[tenant_id].append(sheet)
                return sheet
            
            elif data_type == "cash_flow":
                flow = CashFlowStatement(**data)
                flow.calculate_metrics()
                self.cash_flows[tenant_id].append(flow)
                return flow
            
            else:
                raise ValueError(f"未知的数据类型: {data_type}")
        
        except Exception as e:
            logger.error(f"导入财务数据失败: {e}")
            raise
    
    def export_financial_data(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        data_type: str = "all"
    ) -> Dict[str, Any]:
        """
        导出财务数据
        
        Args:
            tenant_id: 租户ID
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型
        
        Returns:
            导出的财务数据
        """
        result = {}
        
        # 过滤日期范围
        def filter_by_date(items: List[FinancialData]) -> List[FinancialData]:
            filtered = items
            if start_date:
                filtered = [item for item in filtered if item.date >= start_date]
            if end_date:
                filtered = [item for item in filtered if item.date <= end_date]
            return filtered
        
        if data_type in ["all", "income_statement"]:
            statements = filter_by_date(self.income_statements.get(tenant_id, []))
            result["income_statements"] = [stmt.model_dump() for stmt in statements]
        
        if data_type in ["all", "balance_sheet"]:
            sheets = filter_by_date(self.balance_sheets.get(tenant_id, []))
            result["balance_sheets"] = [sheet.model_dump() for sheet in sheets]
        
        if data_type in ["all", "cash_flow"]:
            flows = filter_by_date(self.cash_flows.get(tenant_id, []))
            result["cash_flows"] = [flow.model_dump() for flow in flows]
        
        return result
    
    # ==================== 查询功能 ====================
    
    def get_income_statements(
        self,
        tenant_id: str,
        period: Optional[FinancialPeriod] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[IncomeStatement]:
        """获取利润表"""
        statements = self.income_statements.get(tenant_id, [])
        
        # 过滤
        if period:
            statements = [s for s in statements if s.period == period]
        if start_date:
            statements = [s for s in statements if s.date >= start_date]
        if end_date:
            statements = [s for s in statements if s.date <= end_date]
        
        return sorted(statements, key=lambda x: x.date)
    
    def get_balance_sheets(
        self,
        tenant_id: str,
        period: Optional[FinancialPeriod] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BalanceSheet]:
        """获取资产负债表"""
        sheets = self.balance_sheets.get(tenant_id, [])
        
        if period:
            sheets = [s for s in sheets if s.period == period]
        if start_date:
            sheets = [s for s in sheets if s.date >= start_date]
        if end_date:
            sheets = [s for s in sheets if s.date <= end_date]
        
        return sorted(sheets, key=lambda x: x.date)
    
    def get_cash_flows(
        self,
        tenant_id: str,
        period: Optional[FinancialPeriod] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CashFlowStatement]:
        """获取现金流量表"""
        flows = self.cash_flows.get(tenant_id, [])
        
        if period:
            flows = [f for f in flows if f.period == period]
        if start_date:
            flows = [f for f in flows if f.date >= start_date]
        if end_date:
            flows = [f for f in flows if f.date <= end_date]
        
        return sorted(flows, key=lambda x: x.date)
    
    # ==================== 聚合分析 ====================
    
    def aggregate_income(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Tuple[float, float, float]:
        """
        聚合利润表数据
        
        Returns:
            (总收入, 总成本, 总利润)
        """
        statements = self.get_income_statements(
            tenant_id, 
            start_date=start_date, 
            end_date=end_date
        )
        
        total_revenue = sum(s.revenue for s in statements)
        total_cost = sum(s.cost_of_goods_sold + s.operating_expenses for s in statements)
        total_profit = sum(s.net_profit for s in statements)
        
        return total_revenue, total_cost, total_profit
    
    def calculate_profit_trend(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        计算利润趋势
        
        Args:
            tenant_id: 租户ID
            period: 周期
            months: 月数
        
        Returns:
            趋势数据列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=30 * months)
        
        statements = self.get_income_statements(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        trend = []
        for stmt in statements:
            trend.append({
                "date": stmt.date.isoformat(),
                "revenue": stmt.revenue,
                "cost": stmt.cost_of_goods_sold + stmt.operating_expenses,
                "profit": stmt.net_profit,
                "margin": stmt.net_margin
            })
        
        return trend
    
    # ==================== 盈亏平衡分析 ====================
    
    def calculate_breakeven(
        self,
        tenant_id: str,
        fixed_costs: Optional[float] = None,
        variable_cost_ratio: Optional[float] = None
    ) -> Tuple[float, int]:
        """
        计算盈亏平衡点
        
        Args:
            tenant_id: 租户ID
            fixed_costs: 固定成本（不提供则自动计算）
            variable_cost_ratio: 变动成本率（不提供则自动计算）
        
        Returns:
            (盈亏平衡点收入, 盈亏平衡点销量)
        """
        # 获取最近的财务数据
        statements = self.get_income_statements(tenant_id)
        if not statements:
            return 0.0, 0
        
        recent = statements[-1]
        
        # 计算固定成本和变动成本
        if fixed_costs is None:
            fixed_costs = recent.operating_expenses
        
        if variable_cost_ratio is None:
            if recent.revenue > 0:
                variable_cost_ratio = recent.cost_of_goods_sold / recent.revenue
            else:
                variable_cost_ratio = 0.5  # 默认50%
        
        # 盈亏平衡点收入 = 固定成本 / (1 - 变动成本率)
        if variable_cost_ratio < 1:
            breakeven_revenue = fixed_costs / (1 - variable_cost_ratio)
        else:
            breakeven_revenue = 0.0
        
        # 假设平均单价
        avg_unit_price = 1000.0  # 可以从历史数据计算
        breakeven_units = int(breakeven_revenue / avg_unit_price) if avg_unit_price > 0 else 0
        
        return breakeven_revenue, breakeven_units
    
    # ==================== 关键因素分析 ====================
    
    def identify_key_factors(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY
    ) -> List[Dict[str, Any]]:
        """
        识别影响利润的关键因素
        
        Returns:
            关键因素列表
        """
        statements = self.get_income_statements(tenant_id, period=period)
        if len(statements) < 2:
            return []
        
        # 比较最近两期
        current = statements[-1]
        previous = statements[-2] if len(statements) > 1 else current
        
        factors = []
        
        # 收入变化
        revenue_change = current.revenue - previous.revenue
        if abs(revenue_change) > 0:
            impact = revenue_change / previous.revenue if previous.revenue > 0 else 0
            factors.append({
                "factor": "收入变化",
                "change": revenue_change,
                "impact": impact,
                "description": f"收入{'增长' if revenue_change > 0 else '下降'} {abs(revenue_change):.2f}"
            })
        
        # 成本变化
        cost_change = (current.cost_of_goods_sold - previous.cost_of_goods_sold)
        if abs(cost_change) > 0:
            impact = -cost_change / previous.cost_of_goods_sold if previous.cost_of_goods_sold > 0 else 0
            factors.append({
                "factor": "成本变化",
                "change": cost_change,
                "impact": impact,
                "description": f"成本{'增加' if cost_change > 0 else '减少'} {abs(cost_change):.2f}"
            })
        
        # 费用变化
        expense_change = (current.operating_expenses - previous.operating_expenses)
        if abs(expense_change) > 0:
            impact = -expense_change / previous.operating_expenses if previous.operating_expenses > 0 else 0
            factors.append({
                "factor": "费用变化",
                "change": expense_change,
                "impact": impact,
                "description": f"费用{'增加' if expense_change > 0 else '减少'} {abs(expense_change):.2f}"
            })
        
        # 按影响程度排序
        factors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return factors
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """获取财务统计信息"""
        return {
            "income_statements_count": len(self.income_statements.get(tenant_id, [])),
            "balance_sheets_count": len(self.balance_sheets.get(tenant_id, [])),
            "cash_flows_count": len(self.cash_flows.get(tenant_id, [])),
            "latest_date": self._get_latest_date(tenant_id)
        }
    
    def _get_latest_date(self, tenant_id: str) -> Optional[str]:
        """获取最新数据日期"""
        all_dates = []
        
        for stmt in self.income_statements.get(tenant_id, []):
            all_dates.append(stmt.date)
        for sheet in self.balance_sheets.get(tenant_id, []):
            all_dates.append(sheet.date)
        for flow in self.cash_flows.get(tenant_id, []):
            all_dates.append(flow.date)
        
        if all_dates:
            return max(all_dates).isoformat()
        return None


# ==================== 全局实例 ====================

finance_manager = FinanceManager()


# ==================== 导出 ====================

__all__ = [
    "FinanceManager",
    "finance_manager"
]






















