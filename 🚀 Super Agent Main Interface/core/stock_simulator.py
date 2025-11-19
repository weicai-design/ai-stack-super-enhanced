"""
股票模拟撮合与风控分析
提供：下单（限价/市价）、撤单、仓位与风险控制（止损/仓位比例）、滑点模拟、执行与风险报表
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random
from typing import Dict, Any, Optional, List


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
    """
    风控模块（增强版）
    支持更细粒度的风控规则
    """
    def __init__(
        self,
        max_position_ratio: float = 0.8,
        stop_loss_ratio: float = 0.1,
        slip_bps: float = 8.0,
        max_single_trade_ratio: float = 0.2,  # 单笔交易最大占比
        max_daily_loss_ratio: float = 0.05,  # 单日最大亏损比例
        max_concentration_ratio: float = 0.3,  # 单只股票最大集中度
    ):
        self.max_position_ratio = max_position_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.slip_bps = slip_bps  # 8 bps = 0.08%
        self.max_single_trade_ratio = max_single_trade_ratio
        self.max_daily_loss_ratio = max_daily_loss_ratio
        self.max_concentration_ratio = max_concentration_ratio
        self.daily_pnl: float = 0.0
        self.last_reset_date: str = datetime.now().date().isoformat()

    def apply_slippage(self, exec_price: float, side: str) -> float:
        """应用滑点"""
        slip = exec_price * (self.slip_bps / 10_000.0)
        return round(exec_price + slip if side == "buy" else exec_price - slip, 3)
    
    def check_single_trade_limit(self, trade_amount: float, equity: float) -> tuple[bool, Optional[str]]:
        """检查单笔交易限额"""
        if equity <= 0:
            return False, "权益为0"
        if trade_amount / equity > self.max_single_trade_ratio:
            return False, f"单笔交易金额超过限制（{self.max_single_trade_ratio*100:.1f}%）"
        return True, None
    
    def check_daily_loss_limit(self, pnl: float, equity: float) -> tuple[bool, Optional[str]]:
        """检查单日亏损限额"""
        # 重置日期
        current_date = datetime.now().date().isoformat()
        if current_date != self.last_reset_date:
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
        
        # 累计当日盈亏
        if pnl < 0:
            self.daily_pnl += pnl
        
        # 检查是否超过限额
        if equity > 0 and abs(self.daily_pnl) / equity > self.max_daily_loss_ratio:
            return False, f"单日亏损超过限制（{self.max_daily_loss_ratio*100:.1f}%）"
        return True, None
    
    def check_concentration_limit(self, symbol: str, position_value: float, total_equity: float) -> tuple[bool, Optional[str]]:
        """检查集中度限制"""
        if total_equity <= 0:
            return False, "权益为0"
        if position_value / total_equity > self.max_concentration_ratio:
            return False, f"单只股票集中度超过限制（{self.max_concentration_ratio*100:.1f}%）"
        return True, None


class StockSimulator:
    """
    轻量股票模拟盘：持仓/现金/撮合记录 + 风控 + 执行分析
    """

    def __init__(self, initial_cash: float = 1_000_000.0):
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}
        self.avg_cost: Dict[str, float] = {}
        self.orders: Dict[str, Order] = {}
        self.risk = RiskControl()
        self.trade_log: List[Dict[str, Any]] = []
        self.risk_alerts: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.realized_pnl: float = 0.0
        self.last_prices: Dict[str, float] = {}

    # ----- 下单 & 状态 -----
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
            "avg_cost": self.avg_cost,
            "realized_pnl": round(self.realized_pnl, 2)
        }

    def place_order(self, symbol: str, side: str, qty: int, order_type: str, price: Optional[float]) -> Dict[str, Any]:
        if qty <= 0:
            return {"success": False, "error": "数量必须>0"}
        order_id = self._gen_order_id()
        ord = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            order_type=order_type,
            price=price,
            status="accepted",
            created_at=datetime.now().isoformat()
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

    # ----- 撮合 & 风控 -----
    def mark_to_market_and_fill(self, symbol: str, quote_price: float) -> List[Dict[str, Any]]:
        """
        按最新行情撮合全部等待中的订单，应用滑点、仓位限制与止损提醒。
        """
        results: List[Dict[str, Any]] = []
        self.last_prices[symbol] = quote_price

        for order in list(self.orders.values()):
            if order.symbol != symbol or order.status != "accepted":
                continue

            exec_price = quote_price
            if order.order_type == "limit":
                if order.side == "buy" and (order.price is None or order.price < quote_price):
                    continue
                if order.side == "sell" and (order.price is None or order.price > quote_price):
                    continue

            exec_price = self.risk.apply_slippage(exec_price, order.side)
            state = self.get_state()
            equity = state["equity"]
            trade_amount = exec_price * order.qty
            
            # 增强风控检查
            # 1. 单笔交易限额
            passed, error_msg = self.risk.check_single_trade_limit(trade_amount, equity)
            if not passed:
                order.status = "rejected"
                self._log_alert(f"下单被拒：{error_msg}({symbol})", "warning", {"order_id": order.order_id})
                results.append({"success": False, "order": order.__dict__, "error": error_msg})
                continue
            
            # 2. 仓位上限检查
            pos_value_after = state["market_value"] + trade_amount if order.side == "buy" else state["market_value"]
            if order.side == "buy" and equity > 0 and pos_value_after / equity > self.risk.max_position_ratio:
                order.status = "rejected"
                self._log_alert(f"下单被拒：超过仓位上限({symbol})", "warning", {"order_id": order.order_id})
                results.append({"success": False, "order": order.__dict__, "error": "超过仓位上限"})
                continue
            
            # 3. 集中度检查（买入时）
            if order.side == "buy":
                new_position_value = (self.positions.get(symbol, 0) + order.qty) * exec_price
                passed, error_msg = self.risk.check_concentration_limit(symbol, new_position_value, equity)
                if not passed:
                    order.status = "rejected"
                    self._log_alert(f"下单被拒：{error_msg}({symbol})", "warning", {"order_id": order.order_id})
                    results.append({"success": False, "order": order.__dict__, "error": error_msg})
                    continue

            if order.side == "buy":
                cost = exec_price * order.qty
                if cost > self.cash:
                    order.status = "rejected"
                    self._log_alert(f"下单被拒：现金不足({symbol})", "error", {"order_id": order.order_id})
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
                    self._log_alert(f"下单被拒：可卖持仓不足({symbol})", "error", {"order_id": order.order_id})
                    results.append({"success": False, "order": order.__dict__, "error": "可卖持仓不足"})
                    continue
                self.positions[symbol] = pos - order.qty
                self.cash += exec_price * order.qty

            # 4. 单日亏损限额检查（卖出时）
            if order.side == "sell":
                avg_cost = self.avg_cost.get(symbol, exec_price)
                pnl = (exec_price - avg_cost) * order.qty
                passed, error_msg = self.risk.check_daily_loss_limit(pnl, equity)
                if not passed:
                    order.status = "rejected"
                    self._log_alert(f"下单被拒：{error_msg}({symbol})", "warning", {"order_id": order.order_id})
                    results.append({"success": False, "order": order.__dict__, "error": error_msg})
                    continue
            
            order.status = "filled"
            self._record_trade(order, exec_price, quote_price)
            results.append({
                "success": True,
                "order": order.__dict__,
                "exec_price": exec_price,
                "reference_price": quote_price
            })

        self._evaluate_stop_loss(symbol, quote_price)
        return results

    def _record_trade(self, order: Order, exec_price: float, reference_price: float):
        """记录交易，并同步到执行分析器"""
        pnl = 0.0
        if order.side == "sell":
            avg_cost = self.avg_cost.get(order.symbol, exec_price)
            pnl = (exec_price - avg_cost) * order.qty
            self.realized_pnl += pnl

        slippage_bps = self._calc_slippage(exec_price, reference_price, order.side)
        
        trade = {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side,
            "qty": order.qty,
            "exec_price": exec_price,
            "reference_price": reference_price,
            "slippage_bps": slippage_bps,
            "pnl": round(pnl, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.trade_log.append(trade)
        self.trade_log = self.trade_log[-500:]
        self._snapshot_equity()
        
        # 同步到执行分析器
        try:
            from core.stock_execution_analyzer import execution_analyzer
            execution_analyzer.record_execution(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                qty=order.qty,
                order_type=order.order_type,
                limit_price=order.price,
                exec_price=exec_price,
                reference_price=reference_price,
                slippage_bps=slippage_bps,
                status="filled",
                timestamp=trade["timestamp"]
            )
        except Exception:
            pass  # 忽略导入错误

    def _calc_slippage(self, exec_price: float, reference_price: float, side: str) -> float:
        if reference_price <= 0:
            return 0.0
        diff = exec_price - reference_price
        if side == "sell":
            diff = reference_price - exec_price
        return round((diff / reference_price) * 10_000, 3)

    def _snapshot_equity(self):
        state = self.get_state()
        self.equity_curve.append({
            "timestamp": datetime.now().isoformat(),
            "equity": state["equity"],
            "cash": state["cash"],
            "market_value": state["market_value"],
            "realized_pnl": round(self.realized_pnl, 2)
        })
        self.equity_curve = self.equity_curve[-500:]

    def _log_alert(self, message: str, level: str = "warning", meta: Optional[Dict[str, Any]] = None):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "meta": meta or {}
        }
        self.risk_alerts.append(alert)
        self.risk_alerts = self.risk_alerts[-100:]

    def _evaluate_stop_loss(self, symbol: str, quote_price: float):
        pos = self.positions.get(symbol, 0)
        if pos <= 0:
            return
        avg_cost = self.avg_cost.get(symbol, 0.0)
        if avg_cost <= 0:
            return
        threshold = avg_cost * (1 - self.risk.stop_loss_ratio)
        if quote_price < threshold:
            self._log_alert(
                f"{symbol} 跌破止损线，建议减仓 (最新 {quote_price} / 成本 {avg_cost})",
                "warning",
                {"symbol": symbol, "price": quote_price, "avg_cost": avg_cost}
            )

    # ----- 报表 -----
    def get_risk_report(self) -> Dict[str, Any]:
        state = self.get_state()
        exposures = []
        total_exposure = 0.0

        for symbol, qty in self.positions.items():
            exposure = qty * self.avg_cost.get(symbol, 0.0)
            exposures.append({
                "symbol": symbol,
                "qty": qty,
                "avg_cost": self.avg_cost.get(symbol, 0.0),
                "gross_exposure": round(exposure, 2),
                "last_price": self.last_prices.get(symbol)
            })
            total_exposure += exposure

        exposures.sort(key=lambda x: x["gross_exposure"], reverse=True)
        equity = max(state["equity"], 1e-9)
        exposure_ratio = total_exposure / equity

        return {
            "state": state,
            "realized_pnl": round(self.realized_pnl, 2),
            "exposure_ratio": round(exposure_ratio, 3),
            "max_position_ratio": self.risk.max_position_ratio,
            "stop_loss_ratio": self.risk.stop_loss_ratio,
            "slippage_bps": self.risk.slip_bps,
            "exposures": exposures,
            "alerts": self.risk_alerts[-10:]
        }

    def get_execution_report(self) -> Dict[str, Any]:
        total = len(self.trade_log)
        winning = len([t for t in self.trade_log if t["pnl"] > 0])
        avg_slippage = sum(t["slippage_bps"] for t in self.trade_log) / total if total else 0.0

        return {
            "total_trades": total,
            "winning_trades": winning,
            "win_rate": round(winning / total, 3) if total else 0.0,
            "realized_pnl": round(self.realized_pnl, 2),
            "avg_slippage_bps": round(avg_slippage, 3),
            "recent_trades": self.trade_log[-25:],
            "equity_curve": self.equity_curve[-100:]
        }

    def get_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.trade_log[-limit:])

    # ----- 风控参数 -----
    def update_risk_config(
        self,
        max_position_ratio: Optional[float] = None,
        stop_loss_ratio: Optional[float] = None,
        slip_bps: Optional[float] = None,
        max_single_trade_ratio: Optional[float] = None,
        max_daily_loss_ratio: Optional[float] = None,
        max_concentration_ratio: Optional[float] = None,
    ) -> Dict[str, Any]:
        """更新风控配置（增强版）"""
        if max_position_ratio is not None:
            self.risk.max_position_ratio = max(0.1, min(0.99, max_position_ratio))
        if stop_loss_ratio is not None:
            self.risk.stop_loss_ratio = max(0.01, min(0.5, stop_loss_ratio))
        if slip_bps is not None:
            self.risk.slip_bps = max(0.0, slip_bps)
        if max_single_trade_ratio is not None:
            self.risk.max_single_trade_ratio = max(0.01, min(0.5, max_single_trade_ratio))
        if max_daily_loss_ratio is not None:
            self.risk.max_daily_loss_ratio = max(0.01, min(0.2, max_daily_loss_ratio))
        if max_concentration_ratio is not None:
            self.risk.max_concentration_ratio = max(0.1, min(0.5, max_concentration_ratio))

        self._log_alert("风控参数已更新", "info", self.get_risk_config())
        return self.get_risk_config()

    def get_risk_config(self) -> Dict[str, Any]:
        """获取风控配置（增强版）"""
        return {
            "max_position_ratio": self.risk.max_position_ratio,
            "stop_loss_ratio": self.risk.stop_loss_ratio,
            "slip_bps": self.risk.slip_bps,
            "max_single_trade_ratio": self.risk.max_single_trade_ratio,
            "max_daily_loss_ratio": self.risk.max_daily_loss_ratio,
            "max_concentration_ratio": self.risk.max_concentration_ratio,
            "daily_pnl": round(self.risk.daily_pnl, 2),
        }
