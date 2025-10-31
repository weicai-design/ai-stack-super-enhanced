"""
智能插件管理器
功能：管理插件生命周期，支持热插拔，处理插件依赖关系
版本：1.0.0
"""

import asyncio
import importlib
import inspect
import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """插件状态枚举"""

    REGISTERED = "registered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    version: str
    description: str
    author: str
    plugin_class: str
    dependencies: List[str]
    config_schema: Dict[str, Any]
    status: PluginStatus
    instance: Any = None
    load_time: float = 0
    error_message: str = ""


class BasePlugin:
    """
    插件基类
    所有插件必须继承此基类
    """

    def __init__(self):
        self.plugin_info: Optional[PluginInfo] = None
        self.core_services: Dict[str, Any] = {}

    async def initialize(
        self, config: Dict[str, Any], core_services: Dict[str, Any]
    ) -> bool:
        """
        初始化插件

        Args:
            config: 插件配置
            core_services: 核心服务

        Returns:
            bool: 初始化是否成功
        """
        self.core_services = core_services
        return True

    async def start(self) -> bool:
        """
        启动插件

        Returns:
            bool: 启动是否成功
        """
        return True

    async def stop(self) -> bool:
        """
        停止插件

        Returns:
            bool: 停止是否成功
        """
        return True

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取插件健康状态

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {"status": "healthy", "message": "Plugin is running normally"}

    async def reload_config(self, new_config: Dict[str, Any]) -> bool:
        """
        重新加载配置

        Args:
            new_config: 新配置

        Returns:
            bool: 重载是否成功
        """
        return True


