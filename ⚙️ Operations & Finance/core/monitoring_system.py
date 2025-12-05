"""
运营财务数据监控系统 - 生产级实现
实时监控专家运行状态、性能指标和告警管理
支持分布式追踪、性能优化和弹性容错
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import threading
from collections import defaultdict, deque
import statistics
from enum import Enum

# 导入结构化日志模块
try:
    from core.structured_logging import get_logger, trace_operation, get_performance_monitor
except ImportError:
    # 回退到本地实现
    import logging
    from datetime import datetime
    from typing import Dict, Any
    
    class PerformanceMonitor:
        def record_performance(self, name: str, value: float, tags: Dict[str, str] = None):
            pass
    
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_performance_monitor():
        return PerformanceMonitor()
    
    class trace_operation:
        def __init__(self, name: str):
            self.name = name
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass


class AlertSeverity(Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型枚举"""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_COUNT = "error_count"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_COUNT = "request_count"


@dataclass
class ExpertMetric:
    """专家指标数据类 - 生产级增强"""
    expert_name: str
    metric_type: str  # MetricType枚举值
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    source: str = "monitor"  # 指标来源
    confidence: float = 1.0  # 数据置信度


@dataclass
class Alert:
    """告警数据类"""
    id: str
    type: str
    expert_name: str
    severity: AlertSeverity
    message: str
    value: Any
    threshold: Any
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: str = None
    acknowledged_at: datetime = None


@dataclass
class ExpertStatus:
    """专家状态数据类 - 生产级增强"""
    expert_name: str
    is_healthy: bool
    health_score: float  # 健康评分 (0-100)
    last_activity: datetime
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    success_rate: float
    error_count: int
    throughput: float  # 请求/分钟
    uptime: float  # 运行时间比例
    performance_score: float  # 性能评分 (0-100)
    trend: str  # "improving", "stable", "degrading"
    recommendations: List[str] = None


