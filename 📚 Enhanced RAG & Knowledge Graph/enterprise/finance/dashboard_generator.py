"""
财务看板生成器
Dashboard Generator

生成日/周/月/季/年的自主财务看板

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from .models import FinancialPeriod
from .finance_manager import finance_manager
from .analysis_engine import FinancialAnalysisEngine

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """财务看板生成器"""
    
    def __init__(self):
        """初始化看板生成器"""
        self.analysis_engine = FinancialAnalysisEngine()
        logger.info("✅ 财务看板生成器已初始化")
    
    def generate_dashboard(
        self,
        tenant_id: str,
        period: FinancialPeriod = FinancialPeriod.MONTHLY,
        date_range: Optional[tuple[date, date]] = None
    ) -> Dict[str, Any]:
        """
        生成财务看板
        
        Args:
            tenant_id: 租户ID
            period: 周期（日/周/月/季/年）
            date_range: 日期范围
        
        Returns:
            看板数据
        """
        # 确定日期范围
        if not date_range:
            end_date = date.today()
            if period == FinancialPeriod.DAILY:
                start_date = end_date - timedelta(days=30)
            elif period == FinancialPeriod.WEEKLY:
                start_date = end_date - timedelta(weeks=12)
            elif period == FinancialPeriod.MONTHLY:
                start_date = end_date - timedelta(days=365)
            elif period == FinancialPeriod.QUARTERLY:
                start_date = end_date - timedelta(days=365*2)
            else:  # YEARLY
                start_date = end_date - timedelta(days=365*5)
            date_range = (start_date, end_date)
        
        start_date, end_date = date_range
        
        # 获取核心指标
        core_metrics = self._get_core_metrics(tenant_id, start_date, end_date)
        
        # 获取趋势数据
        trend_data = self._get_trend_data(tenant_id, period)
        
        # 获取分析结果
        profit_analysis = self.analysis_engine.analyze_profit(
            tenant_id, period, start_date, end_date
        )
        expense_analysis = self.analysis_engine.analyze_expenses(
            tenant_id, period, start_date, end_date
        )
        revenue_analysis = self.analysis_engine.analyze_revenue(
            tenant_id, period, start_date, end_date
        )
        
        # 获取对比数据
        comparison = self._get_period_comparison(tenant_id, period)
        
        # 生成仪表板
        dashboard = {
            "period": period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "core_metrics": core_metrics,
            "trend": trend_data,
            "profit_analysis": profit_analysis.model_dump(),
            "expense_analysis": expense_analysis.model_dump(),
            "revenue_analysis": revenue_analysis.model_dump(),
            "comparison": comparison,
            "alerts": self._generate_alerts(
                profit_analysis,
                expense_analysis,
                revenue_analysis
            )
        }
        
        return dashboard
    
    def _get_core_metrics(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """获取核心财务指标"""
        # 聚合数据
        total_revenue, total_cost, total_profit = finance_manager.aggregate_income(
            tenant_id, start_date, end_date
        )
        
        # 计算率
        profit_margin = total_profit / total_revenue if total_revenue > 0 else 0
        cost_ratio = total_cost / total_revenue if total_revenue > 0 else 0
        
        # 获取资产负债
        balance_sheets = finance_manager.get_balance_sheets(
            tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        latest_assets = balance_sheets[-1].total_assets if balance_sheets else 0
        latest_liabilities = balance_sheets[-1].total_liabilities if balance_sheets else 0
        latest_equity = balance_sheets[-1].equity if balance_sheets else 0
        
        # 获取现金流
        cash_flows = finance_manager.get_cash_flows(
            tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        latest_cash = cash_flows[-1].ending_cash if cash_flows else 0
        
        return {
            "revenue": {
                "value": total_revenue,
                "label": "总收入"
            },
            "cost": {
                "value": total_cost,
                "label": "总成本"
            },
            "profit": {
                "value": total_profit,
                "label": "总利润"
            },
            "profit_margin": {
                "value": profit_margin,
                "label": "利润率",
                "format": "percentage"
            },
            "assets": {
                "value": latest_assets,
                "label": "总资产"
            },
            "liabilities": {
                "value": latest_liabilities,
                "label": "总负债"
            },
            "equity": {
                "value": latest_equity,
                "label": "所有者权益"
            },
            "cash": {
                "value": latest_cash,
                "label": "现金余额"
            }
        }
    
    def _get_trend_data(
        self,
        tenant_id: str,
        period: FinancialPeriod
    ) -> Dict[str, List[Dict[str, Any]]]:
        """获取趋势数据"""
        # 获取利润趋势
        months = {
            FinancialPeriod.DAILY: 1,
            FinancialPeriod.WEEKLY: 3,
            FinancialPeriod.MONTHLY: 12,
            FinancialPeriod.QUARTERLY: 8,
            FinancialPeriod.YEARLY: 5
        }.get(period, 12)
        
        profit_trend = finance_manager.calculate_profit_trend(
            tenant_id, period, months
        )
        
        return {
            "profit": profit_trend
        }
    
    def _get_period_comparison(
        self,
        tenant_id: str,
        period: FinancialPeriod
    ) -> Dict[str, Any]:
        """获取期间对比数据"""
        statements = finance_manager.get_income_statements(tenant_id, period=period)
        
        if len(statements) < 2:
            return {
                "available": False,
                "message": "数据不足，无法对比"
            }
        
        current = statements[-1]
        previous = statements[-2]
        
        # 计算变化
        revenue_change = current.revenue - previous.revenue
        revenue_change_pct = revenue_change / previous.revenue if previous.revenue > 0 else 0
        
        profit_change = current.net_profit - previous.net_profit
        profit_change_pct = profit_change / previous.net_profit if previous.net_profit != 0 else 0
        
        return {
            "available": True,
            "current_period": current.date.isoformat(),
            "previous_period": previous.date.isoformat(),
            "revenue": {
                "current": current.revenue,
                "previous": previous.revenue,
                "change": revenue_change,
                "change_pct": revenue_change_pct
            },
            "profit": {
                "current": current.net_profit,
                "previous": previous.net_profit,
                "change": profit_change,
                "change_pct": profit_change_pct
            }
        }
    
    def _generate_alerts(
        self,
        profit_analysis,
        expense_analysis,
        revenue_analysis
    ) -> List[Dict[str, Any]]:
        """生成警报"""
        alerts = []
        
        # 利润警报
        if profit_analysis.profit_margin < 0:
            alerts.append({
                "level": "critical",
                "type": "profit",
                "message": "当前处于亏损状态",
                "detail": f"利润率: {profit_analysis.profit_margin:.1%}"
            })
        elif profit_analysis.profit_margin < 0.1:
            alerts.append({
                "level": "warning",
                "type": "profit",
                "message": "利润率偏低",
                "detail": f"利润率: {profit_analysis.profit_margin:.1%}"
            })
        
        # 费用警报
        if expense_analysis.reasonableness_score < 70:
            alerts.append({
                "level": "warning",
                "type": "expense",
                "message": "费用结构不合理",
                "detail": f"合理性评分: {expense_analysis.reasonableness_score:.0f}/100"
            })
        
        # 收入警报
        if revenue_analysis.vs_industry < -0.2:
            alerts.append({
                "level": "info",
                "type": "revenue",
                "message": "收入低于行业平均",
                "detail": f"低于行业: {revenue_analysis.vs_industry:.1%}"
            })
        
        return alerts


# ==================== 导出 ====================

__all__ = [
    "DashboardGenerator"
]

















