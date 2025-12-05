"""
智能告警规则配置
P0-018: 可观测体系增强 - 智能告警规则配置
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import time


class AlertSeverity(Enum):
    """告警严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WECHAT_WORK = "wechat_work"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class IntelligentAlertRule:
    """智能告警规则"""
    rule_id: str
    name: str
    description: str
    metric_pattern: str  # 指标模式（支持通配符）
    condition_type: str  # static, dynamic, predictive
    threshold: Any
    severity: AlertSeverity
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    duration: Optional[float] = None  # 持续时间（秒）
    cooldown: Optional[float] = None  # 冷却时间（秒）
    
    # 智能规则参数
    prediction_window: Optional[float] = None  # 预测窗口（秒）
    confidence_threshold: Optional[float] = None  # 置信度阈值
    
    # 通知配置
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


# API性能相关告警规则
API_PERFORMANCE_RULES = [
    IntelligentAlertRule(
        rule_id="api_response_time_predictive",
        name="智能API响应时间预测告警",
        description="基于历史趋势预测API响应时间问题",
        metric_pattern="api_response_time_seconds",
        condition_type="predictive",
        threshold=2.0,  # 2秒
        severity=AlertSeverity.WARNING,
        prediction_window=3600,  # 1小时预测窗口
        confidence_threshold=0.8,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK
        ],
        tags={"category": "api", "type": "performance"}
    ),
    
    IntelligentAlertRule(
        rule_id="api_error_rate_static",
        name="API错误率静态告警",
        description="监控API错误率超过静态阈值",
        metric_pattern="api_error_rate",
        condition_type="static",
        threshold=0.05,  # 5%错误率
        severity=AlertSeverity.ERROR,
        duration=300,  # 持续5分钟
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK,
            NotificationChannel.SLACK
        ],
        tags={"category": "api", "type": "reliability"}
    ),
    
    IntelligentAlertRule(
        rule_id="api_throughput_dynamic",
        name="API吞吐量动态告警",
        description="基于历史数据动态检测API吞吐量异常",
        metric_pattern="api_throughput",
        condition_type="dynamic",
        threshold=3.0,  # 3倍标准差
        severity=AlertSeverity.WARNING,
        notification_channels=[
            NotificationChannel.SLACK
        ],
        tags={"category": "api", "type": "performance"}
    )
]


# 业务指标相关告警规则
BUSINESS_METRIC_RULES = [
    IntelligentAlertRule(
        rule_id="business_success_rate_predictive",
        name="智能业务成功率告警",
        description="预测业务成功率下降趋势",
        metric_pattern="business_success_rate",
        condition_type="predictive",
        threshold=0.95,  # 95%成功率
        severity=AlertSeverity.CRITICAL,
        prediction_window=7200,  # 2小时预测窗口
        confidence_threshold=0.9,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK,
            NotificationChannel.WECHAT_WORK
        ],
        tags={"category": "business", "type": "reliability"}
    ),
    
    IntelligentAlertRule(
        rule_id="user_conversion_rate_static",
        name="用户转化率告警",
        description="监控用户转化率低于阈值",
        metric_pattern="user_conversion_rate",
        condition_type="static",
        threshold=0.02,  # 2%转化率
        severity=AlertSeverity.ERROR,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        ],
        tags={"category": "business", "type": "performance"}
    ),
    
    IntelligentAlertRule(
        rule_id="revenue_growth_dynamic",
        name="收入增长动态告警",
        description="检测收入增长异常",
        metric_pattern="daily_revenue",
        condition_type="dynamic",
        threshold=2.5,  # 2.5倍标准差
        severity=AlertSeverity.WARNING,
        notification_channels=[
            NotificationChannel.EMAIL
        ],
        tags={"category": "business", "type": "financial"}
    )
]


