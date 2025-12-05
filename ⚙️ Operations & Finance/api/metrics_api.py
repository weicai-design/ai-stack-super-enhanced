"""
指标分析API接口 - 生产级增强
提供专家性能指标分析、对比和历史数据功能
"""

import sys
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# 添加路径以导入核心模块
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.metrics_analysis import get_metrics_analysis_api, AnalysisPeriod, PerformanceAnalysis, ComparativeAnalysis
from core.structured_logging import get_logger, trace_operation


# 创建路由
router = APIRouter(prefix="/api/metrics", tags=["指标分析"])

# 初始化日志记录器
logger = get_logger("metrics_api")

# 初始化指标分析API
metrics_analysis_api = get_metrics_analysis_api()


# 请求/响应模型
class PerformanceAnalysisRequest(BaseModel):
    expert_name: str
    period: str = "24h"  # 1h, 24h, 7d


class PerformanceAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[dict] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class ExpertComparisonRequest(BaseModel):
    expert_names: List[str]
    period: str = "24h"  # 1h, 24h, 7d


class ExpertComparisonResponse(BaseModel):
    success: bool
    comparison: Optional[dict] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class PerformanceHistoryRequest(BaseModel):
    expert_name: str
    metric_type: str  # response_time, success_count, error_count, request_count
    period: str = "24h"  # 1h, 24h, 7d
    interval: str = "30m"  # 5m, 30m, 1h


class PerformanceHistoryResponse(BaseModel):
    success: bool
    expert_name: Optional[str] = None
    metric_type: Optional[str] = None
    history: Optional[List[dict]] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    metrics_count: int
    experts_tracked: List[str]


# API端点
@router.get("/health", response_model=HealthCheckResponse, summary="健康检查")
async def metrics_health_check():
    """指标分析系统健康检查"""
    with trace_operation("metrics_health_check") as trace:
        try:
            logger.info("执行指标分析系统健康检查")
            
            # 获取监控的专家列表
            from core.monitoring_system import get_global_monitor
            monitor = get_global_monitor()
            
            # 执行健康检查
            health_info = monitor.health_check()
            
            # 获取跟踪的专家列表
            experts_tracked = list(set(
                key.split(":")[0] for key in monitor.metrics.keys()
            ))
            
            response = HealthCheckResponse(
                status=health_info["system_status"],
                timestamp=health_info["last_health_check"],
                metrics_count=health_info["metrics_collected"],
                experts_tracked=experts_tracked
            )
            
            logger.info("指标分析系统健康检查完成", 
                       status=health_info["system_status"],
                       metrics_count=health_info["metrics_collected"])
            
            return response
            
        except Exception as e:
            logger.error("指标分析系统健康检查失败", error=str(e))
            raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post("/analyze-performance", response_model=PerformanceAnalysisResponse, summary="分析专家性能")
async def analyze_expert_performance(request: PerformanceAnalysisRequest):
    """分析指定专家的性能指标"""
    with trace_operation("analyze_expert_performance") as trace:
        try:
            logger.info(
                "开始分析专家性能",
                expert_name=request.expert_name,
                period=request.period
            )
            
            result = metrics_api.analyze_expert_performance(
                request.expert_name, 
                request.period
            )
            
            if result["success"]:
                logger.info(
                    "专家性能分析完成",
                    expert_name=request.expert_name,
                    response_time=result["analysis"]["avg_response_time"]
                )
            else:
                logger.warning(
                    "专家性能分析失败",
                    expert_name=request.expert_name,
                    error=result.get("error", "未知错误")
                )
            
            # 添加trace_id
            result["trace_id"] = trace.request_id
            
            return result
            
        except Exception as e:
            logger.error(
                "分析专家性能时发生异常",
                expert_name=request.expert_name,
                error=str(e)
            )
            return PerformanceAnalysisResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.post("/compare-experts", response_model=ExpertComparisonResponse, summary="对比专家性能")
