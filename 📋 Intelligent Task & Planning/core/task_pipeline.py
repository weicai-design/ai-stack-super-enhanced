"""
任务生命周期编排器
定义捕获→归类→排期→确认→执行→复盘 的管线
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .task_manager import TaskManager, TaskStatus, TaskPriority
from .task_analyzer import TaskAnalyzer
from .plan_generator import PlanGenerator
from .execution_engine import ExecutionEngine
from .task_loop_bridge import TaskLoopBridge


@dataclass
class PipelineContext:
    manager: TaskManager
    analyzer: TaskAnalyzer
    planner: PlanGenerator
    executor: ExecutionEngine
    loop_bridge: Optional[TaskLoopBridge] = None


class TaskPipeline:
    """ orchestrates lifecycle """

    def __init__(self, context: PipelineContext):
        self.ctx = context

    async def capture(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        priority_value = payload.get("priority", TaskPriority.MEDIUM.value)
        if isinstance(priority_value, TaskPriority):
            priority_enum = priority_value
        else:
            try:
                priority_enum = TaskPriority(priority_value)
            except Exception:
                priority_enum = TaskPriority.MEDIUM
        task = self.ctx.manager.create_task(
            title=payload["title"],
            description=payload.get("description", payload["title"]),
            source=payload.get("source", "user"),
            priority=priority_enum,
            tags=payload.get("tags"),
            dependencies=payload.get("dependencies"),
            metadata=payload.get("metadata"),
        )
        await self._notify_stage(task, TaskStatus.CAPTURED.value, note="capture")
        return task

    async def classify(self, task_id: int) -> Dict[str, Any]:
        task = self.ctx.manager.get_task(task_id)
        analysis = await self.ctx.analyzer.analyze_task(task)
        self.ctx.manager.update_task(task_id, {
            "analysis": analysis,
            "status": TaskStatus.CLASSIFIED.value
        })
        updated = self.ctx.manager.get_task(task_id)
        await self._notify_stage(updated, TaskStatus.CLASSIFIED.value, note="classify")
        return updated

    async def schedule(self, task_id: int, start_date: Optional[str] = None) -> Dict[str, Any]:
        task = self.ctx.manager.get_task(task_id)
        if not task:
            raise ValueError("任务不存在")
        start = start_date or datetime.now().strftime("%Y-%m-%d")
        end = (datetime.fromisoformat(start) + timedelta(days=1)).strftime("%Y-%m-%d")
        schedule = {"start": start, "end": end}
        self.ctx.manager.update_task(task_id, {
            "schedule": schedule,
            "status": TaskStatus.SCHEDULED.value
        })
        updated = self.ctx.manager.get_task(task_id)
        await self._notify_stage(updated, TaskStatus.SCHEDULED.value, note="schedule")
        return updated

    async def confirm(self, task_id: int, approver: str, note: Optional[str] = None):
        updated = self.ctx.manager.update_task(task_id, {
            "status": TaskStatus.CONFIRMED.value,
            "confirmed_by": approver,
            "confirmed_note": note,
            "needs_confirmation": False
        })
        await self._notify_stage(updated, TaskStatus.CONFIRMED.value, note=note)
        return updated

    async def execute(self, task_id: int):
        task = self.ctx.manager.get_task(task_id)
        if task.get("status") != TaskStatus.CONFIRMED.value:
            raise ValueError("任务未确认")
        executing = self.ctx.manager.update_task(task_id, {
            "status": TaskStatus.EXECUTING.value,
            "started_at": datetime.now().isoformat()
        })
        await self._notify_stage(executing, TaskStatus.EXECUTING.value)

        result = await self.ctx.executor.execute_task(executing, None)

        updated = self.ctx.manager.update_task(task_id, {
            "status": TaskStatus.REVIEW_PENDING.value,
            "execution_result": result
        })
        if self.ctx.loop_bridge:
            await self.ctx.loop_bridge.on_execution_result(updated, result)
            rag_response = await self.ctx.loop_bridge.write_back_rag(updated)
            if rag_response:
                metadata = (updated.get("metadata") or {}).copy()
                metadata["rag_writeback"] = rag_response
                updated = self.ctx.manager.update_task(task_id, {"metadata": metadata})
        await self._notify_stage(updated, TaskStatus.REVIEW_PENDING.value)
        return updated

    async def review(self, task_id: int, reviewer: str, feedback: Optional[str] = None):
        updated = self.ctx.manager.update_task(task_id, {
            "status": TaskStatus.REVIEWED.value,
            "reviewed_by": reviewer,
            "review_feedback": feedback,
            "completed_at": datetime.now().isoformat()
        })
        await self._notify_stage(updated, TaskStatus.REVIEWED.value, note=feedback)
        return updated

    def get_timeline(self, task_id: int):
        return self.ctx.manager.lifecycle_log.get(task_id, [])

    async def _notify_stage(
        self,
        task: Optional[Dict[str, Any]],
        stage: str,
        note: Optional[str] = None
    ):
        if not task or not self.ctx.loop_bridge:
            return
        try:
            await self.ctx.loop_bridge.on_stage(task, stage, note=note)
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.debug("任务闭环阶段同步失败: %s", exc)

