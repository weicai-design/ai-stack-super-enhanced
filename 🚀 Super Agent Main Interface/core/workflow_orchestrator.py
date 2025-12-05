#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流编排器（Workflow Orchestrator）
定义智能线（RAG→专家→模块）与直接操作线的数据结构、状态机，并输出事件。

功能：
1. 智能线：RAG检索 → 专家路由 → 模块执行 → RAG整合 → 响应生成
2. 直接操作线：直接模块执行（跳过RAG和专家路由）
3. 状态机管理：工作流状态转换和生命周期管理
4. 事件输出：通过统一事件总线发布工作流事件
5. 可观测性：trace_id、span_id 埋点，日志写入 logs/workflow/
6. 指标暴露：Prometheus 指标和 JSON API
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest
except ImportError:
    # 如果 prometheus_client 不可用，使用模拟类
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    def generate_latest():
        return b"# Prometheus metrics not available\n"

from .unified_event_bus import (
    UnifiedEventBus,
    UnifiedEvent,
    EventCategory,
    EventSeverity,
)

# 尝试导入生产级可观测性（可选）
try:
    from .workflow_orchestrator_observability import (
        ProductionObservabilityMixin,
        ObservabilityLevel,
        StructuredLogger,
        EnhancedMetrics,
        OpenTelemetryIntegration,
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False
    ProductionObservabilityMixin = None
    ObservabilityLevel = None
    StructuredLogger = None
    EnhancedMetrics = None
    OpenTelemetryIntegration = None

# 配置工作流日志，允许通过环境变量覆盖目录
_default_log_dir = Path(os.environ.get("WORKFLOW_LOG_DIR", "logs/workflow"))
_log_handler: logging.Handler

try:
    _default_log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = _default_log_dir / f"workflow_{datetime.now().strftime('%Y%m%d')}.log"
    _log_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _log_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] trace_id=%(trace_id)s span_id=%(span_id)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
except OSError as exc:
    # 在受限环境（如测试沙箱）无法写入时使用空处理器
    _log_handler = logging.NullHandler()
    logging.getLogger(__name__).warning(
        "无法在 %s 创建工作流日志文件，将使用空日志处理器：%s", _default_log_dir, exc
    )

# 创建专用日志记录器
logger = logging.getLogger("workflow_orchestrator")
logger.setLevel(logging.INFO)
logger.addHandler(_log_handler)
logger.propagate = False  # 避免重复输出到根日志


class _TraceContextFilter(logging.Filter):
    """确保日志记录包含 trace_id/span_id 字段，避免格式化错误"""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = "N/A"
        if not hasattr(record, "span_id"):
            record.span_id = "N/A"
        return True


logger.addFilter(_TraceContextFilter())


class WorkflowType(str, Enum):
    """工作流类型"""
    INTELLIGENT = "intelligent"  # 智能线：RAG→专家→模块
    DIRECT = "direct"  # 直接操作线：直接模块执行


class WorkflowState(str, Enum):
    """工作流状态"""
    INITIALIZED = "initialized"  # 已初始化
    RAG_RETRIEVAL_1 = "rag_retrieval_1"  # 第一次RAG检索（智能线）
    EXPERT_ROUTING = "expert_routing"  # 专家路由（智能线）
    MODULE_EXECUTION = "module_execution"  # 模块执行
    RAG_RETRIEVAL_2 = "rag_retrieval_2"  # 第二次RAG检索（智能线）
    RESPONSE_GENERATION = "response_generation"  # 响应生成
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class WorkflowEventType(str, Enum):
    """工作流事件类型"""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STATE_CHANGED = "workflow.state_changed"
    WORKFLOW_STEP_STARTED = "workflow.step_started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_STEP_FAILED = "workflow.step_failed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    step_name: str
    state: WorkflowState
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[float] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligentWorkflowData:
    """智能线工作流数据"""
    workflow_id: str
    workflow_type: WorkflowType = WorkflowType.INTELLIGENT
    state: WorkflowState = WorkflowState.INITIALIZED
    user_input: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 可观测性字段
    trace_id: Optional[str] = None  # Trace ID
    span_id: Optional[str] = None  # 当前 Span ID
    parent_span_id: Optional[str] = None  # 父 Span ID
    
    # 步骤数据
    rag_result_1: Optional[Dict[str, Any]] = None  # 第一次RAG检索结果
    expert_routing_result: Optional[Dict[str, Any]] = None  # 专家路由结果
    module_execution_result: Optional[Dict[str, Any]] = None  # 模块执行结果
    rag_result_2: Optional[Dict[str, Any]] = None  # 第二次RAG检索结果
    response: Optional[str] = None  # 最终响应
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 步骤记录
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    total_duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "state": self.state.value,
            "user_input": self.user_input,
            "context": self.context,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "rag_result_1": self.rag_result_1,
            "expert_routing_result": self.expert_routing_result,
            "module_execution_result": self.module_execution_result,
            "rag_result_2": self.rag_result_2,
            "response": self.response,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
            "error": self.error,
            "total_duration": self.total_duration,
        }