# 系统资源相关告警规则
SYSTEM_RESOURCE_RULES = [
    IntelligentAlertRule(
        rule_id="cpu_usage_predictive",
        name="智能CPU使用率预测告警",
        description="预测CPU使用率超过阈值",
        metric_pattern="cpu_usage_percent",
        condition_type="predictive",
        threshold=80.0,  # 80%
        severity=AlertSeverity.WARNING,
        prediction_window=1800,  # 30分钟预测窗口
        confidence_threshold=0.85,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK
        ],
        tags={"category": "system", "type": "resource"}
    ),
    
    IntelligentAlertRule(
        rule_id="memory_usage_static",
        name="内存使用率告警",
        description="监控内存使用率超过阈值",
        metric_pattern="memory_usage_percent",
        condition_type="static",
        threshold=90.0,  # 90%
        severity=AlertSeverity.CRITICAL,
        duration=600,  # 持续10分钟
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK,
            NotificationChannel.WECHAT_WORK,
            NotificationChannel.SLACK
        ],
        tags={"category": "system", "type": "resource"}
    ),
    
    IntelligentAlertRule(
        rule_id="disk_usage_dynamic",
        name="磁盘使用率动态告警",
        description="基于历史数据动态检测磁盘使用率异常",
        metric_pattern="disk_usage_percent",
        condition_type="dynamic",
        threshold=2.0,  # 2倍标准差
        severity=AlertSeverity.ERROR,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        ],
        tags={"category": "system", "type": "resource"}
    )
]


# 用户行为相关告警规则
USER_BEHAVIOR_RULES = [
    IntelligentAlertRule(
        rule_id="user_activity_anomaly",
        name="用户行为异常检测",
        description="检测异常用户行为模式",
        metric_pattern="user_activity_*",
        condition_type="dynamic",
        threshold=3.0,  # 3倍标准差
        severity=AlertSeverity.WARNING,
        notification_channels=[
            NotificationChannel.SLACK
        ],
        tags={"category": "user", "type": "behavior"}
    ),
    
    IntelligentAlertRule(
        rule_id="login_failure_rate_static",
        name="登录失败率告警",
        description="监控登录失败率超过阈值",
        metric_pattern="login_failure_rate",
        condition_type="static",
        threshold=0.1,  # 10%失败率
        severity=AlertSeverity.ERROR,
        duration=300,  # 持续5分钟
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK
        ],
        tags={"category": "user", "type": "security"}
    ),
    
    IntelligentAlertRule(
        rule_id="session_duration_predictive",
        name="智能会话时长预测告警",
        description="预测会话时长异常",
        metric_pattern="session_duration_seconds",
        condition_type="predictive",
        threshold=3600,  # 1小时
        severity=AlertSeverity.INFO,
        prediction_window=1800,  # 30分钟预测窗口
        confidence_threshold=0.7,
        notification_channels=[
            NotificationChannel.EMAIL
        ],
        tags={"category": "user", "type": "behavior"}
    )
]


# 数据库相关告警规则
DATABASE_RULES = [
    IntelligentAlertRule(
        rule_id="database_connection_pool_static",
        name="数据库连接池告警",
        description="监控数据库连接池使用率",
        metric_pattern="database_connection_pool_usage",
        condition_type="static",
        threshold=0.8,  # 80%使用率
        severity=AlertSeverity.ERROR,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK
        ],
        tags={"category": "database", "type": "resource"}
    ),
    
    IntelligentAlertRule(
        rule_id="query_latency_predictive",
        name="智能查询延迟预测告警",
        description="预测数据库查询延迟问题",
        metric_pattern="database_query_latency_ms",
        condition_type="predictive",
        threshold=1000.0,  # 1秒
        severity=AlertSeverity.WARNING,
        prediction_window=3600,  # 1小时预测窗口
        confidence_threshold=0.8,
        notification_channels=[
            NotificationChannel.EMAIL
        ],
        tags={"category": "database", "type": "performance"}
    ),
    
    IntelligentAlertRule(
        rule_id="deadlock_count_dynamic",
        name="死锁数量动态告警",
        description="动态检测数据库死锁异常",
        metric_pattern="database_deadlock_count",
        condition_type="dynamic",
        threshold=2.0,  # 2倍标准差
        severity=AlertSeverity.CRITICAL,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK,
            NotificationChannel.WECHAT_WORK
        ],
        tags={"category": "database", "type": "reliability"}
    )
]


