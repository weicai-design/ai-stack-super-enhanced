# ai-stack-super-enhanced/🛠️ Intelligent System Resource Management/scheduler/453. health-intelligence.py

"""
健康智能监控模块
负责系统健康状态的智能分析、预测和预警
"""

import asyncio
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """健康指标数据类"""

    name: str
    value: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime


class HealthIntelligence:
    """
    健康智能监控器
    实现智能健康分析、趋势预测和异常检测
    """

    def __init__(self, system_manager=None):
        self.system_manager = system_manager
        self.health_history: Dict[str, List[HealthMetric]] = {}
        self.anomaly_detection_enabled = True
        self.trend_analysis_window = 300  # 5分钟窗口
        self.health_scores: Dict[str, float] = {}

        # 健康阈值配置
        self.thresholds = {
            "cpu_usage": {"warning": 80.0, "critical": 95.0},
            "memory_usage": {"warning": 85.0, "critical": 95.0},
            "disk_usage": {"warning": 90.0, "critical": 98.0},
            "response_time": {"warning": 2.0, "critical": 5.0},  # 秒
            "error_rate": {"warning": 5.0, "critical": 10.0},  # 百分比
        }

        logger.info("健康智能监控器初始化完成")

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化健康监控器"""
        if config:
            self._update_config(config)

        if core_services:
            self.system_manager = core_services.get("system_manager")

        logger.info("健康智能监控器启动完成")

    async def analyze_system_health(self) -> Dict[str, Any]:
        """
        综合分析系统健康状态
        返回详细的健康报告
        """
        try:
            # 收集各项健康指标
            metrics = await self._collect_health_metrics()

            # 分析健康状态
            health_analysis = await self._analyze_health_metrics(metrics)

            # 检测异常模式
            anomalies = await self._detect_anomalies(metrics)

            # 生成健康评分
            health_score = await self._calculate_health_score(metrics, anomalies)

            # 预测健康趋势
            trend_prediction = await self._predict_health_trend(metrics)

            report = {
                "overall_status": health_analysis["overall_status"],
                "health_score": health_score,
                "metrics": metrics,
                "anomalies": anomalies,
                "trend_prediction": trend_prediction,
                "recommendations": health_analysis["recommendations"],
                "timestamp": datetime.utcnow().isoformat(),
                "components_health": await self._get_components_health(),
            }

            # 记录健康历史
            await self._record_health_history(report)

            return report

        except Exception as e:
            logger.error(f"健康分析失败: {str(e)}", exc_info=True)
            return {
                "overall_status": HealthStatus.UNHEALTHY.value,
                "health_score": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _collect_health_metrics(self) -> Dict[str, HealthMetric]:
        """收集系统健康指标"""
        metrics = {}

        try:
            # CPU 使用率
            cpu_percent = await self._get_cpu_usage_intelligent()
            metrics["cpu_usage"] = HealthMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                threshold_warning=self.thresholds["cpu_usage"]["warning"],
                threshold_critical=self.thresholds["cpu_usage"]["critical"],
                timestamp=datetime.utcnow(),
            )

            # 内存使用率
            memory = psutil.virtual_memory()
            metrics["memory_usage"] = HealthMetric(
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                threshold_warning=self.thresholds["memory_usage"]["warning"],
                threshold_critical=self.thresholds["memory_usage"]["critical"],
                timestamp=datetime.utcnow(),
            )

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            metrics["disk_usage"] = HealthMetric(
                name="disk_usage",
                value=disk_percent,
                unit="percent",
                threshold_warning=self.thresholds["disk_usage"]["warning"],
                threshold_critical=self.thresholds["disk_usage"]["critical"],
                timestamp=datetime.utcnow(),
            )

            # 系统负载（仅Linux/Mac）
            if hasattr(psutil, "getloadavg"):
                load_avg = psutil.getloadavg()
                metrics["system_load"] = HealthMetric(
                    name="system_load",
                    value=load_avg[0],  # 1分钟平均负载
                    unit="load",
                    threshold_warning=psutil.cpu_count() * 0.7,
                    threshold_critical=psutil.cpu_count() * 1.5,
                    timestamp=datetime.utcnow(),
                )

            # 网络连接数
            connections = len(psutil.net_connections())
            metrics["network_connections"] = HealthMetric(
                name="network_connections",
                value=connections,
                unit="count",
                threshold_warning=1000,
                threshold_critical=5000,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"收集健康指标失败: {str(e)}")

        return metrics

    async def _get_cpu_usage_intelligent(self) -> float:
        """智能获取CPU使用率"""
        try:
            # 使用非阻塞方式获取CPU使用率
            loop = asyncio.get_event_loop()
            cpu_percent = await loop.run_in_executor(
                None, lambda: psutil.cpu_percent(interval=0.5)
            )
            return cpu_percent
        except Exception as e:
            logger.error(f"获取CPU使用率失败: {str(e)}")
            return 0.0

    async def _analyze_health_metrics(
        self, metrics: Dict[str, HealthMetric]
    ) -> Dict[str, Any]:
        """分析健康指标状态"""
        analysis = {
            "overall_status": HealthStatus.HEALTHY.value,
            "component_status": {},
            "recommendations": [],
        }

        critical_count = 0
        warning_count = 0

        for metric_name, metric in metrics.items():
            status = self._evaluate_metric_status(metric)
            analysis["component_status"][metric_name] = status

            if status == HealthStatus.CRITICAL.value:
                critical_count += 1
                analysis["recommendations"].append(
                    f"紧急: {metric_name} 达到临界值 {metric.value:.1f}{metric.unit}"
                )
            elif status == HealthStatus.UNHEALTHY.value:
                critical_count += 1
            elif status == HealthStatus.DEGRADED.value:
                warning_count += 1
                analysis["recommendations"].append(
                    f"警告: {metric_name} 达到警告值 {metric.value:.1f}{metric.unit}"
                )

        # 确定整体状态
        if critical_count > 0:
            analysis["overall_status"] = HealthStatus.CRITICAL.value
        elif critical_count > 0:
            analysis["overall_status"] = HealthStatus.UNHEALTHY.value
        elif warning_count > 0:
            analysis["overall_status"] = HealthStatus.DEGRADED.value
        else:
            analysis["overall_status"] = HealthStatus.HEALTHY.value

        return analysis

    def _evaluate_metric_status(self, metric: HealthMetric) -> str:
        """评估单个指标状态"""
        if metric.value >= metric.threshold_critical:
            return HealthStatus.CRITICAL.value
        elif metric.value >= metric.threshold_warning:
            return HealthStatus.UNHEALTHY.value
        elif metric.value >= metric.threshold_warning * 0.8:
            return HealthStatus.DEGRADED.value
        else:
            return HealthStatus.HEALTHY.value

    async def _detect_anomalies(
        self, metrics: Dict[str, HealthMetric]
    ) -> List[Dict[str, Any]]:
        """检测健康指标异常"""
        if not self.anomaly_detection_enabled:
            return []

        anomalies = []
        current_time = datetime.utcnow()

        for metric_name, metric in metrics.items():
            # 检查是否超过阈值
            if metric.value >= metric.threshold_warning:
                anomalies.append(
                    {
                        "metric": metric_name,
                        "value": metric.value,
                        "threshold": metric.threshold_warning,
                        "severity": (
                            "warning"
                            if metric.value < metric.threshold_critical
                            else "critical"
                        ),
                        "timestamp": current_time.isoformat(),
                        "description": f"{metric_name} 超过{'警告' if metric.value < metric.threshold_critical else '临界'}阈值",
                    }
                )

            # 检查历史趋势异常（如果有历史数据）
            if metric_name in self.health_history:
                historical_data = self.health_history[metric_name]
                if len(historical_data) >= 10:  # 有足够的历史数据
                    recent_values = [m.value for m in historical_data[-10:]]
                    avg_value = statistics.mean(recent_values[:-1])

                    # 检测突然变化
                    if abs(metric.value - avg_value) > avg_value * 0.5:  # 变化超过50%
                        anomalies.append(
                            {
                                "metric": metric_name,
                                "value": metric.value,
                                "historical_avg": avg_value,
                                "change_percent": (
                                    (metric.value - avg_value) / avg_value
                                )
                                * 100,
                                "severity": "warning",
                                "timestamp": current_time.isoformat(),
                                "description": f"{metric_name} 出现异常变化",
                            }
                        )

        return anomalies

    async def _calculate_health_score(
        self, metrics: Dict[str, HealthMetric], anomalies: List[Dict]
    ) -> float:
        """计算系统健康评分 (0-100)"""
        if not metrics:
            return 0.0

        total_score = 0.0
        metric_count = len(metrics)

        for metric_name, metric in metrics.items():
            # 基于阈值计算分数
            if metric.value <= metric.threshold_warning * 0.5:
                score = 100.0
            elif metric.value <= metric.threshold_warning:
                score = 80.0
            elif metric.value <= metric.threshold_critical:
                score = 50.0
            else:
                score = 20.0

            total_score += score

        base_score = total_score / metric_count

        # 根据异常调整分数
        anomaly_penalty = 0
        for anomaly in anomalies:
            if anomaly["severity"] == "critical":
                anomaly_penalty += 20
            elif anomaly["severity"] == "warning":
                anomaly_penalty += 10

        final_score = max(0.0, base_score - anomaly_penalty)

        # 记录健康评分
        self.health_scores[datetime.utcnow().isoformat()] = final_score

        return final_score

    async def _predict_health_trend(
        self, metrics: Dict[str, HealthMetric]
    ) -> Dict[str, Any]:
        """预测健康趋势"""
        trend_prediction = {
            "direction": "stable",  # improving, stable, deteriorating
            "confidence": 0.0,
            "predicted_issues": [],
            "time_horizon": "1h",  # 1小时预测
        }

        try:
            # 简单的趋势预测逻辑
            deteriorating_metrics = 0
            improving_metrics = 0

            for metric_name, metric in metrics.items():
                if metric_name in self.health_history:
                    historical = self.health_history[metric_name]
                    if len(historical) >= 5:
                        recent_trend = await self._calculate_trend(historical[-5:])
                        if recent_trend > 0.1:  # 上升趋势
                            deteriorating_metrics += 1
                            if metric.value > metric.threshold_warning * 0.8:
                                trend_prediction["predicted_issues"].append(
                                    f"{metric_name} 可能很快达到警告阈值"
                                )
                        elif recent_trend < -0.1:  # 下降趋势
                            improving_metrics += 1

            # 确定整体趋势方向
            if deteriorating_metrics > improving_metrics + 2:
                trend_prediction["direction"] = "deteriorating"
                trend_prediction["confidence"] = min(0.9, deteriorating_metrics * 0.2)
            elif improving_metrics > deteriorating_metrics + 2:
                trend_prediction["direction"] = "improving"
                trend_prediction["confidence"] = min(0.9, improving_metrics * 0.2)
            else:
                trend_prediction["direction"] = "stable"
                trend_prediction["confidence"] = 0.5

        except Exception as e:
            logger.error(f"健康趋势预测失败: {str(e)}")

        return trend_prediction

    async def _calculate_trend(self, metrics: List[HealthMetric]) -> float:
        """计算指标趋势"""
        if len(metrics) < 2:
            return 0.0

        values = [m.value for m in metrics]
        times = [i for i in range(len(values))]  # 简化时间序列

        try:
            # 简单线性趋势计算
            slope = statistics.covariance(times, values) / statistics.variance(times)
            return slope
        except:
            return 0.0

    async def _get_components_health(self) -> Dict[str, Any]:
        """获取各组件健康状态"""
        components_health = {}

        if self.system_manager:
            try:
                modules_health = await self.system_manager.get_modules_health()
                for module_name, health_info in modules_health.items():
                    components_health[module_name] = {
                        "status": health_info.get("status", "unknown"),
                        "response_time": health_info.get("response_time", 0),
                        "last_check": health_info.get("timestamp", ""),
                    }
            except Exception as e:
                logger.error(f"获取组件健康状态失败: {str(e)}")

        return components_health

    async def _record_health_history(self, health_report: Dict[str, Any]):
        """记录健康历史数据"""
        try:
            timestamp = datetime.utcnow()

            for metric_name, metric_data in health_report.get("metrics", {}).items():
                if isinstance(metric_data, HealthMetric):
                    if metric_name not in self.health_history:
                        self.health_history[metric_name] = []

                    self.health_history[metric_name].append(metric_data)

                    # 保持历史数据大小
                    if (
                        len(self.health_history[metric_name]) > 1000
                    ):  # 最多保存1000个数据点
                        self.health_history[metric_name] = self.health_history[
                            metric_name
                        ][-1000:]

        except Exception as e:
            logger.error(f"记录健康历史失败: {str(e)}")

    async def get_health_intelligence_report(self) -> Dict[str, Any]:
        """获取健康智能报告"""
        current_health = await self.analyze_system_health()

        report = {
            "current_health": current_health,
            "health_trends": await self._get_health_trends(),
            "anomaly_summary": await self._get_anomaly_summary(),
            "recommendations": current_health.get("recommendations", []),
            "predicted_risks": await self._predict_future_risks(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return report

    async def _get_health_trends(self) -> Dict[str, Any]:
        """获取健康趋势分析"""
        trends = {"health_score_trend": [], "metric_trends": {}, "stability_index": 0.0}

        try:
            # 健康评分趋势
            score_timestamps = list(self.health_scores.keys())[-24:]  # 最近24个点
            score_values = [self.health_scores[ts] for ts in score_timestamps]

            if len(score_values) >= 2:
                trends["health_score_trend"] = score_values
                trends["stability_index"] = 100 - (statistics.stdev(score_values) * 10)

            # 各指标趋势
            for metric_name, history in self.health_history.items():
                if len(history) >= 10:
                    recent_values = [m.value for m in history[-10:]]
                    trends["metric_trends"][metric_name] = {
                        "current": recent_values[-1],
                        "average": statistics.mean(recent_values),
                        "trend": await self._calculate_trend(history[-5:]),
                    }

        except Exception as e:
            logger.error(f"获取健康趋势失败: {str(e)}")

        return trends

    async def _get_anomaly_summary(self) -> Dict[str, Any]:
        """获取异常摘要"""
        current_health = await self.analyze_system_health()
        anomalies = current_health.get("anomalies", [])

        critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
        warning_anomalies = [a for a in anomalies if a.get("severity") == "warning"]

        return {
            "total_anomalies": len(anomalies),
            "critical_count": len(critical_anomalies),
            "warning_count": len(warning_anomalies),
            "critical_anomalies": critical_anomalies,
            "warning_anomalies": warning_anomalies,
        }

    async def _predict_future_risks(self) -> List[Dict[str, Any]]:
        """预测未来风险"""
        risks = []
        current_health = await self.analyze_system_health()

        for metric_name, metric in current_health.get("metrics", {}).items():
            if isinstance(metric, HealthMetric):
                # 预测基于当前趋势的风险
                if metric_name in self.health_history:
                    history = self.health_history[metric_name]
                    if len(history) >= 5:
                        trend = await self._calculate_trend(history[-5:])

                        if trend > 0 and metric.value > metric.threshold_warning * 0.7:
                            # 上升趋势且接近警告阈值
                            estimated_time = (
                                metric.threshold_warning - metric.value
                            ) / trend
                            if estimated_time > 0 and estimated_time < 3600:  # 1小时内
                                risks.append(
                                    {
                                        "metric": metric_name,
                                        "risk_level": (
                                            "high"
                                            if metric.value
                                            > metric.threshold_warning * 0.9
                                            else "medium"
                                        ),
                                        "estimated_time": f"{int(estimated_time/60)}分钟",
                                        "description": f"{metric_name} 可能在{int(estimated_time/60)}分钟内达到警告阈值",
                                    }
                                )

        return risks

    async def stop(self):
        """停止健康监控"""
        logger.info("健康智能监控器停止")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态（实现BaseModule接口）"""
        return await self.analyze_system_health()


# 模块导出
__all__ = ["HealthIntelligence", "HealthStatus", "HealthMetric"]
