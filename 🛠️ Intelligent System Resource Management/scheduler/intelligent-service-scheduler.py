"""
智能服务调度器
负责服务的智能编排、资源感知调度、优先级管理和冲突解决
对应需求: 8.1/8.2/8.3/8.5 - 动态资源调配、冲突解决、启动顺序、自我进化
"""

import asyncio
import heapq
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from . import (
    DependencyType,
    ServiceInfo,
    ServiceSchedulerError,
    ServiceStartupError,
    ServiceStatus,
    logger,
)


@dataclass
class ScheduledService:
    """调度服务实例"""

    info: ServiceInfo
    status: ServiceStatus
    instance: Any
    startup_time: Optional[float] = None
    health_check_time: Optional[float] = None
    restart_attempts: int = 0
    last_error: Optional[str] = None
    resource_usage: Dict[str, float] = None


@dataclass
class SchedulingPriority:
    """调度优先级"""

    value: int  # 0-100, 越高优先级越高
    reason: str
    factors: Dict[str, float]  # 影响因子的权重


class IntelligentServiceScheduler:
    """
    智能服务调度器
    实现基于资源感知、依赖分析和优先级的多维度调度
    """

    def __init__(self, resource_manager=None, health_monitor=None):
        self.resource_manager = resource_manager
        self.health_monitor = health_monitor
        self.services: Dict[str, ScheduledService] = {}
        self.service_graph: Dict[str, Set[str]] = defaultdict(set)  # 依赖图
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)  # 反向依赖
        self.startup_queue = deque()
        self.priority_queue = []
        self.scheduling_lock = asyncio.Lock()
        self.is_running = False
        self.scheduler_id = f"scheduler-{uuid.uuid4().hex[:8]}"

        # 调度策略配置
        self.scheduling_strategies = {
            "resource_aware": self._resource_aware_scheduling,
            "dependency_first": self._dependency_first_scheduling,
            "priority_based": self._priority_based_scheduling,
            "hybrid": self._hybrid_scheduling,
        }

        # 自适应参数
        self.adaptive_params = {
            "max_concurrent_startups": 3,
            "resource_threshold": 0.8,  # 资源使用率阈值
            "health_check_frequency": 30,  # 健康检查频率(秒)
            "priority_recalc_interval": 60,  # 优先级重计算间隔(秒)
        }

        logger.info(f"智能服务调度器初始化完成: {self.scheduler_id}")

    async def initialize(self):
        """初始化调度器"""
        logger.info("开始初始化智能服务调度器")
        self.is_running = True

        # 启动后台任务
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._priority_recalculation_loop())
        asyncio.create_task(self._resource_optimization_loop())

        logger.info("智能服务调度器初始化完成")

    async def register_service(
        self, service_info: ServiceInfo, service_instance: Any
    ) -> bool:
        """
        注册服务到调度器

        Args:
            service_info: 服务信息
            service_instance: 服务实例

        Returns:
            bool: 注册是否成功
        """
        async with self.scheduling_lock:
            if service_info.name in self.services:
                logger.warning(f"服务已存在: {service_info.name}")
                return False

            # 创建调度服务实例
            scheduled_service = ScheduledService(
                info=service_info,
                status=ServiceStatus.STOPPED,
                instance=service_instance,
                resource_usage={},
            )

            self.services[service_info.name] = scheduled_service

            # 构建依赖图
            for dependency in service_info.dependencies:
                self.service_graph[service_info.name].add(dependency.service_name)
                self.reverse_dependencies[dependency.service_name].add(
                    service_info.name
                )

            logger.info(f"服务注册成功: {service_info.name}")
            return True

    async def start_service(self, service_name: str) -> bool:
        """
        启动单个服务（包含依赖解析）

        Args:
            service_name: 服务名称

        Returns:
            bool: 启动是否成功
        """
        try:
            async with self.scheduling_lock:
                if service_name not in self.services:
                    raise ServiceStartupError(f"服务未注册: {service_name}")

                # 解析依赖启动顺序
                startup_sequence = await self._resolve_dependency_sequence(service_name)
                logger.info(f"服务启动顺序解析完成: {startup_sequence}")

                # 按顺序启动服务
                for service_to_start in startup_sequence:
                    if not await self._start_single_service(service_to_start):
                        raise ServiceStartupError(
                            f"依赖服务启动失败: {service_to_start}"
                        )

                logger.info(f"服务启动完成: {service_name}")
                return True

        except Exception as e:
            logger.error(f"服务启动失败 {service_name}: {str(e)}")
            await self._handle_startup_failure(service_name, str(e))
            return False

    async def start_all_services(self) -> Dict[str, bool]:
        """
        启动所有服务（智能调度）

        Returns:
            Dict[str, bool]: 各服务启动结果
        """
        results = {}

        try:
            # 计算全局启动顺序
            global_sequence = await self._calculate_global_startup_sequence()
            logger.info(f"全局启动顺序计算完成: {global_sequence}")

            # 使用混合调度策略启动服务
            scheduled_sequence = await self.scheduling_strategies["hybrid"](
                global_sequence
            )

            # 并发启动（受资源限制）
            semaphore = asyncio.Semaphore(
                self.adaptive_params["max_concurrent_startups"]
            )

            async def start_with_limits(service_name):
                async with semaphore:
                    results[service_name] = await self._start_single_service(
                        service_name
                    )

            tasks = [start_with_limits(service) for service in scheduled_sequence]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("所有服务启动完成")
            return results

        except Exception as e:
            logger.error(f"全局服务启动失败: {str(e)}")
            # 记录失败的服务
            for service_name in self.services:
                if service_name not in results:
                    results[service_name] = False
            return results

    async def stop_service(self, service_name: str, force: bool = False) -> bool:
        """
        停止服务（考虑依赖关系）

        Args:
            service_name: 服务名称
            force: 是否强制停止

        Returns:
            bool: 停止是否成功
        """
        try:
            async with self.scheduling_lock:
                if service_name not in self.services:
                    logger.warning(f"服务未注册: {service_name}")
                    return False

                # 检查是否有依赖此服务的其他服务
                dependents = self.reverse_dependencies[service_name]
                if dependents and not force:
                    running_dependents = [
                        name
                        for name in dependents
                        if self.services[name].status == ServiceStatus.RUNNING
                    ]
                    if running_dependents:
                        raise ServiceSchedulerError(
                            f"服务 {service_name} 被以下运行中服务依赖: {running_dependents}"
                        )

                # 停止服务
                success = await self._stop_single_service(service_name)
                if success:
                    logger.info(f"服务停止成功: {service_name}")
                else:
                    logger.warning(f"服务停止失败: {service_name}")

                return success

        except Exception as e:
            logger.error(f"服务停止失败 {service_name}: {str(e)}")
            return False

    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        获取服务状态详情

        Args:
            service_name: 服务名称

        Returns:
            Dict[str, Any]: 服务状态信息
        """
        if service_name not in self.services:
            return {"error": "Service not found"}

        service = self.services[service_name]
        return {
            "name": service_name,
            "status": service.status.value,
            "startup_time": service.startup_time,
            "health_check_time": service.health_check_time,
            "restart_attempts": service.restart_attempts,
            "last_error": service.last_error,
            "resource_usage": service.resource_usage,
            "dependencies": [dep.service_name for dep in service.info.dependencies],
            "dependents": list(self.reverse_dependencies[service_name]),
        }

    async def get_scheduling_metrics(self) -> Dict[str, Any]:
        """
        获取调度器运行指标

        Returns:
            Dict[str, Any]: 调度指标
        """
        total_services = len(self.services)
        running_services = sum(
            1 for s in self.services.values() if s.status == ServiceStatus.RUNNING
        )

        return {
            "scheduler_id": self.scheduler_id,
            "total_services": total_services,
            "running_services": running_services,
            "stopped_services": total_services - running_services,
            "adaptive_params": self.adaptive_params,
            "avg_startup_time": await self._calculate_average_startup_time(),
            "success_rate": await self._calculate_success_rate(),
            "resource_efficiency": await self._calculate_resource_efficiency(),
        }

    # ========== 调度策略实现 ==========

    async def _resource_aware_scheduling(self, services: List[str]) -> List[str]:
        """资源感知调度"""
        if not self.resource_manager:
            return services

        try:
            resource_status = await self.resource_manager.get_detailed_status()
            cpu_usage = resource_status["cpu"]["usage_fraction"]
            memory_usage = resource_status["memory"]["usage_fraction"]

            # 资源使用率高的服务延后启动
            scored_services = []
            for service_name in services:
                service = self.services[service_name]
                resource_score = await self._estimate_service_resource_impact(service)

                # 调整分数：资源紧张时，资源需求高的服务分数低
                if cpu_usage > self.adaptive_params["resource_threshold"]:
                    resource_score *= 0.7
                if memory_usage > self.adaptive_params["resource_threshold"]:
                    resource_score *= 0.7

                scored_services.append((resource_score, service_name))

            # 按分数降序排列
            scored_services.sort(reverse=True)
            return [service for _, service in scored_services]

        except Exception as e:
            logger.warning(f"资源感知调度失败，使用默认顺序: {str(e)}")
            return services

    async def _dependency_first_scheduling(self, services: List[str]) -> List[str]:
        """依赖优先调度"""
        # 确保依赖服务先启动
        ordered_services = []
        remaining_services = set(services)

        while remaining_services:
            # 找到没有未启动依赖的服务
            ready_services = [
                s
                for s in remaining_services
                if all(
                    dep.service_name not in remaining_services
                    or dep.dependency_type == DependencyType.WEAK
                    for dep in self.services[s].info.dependencies
                )
            ]

            if not ready_services:
                # 循环依赖，选择依赖最少的服务
                ready_services = [
                    min(
                        remaining_services,
                        key=lambda s: len(
                            [
                                dep
                                for dep in self.services[s].info.dependencies
                                if dep.service_name in remaining_services
                                and dep.dependency_type != DependencyType.WEAK
                            ]
                        ),
                    )
                ]

            ordered_services.extend(ready_services)
            remaining_services -= set(ready_services)

        return ordered_services

    async def _priority_based_scheduling(self, services: List[str]) -> List[str]:
        """基于优先级调度"""
        prioritized_services = []

        for service_name in services:
            priority = await self._calculate_service_priority(service_name)
            heapq.heappush(prioritized_services, (-priority.value, service_name))

        # 按优先级降序返回
        return [
            heapq.heappop(prioritized_services)[1]
            for _ in range(len(prioritized_services))
        ]

    async def _hybrid_scheduling(self, services: List[str]) -> List[str]:
        """混合调度策略"""
        # 第一步：依赖优先
        dependency_ordered = await self._dependency_first_scheduling(services)

        # 第二步：资源感知调整
        resource_adjusted = await self._resource_aware_scheduling(dependency_ordered)

        # 第三步：优先级最终调整
        final_ordered = await self._priority_based_scheduling(resource_adjusted)

        return final_ordered

    # ========== 核心调度逻辑 ==========

    async def _resolve_dependency_sequence(self, target_service: str) -> List[str]:
        """解析服务依赖启动顺序"""
        visited = set()
        sequence = []

        async def dfs(service_name):
            if service_name in visited:
                return
            visited.add(service_name)

            # 先启动依赖服务
            for dependency in self.services[service_name].info.dependencies:
                if dependency.dependency_type != DependencyType.WEAK:
                    await dfs(dependency.service_name)

            sequence.append(service_name)

        await dfs(target_service)
        return sequence

    async def _calculate_global_startup_sequence(self) -> List[str]:
        """计算全局启动顺序"""
        all_services = list(self.services.keys())
        return await self._dependency_first_scheduling(all_services)

    async def _start_single_service(self, service_name: str) -> bool:
        """启动单个服务"""
        service = self.services[service_name]

        try:
            # 更新状态
            service.status = ServiceStatus.STARTING
            service.startup_time = time.time()

            # 检查资源可用性
            if not await self._check_resource_availability(service):
                raise ServiceStartupError("资源不足，无法启动服务")

            # 执行服务启动
            if hasattr(service.instance, "start"):
                if asyncio.iscoroutinefunction(service.instance.start):
                    await service.instance.start()
                else:
                    service.instance.start()

            # 验证服务健康状态
            if not await self._verify_service_health(service_name):
                raise ServiceStartupError("服务启动后健康检查失败")

            # 更新状态
            service.status = ServiceStatus.RUNNING
            service.restart_attempts = 0
            service.last_error = None

            logger.info(f"服务启动成功: {service_name}")
            return True

        except Exception as e:
            service.status = ServiceStatus.FAILED
            service.last_error = str(e)
            service.restart_attempts += 1

            logger.error(f"服务启动失败 {service_name}: {str(e)}")

            # 自动重启逻辑
            if (
                service.info.auto_restart
                and service.restart_attempts < service.info.max_restart_attempts
            ):
                logger.info(f"准备自动重启服务: {service_name}")
                asyncio.create_task(self._schedule_service_restart(service_name))

            return False

    async def _stop_single_service(self, service_name: str) -> bool:
        """停止单个服务"""
        service = self.services[service_name]

        try:
            service.status = ServiceStatus.STOPPING

            # 执行服务停止
            if hasattr(service.instance, "stop"):
                if asyncio.iscoroutinefunction(service.instance.stop):
                    await service.instance.stop()
                else:
                    service.instance.stop()

            service.status = ServiceStatus.STOPPED
            service.startup_time = None
            return True

        except Exception as e:
            service.status = ServiceStatus.FAILED
            service.last_error = str(e)
            logger.error(f"服务停止失败 {service_name}: {str(e)}")
            return False

    # ========== 资源管理 ==========

    async def _check_resource_availability(self, service: ScheduledService) -> bool:
        """检查资源可用性"""
        if not self.resource_manager:
            return True

        try:
            resource_status = await self.resource_manager.get_detailed_status()

            # 检查CPU和内存
            cpu_available = 1.0 - resource_status["cpu"]["usage_fraction"]
            memory_available = 1.0 - resource_status["memory"]["usage_fraction"]

            # 简单的资源检查逻辑
            min_required_cpu = 0.1  # 默认最小CPU要求
            min_required_memory = 0.1  # 默认最小内存要求

            return (
                cpu_available >= min_required_cpu
                and memory_available >= min_required_memory
            )

        except Exception as e:
            logger.warning(f"资源检查失败，允许启动: {str(e)}")
            return True

    async def _estimate_service_resource_impact(
        self, service: ScheduledService
    ) -> float:
        """估算服务资源影响"""
        # 基于服务类型和历史数据估算资源影响
        base_score = 1.0

        # 根据服务配置调整
        if service.info.resource_requirements:
            if "high_cpu" in service.info.resource_requirements:
                base_score *= 0.8
            if "high_memory" in service.info.resource_requirements:
                base_score *= 0.7
            if "low_resource" in service.info.resource_requirements:
                base_score *= 1.2

        return base_score

    # ========== 健康监控 ==========

    async def _health_monitoring_loop(self):
        """健康监控循环"""
        while self.is_running:
            try:
                for service_name, service in self.services.items():
                    if service.status == ServiceStatus.RUNNING:
                        is_healthy = await self._verify_service_health(service_name)
                        if not is_healthy:
                            service.status = ServiceStatus.DEGRADED
                            logger.warning(f"服务健康状态异常: {service_name}")

                            # 触发自动恢复
                            if service.info.auto_restart:
                                asyncio.create_task(
                                    self._schedule_service_restart(service_name)
                                )

                await asyncio.sleep(self.adaptive_params["health_check_frequency"])

            except Exception as e:
                logger.error(f"健康监控循环异常: {str(e)}")
                await asyncio.sleep(10)  # 异常时短暂等待

    async def _verify_service_health(self, service_name: str) -> bool:
        """验证服务健康状态"""
        service = self.services[service_name]

        try:
            # 使用健康检查器（如果可用）
            if self.health_monitor:
                health_status = await self.health_monitor.check_service_health(
                    service_name
                )
                return health_status.get("healthy", False)

            # 默认健康检查：检查服务实例是否有健康检查方法
            if hasattr(service.instance, "get_health_status"):
                if asyncio.iscoroutinefunction(service.instance.get_health_status):
                    status = await service.instance.get_health_status()
                else:
                    status = service.instance.get_health_status()
                return status.get("status") == "healthy"

            # 如果没有健康检查方法，认为服务健康
            return True

        except Exception as e:
            logger.warning(f"服务健康检查失败 {service_name}: {str(e)}")
            return False

    # ========== 优先级计算 ==========

    async def _priority_recalculation_loop(self):
        """优先级重计算循环"""
        while self.is_running:
            try:
                # 重新计算所有服务的优先级
                for service_name in self.services:
                    priority = await self._calculate_service_priority(service_name)
                    # 这里可以更新服务的优先级缓存

                await asyncio.sleep(self.adaptive_params["priority_recalc_interval"])

            except Exception as e:
                logger.error(f"优先级重计算异常: {str(e)}")
                await asyncio.sleep(30)  # 异常时延长等待

    async def _calculate_service_priority(
        self, service_name: str
    ) -> SchedulingPriority:
        """计算服务优先级"""
        service = self.services[service_name]

        factors = {
            "dependency_criticality": await self._calculate_dependency_criticality(
                service_name
            ),
            "resource_efficiency": await self._calculate_resource_efficiency_score(
                service_name
            ),
            "business_importance": await self._calculate_business_importance(
                service_name
            ),
            "historical_reliability": await self._calculate_historical_reliability(
                service_name
            ),
        }

        # 加权计算优先级值
        weights = {
            "dependency_criticality": 0.3,
            "business_importance": 0.3,
            "resource_efficiency": 0.2,
            "historical_reliability": 0.2,
        }

        priority_value = sum(factors[key] * weights[key] for key in factors)
        priority_value = max(0, min(100, priority_value * 100))  # 归一化到0-100

        return SchedulingPriority(
            value=int(priority_value), reason="综合优先级计算", factors=factors
        )

    async def _calculate_dependency_criticality(self, service_name: str) -> float:
        """计算依赖关键性"""
        dependents = self.reverse_dependencies[service_name]
        critical_dependents = sum(
            1
            for dep in dependents
            if any(
                d.dependency_type == DependencyType.REQUIRED
                for d in self.services[dep].info.dependencies
                if d.service_name == service_name
            )
        )
        return min(1.0, critical_dependents / 10.0)  # 归一化

    async def _calculate_resource_efficiency_score(self, service_name: str) -> float:
        """计算资源效率分数"""
        # 基于历史资源使用数据计算效率
        service = self.services[service_name]
        if service.resource_usage:
            # 简单的效率计算：资源使用越稳定，分数越高
            cpu_variance = service.resource_usage.get("cpu_variance", 0.5)
            memory_variance = service.resource_usage.get("memory_variance", 0.5)
            efficiency = 1.0 - (cpu_variance + memory_variance) / 2.0
            return max(0.1, efficiency)
        return 0.5  # 默认值

    async def _calculate_business_importance(self, service_name: str) -> float:
        """计算业务重要性"""
        # 基于服务类型和配置判断业务重要性
        service = self.services[service_name]

        importance_map = {
            "rag_engine": 0.9,
            "erp_core": 0.8,
            "openwebui": 0.7,
            "task_agent": 0.6,
            "content_engine": 0.5,
        }

        for key, value in importance_map.items():
            if key in service_name.lower():
                return value

        return 0.5  # 默认重要性

    async def _calculate_historical_reliability(self, service_name: str) -> float:
        """计算历史可靠性"""
        service = self.services[service_name]

        if service.restart_attempts == 0:
            return 1.0

        success_rate = 1.0 / (1.0 + service.restart_attempts)
        return max(0.1, success_rate)

    # ========== 工具方法 ==========

    async def _handle_startup_failure(self, service_name: str, error: str):
        """处理启动失败"""
        logger.error(f"服务启动失败处理: {service_name} - {error}")

        # 通知依赖服务
        dependents = self.reverse_dependencies[service_name]
        for dependent in dependents:
            if self.services[dependent].status == ServiceStatus.RUNNING:
                logger.warning(f"通知依赖服务 {dependent} 关于 {service_name} 的失败")
                # 这里可以触发依赖服务的降级或停止逻辑

    async def _schedule_service_restart(self, service_name: str):
        """调度服务重启"""
        service = self.services[service_name]

        # 计算重启延迟（指数退避）
        delay = min(300, 5 * (2**service.restart_attempts))  # 最大5分钟

        logger.info(f"调度服务重启: {service_name}，延迟 {delay} 秒")
        await asyncio.sleep(delay)

        if self.is_running and service.status != ServiceStatus.RUNNING:
            await self.start_service(service_name)

    async def _resource_optimization_loop(self):
        """资源优化循环"""
        while self.is_running:
            try:
                # 监控资源使用并调整调度参数
                if self.resource_manager:
                    resource_status = await self.resource_manager.get_detailed_status()

                    # 根据资源使用情况调整并发数
                    cpu_usage = resource_status["cpu"]["usage_fraction"]
                    if cpu_usage > 0.8:
                        self.adaptive_params["max_concurrent_startups"] = 1
                    elif cpu_usage > 0.6:
                        self.adaptive_params["max_concurrent_startups"] = 2
                    else:
                        self.adaptive_params["max_concurrent_startups"] = 3

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"资源优化循环异常: {str(e)}")
                await asyncio.sleep(30)

    async def _calculate_average_startup_time(self) -> float:
        """计算平均启动时间"""
        startup_times = []
        for service in self.services.values():
            if service.startup_time and service.status == ServiceStatus.RUNNING:
                # 这里需要实际的计算逻辑
                startup_times.append(10.0)  # 示例值

        return sum(startup_times) / len(startup_times) if startup_times else 0.0

    async def _calculate_success_rate(self) -> float:
        """计算成功率"""
        total_attempts = sum(s.restart_attempts + 1 for s in self.services.values())
        successful_starts = sum(
            1 for s in self.services.values() if s.status == ServiceStatus.RUNNING
        )

        return successful_starts / total_attempts if total_attempts > 0 else 1.0

    async def _calculate_resource_efficiency(self) -> float:
        """计算资源效率"""
        # 基于实际资源使用和业务吞吐量计算效率
        return 0.85  # 示例值

    async def shutdown(self):
        """关闭调度器"""
        logger.info("开始关闭智能服务调度器")
        self.is_running = False

        # 停止所有服务
        for service_name in list(self.services.keys()):
            await self.stop_service(service_name, force=True)

        logger.info("智能服务调度器关闭完成")


# 导出调度器类
__all__ = ["IntelligentServiceScheduler", "SchedulingPriority"]
