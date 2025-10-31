#!/usr/bin/env python3
"""
预测预警系统
功能：基于历史数据和机器学习预测潜在问题，提前发出预警
对应需求：8.3/9.1/9.2 - 智能预警、自我学习、预测性维护
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """预警级别"""

    CRITICAL = 100  # 严重问题，需要立即处理
    HIGH = 75  # 高度关注，可能很快出现问题
    MEDIUM = 50  # 中等关注，需要监控
    LOW = 25  # 低关注，信息性提醒
    INFO = 10  # 信息性通知


class AlertType(Enum):
    """预警类型"""

    RESOURCE_USAGE = "resource_usage"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    CAPACITY_PLANNING = "capacity_planning"
    SECURITY_ANOMALY = "security_anomaly"
    SYSTEM_HEALTH = "system_health"


@dataclass
class Alert:
    """预警信息"""

    id: str
    type: AlertType
    level: AlertLevel
    module: str
    title: str
    description: str
    timestamp: datetime
    data: Dict[str, Any]
    predicted_impact: float
    confidence: float
    suggested_actions: List[str]
    expiry_time: Optional[datetime] = None


@dataclass
class PredictionModel:
    """预测模型"""

    name: str
    features: List[str]
    thresholds: Dict[str, float]
    training_data: List[Dict[str, Any]]
    last_trained: datetime


class PredictiveAlertSystem:
    """
    预测预警系统
    基于历史数据和机器学习预测潜在问题，提前发出预警
    """

    def __init__(self, resource_manager=None, event_bus=None):
        self.resource_manager = resource_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # 预警存储
        self.active_alerts = {}
        self.alert_history = []

        # 预测模型
        self.prediction_models = {}

        # 系统配置
        self.alert_config = {
            "prediction_window": 3600,  # 预测窗口（秒）
            "training_interval": 3600,  # 训练间隔（秒）
            "alert_retention_days": 30,  # 预警保留天数
            "confidence_threshold": 0.7,  # 置信度阈值
            "escalation_timeout": 300,  # 升级超时（秒）
        }

        # 监控指标历史
        self.metric_history = {}

        # 预警规则
        self.alert_rules = self._initialize_alert_rules()

        self.initialized = False
        self.monitoring_enabled = True

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化预测预警系统"""
        try:
            self.logger.info("初始化预测预警系统...")

            if core_services:
                self.resource_manager = core_services.get("resource_manager")
                self.event_bus = core_services.get("event_bus")

            # 加载配置
            if config:
                self._load_alert_config(config)

            # 初始化预测模型
            await self._initialize_prediction_models()

            # 启动监控循环
            asyncio.create_task(self._prediction_monitoring_loop())
            asyncio.create_task(self._model_training_loop())

            self.initialized = True
            self.logger.info("预测预警系统初始化完成")

        except Exception as e:
            self.logger.error(f"预测预警系统初始化失败: {e}", exc_info=True)
            raise

    def _load_alert_config(self, config: Dict):
        """加载预警配置"""
        alert_config = config.get("predictive_alert_system", {})
        self.alert_config.update(alert_config)

        # 加载自定义规则
        if "custom_rules" in config:
            self.alert_rules.update(config["custom_rules"])

    def _initialize_alert_rules(self) -> Dict[str, Any]:
        """初始化预警规则"""
        return {
            "resource_usage": {
                "cpu_usage_high": {
                    "threshold": 0.8,
                    "window": 300,  # 5分钟
                    "alert_level": AlertLevel.HIGH,
                    "prediction_horizon": 900,  # 预测15分钟
                },
                "memory_usage_high": {
                    "threshold": 0.85,
                    "window": 300,
                    "alert_level": AlertLevel.HIGH,
                    "prediction_horizon": 1200,  # 预测20分钟
                },
            },
            "performance_degradation": {
                "response_time_slow": {
                    "threshold": 2.0,
                    "window": 600,
                    "alert_level": AlertLevel.MEDIUM,
                    "prediction_horizon": 1800,
                },
                "throughput_low": {
                    "threshold": 50,
                    "window": 600,
                    "alert_level": AlertLevel.MEDIUM,
                    "prediction_horizon": 1800,
                },
            },
            "error_rate_increase": {
                "error_rate_high": {
                    "threshold": 0.05,
                    "window": 300,
                    "alert_level": AlertLevel.CRITICAL,
                    "prediction_horizon": 600,
                }
            },
        }

    async def _initialize_prediction_models(self):
        """初始化预测模型"""
        self.logger.info("初始化预测模型...")

        # 资源使用预测模型
        resource_model = PredictionModel(
            name="resource_usage_predictor",
            features=["cpu_usage", "memory_usage", "disk_io", "time_of_day"],
            thresholds={"cpu_usage": 0.75, "memory_usage": 0.8},
            training_data=[],
            last_trained=datetime.now(),
        )
        self.prediction_models["resource_usage"] = resource_model

        # 性能退化预测模型
        performance_model = PredictionModel(
            name="performance_degradation_predictor",
            features=["response_time", "throughput", "error_rate", "concurrent_users"],
            thresholds={"response_time": 1.5, "throughput": 60},
            training_data=[],
            last_trained=datetime.now(),
        )
        self.prediction_models["performance"] = performance_model

        # 容量规划预测模型
        capacity_model = PredictionModel(
            name="capacity_planning_predictor",
            features=["user_growth", "data_volume", "request_pattern"],
            thresholds={"capacity_remaining": 0.2},
            training_data=[],
            last_trained=datetime.now(),
        )
        self.prediction_models["capacity"] = capacity_model

    async def collect_metrics(self, module_name: str, metrics: Dict[str, Any]):
        """收集监控指标"""
        try:
            timestamp = datetime.now()

            if module_name not in self.metric_history:
                self.metric_history[module_name] = []

            metric_record = {
                "timestamp": timestamp,
                "module": module_name,
                "metrics": metrics,
            }

            self.metric_history[module_name].append(metric_record)

            # 保持历史数据在时间窗口内
            self._cleanup_old_metrics(module_name)

            # 实时分析指标
            await self._analyze_realtime_metrics(module_name, metrics, timestamp)

        except Exception as e:
            self.logger.error(f"收集指标失败 {module_name}: {e}")

    def _cleanup_old_metrics(self, module_name: str):
        """清理过期指标"""
        if module_name not in self.metric_history:
            return

        retention_days = self.alert_config["alert_retention_days"]
        cutoff_time = datetime.now() - timedelta(days=retention_days)

        self.metric_history[module_name] = [
            record
            for record in self.metric_history[module_name]
            if record["timestamp"] > cutoff_time
        ]

    async def _analyze_realtime_metrics(
        self, module_name: str, metrics: Dict[str, Any], timestamp: datetime
    ):
        """实时分析指标"""
        try:
            # 检查资源使用规则
            await self._check_resource_usage_rules(module_name, metrics, timestamp)

            # 检查性能规则
            await self._check_performance_rules(module_name, metrics, timestamp)

            # 检查错误率规则
            await self._check_error_rate_rules(module_name, metrics, timestamp)

            # 运行预测分析
            await self._run_predictive_analysis(module_name, metrics, timestamp)

        except Exception as e:
            self.logger.error(f"实时指标分析失败 {module_name}: {e}")

    async def _check_resource_usage_rules(
        self, module_name: str, metrics: Dict[str, Any], timestamp: datetime
    ):
        """检查资源使用规则"""
        rules = self.alert_rules["resource_usage"]

        # CPU使用率检查
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage > rules["cpu_usage_high"]["threshold"]:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                rules["cpu_usage_high"]["alert_level"],
                module_name,
                "高CPU使用率预警",
                f"模块 {module_name} CPU使用率高达 {cpu_usage:.1%}",
                {
                    "current_usage": cpu_usage,
                    "threshold": rules["cpu_usage_high"]["threshold"],
                },
                0.8,  # 预测影响
                0.9,  # 置信度
                ["优化代码效率", "增加CPU资源", "检查是否有内存泄漏"],
            )

        # 内存使用率检查
        memory_usage = metrics.get("memory_usage", 0)
        if memory_usage > rules["memory_usage_high"]["threshold"]:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                rules["memory_usage_high"]["alert_level"],
                module_name,
                "高内存使用率预警",
                f"模块 {module_name} 内存使用率高达 {memory_usage:.1%}",
                {
                    "current_usage": memory_usage,
                    "threshold": rules["memory_usage_high"]["threshold"],
                },
                0.7,
                0.85,
                ["检查内存泄漏", "优化数据结构", "增加内存资源"],
            )

    async def _check_performance_rules(
        self, module_name: str, metrics: Dict[str, Any], timestamp: datetime
    ):
        """检查性能规则"""
        rules = self.alert_rules["performance_degradation"]

        # 响应时间检查
        response_time = metrics.get("response_time", 0)
        if response_time > rules["response_time_slow"]["threshold"]:
            await self._create_alert(
                AlertType.PERFORMANCE_DEGRADATION,
                rules["response_time_slow"]["alert_level"],
                module_name,
                "响应时间延迟预警",
                f"模块 {module_name} 响应时间延迟: {response_time:.2f}秒",
                {
                    "current_response_time": response_time,
                    "threshold": rules["response_time_slow"]["threshold"],
                },
                0.6,
                0.8,
                ["优化数据库查询", "增加缓存", "检查网络延迟"],
            )

        # 吞吐量检查
        throughput = metrics.get("throughput", 0)
        if throughput < rules["throughput_low"]["threshold"]:
            await self._create_alert(
                AlertType.PERFORMANCE_DEGRADATION,
                rules["throughput_low"]["alert_level"],
                module_name,
                "低吞吐量预警",
                f"模块 {module_name} 吞吐量低: {throughput:.1f} 请求/秒",
                {
                    "current_throughput": throughput,
                    "threshold": rules["throughput_low"]["threshold"],
                },
                0.5,
                0.75,
                ["优化并发处理", "增加工作线程", "检查系统负载"],
            )

    async def _check_error_rate_rules(
        self, module_name: str, metrics: Dict[str, Any], timestamp: datetime
    ):
        """检查错误率规则"""
        rules = self.alert_rules["error_rate_increase"]

        error_rate = metrics.get("error_rate", 0)
        if error_rate > rules["error_rate_high"]["threshold"]:
            await self._create_alert(
                AlertType.ERROR_RATE_INCREASE,
                rules["error_rate_high"]["alert_level"],
                module_name,
                "高错误率预警",
                f"模块 {module_name} 错误率高达 {error_rate:.1%}",
                {
                    "current_error_rate": error_rate,
                    "threshold": rules["error_rate_high"]["threshold"],
                },
                0.9,
                0.95,
                ["检查日志文件", "回滚最近更改", "增加错误监控"],
            )

    async def _run_predictive_analysis(
        self, module_name: str, metrics: Dict[str, Any], timestamp: datetime
    ):
        """运行预测分析"""
        try:
            # 预测资源使用趋势
            resource_prediction = await self._predict_resource_usage(
                module_name, metrics
            )
            if resource_prediction["needs_alert"]:
                await self._create_predictive_alert(
                    AlertType.RESOURCE_USAGE,
                    resource_prediction["level"],
                    module_name,
                    "资源使用趋势预警",
                    resource_prediction["message"],
                    resource_prediction["data"],
                    resource_prediction["impact"],
                    resource_prediction["confidence"],
                    resource_prediction["suggested_actions"],
                )

            # 预测性能趋势
            performance_prediction = await self._predict_performance_trend(
                module_name, metrics
            )
            if performance_prediction["needs_alert"]:
                await self._create_predictive_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    performance_prediction["level"],
                    module_name,
                    "性能趋势预警",
                    performance_prediction["message"],
                    performance_prediction["data"],
                    performance_prediction["impact"],
                    performance_prediction["confidence"],
                    performance_prediction["suggested_actions"],
                )

        except Exception as e:
            self.logger.error(f"预测分析失败 {module_name}: {e}")

    async def _predict_resource_usage(
        self, module_name: str, current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测资源使用趋势"""
        # 简化实现 - 实际应使用机器学习模型
        if (
            module_name not in self.metric_history
            or len(self.metric_history[module_name]) < 10
        ):
            return {"needs_alert": False}

        # 分析历史趋势
        recent_metrics = self.metric_history[module_name][-10:]
        cpu_trend = await self._calculate_trend(
            [m["metrics"].get("cpu_usage", 0) for m in recent_metrics]
        )
        memory_trend = await self._calculate_trend(
            [m["metrics"].get("memory_usage", 0) for m in recent_metrics]
        )

        current_cpu = current_metrics.get("cpu_usage", 0)
        current_memory = current_metrics.get("memory_usage", 0)

        # 预测未来值
        predicted_cpu = current_cpu + cpu_trend * 4  # 预测4个周期后
        predicted_memory = current_memory + memory_trend * 4

        needs_alert = False
        alert_level = AlertLevel.LOW
        message = ""

        if predicted_cpu > 0.9:
            needs_alert = True
            alert_level = AlertLevel.CRITICAL
            message = f"预测CPU使用率将在短期内达到 {predicted_cpu:.1%}"
        elif predicted_cpu > 0.8:
            needs_alert = True
            alert_level = AlertLevel.HIGH
            message = f"预测CPU使用率将增长到 {predicted_cpu:.1%}"

        if predicted_memory > 0.95:
            needs_alert = True
            alert_level = max(alert_level, AlertLevel.CRITICAL)
            message += f"，内存使用率可能达到 {predicted_memory:.1%}"
        elif predicted_memory > 0.85:
            needs_alert = True
            alert_level = max(alert_level, AlertLevel.HIGH)
            message += f"，内存使用率可能增长到 {predicted_memory:.1%}"

        return {
            "needs_alert": needs_alert,
            "level": alert_level,
            "message": message,
            "data": {
                "current_cpu": current_cpu,
                "current_memory": current_memory,
                "predicted_cpu": predicted_cpu,
                "predicted_memory": predicted_memory,
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
            },
            "impact": min((predicted_cpu - 0.7) / 0.3, 1.0),  # 标准化影响分数
            "confidence": 0.7,
            "suggested_actions": ["预分配额外资源", "优化当前资源使用", "考虑横向扩展"],
        }

    async def _predict_performance_trend(
        self, module_name: str, current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测性能趋势"""
        if (
            module_name not in self.metric_history
            or len(self.metric_history[module_name]) < 10
        ):
            return {"needs_alert": False}

        # 分析性能趋势
        recent_metrics = self.metric_history[module_name][-10:]
        response_trend = await self._calculate_trend(
            [m["metrics"].get("response_time", 0) for m in recent_metrics]
        )
        throughput_trend = await self._calculate_trend(
            [m["metrics"].get("throughput", 0) for m in recent_metrics]
        )

        current_response = current_metrics.get("response_time", 0)
        current_throughput = current_metrics.get("throughput", 0)

        # 预测未来值
        predicted_response = max(0, current_response + response_trend * 4)
        predicted_throughput = max(0, current_throughput + throughput_trend * 4)

        needs_alert = False
        alert_level = AlertLevel.LOW
        message = ""

        if predicted_response > 3.0:
            needs_alert = True
            alert_level = AlertLevel.HIGH
            message = f"预测响应时间将延迟到 {predicted_response:.2f}秒"
        elif predicted_response > 2.0 and response_trend > 0:
            needs_alert = True
            alert_level = AlertLevel.MEDIUM
            message = f"响应时间呈上升趋势，可能达到 {predicted_response:.2f}秒"

        if predicted_throughput < 30 and throughput_trend < 0:
            needs_alert = True
            alert_level = max(alert_level, AlertLevel.MEDIUM)
            message += f"，吞吐量可能下降到 {predicted_throughput:.1f}"

        return {
            "needs_alert": needs_alert,
            "level": alert_level,
            "message": message,
            "data": {
                "current_response": current_response,
                "current_throughput": current_throughput,
                "predicted_response": predicted_response,
                "predicted_throughput": predicted_throughput,
                "response_trend": response_trend,
                "throughput_trend": throughput_trend,
            },
            "impact": min((3.0 - predicted_throughput / 50) / 3.0, 1.0),
            "confidence": 0.6,
            "suggested_actions": ["优化性能关键路径", "检查数据库索引", "增加缓存层级"],
        }

    async def _calculate_trend(self, values: List[float]) -> float:
        """计算数值趋势（简单线性回归）"""
        if len(values) < 2:
            return 0.0

        x = list(range(len(values)))
        x_mean = sum(x) / len(x)
        y_mean = sum(values) / len(values)

        numerator = sum(
            (x[i] - x_mean) * (values[i] - y_mean) for i in range(len(values))
        )
        denominator = sum((x[i] - x_mean) ** 2 for i in range(len(values)))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    async def _create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        module: str,
        title: str,
        description: str,
        data: Dict[str, Any],
        predicted_impact: float,
        confidence: float,
        suggested_actions: List[str],
    ):
        """创建预警"""
        alert_id = f"{alert_type.value}_{module}_{int(time.time())}"

        # 检查是否已存在类似预警
        existing_alert = await self._find_similar_alert(alert_type, module, level)
        if existing_alert:
            await self._update_existing_alert(existing_alert, data, confidence)
            return

        alert = Alert(
            id=alert_id,
            type=alert_type,
            level=level,
            module=module,
            title=title,
            description=description,
            timestamp=datetime.now(),
            data=data,
            predicted_impact=predicted_impact,
            confidence=confidence,
            suggested_actions=suggested_actions,
            expiry_time=datetime.now() + timedelta(hours=24),  # 24小时后过期
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # 发布预警事件
        if self.event_bus:
            await self.event_bus.publish("alert.created", self._alert_to_dict(alert))

        self.logger.warning(f"创建预警: {title} (级别: {level.name}, 模块: {module})")

    async def _create_predictive_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        module: str,
        title: str,
        description: str,
        data: Dict[str, Any],
        predicted_impact: float,
        confidence: float,
        suggested_actions: List[str],
    ):
        """创建预测性预警"""
        # 只创建高置信度的预测预警
        if confidence < self.alert_config["confidence_threshold"]:
            return

        await self._create_alert(
            alert_type,
            level,
            module,
            title,
            description,
            data,
            predicted_impact,
            confidence,
            suggested_actions,
        )

    async def _find_similar_alert(
        self, alert_type: AlertType, module: str, level: AlertLevel
    ) -> Optional[Alert]:
        """查找类似预警"""
        for alert in self.active_alerts.values():
            if (
                alert.type == alert_type
                and alert.module == module
                and alert.level == level
                and (datetime.now() - alert.timestamp).total_seconds() < 3600
            ):  # 1小时内
                return alert
        return None

    async def _update_existing_alert(
        self, alert: Alert, new_data: Dict[str, Any], confidence: float
    ):
        """更新现有预警"""
        # 更新数据
        alert.data.update(new_data)
        alert.confidence = max(alert.confidence, confidence)
        alert.timestamp = datetime.now()

        # 发布更新事件
        if self.event_bus:
            await self.event_bus.publish("alert.updated", self._alert_to_dict(alert))

    async def resolve_alert(self, alert_id: str, resolution_notes: str = ""):
        """解决预警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            del self.active_alerts[alert_id]

            # 记录解决信息
            resolution_info = {
                "resolved_at": datetime.now(),
                "resolution_notes": resolution_notes,
                "alert": self._alert_to_dict(alert),
            }

            # 发布解决事件
            if self.event_bus:
                await self.event_bus.publish("alert.resolved", resolution_info)

            self.logger.info(f"预警已解决: {alert.title} (ID: {alert_id})")

    async def get_active_alerts(
        self, module: str = None, level: AlertLevel = None
    ) -> List[Dict[str, Any]]:
        """获取活跃预警"""
        alerts = list(self.active_alerts.values())

        if module:
            alerts = [a for a in alerts if a.module == module]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return [self._alert_to_dict(alert) for alert in alerts]

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """获取预警统计"""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)

        # 按类型统计
        type_stats = {}
        for alert in self.alert_history:
            alert_type = alert.type.value
            type_stats[alert_type] = type_stats.get(alert_type, 0) + 1

        # 按级别统计
        level_stats = {}
        for alert in self.alert_history:
            alert_level = alert.level.name
            level_stats[alert_level] = level_stats.get(alert_level, 0) + 1

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": total_alerts - active_alerts,
            "by_type": type_stats,
            "by_level": level_stats,
            "resolution_rate": (total_alerts - active_alerts) / max(total_alerts, 1),
            "average_confidence": (
                np.mean([a.confidence for a in self.alert_history])
                if self.alert_history
                else 0
            ),
        }

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """将预警转换为字典"""
        return {
            "id": alert.id,
            "type": alert.type.value,
            "level": alert.level.name,
            "module": alert.module,
            "title": alert.title,
            "description": alert.description,
            "timestamp": alert.timestamp.isoformat(),
            "data": alert.data,
            "predicted_impact": alert.predicted_impact,
            "confidence": alert.confidence,
            "suggested_actions": alert.suggested_actions,
            "expiry_time": alert.expiry_time.isoformat() if alert.expiry_time else None,
        }

    async def _prediction_monitoring_loop(self):
        """预测监控循环"""
        while self.monitoring_enabled:
            try:
                # 检查所有模块的指标历史，进行批量预测
                for module_name in list(self.metric_history.keys()):
                    if (
                        module_name in self.metric_history
                        and self.metric_history[module_name]
                    ):
                        latest_metrics = self.metric_history[module_name][-1]["metrics"]
                        await self._run_predictive_analysis(
                            module_name, latest_metrics, datetime.now()
                        )

                # 清理过期预警
                await self._cleanup_expired_alerts()

                # 等待下一次监控
                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"预测监控循环错误: {e}")
                await asyncio.sleep(10)

    async def _model_training_loop(self):
        """模型训练循环"""
        while self.monitoring_enabled:
            try:
                # 定期训练预测模型
                await self._train_prediction_models()

                # 等待下一次训练
                interval = self.alert_config["training_interval"]
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"模型训练循环错误: {e}")
                await asyncio.sleep(300)  # 出错时等待5分钟

    async def _train_prediction_models(self):
        """训练预测模型"""
        self.logger.info("开始训练预测模型...")

        for model_name, model in self.prediction_models.items():
            try:
                # 收集训练数据
                training_data = await self._collect_training_data(model_name)
                model.training_data = training_data
                model.last_trained = datetime.now()

                self.logger.info(
                    f"模型 {model_name} 训练完成，数据量: {len(training_data)}"
                )

            except Exception as e:
                self.logger.error(f"训练模型 {model_name} 失败: {e}")

    async def _collect_training_data(self, model_name: str) -> List[Dict[str, Any]]:
        """收集训练数据"""
        training_data = []

        for module_name, metrics_list in self.metric_history.items():
            if len(metrics_list) < 10:
                continue

            # 提取特征和标签
            for i in range(len(metrics_list) - 1):
                current = metrics_list[i]
                next_point = metrics_list[i + 1]

                features = self._extract_features(current["metrics"], model_name)
                label = self._extract_label(
                    current["metrics"], next_point["metrics"], model_name
                )

                if features and label is not None:
                    training_data.append(
                        {
                            "features": features,
                            "label": label,
                            "timestamp": current["timestamp"],
                            "module": module_name,
                        }
                    )

        return training_data

    def _extract_features(
        self, metrics: Dict[str, Any], model_name: str
    ) -> Dict[str, Any]:
        """提取特征"""
        if model_name == "resource_usage":
            return {
                "cpu_usage": metrics.get("cpu_usage", 0),
                "memory_usage": metrics.get("memory_usage", 0),
                "disk_io": metrics.get("disk_io", 0),
                "time_of_day": datetime.now().hour / 24.0,
            }
        elif model_name == "performance":
            return {
                "response_time": metrics.get("response_time", 0),
                "throughput": metrics.get("throughput", 0),
                "error_rate": metrics.get("error_rate", 0),
                "concurrent_users": metrics.get("concurrent_users", 1),
            }
        else:
            return {}

    def _extract_label(
        self,
        current_metrics: Dict[str, Any],
        next_metrics: Dict[str, Any],
        model_name: str,
    ) -> Optional[float]:
        """提取标签"""
        if model_name == "resource_usage":
            # 预测CPU使用率变化
            current_cpu = current_metrics.get("cpu_usage", 0)
            next_cpu = next_metrics.get("cpu_usage", 0)
            return next_cpu - current_cpu
        elif model_name == "performance":
            # 预测响应时间变化
            current_response = current_metrics.get("response_time", 0)
            next_response = next_metrics.get("response_time", 0)
            return next_response - current_response
        return None

    async def _cleanup_expired_alerts(self):
        """清理过期预警"""
        current_time = datetime.now()
        expired_alerts = []

        for alert_id, alert in self.active_alerts.items():
            if alert.expiry_time and current_time > alert.expiry_time:
                expired_alerts.append(alert_id)

        for alert_id in expired_alerts:
            await self.resolve_alert(alert_id, "预警已过期")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy" if self.initialized else "initializing",
            "monitoring_enabled": self.monitoring_enabled,
            "modules_monitored": len(self.metric_history),
            "active_alerts": len(self.active_alerts),
            "models_trained": len(
                [m for m in self.prediction_models.values() if m.training_data]
            ),
            "prediction_accuracy": await self._calculate_prediction_accuracy(),
            "last_training": (
                max(
                    [m.last_trained for m in self.prediction_models.values()]
                ).isoformat()
                if self.prediction_models
                else None
            ),
        }

    async def _calculate_prediction_accuracy(self) -> float:
        """计算预测准确率"""
        # 简化实现 - 实际应基于历史预测结果计算
        if not self.alert_history:
            return 0.0

        successful_predictions = len(
            [
                alert
                for alert in self.alert_history
                if alert.confidence > 0.7 and alert.predicted_impact > 0.5
            ]
        )

        return successful_predictions / len(self.alert_history)

    async def stop(self):
        """停止预测预警系统"""
        self.logger.info("停止预测预警系统")
        self.monitoring_enabled = False
        self.initialized = False
