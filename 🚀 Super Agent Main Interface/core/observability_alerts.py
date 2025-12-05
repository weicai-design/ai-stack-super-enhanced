"""
可观测性告警机制
基于指标和事件设置告警规则
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import threading

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCondition(Enum):
    """告警条件"""
    GT = "gt"  # 大于
    GTE = "gte"  # 大于等于
    LT = "lt"  # 小于
    LTE = "lte"  # 小于等于
    EQ = "eq"  # 等于
    NEQ = "neq"  # 不等于
    CONTAINS = "contains"  # 包含
    REGEX = "regex"  # 正则匹配


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    rule_type: str  # metric, event, trace
    condition: AlertCondition
    threshold: Any
    severity: AlertSeverity
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    metric_name: Optional[str] = None
    event_name: Optional[str] = None
    duration: Optional[float] = None  # 持续时间（秒）
    cooldown: Optional[float] = None  # 冷却时间（秒）
    action: Optional[str] = None  # 告警动作（webhook, email, etc.）
    created_at: float = field(default_factory=time.time)
    last_triggered: Optional[float] = None


@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    value: Any
    threshold: Any
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ObservabilityAlertSystem:
    """可观测性告警系统"""
    
    def __init__(self, observability_system):
        """
        初始化告警系统
        
        Args:
            observability_system: 可观测性系统实例
        """
        self.observability = observability_system
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable] = []
        
        # 默认告警规则
        self._init_default_rules()
        
        logger.info("可观测性告警系统初始化完成")
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        # HTTP错误率告警
        self.add_rule(AlertRule(
            rule_id="http_error_rate",
            name="HTTP错误率告警",
            description="当HTTP错误率超过阈值时触发",
            rule_type="metric",
            condition=AlertCondition.GT,
            threshold=0.1,  # 10%
            severity=AlertSeverity.WARNING,
            metric_name="http_error_rate",
            duration=60.0,  # 持续60秒
            cooldown=300.0  # 冷却5分钟
        ))
        
        # 请求延迟告警
        self.add_rule(AlertRule(
            rule_id="http_request_duration",
            name="请求延迟告警",
            description="当请求延迟超过阈值时触发",
            rule_type="metric",
            condition=AlertCondition.GT,
            threshold=5.0,  # 5秒
            severity=AlertSeverity.WARNING,
            metric_name="http_request_duration",
            tags={"status_code": "200"},
            duration=60.0,
            cooldown=300.0
        ))
        
        # 长任务超时告警
        self.add_rule(AlertRule(
            rule_id="long_task_timeout",
            name="长任务超时告警",
            description="当长任务执行时间超过阈值时触发",
            rule_type="trace",
            condition=AlertCondition.GT,
            threshold=3600.0,  # 1小时
            severity=AlertSeverity.ERROR,
            duration=0.0,
            cooldown=600.0
        ))
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self.rules[rule.rule_id] = rule
            logger.info(f"告警规则已添加: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """移除告警规则"""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"告警规则已移除: {rule_id}")
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """注册告警回调"""
        self._alert_callbacks.append(callback)
    
    def check_metric_alert(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """检查指标告警"""
        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                if rule.rule_type != "metric":
                    continue
                
                if rule.metric_name != metric_name:
                    continue
                
                # 检查标签匹配
                if rule.tags:
                    if not tags:
                        continue
                    if not all(tags.get(k) == v for k, v in rule.tags.items()):
                        continue
                
                # 检查条件
                if self._check_condition(value, rule.condition, rule.threshold):
                    # 检查冷却时间
                    if rule.cooldown and rule.last_triggered:
                        if time.time() - rule.last_triggered < rule.cooldown:
                            continue
                    
                    # 触发告警
                    self._trigger_alert(rule, value, {"metric_name": metric_name, "tags": tags})
    
    def check_event_alert(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """检查事件告警"""
        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                if rule.rule_type != "event":
                    continue
                
                if rule.event_name != event_name:
                    continue
                
                # 检查条件
                if rule.condition == AlertCondition.CONTAINS:
                    if not properties:
                        continue
                    if rule.threshold not in str(properties):
                        continue
                
                # 检查冷却时间
                if rule.cooldown and rule.last_triggered:
                    if time.time() - rule.last_triggered < rule.cooldown:
                        continue
                
                # 触发告警
                self._trigger_alert(rule, event_name, {"event_name": event_name, "properties": properties})
    
    def check_trace_alert(self, trace: Dict[str, Any]):
        """检查Trace告警"""
        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                if rule.rule_type != "trace":
                    continue
                
                # 检查持续时间
                duration = trace.get("duration")
                if duration is None:
                    continue
                
                # 检查条件
                if self._check_condition(duration, rule.condition, rule.threshold):
                    # 检查冷却时间
                    if rule.cooldown and rule.last_triggered:
                        if time.time() - rule.last_triggered < rule.cooldown:
                            continue
                    
                    # 触发告警
                    self._trigger_alert(rule, duration, {"trace_id": trace.get("trace_id")})
    
    def _check_condition(self, value: Any, condition: AlertCondition, threshold: Any) -> bool:
        """检查条件"""
        try:
            if condition == AlertCondition.GT:
                return float(value) > float(threshold)
            elif condition == AlertCondition.GTE:
                return float(value) >= float(threshold)
            elif condition == AlertCondition.LT:
                return float(value) < float(threshold)
            elif condition == AlertCondition.LTE:
                return float(value) <= float(threshold)
            elif condition == AlertCondition.EQ:
                return value == threshold
            elif condition == AlertCondition.NEQ:
                return value != threshold
            elif condition == AlertCondition.CONTAINS:
                return str(threshold) in str(value)
            elif condition == AlertCondition.REGEX:
                import re
                return bool(re.search(str(threshold), str(value)))
        except (ValueError, TypeError):
            return False
        
        return False
    
    def _trigger_alert(self, rule: AlertRule, value: Any, metadata: Dict[str, Any]):
        """触发告警"""
        alert_id = f"alert_{int(time.time() * 1000)}_{len(self.alerts)}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"{rule.description}: {value} (阈值: {rule.threshold})",
            value=value,
            threshold=rule.threshold,
            metadata=metadata
        )
        
        with self._lock:
            self.alerts.append(alert)
            
            # 保留最近10000条告警
            if len(self.alerts) > 10000:
                self.alerts = self.alerts[-10000:]
            
            # 更新规则最后触发时间
            rule.last_triggered = time.time()
        
        # 调用回调
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
        
        logger.warning(f"告警触发: {rule.name} - {alert.message}")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = time.time()
                    logger.info(f"告警已解决: {alert_id}")
                    return True
        return False
    
    def get_alerts(
        self,
        rule_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取告警"""
        alerts = self.alerts
        
        if rule_id:
            alerts = [a for a in alerts if a.rule_id == rule_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [
            {
                "alert_id": a.alert_id,
                "rule_id": a.rule_id,
                "rule_name": a.rule_name,
                "severity": a.severity.value,
                "message": a.message,
                "value": a.value,
                "threshold": a.threshold,
                "timestamp": a.timestamp,
                "resolved": a.resolved,
                "resolved_at": a.resolved_at,
                "metadata": a.metadata
            }
            for a in alerts[-limit:]
        ]
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "rule_type": r.rule_type,
                "condition": r.condition.value,
                "threshold": r.threshold,
                "severity": r.severity.value,
                "enabled": r.enabled,
                "tags": r.tags,
                "metric_name": r.metric_name,
                "event_name": r.event_name,
                "duration": r.duration,
                "cooldown": r.cooldown,
                "action": r.action,
                "created_at": r.created_at,
                "last_triggered": r.last_triggered
            }
            for r in self.rules.values()
        ]














