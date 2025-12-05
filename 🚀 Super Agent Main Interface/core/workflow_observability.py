"""
工作流可观测性增强模块
为工作流提供详细的日志、指标和链路追踪
"""

from __future__ import annotations

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

from .observability_system import (
    ObservabilitySystem,
    Span,
    SpanType,
    SpanStatus,
    Trace,
    LongTask,
    Metric,
)

# 尝试导入生产级模块（如果可用）
try:
    from .workflow_observability_production import (
        ProductionWorkflowObservability,
        AsyncLogWriter,
        SensitiveDataFilter,
        SamplingController,
        LogLevel,
    )
    PRODUCTION_MODE_AVAILABLE = True
except ImportError:
    PRODUCTION_MODE_AVAILABLE = False
    ProductionWorkflowObservability = None
    AsyncLogWriter = None
    SensitiveDataFilter = None
    SamplingController = None
    LogLevel = None

logger = logging.getLogger(__name__)


class WorkflowObservabilityEvent(str, Enum):
    """工作流可观测性事件类型"""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_STEP_FAILED = "workflow.step.failed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    RAG_RETRIEVAL = "workflow.rag.retrieval"
    EXPERT_ROUTING = "workflow.expert.routing"
    MODULE_EXECUTION = "workflow.module.execution"
    RESPONSE_GENERATION = "workflow.response.generation"


