"""
API性能监控和指标收集系统 - T0006-4增强版

功能特性：
1. Prometheus格式指标导出
2. 实时性能监控仪表板
3. 历史数据存储和分析
4. 自定义指标收集
5. 告警和通知机制
"""

import time
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import redis
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("erp_api")


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """指标数据结构"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    description: str = ""


class PerformanceMetricsCollector:
    """性能指标收集器 - T0006-4核心组件"""
    
    def __init__(self, enable_redis: bool = True, redis_client: Optional[redis.Redis] = None):
        self.enable_redis = enable_redis
        self.redis_client = redis_client
        
        # 指标存储
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.realtime_metrics: Dict[str, Any] = {}
        
        # 配置
        self.retention_days = 30  # 数据保留天数
        self.max_metrics_per_type = 10000  # 每种指标最大存储数量
        
        # 系统指标
        self.system_metrics_enabled = True
        self.collection_interval = 60  # 系统指标收集间隔（秒）
        
        # 启动系统指标收集
        if self.system_metrics_enabled:
            asyncio.create_task(self._collect_system_metrics())
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        while True:
            try:
                await self._collect_system_metrics_once()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"系统指标收集失败: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒重试
    
    async def _collect_system_metrics_once(self):
        """单次系统指标收集"""
        import psutil
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric(
            name="system_cpu_usage",
            type=MetricType.GAUGE,
            value=cpu_percent,
            labels={"type": "percent"},
            description="系统CPU使用率"
        )
        
        # 内存使用
        memory = psutil.virtual_memory()
        self.record_metric(
            name="system_memory_usage",
            type=MetricType.GAUGE,
            value=memory.percent,
            labels={"type": "percent"},
            description="系统内存使用率"
        )
        
        # 内存使用量（字节）
        self.record_metric(
            name="system_memory_bytes",
            type=MetricType.GAUGE,
            value=memory.used,
            labels={"type": "used"},
            description="系统已使用内存字节数"
        )
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        self.record_metric(
            name="system_disk_usage",
            type=MetricType.GAUGE,
            value=disk.percent,
            labels={"type": "percent"},
            description="系统磁盘使用率"
        )
        
        # 网络IO
        net_io = psutil.net_io_counters()
        self.record_metric(
            name="system_network_bytes",
            type=MetricType.COUNTER,
            value=net_io.bytes_sent,
            labels={"direction": "sent"},
            description="网络发送字节数"
        )
        self.record_metric(
            name="system_network_bytes",
            type=MetricType.COUNTER,
            value=net_io.bytes_recv,
            labels={"direction": "received"},
            description="网络接收字节数"
        )
        
        # 进程指标
        process = psutil.Process()
        self.record_metric(
            name="process_memory_rss",
            type=MetricType.GAUGE,
            value=process.memory_info().rss,
            labels={"type": "rss"},
            description="进程RSS内存使用量"
        )
        
        logger.debug("系统指标收集完成")
    
    def record_metric(self, name: str, type: MetricType, value: float, 
                     labels: Dict[str, str], description: str = ""):
        """记录指标"""
        metric = Metric(
            name=name,
            type=type,
            value=value,
            labels=labels,
            timestamp=datetime.now(),
            description=description
        )
        
        # 存储到内存
        key = f"{name}_{json.dumps(labels, sort_keys=True)}"
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=self.max_metrics_per_type)
        
        self.metrics[key].append(metric)
        
        # 更新实时指标
        self.realtime_metrics[key] = metric
        
        # 存储到Redis（如果启用）
        if self.enable_redis and self.redis_client:
            try:
                redis_key = f"metrics:{name}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.redis_client.setex(
                    redis_key, 
                    self.retention_days * 24 * 3600,  # 保留天数转换为秒
                    json.dumps({
                        "name": name,
                        "type": type.value,
                        "value": value,
                        "labels": labels,
                        "timestamp": metric.timestamp.isoformat(),
                        "description": description
                    })
                )
            except Exception as e:
                logger.warning(f"Redis指标存储失败: {e}")
    
    def record_api_metric(self, endpoint: str, method: str, status_code: int, 
                         duration: float, user_agent: str = ""):
        """记录API性能指标"""
        labels = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
            "user_agent": user_agent.split()[0] if user_agent else "unknown"
        }
        
        # 响应时间指标
        self.record_metric(
            name="api_response_time_seconds",
            type=MetricType.HISTOGRAM,
            value=duration,
            labels=labels,
            description="API响应时间"
        )
        
        # 请求计数指标
        self.record_metric(
            name="api_requests_total",
            type=MetricType.COUNTER,
            value=1,
            labels=labels,
            description="API请求总数"
        )
        
        # 错误率指标（针对非2xx状态码）
        if status_code >= 400:
            self.record_metric(
                name="api_errors_total",
                type=MetricType.COUNTER,
                value=1,
                labels=labels,
                description="API错误总数"
            )
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "system_metrics": {},
            "api_metrics": {},
            "custom_metrics": {}
        }
        
        # 分析API指标
        api_metrics = {}
        for key, metrics in self.metrics.items():
            if key.startswith("api_"):
                recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
                if recent_metrics:
                    metric_name = key.split('_')[0] + "_" + key.split('_')[1]
                    if metric_name not in api_metrics:
                        api_metrics[metric_name] = {
                            "count": len(recent_metrics),
                            "avg_value": sum(m.value for m in recent_metrics) / len(recent_metrics),
                            "min_value": min(m.value for m in recent_metrics),
                            "max_value": max(m.value for m in recent_metrics)
                        }
        
        summary["api_metrics"] = api_metrics
        
        # 系统指标
        system_keys = [k for k in self.realtime_metrics.keys() if k.startswith("system_")]
        for key in system_keys:
            metric = self.realtime_metrics[key]
            summary["system_metrics"][metric.name] = metric.value
        
        return summary
    
    def export_prometheus_metrics(self) -> str:
        """导出Prometheus格式指标"""
        prometheus_lines = []
        
        # 添加HELP和TYPE注释
        metric_help = {
            "api_response_time_seconds": "API响应时间（秒）",
            "api_requests_total": "API请求总数",
            "api_errors_total": "API错误总数",
            "system_cpu_usage": "系统CPU使用率（百分比）",
            "system_memory_usage": "系统内存使用率（百分比）",
            "system_memory_bytes": "系统内存使用量（字节）",
            "system_disk_usage": "系统磁盘使用率（百分比）",
            "system_network_bytes": "网络流量字节数",
            "process_memory_rss": "进程RSS内存使用量（字节）"
        }
        
        metric_types = {
            "api_response_time_seconds": "histogram",
            "api_requests_total": "counter",
            "api_errors_total": "counter",
            "system_cpu_usage": "gauge",
            "system_memory_usage": "gauge",
            "system_memory_bytes": "gauge",
            "system_disk_usage": "gauge",
            "system_network_bytes": "counter",
            "process_memory_rss": "gauge"
        }
        
        # 按指标名称分组
        grouped_metrics = defaultdict(list)
        for metric in self.realtime_metrics.values():
            grouped_metrics[metric.name].append(metric)
        
        # 生成Prometheus格式
        for metric_name, metrics in grouped_metrics.items():
            # HELP注释
            if metric_name in metric_help:
                prometheus_lines.append(f"# HELP {metric_name} {metric_help[metric_name]}")
            
            # TYPE注释
            if metric_name in metric_types:
                prometheus_lines.append(f"# TYPE {metric_name} {metric_types[metric_name]}")
            
            # 指标数据
            for metric in metrics:
                labels_str = ""
                if metric.labels:
                    labels_list = [f'{k}="{v}"' for k, v in metric.labels.items()]
                    labels_str = "{" + ",".join(labels_list) + "}"
                
                prometheus_lines.append(f"{metric_name}{labels_str} {metric.value}")
        
        return "\n".join(prometheus_lines)


# 全局性能监控实例
_performance_monitor: Optional[PerformanceMetricsCollector] = None


def get_performance_monitor(redis_client: Optional[redis.Redis] = None) -> PerformanceMetricsCollector:
    """获取性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMetricsCollector(
            enable_redis=True,
            redis_client=redis_client
        )
    return _performance_monitor


def record_api_performance(endpoint: str, method: str, response_time: float, 
                          status_code: int, cache_hit: bool = False, error_type: str = ""):
    """记录API性能指标（便捷函数）- 与中间件集成"""
    monitor = get_performance_monitor()
    
    # 构建用户代理信息（简化）
    user_agent = "cache_hit" if cache_hit else "cache_miss"
    if error_type:
        user_agent = f"error_{error_type}"
    
    monitor.record_api_metric(endpoint, method, status_code, response_time, user_agent)