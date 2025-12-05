#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件化安全策略管理器
支持动态加载、卸载和配置安全策略插件
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Callable
from uuid import uuid4

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    """插件类型"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    RISK_ASSESSMENT = "risk_assessment"
    THREAT_DETECTION = "threat_detection"


class PluginStatus(str, Enum):
    """插件状态"""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class SecurityPlugin:
    """安全插件"""
    plugin_id: str
    name: str
    description: str
    plugin_type: PluginType
    version: str
    author: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    status: PluginStatus = PluginStatus.LOADED
    load_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error_message: Optional[str] = None
    instance: Optional[Any] = None


class SecurityPluginBase(ABC):
    """安全插件基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugin_id = str(uuid4())
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件逻辑"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据"""
        return {
            "plugin_id": self.plugin_id,
            "class_name": self.__class__.__name__,
            "config": self.config,
        }


class PluginSecurityManager:
    """
    插件化安全策略管理器
    
    支持：
    1. 动态加载和卸载安全插件
    2. 插件配置管理
    3. 插件执行流水线
    4. 插件状态监控
    """
    
    def __init__(self, plugins_directory: Optional[str] = None):
        self.plugins: Dict[str, SecurityPlugin] = {}
        self.plugins_directory = plugins_directory or "plugins/security"
        self.execution_pipelines: Dict[PluginType, List[str]] = {}
        
        # 创建插件目录
        Path(self.plugins_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化执行流水线
        self._initialize_pipelines()
        
        logger.info("插件化安全策略管理器初始化完成")
    
    def _initialize_pipelines(self) -> None:
        """初始化插件执行流水线"""
        self.execution_pipelines = {
            PluginType.AUTHENTICATION: [],
            PluginType.AUTHORIZATION: [],
            PluginType.AUDIT: [],
            PluginType.COMPLIANCE: [],
            PluginType.RISK_ASSESSMENT: [],
            PluginType.THREAT_DETECTION: [],
        }
    
    def load_plugin_from_module(self, module_name: str, class_name: str, config: Dict[str, Any]) -> Optional[str]:
        """从模块加载插件"""
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)
            
            # 获取插件类
            plugin_class = getattr(module, class_name)
            
            # 验证插件类
            if not inspect.isclass(plugin_class) or not issubclass(plugin_class, SecurityPluginBase):
                logger.error(f"无效的插件类: {class_name}")
                return None
            
            # 创建插件实例
            plugin_instance = plugin_class(config)
            
            # 初始化插件
            if not plugin_instance.initialize():
                logger.error(f"插件初始化失败: {class_name}")
                return None
            
            # 创建插件记录
            plugin = SecurityPlugin(
                plugin_id=str(uuid4()),
                name=plugin_class.__name__,
                description=getattr(plugin_class, '__doc__', 'No description'),
                plugin_type=self._detect_plugin_type(plugin_class),
                version=getattr(plugin_class, 'version', '1.0.0'),
                author=getattr(plugin_class, 'author', 'Unknown'),
                config=config,
                instance=plugin_instance,
            )
            
            # 注册插件
            self.plugins[plugin.plugin_id] = plugin
            
            # 添加到执行流水线
            self._add_to_pipeline(plugin)
            
            logger.info(f"成功加载插件: {plugin.name}")
            return plugin.plugin_id
            
        except Exception as e:
            logger.error(f"加载插件失败: {e}", exc_info=True)
            return None
    
    def load_plugin_from_file(self, file_path: str, class_name: str, config: Dict[str, Any]) -> Optional[str]:
        """从文件加载插件"""
        try:
            # 将文件路径添加到Python路径
            file_dir = os.path.dirname(file_path)
            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)
            
            # 获取模块名
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 获取插件类
            plugin_class = getattr(module, class_name)
            
            # 创建插件实例
            plugin_instance = plugin_class(config)
            
            # 初始化插件
            if not plugin_instance.initialize():
                logger.error(f"插件初始化失败: {class_name}")
                return None
            
            # 创建插件记录
            plugin = SecurityPlugin(
                plugin_id=str(uuid4()),
                name=plugin_class.__name__,
                description=getattr(plugin_class, '__doc__', 'No description'),
                plugin_type=self._detect_plugin_type(plugin_class),
                version=getattr(plugin_class, 'version', '1.0.0'),
                author=getattr(plugin_class, 'author', 'Unknown'),
                config=config,
                instance=plugin_instance,
            )
            
            # 注册插件
            self.plugins[plugin.plugin_id] = plugin
            
            # 添加到执行流水线
            self._add_to_pipeline(plugin)
            
            logger.info(f"成功加载插件: {plugin.name}")
            return plugin.plugin_id
            
        except Exception as e:
            logger.error(f"从文件加载插件失败: {e}", exc_info=True)
            return None
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self.plugins:
            logger.error(f"插件不存在: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        try:
            # 清理插件资源
            if plugin.instance:
                plugin.instance.cleanup()
            
            # 从流水线移除
            self._remove_from_pipeline(plugin)
            
            # 移除插件
            del self.plugins[plugin_id]
            
            logger.info(f"成功卸载插件: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件失败: {e}", exc_info=True)
            return False
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        plugin.enabled = True
        plugin.status = PluginStatus.ENABLED
        
        logger.info(f"启用插件: {plugin.name}")
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        plugin.enabled = False
        plugin.status = PluginStatus.DISABLED
        
        logger.info(f"禁用插件: {plugin.name}")
        return True
    
    def execute_pipeline(self, pipeline_type: PluginType, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件流水线"""
        if pipeline_type not in self.execution_pipelines:
            return {"success": False, "error": f"未知的流水线类型: {pipeline_type}"}
        
        plugin_ids = self.execution_pipelines[pipeline_type]
        results = {}
        
        for plugin_id in plugin_ids:
            if plugin_id not in self.plugins:
                continue
                
            plugin = self.plugins[plugin_id]
            
            if not plugin.enabled or plugin.status != PluginStatus.ENABLED:
                continue
            
            try:
                result = plugin.instance.execute(context)
                results[plugin_id] = {
                    "plugin_name": plugin.name,
                    "success": True,
                    "result": result,
                }
                
            except Exception as e:
                results[plugin_id] = {
                    "plugin_name": plugin.name,
                    "success": False,
                    "error": str(e),
                }
                logger.error(f"插件执行失败: {plugin.name} - {e}")
        
        return {
            "pipeline_type": pipeline_type.value,
            "executed_plugins": len(results),
            "results": results,
        }
    
    def _detect_plugin_type(self, plugin_class: Type) -> PluginType:
        """检测插件类型"""
        class_name = plugin_class.__name__.lower()
        
        if 'auth' in class_name and 'authz' not in class_name:
            return PluginType.AUTHENTICATION
        elif 'authz' in class_name or 'authorization' in class_name:
            return PluginType.AUTHORIZATION
        elif 'audit' in class_name:
            return PluginType.AUDIT
        elif 'compliance' in class_name:
            return PluginType.COMPLIANCE
        elif 'risk' in class_name:
            return PluginType.RISK_ASSESSMENT
        elif 'threat' in class_name or 'detection' in class_name:
            return PluginType.THREAT_DETECTION
        else:
            return PluginType.AUTHENTICATION  # 默认类型
    
    def _add_to_pipeline(self, plugin: SecurityPlugin) -> None:
        """将插件添加到执行流水线"""
        pipeline_type = plugin.plugin_type
        
        if pipeline_type in self.execution_pipelines:
            # 按优先级排序插入
            self.execution_pipelines[pipeline_type].append(plugin.plugin_id)
            # 可以根据插件优先级进行排序
            # self.execution_pipelines[pipeline_type].sort(key=lambda pid: self.plugins[pid].priority)
    
    def _remove_from_pipeline(self, plugin: SecurityPlugin) -> None:
        """从执行流水线移除插件"""
        pipeline_type = plugin.plugin_type
        
        if pipeline_type in self.execution_pipelines:
            if plugin.plugin_id in self.execution_pipelines[pipeline_type]:
                self.execution_pipelines[pipeline_type].remove(plugin.plugin_id)
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """获取插件状态统计"""
        status_counts = {status.value: 0 for status in PluginStatus}
        type_counts = {ptype.value: 0 for ptype in PluginType}
        
        for plugin in self.plugins.values():
            status_counts[plugin.status.value] += 1
            type_counts[plugin.plugin_type.value] += 1
        
        return {
            "total_plugins": len(self.plugins),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "pipelines": {
                ptype.value: len(plugin_ids)
                for ptype, plugin_ids in self.execution_pipelines.items()
            }
        }


# 全局实例
_plugin_security_manager: Optional[PluginSecurityManager] = None


def get_plugin_security_manager() -> PluginSecurityManager:
    """获取插件化安全策略管理器实例"""
    global _plugin_security_manager
    if _plugin_security_manager is None:
        _plugin_security_manager = PluginSecurityManager()
    return _plugin_security_manager