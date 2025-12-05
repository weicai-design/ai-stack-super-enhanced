"""
工作流可观测性API
提供工作流可观测性数据的查询接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.workflow_observability import (
    WorkflowObservability,
    get_workflow_observability,
)
from core.dual_loop_workflow_engine import (
    DualLoopWorkflowEngine,
    get_dual_loop_workflow_engine,
)
from core.observability_system import ObservabilitySystem

router = APIRouter(prefix="/api/workflow/observability", tags=["工作流可观测性"])


# ============ 响应模型 ============

class WorkflowTraceResponse(BaseModel):
    """工作流Trace响应"""
    workflow_id: str
    trace: Optional[Dict[str, Any]] = None
    spans: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    span_count: int = 0
    metric_count: int = 0


class WorkflowSpanResponse(BaseModel):
    """工作流Span响应"""
    span_id: str
    trace_id: str
    name: str
    type: str
    status: str
    duration: Optional[float] = None
    tags: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ============ 依赖注入 ============

def get_observability() -> WorkflowObservability:
    """获取工作流可观测性实例"""
    return get_workflow_observability()


def get_engine() -> DualLoopWorkflowEngine:
    """获取工作流引擎实例"""
    return get_dual_loop_workflow_engine()


# ============ API端点 ============

@router.get("/trace/{workflow_id}", response_model=WorkflowTraceResponse)
async def get_workflow_trace(
    workflow_id: str,
    observability: WorkflowObservability = Depends(get_observability),
) -> WorkflowTraceResponse:
    """
    获取工作流完整可观测性数据
    
    包括：
    - Trace信息
    - 所有Span
    - 相关指标
    """
    try:
        data = observability.get_workflow_observability_data(workflow_id)
        
        if not data.get("trace"):
            raise HTTPException(status_code=404, detail="工作流Trace不存在")
        
        return WorkflowTraceResponse(
            workflow_id=data["workflow_id"],
            trace=data["trace"],
            spans=data["spans"],
            metrics=data["metrics"],
            span_count=data["span_count"],
            metric_count=data["metric_count"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流Trace失败: {str(e)}")


@router.get("/spans/{workflow_id}")
async def get_workflow_spans(
    workflow_id: str,
    observability: WorkflowObservability = Depends(get_observability),
) -> List[Dict[str, Any]]:
    """获取工作流所有Span"""
    try:
        spans = observability.get_workflow_spans(workflow_id)
        return [span.to_dict() for span in spans]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流Span失败: {str(e)}")


@router.get("/metrics/{workflow_id}")
async def get_workflow_metrics(
    workflow_id: str,
    observability: WorkflowObservability = Depends(get_observability),
) -> List[Dict[str, Any]]:
    """获取工作流指标"""
    try:
        metrics = observability.get_workflow_metrics(workflow_id)
        return [
            {
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp,
                "tags": m.tags,
            }
            for m in metrics
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流指标失败: {str(e)}")


@router.get("/summary/{workflow_id}")
async def get_workflow_summary(
    workflow_id: str,
    observability: WorkflowObservability = Depends(get_observability),
    engine: DualLoopWorkflowEngine = Depends(get_engine),
) -> Dict[str, Any]:
    """
    获取工作流摘要信息
    
    包括：
    - 工作流状态
    - 可观测性数据
    - 执行历史
    """
    try:
        # 获取工作流状态
        workflow_status = await engine.get_workflow_status(workflow_id)
        
        # 获取可观测性数据
        obs_data = observability.get_workflow_observability_data(workflow_id)
        
        # 计算摘要统计
        spans = obs_data.get("spans", [])
        total_duration = sum(span.get("duration", 0) for span in spans if span.get("duration"))
        avg_span_duration = total_duration / len(spans) if spans else 0
        
        success_spans = sum(1 for span in spans if span.get("status") == "ok")
        failed_spans = len(spans) - success_spans
        
        return {
            "workflow_id": workflow_id,
            "workflow_status": workflow_status,
            "observability": {
                "trace_id": obs_data.get("trace", {}).get("trace_id") if obs_data.get("trace") else None,
                "span_count": obs_data.get("span_count", 0),
                "metric_count": obs_data.get("metric_count", 0),
                "total_duration": total_duration,
                "avg_span_duration": avg_span_duration,
                "success_spans": success_spans,
                "failed_spans": failed_spans,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流摘要失败: {str(e)}")


@router.get("/logs/{workflow_id}")
async def get_workflow_logs(
    workflow_id: str,
    limit: int = 100,
    observability: WorkflowObservability = Depends(get_observability),
) -> Dict[str, Any]:
    """
    获取工作流日志
    
    从日志文件中读取工作流相关日志
    """
    try:
        import json
        from pathlib import Path
        
        # 读取日志文件
        log_file = observability.log_file
        
        if not log_file.exists():
            return {
                "workflow_id": workflow_id,
                "logs": [],
                "total": 0,
            }
        
        logs = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if log_entry.get("workflow_id") == workflow_id:
                        logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        # 按时间戳排序（最新的在前）
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 限制数量
        logs = logs[:limit]
        
        return {
            "workflow_id": workflow_id,
            "logs": logs,
            "total": len(logs),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流日志失败: {str(e)}")


@router.get("/prometheus")
async def get_prometheus_metrics(
    observability: WorkflowObservability = Depends(get_observability),
) -> str:
    """
    获取Prometheus格式的指标
    
    用于Prometheus抓取
    """
    try:
        # 如果使用生产模式，获取聚合指标
        if hasattr(observability, '_production_impl') and observability._production_impl:
            return observability._production_impl.get_prometheus_metrics()
        else:
            # 基础模式，返回简单指标
            return "# Prometheus metrics not available in basic mode\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Prometheus指标失败: {str(e)}")


@router.get("/dashboard")
async def get_observability_dashboard(
    limit: int = 50,
    observability: WorkflowObservability = Depends(get_observability),
) -> Dict[str, Any]:
    """
    获取可观测性仪表板数据
    
    包括：
    - 最近的工作流
    - 统计信息
    - 性能指标
    """
    try:
        # 获取所有工作流Trace
        workflow_traces = observability.get_all_workflow_traces()
        
        # 按时间排序
        sorted_traces = sorted(
            workflow_traces.items(),
            key=lambda x: x[1].start_time if x[1] else 0,
            reverse=True,
        )[:limit]
        
        # 统计信息
        total_workflows = len(workflow_traces)
        active_workflows = len([t for t in workflow_traces.values() if t.end_time is None])
        completed_workflows = total_workflows - active_workflows
        
        # 计算平均时长
        completed_traces = [t for t in workflow_traces.values() if t.end_time is not None]
        avg_duration = (
            sum(t.duration for t in completed_traces if t.duration) / len(completed_traces)
            if completed_traces else 0
        )
        
        # 按状态统计
        success_count = sum(1 for t in completed_traces if t.status == "ok")
        error_count = len(completed_traces) - success_count
        
        return {
            "summary": {
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "completed_workflows": completed_workflows,
                "success_count": success_count,
                "error_count": error_count,
                "avg_duration": avg_duration,
            },
            "recent_workflows": [
                {
                    "workflow_id": workflow_id,
                    "trace_id": trace.trace_id,
                    "status": trace.status,
                    "duration": trace.duration,
                    "start_time": trace.start_time,
                    "end_time": trace.end_time,
                }
                for workflow_id, trace in sorted_traces
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可观测性仪表板失败: {str(e)}")

