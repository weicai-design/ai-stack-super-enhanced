"""
结构化日志系统
提供生产级的日志记录、分布式追踪和性能监控支持
"""

import logging
import json
import time
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
import asyncio

# 全局追踪上下文
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
span_id_var: ContextVar[str] = ContextVar('span_id', default='')

# 日志级别枚举
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# 性能指标数据类
@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    operation_name: str
    duration_ms: float
    timestamp: datetime
    success: bool
    error_type: Optional[str] = None
    tags: Dict[str, str] = None

# 错误追踪数据类
@dataclass
class ErrorTrace:
    """错误追踪数据类"""
    error_type: str
    error_message: str
    stack_trace: str
    timestamp: datetime
    request_id: str
    span_id: str
    context: Dict[str, Any] = None


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.name = name
        
        # 性能指标存储
        self.performance_metrics: List[PerformanceMetric] = []
        self.error_traces: List[ErrorTrace] = []
        
        # 如果没有处理器，添加一个
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredLogFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """信息级别日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告级别日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """错误级别日志"""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """调试级别日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """严重级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """内部日志记录方法"""
        # 构建结构化日志记录
        record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': logging.getLevelName(level),
            'message': message,
            'logger': self.logger.name,
            'request_id': request_id_var.get(),
            'span_id': span_id_var.get(),
            **kwargs
        }
        
        # 记录日志
        self.logger.log(level, json.dumps(record, ensure_ascii=False))
    
    def record_performance(self, operation_name: str, duration_ms: float, success: bool, 
                          error_type: str = None, tags: Dict[str, str] = None):
        """记录性能指标"""
        metric = PerformanceMetric(
            operation_name=operation_name,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            success=success,
            error_type=error_type,
            tags=tags or {}
        )
        self.performance_metrics.append(metric)
        
        # 记录性能日志
        self.info(
            f"性能指标: {operation_name}",
            event="performance_metric",
            operation_name=operation_name,
            duration_ms=duration_ms,
            success=success,
            error_type=error_type,
            tags=tags
        )
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误追踪"""
        error_trace = ErrorTrace(
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            timestamp=datetime.now(),
            request_id=request_id_var.get(),
            span_id=span_id_var.get(),
            context=context or {}
        )
        self.error_traces.append(error_trace)
        
        # 记录错误日志
        self.error(
            f"错误追踪: {type(error).__name__}",
            event="error_trace",
            error_type=type(error).__name__,
            error_message=str(error),
            request_id=request_id_var.get(),
            span_id=span_id_var.get(),
            context=context
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_metrics:
            return {"total_operations": 0, "avg_duration": 0, "success_rate": 1.0}
        
        total_ops = len(self.performance_metrics)
        successful_ops = len([m for m in self.performance_metrics if m.success])
        avg_duration = sum(m.duration_ms for m in self.performance_metrics) / total_ops
        success_rate = successful_ops / total_ops
        
        return {
            "total_operations": total_ops,
            "avg_duration": round(avg_duration, 2),
            "success_rate": round(success_rate, 3),
            "recent_operations": [
                {
                    "operation": m.operation_name,
                    "duration": m.duration_ms,
                    "success": m.success,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.performance_metrics[-10:]  # 最近10个操作
            ]
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        if not self.error_traces:
            return {"total_errors": 0, "error_types": {}}
        
        error_types = {}
        for trace in self.error_traces:
            error_types[trace.error_type] = error_types.get(trace.error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_traces),
            "error_types": error_types,
            "recent_errors": [
                {
                    "type": trace.error_type,
                    "message": trace.error_message,
                    "timestamp": trace.timestamp.isoformat(),
                    "request_id": trace.request_id
                }
                for trace in self.error_traces[-5:]  # 最近5个错误
            ]
        }


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        """格式化日志记录"""
        try:
            # 如果是JSON字符串，直接返回
            if isinstance(record.msg, str) and record.msg.startswith('{'):
                return record.msg
            else:
                # 否则构建结构化日志
                log_data = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'logger': record.name,
                    'request_id': request_id_var.get(),
                    'span_id': span_id_var.get(),
                    'file': record.pathname,
                    'line': record.lineno
                }
                return json.dumps(log_data, ensure_ascii=False)
        except Exception:
            # 如果格式化失败，回退到默认格式
            return super().format(record)


class TracingContext:
    """分布式追踪上下文管理器"""
    
    def __init__(self, name: str, request_id: Optional[str] = None):
        self.name = name
        self.request_id = request_id or str(uuid.uuid4())
        self.span_id = str(uuid.uuid4())
        self.start_time = None
        self.logger = StructuredLogger(f"tracing.{name}")
    
    def __enter__(self):
        """进入上下文"""
        # 设置追踪上下文
        self._previous_request_id = request_id_var.set(self.request_id)
        self._previous_span_id = span_id_var.set(self.span_id)
        
        self.start_time = time.time()
        
        # 记录开始追踪
        self.logger.info(
            f"开始追踪: {self.name}",
            event="trace_start",
            trace_name=self.name,
            request_id=self.request_id,
            span_id=self.span_id
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        # 计算执行时间
        duration = time.time() - self.start_time
        
        # 记录结束追踪
        if exc_type is None:
            self.logger.info(
                f"追踪完成: {self.name}",
                event="trace_end",
                trace_name=self.name,
                request_id=self.request_id,
                span_id=self.span_id,
                duration_ms=round(duration * 1000, 2),
                status="success"
            )
        else:
            self.logger.error(
                f"追踪失败: {self.name}",
                event="trace_error",
                trace_name=self.name,
                request_id=self.request_id,
                span_id=self.span_id,
                duration_ms=round(duration * 1000, 2),
                status="error",
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        
        # 恢复之前的上下文
        request_id_var.reset(self._previous_request_id)
        span_id_var.reset(self._previous_span_id)


class RequestTracer:
    """HTTP请求追踪器"""
    
    def __init__(self, logger_name: str = "http"):
        self.logger = StructuredLogger(logger_name)
    
    async def trace_request(self, request, call_next):
        """追踪HTTP请求"""
        request_id = str(uuid.uuid4())
        
        # 设置请求上下文
        request_id_var.set(request_id)
        
        # 记录请求开始
        self.logger.info(
            "HTTP请求开始",
            event="request_start",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_host=request.client.host if request.client else "unknown"
        )
        
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录请求完成
            duration = time.time() - start_time
            self.logger.info(
                "HTTP请求完成",
                event="request_end",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )
            
            return response
            
        except Exception as e:
            # 记录请求错误
            duration = time.time() - start_time
            self.logger.error(
                "HTTP请求错误",
                event="request_error",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                duration_ms=round(duration * 1000, 2),
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise


class PerformanceMonitor:
    """性能监控管理器"""
    
    def __init__(self):
        self.loggers: Dict[str, StructuredLogger] = {}
        self.metrics_exporters: List[Callable] = []
    
    def get_logger(self, name: str) -> StructuredLogger:
        """获取或创建日志记录器"""
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
        return self.loggers[name]
    
    def add_metrics_exporter(self, exporter: Callable):
        """添加指标导出器"""
        self.metrics_exporters.append(exporter)
    
    def export_metrics(self):
        """导出所有指标"""
        all_metrics = {}
        for name, logger in self.loggers.items():
            all_metrics[name] = {
                "performance": logger.get_performance_summary(),
                "errors": logger.get_error_summary()
            }
        
        # 调用所有导出器
        for exporter in self.metrics_exporters:
            try:
                exporter(all_metrics)
            except Exception as e:
                print(f"指标导出失败: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "loggers": {},
            "overall": {"status": "healthy", "message": "系统运行正常"}
        }
        
        for name, logger in self.loggers.items():
            error_summary = logger.get_error_summary()
            performance_summary = logger.get_performance_summary()
            
            health["loggers"][name] = {
                "errors": error_summary,
                "performance": performance_summary,
                "status": "healthy" if error_summary["total_errors"] == 0 else "warning"
            }
        
        # 检查整体状态
        total_errors = sum(logger.get_error_summary()["total_errors"] for logger in self.loggers.values())
        if total_errors > 0:
            health["overall"]["status"] = "warning"
            health["overall"]["message"] = f"系统存在 {total_errors} 个错误"
        
        return health


# 全局性能监控实例
_global_monitor = PerformanceMonitor()


# 全局日志记录器实例
def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器"""
    return _global_monitor.get_logger(name)


def trace_operation(name: str, request_id: Optional[str] = None) -> TracingContext:
    """创建追踪上下文"""
    return TracingContext(name, request_id)


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor


def performance_decorator(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_type = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_type = type(e).__name__
                    # 记录错误
                    logger = get_logger(f"performance.{operation_name}")
                    logger.record_error(e, {"operation": operation_name})
                    raise
                finally:
                    duration = (time.time() - start_time) * 1000
                    logger = get_logger(f"performance.{operation_name}")
                    logger.record_performance(operation_name, duration, success, error_type)
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_type = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_type = type(e).__name__
                    # 记录错误
                    logger = get_logger(f"performance.{operation_name}")
                    logger.record_error(e, {"operation": operation_name})
                    raise
                finally:
                    duration = (time.time() - start_time) * 1000
                    logger = get_logger(f"performance.{operation_name}")
                    logger.record_performance(operation_name, duration, success, error_type)
            
            return sync_wrapper
    
    return decorator


# 示例使用
if __name__ == "__main__":
    # 测试结构化日志
    logger = get_logger("test")
    
    # 测试性能监控装饰器
    @performance_decorator("test_operation")
    def test_function():
        """测试函数"""
        logger.info("执行测试操作")
        time.sleep(0.1)
        return "操作成功"
    
    # 测试错误追踪
    @performance_decorator("error_operation")
    def error_function():
        """错误测试函数"""
        logger.info("执行错误操作")
        raise ValueError("测试错误")
    
    with trace_operation("test_operation") as trace:
        logger.info("测试信息日志", custom_field="test_value")
        logger.warning("测试警告日志", severity="medium")
        
        # 测试正常操作
        try:
            result = test_function()
            logger.info(f"操作结果: {result}")
        except Exception as e:
            logger.error(f"操作失败: {e}")
        
        # 测试错误操作
        try:
            error_function()
        except Exception as e:
            logger.error(f"错误操作失败: {e}")
        
        # 获取性能摘要
        monitor = get_performance_monitor()
        health = monitor.get_system_health()
        
        logger.info("系统健康状态", health=health)
        
        # 导出指标
        monitor.export_metrics()
        
        logger.info("测试完成", result="success")