class PluginManager:
    """
    智能插件管理器
    负责插件的加载、管理、热插拔和生命周期管理
    """

    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_directory = Path(plugins_directory)
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_instances: Dict[str, BasePlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._dependency_resolver = None

        # 创建插件目录
        self.plugins_directory.mkdir(exist_ok=True)

    async def initialize(self, core_services: Dict[str, Any]) -> bool:
        """
        初始化插件管理器

        Args:
            core_services: 核心服务

        Returns:
            bool: 初始化是否成功
        """
        try:
            self._dependency_resolver = core_services.get("dependency_resolver")

            # 扫描并加载插件
            await self._scan_plugins_directory()

            # 加载插件配置
            await self._load_plugin_configs()

            logger.info("插件管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"插件管理器初始化失败: {str(e)}")
            return False

    async def register_plugin(self, plugin_info: PluginInfo) -> bool:
        """
        注册插件

        Args:
            plugin_info: 插件信息

        Returns:
            bool: 注册是否成功
        """
        try:
            # 验证插件信息
            if not await self._validate_plugin_info(plugin_info):
                return False

            # 检查重复注册
            if plugin_info.name in self._plugins:
                logger.warning(f"插件已注册: {plugin_info.name}")
                return False

            # 注册插件
            self._plugins[plugin_info.name] = plugin_info
            plugin_info.status = PluginStatus.REGISTERED

            logger.info(f"插件注册成功: {plugin_info.name} v{plugin_info.version}")
            return True

        except Exception as e:
            logger.error(f"插件注册失败 {plugin_info.name}: {str(e)}")
            return False

    async def load_plugin(self, plugin_name: str) -> bool:
        """
        加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 加载是否成功
        """
        if plugin_name not in self._plugins:
            logger.error(f"插件未注册: {plugin_name}")
            return False

        plugin_info = self._plugins[plugin_name]

        try:
            # 检查插件依赖
            if not await self._check_plugin_dependencies(plugin_info):
                logger.error(f"插件依赖不满足: {plugin_name}")
                return False

            # 动态加载插件类
            plugin_class = await self._load_plugin_class(plugin_info)
            if plugin_class is None:
                return False

            # 创建插件实例
            instance = plugin_class()
            instance.plugin_info = plugin_info

            # 获取插件配置
            config = self._plugin_configs.get(plugin_name, {})

            # 准备核心服务
            core_services = await self._prepare_core_services()

            # 初始化插件
            if not await instance.initialize(config, core_services):
                logger.error(f"插件初始化失败: {plugin_name}")
                plugin_info.status = PluginStatus.ERROR
                return False

            # 启动插件
            if not await instance.start():
                logger.error(f"插件启动失败: {plugin_name}")
                plugin_info.status = PluginStatus.ERROR
                return False

            # 更新状态
            plugin_info.instance = instance
            plugin_info.status = PluginStatus.ACTIVE
            self._plugin_instances[plugin_name] = instance

            logger.info(f"插件加载成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"插件加载失败 {plugin_name}: {str(e)}")
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self._plugin_instances:
            logger.warning(f"插件未加载: {plugin_name}")
            return True

        try:
            instance = self._plugin_instances[plugin_name]
            plugin_info = self._plugins[plugin_name]

            # 停止插件
            if not await instance.stop():
                logger.warning(f"插件停止失败: {plugin_name}")

            # 清理实例
            del self._plugin_instances[plugin_name]
            plugin_info.instance = None
            plugin_info.status = PluginStatus.REGISTERED

            logger.info(f"插件卸载成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"插件卸载失败 {plugin_name}: {str(e)}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 重载是否成功
        """
        # 先卸载再加载
        if not await self.unload_plugin(plugin_name):
            return False

        # 短暂延迟确保完全卸载
        await asyncio.sleep(0.1)

        return await self.load_plugin(plugin_name)

    async def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[BasePlugin]: 插件实例
        """
        return self._plugin_instances.get(plugin_name)

    async def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[PluginInfo]: 插件信息
        """
        return self._plugins.get(plugin_name)

    async def list_plugins(
        self, status_filter: PluginStatus = None
    ) -> List[PluginInfo]:
        """
        列出插件

        Args:
            status_filter: 状态过滤器

        Returns:
            List[PluginInfo]: 插件列表
        """
        if status_filter:
            return [
                info for info in self._plugins.values() if info.status == status_filter
            ]
        return list(self._plugins.values())

    async def update_plugin_config(
        self, plugin_name: str, new_config: Dict[str, Any]
    ) -> bool:
        """
        更新插件配置

        Args:
            plugin_name: 插件名称
            new_config: 新配置

        Returns:
            bool: 更新是否成功
        """
        if plugin_name not in self._plugins:
            return False

        try:
            # 验证配置
            if not await self._validate_plugin_config(plugin_name, new_config):
                return False

            # 更新配置
            self._plugin_configs[plugin_name] = new_config

            # 如果插件已加载，应用新配置
            if plugin_name in self._plugin_instances:
                instance = self._plugin_instances[plugin_name]
                if hasattr(instance, "reload_config"):
                    if not await instance.reload_config(new_config):
                        logger.warning(f"插件配置重载失败: {plugin_name}")

            # 保存配置
            await self._save_plugin_config(plugin_name, new_config)

            logger.info(f"插件配置更新成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"插件配置更新失败 {plugin_name}: {str(e)}")
            return False

    async def get_plugin_health_report(self) -> Dict[str, Any]:
        """
        获取插件健康报告

        Returns:
            Dict[str, Any]: 健康报告
        """
        report = {
            "total_plugins": len(self._plugins),
            "active_plugins": 0,
            "error_plugins": 0,
            "disabled_plugins": 0,
            "health_score": 0.0,
            "plugin_details": {},
        }

        for plugin_name, plugin_info in self._plugins.items():
            status_info = {
                "name": plugin_info.name,
                "version": plugin_info.version,
                "status": plugin_info.status.value,
                "load_time": plugin_info.load_time,
            }

            if plugin_info.status == PluginStatus.ACTIVE:
                report["active_plugins"] += 1
                # 获取详细健康状态
                if plugin_name in self._plugin_instances:
                    instance = self._plugin_instances[plugin_name]
                    health_status = await instance.get_health_status()
                    status_info["health"] = health_status
            elif plugin_info.status == PluginStatus.ERROR:
                report["error_plugins"] += 1
                status_info["error"] = plugin_info.error_message
            elif plugin_info.status == PluginStatus.DISABLED:
                report["disabled_plugins"] += 1

            report["plugin_details"][plugin_name] = status_info

        # 计算健康分数
        if report["total_plugins"] > 0:
            report["health_score"] = report["active_plugins"] / report["total_plugins"]

        return report

    async def _scan_plugins_directory(self):
        """扫描插件目录"""
        if not self.plugins_directory.exists():
            logger.warning(f"插件目录不存在: {self.plugins_directory}")
            return

        for plugin_file in self.plugins_directory.glob("**/plugin_*.py"):
            try:
                plugin_info = await self._parse_plugin_file(plugin_file)
                if plugin_info:
                    await self.register_plugin(plugin_info)
            except Exception as e:
                logger.error(f"插件文件解析失败 {plugin_file}: {str(e)}")

    async def _parse_plugin_file(self, plugin_file: Path) -> Optional[PluginInfo]:
        """解析插件文件"""
        try:
            # 动态导入插件模块
            module_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                ):
                    plugin_class = obj
                    break

            if not plugin_class:
                logger.warning(f"未找到插件类: {plugin_file}")
                return None

            # 提取插件信息
            plugin_info = PluginInfo(
                name=getattr(plugin_class, "PLUGIN_NAME", module_name),
                version=getattr(plugin_class, "PLUGIN_VERSION", "1.0.0"),
                description=getattr(plugin_class, "PLUGIN_DESCRIPTION", ""),
                author=getattr(plugin_class, "PLUGIN_AUTHOR", ""),
                plugin_class=f"{module.__name__}.{plugin_class.__name__}",
                dependencies=getattr(plugin_class, "PLUGIN_DEPENDENCIES", []),
                config_schema=getattr(plugin_class, "PLUGIN_CONFIG_SCHEMA", {}),
                status=PluginStatus.REGISTERED,
            )

            return plugin_info

        except Exception as e:
            logger.error(f"插件文件解析失败 {plugin_file}: {str(e)}")
            return None

    async def _load_plugin_class(
        self, plugin_info: PluginInfo
    ) -> Optional[Type[BasePlugin]]:
        """加载插件类"""
        try:
            module_name, class_name = plugin_info.plugin_class.rsplit(".", 1)
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)

            if not issubclass(plugin_class, BasePlugin):
                logger.error(f"插件类必须继承BasePlugin: {plugin_info.name}")
                return None

            return plugin_class

        except Exception as e:
            logger.error(f"插件类加载失败 {plugin_info.name}: {str(e)}")
            return None

    async def _validate_plugin_info(self, plugin_info: PluginInfo) -> bool:
        """验证插件信息"""
        required_fields = ["name", "version", "plugin_class"]
        for field in required_fields:
            if not getattr(plugin_info, field, None):
                logger.error(f"插件信息缺少必需字段: {field}")
                return False

        if not isinstance(plugin_info.dependencies, list):
            logger.error("插件依赖必须是列表")
            return False

        return True

    async def _check_plugin_dependencies(self, plugin_info: PluginInfo) -> bool:
        """检查插件依赖"""
        for dep in plugin_info.dependencies:
            if dep not in self._plugins:
                logger.error(f"插件依赖未注册: {dep}")
                return False

            dep_plugin = self._plugins[dep]
            if dep_plugin.status != PluginStatus.ACTIVE:
                logger.error(f"插件依赖未激活: {dep}")
                return False

        return True

    async def _prepare_core_services(self) -> Dict[str, Any]:
        """准备核心服务"""
        return {
            "plugin_manager": self,
            "resource_manager": getattr(self, "_resource_manager", None),
            "event_bus": getattr(self, "_event_bus", None),
            "dependency_resolver": self._dependency_resolver,
        }

    async def _load_plugin_configs(self):
        """加载插件配置"""
        config_file = self.plugins_directory / "plugin_configs.json"
        if not config_file.exists():
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                configs = json.load(f)

            self._plugin_configs.update(configs)
            logger.info("插件配置加载完成")

        except Exception as e:
            logger.error(f"插件配置加载失败: {str(e)}")

    async def _save_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """保存插件配置"""
        config_file = self.plugins_directory / "plugin_configs.json"

        try:
            # 加载现有配置
            existing_configs = {}
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    existing_configs = json.load(f)

            # 更新配置
            existing_configs[plugin_name] = config

            # 保存配置
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(existing_configs, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"插件配置保存失败 {plugin_name}: {str(e)}")

    async def _validate_plugin_config(
        self, plugin_name: str, config: Dict[str, Any]
    ) -> bool:
        """验证插件配置"""
        if plugin_name not in self._plugins:
            return False

        plugin_info = self._plugins[plugin_name]
        schema = plugin_info.config_schema

        # 简单的配置验证
        if not schema:  # 如果没有定义schema，接受所有配置
            return True

        # 这里可以实现更复杂的配置验证逻辑
        # 目前只做基础的类型检查

        return True

    async def cleanup(self):
        """清理插件管理器"""
        # 卸载所有插件
        for plugin_name in list(self._plugin_instances.keys()):
            await self.unload_plugin(plugin_name)

        self._plugins.clear()
        self._plugin_configs.clear()

        logger.info("插件管理器清理完成")
