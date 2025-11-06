"""
授权交易执行器
实现完整的策略授权、风控检查、自动交易功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio


class TradeAuthLevel(Enum):
    """交易授权级别"""
    NONE = "none"  # 无授权
    VIEW_ONLY = "view_only"  # 仅查看
    MANUAL_APPROVE = "manual_approve"  # 手动审批
    AUTO_LIMITED = "auto_limited"  # 限额自动
    AUTO_FULL = "auto_full"  # 全自动


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 极高风险


class AuthorizedTrader:
    """授权交易执行器"""
    
    def __init__(self, broker):
        """
        初始化授权交易器
        
        Args:
            broker: 券商接口实例
        """
        self.broker = broker
        self.authorization_config = {}
        self.trade_queue = []
        self.pending_approvals = []
        self.trade_log = []
        self.risk_alerts = []
    
    def configure_authorization(
        self,
        auth_level: str,
        max_single_trade: float = 50000,
        max_daily_trade: float = 200000,
        max_position_size: float = 100000,
        max_loss_per_trade: float = 5000,
        max_total_loss: float = 20000,
        allowed_stocks: List[str] = None,
        forbidden_keywords: List[str] = None,
        trading_hours_only: bool = True
    ) -> Dict[str, Any]:
        """
        配置交易授权
        
        Args:
            auth_level: 授权级别
            max_single_trade: 单笔最大交易额
            max_daily_trade: 日最大交易额
            max_position_size: 单只股票最大持仓
            max_loss_per_trade: 单笔最大亏损
            max_total_loss: 总最大亏损
            allowed_stocks: 股票白名单
            forbidden_keywords: 禁止关键词（如ST）
            trading_hours_only: 仅交易时段
        
        Returns:
            配置结果
        """
        self.authorization_config = {
            "auth_level": auth_level,
            "max_single_trade": max_single_trade,
            "max_daily_trade": max_daily_trade,
            "max_position_size": max_position_size,
            "max_loss_per_trade": max_loss_per_trade,
            "max_total_loss": max_total_loss,
            "allowed_stocks": allowed_stocks or [],
            "forbidden_keywords": forbidden_keywords or ["ST", "*ST", "退市"],
            "trading_hours_only": trading_hours_only,
            "daily_traded_amount": 0,
            "total_loss": 0,
            "last_reset_date": datetime.now().strftime('%Y-%m-%d'),
            "configured_at": datetime.now().isoformat(),
            "enabled": True
        }
        
        return {
            "success": True,
            "message": "交易授权已配置",
            "config": self.authorization_config
        }
    
    async def execute_trade_with_authorization(
        self,
        stock_code: str,
        direction: str,
        price: float,
        quantity: int,
        strategy_id: str = "",
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        执行带授权的交易
        
        Args:
            stock_code: 股票代码
            direction: 方向 (buy/sell)
            price: 价格
            quantity: 数量
            strategy_id: 策略ID
            reason: 交易理由
        
        Returns:
            执行结果
        """
        # 1. 检查授权配置
        if not self.authorization_config or not self.authorization_config.get("enabled"):
            return {"success": False, "error": "交易授权未配置或已禁用"}
        
        auth_level = self.authorization_config["auth_level"]
        
        if auth_level == TradeAuthLevel.NONE.value:
            return {"success": False, "error": "无交易授权"}
        
        if auth_level == TradeAuthLevel.VIEW_ONLY.value:
            return {"success": False, "error": "仅有查看权限，无交易权限"}
        
        # 2. 执行风控检查
        risk_check = self._perform_risk_check(stock_code, direction, price, quantity)
        
        if not risk_check["passed"]:
            return {
                "success": False,
                "error": f"风控检查未通过: {risk_check['reason']}",
                "risk_check": risk_check
            }
        
        # 3. 根据授权级别执行
        if auth_level == TradeAuthLevel.MANUAL_APPROVE.value:
            # 需要手动审批
            return self._submit_for_approval(
                stock_code, direction, price, quantity, strategy_id, reason, risk_check
            )
        
        elif auth_level in [TradeAuthLevel.AUTO_LIMITED.value, TradeAuthLevel.AUTO_FULL.value]:
            # 自动交易
            return await self._execute_auto_trade(
                stock_code, direction, price, quantity, strategy_id, reason, risk_check
            )
        
        return {"success": False, "error": "未知授权级别"}
    
    def _perform_risk_check(
        self,
        stock_code: str,
        direction: str,
        price: float,
        quantity: int
    ) -> Dict[str, Any]:
        """
        执行风控检查
        
        Args:
            stock_code: 股票代码
            direction: 方向
            price: 价格
            quantity: 数量
        
        Returns:
            风控检查结果
        """
        checks = []
        amount = price * quantity
        
        # 检查1：基本验证
        if price <= 0 or quantity <= 0:
            return {
                "passed": False,
                "reason": "价格和数量必须大于0",
                "risk_level": RiskLevel.CRITICAL.value
            }
        
        if quantity % 100 != 0:
            return {
                "passed": False,
                "reason": "数量必须是100的整数倍",
                "risk_level": RiskLevel.HIGH.value
            }
        
        checks.append({"check": "基本验证", "result": "通过"})
        
        # 检查2：禁止关键词
        forbidden = self.authorization_config.get("forbidden_keywords", [])
        for keyword in forbidden:
            if keyword in stock_code:
                return {
                    "passed": False,
                    "reason": f"股票包含禁止关键词: {keyword}",
                    "risk_level": RiskLevel.HIGH.value
                }
        checks.append({"check": "关键词过滤", "result": "通过"})
        
        # 检查3：白名单
        allowed_stocks = self.authorization_config.get("allowed_stocks", [])
        if allowed_stocks and stock_code not in allowed_stocks:
            return {
                "passed": False,
                "reason": "股票不在授权白名单中",
                "risk_level": RiskLevel.HIGH.value
            }
        checks.append({"check": "白名单验证", "result": "通过"})
        
        # 检查4：单笔限额
        max_single = self.authorization_config["max_single_trade"]
        if amount > max_single:
            return {
                "passed": False,
                "reason": f"单笔金额{amount:.2f}超过限额{max_single:.2f}",
                "risk_level": RiskLevel.HIGH.value
            }
        checks.append({"check": "单笔限额", "result": "通过"})
        
        # 检查5：日累计限额
        today = datetime.now().strftime('%Y-%m-%d')
        if self.authorization_config["last_reset_date"] != today:
            self.authorization_config["daily_traded_amount"] = 0
            self.authorization_config["last_reset_date"] = today
        
        daily_traded = self.authorization_config["daily_traded_amount"]
        max_daily = self.authorization_config["max_daily_trade"]
        
        if daily_traded + amount > max_daily:
            return {
                "passed": False,
                "reason": f"日累计{daily_traded + amount:.2f}将超过限额{max_daily:.2f}",
                "risk_level": RiskLevel.HIGH.value
            }
        checks.append({"check": "日限额", "result": "通过"})
        
        # 检查6：交易时段
        if self.authorization_config.get("trading_hours_only"):
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            # A股交易时间：9:30-11:30, 13:00-15:00
            is_morning = (hour == 9 and minute >= 30) or (hour == 10) or (hour == 11 and minute <= 30)
            is_afternoon = (hour == 13) or (hour == 14) or (hour == 15 and minute == 0)
            
            if not (is_morning or is_afternoon):
                return {
                    "passed": False,
                    "reason": "非交易时段",
                    "risk_level": RiskLevel.MEDIUM.value
                }
        checks.append({"check": "交易时段", "result": "通过"})
        
        # 所有检查通过
        return {
            "passed": True,
            "reason": "所有风控检查通过",
            "risk_level": RiskLevel.LOW.value,
            "checks": checks
        }
    
    def _submit_for_approval(
        self,
        stock_code: str,
        direction: str,
        price: float,
        quantity: int,
        strategy_id: str,
        reason: str,
        risk_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提交审批
        
        Args:
            stock_code: 股票代码
            direction: 方向
            price: 价格
            quantity: 数量
            strategy_id: 策略ID
            reason: 理由
            risk_check: 风控检查结果
        
        Returns:
            提交结果
        """
        approval_id = f"APP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        approval_request = {
            "approval_id": approval_id,
            "stock_code": stock_code,
            "direction": direction,
            "price": price,
            "quantity": quantity,
            "amount": price * quantity,
            "strategy_id": strategy_id,
            "reason": reason,
            "risk_check": risk_check,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
            "approved_by": None,
            "approved_at": None
        }
        
        self.pending_approvals.append(approval_request)
        
        return {
            "success": True,
            "approval_id": approval_id,
            "message": "交易已提交审批，等待人工确认",
            "approval_request": approval_request
        }
    
    async def approve_trade(
        self,
        approval_id: str,
        approver: str,
        approved: bool,
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        审批交易
        
        Args:
            approval_id: 审批ID
            approver: 审批人
            approved: 是否批准
            comments: 审批意见
        
        Returns:
            审批结果
        """
        approval = next((a for a in self.pending_approvals if a["approval_id"] == approval_id), None)
        
        if not approval:
            return {"success": False, "error": "审批请求不存在"}
        
        if approval["status"] != "pending":
            return {"success": False, "error": f"审批已处理: {approval['status']}"}
        
        if approved:
            approval["status"] = "approved"
            approval["approved_by"] = approver
            approval["approved_at"] = datetime.now().isoformat()
            approval["comments"] = comments
            
            # 执行交易
            if approval["direction"] == "buy":
                result = await self.broker.buy_stock(
                    approval["stock_code"],
                    approval["price"],
                    approval["quantity"]
                )
            else:
                result = await self.broker.sell_stock(
                    approval["stock_code"],
                    approval["price"],
                    approval["quantity"]
                )
            
            # 记录交易日志
            self._log_trade(approval, result)
            
            return {
                "success": True,
                "message": "交易已批准并执行",
                "approval": approval,
                "trade_result": result
            }
        else:
            approval["status"] = "rejected"
            approval["rejected_by"] = approver
            approval["rejected_at"] = datetime.now().isoformat()
            approval["rejection_reason"] = comments
            
            return {
                "success": True,
                "message": "交易已拒绝",
                "approval": approval
            }
    
    async def _execute_auto_trade(
        self,
        stock_code: str,
        direction: str,
        price: float,
        quantity: int,
        strategy_id: str,
        reason: str,
        risk_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行自动交易
        
        Args:
            stock_code: 股票代码
            direction: 方向
            price: 价格
            quantity: 数量
            strategy_id: 策略ID
            reason: 理由
            risk_check: 风控检查结果
        
        Returns:
            执行结果
        """
        # 执行交易
        if direction == "buy":
            result = await self.broker.authorized_buy(
                stock_code, price, quantity, strategy_id
            )
        else:
            result = await self.broker.authorized_sell(
                stock_code, price, quantity, strategy_id
            )
        
        # 记录到交易日志
        trade_record = {
            "stock_code": stock_code,
            "direction": direction,
            "price": price,
            "quantity": quantity,
            "amount": price * quantity,
            "strategy_id": strategy_id,
            "reason": reason,
            "risk_check": risk_check,
            "execution_mode": "auto",
            "executed_at": datetime.now().isoformat(),
            "result": result
        }
        
        self._log_trade(trade_record, result)
        
        # 更新日交易额
        if result.get("success"):
            self.authorization_config["daily_traded_amount"] += price * quantity
        
        return result
    
    def _log_trade(
        self,
        trade_info: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        记录交易日志
        
        Args:
            trade_info: 交易信息
            result: 执行结果
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "trade_info": trade_info,
            "result": result,
            "success": result.get("success", False)
        }
        
        self.trade_log.append(log_entry)
    
    def get_authorization_status(self) -> Dict[str, Any]:
        """
        获取授权状态
        
        Returns:
            授权状态
        """
        if not self.authorization_config:
            return {
                "authorized": False,
                "message": "未配置交易授权"
            }
        
        # 重置日交易额（如果是新的一天）
        today = datetime.now().strftime('%Y-%m-%d')
        if self.authorization_config["last_reset_date"] != today:
            self.authorization_config["daily_traded_amount"] = 0
            self.authorization_config["total_loss"] = 0
            self.authorization_config["last_reset_date"] = today
        
        return {
            "authorized": self.authorization_config.get("enabled", False),
            "auth_level": self.authorization_config.get("auth_level"),
            "limits": {
                "max_single_trade": self.authorization_config["max_single_trade"],
                "max_daily_trade": self.authorization_config["max_daily_trade"],
                "max_position_size": self.authorization_config["max_position_size"],
                "max_loss_per_trade": self.authorization_config["max_loss_per_trade"],
                "max_total_loss": self.authorization_config["max_total_loss"]
            },
            "usage_today": {
                "traded_amount": self.authorization_config["daily_traded_amount"],
                "remaining_amount": self.authorization_config["max_daily_trade"] - self.authorization_config["daily_traded_amount"],
                "total_loss": self.authorization_config["total_loss"],
                "remaining_loss_tolerance": self.authorization_config["max_total_loss"] - self.authorization_config["total_loss"]
            },
            "restrictions": {
                "allowed_stocks_count": len(self.authorization_config.get("allowed_stocks", [])),
                "forbidden_keywords": self.authorization_config.get("forbidden_keywords", []),
                "trading_hours_only": self.authorization_config.get("trading_hours_only", True)
            }
        }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        获取待审批列表
        
        Returns:
            待审批交易列表
        """
        return [a for a in self.pending_approvals if a["status"] == "pending"]
    
    def get_trade_statistics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取交易统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            交易统计
        """
        logs = self.trade_log
        
        # 筛选日期范围
        if start_date:
            logs = [l for l in logs if l["timestamp"][:10] >= start_date]
        if end_date:
            logs = [l for l in logs if l["timestamp"][:10] <= end_date]
        
        total_trades = len(logs)
        successful_trades = sum(1 for l in logs if l["success"])
        
        # 买卖统计
        buy_trades = sum(1 for l in logs if l["trade_info"].get("direction") == "buy")
        sell_trades = sum(1 for l in logs if l["trade_info"].get("direction") == "sell")
        
        # 金额统计
        total_amount = sum(
            l["trade_info"].get("amount", 0)
            for l in logs if l["success"]
        )
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_trades": total_trades,
                "successful_trades": successful_trades,
                "failed_trades": total_trades - successful_trades,
                "success_rate": round((successful_trades / total_trades * 100), 2) if total_trades > 0 else 0
            },
            "by_direction": {
                "buy_trades": buy_trades,
                "sell_trades": sell_trades
            },
            "amount": {
                "total_traded": round(total_amount, 2)
            }
        }


# 创建默认实例（需要传入broker实例）
# authorized_trader = AuthorizedTrader(ths_broker)

