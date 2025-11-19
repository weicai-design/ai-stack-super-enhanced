"""
Cursor插件系统
P0-016: 集成 Cursor（协议/插件/本地桥，授权与权限隔离）
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import importlib
import importlib.util
import inspect
import os
import logging

logger = logging.getLogger(__name__)


class PluginPermission(Enum):
    """插件权限"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EXECUTE_COMMAND = "execute_command"
    ACCESS_NETWORK = "access_network"
    ACCESS_SYSTEM = "access_system"
    FULL_ACCESS = "full_access"


class PluginStatus(Enum):
    """插件状态"""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """插件元数据"""
    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    permissions: List[PluginPermission] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    entry_point: str = "main"
    config_schema: Optional[Dict[str, Any]] = None


@dataclass
class Plugin:
    """插件"""
    metadata: PluginMetadata
    module: Any
    instance: Optional[Any] = None
    status: PluginStatus = PluginStatus.LOADED
    error: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)


class CursorPluginSystem:
    """
    Cursor插件系统
    
    功能：
    1. 插件加载和管理
    2. 权限控制
    3. 插件生命周期管理
    4. 插件间通信
    """
    
    def __init__(self, plugin_directory: Optional[str] = None):
        self.plugin_directory = plugin_directory or os.path.join(
            os.path.dirname(__file__),
            "..",
            "plugins"
        )
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_hooks: Dict[str, List[Callable]] = {}
        self.permission_manager = PermissionManager()
        
        # 确保插件目录存在
        os.makedirs(self.plugin_directory, exist_ok=True)
        
        logger.info(f"Cursor插件系统初始化完成，插件目录: {self.plugin_directory}")
    
    def load_plugin(self, plugin_path: str, config: Optional[Dict[str, Any]] = None) -> Plugin:
        """
        加载插件
        
        Args:
            plugin_path: 插件路径（文件或目录）
            config: 插件配置
            
        Returns:
            插件对象
        """
        try:
            # 加载插件模块
            if os.path.isdir(plugin_path):
                # 目录形式的插件
                plugin_name = os.path.basename(plugin_path)
                spec = importlib.util.spec_from_file_location(
                    plugin_name,
                    os.path.join(plugin_path, "__init__.py")
                )
            else:
                # 文件形式的插件
                plugin_name = os.path.basename(plugin_path).replace('.py', '')
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            
            if not spec or not spec.loader:
                raise ImportError(f"无法加载插件: {plugin_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取插件元数据
            metadata = self._extract_metadata(module, plugin_name)
            
            # 检查权限
            if not self.permission_manager.check_permissions(metadata.permissions):
                raise PermissionError(f"插件权限不足: {metadata.name}")
            
            # 创建插件实例
            plugin = Plugin(
                metadata=metadata,
                module=module,
                instance=getattr(module, metadata.entry_point, None),
                config=config or {},
                status=PluginStatus.LOADED
            )
            
            # 初始化插件
            if plugin.instance and hasattr(plugin.instance, 'initialize'):
                plugin.instance.initialize(config or {})
                plugin.status = PluginStatus.ACTIVE
            
            self.plugins[metadata.plugin_id] = plugin
            
            # 注册插件钩子
            self._register_plugin_hooks(plugin)
            
            logger.info(f"插件加载成功: {metadata.name} v{metadata.version}")
            return plugin
            
        except Exception as e:
            logger.error(f"加载插件失败: {plugin_path}, 错误: {e}", exc_info=True)
            raise
    
    def _extract_metadata(self, module: Any, plugin_name: str) -> PluginMetadata:
        """提取插件元数据"""
        # 从模块属性获取元数据
        metadata = PluginMetadata(
            plugin_id=getattr(module, 'PLUGIN_ID', plugin_name),
            name=getattr(module, 'PLUGIN_NAME', plugin_name),
            version=getattr(module, 'PLUGIN_VERSION', '1.0.0'),
            description=getattr(module, 'PLUGIN_DESCRIPTION', ''),
            author=getattr(module, 'PLUGIN_AUTHOR', 'Unknown'),
            permissions=[
                PluginPermission(p) for p in getattr(module, 'PLUGIN_PERMISSIONS', [])
            ],
            dependencies=getattr(module, 'PLUGIN_DEPENDENCIES', []),
            entry_point=getattr(module, 'PLUGIN_ENTRY_POINT', 'main'),
            config_schema=getattr(module, 'PLUGIN_CONFIG_SCHEMA', None)
        )
        return metadata
    
    def _register_plugin_hooks(self, plugin: Plugin):
        """注册插件钩子"""
        if not plugin.instance:
            return
        
        # 检查插件实现的钩子
        hook_methods = {
            'on_file_open': 'file_open',
            'on_file_save': 'file_save',
            'on_code_edit': 'code_edit',
            'on_error_detected': 'error_detected',
            'on_completion_request': 'completion_request'
        }
        
        for method_name, hook_name in hook_methods.items():
            if hasattr(plugin.instance, method_name):
                hook_func = getattr(plugin.instance, method_name)
                if hook_name not in self.plugin_hooks:
                    self.plugin_hooks[hook_name] = []
                self.plugin_hooks[hook_name].append(hook_func)
                logger.debug(f"已注册插件钩子: {plugin.metadata.name}.{method_name} -> {hook_name}")
    
    async def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        调用插件钩子
        
        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            所有钩子的返回值列表
        """
        results = []
        
        if hook_name not in self.plugin_hooks:
            return results
        
        for hook_func in self.plugin_hooks[hook_name]:
            try:
                if inspect.iscoroutinefunction(hook_func):
                    result = await hook_func(*args, **kwargs)
                else:
                    result = hook_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"调用插件钩子失败: {hook_name}, 错误: {e}", exc_info=True)
        
        return results
    
    def unload_plugin(self, plugin_id: str):
        """卸载插件"""
        if plugin_id not in self.plugins:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        plugin = self.plugins[plugin_id]
        
        # 清理钩子
        for hook_name, hooks in self.plugin_hooks.items():
            self.plugin_hooks[hook_name] = [
                h for h in hooks
                if not (hasattr(h, '__self__') and h.__self__ == plugin.instance)
            ]
        
        # 清理插件实例
        if plugin.instance and hasattr(plugin.instance, 'cleanup'):
            plugin.instance.cleanup()
        
        del self.plugins[plugin_id]
        logger.info(f"插件已卸载: {plugin.metadata.name}")
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return [
            {
                "plugin_id": p.metadata.plugin_id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "status": p.status.value,
                "permissions": [perm.value for perm in p.metadata.permissions]
            }
            for p in self.plugins.values()
        ]
    
    def enable_plugin(self, plugin_id: str):
        """启用插件"""
        if plugin_id not in self.plugins:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        plugin = self.plugins[plugin_id]
        if plugin.status == PluginStatus.DISABLED:
            plugin.status = PluginStatus.ACTIVE
            logger.info(f"插件已启用: {plugin.metadata.name}")
    
    def disable_plugin(self, plugin_id: str):
        """禁用插件"""
        if plugin_id not in self.plugins:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        plugin = self.plugins[plugin_id]
        plugin.status = PluginStatus.DISABLED
        logger.info(f"插件已禁用: {plugin.metadata.name}")


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.granted_permissions: List[PluginPermission] = []
        self.permission_policy: Dict[PluginPermission, bool] = {
            PluginPermission.READ_FILE: True,
            PluginPermission.WRITE_FILE: False,  # 默认不允许写文件
            PluginPermission.EXECUTE_COMMAND: False,  # 默认不允许执行命令
            PluginPermission.ACCESS_NETWORK: False,  # 默认不允许访问网络
            PluginPermission.ACCESS_SYSTEM: False,  # 默认不允许访问系统
            PluginPermission.FULL_ACCESS: False  # 默认不允许完全访问
        }
    
    def check_permissions(self, required_permissions: List[PluginPermission]) -> bool:
        """检查权限"""
        for perm in required_permissions:
            if perm == PluginPermission.FULL_ACCESS:
                # 完全访问需要特殊检查
                return self.permission_policy.get(PluginPermission.FULL_ACCESS, False)
            
            if not self.permission_policy.get(perm, False):
                return False
        
        return True
    
    def grant_permission(self, permission: PluginPermission):
        """授予权限"""
        self.permission_policy[permission] = True
        if permission not in self.granted_permissions:
            self.granted_permissions.append(permission)
        logger.info(f"已授予权限: {permission.value}")
    
    def revoke_permission(self, permission: PluginPermission):
        """撤销权限"""
        self.permission_policy[permission] = False
        if permission in self.granted_permissions:
            self.granted_permissions.remove(permission)
        logger.info(f"已撤销权限: {permission.value}")
    
    def get_permission_status(self) -> Dict[str, bool]:
        """获取权限状态"""
        return {
            perm.value: self.permission_policy.get(perm, False)
            for perm in PluginPermission
        }

