"""
服务发现引擎
Service Discovery - 动态服务注册与发现

功能：
- 服务自动注册与注销
- 健康检查与状态监控
- 负载均衡策略
- 服务路由与版本管理
- 故障检测与自动恢复

版本: 1.0.0
"""

import asyncio
import hashlib
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    OUT_OF_SERVICE = "out_of_service"


class LoadBalanceStrategy(Enum):
    """负载均衡策略枚举"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    CONSISTENT_HASH = "consistent_hash"


@dataclass
class ServiceInstance:
    """服务实例类"""

    id: str
    name: str
    version: str
    address: str
    port: int
    metadata: Dict[str, Any]
    status: ServiceStatus
    last_health_check: float
    health_check_url: Optional[str] = None
    weight: int = 100
    tags: List[str] = None


@dataclass
class ServiceDefinition:
    """服务定义类"""

    name: str
    version: str
    instances: List[ServiceInstance]
    load_balance_strategy: LoadBalanceStrategy
    health_check_interval: int = 30
    health_check_timeout: int = 5
    max_failures: int = 3


class HealthChecker:
    """健康检查器基类"""

    async def check(self, instance: ServiceInstance) -> bool:
        """执行健康检查"""
        raise NotImplementedError


class HttpHealthChecker(HealthChecker):
    """HTTP健康检查器"""

    async def check(self, instance: ServiceInstance) -> bool:
        """HTTP健康检查"""
        try:
            import aiohttp

            if not instance.health_check_url:
                return True

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    instance.health_check_url, timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.debug(f"HTTP健康检查失败 {instance.id}: {str(e)}")
            return False


class TcpHealthChecker(HealthChecker):
    """TCP健康检查器"""

    async def check(self, instance: ServiceInstance) -> bool:
        """TCP健康检查"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(instance.address, instance.port), timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            return True

        except Exception as e:
            logger.debug(f"TCP健康检查失败 {instance.id}: {str(e)}")
            return False


