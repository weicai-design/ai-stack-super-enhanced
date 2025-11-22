"""
可观测性系统
P0-018: 可观测体系（APM/埋点/长任务进度与回放、统一 requestId/traceId）
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import time
import json
import logging
import asyncio
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class SpanType(Enum):
    """Span类型"""
    HTTP = "http"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL = "external"
    INTERNAL = "internal"
    TASK = "task"


class SpanStatus(Enum):
    """Span状态"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Span:
    """追踪Span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str = ""
    type: SpanType = SpanType.INTERNAL
    status: SpanStatus = SpanStatus.OK
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def finish(self, status: Optional[SpanStatus] = None, error: Optional[str] = None):
        """完成Span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        if status:
            self.status = status
        if error:
            self.error = error
            self.status = SpanStatus.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "logs": self.logs,
            "error": self.error
        }


@dataclass
class Trace:
    """追踪Trace"""
    trace_id: str
    request_id: str
    service_name: str = "super-agent"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    spans: List[Span] = field(default_factory=list)
    tags: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    
    def finish(self, status: str = "ok"):
        """完成Trace"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "service_name": self.service_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "spans": [span.to_dict() for span in self.spans],
            "tags": self.tags,
            "status": self.status
        }


@dataclass
class LongTask:
    """长任务"""
    task_id: str
    trace_id: str
    name: str
    task_type: str
    status: str = "running"  # running, completed, failed, cancelled
    progress: float = 0.0  # 0-100
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    current_step: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    snapshots: List[Dict[str, Any]] = field(default_factory=list)  # 进度快照，用于回放
    
    def update_progress(self, progress: float, step: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """更新进度"""
        self.progress = max(0.0, min(100.0, progress))
        if step:
            self.current_step = step
        
        # 记录快照
        snapshot = {
            "timestamp": time.time(),
            "progress": self.progress,
            "step": step,
            "metadata": metadata or {}
        }
        self.snapshots.append(snapshot)
        
        # 保留最近1000个快照
        if len(self.snapshots) > 1000:
            self.snapshots = self.snapshots[-1000:]
    
    def complete(self, status: str = "completed", error: Optional[str] = None):
        """完成任务"""
        self.status = status
        self.progress = 100.0
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        if error:
            self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "current_step": self.current_step,
            "steps": self.steps,
            "metadata": self.metadata,
            "error": self.error,
            "snapshot_count": len(self.snapshots)
        }
    
    def get_replay_data(self) -> Dict[str, Any]:
        """获取回放数据"""
        return {
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "task_type": self.task_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status,
            "snapshots": self.snapshots,
            "steps": self.steps,
            "error": self.error
        }


@dataclass
class Metric:
    """指标"""
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram, summary


class ObservabilitySystem:
    """
    可观测性系统
    
    功能：
    1. APM（应用性能监控）
    2. 埋点系统
    3. 长任务进度与回放
    4. 统一 requestId/traceId
    """
    
    def __init__(self):
        # Trace存储
        self.traces: Dict[str, Trace] = {}
        self.active_traces: Dict[str, Trace] = {}  # 活跃的Trace
        
        # Span存储
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, Span] = {}  # 活跃的Span
        
        # 长任务存储
        self.long_tasks: Dict[str, LongTask] = {}
        self.active_tasks: Dict[str, LongTask] = {}  # 活跃的任务
        
        # 指标存储
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        # 埋点事件
        self.events: deque = deque(maxlen=50000)
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 配置
        self.max_traces = 10000
        self.max_spans_per_trace = 1000
        self.max_long_tasks = 1000
        self.metric_retention_hours = 24
        
        logger.info("可观测性系统初始化完成")
    
    # ============ 统一 Trace ID 管理 ============
    
    def generate_trace_id(self) -> str:
        """生成Trace ID"""
        return str(uuid.uuid4())
    
    def generate_request_id(self) -> str:
        """生成Request ID"""
        return f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    
    def start_trace(
        self,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_name: str = "super-agent",
        tags: Optional[Dict[str, Any]] = None
    ) -> Trace:
        """
        开始追踪
        
        Args:
            request_id: 请求ID（可选，自动生成）
            trace_id: Trace ID（可选，自动生成）
            service_name: 服务名称
            tags: 标签
            
        Returns:
            Trace对象
        """
        if not request_id:
            request_id = self.generate_request_id()
        if not trace_id:
            trace_id = self.generate_trace_id()
        
        trace = Trace(
            trace_id=trace_id,
            request_id=request_id,
            service_name=service_name,
            tags=tags or {}
        )
        
        with self._lock:
            self.traces[trace_id] = trace
            self.active_traces[trace_id] = trace
            
            # 限制存储大小
            if len(self.traces) > self.max_traces:
                # 移除最旧的已完成Trace
                completed_traces = [
                    (tid, t) for tid, t in self.traces.items()
                    if t.end_time is not None
                ]
                if completed_traces:
                    completed_traces.sort(key=lambda x: x[1].end_time)
                    for tid, _ in completed_traces[:100]:
                        del self.traces[tid]
        
        return trace
    
    def finish_trace(self, trace_id: str, status: str = "ok"):
        """完成追踪"""
        with self._lock:
            trace = self.traces.get(trace_id)
            if trace:
                trace.finish(status)
                if trace_id in self.active_traces:
                    del self.active_traces[trace_id]
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取Trace"""
        return self.traces.get(trace_id)
    
    def get_trace_by_request_id(self, request_id: str) -> Optional[Trace]:
        """根据Request ID获取Trace"""
        for trace in self.traces.values():
            if trace.request_id == request_id:
                return trace
        return None
    
    # ============ Span 管理 ============
    
    def start_span(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType = SpanType.INTERNAL,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Span:
        """
        开始Span
        
        Args:
            trace_id: Trace ID
            name: Span名称
            span_type: Span类型
            parent_span_id: 父Span ID
            tags: 标签
            
        Returns:
            Span对象
        """
        span_id = str(uuid.uuid4())
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            type=span_type,
            tags=tags or {}
        )
        
        with self._lock:
            self.spans[span_id] = span
            self.active_spans[span_id] = span
            
            # 添加到Trace
            trace = self.traces.get(trace_id)
            if trace:
                trace.spans.append(span)
                if len(trace.spans) > self.max_spans_per_trace:
                    trace.spans = trace.spans[-self.max_spans_per_trace:]
        
        return span
    
    def finish_span(
        self,
        span_id: str,
        status: Optional[SpanStatus] = None,
        error: Optional[str] = None
    ):
        """完成Span"""
        with self._lock:
            span = self.spans.get(span_id)
            if span:
                span.finish(status, error)
                if span_id in self.active_spans:
                    del self.active_spans[span_id]
    
    def add_span_log(self, span_id: str, message: str, level: str = "info", **kwargs):
        """添加Span日志"""
        with self._lock:
            span = self.spans.get(span_id)
            if span:
                log_entry = {
                    "timestamp": time.time(),
                    "message": message,
                    "level": level,
                    **kwargs
                }
                span.logs.append(log_entry)
    
    # ============ 长任务管理 ============
    
    def create_long_task(
        self,
        name: str,
        task_type: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LongTask:
        """
        创建长任务
        
        Args:
            name: 任务名称
            task_type: 任务类型
            trace_id: Trace ID（可选）
            metadata: 元数据
            
        Returns:
            LongTask对象
        """
        if not trace_id:
            trace_id = self.generate_trace_id()
        
        task_id = f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        task = LongTask(
            task_id=task_id,
            trace_id=trace_id,
            name=name,
            task_type=task_type,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.long_tasks[task_id] = task
            self.active_tasks[task_id] = task
            
            # 限制存储大小
            if len(self.long_tasks) > self.max_long_tasks:
                # 移除最旧的已完成任务
                completed_tasks = [
                    (tid, t) for tid, t in self.long_tasks.items()
                    if t.end_time is not None
                ]
                if completed_tasks:
                    completed_tasks.sort(key=lambda x: x[1].end_time)
                    for tid, _ in completed_tasks[:100]:
                        del self.long_tasks[tid]
        
        return task
    
    def update_long_task_progress(
        self,
        task_id: str,
        progress: float,
        step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """更新长任务进度"""
        with self._lock:
            task = self.long_tasks.get(task_id)
            if task:
                task.update_progress(progress, step, metadata)
    
    def complete_long_task(
        self,
        task_id: str,
        status: str = "completed",
        error: Optional[str] = None
    ):
        """完成长任务"""
        with self._lock:
            task = self.long_tasks.get(task_id)
            if task:
                task.complete(status, error)
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    def get_long_task(self, task_id: str) -> Optional[LongTask]:
        """获取长任务"""
        return self.long_tasks.get(task_id)
    
    def get_long_task_replay(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取长任务回放数据"""
        task = self.long_tasks.get(task_id)
        if task:
            return task.get_replay_data()
        return None
    
    # ============ 指标管理 ============
    
    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metric_type: str = "gauge"
    ):
        """
        记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            tags: 标签
            metric_type: 指标类型（gauge, counter, histogram, summary）
        """
        metric = Metric(
            name=name,
            value=value,
            tags=tags or {},
            metric_type=metric_type
        )
        
        with self._lock:
            self.metrics[name].append(metric)
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Metric]:
        """
        获取指标
        
        Args:
            name: 指标名称（可选，None表示所有）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            tags: 标签过滤（可选）
            
        Returns:
            指标列表
        """
        if not start_time:
            start_time = time.time() - (self.metric_retention_hours * 3600)
        if not end_time:
            end_time = time.time()
        
        metrics = []
        
        with self._lock:
            if name:
                metric_list = self.metrics.get(name, deque())
            else:
                metric_list = []
                for mlist in self.metrics.values():
                    metric_list.extend(mlist)
            
            for metric in metric_list:
                if start_time <= metric.timestamp <= end_time:
                    if tags:
                        # 检查标签匹配
                        match = all(
                            metric.tags.get(k) == v
                            for k, v in tags.items()
                        )
                        if not match:
                            continue
                    
                    metrics.append(metric)
        
        return sorted(metrics, key=lambda x: x.timestamp)
    
    # ============ 埋点系统 ============
    
    def track_event(
        self,
        event_name: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ):
        """
        埋点事件
        
        Args:
            event_name: 事件名称
            trace_id: Trace ID（可选）
            span_id: Span ID（可选）
            properties: 事件属性
            level: 事件级别
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "event_name": event_name,
            "timestamp": time.time(),
            "trace_id": trace_id,
            "span_id": span_id,
            "properties": properties or {},
            "level": level
        }
        
        with self._lock:
            self.events.append(event)
        
        logger.debug(f"埋点事件: {event_name} (trace_id={trace_id})")
    
    def get_events(
        self,
        event_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取埋点事件
        
        Args:
            event_name: 事件名称（可选）
            trace_id: Trace ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        if not start_time:
            start_time = time.time() - 3600  # 默认最近1小时
        if not end_time:
            end_time = time.time()
        
        events = []
        
        with self._lock:
            for event in reversed(self.events):
                if len(events) >= limit:
                    break
                
                if start_time <= event["timestamp"] <= end_time:
                    if event_name and event["event_name"] != event_name:
                        continue
                    if trace_id and event.get("trace_id") != trace_id:
                        continue
                    
                    events.append(event)
        
        return list(reversed(events))
    
    # ============ 查询和统计 ============
    
    def get_active_traces(self) -> List[Dict[str, Any]]:
        """获取活跃的Trace"""
        with self._lock:
            return [
                {
                    "trace_id": trace.trace_id,
                    "request_id": trace.request_id,
                    "service_name": trace.service_name,
                    "start_time": trace.start_time,
                    "duration": time.time() - trace.start_time if trace.end_time is None else trace.duration,
                    "span_count": len(trace.spans),
                    "status": trace.status
                }
                for trace in self.active_traces.values()
            ]
    
    def get_active_long_tasks(self) -> List[Dict[str, Any]]:
        """获取活跃的长任务"""
        with self._lock:
            return [
                {
                    "task_id": task.task_id,
                    "trace_id": task.trace_id,
                    "name": task.name,
                    "task_type": task.task_type,
                    "status": task.status,
                    "progress": task.progress,
                    "current_step": task.current_step,
                    "duration": time.time() - task.start_time if task.end_time is None else task.duration
                }
                for task in self.active_tasks.values()
            ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "traces": {
                    "total": len(self.traces),
                    "active": len(self.active_traces),
                    "completed": len(self.traces) - len(self.active_traces)
                },
                "spans": {
                    "total": len(self.spans),
                    "active": len(self.active_spans)
                },
                "long_tasks": {
                    "total": len(self.long_tasks),
                    "active": len(self.active_tasks),
                    "completed": len(self.long_tasks) - len(self.active_tasks)
                },
                "metrics": {
                    "count": len(self.metrics),
                    "total_points": sum(len(m) for m in self.metrics.values())
                },
                "events": {
                    "total": len(self.events)
                }
            }
    
    # ============ 上下文管理器 ============
    
    def trace_context(
        self,
        name: str,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_name: str = "super-agent",
        tags: Optional[Dict[str, Any]] = None
    ):
        """Trace上下文管理器"""
        return TraceContext(self, name, request_id, trace_id, service_name, tags)
    
    def span_context(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType = SpanType.INTERNAL,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        """Span上下文管理器"""
        return SpanContext(self, trace_id, name, span_type, parent_span_id, tags)


class TraceContext:
    """Trace上下文管理器"""
    
    def __init__(
        self,
        obs: ObservabilitySystem,
        name: str,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        service_name: str = "super-agent",
        tags: Optional[Dict[str, Any]] = None
    ):
        self.obs = obs
        self.name = name
        self.request_id = request_id
        self.trace_id = trace_id
        self.service_name = service_name
        self.tags = tags
        self.trace = None
    
    def __enter__(self):
        self.trace = self.obs.start_trace(
            request_id=self.request_id,
            trace_id=self.trace_id,
            service_name=self.service_name,
            tags=self.tags
        )
        return self.trace
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.trace:
            status = "error" if exc_type else "ok"
            self.obs.finish_trace(self.trace.trace_id, status)


class SpanContext:
    """Span上下文管理器"""
    
    def __init__(
        self,
        obs: ObservabilitySystem,
        trace_id: str,
        name: str,
        span_type: SpanType = SpanType.INTERNAL,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        self.obs = obs
        self.trace_id = trace_id
        self.name = name
        self.span_type = span_type
        self.parent_span_id = parent_span_id
        self.tags = tags
        self.span = None
    
    def __enter__(self):
        self.span = self.obs.start_span(
            trace_id=self.trace_id,
            name=self.name,
            span_type=self.span_type,
            parent_span_id=self.parent_span_id,
            tags=self.tags
        )
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            status = SpanStatus.ERROR if exc_type else None
            error = str(exc_val) if exc_val else None
            self.obs.finish_span(self.span.span_id, status, error)










