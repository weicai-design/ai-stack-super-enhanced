"""
工作流可观测性生产级增强模块
达到生产水平的日志、指标和链路追踪实现

生产级特性：
1. 异步日志写入和批量处理
2. 日志轮转和压缩
3. 指标聚合和Prometheus导出
4. 采样率控制
5. 错误处理和容错
6. 敏感信息过滤
7. 资源限制和监控
"""

from __future__ import annotations

import asyncio
import logging
import json
import gzip
import time
import threading
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from .observability_system import (
    ObservabilitySystem,
    Span,
    SpanType,
    SpanStatus,
    Trace,
    Metric,
)

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    event_type: str
    workflow_id: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    request_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


class AsyncLogWriter:
    """异步日志写入器（生产级）"""
    
    def __init__(
        self,
        log_dir: Path,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        max_files: int = 30,  # 保留30天
        compress_after_days: int = 7,  # 7天后压缩
    ):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.compress_after_days = compress_after_days
        
        # 日志缓冲区
        self.buffer: deque = deque(maxlen=batch_size * 2)
        self.current_file: Optional[Any] = None
        self.current_file_path: Optional[Path] = None
        self.current_file_size: int = 0
        
        # 线程锁
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._flush_thread: Optional[threading.Thread] = None
        
        # 启动后台线程
        self._start_flush_thread()
        
        logger.info(f"异步日志写入器初始化完成: batch_size={batch_size}, flush_interval={flush_interval}")
    
    def _start_flush_thread(self):
        """启动刷新线程"""
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,
            name="AsyncLogWriter-flush"
        )
        self._flush_thread.start()
    
    def _flush_loop(self):
        """刷新循环"""
        while not self._stop_event.is_set():
            try:
                self._stop_event.wait(self.flush_interval)
                if not self._stop_event.is_set():
                    self.flush()
            except Exception as e:
                logger.error(f"日志刷新循环错误: {e}", exc_info=True)
    
    def write(self, entry: LogEntry):
        """写入日志条目（异步）"""
        try:
            with self._lock:
                self.buffer.append(entry)
                
                # 如果缓冲区满了，立即刷新
                if len(self.buffer) >= self.batch_size:
                    self._flush_buffer()
        except Exception as e:
            logger.error(f"写入日志失败: {e}", exc_info=True)
    
    def _flush_buffer(self):
        """刷新缓冲区到文件"""
        if not self.buffer:
            return
        
        # 获取当前日志文件
        today = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"workflow_observability_{today}.jsonl"
        
        # 如果文件切换，关闭旧文件
        if self.current_file_path != log_file:
            if self.current_file:
                self.current_file.close()
            self.current_file = None
            self.current_file_path = None
            self.current_file_size = 0
        
        # 打开文件（追加模式）
        if not self.current_file:
            self.current_file = open(log_file, "a", encoding="utf-8")
            self.current_file_path = log_file
            self.current_file_size = log_file.stat().st_size if log_file.exists() else 0
        
        # 写入缓冲区中的所有条目
        while self.buffer:
            entry = self.buffer.popleft()
            try:
                log_line = json.dumps({
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "event_type": entry.event_type,
                    "workflow_id": entry.workflow_id,
                    "trace_id": entry.trace_id,
                    "span_id": entry.span_id,
                    "request_id": entry.request_id,
                    "data": entry.data,
                    "message": entry.message,
                }, ensure_ascii=False) + "\n"
                
                self.current_file.write(log_line)
                self.current_file_size += len(log_line.encode("utf-8"))
                
                # 如果文件太大，轮转
                if self.current_file_size >= self.max_file_size:
                    self._rotate_log_file()
            except Exception as e:
                logger.error(f"写入日志条目失败: {e}", exc_info=True)
        
        # 刷新到磁盘
        if self.current_file:
            self.current_file.flush()
    
    def _rotate_log_file(self):
        """轮转日志文件"""
        if not self.current_file:
            return
        
        try:
            self.current_file.close()
            self.current_file = None
            
            # 重命名当前文件
            if self.current_file_path and self.current_file_path.exists():
                rotated_file = self.current_file_path.with_suffix(
                    f".{datetime.now().strftime('%H%M%S')}.jsonl"
                )
                self.current_file_path.rename(rotated_file)
            
            self.current_file_path = None
            self.current_file_size = 0
        except Exception as e:
            logger.error(f"轮转日志文件失败: {e}", exc_info=True)
    
    def flush(self):
        """立即刷新缓冲区"""
        with self._lock:
            self._flush_buffer()
    
    def close(self):
        """关闭写入器"""
        self._stop_event.set()
        if self._flush_thread:
            self._flush_thread.join(timeout=5.0)
        
        self.flush()
        
        if self.current_file:
            self.current_file.close()
            self.current_file = None
        
        # 清理旧文件
        self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_files)
            
            for log_file in self.log_dir.glob("workflow_observability_*.jsonl*"):
                try:
                    # 从文件名提取日期
                    date_str = log_file.stem.split("_")[-1]
                    if len(date_str) == 8:  # YYYYMMDD格式
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        if file_date < cutoff_date:
                            log_file.unlink()
                            logger.debug(f"删除旧日志文件: {log_file}")
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"清理旧日志文件失败: {e}", exc_info=True)
    
    def compress_old_files(self):
        """压缩旧日志文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)
            
            for log_file in self.log_dir.glob("workflow_observability_*.jsonl"):
                if log_file.suffix == ".gz":
                    continue
                
                try:
                    # 从文件名提取日期
                    date_str = log_file.stem.split("_")[-1]
                    if len(date_str) == 8:  # YYYYMMDD格式
                        file_date = datetime.strptime(date_str, "%Y%m%d")
                        if file_date < cutoff_date:
                            # 压缩文件
                            compressed_file = log_file.with_suffix(".jsonl.gz")
                            with open(log_file, "rb") as f_in:
                                with gzip.open(compressed_file, "wb") as f_out:
                                    f_out.writelines(f_in)
                            
                            log_file.unlink()
                            logger.info(f"压缩日志文件: {log_file} -> {compressed_file}")
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"压缩旧日志文件失败: {e}", exc_info=True)


class SensitiveDataFilter:
    """敏感信息过滤器"""
    
    def __init__(self):
        # 敏感字段模式
        self.sensitive_patterns: Set[str] = {
            "password", "passwd", "pwd",
            "token", "api_key", "apikey", "secret",
            "credit_card", "card_number", "cvv",
            "ssn", "social_security",
            "email", "phone", "mobile",
        }
        
        # 脱敏函数
        self.mask_func = self._mask_value
    
    def filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤敏感信息"""
        if not isinstance(data, dict):
            return data
        
        filtered = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # 检查是否是敏感字段
            if any(pattern in key_lower for pattern in self.sensitive_patterns):
                filtered[key] = "***MASKED***"
            elif isinstance(value, dict):
                filtered[key] = self.filter(value)
            elif isinstance(value, list):
                filtered[key] = [self.filter(item) if isinstance(item, dict) else item for item in value]
            else:
                filtered[key] = value
        
        return filtered
    
    def _mask_value(self, value: Any) -> str:
        """脱敏值"""
        if isinstance(value, str):
            if len(value) > 8:
                return value[:2] + "***" + value[-2:]
            return "***"
        return "***"


