"""
任务编排器
负责把任务规划系统、模块执行结果与学习事件总线连接起来
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .learning_events import LearningEventBus, LearningEventType


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class OrchestratedTask:
    task_id: str
    title: str
    description: str
    priority: str = "medium"
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


class TaskOrchestrator:
    """
    统一任务编排

    - 作为 TaskPlanning 与模块执行的粘合层
    - 将任务状态变化发送到事件总线
    - 为自我学习系统提供任务上下文
    """

    def __init__(
        self,
        task_planning,
        event_bus: LearningEventBus,
    ):
        self.task_planning = task_planning
        self.event_bus = event_bus
        self.tasks: Dict[str, OrchestratedTask] = {}

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [task.__dict__ for task in self.tasks.values()]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        return task.__dict__ if task else None

    async def register_task(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        task_id = f"task_{uuid4()}"
        task = OrchestratedTask(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            source=source,
            metadata=metadata or {},
            dependencies=dependencies or [],
        )
        self.tasks[task_id] = task

        await self.event_bus.publish_event(
            LearningEventType.TASK_CREATED,
            source="task_orchestrator",
            severity="info",
            payload={"task": task.__dict__},
        )
        return task.__dict__

    async def register_tasks_from_plan(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        registered = []
        for task in tasks:
            payload = await self.register_task(
                title=task.get("title", "未命名任务"),
                description=task.get("description", ""),
                priority=task.get("priority", "medium"),
                source=task.get("source", "plan"),
                metadata={"plan_id": task.get("plan_id"), "estimated_duration": task.get("estimated_duration")},
                dependencies=task.get("dependencies", []),
            )
            registered.append(payload)
        return registered

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        updates: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.status = status
        task.updated_at = datetime.now().isoformat()
        if updates:
            task.metadata.update(updates)

        await self.event_bus.publish_event(
            LearningEventType.TASK_UPDATED,
            source="task_orchestrator",
            severity="warning" if status == TaskStatus.BLOCKED else "info",
            payload={"task": task.__dict__},
        )
        return task.__dict__

    async def mark_task_blocked(self, task_id: str, reason: str) -> Optional[Dict[str, Any]]:
        return await self.update_task_status(
            task_id,
            TaskStatus.BLOCKED,
            updates={"blocked_reason": reason},
        )

    async def attach_module_result(
        self,
        task_id: str,
        module: str,
        result: Any,
        success: bool = True,
    ) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        if not task:
            return None

        history = task.metadata.setdefault("execution_history", [])
        history.append(
            {
                "module": module,
                "success": success,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }
        )
        task.updated_at = datetime.now().isoformat()

        await self.event_bus.publish_event(
            LearningEventType.WORKFLOW_ANOMALY if not success else LearningEventType.TASK_UPDATED,
            source="task_orchestrator",
            severity="medium" if not success else "info",
            payload={
                "task_id": task_id,
                "module": module,
                "success": success,
                "result": result,
            },
        )
        return task.__dict__





