#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闭环执行引擎
P0-001: 整合统一事件流、自动检查、反馈入库、证据记录，实现完整的"接受→执行→检查→反馈→再执行"闭环
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4

from .unified_event_bus import UnifiedEventBus, EventCategory, EventSeverity, get_unified_event_bus
from .execution_checker import ExecutionChecker, CheckType, CheckResult
from .feedback_handler import FeedbackHandler, FeedbackType, FeedbackStatus
from .evidence_recorder import EvidenceRecorder, EvidenceType
from .closure_recorder import ClosureRecorder, ClosurePhase

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXECUTING = "executing"
    CHECKING = "checking"
    FEEDBACK = "feedback"
    RE_EXECUTING = "re_executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """执行上下文"""
    execution_id: str
    task_id: Optional[str]
    module: str
    function: str
    parameters: Dict[str, Any]
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)


class ClosedLoopEngine:
    """
    闭环执行引擎
    
    实现完整的"接受→执行→检查→反馈→再执行"闭环：
    1. ACCEPT: 接受任务
    2. EXECUTE: 执行任务
    3. CHECK: 自动检查执行结果
    4. FEEDBACK: 处理反馈
    5. RE_EXECUTE: 根据反馈再执行（如果需要）
    """
    
    def __init__(
        self,
        event_bus: Optional[UnifiedEventBus] = None,
        execution_checker: Optional[ExecutionChecker] = None,
        feedback_handler: Optional[FeedbackHandler] = None,
        evidence_recorder: Optional[EvidenceRecorder] = None,
        closure_recorder: Optional[ClosureRecorder] = None,
    ):
        self.event_bus = event_bus or get_unified_event_bus()
        self.execution_checker = execution_checker or ExecutionChecker(self.event_bus)
        self.feedback_handler = feedback_handler or FeedbackHandler(self.event_bus)
        self.evidence_recorder = evidence_recorder or EvidenceRecorder(self.event_bus)
        self.closure_recorder = closure_recorder or ClosureRecorder()
        
        # 执行上下文存储
        self.executions: Dict[str, ExecutionContext] = {}
        self._lock = asyncio.Lock()
        
        # 订阅反馈事件（用于触发再执行）
        self._subscribe_to_feedback_events()
    
    def _subscribe_to_feedback_events(self):
        """订阅反馈事件"""
        from .unified_event_bus import EventFilter
        
        feedback_filter = EventFilter(
            category=EventCategory.FEEDBACK,
            event_type="feedback_created",
        )
        self.event_bus.subscribe(
            callback=self._handle_feedback_for_re_execution,
            event_filter=feedback_filter,
            subscriber_id="closed_loop_engine_feedback",
        )
    
    async def _handle_feedback_for_re_execution(self, event):
        """处理反馈事件（判断是否需要再执行）"""
        try:
            feedback_id = event.payload.get("feedback_id")
            execution_id = event.payload.get("execution_id")
            
            # 获取反馈
            feedback = self.feedback_handler.get_feedback(feedback_id)
            if not feedback:
                return
            
            # 如果是检查失败反馈，且状态为pending，考虑再执行
            if (feedback.feedback_type == FeedbackType.CHECK_RESULT and
                feedback.status == FeedbackStatus.PENDING):
                
                check_result = feedback.content.get("result")
                if check_result == "fail":
                    # 自动触发再执行
                    await self.re_execute(execution_id, reason="检查失败自动重试")
        except Exception as e:
            logger.error(f"处理反馈事件失败: {e}", exc_info=True)
    
    async def accept_task(
        self,
        task_id: str,
        module: str,
        function: str,
        parameters: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionContext:
        """
        接受任务（ACCEPT阶段）
        
        Args:
            task_id: 任务ID
            module: 模块名
            function: 函数名
            parameters: 参数
            metadata: 元数据
            
        Returns:
            执行上下文
        """
        execution_id = f"exec_{uuid4()}"
        
        context = ExecutionContext(
            execution_id=execution_id,
            task_id=task_id,
            module=module,
            function=function,
            parameters=parameters,
            status=ExecutionStatus.ACCEPTED,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self.executions[execution_id] = context
        
        # 记录闭环阶段
        self.closure_recorder.record(
            phase=ClosurePhase.ACCEPT,
            source="closed_loop_engine",
            status="success",
            task_id=task_id,
            module=module,
            metadata={
                "execution_id": execution_id,
                "function": function,
            },
        )
        
        # 发布接受事件
        await self.event_bus.publish(
            category=EventCategory.TASK,
            event_type="task_accepted",
            source="closed_loop_engine",
            severity=EventSeverity.INFO,
            payload={
                "execution_id": execution_id,
                "task_id": task_id,
                "module": module,
                "function": function,
            },
            correlation_id=execution_id,
        )
        
        # 记录证据
        await self.evidence_recorder.record_evidence(
            evidence_type=EvidenceType.EXECUTION,
            execution_id=execution_id,
            source="closed_loop_engine",
            content={
                "phase": "accept",
                "task_id": task_id,
                "module": module,
                "function": function,
                "parameters": parameters,
            },
            metadata=metadata,
        )
        
        logger.info(f"任务已接受: {execution_id} ({module}.{function})")
        
        return context
    
    async def execute(
        self,
        execution_id: str,
        executor: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]] | Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        执行任务（EXECUTE阶段）
        
        Args:
            execution_id: 执行ID
            executor: 执行函数
            
        Returns:
            执行结果
        """
        context = self.executions.get(execution_id)
        if not context:
            raise ValueError(f"执行上下文不存在: {execution_id}")
        
        context.status = ExecutionStatus.EXECUTING
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 记录闭环阶段
        self.closure_recorder.record(
            phase=ClosurePhase.EXECUTE,
            source="closed_loop_engine",
            status="success",
            task_id=context.task_id,
            module=context.module,
            metadata={
                "execution_id": execution_id,
                "function": context.function,
            },
        )
        
        # 发布执行事件
        await self.event_bus.publish(
            category=EventCategory.EXECUTION,
            event_type="execution_started",
            source="closed_loop_engine",
            severity=EventSeverity.INFO,
            payload={
                "execution_id": execution_id,
                "module": context.module,
                "function": context.function,
            },
            correlation_id=execution_id,
        )
        
        start_time = datetime.utcnow()
        
        try:
            # 执行
            if asyncio.iscoroutinefunction(executor):
                result = await executor(context.parameters)
            else:
                result = executor(context.parameters)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新上下文
            context.result = {
                "success": True,
                "result": result,
                "duration": duration,
            }
            context.status = ExecutionStatus.CHECKING
            context.updated_at = datetime.utcnow().isoformat() + "Z"
            
            # 记录执行证据
            await self.evidence_recorder.record_evidence(
                evidence_type=EvidenceType.EXECUTION,
                execution_id=execution_id,
                source="closed_loop_engine",
                content={
                    "phase": "execute",
                    "result": result,
                    "duration": duration,
                },
            )
            
            # 自动进入检查阶段
            await self.check_execution(execution_id)
            
            return context.result
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            
            # 更新上下文
            context.result = {
                "success": False,
                "error": error_msg,
                "duration": duration,
            }
            context.error = error_msg
            context.status = ExecutionStatus.FAILED
            context.updated_at = datetime.utcnow().isoformat() + "Z"
            
            # 记录错误证据
            await self.evidence_recorder.record_evidence(
                evidence_type=EvidenceType.EXECUTION,
                execution_id=execution_id,
                source="closed_loop_engine",
                content={
                    "phase": "execute",
                    "error": error_msg,
                    "duration": duration,
                },
            )
            
            # 发布错误事件
            await self.event_bus.publish(
                category=EventCategory.EXECUTION,
                event_type="execution_failed",
                source="closed_loop_engine",
                severity=EventSeverity.ERROR,
                payload={
                    "execution_id": execution_id,
                    "error": error_msg,
                },
                correlation_id=execution_id,
            )
            
            raise
    
    async def check_execution(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        检查执行结果（CHECK阶段）
        
        Args:
            execution_id: 执行ID
            
        Returns:
            检查报告列表
        """
        context = self.executions.get(execution_id)
        if not context or not context.result:
            return []
        
        context.status = ExecutionStatus.CHECKING
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 记录闭环阶段
        self.closure_recorder.record(
            phase=ClosurePhase.CHECK,
            source="closed_loop_engine",
            status="success",
            task_id=context.task_id,
            module=context.module,
            metadata={
                "execution_id": execution_id,
            },
        )
        
        # 执行检查
        check_reports = await self.execution_checker.check_execution(
            execution_id=execution_id,
            execution_result=context.result,
        )
        
        # 记录检查证据
        await self.evidence_recorder.record_evidence(
            evidence_type=EvidenceType.CHECK,
            execution_id=execution_id,
            source="closed_loop_engine",
            content={
                "phase": "check",
                "reports": [report.__dict__ for report in check_reports],
            },
        )
        
        # 判断是否有失败
        has_failure = any(r.result == CheckResult.FAIL for r in check_reports)
        
        if has_failure:
            context.status = ExecutionStatus.FEEDBACK
        else:
            context.status = ExecutionStatus.COMPLETED
        
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 发布检查完成事件
        await self.event_bus.publish(
            category=EventCategory.CHECK,
            event_type="check_completed",
            source="closed_loop_engine",
            severity=EventSeverity.WARNING if has_failure else EventSeverity.INFO,
            payload={
                "execution_id": execution_id,
                "has_failure": has_failure,
                "reports_count": len(check_reports),
            },
            correlation_id=execution_id,
        )
        
        # 如果有失败，自动创建反馈
        if has_failure:
            await self.feedback_handler.create_feedback(
                feedback_type=FeedbackType.CHECK_RESULT,
                execution_id=execution_id,
                source="closed_loop_engine",
                content={
                    "reports": [report.__dict__ for report in check_reports],
                    "has_failure": True,
                },
            )
        
        return [report.__dict__ for report in check_reports]
    
    async def process_feedback(
        self,
        execution_id: str,
        feedback_id: str,
        action: str,
    ) -> bool:
        """
        处理反馈（FEEDBACK阶段）
        
        Args:
            execution_id: 执行ID
            feedback_id: 反馈ID
            action: 处理动作（resolve/ignore/re_execute）
            
        Returns:
            是否成功
        """
        context = self.executions.get(execution_id)
        if not context:
            return False
        
        context.status = ExecutionStatus.FEEDBACK
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 记录闭环阶段
        self.closure_recorder.record(
            phase=ClosurePhase.FEEDBACK,
            source="closed_loop_engine",
            status="success",
            task_id=context.task_id,
            module=context.module,
            metadata={
                "execution_id": execution_id,
                "feedback_id": feedback_id,
                "action": action,
            },
        )
        
        # 处理反馈
        success = await self.feedback_handler.process_feedback(
            feedback_id=feedback_id,
            action=action,
        )
        
        # 记录反馈证据
        await self.evidence_recorder.record_evidence(
            evidence_type=EvidenceType.FEEDBACK,
            execution_id=execution_id,
            source="closed_loop_engine",
            content={
                "phase": "feedback",
                "feedback_id": feedback_id,
                "action": action,
            },
        )
        
        # 如果动作是re_execute，触发再执行
        if action == "re_execute":
            await self.re_execute(execution_id, reason=f"反馈处理: {action}")
        
        return success
    
    async def re_execute(
        self,
        execution_id: str,
        reason: Optional[str] = None,
        executor: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        再执行（RE_EXECUTE阶段）
        
        Args:
            execution_id: 执行ID
            reason: 再执行原因
            executor: 执行函数（如果提供，使用新的执行函数）
            
        Returns:
            执行结果
        """
        context = self.executions.get(execution_id)
        if not context:
            raise ValueError(f"执行上下文不存在: {execution_id}")
        
        context.status = ExecutionStatus.RE_EXECUTING
        context.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 记录闭环阶段
        self.closure_recorder.record(
            phase=ClosurePhase.REEXECUTE,
            source="closed_loop_engine",
            status="success",
            task_id=context.task_id,
            module=context.module,
            metadata={
                "execution_id": execution_id,
                "reason": reason,
            },
        )
        
        # 发布再执行事件
        await self.event_bus.publish(
            category=EventCategory.EXECUTION,
            event_type="re_execution_started",
            source="closed_loop_engine",
            severity=EventSeverity.INFO,
            payload={
                "execution_id": execution_id,
                "reason": reason,
            },
            correlation_id=execution_id,
        )
        
        # 如果提供了新的执行函数，使用新的；否则使用原来的参数重新执行
        # 注意：这里需要外部提供执行函数，因为不同模块的执行逻辑不同
        if executor:
            return await self.execute(execution_id, executor)
        else:
            # 如果没有提供执行函数，标记为需要手动处理
            context.status = ExecutionStatus.PENDING
            context.metadata["re_execute_reason"] = reason
            context.metadata["re_execute_at"] = datetime.utcnow().isoformat() + "Z"
            
            return {
                "success": False,
                "message": "需要提供执行函数才能再执行",
                "reason": reason,
            }
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """获取执行上下文"""
        return self.executions.get(execution_id)
    
    def get_execution_timeline(self, execution_id: str) -> Dict[str, Any]:
        """获取执行时间线（包含所有证据）"""
        context = self.get_execution(execution_id)
        if not context:
            return {}
        
        # 获取所有证据
        evidence_list = self.evidence_recorder.get_evidence_timeline(execution_id)
        
        # 获取所有检查报告
        check_reports = self.execution_checker.get_reports(execution_id=execution_id)
        
        # 获取所有反馈
        feedbacks = self.feedback_handler.get_feedbacks(execution_id=execution_id)
        
        # 获取所有事件
        events = self.event_bus.get_events(correlation_id=execution_id)
        
        return {
            "execution": context.__dict__,
            "evidence": [ev.to_dict() for ev in evidence_list],
            "checks": [r.__dict__ for r in check_reports],
            "feedbacks": [fb.to_dict() for fb in feedbacks],
            "events": [e.to_dict() for e in events],
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.executions)
        by_status = {}
        
        for context in self.executions.values():
            status = context.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_executions": total,
            "by_status": by_status,
            "checker_stats": self.execution_checker.get_statistics(),
            "feedback_stats": self.feedback_handler.get_statistics(),
            "evidence_stats": self.evidence_recorder.get_statistics(),
            "event_stats": self.event_bus.get_statistics(),
        }