class SamplingController:
    """采样率控制器"""
    
    def __init__(self, default_sample_rate: float = 1.0):
        """
        初始化采样控制器
        
        Args:
            default_sample_rate: 默认采样率（0.0-1.0）
        """
        self.default_sample_rate = default_sample_rate
        self.sample_rates: Dict[str, float] = {}
    
    def should_sample(
        self,
        workflow_id: str,
        workflow_type: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> bool:
        """
        判断是否应该采样
        
        Args:
            workflow_id: 工作流ID
            workflow_type: 工作流类型
            trace_id: Trace ID
            
        Returns:
            是否应该采样
        """
        # 根据工作流类型获取采样率
        sample_rate = self.sample_rates.get(
            workflow_type or "default",
            self.default_sample_rate
        )
        
        # 使用Trace ID的哈希值进行采样
        if trace_id:
            hash_value = int(hashlib.md5(trace_id.encode()).hexdigest(), 16)
            return (hash_value % 10000) < (sample_rate * 10000)
        
        # 使用工作流ID的哈希值进行采样
        hash_value = int(hashlib.md5(workflow_id.encode()).hexdigest(), 16)
        return (hash_value % 10000) < (sample_rate * 10000)
    
    def set_sample_rate(self, workflow_type: str, rate: float):
        """设置采样率"""
        self.sample_rates[workflow_type] = max(0.0, min(1.0, rate))


class ProductionWorkflowObservability:
    """
    生产级工作流可观测性
    
    特性：
    1. 异步日志写入
    2. 日志轮转和压缩
    3. 敏感信息过滤
    4. 采样率控制
    5. 指标聚合
    6. 错误处理和容错
    """
    
    def __init__(
        self,
        observability_system: Optional[ObservabilitySystem] = None,
        log_dir: Optional[Path] = None,
        enable_sampling: bool = True,
        default_sample_rate: float = 1.0,
        enable_sensitive_filter: bool = True,
        log_level: LogLevel = LogLevel.INFO,
    ):
        """
        初始化生产级可观测性
        
        Args:
            observability_system: 可观测性系统实例
            log_dir: 日志目录
            enable_sampling: 是否启用采样
            default_sample_rate: 默认采样率
            enable_sensitive_filter: 是否启用敏感信息过滤
            log_level: 日志级别
        """
        self.observability = observability_system
        self.log_level = log_level
        
        # 异步日志写入器
        self.log_writer = AsyncLogWriter(
            log_dir=log_dir or Path("logs/workflow"),
        )
        
        # 敏感信息过滤器
        self.sensitive_filter = SensitiveDataFilter() if enable_sensitive_filter else None
        
        # 采样控制器
        self.sampling = SamplingController(default_sample_rate) if enable_sampling else None
        
        # 工作流追踪存储
        self.workflow_traces: Dict[str, Trace] = {}
        self.workflow_spans: Dict[str, List[Span]] = {}
        self.workflow_metrics: Dict[str, List[Metric]] = {}
        
        # 指标聚合
        self.metric_aggregates: Dict[str, Dict[str, Any]] = {}
        
        logger.info("生产级工作流可观测性系统初始化完成")
    
    def start_workflow_trace(
        self,
        workflow_id: str,
        workflow_type: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        开始工作流追踪（生产级）
        
        包含采样控制和敏感信息过滤
        """
        # 采样检查
        if self.sampling and not self.sampling.should_sample(workflow_id, workflow_type, trace_id):
            logger.debug(f"工作流 {workflow_id} 被采样跳过")
            return {
                "workflow_id": workflow_id,
                "sampled": False,
            }
        
        try:
            if not self.observability:
                return {
                    "workflow_id": workflow_id,
                    "sampled": True,
                    "trace_id": trace_id or f"trace_{workflow_id}",
                }
            
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
            
            # 过滤敏感信息
            filtered_context = self.sensitive_filter.filter(context or {}) if self.sensitive_filter else context
            
            # 记录日志
            self._log_event(
                LogLevel.INFO,
                "workflow.started",
                workflow_id=workflow_id,
                trace_id=trace.trace_id,
                request_id=trace.request_id,
                data={
                    "workflow_type": workflow_type,
                    "user_input_length": len(user_input),
                    "context": filtered_context,
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
            
            return {
                "workflow_id": workflow_id,
                "sampled": True,
                "trace_id": trace.trace_id,
                "request_id": trace.request_id,
            }
        except Exception as e:
            logger.error(f"开始工作流追踪失败: {e}", exc_info=True)
            return {
                "workflow_id": workflow_id,
                "sampled": True,
                "error": str(e),
            }
    
    def _log_event(
        self,
        level: LogLevel,
        event_type: str,
        workflow_id: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        request_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ):
        """记录事件日志（生产级）"""
        try:
            # 过滤敏感信息
            filtered_data = self.sensitive_filter.filter(data or {}) if self.sensitive_filter else (data or {})
            
            entry = LogEntry(
                timestamp=datetime.utcnow().isoformat() + "Z",
                level=level.value,
                event_type=event_type,
                workflow_id=workflow_id,
                trace_id=trace_id,
                span_id=span_id,
                request_id=request_id,
                data=filtered_data,
                message=message,
            )
            
            # 异步写入
            self.log_writer.write(entry)
        except Exception as e:
            logger.error(f"记录事件日志失败: {e}", exc_info=True)
    
    def _record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
    ):
        """记录指标（生产级，带聚合）"""
        if not self.observability:
            return
        
        try:
            # 记录到可观测性系统
            self.observability.record_metric(
                name=name,
                value=value,
                tags=tags or {},
            )
            
            # 聚合指标
            metric_key = f"{name}_{json.dumps(tags or {}, sort_keys=True)}"
            if metric_key not in self.metric_aggregates:
                self.metric_aggregates[metric_key] = {
                    "name": name,
                    "tags": tags or {},
                    "count": 0,
                    "sum": 0.0,
                    "min": float("inf"),
                    "max": float("-inf"),
                    "last_update": time.time(),
                }
            
            agg = self.metric_aggregates[metric_key]
            agg["count"] += 1
            agg["sum"] += value
            agg["min"] = min(agg["min"], value)
            agg["max"] = max(agg["max"], value)
            agg["last_update"] = time.time()
        except Exception as e:
            logger.error(f"记录指标失败: {e}", exc_info=True)
    
    def get_metric_aggregates(self) -> Dict[str, Dict[str, Any]]:
        """获取指标聚合数据"""
        return self.metric_aggregates.copy()
    
    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        lines = []
        
        for metric_key, agg in self.metric_aggregates.items():
            name = agg["name"].replace(".", "_")
            tags = agg["tags"]
            
            # 构建标签字符串
            tag_str = ",".join([f'{k}="{v}"' for k, v in tags.items()])
            if tag_str:
                tag_str = "{" + tag_str + "}"
            
            # 输出各种聚合指标
            lines.append(f"# TYPE {name}_count counter")
            lines.append(f"{name}_count{tag_str} {agg['count']}")
            
            lines.append(f"# TYPE {name}_sum counter")
            lines.append(f"{name}_sum{tag_str} {agg['sum']}")
            
            if agg["count"] > 0:
                lines.append(f"# TYPE {name}_avg gauge")
                lines.append(f"{name}_avg{tag_str} {agg['sum'] / agg['count']}")
            
            if agg["min"] != float("inf"):
                lines.append(f"# TYPE {name}_min gauge")
                lines.append(f"{name}_min{tag_str} {agg['min']}")
            
            if agg["max"] != float("-inf"):
                lines.append(f"# TYPE {name}_max gauge")
                lines.append(f"{name}_max{tag_str} {agg['max']}")
        
        return "\n".join(lines)
    
    def close(self):
        """关闭可观测性系统"""
        self.log_writer.close()
        logger.info("生产级工作流可观测性系统已关闭")


# 单例模式
_production_observability: Optional[ProductionWorkflowObservability] = None


def get_production_workflow_observability(
    observability_system: Optional[ObservabilitySystem] = None,
    log_dir: Optional[Path] = None,
    enable_sampling: bool = True,
    default_sample_rate: float = 1.0,
    enable_sensitive_filter: bool = True,
    log_level: LogLevel = LogLevel.INFO,
) -> ProductionWorkflowObservability:
    """获取生产级工作流可观测性实例"""
    global _production_observability
    if _production_observability is None:
        _production_observability = ProductionWorkflowObservability(
            observability_system=observability_system,
            log_dir=log_dir,
            enable_sampling=enable_sampling,
            default_sample_rate=default_sample_rate,
            enable_sensitive_filter=enable_sensitive_filter,
            log_level=log_level,
        )
    return _production_observability

