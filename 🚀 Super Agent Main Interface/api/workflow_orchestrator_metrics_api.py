"""
工作流编排器指标API
暴露Prometheus指标和JSON API
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from typing import Dict, Any, Optional
from datetime import datetime

from core.workflow_orchestrator import (
    get_workflow_orchestrator,
    WorkflowOrchestrator,
)

router = APIRouter(prefix="/api/workflow/orchestrator/metrics", tags=["工作流编排器指标"])


# ============ 依赖注入 ============

def get_orchestrator() -> WorkflowOrchestrator:
    """获取工作流编排器实例"""
    return get_workflow_orchestrator()


# ============ API端点 ============

@router.get("/prometheus")
async def get_prometheus_metrics(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
) -> Response:
    """
    获取 Prometheus 格式的指标
    
    用于 Prometheus 抓取
    """
    try:
        metrics_bytes = orchestrator.get_prometheus_metrics()
        return Response(
            content=metrics_bytes,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Prometheus 指标失败: {str(e)}")


@router.get("/json")
async def get_metrics_json(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    获取 JSON 格式的指标
    
    包括：
    - 工作流统计
    - 状态统计
    - 性能指标
    - 步骤统计
    """
    try:
        metrics = await orchestrator.get_metrics_json()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 JSON 指标失败: {str(e)}")


@router.get("/summary")
async def get_metrics_summary(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    获取指标摘要
    
    包括关键指标和统计信息
    """
    try:
        metrics = await orchestrator.get_metrics_json()
        
        # 提取关键指标
        summary = {
            "timestamp": metrics.get("timestamp"),
            "total_workflows": metrics.get("total_workflows", 0),
            "active_workflows": metrics.get("active_count", 0),
            "completed_workflows": metrics.get("completed_count", 0),
            "avg_duration_seconds": metrics.get("avg_duration_seconds", 0),
            "workflow_types": {
                "intelligent": metrics.get("intelligent_count", 0),
                "direct": metrics.get("direct_count", 0),
            },
            "state_distribution": metrics.get("state_counts", {}),
            "step_statistics": metrics.get("step_stats", {}),
        }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标摘要失败: {str(e)}")

