"""
运营管理API
Operations Management API

完整的运营管理API端点

版本: v1.0.0
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from .models import Workflow, BusinessProcess, Issue
from .manager import operations_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/operations", tags=["Operations Management"])


# ==================== 请求模型 ====================

class UpdateStageRequest(BaseModel):
    """更新阶段请求"""
    stage: str = Field(..., description="业务阶段")
    data: Dict[str, Any] = Field(..., description="阶段数据")


class ResolveIssueRequest(BaseModel):
    """解决问题请求"""
    resolution: str = Field(..., description="解决方案")


# ==================== API端点 ====================

@router.get("/health")
async def operations_health():
    """运营模块健康检查"""
    return {
        "status": "healthy",
        "module": "operations",
        "version": "1.0.0",
        "features": [
            "workflow_management",
            "process_tracking",
            "issue_collection",
            "closed_loop_monitoring",
            "analytics_dashboard"
        ]
    }


@router.post("/workflows")
async def create_workflow(workflow: Workflow, tenant=Depends(require_tenant)):
    """创建工作流定义"""
    result = operations_manager.create_workflow(tenant.id, workflow)
    return result.model_dump()


@router.get("/workflows")
async def list_workflows(tenant=Depends(require_tenant)):
    """获取工作流列表"""
    workflows = operations_manager.get_workflows(tenant.id)
    return [w.model_dump() for w in workflows]


@router.post("/processes")
async def start_process(process: BusinessProcess, tenant=Depends(require_tenant)):
    """启动业务流程"""
    result = operations_manager.start_process(tenant.id, process)
    return result.model_dump()


@router.get("/processes")
async def list_processes(
    tenant=Depends(require_tenant),
    status: Optional[str] = Query(None, description="按状态过滤")
):
    """查询业务流程列表"""
    filters = {"status": status} if status else None
    processes = operations_manager.get_processes(tenant.id, filters)
    return [p.model_dump() for p in processes]


@router.get("/processes/{process_id}")
async def get_process(process_id: str, tenant=Depends(require_tenant)):
    """获取业务流程详情"""
    process = operations_manager.get_process(tenant.id, process_id)
    if not process:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="流程不存在")
    return process.model_dump()


@router.get("/processes/{process_id}/progress")
async def get_process_progress(process_id: str, tenant=Depends(require_tenant)):
    """获取流程进度"""
    progress = operations_manager.get_process_progress(tenant.id, process_id)
    if not progress:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="流程不存在")
    return progress


@router.post("/processes/{process_id}/update-stage")
async def update_stage(
    process_id: str,
    request: UpdateStageRequest,
    tenant=Depends(require_tenant)
):
    """更新流程阶段数据"""
    result = operations_manager.update_process_stage(
        tenant.id, process_id, request.stage, request.data
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="流程不存在")
    return result.model_dump()


@router.post("/issues")
async def report_issue(issue: Issue, tenant=Depends(require_tenant)):
    """报告问题"""
    result = operations_manager.report_issue(tenant.id, issue)
    return result.model_dump()


@router.get("/issues")
async def list_issues(
    tenant=Depends(require_tenant),
    status: Optional[str] = Query(None, description="按状态过滤")
):
    """获取问题列表"""
    issues = operations_manager.get_issues(tenant.id, status)
    return [i.model_dump() for i in issues]


@router.post("/issues/{issue_id}/resolve")
async def resolve_issue(
    issue_id: str,
    request: ResolveIssueRequest,
    tenant=Depends(require_tenant)
):
    """解决问题"""
    result = operations_manager.resolve_issue(tenant.id, issue_id, request.resolution)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="问题不存在")
    return result.model_dump()


@router.get("/dashboard")
async def get_dashboard(tenant=Depends(require_tenant)):
    """获取运营看板"""
    dashboard = operations_manager.get_dashboard(tenant.id)
    return dashboard.model_dump()


@router.get("/statistics")
async def get_statistics(
    tenant=Depends(require_tenant),
    period: str = Query("month", description="统计周期")
):
    """获取统计分析"""
    stats = operations_manager.get_statistics(tenant.id, period)
    return stats


@router.get("/trend")
async def get_trend(
    tenant=Depends(require_tenant),
    days: int = Query(30, description="天数")
):
    """获取趋势数据"""
    trend = operations_manager.get_trend_data(tenant.id, days)
    return trend


@router.get("/anomalies")
async def detect_anomalies(tenant=Depends(require_tenant)):
    """检测异常流程"""
    anomalies = operations_manager.detect_anomalies(tenant.id)
    return anomalies


@router.get("/closed-loop")
async def check_closed_loop(tenant=Depends(require_tenant)):
    """检查闭环管理状态"""
    status = operations_manager.check_closed_loop(tenant.id)
    return status

