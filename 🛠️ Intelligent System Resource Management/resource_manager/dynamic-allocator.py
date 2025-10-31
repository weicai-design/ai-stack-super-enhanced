"""
动态资源分配器
对应需求: 8.1/8.5 - 动态调配电脑资源、自适应调整
对应开发规则: 资源管理优化、统一生命周期接口
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict

logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """资源分配策略枚举"""

    BALANCED = "balanced"  # 平衡分配
    PERFORMANCE = "performance"  # 性能优先
    EFFICIENCY = "efficiency"  # 效率优先
    CUSTOM = "custom"  # 自定义策略


class ModulePriority(Enum):
    """模块优先级枚举"""

    CRITICAL = 5  # 关键模块 (如核心引擎、RAG)
    HIGH = 4  # 高优先级 (如ERP、交易)
    MEDIUM = 3  # 中优先级 (如内容创作、趋势分析)
    LOW = 2  # 低优先级 (如后台任务)
    BACKGROUND = 1  # 后台任务


@dataclass
class ResourceAllocation:
    """资源分配配置"""

    module_name: str
    cpu_limit: float  # CPU限制 (0-1.0)
    memory_limit: float  # 内存限制 (GB)
    disk_quota: float  # 磁盘配额 (GB)
    network_priority: int  # 网络优先级 (1-10)
    dynamic_adjustment: bool  # 是否允许动态调整


@dataclass
class AllocationRequest:
    """资源分配请求"""

    module_name: str
    priority: ModulePriority
    requested_cpu: float
    requested_memory: float
    requested_disk: float
    justification: str  # 资源需求说明


class DynamicAllocator:
    """
    动态资源分配器
    实现系统资源的智能分配和动态调整
    """

    def __init__(self):
        self.core_services = {}
        self.current_allocations = {}  # 当前分配配置
        self.allocation_strategy = AllocationStrategy.BALANCED
        self.module_priorities = self._get_default_priorities()
        self.total_resources = {}
        self.available_resources = {}

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """
        初始化动态分配器
        对应开发规则: 统一生命周期接口
        """
        self.config = config or {}
        self.core_services = core_services or {}

        # 初始化系统资源信息
        await self._discover_system_resources()

        logger.info("动态资源分配器初始化完成")

    async def start(self):
        """启动动态分配器"""
        # 启动资源监控任务
        self.background_task = asyncio.create_task(
            self._background_allocation_adjustment()
        )
        logger.info("动态资源分配器已启动")

    async def stop(self):
        """停止动态分配器"""
        if hasattr(self, "background_task"):
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass
        logger.info("动态资源分配器已停止")

    async def get_health_status(self) -> Dict:
        """获取健康状态"""
        allocation_stats = await self.get_allocation_statistics()

        return {
            "status": "healthy",
            "details": {
                "total_modules": len(self.current_allocations),
                "allocation_strategy": self.allocation_strategy.value,
                "resource_utilization": allocation_stats,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "allocation_requests_processed": getattr(self, "requests_processed", 0),
                "dynamic_adjustments_made": getattr(self, "adjustments_made", 0),
            },
        }

    async def request_resources(self, request: AllocationRequest) -> ResourceAllocation:
        """
        请求资源分配
        对应需求: 8.1 - 动态调配资源
        """
        # 验证请求的合理性
        if not await self._validate_request(request):
            raise ValueError(f"资源请求无效: {request.justification}")

        # 检查资源可用性
        if not await self._check_resource_availability(request):
            # 资源不足，尝试重新分配
            await self._reallocate_resources(request)

        # 创建分配配置
        allocation = await self._create_allocation(request)
        self.current_allocations[request.module_name] = allocation

        # 更新可用资源
        await self._update_available_resources()

        # 记录统计
        self.requests_processed = getattr(self, "requests_processed", 0) + 1

        logger.info(
            f"已为模块 {request.module_name} 分配资源: "
            f"CPU={allocation.cpu_limit:.2f}, 内存={allocation.memory_limit}GB"
        )

        return allocation

    async def release_resources(self, module_name: str):
        """释放模块资源"""
        if module_name in self.current_allocations:
            allocation = self.current_allocations.pop(module_name)

            # 更新可用资源
            await self._update_available_resources()

            logger.info(f"已释放模块 {module_name} 的资源")

    async def adjust_allocation(
        self, module_name: str, new_cpu: float = None, new_memory: float = None
    ) -> ResourceAllocation:
        """
        调整资源分配
        对应需求: 8.1 - 自适应调整
        """
        if module_name not in self.current_allocations:
            raise ValueError(f"模块未找到: {module_name}")

        allocation = self.current_allocations[module_name]

        # 更新分配配置
        if new_cpu is not None and 0 <= new_cpu <= 1.0:
            allocation.cpu_limit = new_cpu

        if new_memory is not None and new_memory >= 0:
            allocation.memory_limit = new_memory

        # 验证新配置
        if not await self._validate_allocation(allocation):
            raise ValueError("资源分配配置无效")

        self.current_allocations[module_name] = allocation
        await self._update_available_resources()

        self.adjustments_made = getattr(self, "adjustments_made", 0) + 1

        logger.info(f"已调整模块 {module_name} 的资源分配")
        return allocation

    async def set_allocation_strategy(self, strategy: AllocationStrategy):
        """设置分配策略"""
        self.allocation_strategy = strategy
        logger.info(f"已设置资源分配策略: {strategy.value}")

        # 策略变更时重新评估所有分配
        await self._reassess_allocations()

    async def get_allocation_statistics(self) -> Dict:
        """获取分配统计信息"""
        total_cpu_allocated = sum(
            alloc.cpu_limit for alloc in self.current_allocations.values()
        )
        total_memory_allocated = sum(
            alloc.memory_limit for alloc in self.current_allocations.values()
        )

        return {
            "total_allocated_cpu": total_cpu_allocated,
            "total_allocated_memory_gb": total_memory_allocated,
            "available_cpu": self.available_resources.get("cpu", 0),
            "available_memory_gb": self.available_resources.get("memory", 0),
            "module_count": len(self.current_allocations),
            "utilization_rate": await self._calculate_utilization_rate(),
        }

    async def _discover_system_resources(self):
        """发现系统资源"""
        import psutil

        # CPU资源
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)

        # 内存资源
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)

        # 磁盘资源
        disk = psutil.disk_usage("/")
        total_disk_gb = disk.total / (1024**3)

        self.total_resources = {
            "cpu_cores": cpu_cores,
            "cpu_threads": cpu_threads,
            "total_cpu": 1.0,  # 标准化为1.0
            "total_memory_gb": total_memory_gb,
            "total_disk_gb": total_disk_gb,
        }

        self.available_resources = self.total_resources.copy()

        logger.info(
            f"发现系统资源: {cpu_cores}核心, {total_memory_gb:.1f}GB内存, {total_disk_gb:.1f}GB磁盘"
        )

    async def _validate_request(self, request: AllocationRequest) -> bool:
        """验证资源请求"""
        # 检查基本参数
        if not request.module_name or request.requested_cpu <= 0:
            return False

        # 检查CPU请求是否合理
        if request.requested_cpu > 1.0:
            logger.warning(f"模块 {request.module_name} 请求的CPU资源超过100%")
            return False

        # 检查内存请求是否合理
        max_memory = self.total_resources.get("total_memory_gb", 32) * 0.8  # 最大80%
        if request.requested_memory > max_memory:
            logger.warning(f"模块 {request.module_name} 请求的内存超过系统限制")
            return False

        return True

    async def _check_resource_availability(self, request: AllocationRequest) -> bool:
        """检查资源可用性"""
        available_cpu = self.available_resources.get("total_cpu", 1.0)
        available_memory = self.available_resources.get("total_memory_gb", 0)

        return (
            request.requested_cpu <= available_cpu
            and request.requested_memory <= available_memory
        )

    async def _create_allocation(
        self, request: AllocationRequest
    ) -> ResourceAllocation:
        """创建资源分配配置"""
        # 根据策略调整分配
        adjusted_cpu, adjusted_memory = await self._adjust_allocation_by_strategy(
            request
        )

        return ResourceAllocation(
            module_name=request.module_name,
            cpu_limit=adjusted_cpu,
            memory_limit=adjusted_memory,
            disk_quota=request.requested_disk,
            network_priority=request.priority.value,
            dynamic_adjustment=True,
        )

    async def _adjust_allocation_by_strategy(self, request: AllocationRequest) -> tuple:
        """根据策略调整分配"""
        base_cpu = request.requested_cpu
        base_memory = request.requested_memory

        if self.allocation_strategy == AllocationStrategy.PERFORMANCE:
            # 性能优先：适当增加分配
            cpu = min(base_cpu * 1.2, 1.0)
            memory = base_memory * 1.2

        elif self.allocation_strategy == AllocationStrategy.EFFICIENCY:
            # 效率优先：适当减少分配
            cpu = base_cpu * 0.8
            memory = base_memory * 0.8

        else:  # BALANCED 或 CUSTOM
            cpu = base_cpu
            memory = base_memory

        return cpu, memory

    async def _validate_allocation(self, allocation: ResourceAllocation) -> bool:
        """验证分配配置"""
        return (
            0 <= allocation.cpu_limit <= 1.0
            and allocation.memory_limit >= 0
            and allocation.disk_quota >= 0
        )

    async def _update_available_resources(self):
        """更新可用资源"""
        total_cpu_allocated = sum(
            alloc.cpu_limit for alloc in self.current_allocations.values()
        )
        total_memory_allocated = sum(
            alloc.memory_limit for alloc in self.current_allocations.values()
        )

        self.available_resources["total_cpu"] = max(0, 1.0 - total_cpu_allocated)
        self.available_resources["total_memory_gb"] = max(
            0, self.total_resources["total_memory_gb"] - total_memory_allocated
        )

    async def _reallocate_resources(self, high_priority_request: AllocationRequest):
        """
        重新分配资源以满足高优先级请求
        对应需求: 8.2 - 资源冲突处理
        """
        logger.warning(
            f"资源不足，正在为高优先级模块 {high_priority_request.module_name} 重新分配资源"
        )

        # 按优先级排序当前分配
        sorted_allocations = sorted(
            self.current_allocations.items(),
            key=lambda x: self._get_module_priority(x[0]),
        )

        # 尝试释放低优先级模块的资源
        for module_name, allocation in sorted_allocations:
            if (
                self._get_module_priority(module_name)
                < high_priority_request.priority.value
                and allocation.dynamic_adjustment
            ):

                # 减少该模块的资源分配
                reduced_cpu = allocation.cpu_limit * 0.5  # 减少50%
                reduced_memory = allocation.memory_limit * 0.5

                if reduced_cpu > 0.05 and reduced_memory > 0.1:  # 保持最小资源
                    await self.adjust_allocation(
                        module_name, reduced_cpu, reduced_memory
                    )
                    logger.info(f"已减少低优先级模块 {module_name} 的资源分配")

                    # 检查是否现在有足够资源
                    if await self._check_resource_availability(high_priority_request):
                        break

    async def _background_allocation_adjustment(self):
        """后台资源调整任务"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次

                # 检查系统负载并动态调整
                await self._adaptive_adjustment()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"后台资源调整异常: {e}")
                await asyncio.sleep(10)  # 异常时短暂等待

    async def _adaptive_adjustment(self):
        """自适应资源调整"""
        # 获取当前系统负载
        resource_monitor = self.core_services.get("resource_monitor")
        if not resource_monitor:
            return

        try:
            current_metrics = await resource_monitor.get_current_metrics()

            # 根据系统负载调整分配策略
            await self._adjust_strategy_by_load(current_metrics)

            # 调整具体模块分配
            await self._adjust_module_allocations(current_metrics)

        except Exception as e:
            logger.error(f"自适应调整异常: {e}")

    async def _adjust_strategy_by_load(self, current_metrics: Dict):
        """根据系统负载调整策略"""
        cpu_usage = (
            current_metrics.get("cpu", {}).usage_percent
            if current_metrics.get("cpu")
            else 0
        )
        memory_usage = (
            current_metrics.get("memory", {}).usage_percent
            if current_metrics.get("memory")
            else 0
        )

        high_usage = max(cpu_usage, memory_usage)

        if high_usage > 80:
            self.allocation_strategy = AllocationStrategy.EFFICIENCY
        elif high_usage < 40:
            self.allocation_strategy = AllocationStrategy.PERFORMANCE
        else:
            self.allocation_strategy = AllocationStrategy.BALANCED

    async def _adjust_module_allocations(self, current_metrics: Dict):
        """调整模块资源分配"""
        cpu_usage = (
            current_metrics.get("cpu", {}).usage_percent
            if current_metrics.get("cpu")
            else 0
        )

        for module_name, allocation in self.current_allocations.items():
            if allocation.dynamic_adjustment:
                # 根据系统负载微调分配
                adjustment_factor = await self._calculate_adjustment_factor(cpu_usage)
                new_cpu = allocation.cpu_limit * adjustment_factor
                new_memory = allocation.memory_limit * adjustment_factor

                # 应用调整（保持合理范围）
                new_cpu = max(0.05, min(1.0, new_cpu))
                new_memory = max(0.1, new_memory)

                if abs(new_cpu - allocation.cpu_limit) > 0.05:  # 变化超过5%才调整
                    await self.adjust_allocation(module_name, new_cpu, new_memory)

    async def _calculate_adjustment_factor(self, cpu_usage: float) -> float:
        """计算调整系数"""
        if cpu_usage > 80:
            return 0.9  # 高负载时减少分配
        elif cpu_usage < 30:
            return 1.1  # 低负载时增加分配
        else:
            return 1.0  # 正常负载时保持

    async def _calculate_utilization_rate(self) -> float:
        """计算资源利用率"""
        total_allocated_cpu = sum(
            alloc.cpu_limit for alloc in self.current_allocations.values()
        )
        return min(1.0, total_allocated_cpu)  # CPU利用率

    async def _reassess_allocations(self):
        """重新评估所有分配"""
        logger.info("正在根据新策略重新评估资源分配...")

        for module_name, allocation in self.current_allocations.items():
            if allocation.dynamic_adjustment:
                # 根据新策略重新计算分配
                request = AllocationRequest(
                    module_name=module_name,
                    priority=ModulePriority(allocation.network_priority),
                    requested_cpu=allocation.cpu_limit,
                    requested_memory=allocation.memory_limit,
                    requested_disk=allocation.disk_quota,
                    justification="策略调整重新分配",
                )

                new_allocation = await self._create_allocation(request)
                self.current_allocations[module_name] = new_allocation

        await self._update_available_resources()

    def _get_module_priority(self, module_name: str) -> int:
        """获取模块优先级"""
        return self.module_priorities.get(module_name, ModulePriority.MEDIUM).value

    def _get_default_priorities(self) -> Dict[str, ModulePriority]:
        """获取默认模块优先级"""
        return {
            "rag_engine": ModulePriority.CRITICAL,
            "system_manager": ModulePriority.CRITICAL,
            "event_bus": ModulePriority.CRITICAL,
            "erp_engine": ModulePriority.HIGH,
            "stock_trading": ModulePriority.HIGH,
            "content_creation": ModulePriority.MEDIUM,
            "trend_analysis": ModulePriority.MEDIUM,
            "task_agent": ModulePriority.LOW,
            "background_tasks": ModulePriority.BACKGROUND,
        }
