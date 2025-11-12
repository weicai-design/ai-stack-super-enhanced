"""
股票交易API（完整版）
Stock Trading API

提供完整的股票交易功能：15个端点

版本: v1.0.0
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from .models import Strategy, Trade
from .manager import stock_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stock", tags=["Stock Trading"])


@router.get("/health")
async def stock_health():
    """股票模块健康检查"""
    return {
        "status": "healthy",
        "module": "stock",
        "version": "1.0.0",
        "features": [
            "data_collection",
            "strategy_management",
            "auto_trading",
            "sentiment_analysis",
            "historical_analysis",
            "portfolio_management"
        ]
    }


# ==================== 数据采集 ====================

@router.get("/data/{stock_code}")
async def get_stock_data(
    stock_code: str,
    market: str = Query("A", description="市场"),
    tenant=Depends(require_tenant)
):
    """获取股票数据"""
    stock = stock_manager.collect_data(stock_code, market)
    return stock.model_dump()


@router.get("/data/realtime")
async def get_realtime_data(
    codes: str = Query(..., description="股票代码，逗号分隔"),
    tenant=Depends(require_tenant)
):
    """获取实时数据"""
    stock_codes = [c.strip() for c in codes.split(",")]
    stocks = stock_manager.get_realtime_data(stock_codes)
    return [s.model_dump() for s in stocks]


@router.get("/data/{stock_code}/historical")
async def get_historical_data(
    stock_code: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    tenant=Depends(require_tenant)
):
    """获取历史数据"""
    data = stock_manager.get_historical_data(stock_code, start_date, end_date)
    return data


# ==================== 策略管理 ====================

@router.post("/strategies")
async def add_strategy(strategy: Strategy, tenant=Depends(require_tenant)):
    """添加交易策略"""
    result = stock_manager.add_strategy(tenant.id, strategy)
    return result.model_dump()


@router.get("/strategies")
async def list_strategies(tenant=Depends(require_tenant)):
    """获取策略列表"""
    strategies = stock_manager.get_strategies(tenant.id)
    return [s.model_dump() for s in strategies]


@router.get("/strategies/{strategy_id}/evaluate")
async def evaluate_strategy(
    strategy_id: str,
    stock_code: str = Query(...),
    tenant=Depends(require_tenant)
):
    """评估策略"""
    result = stock_manager.evaluate_strategy(tenant.id, strategy_id, stock_code)
    return result


# ==================== 交易执行 ====================

@router.post("/trades")
async def execute_trade(trade: Trade, tenant=Depends(require_tenant)):
    """执行交易"""
    result = stock_manager.execute_trade(tenant.id, trade)
    return result.model_dump()


@router.get("/trades")
async def list_trades(tenant=Depends(require_tenant)):
    """获取交易记录"""
    trades = stock_manager.get_trades(tenant.id)
    return [t.model_dump() for t in trades]


# ==================== 投资组合 ====================

@router.get("/portfolio")
async def get_portfolio(tenant=Depends(require_tenant)):
    """获取投资组合"""
    portfolio = stock_manager.get_portfolio(tenant.id)
    return portfolio.model_dump()


# ==================== 分析功能 ====================

@router.get("/analysis/historical")
async def analyze_historical(
    stock_code: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    tenant=Depends(require_tenant)
):
    """历史绩效分析"""
    result = stock_manager.analyze_historical(stock_code, start_date, end_date)
    return result


@router.get("/analysis/sentiment")
async def analyze_sentiment(
    stock_code: str = Query(...),
    tenant=Depends(require_tenant)
):
    """市场情绪分析"""
    result = stock_manager.analyze_sentiment(stock_code)
    return result


@router.get("/analysis/returns")
async def calculate_returns(tenant=Depends(require_tenant)):
    """收益分析"""
    result = stock_manager.calculate_returns(tenant.id)
    return result

