"""
运营管理API
"""

from fastapi import APIRouter
from typing import Dict, Optional, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_analyzer import DataAnalyzer
from core.chart_expert import ChartExpert
from core.erp_connector import ERPConnector

router = APIRouter(prefix="/api/operations", tags=["Operations"])

# 初始化服务
erp_connector = ERPConnector(connection_type="both")
data_analyzer = DataAnalyzer(erp_connector)
chart_expert = ChartExpert()


@router.get("/manufacturing-flow")
async def get_manufacturing_flow():
    """获取制造流程分析"""
    analysis = await data_analyzer.analyze_manufacturing_flow()
    return {"success": True, "analysis": analysis}


@router.post("/charts/recommend")
async def recommend_chart(data: Dict, purpose: str = "analysis"):
    """推荐图表"""
    recommendation = chart_expert.recommend_chart(data, purpose)
    return {"success": True, "recommendation": recommendation}


@router.post("/charts/generate")
async def generate_chart(chart_type: str, data: Dict, options: Optional[Dict] = None):
    """生成图表配置"""
    config = chart_expert.generate_chart_config(chart_type, data, options or {})
    return {"success": True, "config": config}