class ServiceDiscovery:
    """
    服务发现引擎主类
    """

    def __init__(self):
        self.services: Dict[str, ServiceDefinition] = {}
        self.health_checkers: Dict[str, HealthChecker] = {}
        self.instance_index: Dict[str, ServiceInstance] = {}
        self.load_balancers: Dict[str, Any] = {}
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.is_running: bool = False
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # 初始化健康检查器
        self.health_checkers["http"] = HttpHealthChecker()
        self.health_checkers["tcp"] = TcpHealthChecker()

    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        初始化服务发现引擎

        Args:
            config: 引擎配置
        """
        logger.info("初始化服务发现引擎...")

        self.is_running = True

        logger.info("服务发现引擎初始化完成")

    async def start(self) -> None:
        """启动服务发现引擎"""
        logger.info("启动服务发现引擎")
        self.is_running = True

        # 启动健康检查任务
        for service_name in self.services:
            self._start_health_checking(service_name)

    async def stop(self) -> None:
        """停止服务发现引擎"""
        logger.info("停止服务发现引擎")
        self.is_running = False

        # 停止所有健康检查任务
        for task in self.health_check_tasks.values():
            task.cancel()

        # 等待任务完成
        for task in self.health_check_tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        total_instances = len(self.instance_index)
        healthy_instances = sum(
            1
            for instance in self.instance_index.values()
            if instance.status == ServiceStatus.HEALTHY
        )

        health_score = (
            (healthy_instances / total_instances * 100) if total_instances > 0 else 100
        )

        return {
            "status": "healthy" if health_score >= 80 else "degraded",
            "health_score": health_score,
            "total_services": len(self.services),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "timestamp": time.time(),
        }

    def register_service(
        self,
        name: str,
        version: str = "1.0.0",
        load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
        health_check_interval: int = 30,
        health_check_timeout: int = 5,
        max_failures: int = 3,
    ) -> bool:
        """
        注册服务定义

        Args:
            name: 服务名称
            version: 服务版本
            load_balance_strategy: 负载均衡策略
            health_check_interval: 健康检查间隔
            health_check_timeout: 健康检查超时
            max_failures: 最大失败次数

        Returns:
            bool: 注册是否成功
        """
        try:
            service_key = self._get_service_key(name, version)

            if service_key in self.services:
                logger.warning(f"服务已注册: {name} v{version}")
                return False

            service_def = ServiceDefinition(
                name=name,
                version=version,
                instances=[],
                load_balance_strategy=load_balance_strategy,
                health_check_interval=health_check_interval,
                health_check_timeout=health_check_timeout,
                max_failures=max_failures,
            )

            self.services[service_key] = service_def
            self._create_load_balancer(service_key, load_balance_strategy)

            # 启动健康检查
            self._start_health_checking(service_key)

            logger.info(f"服务注册成功: {name} v{version}")
            return True

        except Exception as e:
            logger.error(f"服务注册失败 {name}: {str(e)}")
            return False

    def register_instance(
        self,
        name: str,
        version: str,
        address: str,
        port: int,
        metadata: Dict[str, Any] = None,
        health_check_url: str = None,
        weight: int = 100,
        tags: List[str] = None,
    ) -> str:
        """
        注册服务实例

        Args:
            name: 服务名称
            version: 服务版本
            address: 实例地址
            port: 实例端口
            metadata: 实例元数据
            health_check_url: 健康检查URL
            weight: 实例权重
            tags: 实例标签

        Returns:
            str: 实例ID
        """
        try:
            service_key = self._get_service_key(name, version)

            if service_key not in self.services:
                logger.error(f"服务未注册: {name} v{version}")
                return None

            instance_id = str(uuid.uuid4())
            instance = ServiceInstance(
                id=instance_id,
                name=name,
                version=version,
                address=address,
                port=port,
                metadata=metadata or {},
                status=ServiceStatus.STARTING,
                last_health_check=time.time(),
                health_check_url=health_check_url,
                weight=weight,
                tags=tags or [],
            )

            # 添加到服务定义
            self.services[service_key].instances.append(instance)
            self.instance_index[instance_id] = instance

            # 触发实例注册事件
            self._trigger_event("instance_registered", instance)

            logger.info(f"服务实例注册成功: {name} v{version} at {address}:{port}")
            return instance_id

        except Exception as e:
            logger.error(f"服务实例注册失败 {name}: {str(e)}")
            return None

    def deregister_instance(self, instance_id: str) -> bool:
        """
        注销服务实例

        Args:
            instance_id: 实例ID

        Returns:
            bool: 注销是否成功
        """
        if instance_id not in self.instance_index:
            logger.warning(f"实例未找到: {instance_id}")
            return False

        instance = self.instance_index[instance_id]
        service_key = self._get_service_key(instance.name, instance.version)

        if service_key in self.services:
            service_def = self.services[service_key]
            service_def.instances = [
                inst for inst in service_def.instances if inst.id != instance_id
            ]

            # 清理空服务
            if not service_def.instances:
                del self.services[service_key]
                if service_key in self.health_check_tasks:
                    self.health_check_tasks[service_key].cancel()
                    del self.health_check_tasks[service_key]

        # 从索引中移除
        del self.instance_index[instance_id]

        # 触发实例注销事件
        self._trigger_event("instance_deregistered", instance)

        logger.info(f"服务实例注销成功: {instance.name} {instance_id}")
        return True

    def get_instance(self, instance_id: str) -> Optional[ServiceInstance]:
        """
        获取服务实例

        Args:
            instance_id: 实例ID

        Returns:
            Optional[ServiceInstance]: 服务实例
        """
        return self.instance_index.get(instance_id)

    def get_instances(
        self, name: str, version: str = None, healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """
        获取服务实例列表

        Args:
            name: 服务名称
            version: 服务版本，None表示所有版本
            healthy_only: 是否只返回健康实例

        Returns:
            List[ServiceInstance]: 服务实例列表
        """
        instances = []

        for service_key, service_def in self.services.items():
            if service_def.name == name and (
                version is None or service_def.version == version
            ):
                for instance in service_def.instances:
                    if not healthy_only or instance.status == ServiceStatus.HEALTHY:
                        instances.append(instance)

        return instances

    def select_instance(
        self, name: str, version: str = None, context: Dict[str, Any] = None
    ) -> Optional[ServiceInstance]:
        """
        选择服务实例（负载均衡）

        Args:
            name: 服务名称
            version: 服务版本
            context: 选择上下文

        Returns:
            Optional[ServiceInstance]: 选择的实例
        """
        instances = self.get_instances(name, version, healthy_only=True)

        if not instances:
            return None

        service_key = self._get_service_key(name, version or instances[0].version)

        if service_key not in self.load_balancers:
            return instances[0]

        load_balancer = self.load_balancers[service_key]
        return load_balancer.select(instances, context)

    def update_instance_status(self, instance_id: str, status: ServiceStatus) -> bool:
        """
        更新实例状态

        Args:
            instance_id: 实例ID
            status: 新状态

        Returns:
            bool: 更新是否成功
        """
        if instance_id not in self.instance_index:
            return False

        instance = self.instance_index[instance_id]
        old_status = instance.status
        instance.status = status

        # 触发状态变更事件
        if old_status != status:
            self._trigger_event(
                "instance_status_changed",
                instance,
                {"old_status": old_status, "new_status": status},
            )

        logger.debug(
            f"实例状态更新: {instance_id} {old_status.value} -> {status.value}"
        )
        return True

    def add_event_listener(self, event_type: str, callback: Callable) -> None:
        """
        添加事件监听器

        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        self.event_callbacks[event_type].append(callback)
        logger.debug(f"事件监听器添加: {event_type}")

    def remove_event_listener(self, event_type: str, callback: Callable) -> bool:
        """
        移除事件监听器

        Args:
            event_type: 事件类型
            callback: 回调函数

        Returns:
            bool: 移除是否成功
        """
        if (
            event_type in self.event_callbacks
            and callback in self.event_callbacks[event_type]
        ):
            self.event_callbacks[event_type].remove(callback)
            logger.debug(f"事件监听器移除: {event_type}")
            return True

        return False

    def _get_service_key(self, name: str, version: str) -> str:
        """
        获取服务键

        Args:
            name: 服务名称
            version: 服务版本

        Returns:
            str: 服务键
        """
        return f"{name}::{version}"

    def _create_load_balancer(
        self, service_key: str, strategy: LoadBalanceStrategy
    ) -> None:
        """
        创建负载均衡器

        Args:
            service_key: 服务键
            strategy: 负载均衡策略
        """
        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            self.load_balancers[service_key] = RoundRobinLoadBalancer()
        elif strategy == LoadBalanceStrategy.RANDOM:
            self.load_balancers[service_key] = RandomLoadBalancer()
        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            self.load_balancers[service_key] = LeastConnectionsLoadBalancer()
        elif strategy == LoadBalanceStrategy.WEIGHTED:
            self.load_balancers[service_key] = WeightedRoundRobinLoadBalancer()
        elif strategy == LoadBalanceStrategy.CONSISTENT_HASH:
            self.load_balancers[service_key] = ConsistentHashLoadBalancer()

    def _start_health_checking(self, service_key: str) -> None:
        """
        启动健康检查

        Args:
            service_key: 服务键
        """
        if service_key in self.health_check_tasks:
            return

        async def health_check_loop():
            service_def = self.services[service_key]

            while self.is_running and service_key in self.services:
                try:
                    await self._perform_health_checks(service_def)
                    await asyncio.sleep(service_def.health_check_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"健康检查循环异常 {service_key}: {str(e)}")
                    await asyncio.sleep(10)

        self.health_check_tasks[service_key] = asyncio.create_task(health_check_loop())

    async def _perform_health_checks(self, service_def: ServiceDefinition) -> None:
        """
        执行健康检查

        Args:
            service_def: 服务定义
        """
        tasks = []

        for instance in service_def.instances:
            task = asyncio.create_task(
                self._check_instance_health(instance, service_def)
            )
            tasks.append(task)

        # 并行执行健康检查
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_instance_health(
        self, instance: ServiceInstance, service_def: ServiceDefinition
    ) -> None:
        """
        检查实例健康状态

        Args:
            instance: 服务实例
            service_def: 服务定义
        """
        try:
            # 选择健康检查器
            health_checker = None
            if instance.health_check_url and instance.health_check_url.startswith(
                "http"
            ):
                health_checker = self.health_checkers["http"]
            else:
                health_checker = self.health_checkers["tcp"]

            # 执行健康检查
            is_healthy = await asyncio.wait_for(
                health_checker.check(instance), timeout=service_def.health_check_timeout
            )

            instance.last_health_check = time.time()

            if is_healthy:
                if instance.status != ServiceStatus.HEALTHY:
                    self.update_instance_status(instance.id, ServiceStatus.HEALTHY)
            else:
                if instance.status == ServiceStatus.HEALTHY:
                    self.update_instance_status(instance.id, ServiceStatus.UNHEALTHY)
                # 这里可以添加失败计数和自动注销逻辑

        except Exception as e:
            logger.debug(f"健康检查执行失败 {instance.id}: {str(e)}")
            if instance.status == ServiceStatus.HEALTHY:
                self.update_instance_status(instance.id, ServiceStatus.UNHEALTHY)

    def _trigger_event(
        self, event_type: str, instance: ServiceInstance, data: Dict[str, Any] = None
    ) -> None:
        """
        触发事件

        Args:
            event_type: 事件类型
            instance: 服务实例
            data: 事件数据
        """
        if event_type not in self.event_callbacks:
            return

        event_data = {
            "event_type": event_type,
            "instance": instance,
            "timestamp": time.time(),
            "data": data or {},
        }

        for callback in self.event_callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event_data))
                else:
                    callback(event_data)
            except Exception as e:
                logger.error(f"事件回调执行失败: {str(e)}")


