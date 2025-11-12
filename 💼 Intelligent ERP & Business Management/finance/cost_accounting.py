"""
ERP系统 - 成本核算模块
支持成本中心、成本分摊、成本分析
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CostType(str, Enum):
    """成本类型"""
    DIRECT_MATERIAL = "direct_material"  # 直接材料
    DIRECT_LABOR = "direct_labor"  # 直接人工
    MANUFACTURING_OVERHEAD = "manufacturing_overhead"  # 制造费用
    SELLING_EXPENSE = "selling_expense"  # 销售费用
    ADMIN_EXPENSE = "admin_expense"  # 管理费用
    FINANCE_EXPENSE = "finance_expense"  # 财务费用


class CostCenter(BaseModel):
    """成本中心模型"""
    id: Optional[int] = None
    code: str  # 成本中心代码
    name: str  # 成本中心名称
    department: str  # 所属部门
    manager: str  # 负责人
    is_active: bool = True
    created_at: datetime = datetime.now()


class CostItem(BaseModel):
    """成本项目模型"""
    id: Optional[int] = None
    cost_center_id: int  # 成本中心ID
    cost_type: CostType  # 成本类型
    item_name: str  # 项目名称
    amount: Decimal  # 金额
    quantity: Optional[Decimal] = None  # 数量
    unit_cost: Optional[Decimal] = None  # 单位成本
    date: date  # 发生日期
    reference: Optional[str] = None  # 关联单据
    description: str = ""  # 说明
    created_at: datetime = datetime.now()


class CostAllocation(BaseModel):
    """成本分摊记录"""
    id: Optional[int] = None
    source_cost_center: int  # 源成本中心
    target_cost_centers: List[int]  # 目标成本中心列表
    total_amount: Decimal  # 总金额
    allocation_method: str  # 分摊方法（equal/ratio/driver）
    allocation_date: date  # 分摊日期
    description: str = ""


class CostAccountingManager:
    """
    成本核算管理器
    
    功能：
    - 成本中心管理
    - 成本项目记录
    - 成本分摊
    - 成本分析和报表
    """
    
    def __init__(self):
        """初始化成本核算管理器"""
        self.cost_centers: List[CostCenter] = []
        self.cost_items: List[CostItem] = []
        self.allocations: List[CostAllocation] = []
    
    def create_cost_center(self, cost_center: CostCenter) -> CostCenter:
        """
        创建成本中心
        
        Args:
            cost_center: 成本中心对象
            
        Returns:
            创建的成本中心
        """
        if cost_center.id is None:
            cost_center.id = len(self.cost_centers) + 1
        
        self.cost_centers.append(cost_center)
        logger.info(f"创建成本中心: {cost_center.code} - {cost_center.name}")
        
        return cost_center
    
    def get_cost_center(self, cost_center_id: int) -> Optional[CostCenter]:
        """获取成本中心"""
        for center in self.cost_centers:
            if center.id == cost_center_id:
                return center
        return None
    
    def list_cost_centers(
        self,
        department: Optional[str] = None,
        active_only: bool = True
    ) -> List[CostCenter]:
        """
        列出成本中心
        
        Args:
            department: 部门筛选
            active_only: 是否只返回激活的
            
        Returns:
            成本中心列表
        """
        filtered = self.cost_centers
        
        if department:
            filtered = [c for c in filtered if c.department == department]
        if active_only:
            filtered = [c for c in filtered if c.is_active]
        
        return filtered
    
    def record_cost(self, cost_item: CostItem) -> CostItem:
        """
        记录成本
        
        Args:
            cost_item: 成本项目
            
        Returns:
            成本项目
        """
        if cost_item.id is None:
            cost_item.id = len(self.cost_items) + 1
        
        # 如果有数量和单位成本，计算金额
        if cost_item.quantity and cost_item.unit_cost:
            cost_item.amount = cost_item.quantity * cost_item.unit_cost
        
        self.cost_items.append(cost_item)
        logger.info(
            f"记录成本: {cost_item.item_name} - {cost_item.amount}"
        )
        
        return cost_item
    
    def get_cost_items(
        self,
        cost_center_id: Optional[int] = None,
        cost_type: Optional[CostType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CostItem]:
        """
        获取成本项目
        
        Args:
            cost_center_id: 成本中心ID
            cost_type: 成本类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            成本项目列表
        """
        filtered = self.cost_items
        
        if cost_center_id:
            filtered = [c for c in filtered if c.cost_center_id == cost_center_id]
        if cost_type:
            filtered = [c for c in filtered if c.cost_type == cost_type]
        if start_date:
            filtered = [c for c in filtered if c.date >= start_date]
        if end_date:
            filtered = [c for c in filtered if c.date <= end_date]
        
        return filtered
    
    def allocate_cost(
        self,
        source_center: int,
        target_centers: List[int],
        amount: Decimal,
        method: str = "equal"
    ) -> CostAllocation:
        """
        分摊成本
        
        Args:
            source_center: 源成本中心
            target_centers: 目标成本中心列表
            amount: 总金额
            method: 分摊方法
                - equal: 平均分摊
                - ratio: 按比例分摊
                - driver: 按动因分摊
            
        Returns:
            成本分摊记录
        """
        allocation = CostAllocation(
            id=len(self.allocations) + 1,
            source_cost_center=source_center,
            target_cost_centers=target_centers,
            total_amount=amount,
            allocation_method=method,
            allocation_date=datetime.now().date()
        )
        
        # 执行分摊
        if method == "equal":
            # 平均分摊
            per_center_amount = amount / len(target_centers)
            
            for target_id in target_centers:
                cost_item = CostItem(
                    cost_center_id=target_id,
                    cost_type=CostType.MANUFACTURING_OVERHEAD,
                    item_name=f"成本分摊自{source_center}",
                    amount=per_center_amount,
                    date=datetime.now().date(),
                    description=f"分摊方法: {method}"
                )
                self.record_cost(cost_item)
        
        self.allocations.append(allocation)
        logger.info(
            f"成本分摊: {amount} from {source_center} to {len(target_centers)} centers"
        )
        
        return allocation
    
    def get_cost_center_summary(
        self,
        cost_center_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, any]:
        """
        获取成本中心汇总
        
        Args:
            cost_center_id: 成本中心ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            成本汇总数据
        """
        center = self.get_cost_center(cost_center_id)
        if not center:
            return {}
        
        # 获取成本项目
        items = self.get_cost_items(
            cost_center_id=cost_center_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 按类型分组统计
        by_type = {}
        for item in items:
            cost_type = item.cost_type.value
            if cost_type not in by_type:
                by_type[cost_type] = Decimal("0")
            by_type[cost_type] += item.amount
        
        total = sum(item.amount for item in items)
        
        summary = {
            "cost_center": {
                "id": center.id,
                "name": center.name,
                "department": center.department
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_cost": float(total),
                "item_count": len(items),
                "by_type": {k: float(v) for k, v in by_type.items()}
            },
            "items": [
                {
                    "name": item.item_name,
                    "type": item.cost_type.value,
                    "amount": float(item.amount),
                    "date": item.date.isoformat()
                }
                for item in items
            ]
        }
        
        return summary
    
    def analyze_cost_trend(
        self,
        cost_center_id: int,
        months: int = 12
    ) -> List[Dict[str, any]]:
        """
        分析成本趋势
        
        Args:
            cost_center_id: 成本中心ID
            months: 分析月数
            
        Returns:
            月度成本趋势数据
        """
        from datetime import timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months * 30)
        
        items = self.get_cost_items(
            cost_center_id=cost_center_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 按月分组
        monthly_costs = {}
        for item in items:
            month_key = item.date.strftime("%Y-%m")
            if month_key not in monthly_costs:
                monthly_costs[month_key] = Decimal("0")
            monthly_costs[month_key] += item.amount
        
        # 转换为列表
        trend = [
            {
                "month": month,
                "total_cost": float(cost)
            }
            for month, cost in sorted(monthly_costs.items())
        ]
        
        return trend


# 全局实例
_cost_manager: Optional[CostAccountingManager] = None


def get_cost_manager() -> CostAccountingManager:
    """获取全局成本核算管理器实例"""
    global _cost_manager
    if _cost_manager is None:
        _cost_manager = CostAccountingManager()
    return _cost_manager


# 使用示例
def example_usage():
    """使用示例"""
    
    manager = get_cost_manager()
    
    # 1. 创建成本中心
    center = CostCenter(
        code="CC001",
        name="生产车间一",
        department="生产部",
        manager="张三"
    )
    center = manager.create_cost_center(center)
    
    # 2. 记录成本
    cost = CostItem(
        cost_center_id=center.id,
        cost_type=CostType.DIRECT_MATERIAL,
        item_name="原材料采购",
        amount=Decimal("50000"),
        quantity=Decimal("1000"),
        unit_cost=Decimal("50"),
        date=date.today()
    )
    manager.record_cost(cost)
    
    # 3. 成本分摊
    manager.allocate_cost(
        source_center=1,
        target_centers=[2, 3, 4],
        amount=Decimal("30000"),
        method="equal"
    )
    
    # 4. 成本汇总
    summary = manager.get_cost_center_summary(
        cost_center_id=center.id,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31)
    )
    print(f"成本汇总: {summary}")
    
    # 5. 成本趋势分析
    trend = manager.analyze_cost_trend(center.id, months=12)
    print(f"成本趋势: {len(trend)}个月")


if __name__ == "__main__":
    example_usage()


















