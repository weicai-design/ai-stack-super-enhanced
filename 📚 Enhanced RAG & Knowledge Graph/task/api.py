"""任务管理API"""
import logging
from fastapi import APIRouter, Depends
from .models import Task, TaskPlan
from .manager import task_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Task Management"])

@router.get("/health")
async def task_health():
    return {"status": "healthy", "module": "task", "version": "1.0.0"}

@router.post("/")
async def create_task(task: Task, tenant=Depends(require_tenant)):
    result = task_manager.create_task(tenant.id, task)
    return result.model_dump()

@router.post("/plans")
async def create_plan(plan: TaskPlan, tenant=Depends(require_tenant)):
    result = task_manager.create_plan(tenant.id, plan)
    return result.model_dump()

















