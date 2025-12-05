"""
RAG专家监控系统
为RAG专家模块提供生产级性能监控和指标收集功能
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import defaultdict, deque
import threading
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """监控指标"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_prometheus_format(self) -> str:
        """转换为Prometheus格式"""
        labels_str = ""
        if self.labels:
            labels_str = "{" + ",".join([f'{k}="{v}"' for k, v in self.labels.items()]) + "}"
        
        return f"{self.name}{labels_str} {self.value} {int(self.timestamp * 1000)}"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class RAGMetricsCollector:
    """RAG指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, List[Metric]] = defaultdict(list)
        self._lock = threading.RLock()
        self._max_metrics_per_name = 1000
        
        # 注册默认指标
        self._register_default_metrics()
    
    def _register_default_metrics(self):
        """注册默认指标"""
        # 请求相关指标
        self.record_counter("rag_requests_total", labels={"status": "total"})
        self.record_counter("rag_requests_total", labels={"status": "success"})
        self.record_counter("rag_requests_total", labels={"status": "error"})
        
        # 性能指标
        self.record_histogram("rag_request_duration_seconds", labels={})
        self.record_gauge("rag_concurrent_requests", 0, labels={})
        
        # 专家特定指标
        for expert_type in ["knowledge", "retrieval", "graph"]:
            self.record_counter(f"rag_{expert_type}_analyses_total", labels={"status": "total"})
            self.record_counter(f"rag_{expert_type}_analyses_total", labels={"status": "success"})
            self.record_counter(f"rag_{expert_type}_analyses_total", labels={"status": "error"})
            self.record_histogram(f"rag_{expert_type}_analysis_duration_seconds", labels={})
    
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """记录计数器指标"""
        with self._lock:
            metric = Metric(name, MetricType.COUNTER, value, labels or {})
            self._add_metric(metric)
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """记录仪表盘指标"""
        with self._lock:
            metric = Metric(name, MetricType.GAUGE, value, labels or {})
            self._add_metric(metric)
    
    def record_histogram(self, name: str, value: float = 0.0, labels: Optional[Dict[str, str]] = None):
        """记录直方图指标"""
        with self._lock:
            metric = Metric(name, MetricType.HISTOGRAM, value, labels or {})
            self._add_metric(metric)
    
    def _add_metric(self, metric: Metric):
        """添加指标"""
        metrics = self._metrics[metric.name]
        metrics.append(metric)
        
        # 限制指标数量
        if len(metrics) > self._max_metrics_per_name:
            self._metrics[metric.name] = metrics[-self._max_metrics_per_name:]
    
    def get_metrics(self, name: Optional[str] = None, 
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None) -> List[Metric]:
        """获取指标"""
        with self._lock:
            if name:
                metrics = self._metrics.get(name, [])
            else:
                metrics = []
                for name_metrics in self._metrics.values():
                    metrics.extend(name_metrics)
            
            # 时间过滤
            if start_time or end_time:
                filtered_metrics = []
                for metric in metrics:
                    if start_time and metric.timestamp < start_time:
                        continue
                    if end_time and metric.timestamp > end_time:
                        continue
                    filtered_metrics.append(metric)
                metrics = filtered_metrics
            
            return sorted(metrics, key=lambda x: x.timestamp)
    
    def get_prometheus_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        metrics = self.get_metrics()
        prometheus_lines = []
        
        for metric in metrics:
            prometheus_lines.append(metric.to_prometheus_format())
        
        return "\n".join(prometheus_lines)
    
    def clear_metrics(self, name: Optional[str] = None):
        """清除指标"""
        with self._lock:
            if name:
                self._metrics[name] = []
            else:
                self._metrics.clear()
                self._register_default_metrics()


class RAGHealthChecker:
    """RAG健康检查器"""
    
    def __init__(self, metrics_collector: RAGMetricsCollector):
        self.metrics_collector = metrics_collector
        self._health_checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._register_default_health_checks()
    
    def _register_default_health_checks(self):
        """注册默认健康检查"""
        self.register_health_check("system", self._check_system_health)
        self.register_health_check("performance", self._check_performance_health)
        self.register_health_check("memory", self._check_memory_health)
    
    def register_health_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """注册健康检查"""
        self._health_checks[name] = check_func
    
    def _check_system_health(self) -> HealthCheckResult:
        """检查系统健康状态"""
        try:
            # 检查最近错误率
            error_metrics = self.metrics_collector.get_metrics(
                "rag_requests_total", 
                start_time=time.time() - 300,  # 最近5分钟
                end_time=time.time()
            )
            
            error_count = sum(m.value for m in error_metrics if m.labels.get("status") == "error")
            total_count = sum(m.value for m in error_metrics if m.labels.get("status") == "total")
            
            error_rate = error_count / total_count if total_count > 0 else 0
            
            if error_rate > 0.1:  # 错误率超过10%
                return HealthCheckResult(
                    HealthStatus.UNHEALTHY,
                    f"系统错误率过高: {error_rate:.2%}",
                    {"error_rate": error_rate, "error_count": error_count, "total_count": total_count}
                )
            elif error_rate > 0.05:  # 错误率超过5%
                return HealthCheckResult(
                    HealthStatus.DEGRADED,
                    f"系统错误率较高: {error_rate:.2%}",
                    {"error_rate": error_rate, "error_count": error_count, "total_count": total_count}
                )
            else:
                return HealthCheckResult(
                    HealthStatus.HEALTHY,
                    "系统运行正常",
                    {"error_rate": error_rate, "error_count": error_count, "total_count": total_count}
                )
                
        except Exception as e:
            return HealthCheckResult(
                HealthStatus.UNHEALTHY,
                f"健康检查失败: {str(e)}",
                {"error": str(e)}
            )
    
    def _check_performance_health(self) -> HealthCheckResult:
        """检查性能健康状态"""
        try:
            # 检查响应时间
            duration_metrics = self.metrics_collector.get_metrics(
                "rag_request_duration_seconds",
                start_time=time.time() - 300,  # 最近5分钟
                end_time=time.time()
            )
            
            if not duration_metrics:
                return HealthCheckResult(
                    HealthStatus.UNKNOWN,
                    "暂无性能数据",
                    {}
                )
            
            durations = [m.value for m in duration_metrics]
            avg_duration = sum(durations) / len(durations)
            
            if avg_duration > 5.0:  # 平均响应时间超过5秒
                return HealthCheckResult(
                    HealthStatus.UNHEALTHY,
                    f"响应时间过长: {avg_duration:.2f}秒",
                    {"avg_duration": avg_duration, "sample_count": len(durations)}
                )
            elif avg_duration > 2.0:  # 平均响应时间超过2秒
                return HealthCheckResult(
                    HealthStatus.DEGRADED,
                    f"响应时间较高: {avg_duration:.2f}秒",
                    {"avg_duration": avg_duration, "sample_count": len(durations)}
                )
            else:
                return HealthCheckResult(
                    HealthStatus.HEALTHY,
                    f"响应时间正常: {avg_duration:.2f}秒",
                    {"avg_duration": avg_duration, "sample_count": len(durations)}
                )
                
        except Exception as e:
            return HealthCheckResult(
                HealthStatus.UNHEALTHY,
                f"性能检查失败: {str(e)}",
                {"error": str(e)}
            )
    
    def _check_memory_health(self) -> HealthCheckResult:
        """检查内存健康状态"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100
            
            if memory_usage > 0.9:  # 内存使用率超过90%
                return HealthCheckResult(
                    HealthStatus.UNHEALTHY,
                    f"内存使用率过高: {memory_usage:.2%}",
                    {"memory_usage": memory_usage, "available": memory.available}
                )
            elif memory_usage > 0.8:  # 内存使用率超过80%
                return HealthCheckResult(
                    HealthStatus.DEGRADED,
                    f"内存使用率较高: {memory_usage:.2%}",
                    {"memory_usage": memory_usage, "available": memory.available}
                )
            else:
                return HealthCheckResult(
                    HealthStatus.HEALTHY,
                    f"内存使用正常: {memory_usage:.2%}",
                    {"memory_usage": memory_usage, "available": memory.available}
                )
                
        except ImportError:
            return HealthCheckResult(
                HealthStatus.UNKNOWN,
                "无法检查内存状态(psutil未安装)",
                {}
            )
        except Exception as e:
            return HealthCheckResult(
                HealthStatus.UNHEALTHY,
                f"内存检查失败: {str(e)}",
                {"error": str(e)}
            )
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """执行所有健康检查"""
        results = {}
        for name, check_func in self._health_checks.items():
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = HealthCheckResult(
                    HealthStatus.UNHEALTHY,
                    f"健康检查异常: {str(e)}",
                    {"error": str(e)}
                )
        return results
    
    def get_overall_health(self) -> HealthStatus:
        """获取整体健康状态"""
        results = self.check_all()
        
        status_priority = {
            HealthStatus.UNHEALTHY: 3,
            HealthStatus.DEGRADED: 2,
            HealthStatus.UNKNOWN: 1,
            HealthStatus.HEALTHY: 0
        }
        
        worst_status = HealthStatus.HEALTHY
        for result in results.values():
            if status_priority[result.status] > status_priority[worst_status]:
                worst_status = result.status
        
        return worst_status


