"""
智能资源治理器
功能：管理系统资源分配，监控资源使用，优化资源调度
版本：1.0.0
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """资源类型枚举"""

    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class ResourcePriority(Enum):
    """资源优先级枚举"""

    CRITICAL = "critical"  # 关键系统服务
    HIGH = "high"  # 核心业务模块
    MEDIUM = "medium"  # 一般功能模块
    LOW = "low"  # 后台任务
    IDLE = "idle"  # 低优先级任务


@dataclass
class ResourceQuota:
    """资源配额"""

    cpu_limit: float = 1.0  # CPU使用限制 (0.0-1.0)
    memory_limit_mb: int = 1024  # 内存限制 (MB)
    disk_quota_mb: int = 10240  # 磁盘配额 (MB)
    network_bandwidth_mbps: int = 100  # 网络带宽 (Mbps)
    gpu_memory_mb: int = 0  # GPU内存 (MB)


@dataclass
class ResourceUsage:
    """资源使用情况"""

    cpu_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0
    disk_used_mb: float = 0.0
    disk_percent: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    gpu_usage_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    timestamp: float = 0.0


@dataclass
class ResourceAllocation:
    """资源分配"""

    module_name: str
    priority: ResourcePriority
    quota: ResourceQuota
    current_usage: ResourceUsage
    allocated_resources: Dict[str, Any]


class ResourceGovernor:
    """
    智能资源治理器
    负责系统资源的监控、分配和优化
    """

    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        self._allocations: Dict[str, ResourceAllocation] = {}
        self._system_usage = ResourceUsage()
        self._historical_usage: List[ResourceUsage] = []
        self._max_history_size = 1000

        # 资源限制配置
        self._system_limits = ResourceQuota(
            cpu_limit=0.9,  # 系统最大CPU使用率
            memory_limit_mb=psutil.virtual_memory().total // (1024 * 1024) * 0.9,
            disk_quota_mb=psutil.disk_usage("/").total // (1024 * 1024) * 0.8,
            network_bandwidth_mbps=1000,
            gpu_memory_mb=0,
        )

        # 监控状态
        self._is_monitoring = False
        self._monitor_task = None
        self._executor = ThreadPoolExecutor(max_workers=2)

        # 网络使用基准
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()

    async def initialize(self, core_services: Dict[str, Any] = None) -> bool:
        """
        初始化资源治理器

        Args:
            core_services: 核心服务

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 启动资源监控
            await self.start_monitoring()

            logger.info("资源治理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"资源治理器初始化失败: {str(e)}")
            return False

    async def register_module(
        self, module_name: str, priority: ResourcePriority, quota: ResourceQuota = None
    ) -> bool:
        """
        注册模块资源需求

        Args:
            module_name: 模块名称
            priority: 资源优先级
            quota: 资源配额

        Returns:
            bool: 注册是否成功
        """
        try:
            if module_name in self._allocations:
                logger.warning(f"模块已注册: {module_name}")
                return True

            # 使用默认配额如果未提供
            if quota is None:
                quota = self._get_default_quota(priority)

            # 验证配额合理性
            if not await self._validate_quota(quota):
                logger.error(f"资源配额无效: {module_name}")
                return False

            # 创建资源分配记录
            allocation = ResourceAllocation(
                module_name=module_name,
                priority=priority,
                quota=quota,
                current_usage=ResourceUsage(),
                allocated_resources={},
            )

            self._allocations[module_name] = allocation

            logger.info(f"模块资源注册成功: {module_name} [{priority.value}]")
            return True

        except Exception as e:
            logger.error(f"模块资源注册失败 {module_name}: {str(e)}")
            return False

    async def allocate_resources(
        self, module_name: str, resource_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分配资源给模块

        Args:
            module_name: 模块名称
            resource_request: 资源请求

        Returns:
            Dict[str, Any]: 分配的资源
        """
        if module_name not in self._allocations:
            logger.error(f"模块未注册: {module_name}")
            return {}

        allocation = self._allocations[module_name]

        try:
            # 检查系统资源是否充足
            if not await self._check_system_capacity(resource_request):
                logger.warning(f"系统资源不足，无法满足请求: {module_name}")
                return {}

            # 根据优先级和配额分配资源
            allocated = await self._calculate_allocation(allocation, resource_request)

            # 更新分配记录
            allocation.allocated_resources.update(allocated)

            logger.debug(f"资源分配完成: {module_name} -> {allocated}")
            return allocated

        except Exception as e:
            logger.error(f"资源分配失败 {module_name}: {str(e)}")
            return {}

    async def release_resources(
        self, module_name: str, resources: Dict[str, Any] = None
    ) -> bool:
        """
        释放模块占用的资源

        Args:
            module_name: 模块名称
            resources: 要释放的特定资源，如果为None则释放所有

        Returns:
            bool: 释放是否成功
        """
        if module_name not in self._allocations:
            return True

        allocation = self._allocations[module_name]

        try:
            if resources is None:
                # 释放所有资源
                allocation.allocated_resources.clear()
            else:
                # 释放特定资源
                for resource_key in resources:
                    allocation.allocated_resources.pop(resource_key, None)

            logger.debug(f"资源释放完成: {module_name}")
            return True

        except Exception as e:
            logger.error(f"资源释放失败 {module_name}: {str(e)}")
            return False

    async def update_resource_usage(
        self, module_name: str, usage: ResourceUsage
    ) -> bool:
        """
        更新模块资源使用情况

        Args:
            module_name: 模块名称
            usage: 资源使用情况

        Returns:
            bool: 更新是否成功
        """
        if module_name not in self._allocations:
            return False

        allocation = self._allocations[module_name]
        allocation.current_usage = usage
        return True

    async def get_system_usage(self) -> ResourceUsage:
        """
        获取系统资源使用情况

        Returns:
            ResourceUsage: 系统资源使用情况
        """
        return self._system_usage

    async def get_module_usage(self, module_name: str) -> Optional[ResourceUsage]:
        """
        获取模块资源使用情况

        Args:
            module_name: 模块名称

        Returns:
            Optional[ResourceUsage]: 模块资源使用情况
        """
        if module_name not in self._allocations:
            return None
        return self._allocations[module_name].current_usage

    async def get_resource_report(self) -> Dict[str, Any]:
        """
        获取资源使用报告

        Returns:
            Dict[str, Any]: 资源报告
        """
        report = {
            "timestamp": time.time(),
            "system_usage": {
                "cpu_percent": self._system_usage.cpu_percent,
                "memory_used_mb": self._system_usage.memory_used_mb,
                "memory_percent": self._system_usage.memory_percent,
                "disk_used_mb": self._system_usage.disk_used_mb,
                "disk_percent": self._system_usage.disk_percent,
                "network_usage_mb": self._system_usage.network_sent_mb
                + self._system_usage.network_recv_mb,
            },
            "system_limits": {
                "cpu_limit": self._system_limits.cpu_limit,
                "memory_limit_mb": self._system_limits.memory_limit_mb,
                "disk_quota_mb": self._system_limits.disk_quota_mb,
                "network_bandwidth_mbps": self._system_limits.network_bandwidth_mbps,
            },
            "module_allocations": {},
            "health_status": await self._calculate_health_status(),
        }

        # 添加模块分配信息
        for module_name, allocation in self._allocations.items():
            report["module_allocations"][module_name] = {
                "priority": allocation.priority.value,
                "quota": {
                    "cpu_limit": allocation.quota.cpu_limit,
                    "memory_limit_mb": allocation.quota.memory_limit_mb,
                    "disk_quota_mb": allocation.quota.disk_quota_mb,
                },
                "current_usage": {
                    "cpu_percent": allocation.current_usage.cpu_percent,
                    "memory_used_mb": allocation.current_usage.memory_used_mb,
                    "disk_used_mb": allocation.current_usage.disk_used_mb,
                },
                "allocated_resources": allocation.allocated_resources,
            }

        return report

    async def optimize_resources(self) -> Dict[str, Any]:
        """
        执行资源优化

        Returns:
            Dict[str, Any]: 优化结果
        """
        optimization_result = {
            "timestamp": time.time(),
            "actions_taken": [],
            "resource_savings": {},
            "recommendations": [],
        }

        try:
            # 检查内存使用优化
            memory_actions = await self._optimize_memory_usage()
            optimization_result["actions_taken"].extend(memory_actions)

            # 检查CPU使用优化
            cpu_actions = await self._optimize_cpu_usage()
            optimization_result["actions_taken"].extend(cpu_actions)

            # 生成优化建议
            recommendations = await self._generate_optimization_recommendations()
            optimization_result["recommendations"] = recommendations

            # 计算资源节省
            optimization_result["resource_savings"] = (
                await self._calculate_resource_savings()
            )

            logger.info("资源优化完成")
            return optimization_result

        except Exception as e:
            logger.error(f"资源优化失败: {str(e)}")
            optimization_result["error"] = str(e)
            return optimization_result

    async def start_monitoring(self):
        """启动资源监控"""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("资源监控已启动")

    async def stop_monitoring(self):
        """停止资源监控"""
        self._is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("资源监控已停止")

    async def _monitoring_loop(self):
        """资源监控循环"""
        while self._is_monitoring:
            try:
                # 收集系统资源使用情况
                await self._collect_system_usage()

                # 检查资源限制
                await self._enforce_resource_limits()

                # 保存历史数据
                await self._save_historical_data()

                await asyncio.sleep(self.update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控错误: {str(e)}")
                await asyncio.sleep(self.update_interval)

    async def _collect_system_usage(self):
        """收集系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent

            # 磁盘使用
            disk = psutil.disk_usage("/")
            disk_used_mb = disk.used / (1024 * 1024)
            disk_percent = disk.percent

            # 网络使用
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            time_diff = current_time - self._last_net_time

            if time_diff > 0:
                net_sent_mb = (
                    current_net_io.bytes_sent - self._last_net_io.bytes_sent
                ) / (1024 * 1024)
                net_recv_mb = (
                    current_net_io.bytes_recv - self._last_net_io.bytes_recv
                ) / (1024 * 1024)
            else:
                net_sent_mb = 0
                net_recv_mb = 0

            # 更新基准值
            self._last_net_io = current_net_io
            self._last_net_time = current_time

            # 更新系统使用情况
            self._system_usage = ResourceUsage(
                cpu_percent=cpu_percent,
                memory_used_mb=memory_used_mb,
                memory_percent=memory_percent,
                disk_used_mb=disk_used_mb,
                disk_percent=disk_percent,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                timestamp=current_time,
            )

        except Exception as e:
            logger.error(f"系统资源收集失败: {str(e)}")

    async def _enforce_resource_limits(self):
        """强制执行资源限制"""
        try:
            # 检查系统级限制
            if self._system_usage.cpu_percent > self._system_limits.cpu_limit * 100:
                await self._handle_cpu_overload()

            if self._system_usage.memory_percent > 90:  # 内存使用超过90%
                await self._handle_memory_overload()

            # 检查模块级限制
            for module_name, allocation in self._allocations.items():
                usage = allocation.current_usage
                quota = allocation.quota

                # 检查CPU限制
                if usage.cpu_percent > quota.cpu_limit * 100:
                    await self._throttle_module(module_name, "cpu")

                # 检查内存限制
                if usage.memory_used_mb > quota.memory_limit_mb:
                    await self._throttle_module(module_name, "memory")

        except Exception as e:
            logger.error(f"资源限制执行失败: {str(e)}")

    async def _handle_cpu_overload(self):
        """处理CPU过载"""
        logger.warning("系统CPU使用率过高，执行优化措施")

        # 降低低优先级任务的CPU分配
        for module_name, allocation in self._allocations.items():
            if allocation.priority in [ResourcePriority.LOW, ResourcePriority.IDLE]:
                await self._adjust_module_cpu_limit(module_name, 0.5)  # 降低50%

    async def _handle_memory_overload(self):
        """处理内存过载"""
        logger.warning("系统内存使用率过高，执行优化措施")

        # 建议清理内存或终止低优先级任务
        recommendations = await self._generate_memory_optimization_recommendations()
        for recommendation in recommendations:
            logger.info(f"内存优化建议: {recommendation}")

    async def _throttle_module(self, module_name: str, resource_type: str):
        """限制模块资源使用"""
        logger.warning(f"模块 {module_name} {resource_type} 使用超出限制，执行限制措施")

        # 这里可以实现具体的限制逻辑
        # 例如：降低CPU优先级、限制内存分配等

    async def _adjust_module_cpu_limit(self, module_name: str, factor: float):
        """调整模块CPU限制"""
        if module_name in self._allocations:
            allocation = self._allocations[module_name]
            new_limit = allocation.quota.cpu_limit * factor
            allocation.quota.cpu_limit = max(new_limit, 0.1)  # 最低10%

    async def _get_default_quota(self, priority: ResourcePriority) -> ResourceQuota:
        """获取默认资源配额"""
        base_quota = ResourceQuota()

        if priority == ResourcePriority.CRITICAL:
            return base_quota
        elif priority == ResourcePriority.HIGH:
            return ResourceQuota(
                cpu_limit=0.8,
                memory_limit_mb=512,
                disk_quota_mb=5120,
                network_bandwidth_mbps=50,
            )
        elif priority == ResourcePriority.MEDIUM:
            return ResourceQuota(
                cpu_limit=0.5,
                memory_limit_mb=256,
                disk_quota_mb=2048,
                network_bandwidth_mbps=20,
            )
        elif priority == ResourcePriority.LOW:
            return ResourceQuota(
                cpu_limit=0.3,
                memory_limit_mb=128,
                disk_quota_mb=1024,
                network_bandwidth_mbps=10,
            )
        else:  # IDLE
            return ResourceQuota(
                cpu_limit=0.1,
                memory_limit_mb=64,
                disk_quota_mb=512,
                network_bandwidth_mbps=5,
            )

    async def _validate_quota(self, quota: ResourceQuota) -> bool:
        """验证资源配额合理性"""
        if quota.cpu_limit <= 0 or quota.cpu_limit > 1.0:
            return False

        if quota.memory_limit_mb <= 0:
            return False

        if quota.disk_quota_mb <= 0:
            return False

        if quota.network_bandwidth_mbps <= 0:
            return False

        return True

    async def _check_system_capacity(self, resource_request: Dict[str, Any]) -> bool:
        """检查系统容量"""
        # 简单的容量检查
        # 在实际实现中，这里需要更复杂的逻辑

        current_usage = self._system_usage

        # 检查CPU容量
        if (
            current_usage.cpu_percent + resource_request.get("cpu_percent", 0)
        ) > self._system_limits.cpu_limit * 100:
            return False

        # 检查内存容量
        requested_memory = resource_request.get("memory_mb", 0)
        available_memory = (
            self._system_limits.memory_limit_mb - current_usage.memory_used_mb
        )
        if requested_memory > available_memory * 0.8:  # 保留20%缓冲
            return False

        return True

    async def _calculate_allocation(
        self, allocation: ResourceAllocation, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算资源分配"""
        allocated = {}
        priority_factor = self._get_priority_factor(allocation.priority)

        # CPU分配
        if "cpu_cores" in request:
            max_cores = min(request["cpu_cores"], allocation.quota.cpu_limit)
            allocated["cpu_cores"] = max_cores * priority_factor

        # 内存分配
        if "memory_mb" in request:
            max_memory = min(request["memory_mb"], allocation.quota.memory_limit_mb)
            allocated["memory_mb"] = max_memory * priority_factor

        # 磁盘分配
        if "disk_mb" in request:
            max_disk = min(request["disk_mb"], allocation.quota.disk_quota_mb)
            allocated["disk_mb"] = max_disk

        # 网络分配
        if "network_mbps" in request:
            max_network = min(
                request["network_mbps"], allocation.quota.network_bandwidth_mbps
            )
            allocated["network_mbps"] = max_network * priority_factor

        return allocated

    def _get_priority_factor(self, priority: ResourcePriority) -> float:
        """获取优先级因子"""
        factors = {
            ResourcePriority.CRITICAL: 1.0,
            ResourcePriority.HIGH: 0.9,
            ResourcePriority.MEDIUM: 0.7,
            ResourcePriority.LOW: 0.5,
            ResourcePriority.IDLE: 0.3,
        }
        return factors.get(priority, 0.5)

    async def _save_historical_data(self):
        """保存历史数据"""
        self._historical_usage.append(self._system_usage)

        # 限制历史数据大小
        if len(self._historical_usage) > self._max_history_size:
            self._historical_usage.pop(0)

    async def _calculate_health_status(self) -> Dict[str, Any]:
        """计算健康状态"""
        health = {
            "status": "healthy",
            "score": 100,
            "warnings": [],
            "critical_issues": [],
        }

        # 检查CPU健康
        if self._system_usage.cpu_percent > 80:
            health["warnings"].append("CPU使用率较高")
            health["score"] -= 10

        if self._system_usage.cpu_percent > 95:
            health["critical_issues"].append("CPU使用率严重过高")
            health["score"] -= 30

        # 检查内存健康
        if self._system_usage.memory_percent > 85:
            health["warnings"].append("内存使用率较高")
            health["score"] -= 10

        if self._system_usage.memory_percent > 95:
            health["critical_issues"].append("内存使用率严重过高")
            health["score"] -= 30

        # 检查磁盘健康
        if self._system_usage.disk_percent > 90:
            health["warnings"].append("磁盘空间不足")
            health["score"] -= 10

        # 更新总体状态
        if health["score"] < 70:
            health["status"] = "unhealthy"
        elif health["score"] < 90:
            health["status"] = "degraded"

        return health

    async def _optimize_memory_usage(self) -> List[str]:
        """优化内存使用"""
        actions = []

        # 检查低优先级模块的内存使用
        for module_name, allocation in self._allocations.items():
            if (
                allocation.priority in [ResourcePriority.LOW, ResourcePriority.IDLE]
                and allocation.current_usage.memory_used_mb
                > allocation.quota.memory_limit_mb * 0.8
            ):

                # 建议清理内存
                actions.append(f"建议模块 {module_name} 清理内存")

        return actions

    async def _optimize_cpu_usage(self) -> List[str]:
        """优化CPU使用"""
        actions = []

        # 检查高CPU使用的模块
        for module_name, allocation in self._allocations.items():
            if allocation.current_usage.cpu_percent > 50:  # CPU使用超过50%
                if allocation.priority in [ResourcePriority.LOW, ResourcePriority.IDLE]:
                    # 限制低优先级模块的CPU使用
                    actions.append(f"限制模块 {module_name} 的CPU使用")

        return actions

    async def _generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于历史数据的建议
        if len(self._historical_usage) > 10:
            avg_cpu = (
                sum(usage.cpu_percent for usage in self._historical_usage[-10:]) / 10
            )
            if avg_cpu > 70:
                recommendations.append("考虑优化高CPU使用模块或增加计算资源")

        # 内存使用建议
        if self._system_usage.memory_percent > 80:
            recommendations.append("考虑优化内存使用或增加内存资源")

        # 磁盘使用建议
        if self._system_usage.disk_percent > 85:
            recommendations.append("考虑清理磁盘空间或增加存储容量")

        return recommendations

    async def _generate_memory_optimization_recommendations(self) -> List[str]:
        """生成内存优化建议"""
        recommendations = []

        # 识别内存使用大户
        memory_hogs = []
        for module_name, allocation in self._allocations.items():
            if allocation.current_usage.memory_used_mb > 100:  # 使用超过100MB
                memory_hogs.append(
                    (module_name, allocation.current_usage.memory_used_mb)
                )

        # 按内存使用排序
        memory_hogs.sort(key=lambda x: x[1], reverse=True)

        for module_name, memory_used in memory_hogs[:3]:  # 前3个
            recommendations.append(
                f"模块 {module_name} 使用了 {memory_used:.1f}MB 内存，建议优化"
            )

        return recommendations

    async def _calculate_resource_savings(self) -> Dict[str, float]:
        """计算资源节省"""
        # 这里可以实现资源节省的计算逻辑
        # 目前返回示例数据
        return {
            "cpu_saving_percent": 5.0,
            "memory_saving_mb": 50.0,
            "disk_saving_mb": 100.0,
        }

    async def cleanup(self):
        """清理资源"""
        await self.stop_monitoring()

        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

        self._allocations.clear()
        self._historical_usage.clear()

        logger.info("资源治理器清理完成")
