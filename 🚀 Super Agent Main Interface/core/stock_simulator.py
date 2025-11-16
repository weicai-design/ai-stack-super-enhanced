"""
股票模拟撮合与基础风控
提供：下单（限价/市价）、撤单、仓位与风险控制（止损/仓位比例）、滑点与延迟模拟
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import random


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # buy/sell
    qty: int
    order_type: str  # market/limit
    price: Optional[float]
    status: str
    created_at: str


class RiskControl:
    def __init__(self, max_position_ratio: float = 0.8, stop_loss_ratio: float = 0.1, slip_bps: float = 8.0):
        self.max_position_ratio = max_position_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.slip_bps = slip_bps  # 8 bps = 0.08%

    def apply_slippage(self, exec_price: float, side: str) -> float:
        slip = exec_price * (self.slip_bps / 10_000.0)
        return round(exec_price + slip if side == "buy" else exec_price - slip, 3)


class StockSimulator:
    def __init__(self, initial_cash: float = 1_000_000.0):
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}
        self.avg_cost: Dict[str, float] = {}
        self.orders: Dict[str, Order] = {}
        self.risk = RiskControl()

    def _gen_order_id(self) -> str:
        return f"SIM-{int(datetime.now().timestamp()*1000)}-{random.randint(100,999)}"

    def get_state(self) -> Dict[str, Any]:
        market_value = sum(self.positions.get(sym, 0) * self.avg_cost.get(sym, 0.0) for sym in self.positions)
        equity = self.cash + market_value
        return {
            "cash": round(self.cash, 2),
            "market_value": round(market_value, 2),
            "equity": round(equity, 2),
            "positions": self.positions,
            "avg_cost": self.avg_cost
        }

    def place_order(self, symbol: str, side: str, qty: int, order_type: str, price: Optional[float]) -> Dict[str, Any]:
        if qty <= 0:
            return {"success": False, "error": "数量必须>0"}
        order_id = self._gen_order_id()
        ord = Order(
            order_id=order_id, symbol=symbol, side=side, qty=qty,
            order_type=order_type, price=price, status="accepted", created_at=datetime.now().isoformat()
        )
        self.orders[order_id] = ord
        return {"success": True, "order": ord.__dict__}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        ord = self.orders.get(order_id)
        if not ord:
            return {"success": False, "error": "订单不存在"}
        if ord.status not in ["accepted"]:
            return {"success": False, "error": "订单不可撤销"}
        ord.status = "canceled"
        return {"success": True, "order": ord.__dict__}

    def mark_to_market_and_fill(self, symbol: str, quote_price: float) -> List[Dict[str, Any]]:
        """撮合：按市价或满足限价条件成交，应用滑点与简易延迟"""
        results: List[Dict[str, Any]] = []
        for order in list(self.orders.values()):
            if order.symbol != symbol or order.status != "accepted":
                continue
            exec_price = quote_price
            if order.order_type == "limit":
                if order.side == "buy" and (order.price is None or order.price < quote_price):
                    continue
                if order.side == "sell" and (order.price is None or order.price > quote_price):
                    continue
            # 应用滑点
            exec_price = self.risk.apply_slippage(exec_price, order.side)
            # 风控：仓位比例（简化，按市值/权益）
            state = self.get_state()
            equity = state["equity"]
            pos_value_after = state["market_value"] + exec_price * order.qty if order.side == "buy" else state["market_value"]
            if pos_value_after / max(equity, 1e-9) > self.risk.max_position_ratio and order.side == "buy":
                order.status = "rejected"
                results.append({"success": False, "order": order.__dict__, "error": "超过仓位上限"})
                continue
            # 执行
            if order.side == "buy":
                cost = exec_price * order.qty
                if cost > self.cash:
                    order.status = "rejected"
                    results.append({"success": False, "order": order.__dict__, "error": "现金不足"})
                    continue
                self.cash -= cost
                pos = self.positions.get(symbol, 0)
                total_cost = self.avg_cost.get(symbol, 0.0) * pos + cost
                new_pos = pos + order.qty
                self.positions[symbol] = new_pos
                self.avg_cost[symbol] = round(total_cost / new_pos, 4)
            else:
                pos = self.positions.get(symbol, 0)
                if order.qty > pos:
                    order.status = "rejected"
                    results.append({"success": False, "order": order.__dict__, "error": "可卖持仓不足"})
                    continue
                self.positions[symbol] = pos - order.qty
                self.cash += exec_price * order.qty
            order.status = "filled"
            results.append({"success": True, "order": order.__dict__, "exec_price": exec_price})
        return results


