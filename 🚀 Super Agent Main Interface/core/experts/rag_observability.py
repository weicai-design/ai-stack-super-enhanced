"""
RAG专家可观测性系统
为RAG专家模块提供生产级健康检查、追踪和日志支持
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from contextlib import contextmanager
import uuid
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class TracingContext:
    """追踪上下文"""
    
    def __init__(self, trace_id: Optional[str] = None, span_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id: Optional[str] = None
        self.tags: Dict[str, Any] = {}
        self.baggage: Dict[str, str] = {}
    
    def create_child_context(self) -> 'TracingContext':
        """创建子上下文"""
        child = TracingContext(self.trace_id)
        child.parent_span_id = self.span_id
        child.baggage = self.baggage.copy()
        return child
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "tags": self.tags,
            "baggage": self.baggage
        }


class Span:
    """追踪Span"""
    
    def __init__(self, name: str, context: TracingContext):
        self.name = name
        self.context = context
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.status: str = "ok"
        self.error: Optional[str] = None
    
    def finish(self, status: str = "ok", error: Optional[str] = None):
        """完成Span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error = error
    
    def add_tag(self, key: str, value: Any):
        """添加标签"""
        self.tags[key] = value
    
    def add_log(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """添加日志"""
        log_entry = {
            "timestamp": time.time(),
            "message": message,
            "fields": fields or {}
        }
        self.logs.append(log_entry)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "context": self.context.to_dict(),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "logs": self.logs,
            "status": self.status,
            "error": self.error
        }


