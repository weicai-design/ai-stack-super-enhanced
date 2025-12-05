#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控告警系统
实现实时监控、智能告警和自动恢复机制
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4

import psutil
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from redis import Redis

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态"""
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class MetricType(str, Enum):
    """指标类型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # 例如: "value > 80"
    threshold: float
    duration: int  # 持续时间（秒）
    alert_level: AlertLevel
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    alert_level: AlertLevel
    status: AlertStatus = AlertStatus.FIRING
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_bytes: int
    process_count: int
    timestamp: str


class MetricCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集指标数据"""
        pass
    
    @abstractmethod
    def get_metric_names(self) -> List[str]:
        """获取指标名称列表"""
        pass


class SystemMetricCollector(MetricCollector):
    """系统指标收集器"""
    
    def __init__(self):
        self.metric_names = [
            "system_cpu_percent",
            "system_memory_percent", 
            "system_disk_usage_percent",
            "system_network_io_bytes",
            "system_process_count",
        ]
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # 网络IO
            network_io = psutil.net_io_counters()
            network_io_bytes = network_io.bytes_sent + network_io.bytes_recv
            
            # 进程数量
            process_count = len(psutil.pids())
            
            return {
                "system_cpu_percent": cpu_percent,
                "system_memory_percent": memory_percent,
                "system_disk_usage_percent": disk_usage_percent,
                "system_network_io_bytes": network_io_bytes,
                "system_process_count": process_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"系统指标收集失败: {e}")
            return {}
    
    def get_metric_names(self) -> List[str]:
        return self.metric_names


class ApplicationMetricCollector(MetricCollector):
    """应用指标收集器"""
    
    def __init__(self):
        self.metric_names = [
            "app_request_count",
            "app_error_count",
            "app_response_time_ms",
            "app_active_users",
            "app_database_connections",
        ]
        self.metrics = {}
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集应用指标"""
        # 这里可以集成应用特定的指标收集逻辑
        # 例如从应用日志、数据库、缓存等获取指标
        
        return {
            "app_request_count": self.metrics.get("request_count", 0),
            "app_error_count": self.metrics.get("error_count", 0),
            "app_response_time_ms": self.metrics.get("response_time_ms", 0),
            "app_active_users": self.metrics.get("active_users", 0),
            "app_database_connections": self.metrics.get("db_connections", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def update_metric(self, metric_name: str, value: Any) -> None:
        """更新应用指标"""
        self.metrics[metric_name] = value
    
    def get_metric_names(self) -> List[str]:
        return self.metric_names


class AlertManager:
    """告警管理器"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.redis_client = redis_client
        self.alert_history: List[Alert] = []
        
        # 告警通知渠道
        self.notification_channels: Dict[str, Callable] = {}
        
        # 初始化默认告警规则
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """初始化默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="high_cpu_usage",
                name="高CPU使用率",
                description="CPU使用率超过80%持续5分钟",
                metric_name="system_cpu_percent",
                condition=">",
                threshold=80.0,
                duration=300,
                alert_level=AlertLevel.WARNING,
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="高内存使用率", 
                description="内存使用率超过85%持续3分钟",
                metric_name="system_memory_percent",
                condition=">",
                threshold=85.0,
                duration=180,
                alert_level=AlertLevel.WARNING,
            ),
            AlertRule(
                rule_id="critical_disk_usage",
                name="磁盘空间严重不足",
                description="磁盘使用率超过95%持续1分钟",
                metric_name="system_disk_usage_percent",
                condition=">",
                threshold=95.0,
                duration=60,
                alert_level=AlertLevel.CRITICAL,
            ),
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"添加告警规则: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"移除告警规则: {rule_id}")
            return True
        return False
    
    def evaluate_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估指标并生成告警"""
        new_alerts = []
        
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            if rule.metric_name not in metrics:
                continue
            
            current_value = metrics[rule.metric_name]
            
            # 检查条件
            condition_met = False
            if rule.condition == ">":
                condition_met = current_value > rule.threshold
            elif rule.condition == ">=":
                condition_met = current_value >= rule.threshold
            elif rule.condition == "<":
                condition_met = current_value < rule.threshold
            elif rule.condition == "<=":
                condition_met = current_value <= rule.threshold
            elif rule.condition == "==":
                condition_met = current_value == rule.threshold
            
            if condition_met:
                # 检查是否已经存在相同规则的告警
                existing_alert = self._find_existing_alert(rule.rule_id)
                
                if existing_alert:
                    # 更新现有告警
                    existing_alert.current_value = current_value
                else:
                    # 创建新告警
                    alert = Alert(
                        alert_id=str(uuid4()),
                        rule_id=rule.rule_id,
                        metric_name=rule.metric_name,
                        current_value=current_value,
                        threshold=rule.threshold,
                        alert_level=rule.alert_level,
                        labels=rule.labels,
                        annotations={
                            "description": rule.description,
                            "condition": f"{rule.metric_name} {rule.condition} {rule.threshold}",
                        },
                    )
                    
                    self.active_alerts[alert.alert_id] = alert
                    new_alerts.append(alert)
                    
                    # 发送告警通知
                    self._send_notification(alert)
            else:
                # 条件不满足，检查是否需要解决告警
                self._resolve_alerts(rule.rule_id)
        
        return new_alerts
    
    def _find_existing_alert(self, rule_id: str) -> Optional[Alert]:
        """查找相同规则的现有告警"""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and alert.status == AlertStatus.FIRING:
                return alert
        return None
    
    def _resolve_alerts(self, rule_id: str) -> None:
        """解决告警"""
        alerts_to_resolve = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.rule_id == rule_id and alert.status == AlertStatus.FIRING:
                alerts_to_resolve.append(alert_id)
        
        for alert_id in alerts_to_resolve:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.end_time = datetime.utcnow().isoformat()
            
            # 添加到历史记录
            self.alert_history.append(alert)
            
            # 发送解决通知
            self._send_resolution_notification(alert)
            
            logger.info(f"告警已解决: {alert.rule_id}")
    
    def _send_notification(self, alert: Alert) -> None:
        """发送告警通知"""
        message = f"🚨 [{alert.alert_level.upper()}] {alert.metric_name} 告警\n"
        message += f"当前值: {alert.current_value}, 阈值: {alert.threshold}\n"
        message += f"时间: {alert.start_time}\n"
        
        if alert.annotations:
            message += f"描述: {alert.annotations.get('description', '')}\n"
        
        logger.warning(message)
        
        # 这里可以集成邮件、短信、钉钉等通知渠道
        # 例如: self._send_email_notification(alert)
        #       self._send_sms_notification(alert)
        #       self._send_dingtalk_notification(alert)
    
    def _send_resolution_notification(self, alert: Alert) -> None:
        """发送告警解决通知"""
        message = f"✅ [{alert.alert_level.upper()}] {alert.metric_name} 告警已解决\n"
        message += f"持续时间: {self._calculate_duration(alert.start_time, alert.end_time)}\n"
        
        logger.info(message)
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """计算持续时间"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = end - start
            return str(duration)
        except:
            return "未知"
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            return True
        return False


class RateLimiter:
    """限流器"""
    
    def __init__(self, redis_client: Redis, max_requests: int = 100, window_seconds: int = 60):
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        try:
            current_time = int(time.time())
            window_start = current_time - self.window_seconds
            
            # 使用Redis的ZSET实现滑动窗口限流
            pipeline = self.redis_client.pipeline()
            
            # 移除过期请求
            pipeline.zremrangebyscore(key, 0, window_start)
            
            # 获取当前窗口内的请求数量
            pipeline.zcard(key)
            
            # 添加当前请求
            pipeline.zadd(key, {str(current_time): current_time})
            
            # 设置过期时间
            pipeline.expire(key, self.window_seconds)
            
            results = pipeline.execute()
            current_count = results[1]
            
            return current_count <= self.max_requests
            
        except Exception as e:
            logger.error(f"限流检查失败: {e}")
            return True  # 失败时允许请求


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def execute(self, operation: Callable) -> Any:
        """执行操作，支持熔断"""
        if self.state == "OPEN":
            # 检查是否应该尝试恢复
            if self._should_attempt_recovery():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("熔断器已打开")
        
        try:
            result = await operation()
            
            # 操作成功，重置熔断器
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
    
    def _should_attempt_recovery(self) -> bool:
        """检查是否应该尝试恢复"""
        if self.last_failure_time is None:
            return True
        
        recovery_time = self.last_failure_time + self.recovery_timeout
        return time.time() >= recovery_time


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


class MonitoringAlertSystem:
    """
    监控告警系统
    
    集成功能：
    1. 实时指标收集
    2. 智能告警管理
    3. 限流熔断保护
    4. 自动恢复机制
    """
    
    def __init__(self, redis_client: Optional[Redis] = None, metrics_port: int = 9090):
        self.redis_client = redis_client
        self.metrics_port = metrics_port
        
        # 指标收集器
        self.metric_collectors: List[MetricCollector] = [
            SystemMetricCollector(),
            ApplicationMetricCollector(),
        ]
        
        # 告警管理器
        self.alert_manager = AlertManager(redis_client)
        
        # 限流器
        self.rate_limiter = RateLimiter(redis_client) if redis_client else None
        
        # 熔断器
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # 监控任务
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # 初始化Prometheus指标
        self._initialize_prometheus_metrics()
        
        logger.info("监控告警系统初始化完成")
    
    def _initialize_prometheus_metrics(self) -> None:
        """初始化Prometheus指标"""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"监控指标服务器启动在端口 {self.metrics_port}")
            
            # 定义监控指标
            self.request_counter = Counter('http_requests_total', 'Total HTTP requests')
            self.error_counter = Counter('http_errors_total', 'Total HTTP errors')
            self.response_time = Histogram('http_response_time_seconds', 'HTTP response time')
            
        except Exception as e:
            logger.error(f"Prometheus指标初始化失败: {e}")
    
    async def start_monitoring(self, interval: int = 30) -> None:
        """启动监控任务"""
        if self.is_running:
            logger.warning("监控任务已在运行中")
            return
        
        self.is_running = True
        
        async def monitoring_loop():
            while self.is_running:
                try:
                    # 收集所有指标
                    all_metrics = {}
                    
                    for collector in self.metric_collectors:
                        metrics = await collector.collect_metrics()
                        all_metrics.update(metrics)
                    
                    # 评估告警规则
                    new_alerts = self.alert_manager.evaluate_metrics(all_metrics)
                    
                    # 记录指标
                    self._record_metrics(all_metrics)
                    
                    # 记录活跃告警数量
                    active_alerts_count = len(self.alert_manager.get_active_alerts())
                    logger.debug(f"当前活跃告警: {active_alerts_count}")
                    
                    # 等待下一个收集周期
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"监控任务执行失败: {e}")
                    await asyncio.sleep(interval)  # 继续执行
        
        self.monitoring_task = asyncio.create_task(monitoring_loop())
        logger.info(f"监控任务已启动，间隔: {interval}秒")
    
    async def stop_monitoring(self) -> None:
        """停止监控任务"""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("监控任务已停止")
    
    def _record_metrics(self, metrics: Dict[str, Any]) -> None:
        """记录指标到Prometheus"""
        try:
            # 记录系统指标
            if 'system_cpu_percent' in metrics:
                Gauge('system_cpu_percent', 'System CPU usage percent').set(metrics['system_cpu_percent'])
            
            if 'system_memory_percent' in metrics:
                Gauge('system_memory_percent', 'System memory usage percent').set(metrics['system_memory_percent'])
            
            if 'system_disk_usage_percent' in metrics:
                Gauge('system_disk_usage_percent', 'System disk usage percent').set(metrics['system_disk_usage_percent'])
            
        except Exception as e:
            logger.error(f"记录指标失败: {e}")
    
    async def check_rate_limit(self, key: str) -> bool:
        """检查限流"""
        if self.rate_limiter:
            return await self.rate_limiter.is_allowed(key)
        return True
    
    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """获取熔断器实例"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "monitoring_running": self.is_running,
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "alert_rules": len(self.alert_manager.alert_rules),
            "metric_collectors": len(self.metric_collectors),
        }


# 全局实例
_monitoring_system: Optional[MonitoringAlertSystem] = None


def get_monitoring_system(redis_client: Optional[Redis] = None) -> MonitoringAlertSystem:
    """获取监控告警系统实例"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringAlertSystem(redis_client)
    return _monitoring_system