"""
财务管理API
"""

from fastapi import APIRouter
from typing import Dict, List, Optional, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from finance.core.price_analyzer import PriceAnalyzer
from finance.core.time_analyzer import TimeAnalyzer
from core.structured_logging import get_logger, trace_operation

# ERP连接器从finance模块导入
from finance.core.erp_connector import ERPConnector

router = APIRouter(prefix="/api/finance", tags=["Finance"])

# 初始化服务和日志记录器
erp_connector = ERPConnector(connection_type="both")
price_analyzer = PriceAnalyzer()
time_analyzer = TimeAnalyzer()
logger = get_logger("finance_api")


@router.get("/price/trend")
async def get_price_trend(product_id: Optional[int] = None, period: str = "30d"):
    """获取价格趋势"""
    with trace_operation("price_trend_analysis") as trace:
        try:
            logger.info(
                "开始价格趋势分析",
                product_id=product_id,
                period=period
            )
            
            trend = await price_analyzer.analyze_price_trend(product_id, period)
            
            logger.info("价格趋势分析完成", analysis_type=type(trend).__name__)
            
            return {"success": True, "trend": trend, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "价格趋势分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/price/compare")
async def compare_prices(products: List[int], competitors: Optional[List[str]] = None):
    """价格对比"""
    with trace_operation("price_comparison") as trace:
        try:
            logger.info(
                "开始价格对比分析",
                product_count=len(products),
                competitor_count=len(competitors) if competitors else 0
            )
            
            comparison = await price_analyzer.compare_prices(products, competitors)
            
            logger.info("价格对比分析完成")
            
            return {"success": True, "comparison": comparison, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "价格对比分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/price/optimize")
async def optimize_pricing(product_id: int, cost: float, market_data: Optional[Dict] = None):
    """优化定价"""
    with trace_operation("price_optimization") as trace:
        try:
            logger.info(
                "开始价格优化分析",
                product_id=product_id
            )
            
            optimization = await price_analyzer.optimize_pricing(product_id, cost, market_data)
            
            logger.info("价格优化分析完成")
            
            return {"success": True, "optimization": optimization, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "价格优化分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/work-hours/analyze")
async def analyze_work_hours(project_id: Optional[int] = None, period: str = "30d"):
    """分析工时"""
    with trace_operation("time_efficiency_analysis") as trace:
        try:
            logger.info(
                "开始工时效率分析",
                project_id=project_id,
                period=period
            )
            
            analysis = await time_analyzer.analyze_work_hours(project_id, period)
            
            logger.info("工时效率分析完成")
            
            return {"success": True, "analysis": analysis, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "工时效率分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/work-hours/optimize")
async def optimize_work_hours(project_id: int, current_hours: float, target_hours: Optional[float] = None):
    """优化工时"""
    with trace_operation("time_optimization") as trace:
        try:
            logger.info(
                "开始工时使用优化",
                project_id=project_id
            )
            
            optimization = await time_analyzer.optimize_work_hours(project_id, current_hours, target_hours)
            
            logger.info("工时使用优化完成")
            
            return {"success": True, "optimization": optimization, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "工时使用优化失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

