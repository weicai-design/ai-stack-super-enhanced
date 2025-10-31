"""
AI Stack Super Enhanced - Core Engine Package
核心引擎模块初始化文件

功能：
- 定义核心引擎包导出接口
- 初始化核心服务注册表
- 提供模块版本信息

版本: 1.0.0
创建日期: 2024
"""

import logging
from typing import Any, Dict, Optional

__version__ = "1.0.0"
__author__ = "AI Stack Development Team"

# 核心服务导出
__all__ = [
    "SmartOrchestrator",
    "AdaptiveEventBus",
    "ServiceDiscovery",
    "DependencyResolver",
    "PluginManager",
    "ResourceGovernor",
    "get_core_services",
    "initialize_core_engine",
]

# 模块级日志配置
logger = logging.getLogger(__name__)

# 全局核心服务注册表
_core_services_registry = {}


class CoreEngineError(Exception):
    """核心引擎基础异常类"""

    pass


class ServiceRegistrationError(CoreEngineError):
    """服务注册异常"""

    pass


class ServiceDiscoveryError(CoreEngineError):
    """服务发现异常"""

    pass


def get_core_services() -> Dict[str, Any]:
    """
    获取核心服务注册表

    Returns:
        Dict[str, Any]: 核心服务字典
    """
    return _core_services_registry.copy()


def register_core_service(service_name: str, service_instance: Any) -> None:
    """
    注册核心服务

    Args:
        service_name: 服务名称
        service_instance: 服务实例

    Raises:
        ServiceRegistrationError: 服务注册失败时抛出
    """
    if service_name in _core_services_registry:
        raise ServiceRegistrationError(f"服务已注册: {service_name}")

    _core_services_registry[service_name] = service_instance
    logger.info(f"核心服务注册成功: {service_name}")


def get_service(service_name: str) -> Optional[Any]:
    """
    获取核心服务实例

    Args:
        service_name: 服务名称

    Returns:
        Optional[Any]: 服务实例，未找到时返回None
    """
    return _core_services_registry.get(service_name)


async def initialize_core_engine(config: Dict[str, Any] = None) -> bool:
    """
    初始化核心引擎

    Args:
        config: 引擎配置字典

    Returns:
        bool: 初始化是否成功
    """
    try:
        logger.info("开始初始化核心引擎...")

        # 验证基础配置
        if config is None:
            config = {}

        # 初始化基础服务
        from .adaptive_event_bus import AdaptiveEventBus
        from .service_discovery import ServiceDiscovery
        from .smart_orchestrator import SmartOrchestrator

        # 创建核心服务实例
        event_bus = AdaptiveEventBus()
        service_discovery = ServiceDiscovery()
        smart_orchestrator = SmartOrchestrator()

        # 注册核心服务
        register_core_service("event_bus", event_bus)
        register_core_service("service_discovery", service_discovery)
        register_core_service("smart_orchestrator", smart_orchestrator)

        # 初始化服务
        await event_bus.initialize(config.get("event_bus", {}))
        await service_discovery.initialize(config.get("service_discovery", {}))
        await smart_orchestrator.initialize(config.get("orchestrator", {}))

        logger.info("核心引擎初始化完成")
        return True

    except Exception as e:
        logger.error(f"核心引擎初始化失败: {str(e)}", exc_info=True)
        return False


def get_engine_version() -> str:
    """
    获取引擎版本信息

    Returns:
        str: 版本字符串
    """
    return f"AI Stack Core Engine v{__version__}"


from .adaptive_event_bus import AdaptiveEventBus
from .dependency_resolver import DependencyResolver
from .plugin_manager import PluginManager
from .resource_governor import ResourceGovernor
from .service_discovery import ServiceDiscovery

# 导入核心类
from .smart_orchestrator import SmartOrchestrator

logger.info(f"AI Stack Core Engine v{__version__} 加载完成")