# 网络相关告警规则
NETWORK_RULES = [
    IntelligentAlertRule(
        rule_id="network_latency_static",
        name="网络延迟告警",
        description="监控网络延迟超过阈值",
        metric_pattern="network_latency_ms",
        condition_type="static",
        threshold=500.0,  # 500ms
        severity=AlertSeverity.WARNING,
        notification_channels=[
            NotificationChannel.EMAIL
        ],
        tags={"category": "network", "type": "performance"}
    ),
    
    IntelligentAlertRule(
        rule_id="packet_loss_rate_predictive",
        name="智能丢包率预测告警",
        description="预测网络丢包率问题",
        metric_pattern="packet_loss_rate",
        condition_type="predictive",
        threshold=0.05,  # 5%丢包率
        severity=AlertSeverity.ERROR,
        prediction_window=1800,  # 30分钟预测窗口
        confidence_threshold=0.85,
        notification_channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.DINGTALK
        ],
        tags={"category": "network", "type": "reliability"}
    )
]


# 所有告警规则集合
ALL_INTELLIGENT_ALERT_RULES = (
    API_PERFORMANCE_RULES +
    BUSINESS_METRIC_RULES +
    SYSTEM_RESOURCE_RULES +
    USER_BEHAVIOR_RULES +
    DATABASE_RULES +
    NETWORK_RULES
)


class IntelligentAlertRuleManager:
    """智能告警规则管理器"""
    
    def __init__(self):
        self.rules: Dict[str, IntelligentAlertRule] = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认规则"""
        for rule in ALL_INTELLIGENT_ALERT_RULES:
            self.rules[rule.rule_id] = rule
    
    def add_rule(self, rule: IntelligentAlertRule):
        """添加规则"""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str):
        """移除规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
    
    def get_rule(self, rule_id: str) -> Optional[IntelligentAlertRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: str) -> List[IntelligentAlertRule]:
        """根据分类获取规则"""
        return [
            rule for rule in self.rules.values()
            if rule.tags.get("category") == category
        ]
    
    def get_rules_by_type(self, rule_type: str) -> List[IntelligentAlertRule]:
        """根据类型获取规则"""
        return [
            rule for rule in self.rules.values()
            if rule.tags.get("type") == rule_type
        ]
    
    def get_enabled_rules(self) -> List[IntelligentAlertRule]:
        """获取已启用的规则"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    def enable_rule(self, rule_id: str):
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """获取规则摘要"""
        enabled_rules = self.get_enabled_rules()
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len(enabled_rules),
            "by_category": {
                category: len(self.get_rules_by_category(category))
                for category in set(
                    rule.tags.get("category", "unknown") 
                    for rule in self.rules.values()
                )
            },
            "by_severity": {
                severity.value: len([
                    rule for rule in enabled_rules 
                    if rule.severity == severity
                ])
                for severity in AlertSeverity
            },
            "by_condition_type": {
                condition_type: len([
                    rule for rule in enabled_rules 
                    if rule.condition_type == condition_type
                ])
                for condition_type in set(
                    rule.condition_type for rule in enabled_rules
                )
            }
        }


# 全局规则管理器实例
_intelligent_alert_rule_manager: IntelligentAlertRuleManager = None


def get_intelligent_alert_rule_manager() -> IntelligentAlertRuleManager:
    """获取智能告警规则管理器实例"""
    global _intelligent_alert_rule_manager
    if _intelligent_alert_rule_manager is None:
        _intelligent_alert_rule_manager = IntelligentAlertRuleManager()
    return _intelligent_alert_rule_manager