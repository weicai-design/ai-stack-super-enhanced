"""
工作流编排器可观测性增强模块
生产级的埋点、日志和指标实现

功能：
1. 完整的 trace_id、span_id 埋点
2. 结构化日志（JSON格式）
3. Prometheus 指标增强
4. JSON API 指标端点
5. OpenTelemetry 集成（可选）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# 使用类型提示避免循环导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .workflow_orchestrator import (
        WorkflowOrchestrator,
        WorkflowType,
        WorkflowState,
        WorkflowEventType,
        WorkflowData,
    )

logger = logging.getLogger(__name__)


# 尝试导入 OpenTelemetry（可选）
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None


class ObservabilityLevel(str, Enum):
    """可观测性级别"""
    MINIMAL = "minimal"  # 最小埋点
    STANDARD = "standard"  # 标准埋点
    DETAILED = "detailed"  # 详细埋点
    FULL = "full"  # 完整埋点


class StructuredLogger:
    """结构化日志记录器（生产级）"""
    
    def __init__(
        self,
        log_dir: Path,
        log_level: str = "INFO",
        enable_sampling: bool = False,
        sample_rate: float = 1.0,
    ):
        """
        初始化结构化日志记录器
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
            enable_sampling: 是否启用采样
            sample_rate: 采样率（0.0-1.0）
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_sampling = enable_sampling
        self.sample_rate = sample_rate
        
        # 日志文件
        self.log_file = self.log_dir / f"workflow_orchestrator_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        logger.info(f"结构化日志记录器初始化完成: {self.log_dir}")
    
    def log(
        self,
        level: str,
        event: str,
        workflow_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        """
        记录结构化日志
        
        Args:
            level: 日志级别
            event: 事件名称
            workflow_id: 工作流ID
            trace_id: Trace ID
            span_id: Span ID
            data: 附加数据
            message: 消息
        """
        try:
            # 采样检查
            if self.enable_sampling:
                import random
                if random.random() > self.sample_rate:
                    return
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": level.upper(),
                "event": event,
                "workflow_id": workflow_id,
                "trace_id": trace_id or "unknown",
                "span_id": span_id or "unknown",
                "data": data or {},
                "message": message,
            }
            
            # 写入 JSONL 文件
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            # 同时写入标准日志
            log_func = getattr(logger, level.lower(), logger.info)
            log_func(
                f"[{event}] workflow_id={workflow_id}, trace_id={trace_id}, span_id={span_id}",
                extra={
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "event": event,
                    "data": data,
                },
            )
        except Exception as e:
            logger.error(f"记录结构化日志失败: {e}", exc_info=True)


