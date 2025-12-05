"""
运营财务专家API接口
提供专家级的运营财务分析和管理功能
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import sys
import os

# 添加模块路径
operations_path = os.path.join(os.path.dirname(__file__), "..", "operations")
finance_path = os.path.join(os.path.dirname(__file__), "..", "finance")
sys.path.insert(0, operations_path)
sys.path.insert(0, finance_path)

from core.data_analyzer import DataAnalyzer
from core.chart_expert import ChartExpert
from core.erp_connector import ERPConnector
from core.price_analyzer import PriceAnalyzer
from core.time_analyzer import TimeAnalyzer
from core.structured_logging import get_logger, trace_operation

router = APIRouter(prefix="/api/experts", tags=["Experts"])

# 初始化专家服务和日志记录器
erp_connector = ERPConnector(connection_type="both")
data_analyzer = DataAnalyzer(erp_connector)
chart_expert = ChartExpert()
price_analyzer = PriceAnalyzer()
time_analyzer = TimeAnalyzer()
logger = get_logger("experts_api")

# 请求模型
class ExpertAnalysisRequest(BaseModel):
    """专家分析请求"""
    analysis_type: str
    parameters: Dict[str, Any]
    timeframe: Optional[str] = "30d"
    expert_level: str = "advanced"

class OptimizationRequest(BaseModel):
    """优化请求"""
    target: str
    constraints: Dict[str, Any]
    optimization_method: str = "multi_objective"

class ChartGenerationRequest(BaseModel):
    """图表生成请求"""
    data: Dict[str, Any]
    chart_type: Optional[str] = None
    purpose: str = "analysis"
    customization: Optional[Dict[str, Any]] = None

# 专家分析端点
@router.post("/analysis")
async def expert_analysis(request: ExpertAnalysisRequest):
    """专家级分析"""
    with trace_operation("expert_analysis") as trace:
        try:
            logger.info(
                "开始专家级分析",
                analysis_type=request.analysis_type,
                parameters=request.parameters
            )
            
            if request.analysis_type == "manufacturing_flow":
                result = await data_analyzer.analyze_manufacturing_flow()
            elif request.analysis_type == "price_trend":
                product_id = request.parameters.get("product_id")
                result = await price_analyzer.analyze_price_trend(product_id, request.timeframe)
            elif request.analysis_type == "work_hours":
                project_id = request.parameters.get("project_id")
                result = await time_analyzer.analyze_work_hours(project_id, request.timeframe)
            else:
                logger.warning("不支持的分析类型", analysis_type=request.analysis_type)
                raise HTTPException(status_code=400, detail=f"不支持的分析类型: {request.analysis_type}")
            
            logger.info("专家级分析完成", analysis_type=request.analysis_type)
            
            return {
                "success": True,
                "analysis_type": request.analysis_type,
                "expert_level": request.expert_level,
                "result": result,
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "专家级分析失败",
                analysis_type=request.analysis_type,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

# 优化端点
@router.post("/optimization")
async def expert_optimization(request: OptimizationRequest):
    """专家级优化"""
    with trace_operation("expert_optimization") as trace:
        try:
            logger.info(
                "开始专家级优化",
                target=request.target,
                constraints=request.constraints
            )
            
            if request.target == "pricing":
                product_id = request.constraints.get("product_id")
                cost = request.constraints.get("cost")
                market_data = request.constraints.get("market_data", {})
                result = await price_analyzer.optimize_pricing(product_id, cost, market_data)
            elif request.target == "work_hours":
                project_id = request.constraints.get("project_id")
                current_hours = request.constraints.get("current_hours")
                target_hours = request.constraints.get("target_hours")
                result = await time_analyzer.optimize_work_hours(project_id, current_hours, target_hours)
            else:
                logger.warning("不支持的优化目标", target=request.target)
                raise HTTPException(status_code=400, detail=f"不支持的优化目标: {request.target}")
            
            logger.info("专家级优化完成", target=request.target)
            
            return {
                "success": True,
                "target": request.target,
                "optimization_method": request.optimization_method,
                "result": result,
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "专家级优化失败",
                target=request.target,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"优化失败: {str(e)}")

# 图表专家端点
@router.post("/charts/recommend")
async def expert_chart_recommendation(request: ChartGenerationRequest):
    """专家图表推荐"""
    with trace_operation("expert_chart_recommendation") as trace:
        try:
            logger.info(
                "开始专家图表推荐",
                purpose=request.purpose,
                data_keys=list(request.data.keys()) if request.data else []
            )
            
            recommendation = chart_expert.recommend_chart(request.data, request.purpose)
            
            logger.info("专家图表推荐完成", purpose=request.purpose)
            
            return {
                "success": True,
                "recommendation": recommendation,
                "purpose": request.purpose,
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "专家图表推荐失败",
                purpose=request.purpose,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"图表推荐失败: {str(e)}")

@router.post("/charts/generate")
async def expert_chart_generation(request: ChartGenerationRequest):
    """专家图表生成"""
    with trace_operation("expert_chart_generation") as trace:
        try:
            logger.info(
                "开始专家图表生成",
                chart_type=request.chart_type,
                purpose=request.purpose
            )
            
            if not request.chart_type:
                # 如果没有指定图表类型，先推荐
                recommendation = chart_expert.recommend_chart(request.data, request.purpose)
                request.chart_type = recommendation.get("recommended_chart")
            
            config = chart_expert.generate_chart_config(
                request.chart_type, 
                request.data, 
                request.customization or {}
            )
            
            logger.info("专家图表生成完成", chart_type=request.chart_type)
            
            return {
                "success": True,
                "chart_type": request.chart_type,
                "config": config,
                "customization": request.customization,
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "专家图表生成失败",
                chart_type=request.chart_type,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"图表生成失败: {str(e)}")

# 综合运营财务分析端点
@router.post("/comprehensive-analysis")
async def comprehensive_analysis(parameters: Dict[str, Any]):
    """综合运营财务分析"""
    with trace_operation("comprehensive_analysis") as trace:
        try:
            logger.info(
                "开始综合运营财务分析",
                parameters=parameters
            )
            
            # 并行执行多个分析
            analyses = {}
            
            # 制造流程分析
            if parameters.get("include_manufacturing", True):
                analyses["manufacturing_flow"] = await data_analyzer.analyze_manufacturing_flow()
            
            # 价格趋势分析
            if parameters.get("include_pricing", True):
                product_id = parameters.get("product_id")
                analyses["price_trend"] = await price_analyzer.analyze_price_trend(product_id, "30d")
            
            # 工时分析
            if parameters.get("include_work_hours", True):
                project_id = parameters.get("project_id")
                analyses["work_hours"] = await time_analyzer.analyze_work_hours(project_id, "30d")
            
            # 价格对比分析
            if parameters.get("include_price_comparison", False):
                products = parameters.get("products", [])
                competitors = parameters.get("competitors", [])
                analyses["price_comparison"] = await price_analyzer.compare_prices(products, competitors)
            
            logger.info("综合运营财务分析完成", analysis_count=len(analyses))
            
            return {
                "success": True,
                "analyses": analyses,
                "parameters": parameters,
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "综合运营财务分析失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"综合分析失败: {str(e)}")

# 专家健康检查
@router.get("/health")
async def experts_health_check():
    """专家服务健康检查"""
    with trace_operation("experts_health_check") as trace:
        try:
            logger.info("开始专家服务健康检查")
            
            # 检查各个专家服务的状态
            services_status = {
                "data_analyzer": True,
                "chart_expert": True,
                "price_analyzer": True,
                "time_analyzer": True,
                "erp_connector": erp_connector.listening
            }
            
            logger.info("专家服务健康检查完成", services_status=services_status)
            
            return {
                "success": True,
                "status": "healthy",
                "services": services_status,
                "timestamp": "2024-01-01T00:00:00Z",  # 实际实现中应该使用当前时间
                "trace_id": trace.request_id
            }
        except Exception as e:
            logger.error(
                "专家服务健康检查失败",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "trace_id": trace.request_id
            }

# 专家能力列表
@router.get("/capabilities")
async def get_expert_capabilities():
    """获取专家能力列表"""
    return {
        "success": True,
        "capabilities": {
            "analysis_types": [
                "manufacturing_flow",
                "price_trend", 
                "work_hours",
                "price_comparison"
            ],
            "optimization_targets": [
                "pricing",
                "work_hours"
            ],
            "chart_types": [
                "line",
                "bar", 
                "pie",
                "scatter",
                "heatmap",
                "gauge"
            ],
            "expert_levels": [
                "basic",
                "intermediate", 
                "advanced",
                "expert"
            ]
        }
    }