# 负载均衡器实现


class LoadBalancer:
    """负载均衡器基类"""

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        """选择实例"""
        raise NotImplementedError


class RoundRobinLoadBalancer(LoadBalancer):
    """轮询负载均衡器"""

    def __init__(self):
        self.current_index = 0

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        if not instances:
            return None

        instance = instances[self.current_index % len(instances)]
        self.current_index += 1
        return instance


class RandomLoadBalancer(LoadBalancer):
    """随机负载均衡器"""

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        if not instances:
            return None

        import random

        return random.choice(instances)


class LeastConnectionsLoadBalancer(LoadBalancer):
    """最少连接负载均衡器"""

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        if not instances:
            return None

        # 这里使用权重作为连接数的代理
        return min(instances, key=lambda x: x.weight)


class WeightedRoundRobinLoadBalancer(LoadBalancer):
    """加权轮询负载均衡器"""

    def __init__(self):
        self.current_weight = 0
        self.gcd_weight = 0
        self.max_weight = 0
        self.current_index = -1

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        if not instances:
            return None

        while True:
            self.current_index = (self.current_index + 1) % len(instances)
            if self.current_index == 0:
                self.current_weight = self.current_weight - self.gcd_weight
                if self.current_weight <= 0:
                    self.current_weight = self.max_weight
                    if self.current_weight == 0:
                        return None

            instance = instances[self.current_index]
            if instance.weight >= self.current_weight:
                return instance


