"""
财务报表生成器
Report Generator

生成各类财务报表

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional
import json

from .models import FinancialPeriod
from .finance_manager import finance_manager

logger = logging.getLogger(__name__)


class ReportGenerator:
    """财务报表生成器"""
    
    def __init__(self):
        """初始化报表生成器"""
        logger.info("✅ 财务报表生成器已初始化")
    
    def generate_income_statement_report(
        self,
        tenant_id: str,
        period: FinancialPeriod,
        start_date: date,
        end_date: date,
        format: str = "json"
    ) -> Any:
        """
        生成利润表报告
        
        Args:
            tenant_id: 租户ID
            period: 周期
            start_date: 开始日期
            end_date: 结束日期
            format: 格式（json/html/excel）
        
        Returns:
            报告数据
        """
        statements = finance_manager.get_income_statements(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "json":
            return self._format_income_statement_json(statements)
        elif format == "html":
            return self._format_income_statement_html(statements)
        elif format == "excel":
            return self._format_income_statement_excel(statements)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _format_income_statement_json(self, statements: List) -> Dict[str, Any]:
        """格式化为JSON"""
        return {
            "report_type": "income_statement",
            "count": len(statements),
            "data": [stmt.model_dump() for stmt in statements],
            "summary": self._calculate_income_summary(statements)
        }
    
    def _format_income_statement_html(self, statements: List) -> str:
        """格式化为HTML"""
        html = """
        <html>
        <head><title>利润表</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
        </style>
        </head>
        <body>
        <h1>利润表</h1>
        <table>
        <tr>
            <th>日期</th>
            <th>收入</th>
            <th>成本</th>
            <th>毛利润</th>
            <th>费用</th>
            <th>净利润</th>
            <th>利润率</th>
        </tr>
        """
        
        for stmt in statements:
            html += f"""
            <tr>
                <td>{stmt.date}</td>
                <td>{stmt.revenue:.2f}</td>
                <td>{stmt.cost_of_goods_sold:.2f}</td>
                <td>{stmt.gross_profit:.2f}</td>
                <td>{stmt.operating_expenses:.2f}</td>
                <td>{stmt.net_profit:.2f}</td>
                <td>{stmt.net_margin:.1%}</td>
            </tr>
            """
        
        html += """
        </table>
        </body>
        </html>
        """
        
        return html
    
    def _format_income_statement_excel(self, statements: List) -> Dict[str, Any]:
        """格式化为Excel数据（实际生成Excel需要额外库）"""
        headers = ["日期", "收入", "成本", "毛利润", "费用", "净利润", "利润率"]
        rows = []
        
        for stmt in statements:
            rows.append([
                stmt.date.isoformat(),
                stmt.revenue,
                stmt.cost_of_goods_sold,
                stmt.gross_profit,
                stmt.operating_expenses,
                stmt.net_profit,
                f"{stmt.net_margin:.1%}"
            ])
        
        return {
            "headers": headers,
            "rows": rows
        }
    
    def _calculate_income_summary(self, statements: List) -> Dict[str, float]:
        """计算利润表汇总"""
        if not statements:
            return {}
        
        total_revenue = sum(s.revenue for s in statements)
        total_cost = sum(s.cost_of_goods_sold for s in statements)
        total_profit = sum(s.net_profit for s in statements)
        
        return {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "average_margin": total_profit / total_revenue if total_revenue > 0 else 0
        }
    
    def generate_balance_sheet_report(
        self,
        tenant_id: str,
        period: FinancialPeriod,
        start_date: date,
        end_date: date,
        format: str = "json"
    ) -> Any:
        """生成资产负债表报告"""
        sheets = finance_manager.get_balance_sheets(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "json":
            return {
                "report_type": "balance_sheet",
                "count": len(sheets),
                "data": [sheet.model_dump() for sheet in sheets]
            }
        else:
            # 简化处理，其他格式类似
            return {"message": f"格式{format}正在开发中"}
    
    def generate_cash_flow_report(
        self,
        tenant_id: str,
        period: FinancialPeriod,
        start_date: date,
        end_date: date,
        format: str = "json"
    ) -> Any:
        """生成现金流量表报告"""
        flows = finance_manager.get_cash_flows(
            tenant_id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "json":
            return {
                "report_type": "cash_flow",
                "count": len(flows),
                "data": [flow.model_dump() for flow in flows]
            }
        else:
            return {"message": f"格式{format}正在开发中"}


# ==================== 导出 ====================

__all__ = [
    "ReportGenerator"
]






















