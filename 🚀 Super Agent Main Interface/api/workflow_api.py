"""
双线闭环工作流API
提供工作流执行的HTTP接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dual_loop_workflow_engine import (
    DualLoopWorkflowEngine,
    get_dual_loop_workflow_engine,
    WorkflowType,
    WorkflowExecutionResult,
)
from core.workflow_orchestrator import get_workflow_orchestrator
from core.rag_service_adapter import RAGServiceAdapter
from core.expert_router import ExpertRouter
from core.module_executor import ModuleExecutor

router = APIRouter(prefix="/api/workflow", tags=["工作流"])


# ============ 请求模型 ============

class IntelligentWorkflowRequest(BaseModel):
    """智能线工作流请求"""
    user_input: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    trace_id: Optional[str] = Field(None, description="Trace ID（可选）")
    parent_span_id: Optional[str] = Field(None, description="父 Span ID（可选）")


class DirectWorkflowRequest(BaseModel):
    """直接操作线工作流请求"""
    user_input: str = Field(..., description="用户输入")
    target_module: str = Field(..., description="目标模块")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    trace_id: Optional[str] = Field(None, description="Trace ID（可选）")
    parent_span_id: Optional[str] = Field(None, description="父 Span ID（可选）")


# ============ 响应模型 ============

class WorkflowStepResponse(BaseModel):
    """工作流步骤响应"""
    step_type: str
    success: bool
    duration: float
    error: Optional[str] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    workflow_type: str
    success: bool
    response: str
    total_duration: float
    steps: List[WorkflowStepResponse]
    trace_id: Optional[str] = None
    error: Optional[str] = None


# ============ 依赖注入 ============

def get_workflow_engine() -> DualLoopWorkflowEngine:
    """获取工作流引擎实例"""
    orchestrator = get_workflow_orchestrator()
    rag_service = RAGServiceAdapter()
    expert_router = ExpertRouter()
    module_executor = ModuleExecutor()
    
    return get_dual_loop_workflow_engine(
        workflow_orchestrator=orchestrator,
        rag_service=rag_service,
        expert_router=expert_router,
        module_executor=module_executor,
    )


# ============ API端点 ============

@router.post("/intelligent", response_model=WorkflowResponse)
async def execute_intelligent_workflow(
    request: IntelligentWorkflowRequest,
    engine: DualLoopWorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    """
    执行智能线工作流（RAG→专家→模块→专家→RAG）
    
    完整流程：
    1. RAG检索（理解需求）
    2. 专家路由（选择专家和模块）
    3. 模块执行（执行具体功能）
    4. 专家后处理（专家系统处理结果）
    5. RAG检索（整合历史经验和最佳实践）
    6. 响应生成（综合所有信息生成最终响应）
    """
    try:
        result = await engine.execute_intelligent_workflow(
            user_input=request.user_input,
            context=request.context,
            trace_id=request.trace_id,
            parent_span_id=request.parent_span_id,
        )
        
        return WorkflowResponse(
            workflow_id=result.workflow_id,
            workflow_type=result.workflow_type.value,
            success=result.success,
            response=result.response,
            total_duration=result.total_duration,
            steps=[
                WorkflowStepResponse(
                    step_type=step.step_type.value,
                    success=step.success,
                    duration=step.duration,
                    error=step.error,
                )
                for step in result.steps
            ],
            trace_id=result.trace_id,
            error=result.error,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.post("/direct", response_model=WorkflowResponse)
async def execute_direct_workflow(
    request: DirectWorkflowRequest,
    engine: DualLoopWorkflowEngine = Depends(get_workflow_engine),
) -> WorkflowResponse:
    """
    执行直接操作线工作流（跳过RAG和专家路由）
    
    流程：
    1. 模块执行
    2. 响应生成
    """
    try:
        result = await engine.execute_direct_workflow(
            user_input=request.user_input,
            target_module=request.target_module,
            context=request.context,
            trace_id=request.trace_id,
            parent_span_id=request.parent_span_id,
        )
        
        return WorkflowResponse(
            workflow_id=result.workflow_id,
            workflow_type=result.workflow_type.value,
            success=result.success,
            response=result.response,
            total_duration=result.total_duration,
            steps=[
                WorkflowStepResponse(
                    step_type=step.step_type.value,
                    success=step.success,
                    duration=step.duration,
                    error=step.error,
                )
                for step in result.steps
            ],
            trace_id=result.trace_id,
            error=result.error,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@router.get("/status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    engine: DualLoopWorkflowEngine = Depends(get_workflow_engine),
) -> Dict[str, Any]:
    """获取工作流状态"""
    try:
        status = await engine.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流状态失败: {str(e)}")


@router.get("/history")
async def get_execution_history(
    workflow_id: Optional[str] = None,
    limit: int = 100,
    engine: DualLoopWorkflowEngine = Depends(get_workflow_engine),
) -> List[Dict[str, Any]]:
    """获取执行历史"""
    try:
        results = await engine.get_execution_history(
            workflow_id=workflow_id,
            limit=limit,
        )
        
        return [
            {
                "workflow_id": r.workflow_id,
                "workflow_type": r.workflow_type.value,
                "success": r.success,
                "response": r.response[:200] if r.response else "",  # 限制长度
                "total_duration": r.total_duration,
                "steps_count": len(r.steps),
                "trace_id": r.trace_id,
                "error": r.error,
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行历史失败: {str(e)}")


@router.get("/metrics")
async def get_workflow_metrics(
    engine: DualLoopWorkflowEngine = Depends(get_workflow_engine),
) -> Dict[str, Any]:
    """获取工作流指标"""
    try:
        orchestrator = engine.orchestrator
        metrics = await orchestrator.get_metrics_json()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流指标失败: {str(e)}")


@router.get("/status")
async def get_workflow_status_summary(
    workflow_type: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    获取工作流状态摘要（用于前端可视化）
    
    返回格式：
    {
        "success": true,
        "data": {
            "statistics": {...},
            "intelligent_workflows": [...],
            "direct_workflows": [...],
            "active_workflows": [...],
            "type_state_counts": {...}
        }
    }
    """
    try:
        from core.workflow_orchestrator import (
            get_workflow_orchestrator,
            WorkflowType,
            WorkflowState,
        )
        
        orchestrator = get_workflow_orchestrator()
        
        # 获取指标
        metrics = await orchestrator.get_metrics_json()
        
        # 获取工作流列表
        wf_type = WorkflowType(workflow_type) if workflow_type else None
        wf_state = WorkflowState(state) if state else None
        
        all_workflows = await orchestrator.list_workflows(
            workflow_type=wf_type,
            state=wf_state,
            limit=limit
        )
        
        # 分离智能线和直接操作线（活跃的）
        intelligent_workflows = [
            wf for wf in all_workflows
            if wf.get("workflow_type") == "intelligent"
            and wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        direct_workflows = [
            wf for wf in all_workflows
            if wf.get("workflow_type") == "direct"
            and wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        # 所有活跃工作流
        active_workflows = [
            wf for wf in all_workflows
            if wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        return {
            "success": True,
            "data": {
                "statistics": {
                    "total_workflows": metrics.get("total_workflows", 0),
                    "intelligent_count": metrics.get("intelligent_count", 0),
                    "direct_count": metrics.get("direct_count", 0),
                    "active_count": metrics.get("active_count", 0),
                    "completed_count": metrics.get("completed_count", 0),
                    "avg_duration_seconds": metrics.get("avg_duration_seconds", 0),
                },
                "intelligent_workflows": intelligent_workflows,
                "direct_workflows": direct_workflows,
                "active_workflows": active_workflows,
                "type_state_counts": metrics.get("type_state_counts", {}),
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "statistics": {},
                "intelligent_workflows": [],
                "direct_workflows": [],
                "active_workflows": [],
                "type_state_counts": {},
            }
        }

