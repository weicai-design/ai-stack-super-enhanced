"""
策略引擎
Strategy Engine

股票交易策略引擎

版本: v1.0.0
"""

import logging
from typing import Dict, List, Any
from .models import Strategy, Stock

logger = logging.getLogger(__name__)


class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        logger.info("✅ 策略引擎已初始化")
    
    def evaluate_strategy(
        self,
        strategy: Strategy,
        stock: Stock
    ) -> Dict[str, Any]:
        """
        评估策略
        
        Args:
            strategy: 交易策略
            stock: 股票数据
        
        Returns:
            评估结果
        """
        rules = strategy.rules
        
        # 简单规则评估
        signals = []
        
        # 价格规则
        if "buy_price" in rules and stock.price <= rules["buy_price"]:
            signals.append({"action": "buy", "reason": "价格达到买入点"})
        
        if "sell_price" in rules and stock.price >= rules["sell_price"]:
            signals.append({"action": "sell", "reason": "价格达到卖出点"})
        
        # 涨跌幅规则
        if "max_loss" in rules and stock.change < -rules["max_loss"]:
            signals.append({"action": "sell", "reason": "止损"})
        
        if "target_profit" in rules and stock.change > rules["target_profit"]:
            signals.append({"action": "sell", "reason": "止盈"})
        
        return {
            "stock_code": stock.code,
            "strategy_name": strategy.name,
            "signals": signals,
            "recommendation": signals[0]["action"] if signals else "hold"
        }
    
    def optimize_strategy(
        self,
        strategy: Strategy,
        trade_results: List[Dict[str, Any]]
    ) -> Strategy:
        """
        优化策略（自我学习）
        
        Args:
            strategy: 当前策略
            trade_results: 交易结果
        
        Returns:
            优化后的策略
        """
        # 计算策略表现
        total_trades = len(trade_results)
        profitable_trades = sum(1 for t in trade_results if t.get("profit", 0) > 0)
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        logger.info(f"策略 {strategy.name} 胜率: {win_rate:.1%}")
        
        # 简单优化：如果胜率低，调整参数
        if win_rate < 0.5 and "buy_price" in strategy.rules:
            strategy.rules["buy_price"] *= 0.95  # 降低买入价
            logger.info(f"策略优化: 降低买入价到 {strategy.rules['buy_price']}")
        
        return strategy


strategy_engine = StrategyEngine()












