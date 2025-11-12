"""
V5.7 业务逻辑增强
实现真实的业务规则和算法
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

# ==================== 财务管理：复式记账系统 ====================

class AccountType(Enum):
    """账户类型"""
    ASSET = "资产"           # 借增贷减
    LIABILITY = "负债"       # 贷增借减
    EQUITY = "权益"          # 贷增借减
    REVENUE = "收入"         # 贷增借减
    EXPENSE = "费用"         # 借增贷减

class JournalEntry:
    """记账分录"""
    def __init__(self, date: datetime, description: str):
        self.date = date
        self.description = description
        self.debits: List[Dict] = []   # 借方
        self.credits: List[Dict] = []  # 贷方
    
    def add_debit(self, account: str, amount: float):
        """添加借方"""
        self.debits.append({"account": account, "amount": amount})
    
    def add_credit(self, account: str, amount: float):
        """添加贷方"""
        self.credits.append({"account": account, "amount": amount})
    
    def is_balanced(self) -> bool:
        """检查借贷平衡"""
        debit_total = sum(d["amount"] for d in self.debits)
        credit_total = sum(c["amount"] for c in self.credits)
        return abs(debit_total - credit_total) < 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "date": self.date.isoformat(),
            "description": self.description,
            "debits": self.debits,
            "credits": self.credits,
            "balanced": self.is_balanced()
        }

class DoubleEntryBookkeeping:
    """复式记账系统"""
    
    @staticmethod
    def record_sales(amount: float, cost: float) -> JournalEntry:
        """记录销售（收入确认）"""
        entry = JournalEntry(datetime.now(), f"销售收入 ¥{amount}")
        
        # 借：银行存款  贷：主营业务收入
        entry.add_debit("银行存款", amount)
        entry.add_credit("主营业务收入", amount)
        
        # 借：主营业务成本  贷：库存商品
        entry.add_debit("主营业务成本", cost)
        entry.add_credit("库存商品", cost)
        
        return entry
    
    @staticmethod
    def record_expense(amount: float, category: str) -> JournalEntry:
        """记录费用"""
        entry = JournalEntry(datetime.now(), f"{category} ¥{amount}")
        
        # 借：费用科目  贷：银行存款
        entry.add_debit(category, amount)
        entry.add_credit("银行存款", amount)
        
        return entry
    
    @staticmethod
    def record_purchase(amount: float) -> JournalEntry:
        """记录采购"""
        entry = JournalEntry(datetime.now(), f"采购商品 ¥{amount}")
        
        # 借：库存商品  贷：应付账款
        entry.add_debit("库存商品", amount)
        entry.add_credit("应付账款", amount)
        
        return entry

# ==================== ERP：订单状态机 ====================

class OrderState(Enum):
    """订单状态"""
    DRAFT = "草稿"
    CONFIRMED = "已确认"
    IN_PRODUCTION = "生产中"
    QUALITY_CHECK = "质检中"
    READY_TO_SHIP = "待发货"
    SHIPPED = "已发货"
    DELIVERED = "已送达"
    COMPLETED = "已完成"
    CANCELLED = "已取消"

class OrderStateMachine:
    """订单状态机"""
    
    # 状态转换规则
    TRANSITIONS = {
        OrderState.DRAFT: [OrderState.CONFIRMED, OrderState.CANCELLED],
        OrderState.CONFIRMED: [OrderState.IN_PRODUCTION, OrderState.CANCELLED],
        OrderState.IN_PRODUCTION: [OrderState.QUALITY_CHECK, OrderState.CANCELLED],
        OrderState.QUALITY_CHECK: [OrderState.READY_TO_SHIP, OrderState.IN_PRODUCTION],
        OrderState.READY_TO_SHIP: [OrderState.SHIPPED],
        OrderState.SHIPPED: [OrderState.DELIVERED],
        OrderState.DELIVERED: [OrderState.COMPLETED],
        OrderState.COMPLETED: [],
        OrderState.CANCELLED: []
    }
    
    @classmethod
    def can_transition(cls, from_state: OrderState, to_state: OrderState) -> bool:
        """检查是否可以转换状态"""
        return to_state in cls.TRANSITIONS.get(from_state, [])
    
    @classmethod
    def get_next_states(cls, current_state: OrderState) -> List[OrderState]:
        """获取可转换的下一个状态"""
        return cls.TRANSITIONS.get(current_state, [])
    
    @classmethod
    def transition(cls, order: Dict, to_state: OrderState) -> Dict[str, Any]:
        """执行状态转换"""
        current_state = OrderState(order.get("status", "草稿"))
        
        if not cls.can_transition(current_state, to_state):
            return {
                "success": False,
                "error": f"不能从 {current_state.value} 转换到 {to_state.value}",
                "current_state": current_state.value,
                "allowed_states": [s.value for s in cls.get_next_states(current_state)]
            }
        
        # 执行转换
        order["status"] = to_state.value
        order["status_updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "previous_state": current_state.value,
            "new_state": to_state.value,
            "order": order
        }

# ==================== 股票：移动平均交叉策略 ====================

class TradingStrategy:
    """交易策略"""
    
    @staticmethod
    def moving_average(prices: List[float], period: int) -> List[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return []
        
        ma = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i-period+1:i+1]) / period
            ma.append(round(avg, 2))
        
        return ma
    
    @classmethod
    def ma_crossover_strategy(cls, prices: List[float], short: int = 5, long: int = 20) -> Dict[str, Any]:
        """移动平均交叉策略"""
        if len(prices) < long:
            return {"signal": "HOLD", "reason": "数据不足"}
        
        ma_short = cls.moving_average(prices, short)
        ma_long = cls.moving_average(prices, long)
        
        if not ma_short or not ma_long:
            return {"signal": "HOLD", "reason": "无法计算均线"}
        
        # 获取最新的均线值
        current_short = ma_short[-1]
        current_long = ma_long[-1]
        prev_short = ma_short[-2] if len(ma_short) > 1 else current_short
        prev_long = ma_long[-2] if len(ma_long) > 1 else current_long
        
        # 金叉（买入信号）：短期均线从下方穿越长期均线
        if prev_short <= prev_long and current_short > current_long:
            return {
                "signal": "BUY",
                "reason": "金叉",
                "ma_short": current_short,
                "ma_long": current_long,
                "strength": (current_short - current_long) / current_long * 100
            }
        
        # 死叉（卖出信号）：短期均线从上方穿越长期均线
        if prev_short >= prev_long and current_short < current_long:
            return {
                "signal": "SELL",
                "reason": "死叉",
                "ma_short": current_short,
                "ma_long": current_long,
                "strength": (current_long - current_short) / current_long * 100
            }
        
        # 持有
        return {
            "signal": "HOLD",
            "reason": "无交叉信号",
            "ma_short": current_short,
            "ma_long": current_long
        }
    
    @staticmethod
    def calculate_risk(price: float, stop_loss: float, position_size: int) -> Dict[str, Any]:
        """计算风险"""
        max_loss = abs(price - stop_loss) * position_size
        risk_percent = abs(price - stop_loss) / price * 100
        
        return {
            "max_loss": round(max_loss, 2),
            "risk_percent": round(risk_percent, 2),
            "stop_loss": stop_loss,
            "risk_level": "高" if risk_percent > 5 else "中" if risk_percent > 2 else "低"
        }

# ==================== 财务：成本分摊算法 ====================

class CostAllocation:
    """成本分摊"""
    
    @staticmethod
    def allocate_by_ratio(total_cost: float, ratios: Dict[str, float]) -> Dict[str, float]:
        """按比例分摊成本"""
        total_ratio = sum(ratios.values())
        if total_ratio == 0:
            return {k: 0 for k in ratios}
        
        result = {}
        for item, ratio in ratios.items():
            allocated = total_cost * (ratio / total_ratio)
            result[item] = round(allocated, 2)
        
        return result
    
    @staticmethod
    def allocate_by_activity(total_cost: float, activities: Dict[str, int]) -> Dict[str, float]:
        """按作业量分摊成本（ABC成本法）"""
        total_activity = sum(activities.values())
        if total_activity == 0:
            return {k: 0 for k in activities}
        
        cost_per_unit = total_cost / total_activity
        
        result = {}
        for item, activity in activities.items():
            allocated = cost_per_unit * activity
            result[item] = round(allocated, 2)
        
        return result

# ==================== 工具函数 ====================

def calculate_profit_margin(revenue: float, cost: float) -> Dict[str, Any]:
    """计算利润率"""
    if revenue == 0:
        return {"profit_margin": 0, "gross_profit": 0}
    
    gross_profit = revenue - cost
    profit_margin = (gross_profit / revenue) * 100
    
    return {
        "revenue": revenue,
        "cost": cost,
        "gross_profit": round(gross_profit, 2),
        "profit_margin": round(profit_margin, 2)
    }

def calculate_roi(investment: float, return_amount: float) -> Dict[str, Any]:
    """计算投资回报率"""
    if investment == 0:
        return {"roi": 0, "net_return": 0}
    
    net_return = return_amount - investment
    roi = (net_return / investment) * 100
    
    return {
        "investment": investment,
        "return": return_amount,
        "net_return": round(net_return, 2),
        "roi": round(roi, 2)
    }


print("✅ 业务逻辑模块已加载")
print("   - 复式记账系统")
print("   - 订单状态机")
print("   - 交易策略算法")
print("   - 成本分摊算法")


