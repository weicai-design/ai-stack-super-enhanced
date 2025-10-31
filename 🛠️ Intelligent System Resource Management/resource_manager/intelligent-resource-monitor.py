"""
智能资源监控器
对应需求: 8.1/8.2/8.5 - 资源监控、冲突检测、动态调配
对应开发规则: 性能与资源管理优化、统一生命周期接口
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """资源类型枚举"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    STORAGE = "storage"


class ResourceStatus(Enum):
    """资源状态枚举"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OVERLOAD = "overload"


@dataclass
class ResourceMetric:
    """资源指标数据类"""

    resource_type: ResourceType
    usage_percent: float
    usage_value: float
    total_value: float
    unit: str
    timestamp: datetime
    status: ResourceStatus


class IntelligentResourceMonitor:
    """
    智能资源监控器
    实现系统资源的实时监控、趋势分析和预警
    """

    def __init__(self):
        self.core_services = {}
        self.monitoring_tasks = {}
        self.metric_history = {}
        self.alert_thresholds = {
            ResourceType.CPU: {"warning": 70.0, "critical": 85.0},
            ResourceType.MEMORY: {"warning": 75.0, "critical": 90.0},
            ResourceType.DISK: {"warning": 80.0, "critical": 95.0},
            ResourceType.NETWORK: {"warning": 60.0, "critical": 80.0},
        }
        self.monitoring_interval = 5  # 监控间隔(秒)
        self.is_monitoring = False

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """
        初始化资源监控器
        对应开发规则: 统一生命周期接口
        """
        self.config = config or {}
        self.core_services = core_services or {}

        # 初始化指标历史记录
        for resource_type in ResourceType:
            self.metric_history[resource_type] = []

        logger.info("智能资源监控器初始化完成")

    async def start(self):
        """启动资源监控"""
        if self.is_monitoring:
            logger.warning("资源监控已在运行中")
            return

        self.is_monitoring = True
        self.monitoring_tasks["cpu_monitor"] = asyncio.create_task(
            self._monitor_cpu_usage()
        )
        self.monitoring_tasks["memory_monitor"] = asyncio.create_task(
            self._monitor_memory_usage()
        )
        self.monitoring_tasks["disk_monitor"] = asyncio.create_task(
            self._monitor_disk_usage()
        )
        self.monitoring_tasks["network_monitor"] = asyncio.create_task(
            self._monitor_network_usage()
        )

        logger.info("资源监控已启动")

    async def stop(self):
        """停止资源监控"""
        self.is_monitoring = False

        # 停止所有监控任务
        for task_name, task in self.monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.monitoring_tasks.clear()
        logger.info("资源监控已停止")

    async def get_health_status(self) -> Dict:
        """获取健康状态"""
        current_metrics = await self.get_current_metrics()
        overall_health = self._calculate_overall_health(current_metrics)

        return {
            "status": overall_health.value,
            "details": current_metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "active_monitors": len(self.monitoring_tasks),
                "history_size": sum(
                    len(history) for history in self.metric_history.values()
                ),
            },
        }

    async def get_current_metrics(self) -> Dict[str, ResourceMetric]:
        """获取当前资源指标"""
        tasks = [
            self._get_cpu_metric(),
            self._get_memory_metric(),
            self._get_disk_metric(),
            self._get_network_metric(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        metrics = {}
        resource_types = [
            ResourceType.CPU,
            ResourceType.MEMORY,
            ResourceType.DISK,
            ResourceType.NETWORK,
        ]

        for i, resource_type in enumerate(resource_types):
            if not isinstance(results[i], Exception):
                metrics[resource_type.value] = results[i]

        return metrics

    async def _monitor_cpu_usage(self):
        """监控CPU使用率"""
        while self.is_monitoring:
            try:
                cpu_metric = await self._get_cpu_metric()
                self._record_metric(cpu_metric)

                # 检查预警
                await self._check_resource_alert(cpu_metric)

            except Exception as e:
                logger.error(f"CPU监控异常: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def _monitor_memory_usage(self):
        """监控内存使用率"""
        while self.is_monitoring:
            try:
                memory_metric = await self._get_memory_metric()
                self._record_metric(memory_metric)

                # 检查预警
                await self._check_resource_alert(memory_metric)

            except Exception as e:
                logger.error(f"内存监控异常: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def _monitor_disk_usage(self):
        """监控磁盘使用率"""
        while self.is_monitoring:
            try:
                disk_metric = await self._get_disk_metric()
                self._record_metric(disk_metric)

                # 检查预警
                await self._check_resource_alert(disk_metric)

            except Exception as e:
                logger.error(f"磁盘监控异常: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def _monitor_network_usage(self):
        """监控网络使用率"""
        while self.is_monitoring:
            try:
                network_metric = await self._get_network_metric()
                self._record_metric(network_metric)

                # 检查预警
                await self._check_resource_alert(network_metric)

            except Exception as e:
                logger.error(f"网络监控异常: {e}")

            await asyncio.sleep(self.monitoring_interval)

    async def _get_cpu_metric(self) -> ResourceMetric:
        """获取CPU指标 - 非阻塞实现"""
        loop = asyncio.get_event_loop()
        cpu_percent = await loop.run_in_executor(
            None, lambda: psutil.cpu_percent(interval=0.5)
        )

        status = self._evaluate_resource_status(ResourceType.CPU, cpu_percent)

        return ResourceMetric(
            resource_type=ResourceType.CPU,
            usage_percent=cpu_percent,
            usage_value=cpu_percent,
            total_value=100.0,
            unit="percent",
            timestamp=datetime.utcnow(),
            status=status,
        )

    async def _get_memory_metric(self) -> ResourceMetric:
        """获取内存指标"""
        loop = asyncio.get_event_loop()
        memory_info = await loop.run_in_executor(None, psutil.virtual_memory)

        usage_percent = memory_info.percent
        status = self._evaluate_resource_status(ResourceType.MEMORY, usage_percent)

        return ResourceMetric(
            resource_type=ResourceType.MEMORY,
            usage_percent=usage_percent,
            usage_value=memory_info.used,
            total_value=memory_info.total,
            unit="bytes",
            timestamp=datetime.utcnow(),
            status=status,
        )

    async def _get_disk_metric(self) -> ResourceMetric:
        """获取磁盘指标"""
        loop = asyncio.get_event_loop()
        disk_info = await loop.run_in_executor(None, lambda: psutil.disk_usage("/"))

        usage_percent = (disk_info.used / disk_info.total) * 100
        status = self._evaluate_resource_status(ResourceType.DISK, usage_percent)

        return ResourceMetric(
            resource_type=ResourceType.DISK,
            usage_percent=usage_percent,
            usage_value=disk_info.used,
            total_value=disk_info.total,
            unit="bytes",
            timestamp=datetime.utcnow(),
            status=status,
        )

    async def _get_network_metric(self) -> ResourceMetric:
        """获取网络指标"""
        loop = asyncio.get_event_loop()
        net_io = await loop.run_in_executor(None, psutil.net_io_counters)

        # 计算网络使用率 (基于历史数据)
        usage_percent = 0.0  # 简化实现，实际需要基于历史数据计算

        status = self._evaluate_resource_status(ResourceType.NETWORK, usage_percent)

        return ResourceMetric(
            resource_type=ResourceType.NETWORK,
            usage_percent=usage_percent,
            usage_value=net_io.bytes_sent + net_io.bytes_recv if net_io else 0,
            total_value=0,  # 网络无总容量概念
            unit="bytes",
            timestamp=datetime.utcnow(),
            status=status,
        )

    def _evaluate_resource_status(
        self, resource_type: ResourceType, usage_percent: float
    ) -> ResourceStatus:
        """评估资源状态"""
        thresholds = self.alert_thresholds.get(resource_type, {})

        if usage_percent >= thresholds.get("critical", 85):
            return ResourceStatus.CRITICAL
        elif usage_percent >= thresholds.get("warning", 70):
            return ResourceStatus.WARNING
        else:
            return ResourceStatus.HEALTHY

    def _record_metric(self, metric: ResourceMetric):
        """记录指标到历史"""
        history = self.metric_history[metric.resource_type]
        history.append(metric)

        # 保留最近1小时的数据 (基于监控间隔计算)
        max_records = 3600 // self.monitoring_interval
        if len(history) > max_records:
            self.metric_history[metric.resource_type] = history[-max_records:]

    def _calculate_overall_health(
        self, current_metrics: Dict[str, ResourceMetric]
    ) -> ResourceStatus:
        """计算整体健康状态"""
        if not current_metrics:
            return ResourceStatus.HEALTHY

        status_priority = {
            ResourceStatus.CRITICAL: 3,
            ResourceStatus.WARNING: 2,
            ResourceStatus.OVERLOAD: 1,
            ResourceStatus.HEALTHY: 0,
        }

        # 取最严重的状态
        worst_status = max(
            current_metrics.values(), key=lambda x: status_priority[x.status]
        ).status

        return worst_status

    async def _check_resource_alert(self, metric: ResourceMetric):
        """检查资源预警"""
        if metric.status in [ResourceStatus.WARNING, ResourceStatus.CRITICAL]:
            # 发布资源预警事件
            event_bus = self.core_services.get("event_bus")
            if event_bus:
                await event_bus.publish(
                    "resource.alert",
                    {
                        "resource_type": metric.resource_type.value,
                        "usage_percent": metric.usage_percent,
                        "status": metric.status.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "message": f"{metric.resource_type.value} 资源使用率 {metric.usage_percent:.1f}% - {metric.status.value}",
                    },
                    {"source": "resource_monitor"},
                )

    async def get_resource_trend(
        self, resource_type: ResourceType, hours: int = 1
    ) -> List[ResourceMetric]:
        """获取资源趋势数据"""
        history = self.metric_history.get(resource_type, [])

        if not history:
            return []

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [metric for metric in history if metric.timestamp >= cutoff_time]

    async def set_alert_threshold(
        self, resource_type: ResourceType, warning: float, critical: float
    ):
        """设置预警阈值"""
        self.alert_thresholds[resource_type] = {
            "warning": max(0, min(100, warning)),
            "critical": max(0, min(100, critical)),
        }
        logger.info(
            f"已更新 {resource_type.value} 预警阈值: 警告={warning}%, 严重={critical}%"
        )
