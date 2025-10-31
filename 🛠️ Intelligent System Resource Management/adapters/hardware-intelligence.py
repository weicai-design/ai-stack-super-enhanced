"""
硬件智能监控模块
跨平台硬件状态监控、性能分析和智能优化

功能特性：
- 多平台硬件兼容监控
- 实时性能指标收集
- 智能故障预测
- 动态资源分配建议
- 硬件健康状态评估

版本: 1.0.0
创建日期: 2024-12-19
"""

import asyncio
import logging
import platform
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import psutil

from . import BaseSystemAdapter, HardwareMonitoringError, SystemAdapterFactory

logger = logging.getLogger(__name__)


class HardwareComponent(Enum):
    """硬件组件枚举"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    BATTERY = "battery"
    SENSORS = "sensors"


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HardwareIntelligence(BaseSystemAdapter):
    """
    硬件智能监控器
    提供跨平台的硬件状态监控和智能分析
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化硬件智能监控器

        Args:
            config: 监控器配置
        """
        super().__init__(config)
        self.monitoring_interval = config.get("monitoring_interval", 5)  # 秒
        self.health_thresholds = config.get(
            "health_thresholds",
            {
                "cpu_usage_critical": 90,
                "memory_usage_critical": 85,
                "disk_usage_critical": 90,
                "temperature_critical": 85,
            },
        )
        self._monitoring_task = None
        self._is_monitoring = False
        self._hardware_metrics_history = {}
        self._component_health = {}
        self._prediction_models = {}

    async def _setup_adapter(self):
        """设置硬件监控器"""
        try:
            # 初始化硬件组件状态
            await self._initialize_hardware_components()

            # 设置监控指标历史记录
            for component in HardwareComponent:
                self._hardware_metrics_history[component.value] = []
                self._component_health[component.value] = HealthStatus.UNKNOWN

            # 初始化性能基准
            await self._establish_performance_baselines()

            # 启动监控任务
            self._is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._continuous_monitoring())

            logger.info("硬件智能监控器初始化完成")

        except Exception as e:
            logger.error(f"硬件监控器初始化失败: {str(e)}")
            raise HardwareMonitoringError(f"硬件监控器初始化失败: {str(e)}") from e

    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取硬件系统详细信息

        Returns:
            Dict: 硬件信息字典
        """
        try:
            hardware_info = {
                "platform": {
                    "system": platform.system(),
                    "version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": platform.processor(),
                },
                "components": {},
                "health_summary": await self._get_health_summary(),
                "performance_metrics": await self._get_current_metrics(),
                "recommendations": await self._generate_recommendations(),
            }

            # 收集各组件详细信息
            for component in HardwareComponent:
                component_info = await self._get_component_info(component)
                hardware_info["components"][component.value] = component_info

            return hardware_info

        except Exception as e:
            logger.error(f"获取硬件信息失败: {str(e)}")
            return {"error": f"获取硬件信息失败: {str(e)}"}

    async def optimize_performance(
        self, optimization_level: str = "balanced"
    ) -> Dict[str, Any]:
        """
        基于硬件智能的性能优化

        Args:
            optimization_level: 优化级别

        Returns:
            Dict: 优化建议和结果
        """
        optimization_report = {
            "optimization_level": optimization_level,
            "timestamp": datetime.utcnow().isoformat(),
            "hardware_analysis": await self._analyze_hardware_capabilities(),
            "recommendations": [],
            "estimated_improvements": {},
            "warnings": [],
        }

        try:
            # 基于当前硬件状态生成优化建议
            analysis = await self._analyze_hardware_capabilities()

            if optimization_level == "performance":
                recommendations = await self._generate_performance_recommendations(
                    analysis
                )
            elif optimization_level == "power_saving":
                recommendations = await self._generate_power_saving_recommendations(
                    analysis
                )
            else:  # balanced
                recommendations = await self._generate_balanced_recommendations(
                    analysis
                )

            optimization_report["recommendations"] = recommendations
            optimization_report["estimated_improvements"] = (
                await self._estimate_improvements(recommendations)
            )

            # 检查潜在风险
            risks = await self._assess_optimization_risks(recommendations)
            if risks:
                optimization_report["warnings"] = risks

        except Exception as e:
            error_msg = f"硬件性能优化分析失败: {str(e)}"
            logger.error(error_msg)
            optimization_report["error"] = error_msg

        return optimization_report

    async def _continuous_monitoring(self):
        """持续硬件监控循环"""
        logger.info("启动硬件持续监控")

        while self._is_monitoring:
            try:
                # 收集所有硬件指标
                current_metrics = await self._collect_all_metrics()

                # 更新健康状态
                await self._update_health_status(current_metrics)

                # 存储历史数据（限制历史记录长度）
                for component, metrics in current_metrics.items():
                    history = self._hardware_metrics_history.get(component, [])
                    history.append(
                        {"timestamp": datetime.utcnow().isoformat(), "metrics": metrics}
                    )
                    # 保留最近100条记录
                    if len(history) > 100:
                        history.pop(0)

                # 检查异常情况
                await self._check_anomalies(current_metrics)

                # 预测性维护检查
                await self._predictive_maintenance_check()

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"硬件监控循环异常: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)  # 继续监控

    async def _initialize_hardware_components(self):
        """初始化硬件组件监控"""
        logger.info("初始化硬件组件监控")

        # 检测可用的硬件组件
        available_components = []

        # CPU 总是可用
        available_components.append(HardwareComponent.CPU)

        # 内存
        if hasattr(psutil, "virtual_memory"):
            available_components.append(HardwareComponent.MEMORY)

        # 磁盘
        if hasattr(psutil, "disk_usage"):
            available_components.append(HardwareComponent.DISK)

        # 网络
        if hasattr(psutil, "net_io_counters"):
            available_components.append(HardwareComponent.NETWORK)

        # 电池（如果可用）
        if hasattr(psutil, "sensors_battery"):
            try:
                battery = psutil.sensors_battery()
                if battery:
                    available_components.append(HardwareComponent.BATTERY)
            except:
                pass

        # 传感器
        if hasattr(psutil, "sensors_temperatures"):
            available_components.append(HardwareComponent.SENSORS)

        self._available_components = available_components
        logger.info(
            f"检测到可用硬件组件: {[comp.value for comp in available_components]}"
        )

    async def _collect_all_metrics(self) -> Dict[str, Any]:
        """收集所有硬件指标"""
        metrics = {}

        for component in self._available_components:
            try:
                if component == HardwareComponent.CPU:
                    metrics["cpu"] = await self._get_cpu_metrics()
                elif component == HardwareComponent.MEMORY:
                    metrics["memory"] = await self._get_memory_metrics()
                elif component == HardwareComponent.DISK:
                    metrics["disk"] = await self._get_disk_metrics()
                elif component == HardwareComponent.NETWORK:
                    metrics["network"] = await self._get_network_metrics()
                elif component == HardwareComponent.BATTERY:
                    metrics["battery"] = await self._get_battery_metrics()
                elif component == HardwareComponent.SENSORS:
                    metrics["sensors"] = await self._get_sensor_metrics()
            except Exception as e:
                logger.warning(f"收集 {component.value} 指标失败: {str(e)}")
                metrics[component.value] = {"error": str(e)}

        return metrics

    async def _get_cpu_metrics(self) -> Dict[str, Any]:
        """获取CPU指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_times = psutil.cpu_times()
            cpu_freq = psutil.cpu_freq()
            load_avg = (
                psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
            )

            return {
                "usage_percent": cpu_percent,
                "user_time": cpu_times.user,
                "system_time": cpu_times.system,
                "idle_time": cpu_times.idle,
                "core_count": psutil.cpu_count(logical=False),
                "logical_core_count": psutil.cpu_count(logical=True),
                "frequency_current": cpu_freq.current if cpu_freq else None,
                "frequency_min": cpu_freq.min if cpu_freq else None,
                "frequency_max": cpu_freq.max if cpu_freq else None,
                "load_1min": load_avg[0],
                "load_5min": load_avg[1],
                "load_15min": load_avg[2],
            }
        except Exception as e:
            logger.error(f"获取CPU指标失败: {str(e)}")
            return {"error": str(e)}

    async def _get_memory_metrics(self) -> Dict[str, Any]:
        """获取内存指标"""
        try:
            virtual_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()

            return {
                "total_gb": virtual_memory.total / (1024**3),
                "available_gb": virtual_memory.available / (1024**3),
                "used_gb": virtual_memory.used / (1024**3),
                "usage_percent": virtual_memory.percent,
                "swap_total_gb": swap_memory.total / (1024**3),
                "swap_used_gb": swap_memory.used / (1024**3),
                "swap_usage_percent": swap_memory.percent,
            }
        except Exception as e:
            logger.error(f"获取内存指标失败: {str(e)}")
            return {"error": str(e)}

    async def _get_disk_metrics(self) -> Dict[str, Any]:
        """获取磁盘指标"""
        try:
            disk_usage = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            return {
                "total_gb": disk_usage.total / (1024**3),
                "used_gb": disk_usage.used / (1024**3),
                "free_gb": disk_usage.free / (1024**3),
                "usage_percent": (disk_usage.used / disk_usage.total) * 100,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0,
            }
        except Exception as e:
            logger.error(f"获取磁盘指标失败: {str(e)}")
            return {"error": str(e)}

    async def _get_network_metrics(self) -> Dict[str, Any]:
        """获取网络指标"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())

            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "active_connections": net_connections,
            }
        except Exception as e:
            logger.error(f"获取网络指标失败: {str(e)}")
            return {"error": str(e)}

    async def _get_battery_metrics(self) -> Dict[str, Any]:
        """获取电池指标"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "seconds_left": (
                        battery.secsleft
                        if battery.secsleft != psutil.POWER_TIME_UNLIMITED
                        else None
                    ),
                }
            else:
                return {"available": False}
        except Exception as e:
            logger.error(f"获取电池指标失败: {str(e)}")
            return {"error": str(e)}

    async def _get_sensor_metrics(self) -> Dict[str, Any]:
        """获取传感器指标"""
        try:
            temperatures = psutil.sensors_temperatures()
            fans = psutil.sensors_fans()

            sensor_data = {"temperatures": {}, "fans": {}}

            if temperatures:
                for name, entries in temperatures.items():
                    sensor_data["temperatures"][name] = [
                        {
                            "label": entry.label or f"Sensor {i}",
                            "current": entry.current,
                        }
                        for i, entry in enumerate(entries)
                    ]

            if fans:
                for name, entries in fans.items():
                    sensor_data["fans"][name] = [
                        {"label": entry.label or f"Fan {i}", "current": entry.current}
                        for i, entry in enumerate(entries)
                    ]

            return sensor_data
        except Exception as e:
            logger.error(f"获取传感器指标失败: {str(e)}")
            return {"error": str(e)}

    async def _update_health_status(self, current_metrics: Dict[str, Any]):
        """更新硬件健康状态"""
        for component, metrics in current_metrics.items():
            if "error" in metrics:
                self._component_health[component] = HealthStatus.UNKNOWN
                continue

            try:
                if component == "cpu":
                    health = await self._assess_cpu_health(metrics)
                elif component == "memory":
                    health = await self._assess_memory_health(metrics)
                elif component == "disk":
                    health = await self._assess_disk_health(metrics)
                elif component == "battery":
                    health = await self._assess_battery_health(metrics)
                else:
                    health = HealthStatus.HEALTHY

                self._component_health[component] = health

            except Exception as e:
                logger.warning(f"评估 {component} 健康状态失败: {str(e)}")
                self._component_health[component] = HealthStatus.UNKNOWN

    async def _assess_cpu_health(self, metrics: Dict[str, Any]) -> HealthStatus:
        """评估CPU健康状态"""
        usage = metrics.get("usage_percent", 0)
        load = metrics.get("load_15min", 0)

        if usage > self.health_thresholds["cpu_usage_critical"] and load > 2.0:
            return HealthStatus.CRITICAL
        elif usage > 80:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _assess_memory_health(self, metrics: Dict[str, Any]) -> HealthStatus:
        """评估内存健康状态"""
        usage = metrics.get("usage_percent", 0)
        swap_usage = metrics.get("swap_usage_percent", 0)

        if usage > self.health_thresholds["memory_usage_critical"]:
            return HealthStatus.CRITICAL
        elif usage > 75 or swap_usage > 50:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _assess_disk_health(self, metrics: Dict[str, Any]) -> HealthStatus:
        """评估磁盘健康状态"""
        usage = metrics.get("usage_percent", 0)

        if usage > self.health_thresholds["disk_usage_critical"]:
            return HealthStatus.CRITICAL
        elif usage > 80:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _assess_battery_health(self, metrics: Dict[str, Any]) -> HealthStatus:
        """评估电池健康状态"""
        if not metrics.get("available", False):
            return HealthStatus.UNKNOWN

        percent = metrics.get("percent", 100)

        if percent < 10 and not metrics.get("power_plugged", True):
            return HealthStatus.CRITICAL
        elif percent < 20 and not metrics.get("power_plugged", True):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def _get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        critical_components = []
        degraded_components = []

        for component, health in self._component_health.items():
            if health == HealthStatus.CRITICAL:
                critical_components.append(component)
            elif health == HealthStatus.DEGRADED:
                degraded_components.append(component)

        overall_health = HealthStatus.HEALTHY
        if critical_components:
            overall_health = HealthStatus.CRITICAL
        elif degraded_components:
            overall_health = HealthStatus.DEGRADED

        return {
            "overall": overall_health.value,
            "components": {
                comp: health.value for comp, health in self._component_health.items()
            },
            "critical_components": critical_components,
            "degraded_components": degraded_components,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def _get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        # 返回最近收集的指标
        current_metrics = {}
        for component, history in self._hardware_metrics_history.items():
            if history:
                current_metrics[component] = history[-1]["metrics"]

        return current_metrics

    async def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []
        health_summary = await self._get_health_summary()

        # 基于健康状态生成建议
        for component in health_summary["critical_components"]:
            recommendations.append(
                {
                    "component": component,
                    "priority": "high",
                    "message": f"{component} 处于严重状态，建议立即处理",
                    "action": f"检查{component}使用情况并释放资源",
                }
            )

        for component in health_summary["degraded_components"]:
            recommendations.append(
                {
                    "component": component,
                    "priority": "medium",
                    "message": f"{component} 性能下降，建议优化",
                    "action": f"优化{component}配置或清理资源",
                }
            )

        return recommendations

    async def _analyze_hardware_capabilities(self) -> Dict[str, Any]:
        """分析硬件能力"""
        return {
            "cpu_capabilities": await self._analyze_cpu_capabilities(),
            "memory_capabilities": await self._analyze_memory_capabilities(),
            "storage_capabilities": await self._analyze_storage_capabilities(),
            "bottleneck_analysis": await self._identify_bottlenecks(),
        }

    async def _check_anomalies(self, current_metrics: Dict[str, Any]):
        """检查硬件异常"""
        # 实现异常检测逻辑
        pass

    async def _predictive_maintenance_check(self):
        """预测性维护检查"""
        # 实现预测性维护逻辑
        pass

    # 以下为占位方法，需要根据具体需求实现
    async def _establish_performance_baselines(self):
        """建立性能基准"""
        pass

    async def _get_component_info(self, component: HardwareComponent) -> Dict[str, Any]:
        """获取组件详细信息"""
        return {}

    async def _generate_performance_recommendations(
        self, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成性能优化建议"""
        return []

    async def _generate_power_saving_recommendations(
        self, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成节能建议"""
        return []

    async def _generate_balanced_recommendations(
        self, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成平衡建议"""
        return []

    async def _estimate_improvements(
        self, recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """估计改进效果"""
        return {}

    async def _assess_optimization_risks(
        self, recommendations: List[Dict[str, Any]]
    ) -> List[str]:
        """评估优化风险"""
        return []

    async def _analyze_cpu_capabilities(self) -> Dict[str, Any]:
        """分析CPU能力"""
        return {}

    async def _analyze_memory_capabilities(self) -> Dict[str, Any]:
        """分析内存能力"""
        return {}

    async def _analyze_storage_capabilities(self) -> Dict[str, Any]:
        """分析存储能力"""
        return {}

    async def _identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        return []

    async def cleanup(self):
        """清理资源"""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        await super().cleanup()
        logger.info("硬件智能监控器资源清理完成")


# 注册到适配器工厂
SystemAdapterFactory.register_adapter("hardware_intelligence", HardwareIntelligence)

logger.info("硬件智能监控模块加载完成")
