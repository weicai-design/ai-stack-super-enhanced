"""
智能编排引擎
Smart Orchestrator - 核心编排引擎

功能：
- 系统服务智能编排与调度
- 模块依赖关系管理
- 服务生命周期协调
- 自适应负载均衡
- 故障转移与恢复

版本: 1.0.0
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    DEGRADED = "degraded"


class OrchestrationStrategy(Enum):
    """编排策略枚举"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    DEPENDENCY_ORDER = "dependency"  # 依赖顺序
    INTELLIGENT = "intelligent"  # 智能编排


@dataclass
class ServiceInfo:
    """服务信息类"""

    name: str
    version: str
    status: ServiceStatus
    dependencies: List[str]
    health_check: Callable[[], bool]
    startup_order: int = 0
    config: Dict[str, Any] = None
    last_health_check: float = 0
    error_count: int = 0


@dataclass
class OrchestrationPlan:
    """编排计划类"""

    plan_id: str
    services: List[str]
    strategy: OrchestrationStrategy
    dependencies: Dict[str, List[str]]
    expected_duration: float
    created_at: float


class SmartOrchestrator:
    """
    智能编排引擎主类
    """

    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.service_instances: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)
        self.reverse_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.health_check_interval: int = 30  # 健康检查间隔(秒)
        self.max_errors: int = 3  # 最大错误次数
        self.is_running: bool = False
        self.health_check_task: Optional[asyncio.Task] = None

    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        初始化编排引擎

        Args:
            config: 引擎配置
        """
        logger.info("初始化智能编排引擎...")

        if config:
            self.health_check_interval = config.get("health_check_interval", 30)
            self.max_errors = config.get("max_errors", 3)

        # 启动健康检查任务
        self.is_running = True
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())

        logger.info("智能编排引擎初始化完成")

    async def start(self) -> None:
        """启动编排引擎"""
        logger.info("启动智能编排引擎")
        self.is_running = True

    async def stop(self) -> None:
        """停止编排引擎"""
        logger.info("停止智能编排引擎")
        self.is_running = False

        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # 停止所有服务
        for service_name in self.services:
            await self._stop_service(service_name)

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        total_services = len(self.services)
        running_services = sum(
            1 for s in self.services.values() if s.status == ServiceStatus.RUNNING
        )
        error_services = sum(
            1 for s in self.services.values() if s.status == ServiceStatus.ERROR
        )

        health_score = (
            (running_services / total_services * 100) if total_services > 0 else 100
        )

        return {
            "status": "healthy" if health_score >= 80 else "degraded",
            "health_score": health_score,
            "total_services": total_services,
            "running_services": running_services,
            "error_services": error_services,
            "degraded_services": sum(
                1 for s in self.services.values() if s.status == ServiceStatus.DEGRADED
            ),
            "timestamp": time.time(),
        }

    def register_service(
        self,
        service_name: str,
        service_instance: Any,
        dependencies: List[str] = None,
        health_check: Callable[[], bool] = None,
        version: str = "1.0.0",
        config: Dict[str, Any] = None,
    ) -> bool:
        """
        注册服务

        Args:
            service_name: 服务名称
            service_instance: 服务实例
            dependencies: 依赖服务列表
            health_check: 健康检查函数
            version: 服务版本
            config: 服务配置

        Returns:
            bool: 注册是否成功
        """
        try:
            if service_name in self.services:
                logger.warning(f"服务已注册: {service_name}")
                return False

            # 创建服务信息
            service_info = ServiceInfo(
                name=service_name,
                version=version,
                status=ServiceStatus.STOPPED,
                dependencies=dependencies or [],
                health_check=health_check or (lambda: True),
                config=config or {},
            )

            # 注册服务
            self.services[service_name] = service_info
            self.service_instances[service_name] = service_instance

            # 更新依赖图
            for dep in service_info.dependencies:
                self.dependency_graph[service_name].append(dep)
                self.reverse_dependencies[dep].append(service_name)

            logger.info(f"服务注册成功: {service_name} v{version}")
            return True

        except Exception as e:
            logger.error(f"服务注册失败 {service_name}: {str(e)}")
            return False

    async def start_services(
        self,
        service_names: List[str] = None,
        strategy: OrchestrationStrategy = OrchestrationStrategy.INTELLIGENT,
    ) -> Dict[str, bool]:
        """
        启动服务

        Args:
            service_names: 要启动的服务列表，None表示所有服务
            strategy: 启动策略

        Returns:
            Dict[str, bool]: 服务启动结果字典
        """
        services_to_start = service_names or list(self.services.keys())
        results = {}

        logger.info(f"开始启动服务，策略: {strategy.value}")

        if strategy == OrchestrationStrategy.SEQUENTIAL:
            # 顺序启动
            for service_name in services_to_start:
                result = await self._start_service(service_name)
                results[service_name] = result

        elif strategy == OrchestrationStrategy.PARALLEL:
            # 并行启动
            tasks = []
            for service_name in services_to_start:
                task = asyncio.create_task(self._start_service(service_name))
                tasks.append((service_name, task))

            for service_name, task in tasks:
                results[service_name] = await task

        elif strategy in [
            OrchestrationStrategy.DEPENDENCY_ORDER,
            OrchestrationStrategy.INTELLIGENT,
        ]:
            # 依赖顺序或智能启动
            execution_order = self._calculate_execution_order(services_to_start)

            for service_name in execution_order:
                if service_name in services_to_start:
                    result = await self._start_service(service_name)
                    results[service_name] = result
                    # 添加智能延迟
                    if strategy == OrchestrationStrategy.INTELLIGENT:
                        await asyncio.sleep(0.1)

        logger.info(f"服务启动完成: {sum(results.values())}/{len(results)} 成功")
        return results

    async def stop_services(self, service_names: List[str] = None) -> Dict[str, bool]:
        """
        停止服务

        Args:
            service_names: 要停止的服务列表，None表示所有服务

        Returns:
            Dict[str, bool]: 服务停止结果字典
        """
        services_to_stop = service_names or list(self.services.keys())
        results = {}

        logger.info(f"开始停止 {len(services_to_stop)} 个服务")

        # 按依赖逆序停止
        stop_order = self._calculate_stop_order(services_to_stop)

        for service_name in stop_order:
            result = await self._stop_service(service_name)
            results[service_name] = result

        logger.info(f"服务停止完成: {sum(results.values())}/{len(results)} 成功")
        return results

    def _calculate_execution_order(self, service_names: List[str]) -> List[str]:
        """
        计算服务执行顺序（拓扑排序）

        Args:
            service_names: 服务名称列表

        Returns:
            List[str]: 执行顺序列表
        """
        visited = set()
        temp_visited = set()
        order = []

        def visit(service):
            if service in temp_visited:
                raise ValueError(f"检测到循环依赖: {service}")
            if service not in visited:
                temp_visited.add(service)

                # 先访问依赖
                for dep in self.dependency_graph.get(service, []):
                    if dep in service_names:
                        visit(dep)

                temp_visited.remove(service)
                visited.add(service)
                order.append(service)

        for service in service_names:
            if service not in visited:
                visit(service)

        return order

    def _calculate_stop_order(self, service_names: List[str]) -> List[str]:
        """
        计算服务停止顺序（依赖逆序）

        Args:
            service_names: 服务名称列表

        Returns:
            List[str]: 停止顺序列表
        """
        execution_order = self._calculate_execution_order(service_names)
        return list(reversed(execution_order))

    async def _start_service(self, service_name: str) -> bool:
        """
        启动单个服务

        Args:
            service_name: 服务名称

        Returns:
            bool: 启动是否成功
        """
        if service_name not in self.services:
            logger.error(f"服务未注册: {service_name}")
            return False

        service_info = self.services[service_name]
        service_instance = self.service_instances[service_name]

        try:
            # 检查依赖服务
            for dep_name in service_info.dependencies:
                if (
                    dep_name in self.services
                    and self.services[dep_name].status != ServiceStatus.RUNNING
                ):
                    logger.warning(f"服务 {service_name} 的依赖服务 {dep_name} 未运行")
                    return False

            # 更新服务状态
            service_info.status = ServiceStatus.STARTING

            # 执行启动
            if hasattr(service_instance, "start") and callable(service_instance.start):
                if asyncio.iscoroutinefunction(service_instance.start):
                    await service_instance.start()
                else:
                    service_instance.start()

            service_info.status = ServiceStatus.RUNNING
            service_info.error_count = 0
            logger.info(f"服务启动成功: {service_name}")
            return True

        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            service_info.error_count += 1
            logger.error(f"服务启动失败 {service_name}: {str(e)}")
            return False

    async def _stop_service(self, service_name: str) -> bool:
        """
        停止单个服务

        Args:
            service_name: 服务名称

        Returns:
            bool: 停止是否成功
        """
        if service_name not in self.services:
            return False

        service_info = self.services[service_name]
        service_instance = self.service_instances[service_name]

        try:
            # 更新服务状态
            service_info.status = ServiceStatus.STOPPING

            # 执行停止
            if hasattr(service_instance, "stop") and callable(service_instance.stop):
                if asyncio.iscoroutinefunction(service_instance.stop):
                    await service_instance.stop()
                else:
                    service_instance.stop()

            service_info.status = ServiceStatus.STOPPED
            logger.info(f"服务停止成功: {service_name}")
            return True

        except Exception as e:
            service_info.status = ServiceStatus.ERROR
            logger.error(f"服务停止失败 {service_name}: {str(e)}")
            return False

    async def _health_monitor_loop(self) -> None:
        """健康监控循环"""
        while self.is_running:
            try:
                current_time = time.time()

                for service_name, service_info in self.services.items():
                    # 检查健康状态
                    if (
                        current_time - service_info.last_health_check
                    ) >= self.health_check_interval:
                        try:
                            is_healthy = service_info.health_check()
                            service_info.last_health_check = current_time

                            if not is_healthy:
                                service_info.error_count += 1
                                if service_info.status == ServiceStatus.RUNNING:
                                    service_info.status = ServiceStatus.DEGRADED
                                    logger.warning(f"服务健康状态异常: {service_name}")

                                # 错误次数超过阈值，尝试恢复
                                if service_info.error_count >= self.max_errors:
                                    logger.warning(
                                        f"服务 {service_name} 错误次数超过阈值，尝试恢复"
                                    )
                                    await self._restart_service(service_name)
                            else:
                                if service_info.status == ServiceStatus.DEGRADED:
                                    service_info.status = ServiceStatus.RUNNING
                                    logger.info(f"服务恢复健康: {service_name}")
                                service_info.error_count = 0

                        except Exception as e:
                            logger.error(f"服务健康检查失败 {service_name}: {str(e)}")
                            service_info.error_count += 1

                await asyncio.sleep(5)  # 监控循环间隔

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康监控循环异常: {str(e)}")
                await asyncio.sleep(10)

    async def _restart_service(self, service_name: str) -> bool:
        """
        重启服务

        Args:
            service_name: 服务名称

        Returns:
            bool: 重启是否成功
        """
        logger.info(f"尝试重启服务: {service_name}")

        # 先停止
        stop_success = await self._stop_service(service_name)
        if not stop_success:
            return False

        # 等待一段时间
        await asyncio.sleep(1)

        # 再启动
        start_success = await self._start_service(service_name)

        if start_success:
            logger.info(f"服务重启成功: {service_name}")
            self.services[service_name].error_count = 0
        else:
            logger.error(f"服务重启失败: {service_name}")

        return start_success

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        获取服务状态详情

        Args:
            service_name: 服务名称

        Returns:
            Optional[Dict[str, Any]]: 服务状态信息
        """
        if service_name not in self.services:
            return None

        service_info = self.services[service_name]

        return {
            "name": service_info.name,
            "version": service_info.version,
            "status": service_info.status.value,
            "dependencies": service_info.dependencies,
            "error_count": service_info.error_count,
            "last_health_check": service_info.last_health_check,
            "config": service_info.config,
        }

    def get_dependency_graph(self) -> Dict[str, Any]:
        """
        获取依赖关系图

        Returns:
            Dict[str, Any]: 依赖关系信息
        """
        return {
            "dependency_graph": dict(self.dependency_graph),
            "reverse_dependencies": dict(self.reverse_dependencies),
            "services": list(self.services.keys()),
        }


# 导出类
__all__ = ["SmartOrchestrator", "ServiceStatus", "OrchestrationStrategy"]
