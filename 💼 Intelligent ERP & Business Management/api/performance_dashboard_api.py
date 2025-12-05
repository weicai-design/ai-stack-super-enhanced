"""
API性能监控仪表板 - T0006-4增强版

提供：
1. 实时性能数据展示
2. 历史趋势分析
3. 性能告警和通知
4. Prometheus指标导出
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from utils import APIResponse
from performance_monitor import get_performance_monitor, record_api_performance

router = APIRouter(prefix="/api/performance", tags=["性能监控"])


@router.get("/dashboard")
async def get_performance_dashboard(
    hours: int = Query(24, description="时间范围（小时）", ge=1, le=168)
):
    """获取性能监控仪表板数据"""
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_metrics_summary(hours=hours)
        
        # 计算API性能指标
        api_stats = {
            "total_requests": summary["api_metrics"].get("api_requests_total", {}).get("count", 0),
            "avg_response_time": summary["api_metrics"].get("api_response_time_seconds", {}).get("avg_value", 0),
            "error_rate": 0
        }
        
        if api_stats["total_requests"] > 0:
            error_count = summary["api_metrics"].get("api_errors_total", {}).get("count", 0)
            api_stats["error_rate"] = (error_count / api_stats["total_requests"]) * 100
        
        # 系统健康状态
        system_health = {
            "cpu_usage": summary["system_metrics"].get("system_cpu_usage", 0),
            "memory_usage": summary["system_metrics"].get("system_memory_usage", 0),
            "disk_usage": summary["system_metrics"].get("system_disk_usage", 0),
            "status": "healthy"
        }
        
        # 健康状态判断
        if system_health["cpu_usage"] > 80 or system_health["memory_usage"] > 85:
            system_health["status"] = "warning"
        elif system_health["cpu_usage"] > 90 or system_health["memory_usage"] > 95:
            system_health["status"] = "critical"
        
        # 性能评分
        performance_score = _calculate_performance_score(api_stats, system_health)
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "performance_score": performance_score,
            "api_stats": api_stats,
            "system_health": system_health,
            "top_endpoints": _get_top_endpoints(summary),
            "alerts": _get_active_alerts(api_stats, system_health)
        }
        
        return APIResponse.success(
            data=dashboard_data,
            message="性能监控仪表板数据获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能仪表板失败: {str(e)}")


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """导出Prometheus格式指标"""
    try:
        monitor = get_performance_monitor()
        prometheus_data = monitor.export_prometheus_metrics()
        
        return PlainTextResponse(
            content=prometheus_data,
            media_type="text/plain; version=0.0.4"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Prometheus指标失败: {str(e)}")


@router.get("/metrics/summary")
async def get_metrics_summary(
    hours: int = Query(24, description="时间范围（小时）", ge=1, le=168)
):
    """获取指标摘要"""
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_metrics_summary(hours=hours)
        
        return APIResponse.success(
            data=summary,
            message="指标摘要数据获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标摘要失败: {str(e)}")


@router.get("/alerts")
async def get_performance_alerts():
    """获取性能告警"""
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_metrics_summary(hours=1)  # 最近1小时数据
        
        alerts = []
        
        # 检查API性能告警
        api_stats = summary["api_metrics"]
        if "api_response_time_seconds" in api_stats:
            avg_response_time = api_stats["api_response_time_seconds"]["avg_value"]
            if avg_response_time > 1.0:  # 超过1秒
                alerts.append({
                    "type": "api_performance",
                    "level": "warning",
                    "message": f"API平均响应时间过高: {avg_response_time:.2f}秒",
                    "metric": "api_response_time_seconds",
                    "value": avg_response_time,
                    "threshold": 1.0
                })
            elif avg_response_time > 2.0:  # 超过2秒
                alerts.append({
                    "type": "api_performance",
                    "level": "critical",
                    "message": f"API平均响应时间严重过高: {avg_response_time:.2f}秒",
                    "metric": "api_response_time_seconds",
                    "value": avg_response_time,
                    "threshold": 2.0
                })
        
        # 检查错误率告警
        total_requests = api_stats.get("api_requests_total", {}).get("count", 0)
        error_count = api_stats.get("api_errors_total", {}).get("count", 0)
        
        if total_requests > 0:
            error_rate = (error_count / total_requests) * 100
            if error_rate > 5.0:  # 错误率超过5%
                alerts.append({
                    "type": "api_errors",
                    "level": "warning",
                    "message": f"API错误率过高: {error_rate:.1f}%",
                    "metric": "api_error_rate",
                    "value": error_rate,
                    "threshold": 5.0
                })
            elif error_rate > 10.0:  # 错误率超过10%
                alerts.append({
                    "type": "api_errors",
                    "level": "critical",
                    "message": f"API错误率严重过高: {error_rate:.1f}%",
                    "metric": "api_error_rate",
                    "value": error_rate,
                    "threshold": 10.0
                })
        
        # 检查系统资源告警
        system_metrics = summary["system_metrics"]
        cpu_usage = system_metrics.get("system_cpu_usage", 0)
        memory_usage = system_metrics.get("system_memory_usage", 0)
        
        if cpu_usage > 80:
            alerts.append({
                "type": "system_resources",
                "level": "warning",
                "message": f"CPU使用率过高: {cpu_usage:.1f}%",
                "metric": "system_cpu_usage",
                "value": cpu_usage,
                "threshold": 80.0
            })
        
        if memory_usage > 85:
            alerts.append({
                "type": "system_resources",
                "level": "warning",
                "message": f"内存使用率过高: {memory_usage:.1f}%",
                "metric": "system_memory_usage",
                "value": memory_usage,
                "threshold": 85.0
            })
        
        return APIResponse.success(
            data={
                "timestamp": datetime.now().isoformat(),
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a["level"] == "critical"]),
                "warning_alerts": len([a for a in alerts if a["level"] == "warning"])
            },
            message="性能告警数据获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能告警失败: {str(e)}")


@router.get("/endpoints/top")
async def get_top_endpoints(
    hours: int = Query(24, description="时间范围（小时）", ge=1, le=168),
    limit: int = Query(10, description="返回数量", ge=1, le=50)
):
    """获取热门API端点"""
    try:
        monitor = get_performance_monitor()
        summary = monitor.get_metrics_summary(hours=hours)
        
        # 按请求量排序端点
        endpoint_stats = {}
        for key, metrics in summary["api_metrics"].items():
            if key.startswith("api_requests_total"):
                # 解析端点信息
                endpoint_info = _parse_endpoint_from_key(key)
                if endpoint_info:
                    endpoint_name = endpoint_info["endpoint"]
                    if endpoint_name not in endpoint_stats:
                        endpoint_stats[endpoint_name] = {
                            "endpoint": endpoint_name,
                            "request_count": 0,
                            "avg_response_time": 0,
                            "error_count": 0
                        }
                    
                    endpoint_stats[endpoint_name]["request_count"] += metrics["count"]
        
        # 添加响应时间和错误信息
        for key, metrics in summary["api_metrics"].items():
            if key.startswith("api_response_time_seconds"):
                endpoint_info = _parse_endpoint_from_key(key)
                if endpoint_info and endpoint_info["endpoint"] in endpoint_stats:
                    endpoint_stats[endpoint_info["endpoint"]]["avg_response_time"] = metrics["avg_value"]
            
            elif key.startswith("api_errors_total"):
                endpoint_info = _parse_endpoint_from_key(key)
                if endpoint_info and endpoint_info["endpoint"] in endpoint_stats:
                    endpoint_stats[endpoint_info["endpoint"]]["error_count"] = metrics["count"]
        
        # 排序并限制数量
        top_endpoints = sorted(
            endpoint_stats.values(),
            key=lambda x: x["request_count"],
            reverse=True
        )[:limit]
        
        # 计算错误率
        for endpoint in top_endpoints:
            if endpoint["request_count"] > 0:
                endpoint["error_rate"] = (endpoint["error_count"] / endpoint["request_count"]) * 100
            else:
                endpoint["error_rate"] = 0
        
        return APIResponse.success(
            data={
                "timestamp": datetime.now().isoformat(),
                "time_range_hours": hours,
                "top_endpoints": top_endpoints
            },
            message="热门API端点数据获取成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门端点失败: {str(e)}")


def _calculate_performance_score(api_stats: Dict[str, Any], system_health: Dict[str, Any]) -> float:
    """计算性能评分（0-100）"""
    score = 100.0
    
    # API响应时间扣分（超过500ms开始扣分）
    avg_response_time = api_stats.get("avg_response_time", 0)
    if avg_response_time > 0.5:
        time_penalty = min(20, (avg_response_time - 0.5) * 10)  # 最多扣20分
        score -= time_penalty
    
    # 错误率扣分
    error_rate = api_stats.get("error_rate", 0)
    if error_rate > 0:
        error_penalty = min(30, error_rate * 2)  # 最多扣30分
        score -= error_penalty
    
    # 系统资源扣分
    cpu_usage = system_health.get("cpu_usage", 0)
    if cpu_usage > 80:
        cpu_penalty = min(15, (cpu_usage - 80) * 0.5)  # 最多扣15分
        score -= cpu_penalty
    
    memory_usage = system_health.get("memory_usage", 0)
    if memory_usage > 85:
        memory_penalty = min(15, (memory_usage - 85) * 0.5)  # 最多扣15分
        score -= memory_penalty
    
    return max(0, min(100, score))


def _get_top_endpoints(summary: Dict[str, Any]) -> list:
    """获取热门端点"""
    endpoint_stats = {}
    
    for key, metrics in summary["api_metrics"].items():
        if key.startswith("api_requests_total"):
            endpoint_info = self._parse_endpoint_from_key(key)
            if endpoint_info:
                endpoint_name = endpoint_info["endpoint"]
                if endpoint_name not in endpoint_stats:
                    endpoint_stats[endpoint_name] = {"request_count": 0}
                endpoint_stats[endpoint_name]["request_count"] += metrics["count"]
    
    return sorted(
        [{"endpoint": k, "count": v["request_count"]} for k, v in endpoint_stats.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]


def _get_active_alerts(api_stats: Dict[str, Any], system_health: Dict[str, Any]) -> list:
    """获取活跃告警"""
    alerts = []
    
    # API性能告警
    if api_stats.get("avg_response_time", 0) > 1.0:
        alerts.append({
            "type": "performance",
            "level": "warning",
            "message": f"API响应时间偏高: {api_stats['avg_response_time']:.2f}秒"
        })
    
    if api_stats.get("error_rate", 0) > 5.0:
        alerts.append({
            "type": "errors",
            "level": "warning",
            "message": f"API错误率偏高: {api_stats['error_rate']:.1f}%"
        })
    
    # 系统资源告警
    if system_health.get("cpu_usage", 0) > 80:
        alerts.append({
            "type": "system",
            "level": "warning",
            "message": f"CPU使用率偏高: {system_health['cpu_usage']:.1f}%"
        })
    
    if system_health.get("memory_usage", 0) > 85:
        alerts.append({
            "type": "system",
            "level": "warning",
            "message": f"内存使用率偏高: {system_health['memory_usage']:.1f}%"
        })
    
    return alerts


def _parse_endpoint_from_key(key: str) -> Optional[Dict[str, str]]:
    """从指标键解析端点信息"""
    try:
        # 解析格式: api_requests_total{"endpoint": "/api/test", "method": "GET", ...}
        if '{"' in key:
            labels_part = key.split('{"', 1)[1].rsplit('"}', 1)[0]
            labels = json.loads('{"' + labels_part + '"}')
            return labels
    except:
        pass
    return None