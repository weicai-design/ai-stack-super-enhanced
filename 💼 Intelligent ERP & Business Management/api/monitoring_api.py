"""
T013和T014模块监控API
提供项目管理与采购管理的实时监控数据接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

# 导入监控模块
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.monitoring.project_procurement_monitor import monitor

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class AlertResponse(BaseModel):
    """告警响应模型"""
    id: str
    module: str
    metric: str
    level: str
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None


class MetricSummary(BaseModel):
    """指标摘要模型"""
    count: int
    avg: float
    min: float
    max: float
    latest: float


class MonitoringSummary(BaseModel):
    """监控摘要响应模型"""
    metrics: Dict[str, MetricSummary]
    active_alerts: List[AlertResponse]
    total_alerts: int
    resolved_alerts: int


@router.get("/summary", response_model=MonitoringSummary)
async def get_monitoring_summary():
    """获取监控摘要"""
    try:
        # 获取指标摘要
        metrics_summary = monitor.get_metrics_summary()
        
        # 获取活跃告警
        active_alerts = monitor.get_active_alerts()
        
        # 计算告警统计
        total_alerts = len(monitor.alerts)
        resolved_alerts = sum(1 for alert in monitor.alerts if alert.resolved)
        
        # 转换告警为响应模型
        alert_responses = []
        for alert in active_alerts:
            alert_responses.append(AlertResponse(
                id=alert.id,
                module=alert.module,
                metric=alert.metric.value,
                level=alert.level.value,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at
            ))
        
        # 转换指标为响应模型
        metrics = {}
        for metric_name, metric_data in metrics_summary.items():
            metrics[metric_name] = MetricSummary(**metric_data)
        
        return MonitoringSummary(
            metrics=metrics,
            active_alerts=alert_responses,
            total_alerts=total_alerts,
            resolved_alerts=resolved_alerts
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取监控摘要失败: {str(e)}")


@router.get("/alerts/active", response_model=List[AlertResponse])
async def get_active_alerts():
    """获取活跃告警"""
    try:
        active_alerts = monitor.get_active_alerts()
        
        alert_responses = []
        for alert in active_alerts:
            alert_responses.append(AlertResponse(
                id=alert.id,
                module=alert.module,
                metric=alert.metric.value,
                level=alert.level.value,
                message=alert.message,
                value=alert.value,
                threshold=alert.threshold,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at
            ))
        
        return alert_responses
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取活跃告警失败: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """解决告警"""
    try:
        monitor.resolve_alert(alert_id)
        return {"success": True, "message": f"告警 {alert_id} 已解决"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


@router.get("/metrics/{metric_name}")
async def get_metric_history(metric_name: str, limit: int = 100):
    """获取指标历史数据"""
    try:
        # 过滤指定指标的最近数据
        metric_data = [
            {
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags
            }
            for metric in monitor.metrics
            if metric.name == metric_name
        ][-limit:]
        
        return {
            "success": True,
            "metric": metric_name,
            "data": metric_data,
            "total": len(metric_data)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标历史数据失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查监控系统状态
        metrics_count = len(monitor.metrics)
        alerts_count = len(monitor.alerts)
        
        return {
            "success": True,
            "status": "healthy",
            "metrics_count": metrics_count,
            "alerts_count": alerts_count,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


# 模拟数据端点，用于测试监控系统
@router.post("/test/generate-metrics")
async def generate_test_metrics():
    """生成测试监控数据"""
    try:
        from datetime import datetime, timedelta
        
        # 生成测试数据
        test_metrics = [
            ("project_creation_rate", 8, {"method": "test"}),
            ("project_completion_rate", 0.85, {"project_id": "test"}),
            ("milestone_delay_rate", 0.15, {"project_id": "test"}),
            ("procurement_order_rate", 4, {"method": "test"}),
            ("supplier_performance", 0.92, {"supplier_id": "test"}),
            ("delivery_delay_rate", 0.12, {"order_id": "test"}),
            ("budget_overspend", 0.08, {"project_id": "test"}),
            ("api_response_time", 0.5, {"method": "test"}),
            ("error_rate", 0.02, {"method": "test"})
        ]
        
        for metric_name, value, tags in test_metrics:
            monitor.record_metric(
                monitor.MetricType(metric_name),
                value,
                tags
            )
        
        return {
            "success": True,
            "message": "测试监控数据已生成",
            "metrics_generated": len(test_metrics)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试数据失败: {str(e)}")