async def compare_experts_performance(request: ExpertComparisonRequest):
    """对比多个专家的性能指标"""
    with trace_operation("compare_experts_performance") as trace:
        try:
            logger.info(
                "开始对比专家性能",
                expert_count=len(request.expert_names),
                period=request.period
            )
            
            result = metrics_api.compare_experts_performance(
                request.expert_names, 
                request.period
            )
            
            if result["success"]:
                logger.info(
                    "专家性能对比完成",
                    expert_count=len(request.expert_names),
                    insights_count=len(result["comparison"]["insights"])
                )
            else:
                logger.warning(
                    "专家性能对比失败",
                    error=result.get("error", "未知错误")
                )
            
            # 添加trace_id
            result["trace_id"] = trace.request_id
            
            return result
            
        except Exception as e:
            logger.error("对比专家性能时发生异常", error=str(e))
            return ExpertComparisonResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.post("/performance-history", response_model=PerformanceHistoryResponse, summary="获取性能历史数据")
async def get_performance_history(request: PerformanceHistoryRequest):
    """获取专家的性能历史数据"""
    with trace_operation("get_performance_history") as trace:
        try:
            logger.info(
                "获取性能历史数据",
                expert_name=request.expert_name,
                metric_type=request.metric_type,
                period=request.period,
                interval=request.interval
            )
            
            result = metrics_api.get_performance_history(
                request.expert_name,
                request.metric_type,
                request.period,
                request.interval
            )
            
            if result["success"]:
                logger.info(
                    "性能历史数据获取完成",
                    expert_name=request.expert_name,
                    data_points=len(result["history"])
                )
            else:
                logger.warning(
                    "性能历史数据获取失败",
                    expert_name=request.expert_name,
                    error=result.get("error", "未知错误")
                )
            
            return PerformanceHistoryResponse(**result)
            
        except Exception as e:
            logger.error(
                "获取性能历史数据时发生异常",
                expert_name=request.expert_name,
                error=str(e)
            )
            return PerformanceHistoryResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.get("/available-metrics", summary="获取可用指标类型")
