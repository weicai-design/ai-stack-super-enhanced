"""
统计分析和报告API
Analytics and Reporting API

提供使用统计、趋势分析、报告生成等功能

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])


# ==================== 数据模型 ====================

class OverviewStats(BaseModel):
    """概览统计"""
    total_requests: int = Field(0, description="总请求数")
    total_errors: int = Field(0, description="总错误数")
    error_rate: str = Field("0%", description="错误率")
    uptime_hours: float = Field(0, description="运行时长（小时）")
    avg_response_time: str = Field("0s", description="平均响应时间")
    requests_per_second: float = Field(0, description="每秒请求数")


class EndpointStats(BaseModel):
    """端点统计"""
    endpoint: str
    count: int
    avg_time: str
    errors: int
    success_rate: str


class IPStats(BaseModel):
    """IP统计"""
    ip: str
    count: int
    unique_endpoints: int
    errors: int


class AnalyticsReport(BaseModel):
    """分析报告"""
    report_time: str
    statistics: Dict[str, Any]
    hourly_trend: Dict[str, int]
    daily_trend: Dict[str, int]
    slow_requests: List[Dict]
    recent_errors: List[Dict]


# ==================== API端点 ====================

@router.get("/overview", response_model=Dict[str, Any])
async def get_overview_statistics():
    """
    获取概览统计
    
    返回总请求数、错误率、响应时间等核心指标
    
    Returns:
        概览统计数据
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        stats = store.get_statistics()
        
        return stats.get("overview", {})
    
    except ImportError:
        return {
            "total_requests": 0,
            "total_errors": 0,
            "error_rate": "0%",
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取概览统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints")
async def get_endpoint_statistics(
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    """
    获取端点统计
    
    返回各端点的请求数、响应时间、错误率等
    
    Args:
        limit: 返回的端点数量
    
    Returns:
        端点统计列表
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        stats = store.get_statistics()
        
        endpoints = stats.get("top_endpoints", [])[:limit]
        
        return {
            "total_endpoints": len(endpoints),
            "endpoints": endpoints
        }
    
    except ImportError:
        return {
            "total_endpoints": 0,
            "endpoints": [],
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取端点统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ips")
async def get_ip_statistics(
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    """
    获取IP统计
    
    返回各IP的请求数、访问端点数、错误数等
    
    Args:
        limit: 返回的IP数量
    
    Returns:
        IP统计列表
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        stats = store.get_statistics()
        
        ips = stats.get("top_ips", [])[:limit]
        
        return {
            "total_ips": len(ips),
            "ips": ips
        }
    
    except ImportError:
        return {
            "total_ips": 0,
            "ips": [],
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取IP统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/hourly")
async def get_hourly_trends(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）")
):
    """
    获取小时趋势
    
    返回最近N小时的请求数趋势
    
    Args:
        hours: 时间范围（1-168小时）
    
    Returns:
        小时趋势数据
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        hourly_stats = store.get_hourly_stats(hours)
        
        return {
            "period": f"last_{hours}_hours",
            "data": hourly_stats,
            "total": sum(hourly_stats.values())
        }
    
    except ImportError:
        return {
            "period": f"last_{hours}_hours",
            "data": {},
            "total": 0,
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取小时趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/daily")
async def get_daily_trends(
    days: int = Query(7, ge=1, le=30, description="时间范围（天）")
):
    """
    获取每日趋势
    
    返回最近N天的请求数趋势
    
    Args:
        days: 时间范围（1-30天）
    
    Returns:
        每日趋势数据
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        daily_stats = store.get_daily_stats(days)
        
        return {
            "period": f"last_{days}_days",
            "data": daily_stats,
            "total": sum(daily_stats.values())
        }
    
    except ImportError:
        return {
            "period": f"last_{days}_days",
            "data": {},
            "total": 0,
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取每日趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slow-requests")
async def get_slow_requests(
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取慢请求列表
    
    返回响应时间超过1秒的请求
    
    Args:
        limit: 返回数量
    
    Returns:
        慢请求列表
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        slow_requests = store.get_slow_requests(limit)
        
        return {
            "count": len(slow_requests),
            "requests": slow_requests
        }
    
    except ImportError:
        return {
            "count": 0,
            "requests": [],
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取慢请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
async def get_error_requests(
    limit: int = Query(20, ge=1, le=100, description="返回数量")
):
    """
    获取错误请求列表
    
    返回最近的错误请求（4xx和5xx）
    
    Args:
        limit: 返回数量
    
    Returns:
        错误请求列表
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        error_requests = store.get_error_requests(limit)
        
        return {
            "count": len(error_requests),
            "requests": error_requests
        }
    
    except ImportError:
        return {
            "count": 0,
            "requests": [],
            "message": "分析系统未启用"
        }
    except Exception as e:
        logger.error(f"获取错误请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", response_model=Dict[str, Any])
async def generate_analytics_report():
    """
    生成完整分析报告
    
    返回包含所有统计数据的综合报告
    
    Returns:
        完整分析报告
    """
    try:
        from api.analytics_middleware import generate_report
        
        report = generate_report()
        
        return report
    
    except ImportError:
        return {
            "report_time": "N/A",
            "message": "分析系统未启用",
            "statistics": {},
            "hourly_trend": {},
            "daily_trend": {},
            "slow_requests": [],
            "recent_errors": []
        }
    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analytics_health():
    """分析模块健康检查"""
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        stats = store.get_statistics()
        overview = stats.get("overview", {})
        
        return {
            "status": "healthy",
            "module": "analytics",
            "version": "1.0.0",
            "middleware_enabled": True,
            "total_requests_tracked": overview.get("total_requests", 0),
            "uptime_hours": overview.get("uptime_hours", 0),
            "features": [
                "request-tracking",
                "endpoint-statistics",
                "ip-statistics",
                "hourly-trends",
                "daily-trends",
                "slow-request-detection",
                "error-tracking",
                "report-generation"
            ]
        }
    
    except ImportError:
        return {
            "status": "disabled",
            "module": "analytics",
            "version": "1.0.0",
            "middleware_enabled": False,
            "message": "分析系统未启用"
        }


# ==================== 管理端点 ====================

@router.post("/clear")
async def clear_old_data(
    days: int = Query(7, ge=1, le=30, description="保留天数")
):
    """
    清理旧数据
    
    清理N天前的统计数据
    
    Args:
        days: 保留最近N天的数据
    
    Returns:
        操作结果
    """
    try:
        from api.analytics_middleware import get_analytics_store
        
        store = get_analytics_store()
        store.clear_old_data(days)
        
        return {
            "message": f"已清理{days}天前的数据",
            "days_retained": days
        }
    
    except ImportError:
        raise HTTPException(status_code=503, detail="分析系统未启用")
    except Exception as e:
        logger.error(f"清理数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


