@dataclass
class WorkflowObservabilityContext:
    """工作流可观测性上下文"""
    workflow_id: str
    workflow_type: str
    trace_id: str
    request_id: str
    user_input: str
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowObservability:
    """
    工作流可观测性增强
    
    功能：
    1. 结构化日志记录
    2. 性能指标收集
    3. 链路追踪增强
    4. 长任务进度追踪
    """
    
    def __init__(
        self,
        observability_system: Optional[ObservabilitySystem] = None,
        log_dir: Optional[Path] = None,
        production_mode: bool = True,
    ):
        """
        初始化工作流可观测性
        
        Args:
            observability_system: 可观测性系统实例
            log_dir: 日志目录
            production_mode: 是否使用生产模式（异步日志、采样等）
        """
        self.observability = observability_system or ObservabilitySystem()
        self.log_dir = log_dir or Path("logs/workflow")
        self.production_mode = production_mode and PRODUCTION_MODE_AVAILABLE
        
        # 如果启用生产模式，使用生产级组件
        if self.production_mode and ProductionWorkflowObservability:
            # 使用生产级实现
            self._production_impl = ProductionWorkflowObservability(
                observability_system=observability_system,
                log_dir=log_dir,
            )
            self.log_writer = self._production_impl.log_writer
        else:
            # 使用基础实现
            self._production_impl = None
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / f"workflow_observability_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # 工作流追踪存储
        self.workflow_traces: Dict[str, Trace] = {}
        self.workflow_spans: Dict[str, List[Span]] = {}
        self.workflow_metrics: Dict[str, List[Metric]] = {}
        self.trace_index: Dict[str, str] = {}
        
        logger.info(f"工作流可观测性系统初始化完成，生产模式: {self.production_mode}, 日志目录: {self.log_dir}")
    
    def start_workflow_trace(
        self,
        workflow_id: str,
        workflow_type: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> WorkflowObservabilityContext:
        """
        开始工作流追踪
        
        Args:
            workflow_id: 工作流ID
            workflow_type: 工作流类型
            user_input: 用户输入
            context: 上下文
            trace_id: Trace ID（可选）
            request_id: Request ID（可选）
            
        Returns:
            可观测性上下文
        """
        # 创建Trace
        trace = self.observability.start_trace(
            request_id=request_id,
            trace_id=trace_id,
            service_name="workflow-engine",
            tags={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "user_input_length": len(user_input),
            },
        )
        
        self.workflow_traces[workflow_id] = trace
        self.trace_index[trace.trace_id] = workflow_id
        
        # 创建长任务（用于进度追踪）
        long_task = self.observability.create_long_task(
            name=f"工作流: {workflow_id}",
            task_type=workflow_type,
            trace_id=trace.trace_id,
            metadata={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "user_input": user_input[:200],  # 限制长度
            },
        )
        
        # 记录开始事件
        self._log_event(
            WorkflowObservabilityEvent.WORKFLOW_STARTED,
            workflow_id=workflow_id,
            trace_id=trace.trace_id,
            request_id=trace.request_id,
            data={
                "workflow_type": workflow_type,
                "user_input": user_input[:200],
            },
        )
        
        # 记录指标
        self._record_metric(
            "workflow.started",
            1.0,
            tags={
                "workflow_type": workflow_type,
                "workflow_id": workflow_id,
            },
        )
        
        return WorkflowObservabilityContext(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            trace_id=trace.trace_id,
            request_id=trace.request_id,
            user_input=user_input,
            context=context or {},
            metadata={
                "long_task_id": long_task.task_id,
            },
        )
    
    def start_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_type: str,
        parent_span_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Span]:
        """
        开始工作流步骤追踪
        
        Args:
            workflow_id: 工作流ID
            step_name: 步骤名称
            step_type: 步骤类型
            parent_span_id: 父Span ID
            input_data: 输入数据
            
        Returns:
            Span对象
        """
        if not self.observability:
            return None
        
        trace = self.workflow_traces.get(workflow_id)
        if not trace:
            return None
        
        # 创建Span
        span = self.observability.start_span(
            trace_id=trace.trace_id,
            name=f"workflow.step.{step_name}",
            span_type=SpanType.INTERNAL,
            parent_span_id=parent_span_id,
            tags={
                "workflow_id": workflow_id,
                "step_name": step_name,
                "step_type": step_type,
            },
        )
        
        # 记录到工作流Span列表
        if workflow_id not in self.workflow_spans:
            self.workflow_spans[workflow_id] = []
        self.workflow_spans[workflow_id].append(span)
        
        # 记录开始事件
        self._log_event(
            WorkflowObservabilityEvent.WORKFLOW_STEP_STARTED,
            workflow_id=workflow_id,
            trace_id=trace.trace_id,
            span_id=span.span_id,
            data={
                "step_name": step_name,
                "step_type": step_type,
                "input_data_size": len(str(input_data)) if input_data else 0,
            },
        )
        
        # 更新长任务进度
        if workflow_id in self.workflow_traces:
            trace = self.workflow_traces[workflow_id]
            if hasattr(trace, 'tags') and 'long_task_id' in trace.tags:
                # 从metadata中获取long_task_id
                pass  # 需要从context中获取
        
        return span
    
    def complete_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        span_id: Optional[str] = None,
        success: bool = True,
        duration: float = 0.0,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """
        完成工作流步骤追踪
        
        Args:
            workflow_id: 工作流ID
            step_name: 步骤名称
            span_id: Span ID
            success: 是否成功
            duration: 执行时长
            output_data: 输出数据
            error: 错误信息
        """
        if not self.observability:
            return
        
        # 完成Span
        if span_id:
            status = SpanStatus.OK if success else SpanStatus.ERROR
            self.observability.finish_span(span_id, status=status, error=error)
        
        trace = self.workflow_traces.get(workflow_id)
        if not trace:
            return
        
        # 记录完成事件
        event_type = (
            WorkflowObservabilityEvent.WORKFLOW_STEP_COMPLETED
            if success
            else WorkflowObservabilityEvent.WORKFLOW_STEP_FAILED
        )
        
        self._log_event(
            event_type,
            workflow_id=workflow_id,
            trace_id=trace.trace_id,
            span_id=span_id,
            data={
                "step_name": step_name,
                "success": success,
                "duration": duration,
                "output_data_size": len(str(output_data)) if output_data else 0,
                "error": error,
            },
        )
        
        # 记录指标
        self._record_metric(
            f"workflow.step.{step_name}.duration",
            duration,
            tags={
                "workflow_type": trace.tags.get("workflow_type", "unknown"),
                "step_name": step_name,
                "success": str(success),
            },
        )
        
        self._record_metric(
            f"workflow.step.{step_name}.total",
            1.0,
            tags={
                "workflow_type": trace.tags.get("workflow_type", "unknown"),
                "step_name": step_name,
                "status": "success" if success else "failed",
            },
        )
    
    def complete_workflow_trace(
        self,
        workflow_id: str,
        success: bool = True,
        total_duration: float = 0.0,
        response: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        完成工作流追踪
        
        Args:
            workflow_id: 工作流ID
            success: 是否成功
            total_duration: 总时长
            response: 响应内容
            error: 错误信息
        """
        if not self.observability:
            return
        
        trace = self.workflow_traces.get(workflow_id)
        if not trace:
            return
        
        # 完成Trace
        status = "ok" if success else "error"
        self.observability.finish_trace(trace.trace_id, status=status)
        
        # 完成长任务
        # 需要从metadata中获取long_task_id，这里简化处理
        # 实际应该从context中获取
        
        # 记录完成事件
        event_type = (
            WorkflowObservabilityEvent.WORKFLOW_COMPLETED
            if success
            else WorkflowObservabilityEvent.WORKFLOW_FAILED
        )
        
        self._log_event(
            event_type,
            workflow_id=workflow_id,
            trace_id=trace.trace_id,
            data={
                "success": success,
                "total_duration": total_duration,
                "response_length": len(response) if response else 0,
                "error": error,
            },
        )
        
        # 记录指标
        self._record_metric(
            "workflow.total",
            1.0,
            tags={
                "workflow_type": trace.tags.get("workflow_type", "unknown"),
                "status": "success" if success else "failed",
            },
        )
        
        self._record_metric(
            "workflow.duration",
            total_duration,
            tags={
                "workflow_type": trace.tags.get("workflow_type", "unknown"),
                "status": "success" if success else "failed",
            },
        )
    
    def update_workflow_progress(
        self,
        workflow_id: str,
        progress: float,
        current_step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        更新工作流进度
        
        Args:
            workflow_id: 工作流ID
            progress: 进度（0-100）
            current_step: 当前步骤
            metadata: 元数据
        """
        if not self.observability:
            return
        
        trace = self.workflow_traces.get(workflow_id)
        if not trace:
            return
        
        # 更新长任务进度
        # 需要从metadata中获取long_task_id
        # 这里简化处理，实际应该从context中获取
    
    def _log_event(
        self,
        event_type: WorkflowObservabilityEvent,
        workflow_id: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        request_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """记录事件日志（支持生产模式）"""
        try:
            if self.production_mode and self._production_impl:
                # 使用生产级日志写入
                from .workflow_observability_production import LogLevel, LogEntry
                entry = LogEntry(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    level=LogLevel.INFO.value,
                    event_type=event_type.value,
                    workflow_id=workflow_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    request_id=request_id,
                    data=data or {},
                )
                self._production_impl.log_writer.write(entry)
            else:
                # 使用基础日志写入
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "event_type": event_type.value,
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "request_id": request_id,
                    "data": data or {},
                }
                
                # 写入JSONL文件
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            # 同时写入标准日志
            logger.info(
                f"[{event_type.value}] workflow_id={workflow_id}, trace_id={trace_id}, span_id={span_id}",
                extra={
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "event_type": event_type.value,
                    "data": data,
                },
            )
        except Exception as e:
            logger.error(f"记录事件日志失败: {e}", exc_info=True)
    
    def _record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """记录指标"""
        if not self.observability:
            return
        
        try:
            self.observability.record_metric(
                name=name,
                value=value,
                tags=tags or {},
            )
        except Exception as e:
            logger.error(f"记录指标失败: {e}", exc_info=True)
    
    def _resolve_workflow_id(self, identifier: str) -> Optional[str]:
        """根据 workflow_id 或 trace_id 解析真正的 workflow_id"""
        if identifier in self.workflow_traces:
            return identifier
        return self.trace_index.get(identifier)
    
    def get_workflow_trace(self, workflow_id: str) -> Optional[Trace]:
        """获取工作流Trace"""
        resolved_id = self._resolve_workflow_id(workflow_id)
        if not resolved_id:
            return None
        return self.workflow_traces.get(resolved_id)
    
    def get_workflow_spans(self, workflow_id: str) -> List[Span]:
        """获取工作流所有Span"""
        resolved_id = self._resolve_workflow_id(workflow_id)
        if not resolved_id:
            return []
        return self.workflow_spans.get(resolved_id, [])
    
    def get_workflow_metrics(self, workflow_id: str) -> List[Metric]:
        """获取工作流指标"""
        resolved_id = self._resolve_workflow_id(workflow_id)
        if not resolved_id:
            return []
        return self.workflow_metrics.get(resolved_id, [])
    
    def get_all_workflow_traces(self) -> Dict[str, Trace]:
        """获取所有工作流Trace（用于仪表板）"""
        return self.workflow_traces.copy()
    
    def get_workflow_observability_data(
        self,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        获取工作流完整可观测性数据
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            可观测性数据
        """
        trace = self.get_workflow_trace(workflow_id)
        spans = self.get_workflow_spans(workflow_id)
        metrics = self.get_workflow_metrics(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "trace": trace.to_dict() if trace else None,
            "spans": [span.to_dict() for span in spans],
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "timestamp": m.timestamp,
                    "tags": m.tags,
                }
                for m in metrics
            ],
            "span_count": len(spans),
            "metric_count": len(metrics),
        }


# 单例模式
_workflow_observability: Optional[WorkflowObservability] = None


def get_workflow_observability(
    observability_system: Optional[ObservabilitySystem] = None,
    log_dir: Optional[Path] = None,
    production_mode: bool = True,
) -> WorkflowObservability:
    """
    获取工作流可观测性实例
    
    Args:
        observability_system: 可观测性系统实例
        log_dir: 日志目录
        production_mode: 是否使用生产模式（默认True）
    """
    global _workflow_observability
    if _workflow_observability is None:
        _workflow_observability = WorkflowObservability(
            observability_system=observability_system,
            log_dir=log_dir,
            production_mode=production_mode,
        )
    return _workflow_observability

