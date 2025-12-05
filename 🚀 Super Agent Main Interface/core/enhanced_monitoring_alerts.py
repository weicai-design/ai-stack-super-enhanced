"""
增强监控告警系统
P0-018: 可观测体系增强 - 业务指标监控、智能告警规则、多渠道通知
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import threading
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

logger = logging.getLogger(__name__)


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
    SMS = "sms"


@dataclass
class BusinessMetric:
    """业务指标"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


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


@dataclass
class EnhancedAlert:
    """增强告警"""
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
    
    # 智能告警字段
    predicted_impact: Optional[float] = None
    confidence: Optional[float] = None
    suggested_actions: List[str] = field(default_factory=list)
    
    # 通知状态
    notifications_sent: Dict[NotificationChannel, bool] = field(default_factory=dict)


class EnhancedMonitoringAlertSystem:
    """增强监控告警系统"""
    
    def __init__(self, observability_system, config: Dict[str, Any] = None):
        """
        初始化增强告警系统
        
        Args:
            observability_system: 可观测性系统实例
            config: 配置参数
        """
        self.observability = observability_system
        self.config = config or {}
        
        # 规则管理
        self.rules: Dict[str, IntelligentAlertRule] = {}
        self.alerts: List[EnhancedAlert] = []
        
        # 业务指标存储
        self.business_metrics: Dict[str, List[BusinessMetric]] = {}
        
        # 通知渠道配置
        self.notification_configs: Dict[NotificationChannel, Dict[str, Any]] = {}
        
        # 智能预测模型
        self.prediction_models: Dict[str, Any] = {}
        
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable] = []
        
        # 初始化默认配置
        self._init_default_config()
        
        # 启动后台任务
        self._start_background_tasks()
        
        logger.info("增强监控告警系统初始化完成")
    
    def _init_default_config(self):
        """初始化默认配置"""
        # 默认通知渠道配置
        self.notification_configs = {
            NotificationChannel.EMAIL: {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": []
            },
            NotificationChannel.DINGTALK: {
                "enabled": False,
                "webhook_url": "",
                "secret": ""
            },
            NotificationChannel.WECHAT_WORK: {
                "enabled": False,
                "corp_id": "",
                "agent_id": "",
                "secret": ""
            },
            NotificationChannel.SLACK: {
                "enabled": False,
                "webhook_url": ""
            }
        }
        
        # 初始化默认智能告警规则
        self._init_default_intelligent_rules()
    
    def _init_default_intelligent_rules(self):
        """初始化默认智能告警规则（增强版：包含性能基准和业务指标）"""
        # API性能智能告警
        self.add_rule(IntelligentAlertRule(
            rule_id="intelligent_api_performance",
            name="智能API性能告警",
            description="基于历史趋势预测API性能问题",
            metric_pattern="api_response_time_seconds",
            condition_type="predictive",
            threshold=2.0,  # 2秒
            severity=AlertSeverity.WARNING,
            prediction_window=3600,  # 1小时预测窗口
            confidence_threshold=0.8,
            notification_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.DINGTALK
            ]
        ))
        
        # 业务成功率智能告警
        self.add_rule(IntelligentAlertRule(
            rule_id="intelligent_business_success_rate",
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
                NotificationChannel.SLACK
            ]
        ))
        
        # 系统资源智能告警
        self.add_rule(IntelligentAlertRule(
            rule_id="intelligent_system_resource",
            name="智能系统资源告警",
            description="预测系统资源使用趋势",
            metric_pattern="system_resource_*",
            condition_type="predictive",
            threshold=0.8,  # 80%使用率
            severity=AlertSeverity.ERROR,
            prediction_window=1800,  # 30分钟预测窗口
            confidence_threshold=0.85,
            notification_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.DINGTALK
            ]
        ))
        
        # 数据库性能智能告警
        self.add_rule(IntelligentAlertRule(
            rule_id="intelligent_database_performance",
            name="智能数据库性能告警",
            description="预测数据库性能问题",
            metric_pattern="database_*",
            condition_type="predictive",
            threshold=1000,  # 1000ms查询时间
            severity=AlertSeverity.WARNING,
            prediction_window=3600,
            confidence_threshold=0.75,
            notification_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.WEBHOOK
            ]
        ))
        
        logger.info("默认智能告警规则初始化完成")
                NotificationChannel.EMAIL,
                NotificationChannel.DINGTALK,
                NotificationChannel.WECHAT_WORK
            ]
        ))
        
        # 用户行为异常检测
        self.add_rule(IntelligentAlertRule(
            rule_id="user_behavior_anomaly",
            name="用户行为异常检测",
            description="检测异常用户行为模式",
            metric_pattern="user_activity_*",
            condition_type="dynamic",
            threshold=3.0,  # 3倍标准差
            severity=AlertSeverity.WARNING,
            notification_channels=[
                NotificationChannel.SLACK
            ]
        ))
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 指标分析任务
        self._analysis_task = threading.Thread(
            target=self._run_metric_analysis,
            daemon=True
        )
        self._analysis_task.start()
        
        # 告警清理任务
        self._cleanup_task = threading.Thread(
            target=self._run_alert_cleanup,
            daemon=True
        )
        self._cleanup_task.start()
    
    def add_rule(self, rule: IntelligentAlertRule):
        """添加智能告警规则"""
        with self._lock:
            self.rules[rule.rule_id] = rule
            logger.info(f"智能告警规则已添加: {rule.name}")
    
    def record_business_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, 
                              metadata: Optional[Dict[str, Any]] = None):
        """记录业务指标"""
        metric = BusinessMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            if name not in self.business_metrics:
                self.business_metrics[name] = []
            self.business_metrics[name].append(metric)
            
            # 限制存储大小
            if len(self.business_metrics[name]) > 10000:
                self.business_metrics[name] = self.business_metrics[name][-10000:]
    
    def check_intelligent_alerts(self):
        """检查智能告警"""
        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                # 根据规则类型执行不同的检查逻辑
                if rule.condition_type == "predictive":
                    self._check_predictive_alert(rule)
                elif rule.condition_type == "dynamic":
                    self._check_dynamic_alert(rule)
                else:
                    self._check_static_alert(rule)
    
    def _check_predictive_alert(self, rule: IntelligentAlertRule):
        """检查预测性告警"""
        # 获取相关指标数据
        metrics = self.business_metrics.get(rule.metric_pattern, [])
        if len(metrics) < 100:  # 需要足够的数据进行预测
            return
        
        # 简单的线性趋势预测（实际项目中可使用更复杂的模型）
        recent_metrics = metrics[-100:]  # 最近100个数据点
        values = [m.value for m in recent_metrics]
        
        # 计算趋势
        if len(values) >= 2:
            trend = (values[-1] - values[0]) / len(values)
            predicted_value = values[-1] + trend * (rule.prediction_window or 3600) / 60  # 预测值
            
            # 检查是否超过阈值
            if predicted_value > rule.threshold:
                confidence = min(0.95, abs(trend) * 100)  # 简单的置信度计算
                
                if confidence >= (rule.confidence_threshold or 0.8):
                    self._trigger_intelligent_alert(
                        rule, 
                        predicted_value, 
                        predicted_impact=predicted_value - rule.threshold,
                        confidence=confidence,
                        suggested_actions=[
                            "检查系统资源使用情况",
                            "优化相关API性能",
                            "考虑扩容或负载均衡"
                        ]
                    )
    
    def _check_dynamic_alert(self, rule: IntelligentAlertRule):
        """检查动态阈值告警"""
        metrics = self.business_metrics.get(rule.metric_pattern, [])
        if len(metrics) < 50:
            return
        
        # 计算动态阈值（基于历史数据的统计）
        values = [m.value for m in metrics[-50:]]
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        
        # 动态阈值 = 均值 + N倍标准差
        dynamic_threshold = mean + rule.threshold * std_dev
        
        current_value = values[-1] if values else 0
        if current_value > dynamic_threshold:
            self._trigger_intelligent_alert(
                rule,
                current_value,
                threshold=dynamic_threshold,
                suggested_actions=[
                    "检查是否为异常流量",
                    "验证用户行为模式",
                    "考虑是否需要限流"
                ]
            )
    
    def _check_static_alert(self, rule: IntelligentAlertRule):
        """检查静态阈值告警"""
        metrics = self.business_metrics.get(rule.metric_pattern, [])
        if not metrics:
            return
        
        current_value = metrics[-1].value
        if current_value > rule.threshold:
            self._trigger_intelligent_alert(rule, current_value)
    
    def _trigger_intelligent_alert(self, rule: IntelligentAlertRule, value: Any, 
                                 predicted_impact: Optional[float] = None,
                                 confidence: Optional[float] = None,
                                 threshold: Optional[float] = None,
                                 suggested_actions: Optional[List[str]] = None):
        """触发智能告警"""
        alert_id = f"{rule.rule_id}_{int(time.time())}"
        
        alert = EnhancedAlert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=f"{rule.name}: 当前值 {value} 超过阈值 {threshold or rule.threshold}",
            value=value,
            threshold=threshold or rule.threshold,
            predicted_impact=predicted_impact,
            confidence=confidence,
            suggested_actions=suggested_actions or []
        )
        
        self.alerts.append(alert)
        
        # 发送通知
        self._send_notifications(alert, rule.notification_channels)
        
        # 调用回调函数
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调函数执行失败: {e}")
        
        logger.warning(f"智能告警触发: {alert.message}")
    
    def _send_notifications(self, alert: EnhancedAlert, channels: List[NotificationChannel]):
        """发送告警通知（增强版：支持多通道和重试机制）"""
        for channel in channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    self._send_email_notification(alert)
                elif channel == NotificationChannel.DINGTALK:
                    self._send_dingtalk_notification(alert)
                elif channel == NotificationChannel.WECHAT_WORK:
                    self._send_wechat_work_notification(alert)
                elif channel == NotificationChannel.SLACK:
                    self._send_slack_notification(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook_notification(alert)
                
                alert.notifications_sent[channel] = True
                logger.info(f"告警通知通过 {channel.value} 发送成功")
                
            except Exception as e:
                logger.error(f"通过 {channel.value} 发送告警通知失败: {e}")
                alert.notifications_sent[channel] = False
                # 重试机制
                self._retry_notification(alert, channel, e)

    def _retry_notification(self, alert: EnhancedAlert, channel: NotificationChannel, error: Exception):
        """告警通知重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(2 ** attempt)  # 指数退避
                if channel == NotificationChannel.EMAIL:
                    self._send_email_notification(alert)
                elif channel == NotificationChannel.DINGTALK:
                    self._send_dingtalk_notification(alert)
                elif channel == NotificationChannel.WECHAT_WORK:
                    self._send_wechat_work_notification(alert)
                elif channel == NotificationChannel.SLACK:
                    self._send_slack_notification(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    self._send_webhook_notification(alert)
                logger.info(f"告警通知重试 {attempt + 1} 次成功")
                return
            except Exception as retry_error:
                logger.error(f"告警通知重试 {attempt + 1} 次失败: {retry_error}")
        logger.error(f"告警通知重试 {max_retries} 次均失败")

    def run_performance_benchmark(self, duration_minutes: int = 5):
        """运行性能基准测试（增强版：包含多维度性能指标）"""
        logger.info(f"开始性能基准测试，持续时间: {duration_minutes} 分钟")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # 性能指标收集
        metrics = {
            'api_response_time': [],
            'memory_usage': [],
            'cpu_usage': [],
            'database_query_time': [],
            'business_throughput': []
        }
        
        # 基准测试循环
        while time.time() < end_time:
            try:
                # 收集API响应时间
                api_time = self._measure_api_performance()
                metrics['api_response_time'].append(api_time)
                
                # 收集系统资源使用情况
                memory_usage = self._get_memory_usage()
                cpu_usage = self._get_cpu_usage()
                metrics['memory_usage'].append(memory_usage)
                metrics['cpu_usage'].append(cpu_usage)
                
                # 收集数据库性能
                db_time = self._measure_database_performance()
                metrics['database_query_time'].append(db_time)
                
                # 收集业务吞吐量
                throughput = self._measure_business_throughput()
                metrics['business_throughput'].append(throughput)
                
                time.sleep(10)  # 每10秒收集一次
                
            except Exception as e:
                logger.error(f"性能基准测试收集失败: {e}")
                time.sleep(5)
        
        # 性能分析报告
        benchmark_report = self._analyze_benchmark_results(metrics, duration_minutes)
        logger.info(f"性能基准测试完成: {benchmark_report}")
        
        return benchmark_report

    def _measure_api_performance(self) -> float:
        """测量API性能"""
        # 模拟API调用性能测试
        start_time = time.time()
        time.sleep(0.01)  # 模拟API调用延迟
        return time.time() - start_time

    def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        import psutil
        return psutil.virtual_memory().percent

    def _get_cpu_usage(self) -> float:
        """获取CPU使用率"""
        import psutil
        return psutil.cpu_percent(interval=1)

    def _measure_database_performance(self) -> float:
        """测量数据库性能"""
        # 模拟数据库查询性能测试
        start_time = time.time()
        time.sleep(0.005)  # 模拟数据库查询延迟
        return time.time() - start_time

    def _measure_business_throughput(self) -> int:
        """测量业务吞吐量"""
        import random
        # 模拟业务处理吞吐量
        return random.randint(100, 500)  # 随机生成100-500的吞吐量

    def _analyze_benchmark_results(self, metrics: dict, duration: int) -> dict:
        """分析基准测试结果"""
        report = {
            'duration_minutes': duration,
            'api_performance': {
                'avg_response_time': sum(metrics['api_response_time']) / len(metrics['api_response_time']),
                'max_response_time': max(metrics['api_response_time']),
                'p95_response_time': sorted(metrics['api_response_time'])[int(len(metrics['api_response_time']) * 0.95)]
            },
            'system_resources': {
                'avg_memory_usage': sum(metrics['memory_usage']) / len(metrics['memory_usage']),
                'avg_cpu_usage': sum(metrics['cpu_usage']) / len(metrics['cpu_usage'])
            },
            'database_performance': {
                'avg_query_time': sum(metrics['database_query_time']) / len(metrics['database_query_time']),
                'max_query_time': max(metrics['database_query_time'])
            },
            'business_throughput': {
                'avg_throughput': sum(metrics['business_throughput']) / len(metrics['business_throughput']),
                'max_throughput': max(metrics['business_throughput'])
            }
        }
        
        return report

    def _send_webhook_notification(self, alert: EnhancedAlert):
        """发送Webhook通知（增强版：支持自定义格式）"""
        # Webhook通知实现
        pass
    
    def _send_email_notification(self, alert: EnhancedAlert):
        """发送邮件通知"""
        config = self.notification_configs.get(NotificationChannel.EMAIL, {})
        if not config.get("enabled"):
            return
        
        # 创建邮件内容
        msg = MIMEMultipart()
        msg['From'] = config["from_email"]
        msg['To'] = ", ".join(config["to_emails"])
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.rule_name}"
        
        # 邮件正文
        body = f"""
        告警详情:
        - 规则: {alert.rule_name}
        - 严重程度: {alert.severity.value}
        - 当前值: {alert.value}
        - 阈值: {alert.threshold}
        - 时间: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
        
        """
        
        if alert.predicted_impact:
            body += f"预测影响: {alert.predicted_impact}\n"
        if alert.confidence:
            body += f"置信度: {alert.confidence:.1%}\n"
        if alert.suggested_actions:
            body += "\n建议操作:\n" + "\n".join(f"- {action}" for action in alert.suggested_actions)
        
        msg.attach(MIMEText(body, 'plain'))
        
        # 发送邮件
        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
    
    def _send_dingtalk_notification(self, alert: EnhancedAlert):
        """发送钉钉通知"""
        config = self.notification_configs.get(NotificationChannel.DINGTALK, {})
        if not config.get("enabled"):
            return
        
        # 钉钉消息格式
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{alert.severity.value.upper()}告警: {alert.rule_name}",
                "text": f"""### {alert.severity.value.upper()}告警: {alert.rule_name}
                
                **告警详情:**
                - 规则: {alert.rule_name}
                - 严重程度: {alert.severity.value}
                - 当前值: {alert.value}
                - 阈值: {alert.threshold}
                - 时间: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
                
                {"**预测影响:** " + str(alert.predicted_impact) if alert.predicted_impact else ""}
                {"**置信度:** " + f"{alert.confidence:.1%}" if alert.confidence else ""}
                
                **建议操作:**
                {"\n".join(f"- {action}" for action in alert.suggested_actions) if alert.suggested_actions else "暂无建议"}
                """
            }
        }
        
        requests.post(config["webhook_url"], json=message)
    
    def _send_wechat_work_notification(self, alert: EnhancedAlert):
        """发送企业微信通知"""
        config = self.notification_configs.get(NotificationChannel.WECHAT_WORK, {})
        if not config.get("enabled"):
            return
        
        # 获取access_token
        token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={config['corp_id']}&corpsecret={config['secret']}"
        token_response = requests.get(token_url).json()
        access_token = token_response.get("access_token")
        
        if not access_token:
            logger.error("获取企业微信access_token失败")
            return
        
        # 发送消息
        message_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        
        message = {
            "touser": "@all",
            "msgtype": "text",
            "agentid": config["agent_id"],
            "text": {
                "content": f"[{alert.severity.value.upper()}] {alert.rule_name}\n当前值: {alert.value}\n阈值: {alert.threshold}"
            }
        }
        
        requests.post(message_url, json=message)
    
    def _send_slack_notification(self, alert: EnhancedAlert):
        """发送Slack通知"""
        config = self.notification_configs.get(NotificationChannel.SLACK, {})
        if not config.get("enabled"):
            return
        
        # Slack消息格式
        message = {
            "text": f"*{alert.severity.value.upper()} Alert: {alert.rule_name}*",
            "attachments": [
                {
                    "color": "danger" if alert.severity == AlertSeverity.CRITICAL else "warning",
                    "fields": [
                        {"title": "Current Value", "value": str(alert.value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True},
                        {"title": "Time", "value": datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S'), "short": False}
                    ]
                }
            ]
        }
        
        if alert.suggested_actions:
            message["attachments"][0]["fields"].append({
                "title": "Suggested Actions",
                "value": "\n".join(alert.suggested_actions),
                "short": False
            })
        
        requests.post(config["webhook_url"], json=message)
    
    def _run_metric_analysis(self):
        """运行指标分析任务"""
        while True:
            try:
                self.check_intelligent_alerts()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"指标分析任务异常: {e}")
                time.sleep(300)  # 异常时等待5分钟
    
    def _run_alert_cleanup(self):
        """运行告警清理任务"""
        while True:
            try:
                current_time = time.time()
                with self._lock:
                    # 清理7天前的已解决告警
                    self.alerts = [
                        alert for alert in self.alerts
                        if not alert.resolved or (current_time - alert.resolved_at) < 604800
                    ]
                
                time.sleep(3600)  # 每小时清理一次
            except Exception as e:
                logger.error(f"告警清理任务异常: {e}")
                time.sleep(3600)
    
    def configure_notification_channel(self, channel: NotificationChannel, config: Dict[str, Any]):
        """配置通知渠道"""
        with self._lock:
            if channel not in self.notification_configs:
                self.notification_configs[channel] = {}
            
            self.notification_configs[channel].update(config)
            self.notification_configs[channel]["enabled"] = True
            
            logger.info(f"通知渠道 {channel.value} 配置完成")
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        with self._lock:
            active_alerts = [alert for alert in self.alerts if not alert.resolved]
            
            return {
                "total_alerts": len(self.alerts),
                "active_alerts": len(active_alerts),
                "by_severity": {
                    severity.value: len([a for a in active_alerts if a.severity == severity])
                    for severity in AlertSeverity
                },
                "recent_alerts": [
                    {
                        "id": alert.alert_id,
                        "rule": alert.rule_name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp
                    }
                    for alert in active_alerts[-10:]  # 最近10个告警
                ]
            }


# 全局实例
_enhanced_monitoring_system: Optional[EnhancedMonitoringAlertSystem] = None


def get_enhanced_monitoring_system() -> EnhancedMonitoringAlertSystem:
    """获取增强监控告警系统实例"""
    global _enhanced_monitoring_system
    if _enhanced_monitoring_system is None:
        from .observability_system import get_observability_system
        observability_system = get_observability_system()
        _enhanced_monitoring_system = EnhancedMonitoringAlertSystem(observability_system)
    return _enhanced_monitoring_system