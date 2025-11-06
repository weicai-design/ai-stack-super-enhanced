"""
交易执行引擎
- 策略执行
- 风险控制
- 交易记录
"""
from typing import Dict, Any, List
from datetime import datetime
import sys
sys.path.append('..')
from brokers.thsbroker import ths_broker


class TradeExecutor:
    """交易执行器"""
    
    def __init__(self):
        self.broker = ths_broker
        self.trade_history = []
        
        # 风控参数
        self.max_single_trade_amount = 100000  # 单笔最大交易金额
        self.max_position_ratio = 0.3          # 单只股票最大仓位比例
        self.stop_loss_ratio = 0.05            # 止损比例
    
    async def execute_strategy_signal(
        self,
        signal: Dict[str, Any],
        user_approval: bool = False
    ) -> Dict[str, Any]:
        """
        执行策略信号
        
        Args:
            signal: {
                "action": "buy/sell",
                "stock_code": "股票代码",
                "stock_name": "股票名称",
                "price": 价格,
                "quantity": 数量,
                "reason": "交易原因",
                "strategy": "策略名称"
            }
            user_approval: 是否经用户批准
        
        Returns:
            执行结果
        """
        if not user_approval:
            return {
                "success": False,
                "error": "需要用户批准才能执行交易",
                "signal": signal
            }
        
        if not self.broker.check_authorization():
            return {
                "success": False,
                "error": "券商未授权"
            }
        
        try:
            # 风控检查
            risk_check = await self._risk_control_check(signal)
            if not risk_check['passed']:
                return {
                    "success": False,
                    "error": f"风控检查未通过: {risk_check['reason']}",
                    "risk_check": risk_check
                }
            
            # 执行交易
            if signal['action'] == 'buy':
                result = await self.broker.buy_stock(
                    signal['stock_code'],
                    signal['price'],
                    signal['quantity']
                )
            elif signal['action'] == 'sell':
                result = await self.broker.sell_stock(
                    signal['stock_code'],
                    signal['price'],
                    signal['quantity']
                )
            else:
                return {
                    "success": False,
                    "error": f"不支持的交易类型: {signal['action']}"
                }
            
            # 记录交易
            if result['success']:
                trade_record = {
                    "signal": signal,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat(),
                    "approved_by_user": user_approval
                }
                self.trade_history.append(trade_record)
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _risk_control_check(self, signal: Dict[str, Any]) -> Dict[str, bool]:
        """风险控制检查"""
        try:
            # 检查1：单笔交易金额限制
            trade_amount = signal['price'] * signal['quantity']
            if trade_amount > self.max_single_trade_amount:
                return {
                    "passed": False,
                    "reason": f"单笔交易金额 {trade_amount} 超过限额 {self.max_single_trade_amount}"
                }
            
            # 检查2：仓位比例限制（买入时）
            if signal['action'] == 'buy':
                account = await self.broker.get_account_info()
                if account['success']:
                    total_assets = account['account']['total_assets']
                    position_ratio = trade_amount / total_assets
                    
                    if position_ratio > self.max_position_ratio:
                        return {
                            "passed": False,
                            "reason": f"仓位比例 {position_ratio:.1%} 超过限额 {self.max_position_ratio:.1%}"
                        }
            
            # 检查3：止损检查（卖出时）
            if signal['action'] == 'sell':
                positions = await self.broker.get_positions()
                if positions['success']:
                    position = next((p for p in positions['positions'] 
                                   if p['stock_code'] == signal['stock_code']), None)
                    
                    if position:
                        loss_ratio = (signal['price'] - position['cost_price']) / position['cost_price']
                        if loss_ratio < -self.stop_loss_ratio:
                            # 触发止损，允许卖出
                            return {
                                "passed": True,
                                "reason": f"触发止损：亏损 {loss_ratio:.1%}"
                            }
            
            return {
                "passed": True,
                "reason": "风控检查通过"
            }
        
        except Exception as e:
            return {
                "passed": False,
                "reason": f"风控检查异常: {str(e)}"
            }
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取交易历史"""
        return self.trade_history[-limit:]
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """获取交易统计"""
        total = len(self.trade_history)
        successful = sum(1 for t in self.trade_history if t['result'].get('success'))
        
        buy_count = sum(1 for t in self.trade_history 
                       if t['signal']['action'] == 'buy')
        sell_count = sum(1 for t in self.trade_history 
                        if t['signal']['action'] == 'sell')
        
        return {
            "total_trades": total,
            "successful_trades": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "buy_count": buy_count,
            "sell_count": sell_count
        }


# 全局实例
trade_executor = TradeExecutor()








