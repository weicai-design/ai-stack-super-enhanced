"""
股票分析器
Stock Analyzer

提供历史分析、市场情绪分析、收益分析

版本: v1.0.0
"""

import logging
from typing import Dict, List, Any
from .models import Stock, Trade

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self):
        logger.info("✅ 股票分析器已初始化")
    
    def analyze_historical_performance(
        self,
        stock_code: str,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        历史绩效分析
        
        Args:
            stock_code: 股票代码
            historical_data: 历史数据
        
        Returns:
            分析结果
        """
        if not historical_data:
            return {"available": False}
        
        # 计算收益率
        prices = [d["close"] for d in historical_data]
        if len(prices) < 2:
            return {"available": False}
        
        start_price = prices[0]
        end_price = prices[-1]
        total_return = (end_price - start_price) / start_price if start_price > 0 else 0
        
        # 计算波动率
        changes = []
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] > 0 else 0
            changes.append(change)
        
        volatility = (sum(c**2 for c in changes) / len(changes)) ** 0.5 if changes else 0
        
        return {
            "stock_code": stock_code,
            "period_days": len(historical_data),
            "start_price": start_price,
            "end_price": end_price,
            "total_return": total_return,
            "volatility": volatility,
            "trend": "上涨" if total_return > 0 else "下跌" if total_return < 0 else "平稳"
        }
    
    def analyze_sentiment(self, stock_code: str, news: List[str] = None) -> Dict[str, Any]:
        """
        市场情绪分析
        
        Args:
            stock_code: 股票代码
            news: 新闻列表
        
        Returns:
            情绪分析结果
        """
        # 简化版情绪分析
        # 实际应该使用NLP模型分析新闻
        
        positive_keywords = ["上涨", "利好", "增长", "盈利", "突破"]
        negative_keywords = ["下跌", "利空", "亏损", "风险", "下滑"]
        
        if news:
            positive_count = sum(1 for n in news if any(k in n for k in positive_keywords))
            negative_count = sum(1 for n in news if any(k in n for k in negative_keywords))
            
            if positive_count > negative_count:
                sentiment = "积极"
                score = 0.7
            elif negative_count > positive_count:
                sentiment = "消极"
                score = 0.3
            else:
                sentiment = "中性"
                score = 0.5
        else:
            sentiment = "中性"
            score = 0.5
        
        return {
            "stock_code": stock_code,
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.8
        }
    
    def calculate_portfolio_return(self, trades: List[Trade]) -> Dict[str, Any]:
        """
        计算投资组合收益
        
        Args:
            trades: 交易记录列表
        
        Returns:
            收益分析
        """
        if not trades:
            return {"available": False}
        
        # 计算总投入和总收益
        buy_amount = sum(t.amount for t in trades if t.action == "buy")
        sell_amount = sum(t.amount for t in trades if t.action == "sell")
        
        net_profit = sell_amount - buy_amount
        return_rate = net_profit / buy_amount if buy_amount > 0 else 0
        
        # 胜率
        profitable_trades = sum(1 for t in trades if t.action == "sell" and t.amount > 0)
        total_sells = sum(1 for t in trades if t.action == "sell")
        win_rate = profitable_trades / total_sells if total_sells > 0 else 0
        
        return {
            "total_trades": len(trades),
            "buy_amount": buy_amount,
            "sell_amount": sell_amount,
            "net_profit": net_profit,
            "return_rate": return_rate,
            "win_rate": win_rate
        }


stock_analyzer = StockAnalyzer()












