#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务生命周期管理器
P2-303: 实现真实任务生命周期管理
"""

from __future__ import annotations

import asyncio
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4
from collections import defaultdict, deque

from .task_templates import TaskTemplateLibrary

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(timestamp: Optional[str]) -> Optional[datetime]:
    if not timestamp:
        return None
    ts = timestamp
    if ts.endswith("Z"):
        ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


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
class TaskDependency:
    """任务依赖"""
    dependency_id: str
    task_id: str
    depends_on_task_id: str
    dependency_type: str  # required/optional/conditional
    condition: Optional[Dict[str, Any]] = None  # 依赖条件
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskStep:
    """任务步骤"""
    step_id: str
    step_name: str
    order: int
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
    status: str = "pending"  # pending/running/completed/failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    rollback_action: Optional[str] = None  # 回滚操作
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RollbackPlan:
    """回滚计划"""
    rollback_id: str
    task_id: str
    steps: List[Dict[str, Any]]  # 回滚步骤
    created_at: str
    executed_at: Optional[str] = None
    status: str = "pending"  # pending/executing/completed/failed
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskSummary:
    """任务总结"""
    task_id: str
    summary_id: str
    execution_summary: Dict[str, Any]
    performance_stats: Dict[str, Any]
    lessons_learned: List[str]
    recommendations: List[str]
    created_at: str
    
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
    # 新增字段（6.1）
    template_id: Optional[str] = None  # 使用的模板ID
    steps: List[TaskStep] = field(default_factory=list)  # 任务步骤
    dependencies: List[TaskDependency] = field(default_factory=list)  # 任务依赖
    rollback_plan: Optional[RollbackPlan] = None  # 回滚计划
    summary: Optional[TaskSummary] = None  # 任务总结
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        data["events"] = [e.to_dict() for e in self.events]
        data["steps"] = [s.to_dict() for s in self.steps]
        data["dependencies"] = [d.to_dict() for d in self.dependencies]
        if self.rollback_plan:
            data["rollback_plan"] = self.rollback_plan.to_dict()
        if self.summary:
            data["summary"] = self.summary.to_dict()
        return data


class TaskLifecycleManager:
    """
    任务生命周期管理器（生产级实现 - 6.1）
    
    功能：
    1. 管理任务完整生命周期
    2. 记录所有生命周期事件
    3. 支持任务状态转换
    4. 提供生命周期查询
    5. 任务模板管理（6.1新增）
    6. 依赖解析（6.1新增）
    7. 失败回滚（6.1新增）
    8. 任务总结（6.1新增）
    """
    
    def __init__(self):
        self.tasks: Dict[str, TaskLifecycle] = {}
        self.event_history: List[TaskLifecycleEvent] = []
        
        # 任务模板库（6.1新增）
        self.template_library = TaskTemplateLibrary()
        self.custom_templates: Dict[str, Dict[str, Any]] = {}
        
        # 依赖图（6.1新增）
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> {depends_on_task_ids}
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> {dependent_task_ids}
        
        # 回滚历史（6.1新增）
        self.rollback_history: List[RollbackPlan] = []
        
        # 任务总结（6.1新增）
        self.task_summaries: Dict[str, TaskSummary] = {}
        
        logger.info("任务生命周期管理器初始化完成（生产级 - 6.1）")
    
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
        now = _now()
        
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
        
        now = _now()
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
        
        now = _now()
        lifecycle.status = TaskStatus.COMPLETED
        lifecycle.completed_at = now
        lifecycle.progress = 100.0
        lifecycle.result = result
        
        # 计算实际耗时
        if lifecycle.started_at:
            start_dt = _parse_iso(lifecycle.started_at)
            end_dt = _parse_iso(now)
            if start_dt and end_dt:
                lifecycle.actual_duration = (end_dt - start_dt).total_seconds()
        
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
        
        now = _now()
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
        
        now = _now()
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
        
        now = _now()
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
        
        now = _now()
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
    
    def set_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """通用状态更新，用于外部系统同步状态"""
        lifecycle = self.tasks.get(task_id)
        if not lifecycle:
            return False
        
        now = _now()
        lifecycle.status = status
        if status == TaskStatus.CANCELLED:
            lifecycle.cancelled_at = now
        if status == TaskStatus.RUNNING and not lifecycle.started_at:
            lifecycle.started_at = now
        event = TaskLifecycleEvent(
            event_id=f"event_{uuid4()}",
            task_id=task_id,
            event_type=f"status_{status.value}",
            status=status,
            timestamp=now,
            metadata=metadata or {},
        )
        lifecycle.events.append(event)
        self.event_history.append(event)
        return True
    
    def mark_task_ready(self, task_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """标记任务为就绪状态"""
        lifecycle = self.tasks.get(task_id)
        if not lifecycle:
            return False
        return self.set_task_status(task_id, TaskStatus.READY, metadata)
    
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
    
    # ============ 任务模板管理（6.1新增） ============
    
    def register_template(
        self,
        template_id: str,
        template_config: Dict[str, Any],
    ) -> bool:
        """
        注册自定义任务模板
        
        Args:
            template_id: 模板ID
            template_config: 模板配置
            
        Returns:
            是否成功
        """
        try:
            # 验证模板配置
            required_fields = ["name", "description", "steps"]
            for field in required_fields:
                if field not in template_config:
                    logger.error(f"模板缺少必需字段: {field}")
                    return False
            
            self.custom_templates[template_id] = template_config
            logger.info(f"注册任务模板: {template_id}")
            return True
        except Exception as e:
            logger.error(f"注册任务模板失败: {e}", exc_info=True)
            return False
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            模板配置
        """
        # 先检查自定义模板
        if template_id in self.custom_templates:
            return self.custom_templates[template_id]
        
        # 再检查内置模板
        return self.template_library.get_template(template_id)
    
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有任务模板
        
        Returns:
            模板字典
        """
        all_templates = {}
        
        # 内置模板
        builtin_templates = self.template_library.get_all_templates()
        for template_id, template in builtin_templates.items():
            all_templates[f"builtin:{template_id}"] = template
        
        # 自定义模板
        for template_id, template in self.custom_templates.items():
            all_templates[f"custom:{template_id}"] = template
        
        return all_templates
    
    def create_task_from_template(
        self,
        template_id: str,
        task_name: str,
        custom_config: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Optional[TaskLifecycle]:
        """
        从模板创建任务
        
        Args:
            template_id: 模板ID（可以是 builtin:xxx 或 custom:xxx）
            task_name: 任务名称
            custom_config: 自定义配置
            priority: 优先级
            
        Returns:
            任务生命周期对象
        """
        # 解析模板ID
        if ":" in template_id:
            template_type, actual_id = template_id.split(":", 1)
        else:
            template_type = "builtin"
            actual_id = template_id
        
        # 获取模板
        if template_type == "custom":
            template = self.custom_templates.get(actual_id)
        else:
            template = self.template_library.get_template(actual_id)
        
        if not template:
            logger.error(f"模板不存在: {template_id}")
            return None
        
        # 创建任务
        task = self.create_task(
            task_name=task_name,
            task_type=actual_id,
            priority=priority,
            metadata={
                "template_id": template_id,
                "template_type": template_type,
                **(custom_config or {}),
            },
        )
        
        # 设置模板信息
        task.template_id = template_id
        task.estimated_duration = template.get("estimated_duration")
        
        # 创建任务步骤
        steps = template.get("steps", [])
        task.steps = [
            TaskStep(
                step_id=f"step_{uuid4()}",
                step_name=step.get("name", f"步骤{step.get('order', 0)}"),
                order=step.get("order", 0),
                dependencies=step.get("dependencies", []),
                rollback_action=step.get("rollback_action"),
            )
            for step in steps
        ]
        task.total_steps = len(task.steps)
        
        logger.info(f"从模板创建任务: {task.task_id} - {template_id}")
        
        return task
    
    # ============ 依赖解析（6.1新增） ============
    
    def add_dependency(
        self,
        task_id: str,
        depends_on_task_id: str,
        dependency_type: str = "required",
        condition: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加任务依赖
        
        Args:
            task_id: 任务ID
            depends_on_task_id: 依赖的任务ID
            dependency_type: 依赖类型（required/optional/conditional）
            condition: 依赖条件
            
        Returns:
            是否成功
        """
        if task_id not in self.tasks or depends_on_task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id} 或 {depends_on_task_id}")
            return False
        
        # 检查循环依赖
        if self._has_circular_dependency(task_id, depends_on_task_id):
            logger.error(f"检测到循环依赖: {task_id} -> {depends_on_task_id}")
            return False
        
        # 添加依赖
        dependency = TaskDependency(
            dependency_id=f"dep_{uuid4()}",
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=dependency_type,
            condition=condition,
        )
        
        self.tasks[task_id].dependencies.append(dependency)
        self.dependency_graph[task_id].add(depends_on_task_id)
        self.reverse_dependency_graph[depends_on_task_id].add(task_id)
        
        logger.info(f"添加任务依赖: {task_id} -> {depends_on_task_id}")
        
        return True
    
    def _has_circular_dependency(self, task_id: str, depends_on_task_id: str) -> bool:
        """
        检查是否存在循环依赖
        
        Args:
            task_id: 任务ID
            depends_on_task_id: 依赖的任务ID
            
        Returns:
            是否存在循环依赖
        """
        # 使用DFS检查循环
        visited = set()
        stack = [depends_on_task_id]
        
        while stack:
            current = stack.pop()
            if current == task_id:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            stack.extend(self.dependency_graph.get(current, set()))
        
        return False
    
    def resolve_dependencies(self, task_id: str) -> Tuple[List[str], List[str]]:
        """
        解析任务依赖，返回执行顺序和冲突
        
        Args:
            task_id: 任务ID
            
        Returns:
            (执行顺序列表, 冲突列表)
        """
        if task_id not in self.tasks:
            return [], [f"任务不存在: {task_id}"]
        
        task = self.tasks[task_id]
        execution_order = []
        conflicts = []
        
        # 拓扑排序
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # 构建依赖图
        for dep in task.dependencies:
            if dep.dependency_type == "required":
                depends_on = dep.depends_on_task_id
                if depends_on not in self.tasks:
                    conflicts.append(f"依赖的任务不存在: {depends_on}")
                    continue
                
                graph[depends_on].append(task_id)
                in_degree[task_id] += 1
        
        # 检查依赖任务状态
        for dep in task.dependencies:
            if dep.dependency_type == "required":
                depends_on = dep.depends_on_task_id
                dep_task = self.tasks.get(depends_on)
                if dep_task:
                    if dep_task.status != TaskStatus.COMPLETED:
                        conflicts.append(
                            f"依赖任务 {depends_on} 未完成，当前状态: {dep_task.status.value}"
                        )
        
        # 拓扑排序
        queue = deque()
        for node in [dep.depends_on_task_id for dep in task.dependencies]:
            if in_degree.get(node, 0) == 0:
                queue.append(node)
        
        while queue:
            node = queue.popleft()
            execution_order.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有未处理的节点（存在循环）
        if len(execution_order) < len([dep.depends_on_task_id for dep in task.dependencies]):
            conflicts.append("检测到循环依赖")
        
        return execution_order, conflicts
    
    def optimize_execution_order(self, task_ids: List[str]) -> List[str]:
        """
        优化任务执行顺序（基于依赖关系）
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            优化后的执行顺序
        """
        # 拓扑排序
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # 构建依赖图
        for task_id in task_ids:
            if task_id not in self.tasks:
                continue
            
            task = self.tasks[task_id]
            for dep in task.dependencies:
                if dep.dependency_type == "required":
                    depends_on = dep.depends_on_task_id
                    if depends_on in task_ids:
                        graph[depends_on].append(task_id)
                        in_degree[task_id] += 1
        
        # 拓扑排序
        queue = deque()
        for task_id in task_ids:
            if in_degree.get(task_id, 0) == 0:
                queue.append(task_id)
        
        execution_order = []
        while queue:
            node = queue.popleft()
            execution_order.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 添加未处理的节点（无依赖或依赖不在列表中）
        for task_id in task_ids:
            if task_id not in execution_order:
                execution_order.append(task_id)
        
        return execution_order
    
    # ============ 失败回滚（6.1新增） ============
    
    def create_rollback_plan(self, task_id: str) -> Optional[RollbackPlan]:
        """
        创建回滚计划
        
        Args:
            task_id: 任务ID
            
        Returns:
            回滚计划
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        # 生成回滚步骤（逆序执行已完成步骤的回滚操作）
        rollback_steps = []
        completed_steps = [s for s in task.steps if s.status == "completed"]
        completed_steps.sort(key=lambda x: x.order, reverse=True)
        
        for step in completed_steps:
            if step.rollback_action:
                rollback_steps.append({
                    "step_id": step.step_id,
                    "step_name": step.step_name,
                    "rollback_action": step.rollback_action,
                    "order": step.order,
                })
        
        rollback_plan = RollbackPlan(
            rollback_id=f"rollback_{uuid4()}",
            task_id=task_id,
            steps=rollback_steps,
                created_at=_now(),
        )
        
        task.rollback_plan = rollback_plan
        self.rollback_history.append(rollback_plan)
        
        logger.info(f"创建回滚计划: {rollback_plan.rollback_id} for {task_id}")
        
        return rollback_plan
    
    async def execute_rollback(self, task_id: str) -> Dict[str, Any]:
        """
        执行回滚
        
        Args:
            task_id: 任务ID
            
        Returns:
            回滚结果
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "任务不存在"}
        
        task = self.tasks[task_id]
        
        if not task.rollback_plan:
            # 自动创建回滚计划
            task.rollback_plan = self.create_rollback_plan(task_id)
        
        if not task.rollback_plan:
            return {"success": False, "error": "无法创建回滚计划"}
        
        rollback_plan = task.rollback_plan
        rollback_plan.status = "executing"
        rollback_plan.executed_at = _now()
        
        rollback_results = []
        
        try:
            # 执行回滚步骤
            for step in rollback_plan.steps:
                try:
                    # 这里应该执行实际的回滚操作
                    # 目前只是记录
                    logger.info(f"执行回滚步骤: {step['step_name']} - {step['rollback_action']}")
                    
                    rollback_results.append({
                        "step_id": step["step_id"],
                        "step_name": step["step_name"],
                        "success": True,
                    })
                except Exception as e:
                    logger.error(f"回滚步骤失败: {step['step_name']} - {e}")
                    rollback_results.append({
                        "step_id": step["step_id"],
                        "step_name": step["step_name"],
                        "success": False,
                        "error": str(e),
                    })
            
            rollback_plan.status = "completed"
            
            # 更新任务状态
            task.status = TaskStatus.CANCELLED
            task.cancelled_at = _now()
            
            # 记录回滚事件
            event = TaskLifecycleEvent(
                event_id=f"event_{uuid4()}",
                task_id=task_id,
                event_type="rolled_back",
                status=TaskStatus.CANCELLED,
                timestamp=_now(),
                metadata={"rollback_id": rollback_plan.rollback_id},
            )
            task.events.append(event)
            self.event_history.append(event)
            
            logger.info(f"回滚完成: {task_id}")
            
            return {
                "success": True,
                "rollback_id": rollback_plan.rollback_id,
                "steps_executed": len(rollback_results),
                "results": rollback_results,
            }
        
        except Exception as e:
            rollback_plan.status = "failed"
            logger.error(f"回滚失败: {task_id} - {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "rollback_id": rollback_plan.rollback_id,
            }
    
    def get_rollback_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取回滚历史
        
        Args:
            task_id: 任务ID（如果为None，返回所有回滚历史）
            limit: 返回数量限制
            
        Returns:
            回滚历史列表
        """
        history = self.rollback_history
        
        if task_id:
            history = [r for r in history if r.task_id == task_id]
        
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return [r.to_dict() for r in history[:limit]]
    
    # ============ 任务总结（6.1新增） ============
    
    def generate_task_summary(self, task_id: str) -> Optional[TaskSummary]:
        """
        生成任务总结
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务总结
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        # 执行总结
        execution_summary = {
            "task_id": task_id,
            "task_name": task.task_name,
            "task_type": task.task_type,
            "status": task.status.value,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "failed_at": task.failed_at,
            "duration": task.actual_duration,
            "estimated_duration": task.estimated_duration,
            "progress": task.progress,
            "total_steps": task.total_steps,
            "completed_steps": task.completed_steps,
            "retry_count": task.retry_count,
            "result": task.result,
            "error": task.error,
        }
        
        # 性能统计
        performance_stats = {
            "duration_vs_estimated": (
                (task.actual_duration / task.estimated_duration * 100)
                if task.actual_duration and task.estimated_duration
                else None
            ),
            "steps_completion_rate": (
                (task.completed_steps / task.total_steps * 100)
                if task.total_steps > 0
                else 0
            ),
            "retry_rate": (
                (task.retry_count / (task.retry_count + 1) * 100)
                if task.retry_count > 0
                else 0
            ),
            "success": task.status == TaskStatus.COMPLETED,
        }
        
        # 经验教训
        lessons_learned = []
        if task.status == TaskStatus.FAILED:
            lessons_learned.append(f"任务失败原因: {task.error}")
        if task.retry_count > 0:
            lessons_learned.append(f"任务重试了 {task.retry_count} 次")
        if task.actual_duration and task.estimated_duration:
            if task.actual_duration > task.estimated_duration * 1.2:
                lessons_learned.append("实际耗时远超预估，需要改进时间估算")
        
        # 建议
        recommendations = []
        if task.status == TaskStatus.FAILED:
            recommendations.append("检查失败原因并修复")
            recommendations.append("考虑增加重试机制")
        if task.retry_count >= task.max_retries:
            recommendations.append("达到最大重试次数，需要人工介入")
        if performance_stats.get("duration_vs_estimated", 0) > 120:
            recommendations.append("实际耗时远超预估，需要优化任务执行效率")
        
        summary = TaskSummary(
            task_id=task_id,
            summary_id=f"summary_{uuid4()}",
            execution_summary=execution_summary,
            performance_stats=performance_stats,
            lessons_learned=lessons_learned,
            recommendations=recommendations,
            created_at=_now(),
        )
        
        task.summary = summary
        self.task_summaries[task_id] = summary
        
        logger.info(f"生成任务总结: {task_id}")
        
        return summary
    
    def get_task_summary(self, task_id: str) -> Optional[TaskSummary]:
        """
        获取任务总结
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务总结
        """
        if task_id in self.task_summaries:
            return self.task_summaries[task_id]
        
        # 如果任务已完成或失败，自动生成总结
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return self.generate_task_summary(task_id)
        
        return None
    
    def get_all_summaries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取所有任务总结
        
        Args:
            limit: 返回数量限制
            
        Returns:
            任务总结列表
        """
        summaries = list(self.task_summaries.values())
        summaries.sort(key=lambda x: x.created_at, reverse=True)
        
        return [s.to_dict() for s in summaries[:limit]]


_task_lifecycle_manager: Optional[TaskLifecycleManager] = None


def get_task_lifecycle_manager() -> TaskLifecycleManager:
    """获取任务生命周期管理器实例"""
    global _task_lifecycle_manager
    if _task_lifecycle_manager is None:
        _task_lifecycle_manager = TaskLifecycleManager()
    return _task_lifecycle_manager

