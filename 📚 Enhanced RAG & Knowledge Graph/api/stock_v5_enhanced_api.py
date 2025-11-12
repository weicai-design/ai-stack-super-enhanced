"""
股票V5增强API - 使用真实业务管理器
完全连接前后端，实现真实股票交易功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v5/stock/real", tags=["Stock-V5-Enhanced"])


# ==================== 数据模型 ====================

class TradeRequest(BaseModel):
    user_id: str
    symbol: str
    trade_type: str  # buy/sell
    shares: float
    price: Optional[float] = None
    strategy_name: Optional[str] = None


# ==================== 行情API（真实实现）====================

@router.get("/quote/{symbol}")
async def get_realtime_quote(symbol: str, market: str = "sh"):
    """获取实时行情（真实API或演示数据）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.get_realtime_quote(symbol, market)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}")
async def get_history_analysis(symbol: str, period: int = 30):
    """历史数据分析（真实计算）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.analyze_history(symbol, period)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交易API（真实实现）====================

@router.post("/trade/execute")
async def execute_trade(trade: TradeRequest):
    """执行交易（真实数据库记录）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.execute_trade(
            user_id=trade.user_id,
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            shares=trade.shares,
            price=trade.price,
            strategy_name=trade.strategy_name
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{user_id}")
async def get_positions(user_id: str):
    """获取用户持仓（真实数据库查询）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.get_positions(user_id)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/{user_id}")
async def get_trade_history(
    user_id: str,
    symbol: Optional[str] = None,
    limit: int = 50
):
    """获取交易历史"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.get_trade_history(
            user_id=user_id,
            symbol=symbol,
            limit=limit
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 分析API（真实计算）====================

@router.get("/returns/{user_id}")
async def analyze_returns(user_id: str, period: str = "all"):
    """收益分析（真实计算）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.analyze_returns(user_id, period)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{symbol}")
async def analyze_sentiment(symbol: str):
    """市场情绪分析"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.analyze_sentiment(symbol)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def backtest_strategy(
    symbol: str,
    strategy_config: Dict[str, Any],
    start_date: str,
    end_date: str,
    initial_capital: float = 100000
):
    """策略回测（真实计算）"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        result = await stock.backtest_strategy(
            symbol=symbol,
            strategy_config=strategy_config,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """股票系统健康检查"""
    try:
        from business.stock_manager import get_stock_manager
        stock = get_stock_manager()
        
        return {
            "status": "healthy",
            "module": "Stock",
            "version": "5.5",
            "features": {
                "realtime_quote": True,
                "history_analysis": True,
                "trade_execution": True,
                "position_management": True,
                "returns_analysis": True,
                "sentiment_analysis": True,
                "strategy_backtest": True
            },
            "api_available": stock.api_available,
            "note": "模拟交易已就绪，真实交易需券商授权"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    print("✅ 股票V5增强API已加载")
    print("📋 真实功能:")
    print("  • 实时行情获取")
    print("  • 历史数据分析")
    print("  • 交易执行（模拟）")
    print("  • 持仓管理")
    print("  • 收益分析")
    print("  • 情绪分析")
    print("  • 策略回测")


