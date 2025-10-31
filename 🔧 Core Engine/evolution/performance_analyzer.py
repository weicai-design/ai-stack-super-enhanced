# ai-stack-super-enhanced/🔧 Core Engine/evolution/performance_analyzer.py
"""
性能分析器 - 负责系统性能监控、分析和瓶颈识别
对应开发计划：阶段1 - Core Engine 中的进化引擎基础
对应开发规则：9.1/9.2 自我学习和自我进化功能需求
"""

import logging
import statistics
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import psutil

logger = logging.getLogger(__name__)


class PerformanceDimension(Enum):
    """性能维度枚举"""

    EFFICIENCY = "efficiency"
    ACCURACY = "accuracy"
    STABILITY = "stability"
    ADAPTABILITY = "adaptability"
    RESOURCE_USAGE = "resource_usage"
    RESPONSIVENESS = "responsiveness"


class AnalysisLevel(Enum):
    """分析级别枚举"""

    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    DEEP = "deep"


class PerformanceAnalyzer:
    """
    性能分析器 - 系统性能监控和分析核心组件

    核心功能：
    1. 多维度性能指标收集和监控
    2. 性能趋势分析和预测
    3. 系统瓶颈识别和定位
    4. 性能异常检测和告警
    5. 性能数据可视化和报告生成
    """

    def __init__(self):
        # 性能数据存储
        self.performance_history = {}
        self.metric_thresholds = {}
        self.anomaly_detectors = {}

        # 分析配置
        self.analysis_config = {}
        self.monitoring_intervals = {}

        # 状态信息
        self.is_initialized = False
        self.last_analysis_time = None
        self.analysis_count = 0

        # 缓存优化
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5分钟缓存

        logger.info("性能分析器实例创建")

    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化性能分析器

        Args:
            config: 分析配置参数

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始初始化性能分析器")

            # 设置配置
            self.analysis_config = config or {}
            await self._setup_default_config()

            # 初始化性能历史存储
            await self._initialize_performance_storage()

            # 设置指标阈值
            await self._setup_metric_thresholds()

            # 初始化异常检测器
            await self._initialize_anomaly_detectors()

            # 启动后台监控任务
            await self._start_background_monitoring()

            self.is_initialized = True
            self.last_analysis_time = datetime.utcnow()

            logger.info("性能分析器初始化完成")
            return True

        except Exception as e:
            logger.error(f"性能分析器初始化失败: {str(e)}", exc_info=True)
            self.is_initialized = False
            return False

    async def _setup_default_config(self):
        """设置默认配置"""
        default_config = {
            "analysis_level": AnalysisLevel.STANDARD.value,
            "data_retention_days": 30,
            "real_time_monitoring": True,
            "anomaly_detection_enabled": True,
            "trend_analysis_enabled": True,
            "performance_prediction": True,
            "auto_threshold_adjustment": True,
            "report_generation_interval": 3600,  # 1小时
            "cache_enabled": True,
        }

        # 合并配置
        for key, value in default_config.items():
            if key not in self.analysis_config:
                self.analysis_config[key] = value

        # 设置监控间隔
        self.monitoring_intervals = {
            "system_metrics": 10,  # 系统指标每10秒
            "application_metrics": 30,  # 应用指标每30秒
            "business_metrics": 60,  # 业务指标每60秒
            "deep_analysis": 300,  # 深度分析每5分钟
        }

    async def _initialize_performance_storage(self):
        """初始化性能数据存储"""
        # 为每个性能维度初始化历史数据存储
        for dimension in PerformanceDimension:
            self.performance_history[dimension.value] = {
                "timestamps": [],
                "values": [],
                "metadata": [],
            }

        # 初始化系统指标存储
        self.performance_history["system"] = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_io": [],
            "network_io": [],
            "timestamps": [],
        }

        logger.debug("性能数据存储初始化完成")

    async def _setup_metric_thresholds(self):
        """设置指标阈值"""
        # 默认阈值配置
        self.metric_thresholds = {
            "cpu_usage": {"warning": 80, "critical": 95},
            "memory_usage": {"warning": 85, "critical": 95},
            "response_time": {"warning": 2.0, "critical": 5.0},  # 秒
            "error_rate": {"warning": 0.05, "critical": 0.1},  # 5%, 10%
            "throughput": {"warning": 0.7, "critical": 0.5},  # 相对值
            "availability": {"warning": 0.99, "critical": 0.95},  # 99%, 95%
        }

        # 从配置中更新阈值
        if "metric_thresholds" in self.analysis_config:
            self.metric_thresholds.update(self.analysis_config["metric_thresholds"])

    async def _initialize_anomaly_detectors(self):
        """初始化异常检测器"""
        try:
            # 简单的统计异常检测器
            self.anomaly_detectors = {
                "z_score": {"enabled": True, "threshold": 3.0},  # 3个标准差
                "moving_average": {"enabled": True, "window_size": 10},
                "rate_of_change": {"enabled": True, "threshold": 2.0},  # 变化率阈值
            }

            logger.debug("异常检测器初始化完成")

        except Exception as e:
            logger.error(f"异常检测器初始化失败: {str(e)}")

    async def _start_background_monitoring(self):
        """启动后台监控任务"""
        if self.analysis_config.get("real_time_monitoring", True):
            # 在实际实现中，这里会启动真正的监控循环
            # 为简化，这里只记录日志
            logger.info("后台性能监控已启用")

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """
        收集系统级性能指标

        Returns:
            Dict: 系统性能指标
        """
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
                    "load_avg": (
                        psutil.getloadavg()
                        if hasattr(psutil, "getloadavg")
                        else [0, 0, 0]
                    ),
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used,
                },
                "disk": {
                    "usage_percent": psutil.disk_usage("/").percent,
                    "io_counters": (
                        psutil.disk_io_counters()._asdict()
                        if psutil.disk_io_counters()
                        else {}
                    ),
                },
                "network": {
                    "io_counters": (
                        psutil.net_io_counters()._asdict()
                        if psutil.net_io_counters()
                        else {}
                    )
                },
                "process": {
                    "count": len(psutil.pids()),
                    "current_rss": psutil.Process().memory_info().rss,
                },
            }

            # 存储系统指标
            await self._store_system_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"系统指标收集失败: {str(e)}")
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    async def _store_system_metrics(self, metrics: Dict[str, Any]):
        """存储系统指标到历史数据"""
        try:
            history = self.performance_history["system"]
            current_time = datetime.utcnow()

            # 添加时间戳
            history["timestamps"].append(current_time)

            # 添加各项指标
            history["cpu_usage"].append(metrics["cpu"]["percent"])
            history["memory_usage"].append(metrics["memory"]["percent"])

            # 磁盘IO
            disk_io = metrics["disk"]["io_counters"]
            disk_io_total = (
                disk_io.get("read_bytes", 0) + disk_io.get("write_bytes", 0)
                if disk_io
                else 0
            )
            history["disk_io"].append(disk_io_total)

            # 网络IO
            net_io = metrics["network"]["io_counters"]
            net_io_total = (
                net_io.get("bytes_sent", 0) + net_io.get("bytes_recv", 0)
                if net_io
                else 0
            )
            history["network_io"].append(net_io_total)

            # 限制历史数据大小
            max_history = 1000
            for key in history:
                if len(history[key]) > max_history:
                    history[key] = history[key][-max_history:]

        except Exception as e:
            logger.error(f"系统指标存储失败: {str(e)}")

    async def collect_application_metrics(self) -> Dict[str, Any]:
        """
        收集应用级性能指标

        Returns:
            Dict: 应用性能指标
        """
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": {
                    "average": self._simulate_response_time(),
                    "p95": self._simulate_response_time() * 1.5,
                    "p99": self._simulate_response_time() * 2.0,
                },
                "throughput": {
                    "requests_per_second": self._simulate_throughput(),
                    "data_processed": self._simulate_data_processed(),
                },
                "error_rates": {
                    "total": self._simulate_error_rate(),
                    "by_type": {"timeout": 0.01, "validation": 0.02, "system": 0.001},
                },
                "business_metrics": {
                    "user_satisfaction": self._simulate_user_satisfaction(),
                    "completion_rate": self._simulate_completion_rate(),
                },
            }

            # 存储应用指标
            await self._store_application_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"应用指标收集失败: {str(e)}")
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}

    def _simulate_response_time(self) -> float:
        """模拟响应时间数据"""
        # 在实际实现中，这里会从实际监控系统获取数据
        return 0.1 + (0.4 * np.random.random())  # 0.1-0.5秒

    def _simulate_throughput(self) -> float:
        """模拟吞吐量数据"""
        return 100 + (900 * np.random.random())  # 100-1000 请求/秒

    def _simulate_data_processed(self) -> float:
        """模拟数据处理量"""
        return 1024 + (10240 * np.random.random())  # 1KB-10KB

    def _simulate_error_rate(self) -> float:
        """模拟错误率"""
        return 0.01 + (0.04 * np.random.random())  # 1%-5%

    def _simulate_user_satisfaction(self) -> float:
        """模拟用户满意度"""
        return 0.8 + (0.19 * np.random.random())  # 80%-99%

    def _simulate_completion_rate(self) -> float:
        """模拟完成率"""
        return 0.85 + (0.14 * np.random.random())  # 85%-99%

    async def _store_application_metrics(self, metrics: Dict[str, Any]):
        """存储应用指标到历史数据"""
        try:
            current_time = datetime.utcnow()

            # 存储到各个性能维度
            dimensions_mapping = {
                PerformanceDimension.EFFICIENCY: metrics["response_time"]["average"],
                PerformanceDimension.ACCURACY: 1.0 - metrics["error_rates"]["total"],
                PerformanceDimension.STABILITY: metrics["business_metrics"][
                    "completion_rate"
                ],
                PerformanceDimension.ADAPTABILITY: metrics["business_metrics"][
                    "user_satisfaction"
                ],
                PerformanceDimension.RESPONSIVENESS: metrics["response_time"][
                    "average"
                ],
            }

            for dimension, value in dimensions_mapping.items():
                history = self.performance_history[dimension.value]
                history["timestamps"].append(current_time)
                history["values"].append(value)
                history["metadata"].append({"source": "application_metrics"})

                # 限制历史数据大小
                max_history = 1000
                if len(history["values"]) > max_history:
                    history["timestamps"] = history["timestamps"][-max_history:]
                    history["values"] = history["values"][-max_history:]
                    history["metadata"] = history["metadata"][-max_history:]

        except Exception as e:
            logger.error(f"应用指标存储失败: {str(e)}")

    async def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        获取综合分析报告

        Returns:
            Dict: 综合分析结果
        """
        try:
            # 检查缓存
            cache_key = "comprehensive_analysis"
            if self.analysis_config.get("cache_enabled", True):
                cached_result = self._get_cached_analysis(cache_key)
                if cached_result:
                    return cached_result

            logger.info("开始执行综合性能分析")

            # 收集当前指标
            system_metrics = await self.collect_system_metrics()
            application_metrics = await self.collect_application_metrics()

            # 执行多维度分析
            analysis_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_id": f"analysis_{self.analysis_count}",
                "summary": await self._generate_analysis_summary(),
                "dimensions": {},
            }

            # 分析各个性能维度
            for dimension in PerformanceDimension:
                dimension_analysis = await self._analyze_performance_dimension(
                    dimension
                )
                analysis_results["dimensions"][dimension.value] = dimension_analysis

            # 执行趋势分析
            analysis_results["trends"] = await self._analyze_performance_trends()

            # 异常检测
            analysis_results["anomalies"] = await self._detect_anomalies()

            # 瓶颈识别
            analysis_results["bottlenecks"] = await self.identify_bottlenecks()

            # 生成建议
            analysis_results["recommendations"] = await self._generate_recommendations(
                analysis_results
            )

            self.analysis_count += 1
            self.last_analysis_time = datetime.utcnow()

            # 缓存结果
            if self.analysis_config.get("cache_enabled", True):
                self._cache_analysis(cache_key, analysis_results)

            logger.info("综合性能分析完成")
            return analysis_results

        except Exception as e:
            logger.error(f"综合性能分析失败: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "analysis_id": f"analysis_error_{self.analysis_count}",
            }

    async def _generate_analysis_summary(self) -> Dict[str, Any]:
        """生成分析摘要"""
        try:
            # 计算整体性能分数
            dimension_scores = []
            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                if history["values"]:
                    recent_values = history["values"][-10:]  # 最近10个值
                    avg_score = sum(recent_values) / len(recent_values)
                    dimension_scores.append(avg_score)

            overall_score = (
                sum(dimension_scores) / len(dimension_scores)
                if dimension_scores
                else 0.0
            )

            # 评估整体状态
            if overall_score >= 0.9:
                status = "excellent"
            elif overall_score >= 0.7:
                status = "good"
            elif overall_score >= 0.5:
                status = "fair"
            else:
                status = "poor"

            return {
                "overall_score": overall_score,
                "status": status,
                "dimensions_analyzed": len(dimension_scores),
                "data_points_used": sum(
                    len(self.performance_history[dim.value]["values"])
                    for dim in PerformanceDimension
                ),
            }

        except Exception as e:
            logger.error(f"分析摘要生成失败: {str(e)}")
            return {"overall_score": 0.0, "status": "unknown", "error": str(e)}

    async def _analyze_performance_dimension(
        self, dimension: PerformanceDimension
    ) -> Dict[str, Any]:
        """分析单个性能维度"""
        try:
            history = self.performance_history[dimension.value]

            if not history["values"]:
                return {
                    "score": 0.0,
                    "status": "insufficient_data",
                    "trend": "unknown",
                    "data_points": 0,
                }

            values = history["values"]
            timestamps = history["timestamps"]

            # 计算当前得分
            current_score = values[-1] if values else 0.0

            # 计算趋势
            trend = await self._calculate_dimension_trend(values)

            # 计算稳定性
            stability = await self._calculate_dimension_stability(values)

            # 评估状态
            status = self._evaluate_dimension_status(dimension, current_score, trend)

            return {
                "score": current_score,
                "status": status,
                "trend": trend,
                "stability": stability,
                "data_points": len(values),
                "last_updated": timestamps[-1].isoformat() if timestamps else None,
            }

        except Exception as e:
            logger.error(f"性能维度分析失败 {dimension.value}: {str(e)}")
            return {"score": 0.0, "status": "analysis_error", "error": str(e)}

    async def _calculate_dimension_trend(self, values: List[float]) -> str:
        """计算维度趋势"""
        if len(values) < 5:
            return "insufficient_data"

        recent_values = values[-10:]  # 最近10个值

        # 简单线性趋势分析
        x = list(range(len(recent_values)))
        y = recent_values

        # 计算斜率
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x2 - sum_x * sum_x

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"

    async def _calculate_dimension_stability(self, values: List[float]) -> float:
        """计算维度稳定性"""
        if len(values) < 2:
            return 1.0

        # 计算变异系数
        mean = statistics.mean(values)
        if mean == 0:
            return 1.0

        stdev = statistics.stdev(values) if len(values) >= 2 else 0
        coefficient_of_variation = stdev / mean

        # 稳定性 = 1 - 变异系数
        stability = max(0.0, 1.0 - coefficient_of_variation)
        return stability

    def _evaluate_dimension_status(
        self, dimension: PerformanceDimension, score: float, trend: str
    ) -> str:
        """评估维度状态"""
        # 不同维度可能有不同的评估标准
        dimension_thresholds = {
            PerformanceDimension.EFFICIENCY: {"good": 0.8, "fair": 0.6},
            PerformanceDimension.ACCURACY: {"good": 0.95, "fair": 0.8},
            PerformanceDimension.STABILITY: {"good": 0.9, "fair": 0.7},
            PerformanceDimension.ADAPTABILITY: {"good": 0.85, "fair": 0.65},
            PerformanceDimension.RESOURCE_USAGE: {"good": 0.8, "fair": 0.6},
            PerformanceDimension.RESPONSIVENESS: {"good": 0.85, "fair": 0.7},
        }

        thresholds = dimension_thresholds.get(dimension, {"good": 0.8, "fair": 0.6})

        if score >= thresholds["good"]:
            base_status = "good"
        elif score >= thresholds["fair"]:
            base_status = "fair"
        else:
            base_status = "poor"

        # 考虑趋势因素
        if trend == "improving" and base_status == "poor":
            return "improving_poor"
        elif trend == "declining" and base_status == "good":
            return "declining_good"
        else:
            return base_status

    async def _analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        try:
            trends = {}

            # 分析各维度趋势
            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                if len(history["values"]) >= 10:
                    values = history["values"][-20:]  # 最近20个值
                    trend_analysis = await self._perform_trend_analysis(values)
                    trends[dimension.value] = trend_analysis

            # 分析整体趋势
            all_scores = []
            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                if history["values"]:
                    all_scores.append(history["values"][-1])

            if all_scores:
                overall_trend = await self._perform_trend_analysis(all_scores)
                trends["overall"] = overall_trend

            return trends

        except Exception as e:
            logger.error(f"性能趋势分析失败: {str(e)}")
            return {"error": str(e)}

    async def _perform_trend_analysis(self, values: List[float]) -> Dict[str, Any]:
        """执行趋势分析"""
        if len(values) < 5:
            return {"trend": "insufficient_data"}

        # 简单线性回归
        x = list(range(len(values)))
        y = values

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x2 - sum_x * sum_x

        if denominator == 0:
            return {"trend": "stable", "slope": 0}

        slope = numerator / denominator

        # 预测下一个值
        next_x = n
        predicted_next = (slope * next_x) + (sum_y / n - slope * sum_x / n)

        # 计算R²
        y_mean = sum_y / n
        ss_tot = sum((y_i - y_mean) ** 2 for y_i in y)
        ss_res = sum(
            (y[i] - (slope * x[i] + (y_mean - slope * sum_x / n))) ** 2
            for i in range(n)
        )

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # 判断趋势强度
        if abs(slope) < 0.001:
            trend_strength = "stable"
        elif abs(slope) < 0.01:
            trend_strength = "weak"
        elif abs(slope) < 0.05:
            trend_strength = "moderate"
        else:
            trend_strength = "strong"

        return {
            "trend": (
                "improving"
                if slope > 0.001
                else "declining" if slope < -0.001 else "stable"
            ),
            "slope": slope,
            "predicted_next": predicted_next,
            "r_squared": r_squared,
            "trend_strength": trend_strength,
            "data_points": n,
        }

    async def _detect_anomalies(self) -> Dict[str, Any]:
        """检测性能异常"""
        try:
            if not self.analysis_config.get("anomaly_detection_enabled", True):
                return {"enabled": False}

            anomalies = {}

            # 检查各维度异常
            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                if len(history["values"]) >= 10:
                    dimension_anomalies = await self._check_dimension_anomalies(
                        dimension, history["values"]
                    )
                    if dimension_anomalies:
                        anomalies[dimension.value] = dimension_anomalies

            # 检查系统指标异常
            system_anomalies = await self._check_system_anomalies()
            if system_anomalies:
                anomalies["system"] = system_anomalies

            return {
                "detected": len(anomalies) > 0,
                "anomalies": anomalies,
                "total_checked": len(PerformanceDimension) + 1,  # +1 for system
            }

        except Exception as e:
            logger.error(f"异常检测失败: {str(e)}")
            return {"error": str(e)}

    async def _check_dimension_anomalies(
        self, dimension: PerformanceDimension, values: List[float]
    ) -> List[Dict[str, Any]]:
        """检查维度异常"""
        anomalies = []

        if len(values) < 10:
            return anomalies

        recent_values = values[-10:]
        current_value = values[-1]

        # Z-score 异常检测
        mean = statistics.mean(recent_values)
        stdev = statistics.stdev(recent_values) if len(recent_values) >= 2 else 0

        if stdev > 0:
            z_score = abs(current_value - mean) / stdev
            if z_score > self.anomaly_detectors["z_score"]["threshold"]:
                anomalies.append(
                    {
                        "type": "z_score_outlier",
                        "value": current_value,
                        "z_score": z_score,
                        "threshold": self.anomaly_detectors["z_score"]["threshold"],
                        "severity": "high" if z_score > 5 else "medium",
                    }
                )

        # 变化率异常检测
        if len(values) >= 2:
            previous_value = values[-2]
            if previous_value != 0:
                rate_of_change = abs(current_value - previous_value) / previous_value
                if (
                    rate_of_change
                    > self.anomaly_detectors["rate_of_change"]["threshold"]
                ):
                    anomalies.append(
                        {
                            "type": "high_rate_of_change",
                            "value": current_value,
                            "rate_of_change": rate_of_change,
                            "threshold": self.anomaly_detectors["rate_of_change"][
                                "threshold"
                            ],
                            "severity": "high" if rate_of_change > 5 else "medium",
                        }
                    )

        return anomalies

    async def _check_system_anomalies(self) -> List[Dict[str, Any]]:
        """检查系统指标异常"""
        anomalies = []

        try:
            system_metrics = await self.collect_system_metrics()

            # 检查CPU使用率
            cpu_usage = system_metrics["cpu"]["percent"]
            if cpu_usage > self.metric_thresholds["cpu_usage"]["critical"]:
                anomalies.append(
                    {
                        "type": "critical_cpu_usage",
                        "metric": "cpu_usage",
                        "value": cpu_usage,
                        "threshold": self.metric_thresholds["cpu_usage"]["critical"],
                        "severity": "critical",
                    }
                )
            elif cpu_usage > self.metric_thresholds["cpu_usage"]["warning"]:
                anomalies.append(
                    {
                        "type": "warning_cpu_usage",
                        "metric": "cpu_usage",
                        "value": cpu_usage,
                        "threshold": self.metric_thresholds["cpu_usage"]["warning"],
                        "severity": "warning",
                    }
                )

            # 检查内存使用率
            memory_usage = system_metrics["memory"]["percent"]
            if memory_usage > self.metric_thresholds["memory_usage"]["critical"]:
                anomalies.append(
                    {
                        "type": "critical_memory_usage",
                        "metric": "memory_usage",
                        "value": memory_usage,
                        "threshold": self.metric_thresholds["memory_usage"]["critical"],
                        "severity": "critical",
                    }
                )
            elif memory_usage > self.metric_thresholds["memory_usage"]["warning"]:
                anomalies.append(
                    {
                        "type": "warning_memory_usage",
                        "metric": "memory_usage",
                        "value": memory_usage,
                        "threshold": self.metric_thresholds["memory_usage"]["warning"],
                        "severity": "warning",
                    }
                )

            return anomalies

        except Exception as e:
            logger.error(f"系统异常检查失败: {str(e)}")
            return [
                {"type": "system_check_error", "error": str(e), "severity": "medium"}
            ]

    async def identify_bottlenecks(self) -> Dict[str, Any]:
        """
        识别系统瓶颈

        Returns:
            Dict: 瓶颈分析结果
        """
        try:
            bottlenecks = {
                "timestamp": datetime.utcnow().isoformat(),
                "bottlenecks": [],
                "severity_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }

            # 分析系统瓶颈
            system_bottlenecks = await self._identify_system_bottlenecks()
            bottlenecks["bottlenecks"].extend(system_bottlenecks)

            # 分析应用瓶颈
            application_bottlenecks = await self._identify_application_bottlenecks()
            bottlenecks["bottlenecks"].extend(application_bottlenecks)

            # 分析架构瓶颈
            architecture_bottlenecks = await self._identify_architecture_bottlenecks()
            bottlenecks["bottlenecks"].extend(architecture_bottlenecks)

            # 统计严重程度
            for bottleneck in bottlenecks["bottlenecks"]:
                severity = bottleneck.get("severity", "low")
                bottlenecks["severity_summary"][severity] += 1

            # 计算整体瓶颈指数
            total_bottlenecks = len(bottlenecks["bottlenecks"])
            severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}

            weighted_sum = sum(
                severity_weights[b.get("severity", "low")]
                for b in bottlenecks["bottlenecks"]
            )

            max_possible_weight = total_bottlenecks * 4 if total_bottlenecks > 0 else 1
            bottleneck_index = (
                weighted_sum / max_possible_weight if max_possible_weight > 0 else 0
            )

            bottlenecks["bottleneck_index"] = bottleneck_index
            bottlenecks["overall_severity"] = self._determine_overall_severity(
                bottlenecks["severity_summary"]
            )

            logger.info(
                f"瓶颈识别完成: 发现{total_bottlenecks}个瓶颈, 指数: {bottleneck_index:.3f}"
            )
            return bottlenecks

        except Exception as e:
            logger.error(f"瓶颈识别失败: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "bottlenecks": [],
            }

    async def _identify_system_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别系统级瓶颈"""
        bottlenecks = []

        try:
            system_metrics = await self.collect_system_metrics()

            # CPU瓶颈
            cpu_usage = system_metrics["cpu"]["percent"]
            if cpu_usage > 90:
                bottlenecks.append(
                    {
                        "type": "system",
                        "category": "cpu",
                        "description": f"CPU使用率过高: {cpu_usage}%",
                        "severity": "critical" if cpu_usage > 95 else "high",
                        "impact": "系统响应缓慢，可能影响所有操作",
                        "suggested_actions": [
                            "优化CPU密集型任务",
                            "考虑水平扩展",
                            "检查是否有异常进程",
                        ],
                    }
                )

            # 内存瓶颈
            memory_usage = system_metrics["memory"]["percent"]
            if memory_usage > 90:
                bottlenecks.append(
                    {
                        "type": "system",
                        "category": "memory",
                        "description": f"内存使用率过高: {memory_usage}%",
                        "severity": "critical" if memory_usage > 95 else "high",
                        "impact": "可能发生内存交换，严重影响性能",
                        "suggested_actions": [
                            "优化内存使用",
                            "增加物理内存",
                            "检查内存泄漏",
                        ],
                    }
                )

            # 磁盘瓶颈
            disk_usage = system_metrics["disk"]["usage_percent"]
            if disk_usage > 95:
                bottlenecks.append(
                    {
                        "type": "system",
                        "category": "disk",
                        "description": f"磁盘空间不足: {disk_usage}%",
                        "severity": "critical",
                        "impact": "系统可能崩溃，无法写入数据",
                        "suggested_actions": [
                            "清理磁盘空间",
                            "增加磁盘容量",
                            "迁移数据到外部存储",
                        ],
                    }
                )

            return bottlenecks

        except Exception as e:
            logger.error(f"系统瓶颈识别失败: {str(e)}")
            return [
                {
                    "type": "system",
                    "category": "analysis_error",
                    "description": f"系统瓶颈分析失败: {str(e)}",
                    "severity": "medium",
                    "impact": "无法准确评估系统瓶颈",
                }
            ]

    async def _identify_application_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别应用级瓶颈"""
        bottlenecks = []

        try:
            app_metrics = await self.collect_application_metrics()

            # 响应时间瓶颈
            avg_response_time = app_metrics["response_time"]["average"]
            if avg_response_time > 5.0:  # 5秒
                bottlenecks.append(
                    {
                        "type": "application",
                        "category": "response_time",
                        "description": f"平均响应时间过长: {avg_response_time:.2f}秒",
                        "severity": "critical" if avg_response_time > 10 else "high",
                        "impact": "用户体验差，可能流失用户",
                        "suggested_actions": [
                            "优化数据库查询",
                            "实现缓存策略",
                            "优化算法复杂度",
                        ],
                    }
                )

            # 错误率瓶颈
            error_rate = app_metrics["error_rates"]["total"]
            if error_rate > 0.1:  # 10%
                bottlenecks.append(
                    {
                        "type": "application",
                        "category": "error_rate",
                        "description": f"错误率过高: {error_rate:.1%}",
                        "severity": "critical" if error_rate > 0.2 else "high",
                        "impact": "服务可靠性差，影响业务连续性",
                        "suggested_actions": [
                            "加强错误处理",
                            "改进输入验证",
                            "实施重试机制",
                        ],
                    }
                )

            # 吞吐量瓶颈
            throughput = app_metrics["throughput"]["requests_per_second"]
            # 这里需要根据具体业务设定阈值
            if throughput < 50:  # 示例阈值
                bottlenecks.append(
                    {
                        "type": "application",
                        "category": "throughput",
                        "description": f"系统吞吐量低: {throughput:.1f} 请求/秒",
                        "severity": "medium",
                        "impact": "系统处理能力有限，可能成为扩展瓶颈",
                        "suggested_actions": [
                            "优化并发处理",
                            "改进资源管理",
                            "考虑异步处理",
                        ],
                    }
                )

            return bottlenecks

        except Exception as e:
            logger.error(f"应用瓶颈识别失败: {str(e)}")
            return [
                {
                    "type": "application",
                    "category": "analysis_error",
                    "description": f"应用瓶颈分析失败: {str(e)}",
                    "severity": "medium",
                    "impact": "无法准确评估应用瓶颈",
                }
            ]

    async def _identify_architecture_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别架构级瓶颈"""
        bottlenecks = []

        try:
            # 分析性能维度间的协调问题
            dimension_scores = {}
            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                if history["values"]:
                    dimension_scores[dimension.value] = history["values"][-1]

            # 检查性能不均衡
            if dimension_scores:
                scores = list(dimension_scores.values())
                score_range = max(scores) - min(scores)

                if score_range > 0.3:  # 性能不均衡阈值
                    bottlenecks.append(
                        {
                            "type": "architecture",
                            "category": "performance_imbalance",
                            "description": f"系统性能不均衡，维度间差异达{score_range:.3f}",
                            "severity": "medium",
                            "impact": "部分维度性能优秀，但其他维度拖累整体表现",
                            "suggested_actions": [
                                "重新平衡资源分配",
                                "优化弱性能维度",
                                "考虑架构重构",
                            ],
                        }
                    )

            # 检查进化协调问题
            if len(self.performance_history["system"]["timestamps"]) > 10:
                system_stability = await self._calculate_dimension_stability(
                    self.performance_history["system"]["cpu_usage"]
                )
                if system_stability < 0.7:
                    bottlenecks.append(
                        {
                            "type": "architecture",
                            "category": "instability",
                            "description": f"系统稳定性不足: {system_stability:.3f}",
                            "severity": "high",
                            "impact": "系统表现波动大，影响可靠性和预测性",
                            "suggested_actions": [
                                "改进资源管理策略",
                                "优化负载均衡",
                                "增强容错机制",
                            ],
                        }
                    )

            return bottlenecks

        except Exception as e:
            logger.error(f"架构瓶颈识别失败: {str(e)}")
            return [
                {
                    "type": "architecture",
                    "category": "analysis_error",
                    "description": f"架构瓶颈分析失败: {str(e)}",
                    "severity": "medium",
                    "impact": "无法准确评估架构瓶颈",
                }
            ]

    def _determine_overall_severity(self, severity_summary: Dict[str, int]) -> str:
        """确定整体严重程度"""
        if severity_summary["critical"] > 0:
            return "critical"
        elif severity_summary["high"] > 0:
            return "high"
        elif severity_summary["medium"] > 0:
            return "medium"
        else:
            return "low"

    async def _generate_recommendations(
        self, analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        try:
            # 基于瓶颈生成建议
            bottlenecks = analysis_results.get("bottlenecks", {}).get("bottlenecks", [])
            for bottleneck in bottlenecks:
                if "suggested_actions" in bottleneck:
                    for action in bottleneck["suggested_actions"]:
                        recommendations.append(
                            {
                                "type": "bottleneck_resolution",
                                "priority": bottleneck.get("severity", "medium"),
                                "description": action,
                                "related_bottleneck": bottleneck.get("description", ""),
                                "estimated_impact": (
                                    "high"
                                    if bottleneck.get("severity")
                                    in ["critical", "high"]
                                    else "medium"
                                ),
                            }
                        )

            # 基于趋势生成建议
            trends = analysis_results.get("trends", {})
            for dimension, trend_info in trends.items():
                if trend_info.get("trend") == "declining" and trend_info.get(
                    "trend_strength"
                ) in ["moderate", "strong"]:
                    recommendations.append(
                        {
                            "type": "preventive_maintenance",
                            "priority": "medium",
                            "description": f"检测到{dimension}性能下降趋势，建议进行预防性优化",
                            "related_metric": dimension,
                            "trend_strength": trend_info.get("trend_strength"),
                            "estimated_impact": "medium",
                        }
                    )

            # 基于异常生成建议
            anomalies = analysis_results.get("anomalies", {}).get("anomalies", {})
            if anomalies:
                recommendations.append(
                    {
                        "type": "anomaly_investigation",
                        "priority": "high",
                        "description": f"检测到{len(anomalies)}个性能异常，建议立即调查",
                        "anomaly_count": len(anomalies),
                        "estimated_impact": "high",
                    }
                )

            # 去重和优先级排序
            unique_recommendations = []
            seen_descriptions = set()

            for rec in recommendations:
                if rec["description"] not in seen_descriptions:
                    seen_descriptions.add(rec["description"])
                    unique_recommendations.append(rec)

            # 按优先级排序
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            unique_recommendations.sort(
                key=lambda x: priority_order.get(x["priority"], 3)
            )

            return unique_recommendations[:10]  # 返回前10个建议

        except Exception as e:
            logger.error(f"建议生成失败: {str(e)}")
            return [
                {
                    "type": "analysis_error",
                    "priority": "medium",
                    "description": f"建议生成过程中发生错误: {str(e)}",
                    "estimated_impact": "low",
                }
            ]

    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的分析结果"""
        try:
            if cache_key in self.analysis_cache:
                cached_data = self.analysis_cache[cache_key]
                cache_time = cached_data.get("cache_time")

                if (
                    cache_time
                    and (datetime.utcnow() - cache_time).total_seconds()
                    < self.cache_ttl
                ):
                    return cached_data.get("data")

            return None

        except Exception as e:
            logger.error(f"缓存获取失败: {str(e)}")
            return None

    def _cache_analysis(self, cache_key: str, data: Dict[str, Any]):
        """缓存分析结果"""
        try:
            self.analysis_cache[cache_key] = {
                "data": data,
                "cache_time": datetime.utcnow(),
            }

            # 清理过期缓存
            current_time = datetime.utcnow()
            expired_keys = [
                key
                for key, cached in self.analysis_cache.items()
                if (current_time - cached["cache_time"]).total_seconds()
                > self.cache_ttl
            ]

            for key in expired_keys:
                del self.analysis_cache[key]

        except Exception as e:
            logger.error(f"缓存存储失败: {str(e)}")

    async def get_performance_history(
        self, dimension: str, hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取性能历史数据

        Args:
            dimension: 性能维度
            hours: 时间范围(小时)

        Returns:
            Dict: 历史数据
        """
        try:
            if dimension not in self.performance_history:
                return {"error": f"未知性能维度: {dimension}"}

            history = self.performance_history[dimension]
            if not history["timestamps"]:
                return {"data": [], "timestamps": []}

            # 计算时间边界
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # 过滤数据
            filtered_data = []
            filtered_timestamps = []

            for i, timestamp in enumerate(history["timestamps"]):
                if timestamp >= cutoff_time:
                    filtered_timestamps.append(timestamp.isoformat())
                    if i < len(history["values"]):
                        filtered_data.append(history["values"][i])

            return {
                "dimension": dimension,
                "data": filtered_data,
                "timestamps": filtered_timestamps,
                "data_points": len(filtered_data),
                "time_range_hours": hours,
            }

        except Exception as e:
            logger.error(f"历史数据获取失败: {str(e)}")
            return {"error": str(e)}

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            # 检查数据收集状态
            data_status = {}
            total_data_points = 0
            active_dimensions = 0

            for dimension in PerformanceDimension:
                history = self.performance_history[dimension.value]
                data_points = len(history["values"])
                total_data_points += data_points

                if data_points > 0:
                    active_dimensions += 1
                    data_status[dimension.value] = {
                        "data_points": data_points,
                        "last_update": (
                            history["timestamps"][-1].isoformat()
                            if history["timestamps"]
                            else None
                        ),
                        "status": "active",
                    }
                else:
                    data_status[dimension.value] = {
                        "data_points": 0,
                        "status": "inactive",
                    }

            # 评估整体健康状态
            health_score = (
                active_dimensions / len(PerformanceDimension)
                if PerformanceDimension
                else 1.0
            )

            if health_score >= 0.8:
                status = "healthy"
            elif health_score >= 0.5:
                status = "degraded"
            else:
                status = "unhealthy"

            return {
                "status": status,
                "health_score": health_score,
                "initialized": self.is_initialized,
                "analysis_count": self.analysis_count,
                "active_dimensions": active_dimensions,
                "total_data_points": total_data_points,
                "data_status": data_status,
                "last_analysis": (
                    self.last_analysis_time.isoformat()
                    if self.last_analysis_time
                    else None
                ),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "health_score": 0.0,
                "error": str(e),
                "initialized": self.is_initialized,
            }

    async def generate_performance_report(
        self, report_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        生成性能报告

        Args:
            report_type: 报告类型

        Returns:
            Dict: 性能报告
        """
        try:
            logger.info(f"生成性能报告: {report_type}")

            # 执行综合分析
            analysis = await self.get_comprehensive_analysis()

            # 生成报告
            report = {
                "report_id": f"report_{int(time.time())}",
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": report_type,
                "executive_summary": await self._generate_executive_summary(analysis),
                "detailed_analysis": analysis,
                "recommendations": analysis.get("recommendations", []),
                "metadata": {
                    "analysis_duration": "实时",
                    "data_sources": [
                        "system_metrics",
                        "application_metrics",
                        "performance_history",
                    ],
                    "report_version": "1.0",
                },
            }

            return report

        except Exception as e:
            logger.error(f"性能报告生成失败: {str(e)}")
            return {
                "report_id": f"report_error_{int(time.time())}",
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
                "report_type": report_type,
            }

    async def _generate_executive_summary(
        self, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成执行摘要"""
        try:
            summary = analysis.get("summary", {})
            bottlenecks = analysis.get("bottlenecks", {})
            trends = analysis.get("trends", {})
            anomalies = analysis.get("anomalies", {})

            return {
                "overall_performance": summary.get("overall_score", 0.0),
                "performance_status": summary.get("status", "unknown"),
                "key_metrics": {
                    "bottlenecks_count": len(bottlenecks.get("bottlenecks", [])),
                    "critical_bottlenecks": bottlenecks.get("severity_summary", {}).get(
                        "critical", 0
                    ),
                    "anomalies_detected": anomalies.get("detected", False),
                    "improving_trends": sum(
                        1 for t in trends.values() if t.get("trend") == "improving"
                    ),
                    "declining_trends": sum(
                        1 for t in trends.values() if t.get("trend") == "declining"
                    ),
                },
                "top_recommendations": [
                    rec
                    for rec in analysis.get("recommendations", [])
                    if rec.get("priority") in ["critical", "high"]
                ][
                    :3
                ],  # 前3个高优先级建议
            }

        except Exception as e:
            logger.error(f"执行摘要生成失败: {str(e)}")
            return {
                "overall_performance": 0.0,
                "performance_status": "analysis_error",
                "error": str(e),
            }
