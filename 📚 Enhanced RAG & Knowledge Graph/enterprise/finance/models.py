"""
财务数据模型
Financial Data Models

定义所有财务相关的数据结构

版本: v1.0.0
"""

from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ==================== 枚举类型 ====================

class FinancialPeriod(str, Enum):
    """财务周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ExpenseCategory(str, Enum):
    """费用类别"""
    SALES = "sales"              # 销售费用
    FINANCE = "finance"          # 财务费用
    MANAGEMENT = "management"    # 管理费用
    LABOR = "labor"              # 生产人工
    MANUFACTURING = "manufacturing"  # 制造费用
    MATERIAL = "material"        # 材料费用


class RevenueCategory(str, Enum):
    """收入类别"""
    PRODUCT_SALES = "product_sales"  # 产品销售
    SERVICE = "service"              # 服务收入
    OTHER = "other"                  # 其他收入


# ==================== 财务数据 ====================

class FinancialData(BaseModel):
    """财务数据基类"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="数据ID")
    tenant_id: str = Field(..., description="租户ID")
    date: date = Field(..., description="日期")
    period: FinancialPeriod = Field(..., description="周期")
    
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ==================== 利润表 ====================

class IncomeStatement(FinancialData):
    """利润表"""
    
    # 收入
    revenue: float = Field(0.0, description="总收入")
    product_revenue: float = Field(0.0, description="产品收入")
    service_revenue: float = Field(0.0, description="服务收入")
    other_revenue: float = Field(0.0, description="其他收入")
    
    # 成本
    cost_of_goods_sold: float = Field(0.0, description="销售成本")
    material_cost: float = Field(0.0, description="材料成本")
    labor_cost: float = Field(0.0, description="人工成本")
    manufacturing_cost: float = Field(0.0, description="制造费用")
    
    # 毛利润
    gross_profit: float = Field(0.0, description="毛利润")
    gross_margin: float = Field(0.0, description="毛利率")
    
    # 费用
    operating_expenses: float = Field(0.0, description="营业费用")
    sales_expenses: float = Field(0.0, description="销售费用")
    management_expenses: float = Field(0.0, description="管理费用")
    finance_expenses: float = Field(0.0, description="财务费用")
    
    # 营业利润
    operating_profit: float = Field(0.0, description="营业利润")
    operating_margin: float = Field(0.0, description="营业利润率")
    
    # 净利润
    net_profit: float = Field(0.0, description="净利润")
    net_margin: float = Field(0.0, description="净利率")
    
    def calculate_metrics(self):
        """计算财务指标"""
        # 毛利润 = 收入 - 销售成本
        self.gross_profit = self.revenue - self.cost_of_goods_sold
        if self.revenue > 0:
            self.gross_margin = self.gross_profit / self.revenue
        
        # 营业利润 = 毛利润 - 营业费用
        self.operating_profit = self.gross_profit - self.operating_expenses
        if self.revenue > 0:
            self.operating_margin = self.operating_profit / self.revenue
        
        # 净利润 = 营业利润（简化版）
        self.net_profit = self.operating_profit
        if self.revenue > 0:
            self.net_margin = self.net_profit / self.revenue


# ==================== 资产负债表 ====================

class BalanceSheet(FinancialData):
    """资产负债表"""
    
    # 资产
    total_assets: float = Field(0.0, description="总资产")
    current_assets: float = Field(0.0, description="流动资产")
    cash: float = Field(0.0, description="现金及现金等价物")
    accounts_receivable: float = Field(0.0, description="应收账款")
    inventory: float = Field(0.0, description="存货")
    fixed_assets: float = Field(0.0, description="固定资产")
    
    # 负债
    total_liabilities: float = Field(0.0, description="总负债")
    current_liabilities: float = Field(0.0, description="流动负债")
    accounts_payable: float = Field(0.0, description="应付账款")
    short_term_debt: float = Field(0.0, description="短期借款")
    long_term_debt: float = Field(0.0, description="长期借款")
    
    # 所有者权益
    equity: float = Field(0.0, description="所有者权益")
    
    # 财务比率
    current_ratio: float = Field(0.0, description="流动比率")
    debt_ratio: float = Field(0.0, description="资产负债率")
    
    def calculate_metrics(self):
        """计算财务指标"""
        # 所有者权益 = 资产 - 负债
        self.equity = self.total_assets - self.total_liabilities
        
        # 流动比率 = 流动资产 / 流动负债
        if self.current_liabilities > 0:
            self.current_ratio = self.current_assets / self.current_liabilities
        
        # 资产负债率 = 总负债 / 总资产
        if self.total_assets > 0:
            self.debt_ratio = self.total_liabilities / self.total_assets


# ==================== 现金流量表 ====================

