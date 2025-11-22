#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务生命周期管理器
P2-303: 实现真实任务生命周期管理
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"  # 待执行
    PLANNING = "planning"  # 规划中
    READY = "ready"  # 就绪
    RUNNING = "running"  # 执行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消
    RETRYING = "retrying"  # 重试中


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskLifecycleEvent:
    """任务生命周期事件"""
    event_id: str
    task_id: str
    event_type: str  # created/started/paused/resumed/completed/failed/cancelled
    status: TaskStatus
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskLifecycle:
    """任务生命周期"""
    task_id: str
    task_name: str
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    progress: float = 0.0
    current_step: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0
    events: List[TaskLifecycleEvent] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: Optional[float] = None
    actual_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        data["events"] = [e.to_dict() for e in self.events]
        return data


class TaskLifecycleManager:
    """
    任务生命周期管理器
    
    功能：
    1. 管理任务完整生命周期
    2. 记录所有生命周期事件
    3. 支持任务状态转换
    4. 提供生命周期查询
    """
    
    def __init__(self):
        self.tasks: Dict[str, TaskLifecycle] = {}
        self.event_history: List[TaskLifecycleEvent] = []
        
        logger.info("任务生命周期管理器初始化完成")
    
    def create_task(
        self,
        task_name: str,
        task_type: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskLifecycle:
        """
        创建任务
        
        Args:
            task_name: 任务名称
            task_type: 任务类型
            priority: 优先级
            metadata: 元数据
            
        Returns:
            任务生命周期对象
        """
        task_id = f"task_{uuid4()}"
        now = datetime.utcnow().isoformat() + "Z"
        
        lifecycle = TaskLifecycle(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=now,
            metadata=metadata or {},
        )
        
        # 记录创建事件
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="created",
            status=TaskStatus.PENDING,
            timestamp=now,
            metadata={"task_name": task_name, "task_type": task_type},
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        self.tasks[task_id] = lifecycle
        
        logger.info(f"创建任务: {task_id} - {task_name}")
        
        return lifecycle
    
    def start_task(self, task_id: str) -> bool:
        """
        启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        if lifecycle.status not in [TaskStatus.PENDING, TaskStatus.READY, TaskStatus.PAUSED]:
            return False
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.status = TaskStatus.RUNNING
        lifecycle.started_at = lifecycle.started_at or now
        
        # 记录启动事件
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="started",
            status=TaskStatus.RUNNING,
            timestamp=now,
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        logger.info(f"启动任务: {task_id}")
        
        return True
    
    def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        completed_steps: Optional[int] = None,
    ) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度 (0-100)
            current_step: 当前步骤
            completed_steps: 已完成步骤数
            
        Returns:
            是否成功
        """
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        lifecycle.progress = max(0.0, min(100.0, progress))
        if current_step:
            lifecycle.current_step = current_step
        if completed_steps is not None:
            lifecycle.completed_steps = completed_steps
        
        return True
    
    def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 执行结果
            
        Returns:
            是否成功
        """
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        if lifecycle.status != TaskStatus.RUNNING:
            return False
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.status = TaskStatus.COMPLETED
        lifecycle.completed_at = now
        lifecycle.progress = 100.0
        lifecycle.result = result
        
        # 计算实际耗时
        if lifecycle.started_at:
            start = datetime.fromisoformat(lifecycle.started_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(now.replace("Z", "+00:00"))
            lifecycle.actual_duration = (end - start).total_seconds()
        
        # 记录完成事件
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="completed",
            status=TaskStatus.COMPLETED,
            timestamp=now,
            metadata={"result": result} if result else {},
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        logger.info(f"完成任务: {task_id}")
        
        return True
    
    def fail_task(
        self,
        task_id: str,
        error: str,
        retry: bool = False,
    ) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            retry: 是否重试
            
        Returns:
            是否成功
        """
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.error = error
        lifecycle.failed_at = now
        
        if retry and lifecycle.retry_count < lifecycle.max_retries:
            lifecycle.status = TaskStatus.RETRYING
            lifecycle.retry_count += 1
            event_type = "retrying"
        else:
            lifecycle.status = TaskStatus.FAILED
            event_type = "failed"
        
        # 记录失败事件
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type=event_type,
            status=lifecycle.status,
            timestamp=now,
            metadata={"error": error, "retry_count": lifecycle.retry_count},
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        logger.warning(f"任务失败: {task_id} - {error}")
        
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        if lifecycle.status != TaskStatus.RUNNING:
            return False
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.status = TaskStatus.PAUSED
        
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="paused",
            status=TaskStatus.PAUSED,
            timestamp=now,
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        return True
    
    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        if lifecycle.status != TaskStatus.PAUSED:
            return False
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.status = TaskStatus.RUNNING
        
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="resumed",
            status=TaskStatus.RUNNING,
            timestamp=now,
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
        
        lifecycle = self.tasks[task_id]
        
        if lifecycle.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        now = datetime.utcnow().isoformat() + "Z"
        lifecycle.status = TaskStatus.CANCELLED
        lifecycle.cancelled_at = now
        
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type="cancelled",
            status=TaskStatus.CANCELLED,
            timestamp=now,
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        
        return True
    
    def get_task(self, task_id: str) -> Optional[TaskLifecycle]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[TaskLifecycle]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计"""
        total = len(self.tasks)
        
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 计算平均完成时间
        completed_tasks = [
            t for t in self.tasks.values()
            if t.status == TaskStatus.COMPLETED and t.actual_duration
        ]
        avg_duration = (
            sum(t.actual_duration for t in completed_tasks) / len(completed_tasks)
            if completed_tasks else 0
        )
        
        return {
            "total_tasks": total,
            "status_distribution": status_counts,
            "average_duration": avg_duration,
            "completed_count": status_counts.get("completed", 0),
            "failed_count": status_counts.get("failed", 0),
            "running_count": status_counts.get("running", 0),
        }


_task_lifecycle_manager: Optional[TaskLifecycleManager] = None


def get_task_lifecycle_manager() -> TaskLifecycleManager:
    """获取任务生命周期管理器实例"""
    global _task_lifecycle_manager
    if _task_lifecycle_manager is None:
        _task_lifecycle_manager = TaskLifecycleManager()
    return _task_lifecycle_manager

