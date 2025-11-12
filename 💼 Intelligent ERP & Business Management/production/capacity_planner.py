"""
生产产能规划模块
智能产能分析、负荷平衡、排程优化
"""

from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ProductionLine(BaseModel):
    """生产线"""
    id: int
    name: str
    capacity_per_hour: Decimal  # 每小时产能
    efficiency: Decimal = Decimal("0.85")  # 效率（默认85%）
    available_hours: Decimal = Decimal("8")  # 可用工时/天


class ProductionPlan(BaseModel):
    """生产计划"""
    id: Optional[int] = None
    product: str
    quantity: Decimal
    start_date: date
    end_date: date
    line_id: int
    status: str = "planned"


class CapacityAnalysis(BaseModel):
    """产能分析结果"""
    line_id: int
    line_name: str
    daily_capacity: Decimal  # 日产能
    utilized_capacity: Decimal  # 已使用产能
    available_capacity: Decimal  # 可用产能
    utilization_rate: Decimal  # 利用率（%）
    is_overloaded: bool  # 是否超负荷


class CapacityPlanner:
    """
    产能规划器
    
    功能：
    - 产能分析
    - 负荷平衡
    - 瓶颈识别
    - 排程优化
    """
    
    def __init__(self):
        """初始化产能规划器"""
        self.production_lines: List[ProductionLine] = []
        self.production_plans: List[ProductionPlan] = []
    
    def add_production_line(self, line: ProductionLine) -> ProductionLine:
        """添加生产线"""
        self.production_lines.append(line)
        logger.info(f"添加生产线: {line.name} (产能: {line.capacity_per_hour}/h)")
        return line
    
    def calculate_line_capacity(
        self,
        line_id: int,
        target_date: date
    ) -> CapacityAnalysis:
        """
        计算生产线产能
        
        Args:
            line_id: 生产线ID
            target_date: 目标日期
            
        Returns:
            产能分析结果
        """
        line = next((l for l in self.production_lines if l.id == line_id), None)
        if not line:
            raise ValueError(f"生产线不存在: {line_id}")
        
        # 计算理论日产能
        daily_capacity = (
            line.capacity_per_hour *
            line.available_hours *
            line.efficiency
        )
        
        # 计算已使用产能
        plans = [
            p for p in self.production_plans
            if p.line_id == line_id
            and p.start_date <= target_date <= p.end_date
        ]
        
        utilized = sum(p.quantity for p in plans)
        available = daily_capacity - utilized
        utilization_rate = (utilized / daily_capacity * 100) if daily_capacity else Decimal("0")
        
        analysis = CapacityAnalysis(
            line_id=line_id,
            line_name=line.name,
            daily_capacity=daily_capacity,
            utilized_capacity=utilized,
            available_capacity=available,
            utilization_rate=utilization_rate,
            is_overloaded=utilized > daily_capacity
        )
        
        return analysis
    
    def find_best_line(
        self,
        quantity: Decimal,
        target_date: date
    ) -> Optional[int]:
        """
        找到最佳生产线
        
        Args:
            quantity: 生产数量
            target_date: 目标日期
            
        Returns:
            生产线ID
        """
        best_line = None
        min_utilization = Decimal("100")
        
        for line in self.production_lines:
            analysis = self.calculate_line_capacity(line.id, target_date)
            
            # 检查是否有足够产能
            if analysis.available_capacity >= quantity:
                # 选择利用率最低的生产线（负荷均衡）
                if analysis.utilization_rate < min_utilization:
                    min_utilization = analysis.utilization_rate
                    best_line = line.id
        
        return best_line
    
    def optimize_schedule(
        self,
        plans: List[ProductionPlan]
    ) -> List[ProductionPlan]:
        """
        优化生产排程
        
        Args:
            plans: 生产计划列表
            
        Returns:
            优化后的计划列表
        """
        logger.info(f"优化排程: {len(plans)}个计划")
        
        optimized_plans = []
        
        # 按优先级和交期排序
        sorted_plans = sorted(plans, key=lambda p: (p.end_date, p.quantity))
        
        for plan in sorted_plans:
            # 为每个计划找最佳生产线
            best_line = self.find_best_line(plan.quantity, plan.start_date)
            
            if best_line:
                plan.line_id = best_line
                optimized_plans.append(plan)
                logger.debug(f"分配计划 {plan.id} 到生产线 {best_line}")
            else:
                logger.warning(f"计划 {plan.id} 无可用产能")
        
        return optimized_plans


# 全局实例
_capacity_planner: Optional[CapacityPlanner] = None


def get_capacity_planner() -> CapacityPlanner:
    """获取全局产能规划器实例"""
    global _capacity_planner
    if _capacity_planner is None:
        _capacity_planner = CapacityPlanner()
    return _capacity_planner


# 使用示例
def example_usage():
    """使用示例"""
    
    planner = get_capacity_planner()
    
    # 1. 添加生产线
    line1 = ProductionLine(
        id=1,
        name="生产线A",
        capacity_per_hour=Decimal("50"),
        efficiency=Decimal("0.85"),
        available_hours=Decimal("8")
    )
    planner.add_production_line(line1)
    
    # 2. 计算产能
    analysis = planner.calculate_line_capacity(1, date.today())
    print(f"日产能: {analysis.daily_capacity}")
    print(f"可用产能: {analysis.available_capacity}")
    print(f"利用率: {analysis.utilization_rate}%")
    
    # 3. 找最佳生产线
    best = planner.find_best_line(Decimal("100"), date.today())
    print(f"最佳生产线: {best}")


if __name__ == "__main__":
    example_usage()


