class ExpertMonitor:
    """专家监控器 - 生产级增强"""
    
    def __init__(self, window_size: int = 1000):  # 增大窗口大小
        self.logger = get_logger("expert_monitor")
        self.performance_monitor = get_performance_monitor()
        self.window_size = window_size
        
        # 存储指标数据
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.status: Dict[str, ExpertStatus] = {}
        
        # 告警管理
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        
        # 监控配置 - 生产级阈值
        self.alert_thresholds = {
            "response_time": {
                "warning": 1.0,  # 1秒
                "error": 3.0,    # 3秒
                "critical": 5.0  # 5秒
            },
            "error_rate": {
                "warning": 0.05,  # 5%
                "error": 0.1,     # 10%
                "critical": 0.2   # 20%
            },
            "throughput": {
                "warning": 50.0,   # 50请求/分钟
                "error": 100.0,    # 100请求/分钟
                "critical": 200.0  # 200请求/分钟
            }
        }
        
        # 监控任务
        self.monitoring_task = None
        self.is_running = False
        self.monitoring_interval = 30  # 30秒
        
        # 健康检查相关
        self.last_health_check = datetime.now()
        self.health_check_interval = 30  # 30秒
        
        # 性能优化
        self._metrics_lock = threading.RLock()
        self._status_cache = None
        self._cache_ttl = 10  # 缓存10秒
        self._last_cache_update = datetime.min
        
        # 统计信息
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_errors = 0
        
        # 告警处理器
        self.alert_handlers: List[Callable] = []
    
    def record_metric(self, expert_name: str, metric_type: str, value: float, tags: Dict[str, str] = None):
        """记录专家指标 - 生产级增强"""
        with self._metrics_lock:
            metric = ExpertMetric(
                expert_name=expert_name,
                metric_type=metric_type,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                source="monitor",
                confidence=1.0
            )
            
            key = f"{expert_name}:{metric_type}"
            self.metrics[key].append(metric)
            
            # 记录性能指标
            self.performance_monitor.record_performance(
                f"expert.{expert_name}.{metric_type}",
                value,
                tags=tags or {}
            )
            
            # 记录日志
            self.logger.debug(
                f"记录专家指标: {expert_name}.{metric_type} - 值: {value}, 标签: {tags}"
            )
    
    def record_request(self, expert_name: str, response_time: float, success: bool, error_type: str = None):
        """记录请求指标 - 生产级增强"""
        with trace_operation("record_expert_request") as trace:
            # 更新统计信息
            self.total_requests += 1
            if not success:
                self.total_errors += 1
            
            # 记录响应时间
            self.record_metric(expert_name, MetricType.RESPONSE_TIME.value, response_time)
            
            # 记录成功/失败
            if success:
                self.record_metric(expert_name, "success_count", 1.0)
            else:
                self.record_metric(expert_name, MetricType.ERROR_COUNT.value, 1.0, {"error_type": error_type or "unknown"})
            
            # 记录吞吐量
            self.record_metric(expert_name, MetricType.REQUEST_COUNT.value, 1.0)
            
            # 记录性能指标
            self.performance_monitor.record_performance(
                f"expert.{expert_name}.request_time",
                response_time,
                tags={"success": str(success), "error_type": error_type or "none"}
            )
            
            # 清除缓存
            self._status_cache = None
    
    def calculate_status(self, expert_name: str) -> ExpertStatus:
        """计算专家状态 - 生产级增强"""
        with trace_operation("calculate_expert_status") as trace:
            now = datetime.now()
            
            # 检查缓存
            if (self._status_cache and 
                (now - self._last_cache_update).total_seconds() < self._cache_ttl):
                return self._status_cache.get(expert_name, self._create_default_status(expert_name))
            
            # 获取相关指标
            response_times = [m.value for m in self.metrics.get(f"{expert_name}:{MetricType.RESPONSE_TIME.value}", [])]
            success_counts = [m.value for m in self.metrics.get(f"{expert_name}:success_count", [])]
            error_counts = [m.value for m in self.metrics.get(f"{expert_name}:{MetricType.ERROR_COUNT.value}", [])]
            request_counts = [m.value for m in self.metrics.get(f"{expert_name}:{MetricType.REQUEST_COUNT.value}", [])]
            
            # 计算统计指标
            response_time_avg = statistics.mean(response_times) if response_times else 0
            response_time_p95 = statistics.quantiles(response_times, n=20)[-1] if len(response_times) >= 20 else response_time_avg
            response_time_p99 = statistics.quantiles(response_times, n=100)[-1] if len(response_times) >= 100 else response_time_avg
            
            total_success = sum(success_counts)
            total_errors = sum(error_counts)
            total_requests = total_success + total_errors
            
            success_rate = total_success / total_requests if total_requests > 0 else 1.0
            
            # 计算吞吐量（最近5分钟的请求数）
            recent_requests = [m for m in self.metrics.get(f"{expert_name}:{MetricType.REQUEST_COUNT.value}", []) 
                              if (now - m.timestamp).total_seconds() <= 300]
            throughput = len(recent_requests) / 5.0  # 请求/分钟
            
            # 计算运行时间比例（最近1小时）
            hour_requests = [m for m in self.metrics.get(f"{expert_name}:{MetricType.REQUEST_COUNT.value}", []) 
                            if (now - m.timestamp).total_seconds() <= 3600]
            uptime = min(len(hour_requests) / 60.0, 1.0)  # 假设每分钟应该有请求
            
            # 计算健康评分 (0-100)
            health_score = self._calculate_health_score(
                response_time_avg, success_rate, throughput, uptime
            )
            
            # 计算性能评分 (0-100)
            performance_score = self._calculate_performance_score(
                response_time_avg, response_time_p95, response_time_p99, success_rate, throughput
            )
            
            # 判断趋势
            trend = self._detect_trend(expert_name)
            
            # 生成建议
            recommendations = self._generate_recommendations(
                response_time_avg, success_rate, throughput, health_score
            )
            
            # 判断健康状态
            is_healthy = health_score >= 80  # 健康评分80分以上为健康
            
            status = ExpertStatus(
                expert_name=expert_name,
                is_healthy=is_healthy,
                health_score=health_score,
                last_activity=now,
                response_time_avg=response_time_avg,
                response_time_p95=response_time_p95,
                response_time_p99=response_time_p99,
                success_rate=success_rate,
                error_count=total_errors,
                throughput=throughput,
                uptime=uptime,
                performance_score=performance_score,
                trend=trend,
                recommendations=recommendations
            )
            
            # 更新缓存
            if not self._status_cache:
                self._status_cache = {}
            self._status_cache[expert_name] = status
            self._last_cache_update = now
            
            self.status[expert_name] = status
        return status
    
    def _create_default_status(self, expert_name: str) -> ExpertStatus:
        """创建默认状态"""
        now = datetime.now()
        return ExpertStatus(
            expert_name=expert_name,
            is_healthy=False,
            health_score=0.0,
            last_activity=now,
            response_time_avg=0.0,
            response_time_p95=0.0,
            response_time_p99=0.0,
            success_rate=1.0,
            error_count=0,
            throughput=0.0,
            uptime=0.0,
            performance_score=0.0,
            trend="unknown",
            recommendations=["专家暂无活动数据"]
        )
    
    def _calculate_health_score(self, response_time: float, success_rate: float, 
                               throughput: float, uptime: float) -> float:
        """计算健康评分 (0-100)"""
        # 响应时间评分 (权重: 30%)
        response_time_score = max(0, 100 - (response_time * 20))  # 每0.05秒扣1分
        
        # 成功率评分 (权重: 40%)
        success_rate_score = success_rate * 100
        
        # 吞吐量评分 (权重: 20%)
        throughput_score = min(throughput / 10.0 * 100, 100)  # 10请求/分钟为满分
        
        # 运行时间评分 (权重: 10%)
        uptime_score = uptime * 100
        
        # 加权平均
        health_score = (
            response_time_score * 0.3 +
            success_rate_score * 0.4 +
            throughput_score * 0.2 +
            uptime_score * 0.1
        )
        
        return max(0, min(100, health_score))
    
    def _calculate_performance_score(self, response_time_avg: float, response_time_p95: float,
                                   response_time_p99: float, success_rate: float, throughput: float) -> float:
        """计算性能评分 (0-100)"""
        # 平均响应时间评分 (权重: 25%)
        avg_response_score = max(0, 100 - (response_time_avg * 40))
        
        # P95响应时间评分 (权重: 25%)
        p95_response_score = max(0, 100 - (response_time_p95 * 30))
        
        # P99响应时间评分 (权重: 20%)
        p99_response_score = max(0, 100 - (response_time_p99 * 20))
        
        # 成功率评分 (权重: 20%)
        success_rate_score = success_rate * 100
        
        # 吞吐量评分 (权重: 10%)
        throughput_score = min(throughput / 20.0 * 100, 100)
        
        # 加权平均
        performance_score = (
            avg_response_score * 0.25 +
            p95_response_score * 0.25 +
            p99_response_score * 0.20 +
            success_rate_score * 0.20 +
            throughput_score * 0.10
        )
        
        return max(0, min(100, performance_score))
    
    def get_expert_status(self, expert_name: str) -> ExpertStatus:
        """获取专家状态 - 生产级增强"""
        with trace_operation("get_expert_status") as trace:
            try:
                # 检查缓存
                now = datetime.now()
                if (self._status_cache and 
                    (now - self._last_cache_update).total_seconds() < self._cache_ttl and
                    expert_name in self._status_cache):
                    return self._status_cache[expert_name]
                
                # 计算状态
                status = self.calculate_status(expert_name)
                
                # 记录日志
                self.logger.debug(
                    "获取专家状态",
                    expert_name=expert_name,
                    health_score=status.health_score,
                    performance_score=status.performance_score
                )
                
                return status
                
            except Exception as e:
                self.logger.error(
                    "获取专家状态失败",
                    expert_name=expert_name,
                    error=str(e)
                )
                return self._create_default_status(expert_name)
    
    def _detect_trend(self, expert_name: str) -> str:
        """检测趋势"""
        # 获取最近30分钟的数据
        now = datetime.now()
        recent_metrics = [
            m for m in self.metrics.get(f"{expert_name}:{MetricType.RESPONSE_TIME.value}", [])
            if (now - m.timestamp).total_seconds() <= 1800
        ]
        
        if len(recent_metrics) < 10:
            return "unknown"
        
        # 计算趋势
        values = [m.value for m in recent_metrics]
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg < first_avg * 0.9:  # 改善10%以上
            return "improving"
        elif second_avg > first_avg * 1.1:  # 恶化10%以上
            return "degrading"
        else:
            return "stable"
    
    def _generate_recommendations(self, response_time: float, success_rate: float,
                                throughput: float, health_score: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if response_time > 1.0:
            recommendations.append("响应时间较高，建议优化处理逻辑或增加缓存")
        
        if success_rate < 0.95:
            recommendations.append("成功率较低，建议检查错误处理机制")
        
        if throughput < 5.0:
            recommendations.append("吞吐量较低，建议检查并发处理能力")
        
        if health_score < 60:
            recommendations.append("健康评分较低，建议全面检查系统状态")
        
        if not recommendations:
            recommendations.append("系统运行良好，继续保持当前配置")
        
        return recommendations
    
    def get_all_status(self) -> Dict[str, ExpertStatus]:
        """获取所有专家状态 - 生产级增强"""
        with trace_operation("get_all_status") as trace:
            # 获取所有已知的专家
            experts = set()
            for key in self.metrics.keys():
                expert_name = key.split(":")[0]
                experts.add(expert_name)
            
            statuses = {}
            
            # 计算每个专家的状态
            for expert in experts:
                status = self.calculate_status(expert)
                if status:
                    statuses[expert] = status
            
            # 记录性能指标
            self.performance_monitor.record_performance(
                "monitoring.get_all_status",
                0.0,  # 实际时间在循环中记录
                tags={"expert_count": str(len(statuses))}
            )
            
            self.logger.debug(
                "获取所有专家状态",
                expert_count=len(statuses)
            )
            
            return statuses
    
    def get_alerts(self, expert_name: Optional[str] = None, severity: Optional[AlertSeverity] = None, 
                  limit: int = 50) -> List[Alert]:
        """获取告警信息 - 生产级增强"""
        with trace_operation("get_alerts") as trace:
            # 检查告警
            alerts = []
            statuses = self.get_all_status()
            
            for expert_name_current, status in statuses.items():
                # 检查响应时间告警
                response_time_alerts = self._check_response_time_alerts(expert_name_current, status)
                alerts.extend(response_time_alerts)
                
                # 检查错误率告警
                error_rate_alerts = self._check_error_rate_alerts(expert_name_current, status)
                alerts.extend(error_rate_alerts)
                
                # 检查吞吐量告警
                throughput_alerts = self._check_throughput_alerts(expert_name_current, status)
                alerts.extend(throughput_alerts)
                
                # 检查健康状态告警
                health_alerts = self._check_health_alerts(expert_name_current, status)
                alerts.extend(health_alerts)
            
            # 处理新告警
            self._process_new_alerts(alerts)
            
            # 获取当前告警列表
            current_alerts = list(self.alerts.values())
            
            # 过滤条件
            if expert_name:
                current_alerts = [alert for alert in current_alerts if alert.expert_name == expert_name]
            
            if severity:
                current_alerts = [alert for alert in current_alerts if alert.severity == severity]
            
            # 按时间排序，最新的在前
            current_alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 限制返回数量
            result = current_alerts[:limit]
            
            # 记录查询
            self.logger.debug(
                f"获取告警信息 - 专家: {expert_name or 'all'}, 严重性: {severity.value if severity else 'all'}, "
                f"限制: {limit}, 返回: {len(result)}, 严重告警: {len([a for a in result if a.severity == AlertSeverity.CRITICAL])}"
            )
            
            return result
    
    def get_metrics(self, expert_name: str, metric_type: str, limit: int = 50) -> List[ExpertMetric]:
        """获取指标数据"""
        key = f"{expert_name}:{metric_type}"
        metrics = list(self.metrics.get(key, []))
        
        # 按时间排序，最新的在前
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制返回数量
        return metrics[:limit]
    
    def _check_response_time_alerts(self, expert_name: str, status: ExpertStatus) -> List[Alert]:
        """检查响应时间告警"""
        alerts = []
        thresholds = self.alert_thresholds["response_time"]
        
        if status.response_time_avg > thresholds["critical"]:
            alerts.append(self._create_alert(
                expert_name, "response_time", AlertSeverity.CRITICAL,
                f"专家 {expert_name} 响应时间严重过高: {status.response_time_avg:.2f}秒",
                status.response_time_avg, thresholds["critical"]
            ))
        elif status.response_time_avg > thresholds["error"]:
            alerts.append(self._create_alert(
                expert_name, "response_time", AlertSeverity.ERROR,
                f"专家 {expert_name} 响应时间过高: {status.response_time_avg:.2f}秒",
                status.response_time_avg, thresholds["error"]
            ))
        elif status.response_time_avg > thresholds["warning"]:
            alerts.append(self._create_alert(
                expert_name, "response_time", AlertSeverity.WARNING,
                f"专家 {expert_name} 响应时间偏高: {status.response_time_avg:.2f}秒",
                status.response_time_avg, thresholds["warning"]
            ))
        
        return alerts
    
    def _check_error_rate_alerts(self, expert_name: str, status: ExpertStatus) -> List[Alert]:
        """检查错误率告警"""
        alerts = []
        error_rate = 1 - status.success_rate
        thresholds = self.alert_thresholds["error_rate"]
        
        if error_rate > thresholds["critical"]:
            alerts.append(self._create_alert(
                expert_name, "error_rate", AlertSeverity.CRITICAL,
                f"专家 {expert_name} 错误率严重过高: {error_rate:.2%}",
                error_rate, thresholds["critical"]
            ))
        elif error_rate > thresholds["error"]:
            alerts.append(self._create_alert(
                expert_name, "error_rate", AlertSeverity.ERROR,
                f"专家 {expert_name} 错误率过高: {error_rate:.2%}",
                error_rate, thresholds["error"]
            ))
        elif error_rate > thresholds["warning"]:
            alerts.append(self._create_alert(
                expert_name, "error_rate", AlertSeverity.WARNING,
                f"专家 {expert_name} 错误率偏高: {error_rate:.2%}",
                error_rate, thresholds["warning"]
            ))
        
        return alerts
    
    def _check_throughput_alerts(self, expert_name: str, status: ExpertStatus) -> List[Alert]:
        """检查吞吐量告警"""
        alerts = []
        thresholds = self.alert_thresholds["throughput"]
        
        if status.throughput > thresholds["critical"]:
            alerts.append(self._create_alert(
                expert_name, "throughput", AlertSeverity.CRITICAL,
                f"专家 {expert_name} 吞吐量严重过高: {status.throughput:.1f} 请求/分钟",
                status.throughput, thresholds["critical"]
            ))
        elif status.throughput > thresholds["error"]:
            alerts.append(self._create_alert(
                expert_name, "throughput", AlertSeverity.ERROR,
                f"专家 {expert_name} 吞吐量过高: {status.throughput:.1f} 请求/分钟",
                status.throughput, thresholds["error"]
            ))
        elif status.throughput > thresholds["warning"]:
            alerts.append(self._create_alert(
                expert_name, "throughput", AlertSeverity.WARNING,
                f"专家 {expert_name} 吞吐量偏高: {status.throughput:.1f} 请求/分钟",
                status.throughput, thresholds["warning"]
            ))
        
        return alerts
    
    def _check_health_alerts(self, expert_name: str, status: ExpertStatus) -> List[Alert]:
        """检查健康状态告警"""
        alerts = []
        
        if not status.is_healthy:
            alerts.append(self._create_alert(
                expert_name, "health", AlertSeverity.CRITICAL,
                f"专家 {expert_name} 健康状态异常 (健康评分: {status.health_score:.1f})",
                status.health_score, 80.0
            ))
        
        if status.health_score < 60:
            alerts.append(self._create_alert(
                expert_name, "health_score", AlertSeverity.ERROR,
                f"专家 {expert_name} 健康评分过低: {status.health_score:.1f}",
                status.health_score, 60.0
            ))
        
        return alerts
    
    def _create_alert(self, expert_name: str, alert_type: str, severity: AlertSeverity,
                     message: str, value: Any, threshold: Any) -> Alert:
        """创建告警"""
        alert_id = f"{expert_name}_{alert_type}_{int(time.time())}"
        return Alert(
            id=alert_id,
            type=alert_type,
            expert_name=expert_name,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold,
            timestamp=datetime.now()
        )
    
    def _process_new_alerts(self, new_alerts: List[Alert]):
        """处理新告警"""
        for alert in new_alerts:
            # 检查是否已存在相同告警
            existing_alert = self.alerts.get(alert.id)
            if existing_alert:
                # 更新现有告警
                existing_alert.timestamp = datetime.now()
                existing_alert.value = alert.value
            else:
                # 添加新告警
                self.alerts[alert.id] = alert
                self.alert_history.append(alert)
                
                # 记录日志
                self.logger.warning(
                    f"新告警: {alert.message} - 告警ID: {alert.id}, 专家: {alert.expert_name}, "
                    f"类型: {alert.type}, 严重性: {alert.severity.value}, 值: {alert.value}, 阈值: {alert.threshold}"
                )
                
                # 调用告警处理器
                self._trigger_alert_handlers(alert)
        
        # 清理已解决的告警
        self._cleanup_resolved_alerts(new_alerts)
    
    def _trigger_alert_handlers(self, alert: Alert):
        """触发告警处理器"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(
                    f"告警处理器执行失败 - 告警ID: {alert.id}, 处理器: {handler}, 错误: {e}"
                )
    
    def _cleanup_resolved_alerts(self, current_alerts: List[Alert]):
        """清理已解决的告警"""
        current_alert_ids = {alert.id for alert in current_alerts}
        resolved_alerts = []
        
        for alert_id in list(self.alerts.keys()):
            if alert_id not in current_alert_ids:
                resolved_alerts.append(self.alerts[alert_id])
                del self.alerts[alert_id]
        
        # 记录已解决的告警
        for alert in resolved_alerts:
            self.logger.info(
                f"告警已解决: {alert.message}",
                alert_id=alert.id,
                expert_name=alert.expert_name,
                alert_type=alert.type
            )
    
    async def start_monitoring(self):
        """启动监控任务 - 生产级增强"""
        with trace_operation("start_monitoring") as trace:
            if self.is_running:
                self.logger.warning("监控系统已在运行中")
                return
            
            self.is_running = True
            self.logger.info("启动专家监控系统", monitoring_interval=self.monitoring_interval)
            
            async def monitoring_loop():
                loop_count = 0
                while self.is_running:
                    try:
                        loop_count += 1
                        
                        # 记录性能指标
                        self.performance_monitor.record_performance(
                            "monitoring.loop_execution",
                            0.0,  # 将在循环结束时记录实际时间
                            tags={"loop_count": str(loop_count)}
                        )
                        
                        loop_start = time.time()
                        
                        # 检查告警
                        alerts = self.check_alerts()
                        
                        # 记录监控状态
                        statuses = self.get_all_status()
                        healthy_count = sum(1 for s in statuses.values() if s.is_healthy)
                        
                        # 记录监控报告
                        self.logger.info(
                            "专家监控状态报告",
                            expert_count=len(statuses),
                            healthy_count=healthy_count,
                            unhealthy_count=len(statuses) - healthy_count,
                            total_alerts=len(alerts),
                            critical_alerts=len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
                            loop_count=loop_count
                        )
                        
                        # 记录性能指标
                        loop_time = time.time() - loop_start
                        self.performance_monitor.record_performance(
                            "monitoring.loop_execution",
                            loop_time,
                            tags={"loop_count": str(loop_count)}
                        )
                        
                        # 等待监控间隔
                        await asyncio.sleep(self.monitoring_interval)
                        
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        self.logger.error("监控任务异常", error=str(e), loop_count=loop_count)
                        await asyncio.sleep(10)  # 异常后等待10秒
            
            self.monitoring_task = asyncio.create_task(monitoring_loop())
            self.logger.info("监控任务已启动", task_id=id(self.monitoring_task))
    
    async def stop_monitoring(self):
        """停止监控任务 - 生产级增强"""
        with trace_operation("stop_monitoring") as trace:
            if not self.is_running:
                self.logger.warning("监控系统未在运行")
                return
            
            self.is_running = False
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                finally:
                    self.monitoring_task = None
            
            self.logger.info("停止专家监控系统", total_requests=self.total_requests, total_errors=self.total_errors)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查 - 生产级增强"""
        with trace_operation("health_check") as trace:
            try:
                self.last_health_check = datetime.now()
                
                # 获取所有专家状态
                statuses = self.get_all_status()
                alerts = self.check_alerts()
                
                # 计算系统健康状态
                total_experts = len(statuses)
                healthy_experts = sum(1 for s in statuses.values() if s.is_healthy)
                
                # 计算系统健康评分
                system_health_score = 0
                if statuses:
                    system_health_score = sum(s.health_score for s in statuses.values()) / len(statuses)
                
                # 检查告警状态
                critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
                
                # 检查监控任务状态
                monitoring_status = "running" if self.is_running else "stopped"
                if self.is_running and not self.monitoring_task:
                    monitoring_status = "error"
                
                # 检查缓存状态
                cache_hit_rate = 0
                if hasattr(self, 'status_cache_hits') and hasattr(self, 'status_cache_misses'):
                    if self.status_cache_hits + self.status_cache_misses > 0:
                        cache_hit_rate = self.status_cache_hits / (self.status_cache_hits + self.status_cache_misses)
                
                # 构建健康检查结果
                health_info = {
                    "status": "healthy" if (system_health_score > 80 and not critical_alerts) else "degraded",
                    "monitoring_status": monitoring_status,
                    "system_health_score": round(system_health_score, 2),
                    "experts_count": total_experts,
                    "healthy_experts": healthy_experts,
                    "unhealthy_experts": total_experts - healthy_experts,
                    "metrics_count": sum(len(metrics) for metrics in self.metrics.values()),
                    "requests_count": self.total_requests,
                    "errors_count": self.total_errors,
                    "error_rate": round(self.total_errors / max(self.total_requests, 1), 4),
                    "alerts_count": len(alerts),
                    "critical_alerts": len(critical_alerts),
                    "cache_hit_rate": round(cache_hit_rate, 4),
                    "cache_hits": getattr(self, 'status_cache_hits', 0),
                    "cache_misses": getattr(self, 'status_cache_misses', 0),
                    "timestamp": self.last_health_check.isoformat(),
                    "uptime": (datetime.now() - self.start_time).total_seconds() if hasattr(self, 'start_time') else 0,
                    "last_health_check": self.last_health_check.isoformat(),
                    "monitoring_active": self.is_running
                }
                
                # 记录健康检查结果
                self.logger.info(f"系统健康检查 - 状态: {health_info['status']}, 健康评分: {health_info['system_health_score']}, 专家数: {health_info['experts_count']}")
                return health_info
            
            except Exception as e:
                self.logger.error(f"监控系统健康检查失败 - 错误: {e}")
                return {
                    "system_status": "error",
                    "error": str(e),
                    "last_health_check": datetime.now().isoformat()
                }


class MonitoringAPI:
    """监控API - 生产级增强"""
    
    def __init__(self, monitor: ExpertMonitor):
        self.monitor = monitor
        self.logger = get_logger("monitoring_api")
    
    def get_expert_status(self, expert_name: str = None, include_metrics: bool = False, 
                         include_alerts: bool = False) -> Dict[str, Any]:
        """获取专家状态 - 生产级增强"""
        with trace_operation("api_get_expert_status") as trace:
            try:
                if expert_name:
                    status = self.monitor.calculate_status(expert_name)
                    result = {
                        "success": True,
                        "expert_name": expert_name,
                        "status": {
                            "is_healthy": status.is_healthy,
                            "health_score": status.health_score,
                            "last_activity": status.last_activity.isoformat(),
                            "response_time_avg": status.response_time_avg,
                            "response_time_p95": status.response_time_p95,
                            "response_time_p99": status.response_time_p99,
                            "success_rate": status.success_rate,
                            "error_count": status.error_count,
                            "throughput": status.throughput,
                            "uptime": status.uptime,
                            "performance_score": status.performance_score,
                            "trend": status.trend,
                            "recommendations": status.recommendations
                        },
                        "trace_id": trace.request_id
                    }
                    
                    # 包含指标数据
                    if include_metrics:
                        key = f"{expert_name}:{MetricType.RESPONSE_TIME.value}"
                        metrics = list(self.monitor.metrics.get(key, []))[-50:]
                        result["metrics"] = [
                            {
                                "value": m.value,
                                "timestamp": m.timestamp.isoformat(),
                                "tags": m.tags
                            }
                            for m in metrics
                        ]
                    
                    # 包含告警数据
                    if include_alerts:
                        alerts = self.monitor.get_alerts(expert_name=expert_name, limit=10)
                        result["alerts"] = alerts
                    
                    self.logger.debug(
                        f"API获取专家状态 - 专家: {expert_name}, 包含指标: {include_metrics}, 包含告警: {include_alerts}"
                    )
                    
                    return result
                else:
                    statuses = self.monitor.get_all_status()
                    result = {
                        "success": True,
                        "statuses": {
                            name: {
                                "is_healthy": status.is_healthy,
                                "health_score": status.health_score,
                                "last_activity": status.last_activity.isoformat(),
                                "response_time_avg": status.response_time_avg,
                                "response_time_p95": status.response_time_p95,
                                "response_time_p99": status.response_time_p99,
                                "success_rate": status.success_rate,
                                "error_count": status.error_count,
                                "throughput": status.throughput,
                                "uptime": status.uptime,
                                "performance_score": status.performance_score,
                                "trend": status.trend,
                                "recommendations": status.recommendations
                            }
                            for name, status in statuses.items()
                        },
                        "trace_id": trace.request_id
                    }
                    
                    # 包含摘要信息
                    summary = {
                        "total_experts": len(statuses),
                        "healthy_experts": sum(1 for s in statuses.values() if s.is_healthy),
                        "average_health_score": round(
                            sum(s.health_score for s in statuses.values()) / max(len(statuses), 1), 2
                        ) if statuses else 0,
                        "total_alerts": len(self.monitor.get_alerts()),
                        "critical_alerts": len([a for a in self.monitor.get_alerts() if a.severity == AlertSeverity.CRITICAL]),
                        "timestamp": datetime.now().isoformat()
                    }
                    result["summary"] = summary
                    
                    self.logger.debug(f"API获取所有专家状态 - 专家数: {len(statuses)}")
                    
                    return result
                    
            except Exception as e:
                self.logger.error(f"API获取专家状态异常 - 专家: {expert_name or 'all'}, 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "expert_name": expert_name or "all",
                    "trace_id": trace.request_id
                }
    
    def get_alerts(self, expert_name: Optional[str] = None, severity: Optional[AlertSeverity] = None, 
                  limit: int = 50) -> Dict[str, Any]:
        """获取告警信息 - 生产级增强"""
        with trace_operation("api_get_alerts") as trace:
            try:
                alerts = self.monitor.get_alerts(expert_name, severity, limit)
                
                result = {
                    "success": True,
                    "alerts": alerts,
                    "total": len(alerts),
                    "critical": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
                    "warning": len([a for a in alerts if a.severity == AlertSeverity.WARNING]),
                    "info": len([a for a in alerts if a.severity == AlertSeverity.INFO]),
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": trace.request_id
                }
                
                self.logger.debug(
                    f"API获取告警信息 - 专家: {expert_name or 'all'}, 严重性: {severity.value if severity else 'all'}, "
                    f"限制: {limit}, 总告警: {len(alerts)}"
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"API获取告警信息异常 - 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trace_id": trace.request_id
                }
    
    def get_metrics(self, expert_name: str, metric_type: str, limit: int = 50, aggregate: bool = False) -> Dict[str, Any]:
        """获取指标数据 - 生产级增强"""
        with trace_operation("api_get_metrics") as trace:
            try:
                key = f"{expert_name}:{metric_type}"
                metrics = list(self.monitor.metrics.get(key, []))[-limit:]
                
                result = {
                    "success": True,
                    "expert_name": expert_name,
                    "metric_type": metric_type,
                    "metrics": [
                        {
                            "value": m.value,
                            "timestamp": m.timestamp.isoformat(),
                            "tags": m.tags
                        }
                        for m in metrics
                    ],
                    "total": len(metrics),
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": trace.request_id
                }
                
                # 聚合统计
                if aggregate and metrics:
                    values = [m.value for m in metrics]
                    result["aggregate"] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "latest": values[-1] if values else 0
                    }
                
                self.logger.debug(
                    f"API获取专家指标 - 专家: {expert_name}, 指标类型: {metric_type}, "
                    f"限制: {limit}, 聚合: {aggregate}, 返回数量: {len(metrics)}"
                )
                
                return result
                
            except Exception as e:
                self.logger.error(f"API获取专家指标异常 - 专家: {expert_name}, 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "expert_name": expert_name,
                    "trace_id": trace.request_id
                }
    
    def health_check(self, detailed: bool = False) -> Dict[str, Any]:
        """健康检查 - 生产级增强"""
        with trace_operation("api_health_check") as trace:
            try:
                health_info = self.monitor.health_check()
                
                if detailed:
                    # 添加详细监控信息
                    statuses = self.monitor.get_all_status()
                    alerts = self.monitor.get_alerts(limit=100)
                    
                    health_info["detailed"] = {
                        "expert_statuses": {
                            name: {
                                "is_healthy": status.is_healthy,
                                "health_score": status.health_score,
                                "last_activity": status.last_activity.isoformat(),
                                "response_time_avg": status.response_time_avg,
                                "success_rate": status.success_rate,
                                "error_count": status.error_count,
                                "throughput": status.throughput
                            }
                            for name, status in statuses.items()
                        },
                        "active_alerts": alerts,
                        "system_info": {
                            "monitor_uptime": health_info.get("uptime", 0)
                        }
                    }
                
                health_info["success"] = True
                health_info["trace_id"] = trace.request_id
                
                self.logger.debug(f"API健康检查 - 详细模式: {detailed}")
                
                return health_info
                
            except Exception as e:
                self.logger.error(f"API健康检查异常 - 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "status": "unhealthy",
                    "trace_id": trace.request_id
                }


