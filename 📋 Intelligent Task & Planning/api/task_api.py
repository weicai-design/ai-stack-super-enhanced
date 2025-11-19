"""
智能工作计划与任务API
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.task_manager import TaskManager, TaskPriority, TaskStatus
from core.task_extractor import TaskExtractor
from core.plan_generator import PlanGenerator
from core.execution_engine import ExecutionEngine
from core.super_agent_integration import SuperAgentIntegration
from core.task_analyzer import TaskAnalyzer
from core.task_pipeline import TaskPipeline, PipelineContext
from core.task_loop_bridge import TaskLoopBridge

router = APIRouter(prefix="/api/task-planning", tags=["Task Planning"])

# 初始化服务
super_agent_integration = SuperAgentIntegration()
task_analyzer = TaskAnalyzer()
task_manager = TaskManager()
task_extractor = TaskExtractor(super_agent_integration)
plan_generator = PlanGenerator(task_analyzer)
execution_engine = ExecutionEngine(super_agent_integration=super_agent_integration)
task_loop_bridge = TaskLoopBridge(
    super_agent_integration=super_agent_integration,
    rag_api_url=os.getenv("RAG_API_URL", "http://127.0.0.1:8001"),
)
pipeline = TaskPipeline(PipelineContext(
    manager=task_manager,
    analyzer=task_analyzer,
    planner=plan_generator,
    executor=execution_engine,
    loop_bridge=task_loop_bridge
))


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    title: str
    description: str
    source: str = "user"
    priority: int = 2
    tags: Optional[List[str]] = None
    dependencies: Optional[List[int]] = None
    metadata: Optional[Dict[str, Any]] = None


class LifecycleActionRequest(BaseModel):
    operator: str
    note: Optional[str] = None


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    """创建任务"""
    payload = request.dict()
    payload["priority"] = request.priority
    task = await pipeline.capture(payload)
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
    
    memo_tasks = await task_extractor.extract_from_memos(memos)
    extracted.extend(memo_tasks)
    
    # 创建任务
    created_tasks = []
    for task_data in extracted:
        classified = task_extractor.classify_task(task_data.get("content", ""))
        metadata = {
            "origin": task_data,
            "memo_id": task_data.get("source_id"),
            "extraction_confidence": task_data.get("confidence"),
        }
        payload = {
            "title": task_data.get("content", ""),
            "description": task_data.get("content", ""),
            "source": task_data.get("source", "agent"),
            "priority": classified.get("priority", TaskPriority.MEDIUM.value),
            "tags": classified.get("tags", []),
            "metadata": metadata,
        }
        task = await pipeline.capture(payload)
        created_tasks.append(task)
        if task_loop_bridge and task_data.get("source") == "memo":
            memo_meta = {
                "id": task_data.get("source_id"),
                "title": task_data.get("content", "")[:30],
                "importance": task_data.get("importance", 3),
                "tags": task_data.get("tags", []),
            }
            await task_loop_bridge.record_memo_link(task, memo_meta)
    
    # 发送给超级Agent确认
    if super_agent_integration and created_tasks:
        asyncio.create_task(
            super_agent_integration.send_tasks_for_confirmation(created_tasks)
        )
    
    return {"tasks": created_tasks, "total": len(created_tasks)}


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int, module_executor: Optional[Any] = None):
    """
    执行任务（与超级Agent集成）
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.get("status") != TaskStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="任务未确认")

    try:
        updated = await pipeline.execute(task_id)
        return {"success": True, "task": updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tasks/{task_id}/analyze")
async def analyze_task(task_id: int):
    """分析任务"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    analysis = await task_analyzer.analyze_task(task)
    task_manager.update_task(task_id, {"analysis": analysis})
    
    return {"success": True, "analysis": analysis}


@router.post("/tasks/{task_id}/lifecycle/confirm")
async def confirm_task(task_id: int, payload: LifecycleActionRequest):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") not in [TaskStatus.SCHEDULED.value, TaskStatus.CLASSIFIED.value]:
        raise HTTPException(status_code=400, detail="当前状态无法确认")
    updated = await pipeline.confirm(task_id, payload.operator, payload.note)
    return {"success": True, "task": updated}


@router.post("/tasks/{task_id}/lifecycle/review")
async def review_task(task_id: int, payload: LifecycleActionRequest):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.get("status") != TaskStatus.REVIEW_PENDING.value:
        raise HTTPException(status_code=400, detail="任务未等待复盘")
    updated = await pipeline.review(task_id, payload.operator, payload.note)
    return {"success": True, "task": updated}


@router.get("/tasks/{task_id}/timeline")
async def get_task_timeline(task_id: int):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    timeline = pipeline.get_timeline(task_id)
    return {"success": True, "timeline": timeline}


@router.get("/plans/generate")
async def generate_plan(start_date: Optional[str] = None, duration_days: int = 7):
    """生成工作计划"""
    tasks = task_manager.get_tasks(status=TaskStatus.CONFIRMED.value)
    plan = await plan_generator.generate_plan(tasks, start_date, duration_days)
    return {"success": True, "plan": plan}


@router.get("/statistics")
async def get_statistics():
    """获取统计信息"""
    stats = task_manager.get_statistics()
    return stats