@dataclass
class DirectWorkflowData:
    """直接操作线工作流数据"""
    workflow_id: str
    workflow_type: WorkflowType = WorkflowType.DIRECT
    state: WorkflowState = WorkflowState.INITIALIZED
    user_input: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # 可观测性字段
    trace_id: Optional[str] = None  # Trace ID
    span_id: Optional[str] = None  # 当前 Span ID
    parent_span_id: Optional[str] = None  # 父 Span ID
    
    # 直接执行数据
    target_module: str = ""  # 目标模块
    module_execution_result: Optional[Dict[str, Any]] = None  # 模块执行结果
    response: Optional[str] = None  # 最终响应
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # 步骤记录
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    total_duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "state": self.state.value,
            "user_input": self.user_input,
            "context": self.context,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "target_module": self.target_module,
            "module_execution_result": self.module_execution_result,
            "response": self.response,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
            "error": self.error,
            "total_duration": self.total_duration,
        }


# 类型别名
WorkflowData = IntelligentWorkflowData | DirectWorkflowData


class WorkflowOrchestrator(
    ProductionObservabilityMixin if OBSERVABILITY_AVAILABLE else object
):
    """
    工作流编排器
    
    功能：
    1. 管理智能线（RAG→专家→模块）和直接操作线的工作流
    2. 实现状态机，控制工作流状态转换
    3. 通过统一事件总线发布工作流事件
    4. 记录工作流执行历史和性能指标
    5. 可观测性：trace_id、span_id 埋点，日志写入 logs/workflow/
    6. 指标暴露：Prometheus 指标和 JSON API
    """

    def __init__(
        self,
        event_bus: Optional[UnifiedEventBus] = None,
        rag_service: Optional[Any] = None,
        expert_router: Optional[Any] = None,
        module_executor: Optional[Any] = None,
        observability_system: Optional[Any] = None,
        enable_production_observability: bool = True,
        observability_level: str = "standard",
        enable_opentelemetry: bool = False,
        otlp_endpoint: Optional[str] = None,
        log_dir: Optional[Path] = None,
    ):
        """
        初始化工作流编排器
        
        Args:
            event_bus: 统一事件总线（可选）
            rag_service: RAG服务适配器（可选）
            expert_router: 专家路由器（可选）
            module_executor: 模块执行器（可选）
            observability_system: 可观测性系统（可选）
        """
        self.event_bus = event_bus
        self.rag_service = rag_service
        self.expert_router = expert_router
        self.module_executor = module_executor
        self.observability = observability_system
        
        # 工作流存储
        self.workflows: Dict[str, WorkflowData] = {}
        self._lock = asyncio.Lock()
        
        # 初始化生产级可观测性
        if enable_production_observability and OBSERVABILITY_AVAILABLE:
            try:
                level = ObservabilityLevel(observability_level) if ObservabilityLevel else ObservabilityLevel.STANDARD
                self._init_observability(
                    log_dir=log_dir,
                    observability_level=level,
                    enable_opentelemetry=enable_opentelemetry,
                    otlp_endpoint=otlp_endpoint,
                )
                self._use_enhanced_metrics = True
            except Exception as e:
                logger.warning(f"初始化生产级可观测性失败: {e}，使用基础版本")
                self._use_enhanced_metrics = False
        else:
            self._use_enhanced_metrics = False
        
        # Prometheus 指标（基础版本，如果未启用增强指标）
        if not self._use_enhanced_metrics:
            # 使用全局标志避免重复注册指标
            if not hasattr(WorkflowOrchestrator, '_metrics_initialized'):
                self.metrics = {
                "workflow_total": Counter(
                    "workflow_orchestrator_total",
                    "Total number of workflows",
                    ["workflow_type", "status"]
                ),
                "workflow_duration": Histogram(
                    "workflow_orchestrator_duration_seconds",
                    "Workflow execution duration in seconds",
                    ["workflow_type", "status"],
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
                ),
                "workflow_active": Gauge(
                    "workflow_orchestrator_active",
                    "Number of active workflows",
                    ["workflow_type", "state"]
                ),
                "workflow_steps_total": Counter(
                    "workflow_orchestrator_steps_total",
                    "Total number of workflow steps",
                    ["workflow_type", "step_name", "status"]
                ),
                }
                WorkflowOrchestrator._metrics_initialized = True
            else:
                # 如果指标已经初始化，使用空字典避免重复注册
                self.metrics = {}
        else:
            # 使用增强指标（在ProductionObservabilityMixin中初始化）
            self.metrics = {}
        
        # 状态转换规则
        self._state_transitions = {
            WorkflowType.INTELLIGENT: {
                WorkflowState.INITIALIZED: [WorkflowState.RAG_RETRIEVAL_1],
                WorkflowState.RAG_RETRIEVAL_1: [WorkflowState.EXPERT_ROUTING, WorkflowState.FAILED],
                WorkflowState.EXPERT_ROUTING: [WorkflowState.MODULE_EXECUTION, WorkflowState.FAILED],
                WorkflowState.MODULE_EXECUTION: [WorkflowState.RAG_RETRIEVAL_2, WorkflowState.FAILED],
                WorkflowState.RAG_RETRIEVAL_2: [WorkflowState.RESPONSE_GENERATION, WorkflowState.FAILED],
                WorkflowState.RESPONSE_GENERATION: [WorkflowState.COMPLETED, WorkflowState.FAILED],
            },
            WorkflowType.DIRECT: {
                WorkflowState.INITIALIZED: [WorkflowState.MODULE_EXECUTION],
                WorkflowState.MODULE_EXECUTION: [WorkflowState.RESPONSE_GENERATION, WorkflowState.FAILED],
                WorkflowState.RESPONSE_GENERATION: [WorkflowState.COMPLETED, WorkflowState.FAILED],
            },
        }

    async def create_intelligent_workflow(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        创建智能线工作流
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            metadata: 元数据
            trace_id: Trace ID（可选，自动生成）
            parent_span_id: 父 Span ID（可选）
            
        Returns:
            工作流ID
        """
        workflow_id = f"wf_intelligent_{uuid4().hex[:12]}"
        
        # 生成或使用传入的 trace_id
        if not trace_id:
            if self.observability:
                trace = self.observability.start_trace(
                    service_name="workflow_orchestrator",
                    tags={"workflow_type": "intelligent"}
                )
                trace_id = trace.trace_id
            else:
                trace_id = str(uuid4())
        
        # 创建 span
        span_id = None
        if self.observability:
            span = self.observability.start_span(
                trace_id=trace_id,
                name=f"workflow.{workflow_id}",
                parent_span_id=parent_span_id,
                tags={"workflow_id": workflow_id, "workflow_type": "intelligent"}
            )
            span_id = span.span_id
        
        workflow = IntelligentWorkflowData(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.INTELLIGENT,
            user_input=user_input,
            context=context or {},
            metadata=metadata or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )
        
        async with self._lock:
            self.workflows[workflow_id] = workflow
        
        # 更新指标
        if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
            self.enhanced_metrics.record_workflow_started("intelligent", trace_id)
        else:
            self.metrics["workflow_total"].labels(
                workflow_type="intelligent",
                status="started"
            ).inc()
            self.metrics["workflow_active"].labels(
                workflow_type="intelligent",
                state="initialized"
            ).inc()
        
        # 记录日志（带 trace_id 和 span_id）
        log_data = {
            "workflow_id": workflow_id,
            "workflow_type": "intelligent",
            "user_input": user_input[:100],  # 限制长度
            "trace_id": trace_id,
            "span_id": span_id,
        }
        
        # 使用结构化日志（如果可用）
        if self._use_enhanced_metrics and hasattr(self, '_log_with_context'):
            self._log_with_context(
                level="info",
                event="workflow.created",
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                data=log_data,
            )
        else:
            self._write_log("workflow.created", log_data, trace_id, span_id)
        
        # 发布事件（带埋点）
        event_success = True
        try:
            await self._publish_event(
                WorkflowEventType.WORKFLOW_STARTED,
                workflow_id=workflow_id,
                workflow_type=WorkflowType.INTELLIGENT.value,
                payload={"user_input": user_input, "context": context, "trace_id": trace_id, "span_id": span_id},
            )
        except Exception as e:
            event_success = False
            logger.error(f"发布工作流启动事件失败: {e}", exc_info=True)
        
        # 记录事件指标
        if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
            self.enhanced_metrics.record_event(
                workflow_type="intelligent",
                event_type=WorkflowEventType.WORKFLOW_STARTED.value,
                success=event_success,
            )
        
        logger.info(
            f"创建智能线工作流: {workflow_id}",
            extra={"trace_id": trace_id, "span_id": span_id}
        )
        return workflow_id

    async def create_direct_workflow(
        self,
        user_input: str,
        target_module: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> str:
        """
        创建直接操作线工作流
        
        Args:
            user_input: 用户输入
            target_module: 目标模块
            context: 上下文信息
            metadata: 元数据
            trace_id: Trace ID（可选，自动生成）
            parent_span_id: 父 Span ID（可选）
            
        Returns:
            工作流ID
        """
        workflow_id = f"wf_direct_{uuid4().hex[:12]}"
        
        # 生成或使用传入的 trace_id
        if not trace_id:
            if self.observability:
                trace = self.observability.start_trace(
                    service_name="workflow_orchestrator",
                    tags={"workflow_type": "direct", "target_module": target_module}
                )
                trace_id = trace.trace_id
            else:
                trace_id = str(uuid4())
        
        # 创建 span
        span_id = None
        if self.observability:
            span = self.observability.start_span(
                trace_id=trace_id,
                name=f"workflow.{workflow_id}",
                parent_span_id=parent_span_id,
                tags={"workflow_id": workflow_id, "workflow_type": "direct", "target_module": target_module}
            )
            span_id = span.span_id
        
        workflow = DirectWorkflowData(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.DIRECT,
            user_input=user_input,
            target_module=target_module,
            context=context or {},
            metadata=metadata or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )
        
        async with self._lock:
            self.workflows[workflow_id] = workflow
        
        # 更新指标
        if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
            self.enhanced_metrics.record_workflow_started("direct", trace_id)
        else:
            self.metrics["workflow_total"].labels(
                workflow_type="direct",
                status="started"
            ).inc()
            self.metrics["workflow_active"].labels(
                workflow_type="direct",
                state="initialized"
            ).inc()
        
        # 记录日志
        log_data = {
            "workflow_id": workflow_id,
            "workflow_type": "direct",
            "target_module": target_module,
            "user_input": user_input[:100],
            "trace_id": trace_id,
            "span_id": span_id,
        }
        
        # 使用结构化日志（如果可用）
        if self._use_enhanced_metrics and hasattr(self, '_log_with_context'):
            self._log_with_context(
                level="info",
                event="workflow.created",
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                data=log_data,
            )
        else:
            self._write_log("workflow.created", log_data, trace_id, span_id)
        
        # 发布事件（带埋点）
        event_success = True
        try:
            await self._publish_event(
                WorkflowEventType.WORKFLOW_STARTED,
                workflow_id=workflow_id,
                workflow_type=WorkflowType.DIRECT.value,
                payload={"user_input": user_input, "target_module": target_module, "context": context, "trace_id": trace_id, "span_id": span_id},
            )
        except Exception as e:
            event_success = False
            logger.error(f"发布工作流启动事件失败: {e}", exc_info=True)
        
        # 记录事件指标
        if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
            self.enhanced_metrics.record_event(
                workflow_type="direct",
                event_type=WorkflowEventType.WORKFLOW_STARTED.value,
                success=event_success,
            )
        
        logger.info(
            f"创建直接操作线工作流: {workflow_id}, 目标模块: {target_module}",
            extra={"trace_id": trace_id, "span_id": span_id}
        )
        return workflow_id

    async def transition_state(
        self,
        workflow_id: str,
        new_state: WorkflowState,
        step_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        状态转换
        
        Args:
            workflow_id: 工作流ID
            new_state: 新状态
            step_data: 步骤数据
            error: 错误信息（如果有）
            
        Returns:
            是否成功转换
        """
        async with self._lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                logger.error(f"工作流不存在: {workflow_id}")
                return False
            
            # 验证状态转换是否合法
            if not self._can_transition(workflow, new_state):
                logger.warning(
                    f"非法状态转换: {workflow_id} {workflow.state.value} -> {new_state.value}"
                )
                return False
            
            old_state = workflow.state
            workflow.state = new_state
            workflow.updated_at = datetime.utcnow().isoformat() + "Z"
            
            if error:
                workflow.error = error
                if new_state == WorkflowState.FAILED:
                    workflow.completed_at = workflow.updated_at
                    if workflow.started_at:
                        start = datetime.fromisoformat(workflow.started_at.replace("Z", "+00:00"))
                        end = datetime.fromisoformat(workflow.completed_at.replace("Z", "+00:00"))
                        workflow.total_duration = (end - start).total_seconds()
            
            # 记录步骤
            if step_data:
                step = WorkflowStep(
                    step_id=f"step_{len(workflow.steps) + 1}",
                    step_name=new_state.value,
                    state=new_state,
                    started_at=step_data.get("started_at"),
                    completed_at=step_data.get("completed_at"),
                    duration=step_data.get("duration"),
                    input_data=step_data.get("input_data", {}),
                    output_data=step_data.get("output_data", {}),
                    error=error,
                    metadata=step_data.get("metadata", {}),
                )
                workflow.steps.append(step)
            
            # 更新工作流特定数据
            if isinstance(workflow, IntelligentWorkflowData):
                if new_state == WorkflowState.RAG_RETRIEVAL_1 and step_data:
                    workflow.rag_result_1 = step_data.get("output_data")
                elif new_state == WorkflowState.EXPERT_ROUTING and step_data:
                    workflow.expert_routing_result = step_data.get("output_data")
                elif new_state == WorkflowState.MODULE_EXECUTION and step_data:
                    workflow.module_execution_result = step_data.get("output_data")
                elif new_state == WorkflowState.RAG_RETRIEVAL_2 and step_data:
                    workflow.rag_result_2 = step_data.get("output_data")
                elif new_state == WorkflowState.RESPONSE_GENERATION and step_data:
                    workflow.response = step_data.get("output_data", {}).get("response")
            elif isinstance(workflow, DirectWorkflowData):
                if new_state == WorkflowState.MODULE_EXECUTION and step_data:
                    workflow.module_execution_result = step_data.get("output_data")
                elif new_state == WorkflowState.RESPONSE_GENERATION and step_data:
                    workflow.response = step_data.get("output_data", {}).get("response")
        
        # 发布状态变更事件
        await self._publish_event(
            WorkflowEventType.WORKFLOW_STATE_CHANGED,
            workflow_id=workflow_id,
            workflow_type=workflow.workflow_type.value,
            payload={
                "old_state": old_state.value,
                "new_state": new_state.value,
                "step_data": step_data,
                "error": error,
            },
        )
        
        # 更新指标
        workflow_type_str = workflow.workflow_type.value
        
        # 计算状态转换持续时间
        transition_duration = 0.0
        if step_data and step_data.get("duration"):
            transition_duration = step_data.get("duration")
        
        if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
            # 使用增强指标
            self.enhanced_metrics.record_state_transition(
                workflow_type=workflow_type_str,
                from_state=old_state.value,
                to_state=new_state.value,
                duration=transition_duration,
                success=not bool(error),
            )
            
            if step_data:
                step_duration = step_data.get("duration", 0.0)
                self.enhanced_metrics.record_step(
                    workflow_type=workflow_type_str,
                    step_name=new_state.value,
                    duration=step_duration,
                    success=not bool(error),
                )
        else:
            # 使用基础指标
            self.metrics["workflow_steps_total"].labels(
                workflow_type=workflow_type_str,
                step_name=new_state.value,
                status="success" if not error else "failed"
            ).inc()
        
        # 如果完成或失败，更新指标并发布事件
        if new_state == WorkflowState.COMPLETED:
            if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
                self.enhanced_metrics.record_workflow_completed(
                    workflow_type=workflow_type_str,
                    duration=workflow.total_duration or 0.0,
                    status="completed",
                )
            else:
                self.metrics["workflow_total"].labels(
                    workflow_type=workflow_type_str,
                    status="completed"
                ).inc()
                self.metrics["workflow_active"].labels(
                    workflow_type=workflow_type_str,
                    state=new_state.value
                ).dec()
                if workflow.total_duration:
                    self.metrics["workflow_duration"].labels(
                        workflow_type=workflow_type_str,
                        status="completed"
                    ).observe(workflow.total_duration)
            
            # 完成 span
            if self.observability and workflow.span_id:
                self.observability.finish_span(workflow.span_id, status="ok")
                if workflow.trace_id:
                    self.observability.finish_trace(workflow.trace_id, status="ok")
            
            await self._publish_event(
                WorkflowEventType.WORKFLOW_COMPLETED,
                workflow_id=workflow_id,
                workflow_type=workflow_type_str,
                payload={"workflow": workflow.to_dict()},
            )
        elif new_state == WorkflowState.FAILED:
            if self._use_enhanced_metrics and hasattr(self, 'enhanced_metrics'):
                self.enhanced_metrics.record_workflow_completed(
                    workflow_type=workflow_type_str,
                    duration=workflow.total_duration or 0.0,
                    status="failed",
                )
                # 记录错误
                error_type = "unknown_error"
                if "timeout" in (error or "").lower():
                    error_type = "timeout"
                elif "state" in (error or "").lower():
                    error_type = "state_transition_error"
                self.enhanced_metrics.record_error(
                    workflow_type=workflow_type_str,
                    error_type=error_type,
                )
            else:
                self.metrics["workflow_total"].labels(
                    workflow_type=workflow_type_str,
                    status="failed"
                ).inc()
                self.metrics["workflow_active"].labels(
                    workflow_type=workflow_type_str,
                    state=new_state.value
                ).dec()
                if workflow.total_duration:
                    self.metrics["workflow_duration"].labels(
                        workflow_type=workflow_type_str,
                        status="failed"
                    ).observe(workflow.total_duration)
            
            # 完成 span（失败）
            if self.observability and workflow.span_id:
                self.observability.finish_span(workflow.span_id, status="error", error=error)
                if workflow.trace_id:
                    self.observability.finish_trace(workflow.trace_id, status="error")
            
            await self._publish_event(
                WorkflowEventType.WORKFLOW_FAILED,
                workflow_id=workflow_id,
                workflow_type=workflow_type_str,
                payload={"workflow": workflow.to_dict(), "error": error},
            )
        
        # 记录日志
        log_data = {
            "workflow_id": workflow_id,
            "old_state": old_state.value,
            "new_state": new_state.value,
            "workflow_type": workflow_type_str,
            "error": error,
            "duration": transition_duration,
        }
        
        # 使用结构化日志（如果可用）
        if self._use_enhanced_metrics and hasattr(self, '_log_with_context'):
            self._log_with_context(
                level="info" if not error else "error",
                event="workflow.state_changed",
                workflow_id=workflow_id,
                trace_id=workflow.trace_id,
                span_id=workflow.span_id,
                data=log_data,
                message=f"状态转换: {old_state.value} -> {new_state.value}",
            )
        else:
            self._write_log("workflow.state_changed", log_data, workflow.trace_id, workflow.span_id)
        
        logger.info(
            f"工作流状态转换: {workflow_id} {old_state.value} -> {new_state.value}",
            extra={"trace_id": workflow.trace_id, "span_id": workflow.span_id}
        )
        return True

    def _can_transition(self, workflow: WorkflowData, new_state: WorkflowState) -> bool:
        """检查状态转换是否合法"""
        transitions = self._state_transitions.get(workflow.workflow_type, {})
        allowed_states = transitions.get(workflow.state, [])
        return new_state in allowed_states

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息"""
        async with self._lock:
            workflow = self.workflows.get(workflow_id)
            return workflow.to_dict() if workflow else None

    async def list_workflows(
        self,
        workflow_type: Optional[WorkflowType] = None,
        state: Optional[WorkflowState] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """列出工作流"""
        async with self._lock:
            workflows = list(self.workflows.values())
            
            # 过滤
            if workflow_type:
                workflows = [w for w in workflows if w.workflow_type == workflow_type]
            if state:
                workflows = [w for w in workflows if w.state == state]
            
            # 排序（最新的在前）
            workflows.sort(key=lambda w: w.created_at, reverse=True)
            
            # 限制数量
            workflows = workflows[:limit]
            
            return [w.to_dict() for w in workflows]

    async def cancel_workflow(self, workflow_id: str, reason: Optional[str] = None) -> bool:
        """取消工作流"""
        async with self._lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return False
            
            if workflow.state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                return False
            
            workflow.state = WorkflowState.CANCELLED
            workflow.updated_at = datetime.utcnow().isoformat() + "Z"
            workflow.completed_at = workflow.updated_at
            if reason:
                workflow.error = reason
        
        await self._publish_event(
            WorkflowEventType.WORKFLOW_CANCELLED,
            workflow_id=workflow_id,
            workflow_type=workflow.workflow_type.value,
            payload={"reason": reason},
        )
        
        logger.info(
            f"取消工作流: {workflow_id}, 原因: {reason}",
            extra={"trace_id": workflow.trace_id, "span_id": workflow.span_id}
        )
        return True
    
    def _write_log(self, event: str, data: Dict[str, Any], trace_id: Optional[str] = None, span_id: Optional[str] = None):
        """写入工作流日志到文件"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event": event,
                "trace_id": trace_id or "unknown",
                "span_id": span_id or "unknown",
                "data": data,
            }
            
            # 写入 JSON 日志文件
            log_file = _default_log_dir / f"workflow_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"写入工作流日志失败: {e}", exc_info=True)
    
    def get_prometheus_metrics(self) -> bytes:
        """获取 Prometheus 格式的指标（增强版）"""
        if self._use_enhanced_metrics and hasattr(self, 'get_enhanced_prometheus_metrics'):
            return self.get_enhanced_prometheus_metrics()
        
        # 回退到基础版本
        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"生成 Prometheus 指标失败: {e}", exc_info=True)
            return b"# Error generating metrics\n"
    
    async def get_metrics_json(self) -> Dict[str, Any]:
        """获取 JSON 格式的指标（增强版）"""
        if self._use_enhanced_metrics and hasattr(self, 'get_enhanced_metrics_json'):
            return self.get_enhanced_metrics_json()
        
        # 回退到基础版本
        try:
            async with self._lock:
                workflows = list(self.workflows.values())
            
            # 统计信息
            total_workflows = len(workflows)
            intelligent_count = sum(1 for w in workflows if w.workflow_type == WorkflowType.INTELLIGENT)
            direct_count = sum(1 for w in workflows if w.workflow_type == WorkflowType.DIRECT)
            
            # 按状态统计
            state_counts = {}
            for state in WorkflowState:
                state_counts[state.value] = sum(1 for w in workflows if w.state == state)
            
            # 按类型和状态统计
            type_state_counts = {}
            for wf_type in WorkflowType:
                type_state_counts[wf_type.value] = {}
                for state in WorkflowState:
                    count = sum(
                        1 for w in workflows
                        if w.workflow_type == wf_type and w.state == state
                    )
                    if count > 0:
                        type_state_counts[wf_type.value][state.value] = count
            
            # 计算平均持续时间
            completed_workflows = [w for w in workflows if w.total_duration is not None]
            avg_duration = (
                sum(w.total_duration for w in completed_workflows) / len(completed_workflows)
                if completed_workflows else 0
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "total_workflows": total_workflows,
                "intelligent_count": intelligent_count,
                "direct_count": direct_count,
                "state_counts": state_counts,
                "type_state_counts": type_state_counts,
                "avg_duration_seconds": avg_duration,
                "completed_count": len(completed_workflows),
                "active_count": sum(1 for w in workflows if w.state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]),
            }
        except Exception as e:
            logger.error(f"获取指标 JSON 失败: {e}", exc_info=True)
            return {"error": str(e)}

    async def _publish_event(
        self,
        event_type: WorkflowEventType,
        workflow_id: str,
        workflow_type: str,
        payload: Dict[str, Any],
        severity: EventSeverity = EventSeverity.INFO,
    ):
        """发布工作流事件"""
        if not self.event_bus:
            return
        
        event = UnifiedEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            category=EventCategory.WORKFLOW,
            event_type=event_type.value,
            source="workflow_orchestrator",
            severity=severity,
            payload={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                **payload,
            },
            correlation_id=workflow_id,
        )
        
        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"发布工作流事件失败: {e}", exc_info=True)

    async def execute_intelligent_workflow(
        self,
        workflow_id: str,
        rag_service: Optional[Any] = None,
        expert_router: Optional[Any] = None,
        module_executor: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        执行智能线工作流（辅助方法）
        
        注意：这是一个简化的执行方法，实际执行逻辑应该在调用方实现
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow or not isinstance(workflow, IntelligentWorkflowData):
            raise ValueError(f"工作流不存在或类型不匹配: {workflow_id}")
        
        if workflow.state != WorkflowState.INITIALIZED:
            raise ValueError(f"工作流状态不正确: {workflow.state.value}")
        
        workflow.started_at = datetime.utcnow().isoformat() + "Z"
        
        # 这里只是示例，实际执行应该由调用方控制
        # 本方法主要用于状态管理和事件发布
        
        return workflow.to_dict()

    async def execute_direct_workflow(
        self,
        workflow_id: str,
        module_executor: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        执行直接操作线工作流（辅助方法）
        
        注意：这是一个简化的执行方法，实际执行逻辑应该在调用方实现
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow or not isinstance(workflow, DirectWorkflowData):
            raise ValueError(f"工作流不存在或类型不匹配: {workflow_id}")
        
        if workflow.state != WorkflowState.INITIALIZED:
            raise ValueError(f"工作流状态不正确: {workflow.state.value}")
        
        workflow.started_at = datetime.utcnow().isoformat() + "Z"
        
        # 这里只是示例，实际执行应该由调用方控制
        # 本方法主要用于状态管理和事件发布
        
        return workflow.to_dict()


# 单例模式
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator(
    event_bus: Optional[UnifiedEventBus] = None,
    rag_service: Optional[Any] = None,
    expert_router: Optional[Any] = None,
    module_executor: Optional[Any] = None,
    observability_system: Optional[Any] = None,
    production_mode: bool = True,
) -> WorkflowOrchestrator:
    """
    获取工作流编排器单例
    
    Args:
        event_bus: 统一事件总线
        rag_service: RAG服务适配器
        expert_router: 专家路由器
        module_executor: 模块执行器
        observability_system: 可观测性系统
        production_mode: 是否使用生产模式（默认True）
    """
    global _workflow_orchestrator
    
    if production_mode:
        # 尝试使用生产级编排器
        try:
            from .workflow_orchestrator_production import (
                get_production_workflow_orchestrator,
            )
            if _workflow_orchestrator is None:
                _workflow_orchestrator = get_production_workflow_orchestrator(
                    event_bus=event_bus,
                    rag_service=rag_service,
                    expert_router=expert_router,
                    module_executor=module_executor,
                    observability_system=observability_system,
                )
            return _workflow_orchestrator
        except ImportError:
            logger.warning("生产级编排器不可用，使用基础版本")
    
    # 使用基础版本
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator(
            event_bus=event_bus,
            rag_service=rag_service,
            expert_router=expert_router,
            module_executor=module_executor,
            observability_system=observability_system,
        )
    return _workflow_orchestrator