class EnhancedMetrics:
    """增强的指标收集器"""
    
    def __init__(self):
        """初始化指标收集器"""
        try:
            from prometheus_client import Counter, Histogram, Gauge, Summary
            self.Counter = Counter
            self.Histogram = Histogram
            self.Gauge = Gauge
            self.Summary = Summary
            self.PROMETHEUS_AVAILABLE = True
        except ImportError:
            self.PROMETHEUS_AVAILABLE = False
            # 使用模拟类
            class MockMetric:
                def __init__(self, *args, **kwargs):
                    pass
                def labels(self, *args, **kwargs):
                    return self
                def inc(self, *args, **kwargs):
                    pass
                def observe(self, *args, **kwargs):
                    pass
                def set(self, *args, **kwargs):
                    pass
            
            self.Counter = MockMetric
            self.Histogram = MockMetric
            self.Gauge = MockMetric
            self.Summary = MockMetric
        
        # 指标定义
        self.metrics = self._init_metrics()
        
        # 指标聚合数据
        self.metric_aggregates: Dict[str, Dict[str, Any]] = {}
    
    def _init_metrics(self) -> Dict[str, Any]:
        """初始化指标"""
        if not self.PROMETHEUS_AVAILABLE:
            return {}
        
        # 使用全局标志避免重复注册指标
        if not hasattr(ProductionObservabilityMixin, '_metrics_initialized'):
            metrics = {
                # 工作流计数
                "workflow_total": self.Counter(
                    "workflow_orchestrator_total",
                    "Total number of workflows",
                    ["workflow_type", "status", "state"]
                ),
                
                # 工作流持续时间
                "workflow_duration": self.Histogram(
                    "workflow_orchestrator_duration_seconds",
                    "Workflow execution duration in seconds",
                    ["workflow_type", "status"],
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
                ),
                
                # 活跃工作流
                "workflow_active": self.Gauge(
                    "workflow_orchestrator_active",
                    "Number of active workflows",
                    ["workflow_type", "state"]
                ),
                
                # 工作流步骤
                "workflow_steps_total": self.Counter(
                    "workflow_orchestrator_steps_total",
                    "Total number of workflow steps",
                    ["workflow_type", "step_name", "status"]
                ),
                
                # 步骤持续时间
                "workflow_step_duration": self.Histogram(
                    "workflow_orchestrator_step_duration_seconds",
                    "Workflow step execution duration in seconds",
                    ["workflow_type", "step_name"],
                    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
                ),
                
                # 状态转换
                "workflow_state_transitions_total": self.Counter(
                    "workflow_orchestrator_state_transitions_total",
                    "Total number of state transitions",
                    ["workflow_type", "from_state", "to_state", "status"]
                ),
                
                # 错误计数
                "workflow_errors_total": self.Counter(
                    "workflow_orchestrator_errors_total",
                    "Total number of workflow errors",
                    ["workflow_type", "error_type"]
                ),
                
                # 事件发布
                "workflow_events_total": self.Counter(
                    "workflow_orchestrator_events_total",
                    "Total number of workflow events",
                    ["workflow_type", "event_type", "status"]
                ),
            }
            ProductionObservabilityMixin._metrics_initialized = True
            return metrics
        else:
            # 如果指标已经初始化，返回空字典避免重复注册
            return {}
    
    def record_workflow_started(
        self,
        workflow_type: str,
        trace_id: Optional[str] = None,
    ):
        """记录工作流启动"""
        if "workflow_total" in self.metrics:
            self.metrics["workflow_total"].labels(
                workflow_type=workflow_type,
                status="started",
                state="initialized"
            ).inc()
        
        if "workflow_active" in self.metrics:
            self.metrics["workflow_active"].labels(
                workflow_type=workflow_type,
                state="initialized"
            ).inc()
    
    def record_workflow_completed(
        self,
        workflow_type: str,
        duration: float,
        status: str = "completed",
    ):
        """记录工作流完成"""
        if "workflow_total" in self.metrics:
            self.metrics["workflow_total"].labels(
                workflow_type=workflow_type,
                status=status,
                state="completed"
            ).inc()
        
        if "workflow_duration" in self.metrics:
            self.metrics["workflow_duration"].labels(
                workflow_type=workflow_type,
                status=status
            ).observe(duration)
        
        if "workflow_active" in self.metrics:
            self.metrics["workflow_active"].labels(
                workflow_type=workflow_type,
                state="completed"
            ).dec()
    
    def record_state_transition(
        self,
        workflow_type: str,
        from_state: str,
        to_state: str,
        duration: float = 0.0,
        success: bool = True,
    ):
        """记录状态转换"""
        if "workflow_state_transitions_total" in self.metrics:
            self.metrics["workflow_state_transitions_total"].labels(
                workflow_type=workflow_type,
                from_state=from_state,
                to_state=to_state,
                status="success" if success else "failed"
            ).inc()
        
        if "workflow_active" in self.metrics:
            # 更新活跃工作流状态
            self.metrics["workflow_active"].labels(
                workflow_type=workflow_type,
                state=from_state
            ).dec()
            self.metrics["workflow_active"].labels(
                workflow_type=workflow_type,
                state=to_state
            ).inc()
    
    def record_step(
        self,
        workflow_type: str,
        step_name: str,
        duration: float,
        success: bool = True,
    ):
        """记录步骤执行"""
        if "workflow_steps_total" in self.metrics:
            self.metrics["workflow_steps_total"].labels(
                workflow_type=workflow_type,
                step_name=step_name,
                status="success" if success else "failed"
            ).inc()
        
        if "workflow_step_duration" in self.metrics:
            self.metrics["workflow_step_duration"].labels(
                workflow_type=workflow_type,
                step_name=step_name
            ).observe(duration)
    
    def record_error(
        self,
        workflow_type: str,
        error_type: str,
    ):
        """记录错误"""
        if "workflow_errors_total" in self.metrics:
            self.metrics["workflow_errors_total"].labels(
                workflow_type=workflow_type,
                error_type=error_type
            ).inc()
    
    def record_event(
        self,
        workflow_type: str,
        event_type: str,
        success: bool = True,
    ):
        """记录事件发布"""
        if "workflow_events_total" in self.metrics:
            self.metrics["workflow_events_total"].labels(
                workflow_type=workflow_type,
                event_type=event_type,
                status="success" if success else "failed"
            ).inc()
    
    def get_prometheus_metrics(self) -> bytes:
        """获取 Prometheus 格式的指标"""
        if not self.PROMETHEUS_AVAILABLE:
            return b"# Prometheus metrics not available\n"
        
        try:
            from prometheus_client import generate_latest
            return generate_latest()
        except Exception as e:
            logger.error(f"生成 Prometheus 指标失败: {e}", exc_info=True)
            return b"# Error generating metrics\n"
    
    def get_metrics_json(self, workflows: List[Any]) -> Dict[str, Any]:
        """获取 JSON 格式的指标"""
        try:
            # 延迟导入避免循环
            from .workflow_orchestrator import WorkflowType, WorkflowState
            
            # 基础统计
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
            
            # 步骤统计
            step_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "avg_duration": 0.0})
            for workflow in workflows:
                for step in workflow.steps:
                    step_name = step.step_name
                    step_stats[step_name]["total"] += 1
                    if step.error:
                        step_stats[step_name]["failed"] += 1
                    else:
                        step_stats[step_name]["success"] += 1
                    if step.duration:
                        current_avg = step_stats[step_name]["avg_duration"]
                        count = step_stats[step_name]["total"]
                        step_stats[step_name]["avg_duration"] = (
                            (current_avg * (count - 1) + step.duration) / count
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
                "active_count": sum(
                    1 for w in workflows
                    if w.state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]
                ),
                "step_stats": dict(step_stats),
            }
        except Exception as e:
            logger.error(f"获取指标 JSON 失败: {e}", exc_info=True)
            return {"error": str(e)}


