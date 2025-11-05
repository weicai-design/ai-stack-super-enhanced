"""
Stock Trading API
股票交易API接口

提供股票数据查询、策略分析、交易执行等功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/📈 Intelligent Stock Trading')

from core.stock_data_fetcher import default_fetcher
from core.strategy_engine import StrategyManager, TrendFollowingStrategy

router = APIRouter(prefix="/stock", tags=["Stock Trading API"])

# 初始化策略管理器
strategy_manager = StrategyManager()


# ============ Pydantic Models ============

class StockInfo(BaseModel):
    """股票信息模型"""
    code: str
    name: str
    market: str
    industry: Optional[str] = None


class StockPriceResponse(BaseModel):
    """股票价格响应"""
    code: str
    current_price: float
    change: float
    change_percent: float
    volume: int
    timestamp: str


class StrategyAnalysisResponse(BaseModel):
    """策略分析响应"""
    stock_code: str
    final_signal: str
    confidence: float
    individual_signals: Dict[str, str]
    analyses: Dict[str, Any]
    timestamp: str


# ============ API Endpoints ============

@router.get("/list", response_model=List[StockInfo])
async def get_stock_list(market: str = Query("A", description="市场类型 A/B/H")):
    """
    获取股票列表
    
    Args:
        market: 市场类型
        
    Returns:
        股票列表
    """
    try:
        stocks = default_fetcher.fetch_stock_list(market)
        return stocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


@router.get("/price/{stock_code}", response_model=StockPriceResponse)
async def get_stock_price(stock_code: str):
    """
    获取实时股价
    
    根据需求3.2: 全天候动态获取
    
    Args:
        stock_code: 股票代码
        
    Returns:
        实时价格数据
    """
    try:
        price_data = default_fetcher.fetch_realtime_price(stock_code)
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股价失败: {str(e)}")


@router.get("/history/{stock_code}")
async def get_historical_data(
    stock_code: str,
    days: int = Query(90, description="历史天数"),
):
    """
    获取历史数据
    
    Args:
        stock_code: 股票代码
        days: 历史天数
        
    Returns:
        历史数据
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = default_fetcher.fetch_historical_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "stock_code": stock_code,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


@router.get("/analyze/{stock_code}", response_model=StrategyAnalysisResponse)
async def analyze_stock(stock_code: str):
    """
    分析股票并生成交易信号
    
    根据需求3.2: 制定投资策略
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果和交易信号
    """
    try:
        # 获取历史数据
        historical_data = default_fetcher.fetch_historical_data(stock_code)
        
        # 使用策略管理器分析
        result = strategy_manager.get_combined_signal(
            stock_code=stock_code,
            stock_data={"historical": historical_data}
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/sentiment")
async def get_market_sentiment():
    """
    获取市场情绪
    
    根据需求3.3: 市场情绪分析
    
    Returns:
        市场情绪数据
    """
    try:
        sentiment = default_fetcher.fetch_market_sentiment()
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场情绪失败: {str(e)}")


@router.get("/strategies/performance")
async def get_strategies_performance():
    """
    获取所有策略表现
    
    根据需求3.5: 提供收益概率、收益率
    
    Returns:
        策略表现数据
    """
    try:
        performance = strategy_manager.get_all_strategies_performance()
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略表现失败: {str(e)}")


@router.get("/dashboard")
async def get_stock_dashboard():
    """
    获取股票交易看板数据
    
    Returns:
        看板数据
    """
    try:
        # 获取市场情绪
        sentiment = default_fetcher.fetch_market_sentiment()
        
        # 获取股票列表
        stocks = default_fetcher.fetch_stock_list("A")
        
        # 获取策略表现
        performance = strategy_manager.get_all_strategies_performance()
        
        # 模拟持仓数据
        positions = [
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "quantity": 100,
                "avg_cost": 1850.00,
                "current_price": 1920.50,
                "profit_loss": 7050.00,
                "profit_loss_percent": 3.81
            },
            {
                "stock_code": "000858",
                "stock_name": "五粮液",
                "quantity": 200,
                "avg_cost": 185.00,
                "current_price": 192.30,
                "profit_loss": 1460.00,
                "profit_loss_percent": 3.95
            }
        ]
        
        # 计算总资产
        total_assets = sum(p["quantity"] * p["current_price"] for p in positions)
        total_cost = sum(p["quantity"] * p["avg_cost"] for p in positions)
        total_profit = total_assets - total_cost
        total_return_rate = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "market_sentiment": sentiment,
            "positions": positions,
            "portfolio_summary": {
                "total_assets": round(total_assets, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "total_return_rate": round(total_return_rate, 2),
                "position_count": len(positions)
            },
            "strategies": performance,
            "stock_count": len(stocks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取看板数据失败: {str(e)}")


@router.get("/")
def root():
    """股票模块根路径"""
    return {
        "module": "Intelligent Stock Trading",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "list": "/stock/list",
            "price": "/stock/price/{code}",
            "history": "/stock/history/{code}",
            "analyze": "/stock/analyze/{code}",
            "sentiment": "/stock/sentiment",
            "dashboard": "/stock/dashboard"
        }
    }

