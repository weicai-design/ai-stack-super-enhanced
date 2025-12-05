"""
运营管理API
"""

from fastapi import APIRouter
from typing import Dict, Optional, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from operations.core.erp_connector import ERPConnector
from operations.core.data_analyzer import DataAnalyzer
from operations.core.chart_expert import ChartExpert
from core.structured_logging import get_logger, trace_operation

router = APIRouter(prefix="/api/operations", tags=["Operations"])

# 初始化服务和日志记录器
erp_connector = ERPConnector(connection_type="both")
data_analyzer = DataAnalyzer(erp_connector)
chart_expert = ChartExpert()
logger = get_logger("operations_api")


@router.get("/manufacturing-flow")
async def get_manufacturing_flow():
    """获取制造流程分析"""
    with trace_operation("manufacturing_flow_analysis") as trace:
        try:
            logger.info("开始制造流程分析")
            
            analysis = await data_analyzer.analyze_manufacturing_flow()
            
            logger.info("制造流程分析完成", analysis_type=type(analysis).__name__)
            
            return {"success": True, "analysis": analysis, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "制造流程分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/charts/recommend")
async def recommend_chart(data: Dict, purpose: str = "analysis"):
    """推荐图表"""
    with trace_operation("chart_recommendation") as trace:
        try:
            logger.info(
                "开始图表推荐",
                purpose=purpose
            )
            
            recommendation = chart_expert.recommend_chart(data, purpose)
            
            logger.info("图表推荐完成")
            
            return {"success": True, "recommendation": recommendation, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "图表推荐失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/charts/generate")
async def generate_chart(chart_type: str, data: Dict, options: Optional[Dict] = None):
    """生成图表配置"""
    with trace_operation("chart_generation") as trace:
        try:
            logger.info(
                "开始生成图表配置",
                chart_type=chart_type
            )
            
            config = chart_expert.generate_chart_config(chart_type, data, options or {})
            
            logger.info("图表配置生成完成")
            
            return {"success": True, "config": config, "trace_id": trace.request_id}
        except Exception as e:
            logger.error(
                "图表配置生成失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

