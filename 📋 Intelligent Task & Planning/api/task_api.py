"""
智能工作计划与任务API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from ..core.task_manager import TaskManager, TaskPriority
from ..core.task_extractor import TaskExtractor
from ..core.plan_generator import PlanGenerator
from ..core.execution_engine import ExecutionEngine
from ..core.super_agent_integration import SuperAgentIntegration
from ..core.task_analyzer import TaskAnalyzer

router = APIRouter(prefix="/api/task-planning", tags=["Task Planning"])

# 初始化服务
super_agent_integration = SuperAgentIntegration()
task_analyzer = TaskAnalyzer()
task_manager = TaskManager()
task_extractor = TaskExtractor(super_agent_integration)
plan_generator = PlanGenerator(task_analyzer)
execution_engine = ExecutionEngine(super_agent_integration=super_agent_integration)


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    title: str
    description: str
    source: str = "user"
    priority: int = 2
    tags: Optional[List[str]] = None
    dependencies: Optional[List[int]] = None


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    """创建任务"""
    priority = TaskPriority(request.priority) if request.priority in [1,2,3,4] else TaskPriority.MEDIUM
    task = task_manager.create_task(
        title=request.title,
        description=request.description,
        source=request.source,
        priority=priority,
        tags=request.tags,
        dependencies=request.dependencies
    )
    return {"success": True, "task": task}


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    source: Optional[str] = None,
    priority: Optional[int] = None,
    needs_confirmation: Optional[bool] = None
):
    """获取任务列表"""
    tasks = task_manager.get_tasks(
        status=status,
        source=source,
        priority=priority,
        needs_confirmation=needs_confirmation
    )
    return {"tasks": tasks, "total": len(tasks)}


@router.post("/tasks/extract")
async def extract_tasks(text: Optional[str] = None, memos: Optional[List[Dict]] = None):
    """提取任务（与超级Agent集成）"""
    extracted = []
    
    if text:
        extracted.extend(task_extractor.extract_from_text(text))
    
    if memos:
        # 使用异步方法
        memo_tasks = await task_extractor.extract_from_memos(memos)
        extracted.extend(memo_tasks)
    
    # 创建任务
    created_tasks = []
    for task_data in extracted:
        classified = task_extractor.classify_task(task_data.get("content", ""))
        task = task_manager.create_task(
            title=task_data.get("content", ""),
            description=task_data.get("content", ""),
            source=task_data.get("source", "agent"),
            priority=TaskPriority(classified.get("priority", 2)),
            tags=classified.get("tags", [])
        )
        created_tasks.append(task)
    
    # 发送给超级Agent确认
    if super_agent_integration and created_tasks:
        await super_agent_integration.send_tasks_for_confirmation(created_tasks)
    
    return {"tasks": created_tasks, "total": len(created_tasks)}


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int, module_executor: Optional[Any] = None):
    """
    执行任务（与超级Agent集成）
    
    支持通过模块执行器调用各模块功能
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.get("status") != "confirmed":
        raise HTTPException(status_code=400, detail="任务未确认")
    
    # 分析任务（如果未分析）
    if not task.get("analysis") and task_analyzer:
        task["analysis"] = await task_analyzer.analyze_task(task)
        task_manager.update_task(task_id, {"analysis": task["analysis"]})
    
    # 执行任务
    result = await execution_engine.execute_task(task, module_executor)
    task_manager.update_task(task_id, result.get("task", {}))
    
    return result


@router.get("/tasks/{task_id}/analyze")
async def analyze_task(task_id: int):
    """分析任务"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    analysis = await task_analyzer.analyze_task(task)
    task_manager.update_task(task_id, {"analysis": analysis})
    
    return {"success": True, "analysis": analysis}


@router.get("/plans/generate")
async def generate_plan(start_date: Optional[str] = None, duration_days: int = 7):
    """生成工作计划"""
    tasks = task_manager.get_tasks(status="confirmed")
    plan = plan_generator.generate_plan(tasks, start_date, duration_days)
    return {"success": True, "plan": plan}


@router.get("/statistics")
async def get_statistics():
    """获取统计信息"""
    stats = task_manager.get_statistics()
    return stats

