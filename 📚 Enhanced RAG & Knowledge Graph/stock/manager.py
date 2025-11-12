"""
股票管理器（增强版）
Stock Manager

版本: v1.0.0
"""

import logging
from typing import Dict, List, Optional
from collections import defaultdict
from .models import Stock, Strategy, Trade, Portfolio
from .data_collector import stock_collector
from .strategy_engine import strategy_engine
from .analyzer import stock_analyzer

logger = logging.getLogger(__name__)


class StockManager:
    """股票管理器（增强版）"""
    
    def __init__(self):
        self.stocks: Dict[str, Stock] = {}
        self.strategies: Dict[str, List[Strategy]] = defaultdict(list)
        self.trades: Dict[str, List[Trade]] = defaultdict(list)
        
        # 核心组件
        self.collector = stock_collector
        self.strategy_engine = strategy_engine
        self.analyzer = stock_analyzer
        
        logger.info("✅ 股票管理器（增强版）已初始化")
    
    # ==================== 数据采集 ====================
    
    def collect_data(self, stock_code: str, market: str = "A") -> Stock:
        """采集股票数据"""
        return self.collector.collect_stock_data(stock_code, market)
    
    def get_realtime_data(self, stock_codes: List[str]) -> List[Stock]:
        """获取实时数据"""
        return self.collector.get_realtime_data(stock_codes)
    
    def get_historical_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """获取历史数据"""
        return self.collector.get_historical_data(stock_code, start_date, end_date)
    
    # ==================== 策略管理 ====================
    
    def add_strategy(self, tenant_id: str, strategy: Strategy) -> Strategy:
        """添加策略"""
        strategy.tenant_id = tenant_id
        self.strategies[tenant_id].append(strategy)
        logger.info(f"策略已添加: {strategy.name}")
        return strategy
    
    def get_strategies(self, tenant_id: str) -> List[Strategy]:
        """获取策略列表"""
        return self.strategies.get(tenant_id, [])
    
    def evaluate_strategy(
        self,
        tenant_id: str,
        strategy_id: str,
        stock_code: str
    ) -> Optional[Dict]:
        """评估策略"""
        # 找到策略
        strategy = None
        for s in self.strategies.get(tenant_id, []):
            if s.id == strategy_id:
                strategy = s
                break
        
        if not strategy:
            return None
        
        # 获取股票数据
        stock = self.collect_data(stock_code)
        
        # 评估策略
        return self.strategy_engine.evaluate_strategy(strategy, stock)
    
    # ==================== 交易执行 ====================
    
    def execute_trade(self, tenant_id: str, trade: Trade) -> Trade:
        """执行交易"""
        trade.tenant_id = tenant_id
        self.trades[tenant_id].append(trade)
        logger.info(f"交易已执行: {trade.action} {trade.stock_code}")
        return trade
    
    def get_trades(self, tenant_id: str) -> List[Trade]:
        """获取交易记录"""
        return self.trades.get(tenant_id, [])
    
    # ==================== 投资组合 ====================
    
    def get_portfolio(self, tenant_id: str) -> Portfolio:
        """获取投资组合"""
        trades = self.trades.get(tenant_id, [])
        
        # 计算总价值
        buy_amount = sum(t.amount for t in trades if t.action == "buy")
        sell_amount = sum(t.amount for t in trades if t.action == "sell")
        
        # 计算持仓
        holdings = defaultdict(int)
        for trade in trades:
            if trade.action == "buy":
                holdings[trade.stock_code] += trade.quantity
            elif trade.action == "sell":
                holdings[trade.stock_code] -= trade.quantity
        
        holdings_list = [
            {"code": code, "quantity": qty}
            for code, qty in holdings.items() if qty > 0
        ]
        
        # 计算收益
        total_return = sell_amount - buy_amount
        
        return Portfolio(
            tenant_id=tenant_id,
            total_value=buy_amount,
            cash=sell_amount - buy_amount,
            holdings=holdings_list,
            total_return=total_return
        )
    
    # ==================== 分析功能 ====================
    
    def analyze_historical(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """历史分析"""
        historical_data = self.get_historical_data(stock_code, start_date, end_date)
        return self.analyzer.analyze_historical_performance(stock_code, historical_data)
    
    def analyze_sentiment(self, stock_code: str) -> Dict:
        """市场情绪分析"""
        return self.analyzer.analyze_sentiment(stock_code)
    
    def calculate_returns(self, tenant_id: str) -> Dict:
        """计算收益"""
        trades = self.get_trades(tenant_id)
        return self.analyzer.calculate_portfolio_return(trades)


stock_manager = StockManager()

