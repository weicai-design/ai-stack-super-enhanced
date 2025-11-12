"""
ERP系统 - 预算管理模块
支持预算编制、执行监控、分析预警
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BudgetPeriod(str, Enum):
    """预算周期"""
    ANNUAL = "annual"  # 年度
    QUARTERLY = "quarterly"  # 季度
    MONTHLY = "monthly"  # 月度


class BudgetCategory(str, Enum):
    """预算类别"""
    REVENUE = "revenue"  # 收入预算
    COST = "cost"  # 成本预算
    EXPENSE = "expense"  # 费用预算
    INVESTMENT = "investment"  # 投资预算


class Budget(BaseModel):
    """预算模型"""
    id: Optional[int] = None
    name: str  # 预算名称
    category: BudgetCategory  # 预算类别
    period: BudgetPeriod  # 预算周期
    year: int  # 年度
    quarter: Optional[int] = None  # 季度（1-4）
    month: Optional[int] = None  # 月份（1-12）
    department: str  # 部门
    amount: Decimal  # 预算金额
    description: str = ""  # 描述
    status: str = "draft"  # 状态（draft/approved/executing/closed）
    created_at: datetime = datetime.now()
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class BudgetExecution(BaseModel):
    """预算执行记录"""
    id: Optional[int] = None
    budget_id: int  # 预算ID
    actual_amount: Decimal  # 实际金额
    execution_date: date  # 执行日期
    description: str = ""  # 说明
    created_at: datetime = datetime.now()


class BudgetAnalysis(BaseModel):
    """预算分析结果"""
    budget_id: int
    budget_amount: Decimal  # 预算金额
    actual_amount: Decimal  # 实际金额
    variance: Decimal  # 差异
    variance_rate: Decimal  # 差异率（%）
    execution_rate: Decimal  # 执行率（%）
    status: str  # 状态（under/match/over）


class BudgetManager:
    """
    预算管理器
    
    功能：
    - 预算编制和审批
    - 预算执行监控
    - 预算分析和预警
    - 预算报表生成
    """
    
    def __init__(self):
        """初始化预算管理器"""
        self.budgets: List[Budget] = []
        self.executions: List[BudgetExecution] = []
        self.alert_threshold = Decimal("0.9")  # 预警阈值（90%）
    
    def create_budget(self, budget: Budget) -> Budget:
        """
        创建预算
        
        Args:
            budget: 预算对象
            
        Returns:
            创建的预算
        """
        if budget.id is None:
            budget.id = len(self.budgets) + 1
        
        self.budgets.append(budget)
        logger.info(f"创建预算: {budget.name} - {budget.amount}")
        
        return budget
    
    def approve_budget(self, budget_id: int, approver: str) -> bool:
        """
        审批预算
        
        Args:
            budget_id: 预算ID
            approver: 审批人
            
        Returns:
            是否审批成功
        """
        budget = self.get_budget(budget_id)
        if not budget:
            logger.error(f"预算不存在: {budget_id}")
            return False
        
        budget.status = "approved"
        budget.approved_at = datetime.now()
        budget.approved_by = approver
        
        logger.info(f"预算已审批: {budget.name} by {approver}")
        return True
    
    def get_budget(self, budget_id: int) -> Optional[Budget]:
        """获取预算"""
        for budget in self.budgets:
            if budget.id == budget_id:
                return budget
        return None
    
    def list_budgets(
        self,
        year: Optional[int] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Budget]:
        """
        列出预算
        
        Args:
            year: 年度筛选
            department: 部门筛选
            status: 状态筛选
            
        Returns:
            预算列表
        """
        filtered = self.budgets
        
        if year:
            filtered = [b for b in filtered if b.year == year]
        if department:
            filtered = [b for b in filtered if b.department == department]
        if status:
            filtered = [b for b in filtered if b.status == status]
        
        return filtered
    
    def record_execution(self, execution: BudgetExecution) -> BudgetExecution:
        """
        记录预算执行
        
        Args:
            execution: 执行记录
            
        Returns:
            执行记录
        """
        if execution.id is None:
            execution.id = len(self.executions) + 1
        
        self.executions.append(execution)
        logger.info(
            f"记录预算执行: Budget#{execution.budget_id} - {execution.actual_amount}"
        )
        
        # 检查是否需要预警
        self._check_budget_alert(execution.budget_id)
        
        return execution
    
    def get_budget_execution(self, budget_id: int) -> List[BudgetExecution]:
        """获取预算执行记录"""
        return [e for e in self.executions if e.budget_id == budget_id]
    
    def analyze_budget(self, budget_id: int) -> Optional[BudgetAnalysis]:
        """
        分析预算执行情况
        
        Args:
            budget_id: 预算ID
            
        Returns:
            预算分析结果
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return None
        
        # 计算实际金额
        executions = self.get_budget_execution(budget_id)
        actual_amount = sum(e.actual_amount for e in executions)
        
        # 计算差异
        variance = budget.amount - actual_amount
        variance_rate = (variance / budget.amount * 100) if budget.amount else Decimal("0")
        execution_rate = (actual_amount / budget.amount * 100) if budget.amount else Decimal("0")
        
        # 判断状态
        if actual_amount < budget.amount * Decimal("0.9"):
            status = "under"  # 执行不足
        elif actual_amount > budget.amount:
            status = "over"  # 超支
        else:
            status = "match"  # 正常
        
        analysis = BudgetAnalysis(
            budget_id=budget_id,
            budget_amount=budget.amount,
            actual_amount=actual_amount,
            variance=variance,
            variance_rate=variance_rate,
            execution_rate=execution_rate,
            status=status
        )
        
        return analysis
    
    def _check_budget_alert(self, budget_id: int):
        """检查预算预警"""
        analysis = self.analyze_budget(budget_id)
        if not analysis:
            return
        
        # 超支预警
        if analysis.status == "over":
            logger.warning(
                f"预算超支预警: Budget#{budget_id}, "
                f"预算{analysis.budget_amount}, "
                f"实际{analysis.actual_amount}, "
                f"超支{abs(analysis.variance)}"
            )
        
        # 即将用完预警
        elif analysis.execution_rate >= self.alert_threshold * 100:
            logger.warning(
                f"预算即将用完: Budget#{budget_id}, "
                f"执行率{analysis.execution_rate}%"
            )
    
    def get_budget_report(
        self,
        year: int,
        department: Optional[str] = None
    ) -> Dict[str, any]:
        """
        生成预算报表
        
        Args:
            year: 年度
            department: 部门（可选）
            
        Returns:
            预算报表
        """
        budgets = self.list_budgets(year=year, department=department)
        
        report_data = []
        total_budget = Decimal("0")
        total_actual = Decimal("0")
        
        for budget in budgets:
            analysis = self.analyze_budget(budget.id)
            if analysis:
                report_data.append({
                    "budget_name": budget.name,
                    "department": budget.department,
                    "category": budget.category,
                    "budget_amount": float(analysis.budget_amount),
                    "actual_amount": float(analysis.actual_amount),
                    "variance": float(analysis.variance),
                    "execution_rate": float(analysis.execution_rate),
                    "status": analysis.status
                })
                
                total_budget += analysis.budget_amount
                total_actual += analysis.actual_amount
        
        report = {
            "year": year,
            "department": department or "全部",
            "summary": {
                "total_budget": float(total_budget),
                "total_actual": float(total_actual),
                "total_variance": float(total_budget - total_actual),
                "overall_execution_rate": float(
                    (total_actual / total_budget * 100) if total_budget else 0
                )
            },
            "details": report_data
        }
        
        logger.info(f"生成预算报表: {year}年")
        return report