class OpenTelemetryIntegration:
    """OpenTelemetry 集成（可选）"""
    
    def __init__(
        self,
        service_name: str = "workflow-orchestrator",
        enable: bool = True,
        otlp_endpoint: Optional[str] = None,
    ):
        """
        初始化 OpenTelemetry 集成
        
        Args:
            service_name: 服务名称
            enable: 是否启用
            otlp_endpoint: OTLP 端点（可选）
        """
        self.enable = enable and OPENTELEMETRY_AVAILABLE
        self.service_name = service_name
        self.tracer = None
        
        if self.enable:
            try:
                # 创建 TracerProvider
                resource = Resource.create({
                    "service.name": service_name,
                    "service.version": "1.0.0",
                })
                
                provider = TracerProvider(resource=resource)
                
                # 添加导出器（如果提供了端点）
                if otlp_endpoint:
                    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                    provider.add_span_processor(BatchSpanProcessor(exporter))
                
                # 设置全局 TracerProvider
                trace.set_tracer_provider(provider)
                
                # 获取 Tracer
                self.tracer = trace.get_tracer(service_name)
                
                logger.info(f"OpenTelemetry 集成初始化完成: {service_name}")
            except Exception as e:
                logger.warning(f"OpenTelemetry 集成初始化失败: {e}")
                self.enable = False
    
    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """开始 Span"""
        if not self.enable or not self.tracer:
            return None
        
        try:
            # 如果有父 Span，创建子 Span
            if parent_span_id:
                # 这里简化处理，实际应该从上下文获取
                span = self.tracer.start_span(name, attributes=attributes or {})
            else:
                span = self.tracer.start_span(name, attributes=attributes or {})
            
            return span
        except Exception as e:
            logger.error(f"创建 OpenTelemetry Span 失败: {e}", exc_info=True)
            return None
    
    def end_span(self, span, status: str = "ok", error: Optional[str] = None):
        """结束 Span"""
        if not span:
            return
        
        try:
            if error:
                span.record_exception(Exception(error))
                span.set_status(trace.Status(trace.StatusCode.ERROR, error))
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))
            span.end()
        except Exception as e:
            logger.error(f"结束 OpenTelemetry Span 失败: {e}", exc_info=True)


