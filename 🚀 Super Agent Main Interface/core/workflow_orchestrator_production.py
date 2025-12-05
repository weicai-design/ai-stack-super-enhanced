"""
工作流编排器生产级增强模块
达到生产水平的状态机、事件系统和错误处理

生产级特性：
1. 状态转换超时处理和回滚
2. 事件持久化和重试
3. 错误分类和恢复策略
4. 工作流数据持久化
5. 并发控制和锁机制
6. 监控和告警
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from uuid import uuid4

from .workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowType,
    WorkflowState,
    WorkflowEventType,
    WorkflowData,
    IntelligentWorkflowData,
    DirectWorkflowData,
)
from .unified_event_bus import UnifiedEventBus, UnifiedEvent, EventCategory, EventSeverity

logger = logging.getLogger(__name__)


class WorkflowErrorType(str, Enum):
    """工作流错误类型"""
    TIMEOUT = "timeout"
    STATE_TRANSITION_ERROR = "state_transition_error"
    MODULE_EXECUTION_ERROR = "module_execution_error"
    EVENT_PUBLISH_ERROR = "event_publish_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class StateTransitionHistory:
    """状态转换历史"""
    from_state: WorkflowState
    to_state: WorkflowState
    timestamp: str
    duration: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowLock:
    """工作流锁"""
    workflow_id: str
    locked_at: float
    locked_by: str
    timeout: float = 300.0  # 5分钟超时


class ProductionWorkflowOrchestrator(WorkflowOrchestrator):
    """
    生产级工作流编排器
    
    增强功能：
    1. 状态转换超时处理
    2. 状态回滚机制
    3. 事件持久化和重试
    4. 错误分类和恢复
    5. 工作流数据持久化
    6. 并发控制
    7. 监控和告警
    """
    
    def __init__(
        self,
        event_bus: Optional[UnifiedEventBus] = None,
        rag_service: Optional[Any] = None,
        expert_router: Optional[Any] = None,
        module_executor: Optional[Any] = None,
        observability_system: Optional[Any] = None,
        persistence_dir: Optional[Path] = None,
        state_timeout: float = 300.0,  # 5分钟
        max_retries: int = 3,
        enable_persistence: bool = True,
    ):
        """
        初始化生产级工作流编排器
        
        Args:
            event_bus: 统一事件总线
            rag_service: RAG服务适配器
            expert_router: 专家路由器
            module_executor: 模块执行器
            observability_system: 可观测性系统
            persistence_dir: 持久化目录
            state_timeout: 状态超时时间（秒）
            max_retries: 最大重试次数
            enable_persistence: 是否启用持久化
        """
        super().__init__(
            event_bus=event_bus,
            rag_service=rag_service,
            expert_router=expert_router,
            module_executor=module_executor,
            observability_system=observability_system,
        )
        
        self.persistence_dir = persistence_dir or Path("data/workflows")
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_timeout = state_timeout
        self.max_retries = max_retries
        self.enable_persistence = enable_persistence
        
        # 状态转换历史
        self.state_history: Dict[str, List[StateTransitionHistory]] = {}
        
        # 工作流锁
        self.workflow_locks: Dict[str, WorkflowLock] = {}
        self._lock_timeout_check_interval = 60.0  # 1分钟检查一次
        
        # 事件持久化队列
        self.event_queue: deque = deque(maxlen=10000)
        self.event_retry_queue: deque = deque(maxlen=1000)
        
        # 错误统计
        self.error_stats: Dict[str, int] = {}
        
        # 状态超时监控
        self.state_timeouts: Dict[str, float] = {}  # workflow_id -> state_start_time
        
        # 启动后台任务
        self._background_tasks: Set[asyncio.Task] = set()
        self._start_background_tasks()
        
        logger.info("生产级工作流编排器初始化完成")
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 状态超时检查任务
        task = asyncio.create_task(self._check_state_timeouts())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        # 事件重试任务
        task = asyncio.create_task(self._retry_failed_events())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        # 锁超时检查任务
        task = asyncio.create_task(self._check_lock_timeouts())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def _check_state_timeouts(self):
        """检查状态超时"""
        while True:
            try:
                await asyncio.sleep(self._lock_timeout_check_interval)
                
                current_time = time.time()
                timed_out_workflows = []
                
                for workflow_id, start_time in self.state_timeouts.items():
                    if current_time - start_time > self.state_timeout:
                        timed_out_workflows.append(workflow_id)
                
                for workflow_id in timed_out_workflows:
                    await self._handle_state_timeout(workflow_id)
                    
            except Exception as e:
                logger.error(f"检查状态超时失败: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def _handle_state_timeout(self, workflow_id: str):
        """处理状态超时"""
        try:
            async with self._lock:
                workflow = self.workflows.get(workflow_id)
                if not workflow:
                    return
                
                # 记录超时错误
                self._record_error(WorkflowErrorType.TIMEOUT, workflow_id)
                
                # 尝试回滚到上一个状态
                if workflow_id in self.state_history and self.state_history[workflow_id]:
                    last_transition = self.state_history[workflow_id][-1]
                    if last_transition.success:
                        # 回滚到上一个状态
                        workflow.state = last_transition.from_state
                        workflow.updated_at = datetime.utcnow().isoformat() + "Z"
                        workflow.error = f"状态超时: {workflow.state.value}"
                        
                        logger.warning(f"工作流 {workflow_id} 状态超时，回滚到 {last_transition.from_state.value}")
                
                # 标记为失败
                workflow.state = WorkflowState.FAILED
                workflow.completed_at = datetime.utcnow().isoformat() + "Z"
                
                # 发布超时事件
                await self._publish_event(
                    WorkflowEventType.WORKFLOW_FAILED,
                    workflow_id=workflow_id,
                    workflow_type=workflow.workflow_type.value,
                    payload={
                        "error_type": WorkflowErrorType.TIMEOUT.value,
                        "error": f"状态 {workflow.state.value} 超时",
                    },
                    severity=EventSeverity.ERROR,
                )
                
                # 持久化
                if self.enable_persistence:
                    await self._persist_workflow(workflow_id)
                
                # 清除超时监控
                if workflow_id in self.state_timeouts:
                    del self.state_timeouts[workflow_id]
                    
        except Exception as e:
            logger.error(f"处理状态超时失败: {e}", exc_info=True)
    
    async def _retry_failed_events(self):
        """重试失败的事件"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                if not self.event_retry_queue:
                    continue
                
                # 重试队列中的事件
                retry_events = []
                while self.event_retry_queue:
                    retry_events.append(self.event_retry_queue.popleft())
                
                for event_data in retry_events:
                    try:
                        await self._publish_event_with_retry(**event_data)
                    except Exception as e:
                        logger.error(f"重试事件失败: {e}", exc_info=True)
                        # 如果重试次数未超限，重新加入队列
                        if event_data.get("retry_count", 0) < self.max_retries:
                            event_data["retry_count"] = event_data.get("retry_count", 0) + 1
                            self.event_retry_queue.append(event_data)
                        
            except Exception as e:
                logger.error(f"重试失败事件失败: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def _check_lock_timeouts(self):
        """检查锁超时"""
        while True:
            try:
                await asyncio.sleep(self._lock_timeout_check_interval)
                
                current_time = time.time()
                expired_locks = []
                
                for workflow_id, lock in self.workflow_locks.items():
                    if current_time - lock.locked_at > lock.timeout:
                        expired_locks.append(workflow_id)
                
                for workflow_id in expired_locks:
                    logger.warning(f"工作流锁超时: {workflow_id}")
                    del self.workflow_locks[workflow_id]
                    
            except Exception as e:
                logger.error(f"检查锁超时失败: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def acquire_workflow_lock(
        self,
        workflow_id: str,
        lock_owner: str = "system",
        timeout: float = 300.0,
    ) -> bool:
        """
        获取工作流锁
        
        Args:
            workflow_id: 工作流ID
            lock_owner: 锁持有者
            timeout: 锁超时时间（秒）
            
        Returns:
            是否成功获取锁
        """
        async with self._lock:
            if workflow_id in self.workflow_locks:
                lock = self.workflow_locks[workflow_id]
                current_time = time.time()
                
                # 检查锁是否过期
                if current_time - lock.locked_at > lock.timeout:
                    # 锁已过期，可以获取
                    self.workflow_locks[workflow_id] = WorkflowLock(
                        workflow_id=workflow_id,
                        locked_at=current_time,
                        locked_by=lock_owner,
                        timeout=timeout,
                    )
                    return True
                else:
                    # 锁仍有效
                    return False
            else:
                # 没有锁，可以获取
                self.workflow_locks[workflow_id] = WorkflowLock(
                    workflow_id=workflow_id,
                    locked_at=time.time(),
                    locked_by=lock_owner,
                    timeout=timeout,
                )
                return True
    
    async def release_workflow_lock(self, workflow_id: str) -> bool:
        """释放工作流锁"""
        async with self._lock:
            if workflow_id in self.workflow_locks:
                del self.workflow_locks[workflow_id]
                return True
            return False
    
    async def transition_state(
        self,
        workflow_id: str,
        new_state: WorkflowState,
        step_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        状态转换（生产级，带超时和回滚）
        """
        # 检查锁
        if workflow_id in self.workflow_locks:
            lock = self.workflow_locks[workflow_id]
            if lock.locked_by != "system":
                logger.warning(f"工作流 {workflow_id} 被锁定，无法转换状态")
                return False
        
        # 记录状态转换开始时间
        self.state_timeouts[workflow_id] = time.time()
        
        try:
            # 调用父类方法
            result = await super().transition_state(workflow_id, new_state, step_data, error)
            
            if result:
                # 记录状态转换历史
                async with self._lock:
                    workflow = self.workflows.get(workflow_id)
                    if workflow:
                        if workflow_id not in self.state_history:
                            self.state_history[workflow_id] = []
                        
                        # 查找上一个状态
                        from_state = WorkflowState.INITIALIZED
                        if self.state_history[workflow_id]:
                            from_state = self.state_history[workflow_id][-1].to_state
                        
                        transition = StateTransitionHistory(
                            from_state=from_state,
                            to_state=new_state,
                            timestamp=datetime.utcnow().isoformat() + "Z",
                            duration=0.0,  # 将在完成时更新
                            success=not bool(error),
                            error=error,
                            metadata=step_data or {},
                        )
                        self.state_history[workflow_id].append(transition)
                
                # 清除超时监控（如果状态转换成功）
                if not error and workflow_id in self.state_timeouts:
                    del self.state_timeouts[workflow_id]
                
                # 持久化
                if self.enable_persistence:
                    await self._persist_workflow(workflow_id)
            
            return result
            
        except Exception as e:
            logger.error(f"状态转换失败: {e}", exc_info=True)
            self._record_error(WorkflowErrorType.STATE_TRANSITION_ERROR, workflow_id)
            return False
    
    async def _publish_event_with_retry(
        self,
        event_type: WorkflowEventType,
        workflow_id: str,
        workflow_type: str,
        payload: Dict[str, Any],
        severity: EventSeverity = EventSeverity.INFO,
        retry_count: int = 0,
    ):
        """发布事件（带重试）"""
        try:
            await self._publish_event(
                event_type=event_type,
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                payload=payload,
                severity=severity,
            )
        except Exception as e:
            logger.error(f"发布事件失败: {e}", exc_info=True)
            
            # 如果重试次数未超限，加入重试队列
            if retry_count < self.max_retries:
                self.event_retry_queue.append({
                    "event_type": event_type,
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type,
                    "payload": payload,
                    "severity": severity,
                    "retry_count": retry_count + 1,
                })
            else:
                self._record_error(WorkflowErrorType.EVENT_PUBLISH_ERROR, workflow_id)
    
    def _record_error(self, error_type: WorkflowErrorType, workflow_id: str):
        """记录错误统计"""
        error_key = f"{error_type.value}_{workflow_id}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1
    
    async def _persist_workflow(self, workflow_id: str):
        """持久化工作流数据"""
        try:
            async with self._lock:
                workflow = self.workflows.get(workflow_id)
                if not workflow:
                    return
                
                # 保存到文件
                workflow_file = self.persistence_dir / f"{workflow_id}.json"
                workflow_data = workflow.to_dict()
                
                # 添加状态历史
                if workflow_id in self.state_history:
                    workflow_data["state_history"] = [
                        {
                            "from_state": h.from_state.value,
                            "to_state": h.to_state.value,
                            "timestamp": h.timestamp,
                            "duration": h.duration,
                            "success": h.success,
                            "error": h.error,
                            "metadata": h.metadata,
                        }
                        for h in self.state_history[workflow_id]
                    ]
                
                with open(workflow_file, "w", encoding="utf-8") as f:
                    json.dump(workflow_data, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"持久化工作流失败: {e}", exc_info=True)
    
    async def load_workflow(self, workflow_id: str) -> Optional[WorkflowData]:
        """从持久化存储加载工作流"""
        try:
            workflow_file = self.persistence_dir / f"{workflow_id}.json"
            
            if not workflow_file.exists():
                return None
            
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
            
            # 重建工作流对象
            if workflow_data.get("workflow_type") == WorkflowType.INTELLIGENT.value:
                workflow = IntelligentWorkflowData(**workflow_data)
            elif workflow_data.get("workflow_type") == WorkflowType.DIRECT.value:
                workflow = DirectWorkflowData(**workflow_data)
            else:
                return None
            
            # 恢复状态历史
            if "state_history" in workflow_data:
                self.state_history[workflow_id] = [
                    StateTransitionHistory(
                        from_state=WorkflowState(h["from_state"]),
                        to_state=WorkflowState(h["to_state"]),
                        timestamp=h["timestamp"],
                        duration=h["duration"],
                        success=h["success"],
                        error=h.get("error"),
                        metadata=h.get("metadata", {}),
                    )
                    for h in workflow_data["state_history"]
                ]
            
            # 恢复到内存
            async with self._lock:
                self.workflows[workflow_id] = workflow
            
            return workflow
            
        except Exception as e:
            logger.error(f"加载工作流失败: {e}", exc_info=True)
            return None
    
    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return self.error_stats.copy()
    
    def get_state_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """获取状态转换历史"""
        if workflow_id not in self.state_history:
            return []
        
        return [
            {
                "from_state": h.from_state.value,
                "to_state": h.to_state.value,
                "timestamp": h.timestamp,
                "duration": h.duration,
                "success": h.success,
                "error": h.error,
                "metadata": h.metadata,
            }
            for h in self.state_history[workflow_id]
        ]
    
    async def rollback_workflow_state(
        self,
        workflow_id: str,
        target_state: Optional[WorkflowState] = None,
    ) -> bool:
        """
        回滚工作流状态
        
        Args:
            workflow_id: 工作流ID
            target_state: 目标状态（如果为None，回滚到上一个成功状态）
            
        Returns:
            是否成功回滚
        """
        try:
            async with self._lock:
                workflow = self.workflows.get(workflow_id)
                if not workflow:
                    return False
                
                if workflow_id not in self.state_history:
                    return False
                
                history = self.state_history[workflow_id]
                
                if target_state:
                    # 回滚到指定状态
                    workflow.state = target_state
                else:
                    # 回滚到上一个成功状态
                    for transition in reversed(history):
                        if transition.success:
                            workflow.state = transition.from_state
                            break
                
                workflow.updated_at = datetime.utcnow().isoformat() + "Z"
                workflow.error = "状态已回滚"
                
                # 发布回滚事件
                await self._publish_event(
                    WorkflowEventType.WORKFLOW_STATE_CHANGED,
                    workflow_id=workflow_id,
                    workflow_type=workflow.workflow_type.value,
                    payload={
                        "old_state": history[-1].to_state.value if history else None,
                        "new_state": workflow.state.value,
                        "reason": "rollback",
                    },
                )
                
                # 持久化
                if self.enable_persistence:
                    await self._persist_workflow(workflow_id)
                
                return True
                
        except Exception as e:
            logger.error(f"回滚工作流状态失败: {e}", exc_info=True)
            return False
    
    async def cleanup(self):
        """清理资源"""
        # 取消后台任务
        for task in self._background_tasks:
            task.cancel()
        
        # 等待任务完成
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        logger.info("生产级工作流编排器已清理")


# 单例模式
_production_orchestrator: Optional[ProductionWorkflowOrchestrator] = None


def get_production_workflow_orchestrator(
    event_bus: Optional[UnifiedEventBus] = None,
    rag_service: Optional[Any] = None,
    expert_router: Optional[Any] = None,
    module_executor: Optional[Any] = None,
    observability_system: Optional[Any] = None,
    persistence_dir: Optional[Path] = None,
    state_timeout: float = 300.0,
    max_retries: int = 3,
    enable_persistence: bool = True,
) -> ProductionWorkflowOrchestrator:
    """获取生产级工作流编排器单例"""
    global _production_orchestrator
    if _production_orchestrator is None:
        _production_orchestrator = ProductionWorkflowOrchestrator(
            event_bus=event_bus,
            rag_service=rag_service,
            expert_router=expert_router,
            module_executor=module_executor,
            observability_system=observability_system,
            persistence_dir=persistence_dir,
            state_timeout=state_timeout,
            max_retries=max_retries,
            enable_persistence=enable_persistence,
        )
    return _production_orchestrator