class RAGMonitoringSystem:
    """RAG监控系统"""
    
    def __init__(self):
        self.metrics_collector = RAGMetricsCollector()
        self.health_checker = RAGHealthChecker(self.metrics_collector)
        self._exporters: List[Callable[[], None]] = []
    
    @contextmanager
    def track_request(self, expert_type: str = "unknown"):
        """跟踪请求的上下文管理器"""
        start_time = time.time()
        self.metrics_collector.record_counter("rag_requests_total", labels={"status": "total"})
        self.metrics_collector.record_gauge("rag_concurrent_requests", 1)
        
        try:
            yield
            duration = time.time() - start_time
            self.metrics_collector.record_counter("rag_requests_total", labels={"status": "success"})
            self.metrics_collector.record_histogram("rag_request_duration_seconds", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.metrics_collector.record_counter("rag_requests_total", labels={"status": "error"})
            self.metrics_collector.record_histogram("rag_request_duration_seconds", duration)
            raise
        finally:
            self.metrics_collector.record_gauge("rag_concurrent_requests", -1)
    
    @contextmanager
    def track_expert_analysis(self, expert_type: str):
        """跟踪专家分析的上下文管理器"""
        start_time = time.time()
        self.metrics_collector.record_counter(
            f"rag_{expert_type}_analyses_total", 
            labels={"status": "total"}
        )
        
        try:
            yield
            duration = time.time() - start_time
            self.metrics_collector.record_counter(
                f"rag_{expert_type}_analyses_total", 
                labels={"status": "success"}
            )
            self.metrics_collector.record_histogram(
                f"rag_{expert_type}_analysis_duration_seconds", 
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.metrics_collector.record_counter(
                f"rag_{expert_type}_analyses_total", 
                labels={"status": "error"}
            )
            self.metrics_collector.record_histogram(
                f"rag_{expert_type}_analysis_duration_seconds", 
                duration
            )
            raise
    
    def register_exporter(self, exporter_func: Callable[[], None]):
        """注册指标导出器"""
        self._exporters.append(exporter_func)
    
    async def start_export_loop(self, interval_seconds: int = 30):
        """启动指标导出循环"""
        while True:
            try:
                for exporter in self._exporters:
                    exporter()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"指标导出失败: {e}")
                await asyncio.sleep(interval_seconds)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        results = self.health_checker.check_all()
        overall = self.health_checker.get_overall_health()
        
        return {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {name: {
                "status": result.status.value,
                "message": result.message,
                "details": result.details,
                "timestamp": datetime.fromtimestamp(result.timestamp).isoformat()
            } for name, result in results.items()}
        }


# 全局监控系统实例
_monitoring_system: Optional[RAGMonitoringSystem] = None


def get_monitoring_system() -> RAGMonitoringSystem:
    """获取全局监控系统"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = RAGMonitoringSystem()
    return _monitoring_system


def track_request(expert_type: str = "unknown"):
    """跟踪请求的装饰器"""
    return get_monitoring_system().track_request(expert_type)


def track_expert_analysis(expert_type: str):
    """跟踪专家分析的装饰器"""
    return get_monitoring_system().track_expert_analysis(expert_type)