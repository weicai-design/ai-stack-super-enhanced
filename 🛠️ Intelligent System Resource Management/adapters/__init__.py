"""
智能系统资源管理 - 适配器模块
MacOS优化器与硬件智能监控适配器

功能概述：
- macOS系统性能优化与资源调优
- 跨平台硬件智能监控与适配
- 系统资源动态分配策略
- 电源管理与性能平衡

版本: 1.0.0
创建日期: 2024-12-19
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

__all__ = [
    "BaseSystemAdapter",
    "MacOSOptimizer",
    "HardwareIntelligence",
    "SystemAdapterFactory",
    "AdapterInitializationError",
    "HardwareMonitoringError",
]


class AdapterInitializationError(Exception):
    """适配器初始化异常"""

    pass


class HardwareMonitoringError(Exception):
    """硬件监控异常"""

    pass


class BaseSystemAdapter(ABC):
    """
    系统适配器基类
    所有系统适配器必须继承此类并实现接口方法
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化系统适配器

        Args:
            config: 适配器配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__module__)
        self._initialized = False
        self._performance_metrics = {}

    async def initialize(self, core_services: Dict[str, Any] = None) -> bool:
        """
        初始化适配器

        Args:
            core_services: 核心服务字典

        Returns:
            bool: 初始化是否成功
        """
        try:
            self.core_services = core_services or {}
            await self._setup_adapter()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} 初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} 初始化失败: {str(e)}")
            raise AdapterInitializationError(f"适配器初始化失败: {str(e)}") from e

    @abstractmethod
    async def _setup_adapter(self):
        """设置适配器具体实现"""
        pass

    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            Dict: 系统信息字典
        """
        pass

    @abstractmethod
    async def optimize_performance(
        self, optimization_level: str = "balanced"
    ) -> Dict[str, Any]:
        """
        优化系统性能

        Args:
            optimization_level: 优化级别 (balanced, performance, power_saving)

        Returns:
            Dict: 优化结果
        """
        pass

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取适配器健康状态

        Returns:
            Dict: 健康状态信息
        """
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
            "adapter_type": self.__class__.__name__,
            "performance_metrics": self._performance_metrics,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }

    async def cleanup(self):
        """清理资源"""
        self._initialized = False
        self.logger.info(f"{self.__class__.__name__} 资源清理完成")


class SystemAdapterFactory:
    """
    系统适配器工厂类
    负责创建和管理系统适配器实例
    """

    _adapters = {}

    @classmethod
    def register_adapter(cls, adapter_type: str, adapter_class):
        """
        注册适配器类

        Args:
            adapter_type: 适配器类型
            adapter_class: 适配器类
        """
        cls._adapters[adapter_type] = adapter_class
        logger.info(f"注册系统适配器: {adapter_type} -> {adapter_class.__name__}")

    @classmethod
    def create_adapter(
        cls, adapter_type: str, config: Dict[str, Any] = None
    ) -> BaseSystemAdapter:
        """
        创建适配器实例

        Args:
            adapter_type: 适配器类型
            config: 配置字典

        Returns:
            BaseSystemAdapter: 适配器实例

        Raises:
            AdapterInitializationError: 适配器创建失败
        """
        if adapter_type not in cls._adapters:
            raise AdapterInitializationError(f"未知的适配器类型: {adapter_type}")

        try:
            adapter_class = cls._adapters[adapter_type]
            instance = adapter_class(config)
            logger.info(f"创建适配器实例: {adapter_type}")
            return instance
        except Exception as e:
            logger.error(f"创建适配器失败 {adapter_type}: {str(e)}")
            raise AdapterInitializationError(f"适配器创建失败: {str(e)}") from e

    @classmethod
    def get_available_adapters(cls) -> List[str]:
        """
        获取可用的适配器类型

        Returns:
            List[str]: 适配器类型列表
        """
        return list(cls._adapters.keys())


# 自动注册适配器类
def _auto_register_adapters():
    """自动注册所有定义的适配器类"""
    try:
        from .hardware_intelligence import HardwareIntelligence
        from .macos_optimizer import MacOSOptimizer

        SystemAdapterFactory.register_adapter("macos_optimizer", MacOSOptimizer)
        SystemAdapterFactory.register_adapter(
            "hardware_intelligence", HardwareIntelligence
        )

        logger.info("系统适配器自动注册完成")
    except ImportError as e:
        logger.warning(f"适配器自动注册时部分模块导入失败: {str(e)}")


# 模块加载时自动执行注册
_auto_register_adapters()

logger.info("系统资源管理适配器模块初始化完成")