# 全局实例
_budget_manager: Optional[BudgetManager] = None


def get_budget_manager() -> BudgetManager:
    """获取全局预算管理器实例"""
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager


# 使用示例
def example_usage():
    """使用示例"""
    
    manager = get_budget_manager()
    
    # 1. 创建年度预算
    budget = Budget(
        name="2025年度营销预算",
        category=BudgetCategory.EXPENSE,
        period=BudgetPeriod.ANNUAL,
        year=2025,
        department="市场部",
        amount=Decimal("1000000"),
        description="年度营销推广预算"
    )
    
    budget = manager.create_budget(budget)
    print(f"创建预算: {budget.name}")
    
    # 2. 审批预算
    manager.approve_budget(budget.id, approver="财务总监")
    
    # 3. 记录执行
    execution = BudgetExecution(
        budget_id=budget.id,
        actual_amount=Decimal("100000"),
        execution_date=date.today(),
        description="Q1营销活动"
    )
    manager.record_execution(execution)
    
    # 4. 分析预算
    analysis = manager.analyze_budget(budget.id)
    print(f"执行率: {analysis.execution_rate}%")
    print(f"剩余预算: {analysis.variance}")
    
    # 5. 生成报表
    report = manager.get_budget_report(year=2025, department="市场部")
    print(f"预算报表: {report['summary']}")


if __name__ == "__main__":
    example_usage()


