async def get_available_metrics():
    """获取可用的指标类型列表"""
    with trace_operation("get_available_metrics") as trace:
        try:
            logger.info("获取可用指标类型")
            
            available_metrics = [
                "response_time",
                "success_count", 
                "error_count",
                "request_count",
                "processing_time",
                "cache_hit_rate"
            ]
            
            logger.info("可用指标类型获取完成", count=len(available_metrics))
            
            return {
                "success": True,
                "metrics": available_metrics,
                "trace_id": trace.request_id
            }
            
        except Exception as e:
            logger.error("获取可用指标类型失败", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


@router.get("/tracked-experts", summary="获取跟踪的专家列表")
async def get_tracked_experts():
    """获取当前正在跟踪的专家列表"""
    with trace_operation("get_tracked_experts") as trace:
        try:
            logger.info("获取跟踪的专家列表")
            
            from core.monitoring_system import get_global_monitor
            monitor = get_global_monitor()
            
            # 获取跟踪的专家列表
            experts_tracked = list(set(
                key.split(":")[0] for key in monitor.metrics.keys()
            ))
            
            logger.info("跟踪的专家列表获取完成", count=len(experts_tracked))
            
            return {
                "success": True,
                "experts": experts_tracked,
                "trace_id": trace.request_id
            }
            
        except Exception as e:
            logger.error("获取跟踪的专家列表失败", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


# 专家性能分析快捷端点
@router.get("/performance/{expert_name}", summary="快速获取专家性能分析")
async def quick_performance_analysis(
    expert_name: str,
    period: str = Query("24h", regex="^(1h|24h|7d)$")
):
    """快速获取专家性能分析（GET版本）"""
    with trace_operation("quick_performance_analysis") as trace:
        try:
            logger.info(
                "快速获取专家性能分析",
                expert_name=expert_name,
                period=period
            )
            
            result = metrics_api.analyze_expert_performance(expert_name, period)
            
            if result["success"]:
                logger.info(
                    "快速性能分析完成",
                    expert_name=expert_name,
                    response_time=result["analysis"]["avg_response_time"]
                )
            
            # 添加trace_id
            result["trace_id"] = trace.request_id
            
            return result
            
        except Exception as e:
            logger.error(
                "快速性能分析失败",
                expert_name=expert_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


# 专家对比快捷端点
@router.get("/comparison", summary="快速对比专家性能")
async def quick_expert_comparison(
    experts: str = Query(..., description="专家名称，用逗号分隔"),
    period: str = Query("24h", regex="^(1h|24h|7d)$")
):
    """快速对比专家性能（GET版本）"""
    with trace_operation("quick_expert_comparison") as trace:
        try:
            expert_names = [name.strip() for name in experts.split(",") if name.strip()]
            
            logger.info(
                "快速对比专家性能",
                expert_count=len(expert_names),
                period=period
            )
            
            result = metrics_api.compare_experts_performance(expert_names, period)
            
            if result["success"]:
                logger.info(
                    "快速专家对比完成",
                    expert_count=len(expert_names),
                    insights_count=len(result["comparison"]["insights"])
                )
            
            # 添加trace_id
            result["trace_id"] = trace.request_id
            
            return result
            
        except Exception as e:
            logger.error("快速专家对比失败", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


# 性能历史数据快捷端点
@router.get("/history/{expert_name}/{metric_type}", summary="快速获取性能历史数据")
async def quick_performance_history(
    expert_name: str,
    metric_type: str,
    period: str = Query("24h", regex="^(1h|24h|7d)$"),
    interval: str = Query("30m", regex="^(5m|30m|1h)$")
):
    """快速获取性能历史数据（GET版本）"""
    with trace_operation("quick_performance_history") as trace:
        try:
            logger.info(
                "快速获取性能历史数据",
                expert_name=expert_name,
                metric_type=metric_type,
                period=period,
                interval=interval
            )
            
            result = metrics_api.get_performance_history(
                expert_name, metric_type, period, interval
            )
            
            if result["success"]:
                logger.info(
                    "快速历史数据获取完成",
                    expert_name=expert_name,
                    data_points=len(result["history"])
                )
            
            return result
            
        except Exception as e:
            logger.error(
                "快速历史数据获取失败",
                expert_name=expert_name,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


# 指标分析系统信息端点
@router.get("/system-info", summary="获取指标分析系统信息")
async def get_system_info():
    """获取指标分析系统的详细信息"""
    with trace_operation("get_system_info") as trace:
        try:
            logger.info("获取指标分析系统信息")
            
            from core.monitoring_system import get_global_monitor
            monitor = get_global_monitor()
            
            # 统计系统信息
            total_metrics = sum(len(metrics) for metrics in monitor.metrics.values())
            experts_tracked = list(set(
                key.split(":")[0] for key in monitor.metrics.keys()
            ))
            
            system_info = {
                "system_name": "运营财务指标分析系统",
                "version": "1.0.0",
                "total_metrics": total_metrics,
                "experts_tracked": experts_tracked,
                "experts_count": len(experts_tracked),
                "last_health_check": monitor.last_health_check.isoformat(),
                "alerts_active": len(monitor.alerts),
                "uptime_hours": (datetime.now() - monitor.start_time).total_seconds() / 3600
            }
            
            logger.info("指标分析系统信息获取完成", experts_count=len(experts_tracked))
            
            return {
                "success": True,
                "system_info": system_info,
                "trace_id": trace.request_id
            }
            
        except Exception as e:
            logger.error("获取指标分析系统信息失败", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace.request_id
            }


# 导入datetime用于系统信息
from datetime import datetime


# 新增指标分析API端点
class MetricsAnalysisRequest(BaseModel):
    expert_name: str
    period: str = "hour"  # real_time, hour, day, week, month


class MetricsAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[dict] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class ComparativeAnalysisRequest(BaseModel):
    expert_name: str
    comparison_type: str = "baseline"  # baseline, peer, historical


class ComparativeAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[dict] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


class AnalysisSummaryResponse(BaseModel):
    success: bool
    summary: Optional[dict] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None


@router.post("/analysis/performance", response_model=MetricsAnalysisResponse, summary="获取性能分析")
async def get_performance_analysis(request: MetricsAnalysisRequest):
    """获取专家性能分析（生产级增强）"""
    with trace_operation("get_performance_analysis") as trace:
        try:
            logger.info(
                "开始获取性能分析",
                expert_name=request.expert_name,
                period=request.period
            )
            
            result = metrics_analysis_api.get_performance_analysis(
                request.expert_name, 
                request.period
            )
            
            if result["success"]:
                logger.info(
                    "性能分析获取完成",
                    expert_name=request.expert_name,
                    health_score=result["analysis"]["health_score"]
                )
            else:
                logger.warning(
                    "性能分析获取失败",
                    expert_name=request.expert_name,
                    error=result.get("error", "未知错误")
                )
            
            return MetricsAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(
                "获取性能分析时发生异常",
                expert_name=request.expert_name,
                error=str(e)
            )
            return MetricsAnalysisResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.post("/analysis/comparative", response_model=ComparativeAnalysisResponse, summary="获取对比分析")
async def get_comparative_analysis(request: ComparativeAnalysisRequest):
    """获取专家对比分析"""
    with trace_operation("get_comparative_analysis") as trace:
        try:
            logger.info(
                "开始获取对比分析",
                expert_name=request.expert_name,
                comparison_type=request.comparison_type
            )
            
            result = metrics_analysis_api.get_comparative_analysis(
                request.expert_name, 
                request.comparison_type
            )
            
            if result["success"]:
                logger.info(
                    "对比分析获取完成",
                    expert_name=request.expert_name,
                    comparison_type=request.comparison_type
                )
            else:
                logger.warning(
                    "对比分析获取失败",
                    expert_name=request.expert_name,
                    error=result.get("error", "未知错误")
                )
            
            return ComparativeAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(
                "获取对比分析时发生异常",
                expert_name=request.expert_name,
                error=str(e)
            )
            return ComparativeAnalysisResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.get("/analysis/summary", response_model=AnalysisSummaryResponse, summary="获取分析摘要")
async def get_analysis_summary():
    """获取指标分析系统摘要"""
    with trace_operation("get_analysis_summary") as trace:
        try:
            logger.info("开始获取分析摘要")
            
            result = metrics_analysis_api.get_analysis_summary()
            
            if result["success"]:
                logger.info(
                    "分析摘要获取完成",
                    total_experts=result["summary"]["total_experts"]
                )
            else:
                logger.warning(
                    "分析摘要获取失败",
                    error=result.get("error", "未知错误")
                )
            
            return AnalysisSummaryResponse(**result)
            
        except Exception as e:
            logger.error("获取分析摘要时发生异常", error=str(e))
            return AnalysisSummaryResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


# 快捷GET端点
@router.get("/analysis/performance/{expert_name}", response_model=MetricsAnalysisResponse, summary="快速获取性能分析")
async def quick_performance_analysis(
    expert_name: str,
    period: str = Query("hour", regex="^(real_time|hour|day|week|month)$")
):
    """快速获取性能分析（GET版本）"""
    with trace_operation("quick_performance_analysis") as trace:
        try:
            logger.info(
                "快速获取性能分析",
                expert_name=expert_name,
                period=period
            )
            
            result = metrics_analysis_api.get_performance_analysis(expert_name, period)
            
            if result["success"]:
                logger.info(
                    "快速性能分析完成",
                    expert_name=expert_name,
                    health_score=result["analysis"]["health_score"]
                )
            
            return MetricsAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(
                "快速性能分析失败",
                expert_name=expert_name,
                error=str(e)
            )
            return MetricsAnalysisResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )


@router.get("/analysis/comparative/{expert_name}", response_model=ComparativeAnalysisResponse, summary="快速获取对比分析")
async def quick_comparative_analysis(
    expert_name: str,
    comparison_type: str = Query("baseline", regex="^(baseline|peer|historical)$")
):
    """快速获取对比分析（GET版本）"""
    with trace_operation("quick_comparative_analysis") as trace:
        try:
            logger.info(
                "快速获取对比分析",
                expert_name=expert_name,
                comparison_type=comparison_type
            )
            
            result = metrics_analysis_api.get_comparative_analysis(expert_name, comparison_type)
            
            if result["success"]:
                logger.info(
                    "快速对比分析完成",
                    expert_name=expert_name,
                    comparison_type=comparison_type
                )
            
            return ComparativeAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(
                "快速对比分析失败",
                expert_name=expert_name,
                error=str(e)
            )
            return ComparativeAnalysisResponse(
                success=False,
                error=str(e),
                trace_id=trace.request_id
            )