class RAGTracer:
    """RAG追踪器"""
    
    def __init__(self):
        self._spans: List[Span] = []
        self._lock = threading.RLock()
        self._exporters: List[Callable[[List[Span]], None]] = []
    
    @contextmanager
    def start_span(self, name: str, context: Optional[TracingContext] = None):
        """启动Span的上下文管理器"""
        if context is None:
            context = TracingContext()
        
        span = Span(name, context)
        
        try:
            yield span
            span.finish("ok")
        except Exception as e:
            span.finish("error", str(e))
            raise
        finally:
            with self._lock:
                self._spans.append(span)
                # 限制Span数量
                if len(self._spans) > 1000:
                    self._spans = self._spans[-1000:]
    
    def get_spans(self, trace_id: Optional[str] = None) -> List[Span]:
        """获取Span"""
        with self._lock:
            if trace_id:
                return [span for span in self._spans if span.context.trace_id == trace_id]
            return self._spans.copy()
    
    def register_exporter(self, exporter: Callable[[List[Span]], None]):
        """注册Span导出器"""
        self._exporters.append(exporter)
    
    def export_spans(self):
        """导出Span"""
        spans = self.get_spans()
        for exporter in self._exporters:
            try:
                exporter(spans)
            except Exception as e:
                logger.error(f"Span导出失败: {e}")
    
    def clear_spans(self):
        """清除Span"""
        with self._lock:
            self._spans.clear()


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, context: Optional[TracingContext] = None):
        self.name = name
        self.context = context or TracingContext()
        self.logger = logging.getLogger(name)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self._log("DEBUG", message, kwargs)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self._log("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self._log("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self._log("ERROR", message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self._log("CRITICAL", message, kwargs)
    
    def _log(self, level: str, message: str, fields: Dict[str, Any]):
        """记录日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "fields": fields
        }
        
        # 转换为JSON格式
        log_json = json.dumps(log_entry, ensure_ascii=False, default=str)
        
        # 使用适当的日志级别记录
        if level == "DEBUG":
            self.logger.debug(log_json)
        elif level == "INFO":
            self.logger.info(log_json)
        elif level == "WARNING":
            self.logger.warning(log_json)
        elif level == "ERROR":
            self.logger.error(log_json)
        elif level == "CRITICAL":
            self.logger.critical(log_json)


class RAGHealthCheckAPI:
    """RAG健康检查API"""
    
    def __init__(self, monitoring_system):
        self.monitoring_system = monitoring_system
        self._custom_checks: Dict[str, Callable[[], Dict[str, Any]]] = {}
    
    def register_custom_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """注册自定义健康检查"""
        self._custom_checks[name] = check_func
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            # 执行系统健康检查
            system_health = self.monitoring_system.get_health_status()
            
            # 执行自定义健康检查
            custom_checks = {}
            for name, check_func in self._custom_checks.items():
                try:
                    custom_checks[name] = check_func()
                except Exception as e:
                    custom_checks[name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            response = {
                "status": system_health["status"],
                "timestamp": datetime.now().isoformat(),
                "duration_ms": (time.time() - start_time) * 1000,
                "system": system_health,
                "custom": custom_checks
            }
            
            return response
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """执行就绪检查"""
        health_status = await self.health_check()
        
        # 就绪检查比健康检查更严格
        if health_status["status"] in ["healthy", "degraded"]:
            return {
                "status": "ready",
                "timestamp": health_status["timestamp"]
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": health_status["timestamp"],
                "reason": "系统不健康"
            }
    
    async def liveness_check(self) -> Dict[str, Any]:
        """执行存活检查"""
        # 存活检查只需要确认进程还在运行
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }


class RAGMetricsAPI:
    """RAG指标API"""
    
    def __init__(self, monitoring_system):
        self.monitoring_system = monitoring_system
    
    async def get_metrics(self, format: str = "prometheus") -> str:
        """获取指标"""
        if format == "prometheus":
            return self.monitoring_system.metrics_collector.get_prometheus_metrics()
        elif format == "json":
            metrics = self.monitoring_system.metrics_collector.get_metrics()
            return json.dumps([m.to_dict() for m in metrics], indent=2, default=str)
        else:
            raise ValueError(f"不支持的指标格式: {format}")
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        metrics = self.monitoring_system.metrics_collector.get_metrics()
        
        # 计算基本统计信息
        request_metrics = [m for m in metrics if m.name == "rag_request_duration_seconds"]
        durations = [m.value for m in request_metrics]
        
        summary = {
            "total_requests": len(request_metrics),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return summary


class RAGObservabilitySystem:
    """RAG可观测性系统"""
    
    def __init__(self):
        from .rag_monitoring import get_monitoring_system
        
        self.monitoring_system = get_monitoring_system()
        self.tracer = RAGTracer()
        self.health_api = RAGHealthCheckAPI(self.monitoring_system)
        self.metrics_api = RAGMetricsAPI(self.monitoring_system)
        
        # 注册默认Span导出器
        self._register_default_exporters()
    
    def _register_default_exporters(self):
        """注册默认导出器"""
        # JSON文件导出器
        def json_exporter(spans: List[Span]):
            if spans:
                span_data = [span.to_dict() for span in spans]
                try:
                    import os
                    from pathlib import Path
                    
                    logs_dir = Path("/tmp/rag_traces")
                    logs_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = logs_dir / f"spans_{timestamp}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(span_data, f, indent=2, ensure_ascii=False, default=str)
                    
                except Exception as e:
                    logger.error(f"Span JSON导出失败: {e}")
        
        self.tracer.register_exporter(json_exporter)
    
    def create_logger(self, name: str, context: Optional[TracingContext] = None) -> StructuredLogger:
        """创建结构化日志记录器"""
        return StructuredLogger(name, context)
    
    @contextmanager
    def trace_operation(self, operation_name: str, context: Optional[TracingContext] = None):
        """追踪操作的上下文管理器"""
        with self.tracer.start_span(operation_name, context) as span:
            # 创建带追踪上下文的日志记录器
            logger = self.create_logger(__name__, span.context)
            
            try:
                yield span, logger
            except Exception as e:
                span.add_tag("error", True)
                logger.error(f"操作失败: {operation_name}", error=str(e))
                raise
    
    async def start_observability_services(self, host: str = "0.0.0.0", port: int = 8080):
        """启动可观测性服务"""
        try:
            import uvicorn
            from fastapi import FastAPI
            
            app = FastAPI(title="RAG Observability API")
            
            @app.get("/health")
            async def health():
                return await self.health_api.health_check()
            
            @app.get("/ready")
            async def ready():
                return await self.health_api.readiness_check()
            
            @app.get("/alive")
            async def alive():
                return await self.health_api.liveness_check()
            
            @app.get("/metrics")
            async def metrics(format: str = "prometheus"):
                return await self.metrics_api.get_metrics(format)
            
            @app.get("/metrics/summary")
            async def metrics_summary():
                return await self.metrics_api.get_metrics_summary()
            
            # 启动服务
            config = uvicorn.Config(app, host=host, port=port, log_level="info")
            server = uvicorn.Server(config)
            
            await server.serve()
            
        except ImportError:
            logger.warning("FastAPI/uvicorn未安装，无法启动可观测性API")
        except Exception as e:
            logger.error(f"启动可观测性服务失败: {e}")


# 全局可观测性系统实例
_observability_system: Optional[RAGObservabilitySystem] = None


def get_observability_system() -> RAGObservabilitySystem:
    """获取全局可观测性系统"""
    global _observability_system
    if _observability_system is None:
        _observability_system = RAGObservabilitySystem()
    return _observability_system


def create_logger(name: str, context: Optional[TracingContext] = None) -> StructuredLogger:
    """创建结构化日志记录器"""
    return get_observability_system().create_logger(name, context)


def trace_operation(operation_name: str, context: Optional[TracingContext] = None):
    """追踪操作的装饰器"""
    return get_observability_system().trace_operation(operation_name, context)