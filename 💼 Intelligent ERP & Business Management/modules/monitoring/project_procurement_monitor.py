"""
T013和T014模块生产级监控系统
实现项目管理与采购管理的实时监控和告警功能
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""
    PROJECT_CREATION_RATE = "project_creation_rate"
    PROJECT_COMPLETION_RATE = "project_completion_rate"
    MILESTONE_DELAY_RATE = "milestone_delay_rate"
    PROCUREMENT_ORDER_RATE = "procurement_order_rate"
    SUPPLIER_PERFORMANCE = "supplier_performance"
    DELIVERY_DELAY_RATE = "delivery_delay_rate"
    BUDGET_OVERSPEND = "budget_overspend"
    API_RESPONSE_TIME = "api_response_time"
    ERROR_RATE = "error_rate"


@dataclass
class Alert:
    """告警信息"""
    id: str
    module: str  # T013 或 T014
    metric: MetricType
    level: AlertLevel
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class Metric:
    """监控指标"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class ProjectProcurementMonitor:
    """项目管理与采购管理监控器"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化监控器
        
        Args:
            alert_thresholds: 告警阈值配置
        """
        # 指标存储
        self.metrics: List[Metric] = []
        
        # 告警存储
        self.alerts: List[Alert] = []
        
        # 默认告警阈值
        self.thresholds = alert_thresholds or {
            "project_creation_rate": 10,  # 每小时创建项目数阈值
            "project_completion_rate": 0.8,  # 项目完成率阈值
            "milestone_delay_rate": 0.2,  # 里程碑延迟率阈值
            "procurement_order_rate": 5,  # 每小时采购订单数阈值
            "supplier_performance": 0.9,  # 供应商绩效阈值
            "delivery_delay_rate": 0.15,  # 交付延迟率阈值
            "budget_overspend": 0.1,  # 预算超支率阈值
            "api_response_time": 2.0,  # API响应时间阈值(秒)
            "error_rate": 0.05  # 错误率阈值
        }
        
        # 监控窗口大小
        self.window_size = timedelta(hours=1)
        
        # 告警回调函数
        self.alert_callbacks = []
    
    def register_alert_callback(self, callback):
        """注册告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def record_metric(self, metric_type: MetricType, value: float, tags: Dict[str, str] = None):
        """记录监控指标"""
        metric = Metric(
            name=metric_type.value,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics.append(metric)
        
        # 检查是否需要触发告警
        self._check_alert(metric)
        
        # 清理过期指标
        self._cleanup_old_metrics()
    
    def _check_alert(self, metric: Metric):
        """检查是否需要触发告警"""
        threshold = self.thresholds.get(metric.name)
        
        if threshold is None:
            return
        
        # 根据指标类型确定告警条件
        alert_level = AlertLevel.INFO
        message = ""
        
        if metric.value > threshold:
            if metric.name in ["api_response_time", "error_rate", "milestone_delay_rate", 
                              "delivery_delay_rate", "budget_overspend"]:
                # 这些指标值越大越差
                if metric.value > threshold * 1.5:
                    alert_level = AlertLevel.CRITICAL
                elif metric.value > threshold * 1.2:
                    alert_level = AlertLevel.ERROR
                else:
                    alert_level = AlertLevel.WARNING
                
                message = f"{metric.name} 超出阈值: {metric.value:.2f} > {threshold:.2f}"
            
            else:
                # 这些指标值越大越好，但过高可能异常
                if metric.value > threshold * 3:
                    alert_level = AlertLevel.WARNING
                    message = f"{metric.name} 异常偏高: {metric.value:.2f} > {threshold:.2f}"
        
        elif metric.value < threshold * 0.5 and metric.name in ["project_completion_rate", "supplier_performance"]:
            # 这些指标值越小越差
            alert_level = AlertLevel.ERROR
            message = f"{metric.name} 低于阈值: {metric.value:.2f} < {threshold:.2f}"
        
        if alert_level != AlertLevel.INFO:
            self._trigger_alert(metric, alert_level, message)
    
    def _trigger_alert(self, metric: Metric, level: AlertLevel, message: str):
        """触发告警"""
        alert_id = f"ALERT_{int(time.time())}_{len(self.alerts)}"
        
        # 确定模块
        module = "T013" if "project" in metric.name else "T014"
        
        alert = Alert(
            id=alert_id,
            module=module,
            metric=MetricType(metric.name),
            level=level,
            message=message,
            value=metric.value,
            threshold=self.thresholds[metric.name],
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # 调用告警回调
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"Alert triggered: {alert.level.value} - {alert.message}")
    
    def _cleanup_old_metrics(self):
        """清理过期指标"""
        cutoff_time = datetime.now() - self.window_size
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        # 按指标类型分组
        for metric_type in MetricType:
            metrics = [m for m in self.metrics if m.name == metric_type.value]
            if metrics:
                values = [m.value for m in metrics]
                summary[metric_type.value] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1]
                }
        
        return summary
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert_id}")
                break


# 监控器实例
monitor = ProjectProcurementMonitor()


def monitor_project_creation():
    """监控项目创建"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功指标
                monitor.record_metric(
                    MetricType.PROJECT_CREATION_RATE, 
                    1,  # 每次创建成功计数+1
                    {"method": func.__name__}
                )
                
                # 记录响应时间
                response_time = time.time() - start_time
                monitor.record_metric(
                    MetricType.API_RESPONSE_TIME,
                    response_time,
                    {"method": func.__name__}
                )
                
                return result
                
            except Exception as e:
                # 记录错误指标
                monitor.record_metric(
                    MetricType.ERROR_RATE,
                    1,  # 错误计数+1
                    {"method": func.__name__, "error": str(e)}
                )
                raise
        
        return wrapper
    return decorator


def monitor_procurement_order():
    """监控采购订单"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # 记录成功指标
                monitor.record_metric(
                    MetricType.PROCUREMENT_ORDER_RATE, 
                    1,  # 每次创建成功计数+1
                    {"method": func.__name__}
                )
                
                # 记录响应时间
                response_time = time.time() - start_time
                monitor.record_metric(
                    MetricType.API_RESPONSE_TIME,
                    response_time,
                    {"method": func.__name__}
                )
                
                return result
                
            except Exception as e:
                # 记录错误指标
                monitor.record_metric(
                    MetricType.ERROR_RATE,
                    1,  # 错误计数+1
                    {"method": func.__name__, "error": str(e)}
                )
                raise
        
        return wrapper
    return decorator


def alert_to_console(alert: Alert):
    """控制台告警输出"""
    print(f"🚨 [{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {alert.module} - {alert.level.value.upper()}: {alert.message}")


# 注册控制台告警输出
monitor.register_alert_callback(alert_to_console)