class ConsistentHashLoadBalancer(LoadBalancer):
    """一致性哈希负载均衡器"""

    def __init__(self, virtual_nodes: int = 100):
        self.virtual_nodes = virtual_nodes
        self.hash_ring = {}

    def select(
        self, instances: List[ServiceInstance], context: Dict[str, Any] = None
    ) -> ServiceInstance:
        if not instances:
            return None

        # 构建哈希环
        self._build_hash_ring(instances)

        # 使用上下文或随机值作为键
        key = str(context.get("key", id(context))) if context else str(id(self))
        hash_key = self._hash(key)

        # 找到最近的节点
        sorted_keys = sorted(self.hash_ring.keys())
        for node_key in sorted_keys:
            if hash_key <= node_key:
                return self.hash_ring[node_key]

        # 回退到第一个节点
        return self.hash_ring[sorted_keys[0]]

    def _build_hash_ring(self, instances: List[ServiceInstance]) -> None:
        """构建哈希环"""
        self.hash_ring.clear()

        for instance in instances:
            for i in range(self.virtual_nodes):
                node_key = f"{instance.id}:{i}"
                hash_value = self._hash(node_key)
                self.hash_ring[hash_value] = instance

    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)


# 导出类
__all__ = [
    "ServiceDiscovery",
    "ServiceInstance",
    "ServiceStatus",
    "LoadBalanceStrategy",
    "HealthChecker",
    "HttpHealthChecker",
    "TcpHealthChecker",
]