class CashFlowStatement(FinancialData):
    """现金流量表"""
    
    # 经营活动现金流
    operating_cash_flow: float = Field(0.0, description="经营活动现金流")
    cash_from_sales: float = Field(0.0, description="销售商品收到的现金")
    cash_to_suppliers: float = Field(0.0, description="支付给供应商的现金")
    cash_to_employees: float = Field(0.0, description="支付给员工的现金")
    
    # 投资活动现金流
    investing_cash_flow: float = Field(0.0, description="投资活动现金流")
    cash_for_assets: float = Field(0.0, description="购置资产支付的现金")
    
    # 筹资活动现金流
    financing_cash_flow: float = Field(0.0, description="筹资活动现金流")
    cash_from_borrowing: float = Field(0.0, description="借款收到的现金")
    cash_for_repayment: float = Field(0.0, description="偿还债务支付的现金")
    
    # 现金净增加额
    net_cash_increase: float = Field(0.0, description="现金净增加额")
    beginning_cash: float = Field(0.0, description="期初现金")
    ending_cash: float = Field(0.0, description="期末现金")
    
    def calculate_metrics(self):
        """计算现金流指标"""
        # 现金净增加额
        self.net_cash_increase = (
            self.operating_cash_flow +
            self.investing_cash_flow +
            self.financing_cash_flow
        )
        
        # 期末现金 = 期初现金 + 现金净增加额
        self.ending_cash = self.beginning_cash + self.net_cash_increase


# ==================== 分析结果 ====================

class ProfitAnalysis(BaseModel):
    """盈亏分析结果"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="分析ID")
    tenant_id: str = Field(..., description="租户ID")
    period: FinancialPeriod = Field(..., description="分析周期")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    
    # 核心指标
    total_revenue: float = Field(0.0, description="总收入")
    total_cost: float = Field(0.0, description="总成本")
    total_profit: float = Field(0.0, description="总利润")
    profit_margin: float = Field(0.0, description="利润率")
    
    # 盈亏平衡点
    breakeven_revenue: float = Field(0.0, description="盈亏平衡点收入")
    breakeven_units: int = Field(0, description="盈亏平衡点销量")
    
    # 趋势
    revenue_trend: str = Field("", description="收入趋势")
    profit_trend: str = Field("", description="利润趋势")
    
    # 关键因素
    key_factors: List[Dict[str, Any]] = Field(default_factory=list, description="关键影响因素")
    
    # 建议
    recommendations: List[str] = Field(default_factory=list, description="经营建议")
    
    created_at: datetime = Field(default_factory=datetime.now, description="分析时间")


class ExpenseAnalysis(BaseModel):
    """费用分析结果"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="分析ID")
    tenant_id: str = Field(..., description="租户ID")
    period: FinancialPeriod = Field(..., description="分析周期")
    
    # 费用明细
    total_expenses: float = Field(0.0, description="总费用")
    sales_expenses: float = Field(0.0, description="销售费用")
    management_expenses: float = Field(0.0, description="管理费用")
    finance_expenses: float = Field(0.0, description="财务费用")
    labor_costs: float = Field(0.0, description="人工成本")
    material_costs: float = Field(0.0, description="材料成本")
    manufacturing_costs: float = Field(0.0, description="制造费用")
    
    # 费用占比
    expense_ratios: Dict[str, float] = Field(default_factory=dict, description="费用占比")
    
    # 合理性评估
    reasonableness_score: float = Field(0.0, description="合理性评分 (0-100)")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    recommendations: List[str] = Field(default_factory=list, description="优化建议")
    
    created_at: datetime = Field(default_factory=datetime.now, description="分析时间")


class RevenueAnalysis(BaseModel):
    """收入分析结果"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="分析ID")
    tenant_id: str = Field(..., description="租户ID")
    period: FinancialPeriod = Field(..., description="分析周期")
    
    # 收入明细
    total_revenue: float = Field(0.0, description="总收入")
    product_revenue: float = Field(0.0, description="产品收入")
    service_revenue: float = Field(0.0, description="服务收入")
    
    # 客户分析
    customer_count: int = Field(0, description="客户数量")
    order_count: int = Field(0, description="订单数量")
    avg_order_value: float = Field(0.0, description="平均订单金额")
    
    # 项目影响
    new_projects_impact: Dict[str, float] = Field(
        default_factory=dict, 
        description="新项目对各期的影响"
    )
    
    # 行业对比
    industry_benchmark: float = Field(0.0, description="行业基准")
    vs_industry: float = Field(0.0, description="相对行业表现")
    
    # 趋势预测
    forecast: Dict[str, float] = Field(default_factory=dict, description="收入预测")
    
    created_at: datetime = Field(default_factory=datetime.now, description="分析时间")


# ==================== 导出 ====================

__all__ = [
    "FinancialPeriod",
    "ExpenseCategory",
    "RevenueCategory",
    "FinancialData",
    "IncomeStatement",
    "BalanceSheet",
    "CashFlowStatement",
    "ProfitAnalysis",
    "ExpenseAnalysis",
    "RevenueAnalysis"
]






