class ProductionObservabilityMixin:
    """
    生产级可观测性混入类
    
    为工作流编排器添加完整的可观测性支持
    """
    
    def _init_observability(
        self,
        log_dir: Optional[Path] = None,
        observability_level: ObservabilityLevel = ObservabilityLevel.STANDARD,
        enable_opentelemetry: bool = False,
        otlp_endpoint: Optional[str] = None,
        enable_log_sampling: bool = False,
        log_sample_rate: float = 1.0,
    ):
        """
        初始化可观测性
        
        Args:
            log_dir: 日志目录
            observability_level: 可观测性级别
            enable_opentelemetry: 是否启用 OpenTelemetry
            otlp_endpoint: OTLP 端点
            enable_log_sampling: 是否启用日志采样
            log_sample_rate: 日志采样率
        """
        # 结构化日志
        log_path = log_dir or Path("logs/workflow")
        self.structured_logger = StructuredLogger(
            log_dir=log_path,
            log_level="INFO",
            enable_sampling=enable_log_sampling,
            sample_rate=log_sample_rate,
        )
        
        # 增强指标
        self.enhanced_metrics = EnhancedMetrics()
        
        # OpenTelemetry 集成（可选）
        self.otel = None
        if enable_opentelemetry:
            self.otel = OpenTelemetryIntegration(
                service_name="workflow-orchestrator",
                enable=True,
                otlp_endpoint=otlp_endpoint,
            )
        
        self.observability_level = observability_level
        
        logger.info(f"生产级可观测性初始化完成: level={observability_level.value}")
    
    def _log_with_context(
        self,
        level: str,
        event: str,
        workflow_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        """带上下文的日志记录"""
        if hasattr(self, 'structured_logger'):
            self.structured_logger.log(
                level=level,
                event=event,
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                data=data,
                message=message,
            )
        else:
            # 回退到基础日志
            logger.info(
                f"[{event}] workflow_id={workflow_id}, trace_id={trace_id}, span_id={span_id}",
                extra={
                    "workflow_id": workflow_id,
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            )
    
    def _create_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """创建 Span（支持 OpenTelemetry）"""
        span = None
        
        # OpenTelemetry Span
        if hasattr(self, 'otel') and self.otel:
            span = self.otel.start_span(
                name=name,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                attributes=attributes or {},
            )
        
        return span
    
    def _end_span(
        self,
        span,
        status: str = "ok",
        error: Optional[str] = None,
    ):
        """结束 Span"""
        if hasattr(self, 'otel') and self.otel and span:
            self.otel.end_span(span, status=status, error=error)
    
    def get_enhanced_prometheus_metrics(self) -> bytes:
        """获取增强的 Prometheus 指标"""
        if hasattr(self, 'enhanced_metrics'):
            return self.enhanced_metrics.get_prometheus_metrics()
        return b"# Metrics not available\n"
    
    def get_enhanced_metrics_json(self) -> Dict[str, Any]:
        """获取增强的 JSON 指标"""
        if hasattr(self, 'enhanced_metrics'):
            # 延迟导入避免循环
            from .workflow_orchestrator import WorkflowType, WorkflowState
            workflows = list(self.workflows.values()) if hasattr(self, 'workflows') else []
            return self.enhanced_metrics.get_metrics_json(workflows)
        return {"error": "Metrics not available"}