# 全局监控实例
global_monitor = ExpertMonitor()
monitoring_api = MonitoringAPI(global_monitor)


def get_global_monitor() -> ExpertMonitor:
    """获取全局监控实例"""
    return global_monitor


def get_monitoring_api() -> MonitoringAPI:
    """获取监控API实例"""
    return monitoring_api


# 装饰器：用于自动监控专家方法调用
def monitor_expert(expert_name: str):
    """专家监控装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                response_time = time.time() - start_time
                global_monitor.record_request(expert_name, response_time, success, error_type)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # 测试代码 - 生产级演示
    import asyncio
    import time
    
    async def test_production_monitoring():
        """生产级监控系统测试"""
        print("=== 生产级监控系统测试 ===")
        
        # 创建监控器
        monitor = ExpertMonitor()
        
        # 模拟生产环境数据
        print("\n1. 模拟生产环境数据...")
        start_time = time.time()
        
        for i in range(200):  # 更多数据点
            # 模拟专家1（高性能）
            monitor.record_metric("expert1", MetricType.RESPONSE_TIME.value, 0.05 + i * 0.001)
            monitor.record_metric("expert1", MetricType.THROUGHPUT.value, 100 + i)
            
            # 模拟专家2（中等性能）
            monitor.record_metric("expert2", MetricType.RESPONSE_TIME.value, 0.15 + i * 0.002)
            monitor.record_metric("expert2", MetricType.THROUGHPUT.value, 80 + i * 0.8)
            
            # 模拟专家3（低性能）
            monitor.record_metric("expert3", MetricType.RESPONSE_TIME.value, 0.3 + i * 0.005)
            monitor.record_metric("expert3", MetricType.THROUGHPUT.value, 50 + i * 0.5)
            
            # 记录请求
            if i % 5 == 0:  # 每5次请求有1次错误
                monitor.record_request("expert1", 0.08, True)
                monitor.record_request("expert2", 0.25, False)
                monitor.record_request("expert3", 0.5, False)
            else:
                monitor.record_request("expert1", 0.06, True)
                monitor.record_request("expert2", 0.18, True)
                monitor.record_request("expert3", 0.35, True)
            
            # 添加延迟以模拟真实环境
            await asyncio.sleep(0.01)
        
        print(f"数据模拟完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 测试增强功能
        print("\n2. 测试增强功能...")
        
        # 获取专家状态（带缓存）
        status1 = monitor.calculate_status("expert1")
        status2 = monitor.calculate_status("expert2")
        status3 = monitor.calculate_status("expert3")
        
        print(f"专家1状态: 健康={status1.is_healthy}, 评分={status1.health_score}, 性能={status1.performance_score}")
        print(f"专家2状态: 健康={status2.is_healthy}, 评分={status2.health_score}, 性能={status2.performance_score}")
        print(f"专家3状态: 健康={status3.is_healthy}, 评分={status3.health_score}, 性能={status3.performance_score}")
        
        # 获取所有状态
        all_statuses = monitor.get_all_status()
        print(f"总专家数: {len(all_statuses)}")
        
        # 检查告警
        alerts = monitor.get_alerts()
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        print(f"总告警数: {len(alerts)}, 严重告警: {len(critical_alerts)}")
        
        # 健康检查
        health = monitor.health_check()
        print(f"系统健康评分: {health['system_health_score']}")
        print(f"缓存命中率: {health['cache_hit_rate']}")
        
        # 测试API
        print("\n3. 测试监控API...")
        api = MonitoringAPI(monitor)
        
        # 获取专家详细状态
        expert_status = api.get_expert_status("expert1", include_metrics=True, include_alerts=True)
        print(f"专家1API状态: 包含{len(expert_status.get('metrics', []))}个指标")
        
        # 获取所有状态摘要
        all_status = api.get_expert_status()
        print(f"所有专家摘要: {all_status['summary']}")
        
        # 获取告警信息
        alerts_info = api.get_alerts(severity=AlertSeverity.CRITICAL)
        print(f"严重告警信息: 总数{alerts_info['total']}, 严重{alerts_info['critical']}")
        
        # 详细健康检查
        detailed_health = api.health_check(detailed=True)
        print(f"详细健康检查: 状态{detailed_health['status']}")
        
        # 测试监控任务
        print("\n4. 测试监控任务...")
        await monitor.start_monitoring()
        await asyncio.sleep(10)  # 运行10秒
        await monitor.stop_monitoring()
        
        print("\n=== 生产级监控系统测试完成 ===")
        
        # 性能统计
        print(f"\n性能统计:")
        print(f"- 总请求数: {monitor.total_requests}")
        print(f"- 总错误数: {monitor.total_errors}")
        print(f"- 错误率: {monitor.total_errors / max(monitor.total_requests, 1):.4f}")
        print(f"- 缓存命中: {getattr(monitor, 'status_cache_hits', 0)}")
        print(f"- 缓存未命中: {getattr(monitor, 'status_cache_misses', 0)}")
        
        # 性能监控器统计
        perf_monitor = get_performance_monitor()
        perf_summary = perf_monitor.get_performance_summary()
        print(f"\n性能监控器统计:")
        for metric, stats in perf_summary.items():
            print(f"- {metric}: 调用{stats['count']}次, 平均{stats['avg']:.4f}秒")
    
    # 运行测试
    asyncio.run(test_production_monitoring())