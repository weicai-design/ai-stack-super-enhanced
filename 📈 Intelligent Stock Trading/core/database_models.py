"""
Stock Trading Database Models
股票交易数据库模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Stock(Base):
    """股票信息表"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    market = Column(String(10))  # A/B/H
    industry = Column(String(50))
    market_cap = Column(Float)  # 市值
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockPrice(Base):
    """股价数据表"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float)  # 成交量
    turnover = Column(Float)  # 成交额
    change_percent = Column(Float)  # 涨跌幅
    created_at = Column(DateTime, default=datetime.utcnow)


class TradingStrategy(Base):
    """交易策略表"""
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50))  # trend/value/ai
    parameters = Column(JSON)  # 策略参数
    is_active = Column(Boolean, default=True)
    performance_metrics = Column(JSON)  # 表现指标
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Trade(Base):
    """交易记录表"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    strategy_id = Column(Integer)
    action = Column(String(10), nullable=False)  # buy/sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)  # 金额
    commission = Column(Float, default=0)  # 手续费
    trade_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending/executed/cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    """持仓表"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)  # 持仓数量
    avg_cost = Column(Float, nullable=False)  # 平均成本
    current_price = Column(Float)  # 当前价格
    market_value = Column(Float)  # 市值
    profit_loss = Column(Float)  # 盈亏
    profit_loss_percent = Column(Float)  # 盈亏比例
    last_updated = Column(DateTime, default=datetime.utcnow)


class MarketSentiment(Base):
    """市场情绪表"""
    __tablename__ = "market_sentiment"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Float)  # 情绪分数 0-100
    fear_greed_index = Column(Float)  # 恐惧贪婪指数
    market_trend = Column(String(20))  # 市场趋势
    volume_ratio = Column(Float)  # 成交量比率
    news_sentiment = Column(JSON)  # 新闻情绪
    created_at = Column(DateTime, default=datetime.utcnow)


class StrategyPerformance(Base):
    """策略表现记录表"""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_return = Column(Float)  # 总收益率
    win_rate = Column(Float)  # 胜率
    sharpe_ratio = Column(Float)  # 夏普比率
    max_drawdown = Column(Float)  # 最大回撤
    trade_count = Column(Integer)  # 交易次数
    metrics = Column(JSON)  # 其他指标
    created_at = Column(DateTime, default=datetime.utcnow)

