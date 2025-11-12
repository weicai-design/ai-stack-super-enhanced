"""
财务管理API
"""

from fastapi import APIRouter
from typing import Dict, List, Optional, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.price_analyzer import PriceAnalyzer
from core.time_analyzer import TimeAnalyzer

# ERP连接器从operations模块导入
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "operations"))
from core.erp_connector import ERPConnector

router = APIRouter(prefix="/api/finance", tags=["Finance"])

# 初始化服务
erp_connector = ERPConnector(connection_type="both")
price_analyzer = PriceAnalyzer()
time_analyzer = TimeAnalyzer()


@router.get("/price/trend")
async def get_price_trend(product_id: Optional[int] = None, period: str = "30d"):
    """获取价格趋势"""
    trend = await price_analyzer.analyze_price_trend(product_id, period)
    return {"success": True, "trend": trend}


@router.post("/price/compare")
async def compare_prices(products: List[int], competitors: Optional[List[str]] = None):
    """价格对比"""
    comparison = await price_analyzer.compare_prices(products, competitors)
    return {"success": True, "comparison": comparison}


@router.post("/price/optimize")
async def optimize_pricing(product_id: int, cost: float, market_data: Optional[Dict] = None):
    """优化定价"""
    optimization = await price_analyzer.optimize_pricing(product_id, cost, market_data)
    return {"success": True, "optimization": optimization}


@router.get("/work-hours/analyze")
async def analyze_work_hours(project_id: Optional[int] = None, period: str = "30d"):
    """分析工时"""
    analysis = await time_analyzer.analyze_work_hours(project_id, period)
    return {"success": True, "analysis": analysis}


@router.post("/work-hours/optimize")
async def optimize_work_hours(project_id: int, current_hours: float, target_hours: Optional[float] = None):
    """优化工时"""
    optimization = await time_analyzer.optimize_work_hours(project_id, current_hours, target_hours)
    return {"success": True, "optimization": optimization}

