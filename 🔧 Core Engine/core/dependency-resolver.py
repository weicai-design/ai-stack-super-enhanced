"""
智能依赖解析器
功能：动态解析模块依赖关系，管理依赖注入，处理循环依赖检测
版本：1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set

import networkx as nx

logger = logging.getLogger(__name__)


class DependencyStatus(Enum):
    """依赖状态枚举"""

    PENDING = "pending"
    RESOLVED = "resolved"
    ERROR = "error"
    CIRCULAR = "circular"


@dataclass
class DependencyNode:
    """依赖节点"""

    name: str
    version: str
    dependencies: List[str]
    status: DependencyStatus
    instance: Any = None
    error_message: str = ""


class DependencyResolver:
    """
    智能依赖解析器
    负责模块依赖关系的解析、验证和注入
    """

    def __init__(self):
        self._dependency_graph = nx.DiGraph()
        self._modules: Dict[str, DependencyNode] = {}
        self._resolved_instances: Dict[str, Any] = {}
        self._resolution_order: List[str] = []

    async def register_module(
        self,
        module_name: str,
        version: str,
        dependencies: List[str],
        instance: Any = None,
    ) -> bool:
        """
        注册模块及其依赖关系

        Args:
            module_name: 模块名称
            version: 模块版本
            dependencies: 依赖模块列表
            instance: 模块实例（可选）

        Returns:
            bool: 注册是否成功
        """
        try:
            # 验证模块信息
            if not await self._validate_module_info(module_name, dependencies):
                return False

            # 创建依赖节点
            node = DependencyNode(
                name=module_name,
                version=version,
                dependencies=dependencies,
                status=DependencyStatus.PENDING,
                instance=instance,
            )

            # 添加到模块注册表
            self._modules[module_name] = node

            # 添加到依赖图
            self._dependency_graph.add_node(module_name)
            for dep in dependencies:
                self._dependency_graph.add_edge(module_name, dep)

            logger.info(f"模块注册成功: {module_name} v{version}, 依赖: {dependencies}")
            return True

        except Exception as e:
            logger.error(f"模块注册失败 {module_name}: {str(e)}")
            return False

    async def resolve_dependencies(self, target_module: str = None) -> Dict[str, Any]:
        """
        解析依赖关系并返回解析后的实例字典

        Args:
            target_module: 目标模块名称，如果为None则解析所有模块

        Returns:
            Dict[str, Any]: 模块名称到实例的映射
        """
        try:
            # 检测循环依赖
            if not await self._detect_circular_dependencies():
                logger.error("检测到循环依赖，解析中止")
                return {}

            # 计算解析顺序
            resolution_order = await self._calculate_resolution_order(target_module)
            if not resolution_order:
                logger.error("无法计算依赖解析顺序")
                return {}

            # 按顺序解析依赖
            resolved_instances = {}
            for module_name in resolution_order:
                if module_name in self._resolved_instances:
                    # 使用已解析的实例
                    resolved_instances[module_name] = self._resolved_instances[
                        module_name
                    ]
                    continue

                # 解析新模块
                instance = await self._resolve_single_module(
                    module_name, resolved_instances
                )
                if instance is None:
                    logger.error(f"模块解析失败: {module_name}")
                    return {}

                resolved_instances[module_name] = instance
                self._resolved_instances[module_name] = instance

            self._resolution_order = resolution_order
            logger.info(f"依赖解析完成，顺序: {resolution_order}")
            return resolved_instances

        except Exception as e:
            logger.error(f"依赖解析失败: {str(e)}")
            return {}

    async def inject_dependencies(
        self, target_instance: Any, dependencies: Dict[str, Any]
    ) -> bool:
        """
        向目标实例注入依赖

        Args:
            target_instance: 目标实例
            dependencies: 依赖字典

        Returns:
            bool: 注入是否成功
        """
        try:
            if not hasattr(target_instance, "initialize"):
                logger.warning(f"目标实例没有initialize方法，跳过依赖注入")
                return True

            # 准备核心服务
            core_services = await self._prepare_core_services(dependencies)

            # 调用initialize方法进行依赖注入
            if asyncio.iscoroutinefunction(target_instance.initialize):
                await target_instance.initialize(core_services=core_services)
            else:
                target_instance.initialize(core_services=core_services)

            logger.debug(f"依赖注入完成: {target_instance.__class__.__name__}")
            return True

        except Exception as e:
            logger.error(f"依赖注入失败 {target_instance.__class__.__name__}: {str(e)}")
            return False

    async def get_dependency_tree(self, module_name: str) -> Dict[str, Any]:
        """
        获取指定模块的依赖树

        Args:
            module_name: 模块名称

        Returns:
            Dict[str, Any]: 依赖树结构
        """
        if module_name not in self._modules:
            return {}

        def build_tree(current_module: str, visited: Set[str]) -> Dict[str, Any]:
            if current_module in visited:
                return {"name": current_module, "circular": True}

            visited.add(current_module)
            node = self._modules.get(
                current_module,
                DependencyNode(current_module, "", [], DependencyStatus.PENDING),
            )

            tree = {
                "name": current_module,
                "version": node.version,
                "status": node.status.value,
                "dependencies": [],
            }

            for dep in node.dependencies:
                tree["dependencies"].append(build_tree(dep, visited.copy()))

            return tree

        return build_tree(module_name, set())

    async def validate_dependency_health(self) -> Dict[str, Any]:
        """
        验证依赖健康状态

        Returns:
            Dict[str, Any]: 健康状态报告
        """
        report = {
            "total_modules": len(self._modules),
            "resolved_modules": len(self._resolved_instances),
            "circular_dependencies": False,
            "unresolved_dependencies": [],
            "health_score": 0.0,
            "details": {},
        }

        # 检查循环依赖
        report["circular_dependencies"] = not await self._detect_circular_dependencies()

        # 检查未解析的依赖
        for module_name, node in self._modules.items():
            unresolved_deps = []
            for dep in node.dependencies:
                if dep not in self._resolved_instances and dep in self._modules:
                    unresolved_deps.append(dep)

            if unresolved_deps:
                report["unresolved_dependencies"].append(
                    {"module": module_name, "unresolved": unresolved_deps}
                )

        # 计算健康分数
        total_deps = sum(len(node.dependencies) for node in self._modules.values())
        resolved_deps = sum(
            1
            for node in self._modules.values()
            for dep in node.dependencies
            if dep in self._resolved_instances
        )

        if total_deps > 0:
            report["health_score"] = resolved_deps / total_deps

        return report

    async def _validate_module_info(
        self, module_name: str, dependencies: List[str]
    ) -> bool:
        """验证模块信息"""
        if not module_name or not isinstance(module_name, str):
            logger.error("模块名称无效")
            return False

        if not isinstance(dependencies, list):
            logger.error("依赖关系必须是列表")
            return False

        # 检查自依赖
        if module_name in dependencies:
            logger.error(f"模块不能依赖自身: {module_name}")
            return False

        return True

    async def _detect_circular_dependencies(self) -> bool:
        """检测循环依赖"""
        try:
            cycles = list(nx.simple_cycles(self._dependency_graph))
            if cycles:
                logger.error(f"检测到循环依赖: {cycles}")
                # 标记循环依赖的模块
                for cycle in cycles:
                    for module_name in cycle:
                        if module_name in self._modules:
                            self._modules[module_name].status = (
                                DependencyStatus.CIRCULAR
                            )
                return False
            return True
        except Exception as e:
            logger.error(f"循环依赖检测失败: {str(e)}")
            return False

    async def _calculate_resolution_order(self, target_module: str = None) -> List[str]:
        """计算依赖解析顺序"""
        try:
            if target_module:
                # 计算目标模块的依赖顺序
                if target_module not in self._dependency_graph:
                    return []
                dependencies = list(
                    nx.descendants(self._dependency_graph, target_module)
                )
                dependencies.append(target_module)
                resolution_order = [
                    node
                    for node in nx.topological_sort(self._dependency_graph)
                    if node in dependencies
                ]
            else:
                # 计算所有模块的解析顺序
                resolution_order = list(nx.topological_sort(self._dependency_graph))

            return resolution_order

        except Exception as e:
            logger.error(f"解析顺序计算失败: {str(e)}")
            return []

    async def _resolve_single_module(
        self, module_name: str, available_instances: Dict[str, Any]
    ) -> Any:
        """解析单个模块"""
        if module_name not in self._modules:
            logger.error(f"模块未注册: {module_name}")
            return None

        node = self._modules[module_name]

        try:
            # 检查依赖是否满足
            missing_deps = [
                dep for dep in node.dependencies if dep not in available_instances
            ]
            if missing_deps:
                logger.error(f"模块 {module_name} 缺少依赖: {missing_deps}")
                node.status = DependencyStatus.ERROR
                node.error_message = f"缺少依赖: {missing_deps}"
                return None

            # 如果已有实例，直接使用
            if node.instance is not None:
                node.status = DependencyStatus.RESOLVED
                return node.instance

            # 创建新实例（这里需要模块注册表支持）
            # 在实际实现中，这里会调用ModuleRegistry创建实例
            logger.warning(f"模块 {module_name} 没有预注册实例，需要扩展实现")
            node.status = DependencyStatus.RESOLVED
            return None

        except Exception as e:
            logger.error(f"模块解析失败 {module_name}: {str(e)}")
            node.status = DependencyStatus.ERROR
            node.error_message = str(e)
            return None

    async def _prepare_core_services(
        self, dependencies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备核心服务字典"""
        core_services = {
            "resource_manager": dependencies.get("resource_manager"),
            "event_bus": dependencies.get("event_bus"),
            "health_monitor": dependencies.get("health_monitor"),
            "dependency_resolver": self,  # 注入自身
            "plugin_manager": dependencies.get("plugin_manager"),
        }

        # 添加其他模块依赖
        for name, instance in dependencies.items():
            if name not in core_services:
                core_services[name] = instance

        return core_services

    async def cleanup(self):
        """清理资源"""
        self._resolved_instances.clear()
        self._resolution_order.clear()

        for node in self._modules.values():
            node.status = DependencyStatus.PENDING
            node.error_message = ""

        logger.info("依赖解析器清理完成")
