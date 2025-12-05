"""
配置管理器
支持环境隔离、动态配置、配置热更新
"""

import json
import os
import threading
import time
from typing import Dict, Any, Optional
from enum import Enum


class Environment(Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.environment = self._detect_environment()
        self.configs: Dict[str, Any] = {}
        self.last_modified: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.watcher_thread = None
        self.watching = False
        
        # 加载配置
        self._load_all_configs()
        
        # 启动配置监听
        self._start_config_watcher()
    
    def _detect_environment(self) -> Environment:
        """检测运行环境"""
        env_str = os.environ.get("ENVIRONMENT", "development").lower()
        
        if env_str in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env_str in ["stage", "staging"]:
            return Environment.STAGING
        elif env_str in ["test", "testing"]:
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT
    
    def _get_config_file_path(self, config_name: str) -> str:
        """获取配置文件路径"""
        return os.path.join(self.config_dir, f"{config_name}.{self.environment.value}.json")
    
    def _load_config(self, config_name: str) -> Dict[str, Any]:
        """加载单个配置文件"""
        config_path = self._get_config_file_path(config_name)
        
        if not os.path.exists(config_path):
            # 尝试加载默认配置
            default_path = os.path.join(self.config_dir, f"{config_name}.json")
            if not os.path.exists(default_path):
                return {}
            config_path = default_path
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 记录最后修改时间
            self.last_modified[config_name] = os.path.getmtime(config_path)
            
            return config
            
        except Exception as e:
            print(f"加载配置文件 {config_path} 失败: {e}")
            return {}
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        config_files = [
            "database", "api", "security", "cache", 
            "rate_limit", "circuit_breaker", "procurement"
        ]
        
        for config_name in config_files:
            self.configs[config_name] = self._load_config(config_name)
    
    def get(self, config_name: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self.lock:
            config = self.configs.get(config_name, {})
            return config.get(key, default)
    
    def set(self, config_name: str, key: str, value: Any):
        """设置配置值（仅内存中）"""
        with self.lock:
            if config_name not in self.configs:
                self.configs[config_name] = {}
            self.configs[config_name][key] = value
    
    def reload_config(self, config_name: str):
        """重新加载配置文件"""
        with self.lock:
            self.configs[config_name] = self._load_config(config_name)
    
    def _check_config_updates(self):
        """检查配置更新"""
        for config_name in list(self.last_modified.keys()):
            config_path = self._get_config_file_path(config_name)
            
            if not os.path.exists(config_path):
                continue
            
            current_mtime = os.path.getmtime(config_path)
            if current_mtime > self.last_modified[config_name]:
                print(f"检测到配置文件 {config_name} 已更新，重新加载...")
                self.reload_config(config_name)
    
    def _config_watcher(self):
        """配置监听器"""
        while self.watching:
            try:
                self._check_config_updates()
                time.sleep(10)  # 每10秒检查一次
            except Exception as e:
                print(f"配置监听器异常: {e}")
                time.sleep(30)
    
    def _start_config_watcher(self):
        """启动配置监听器"""
        if self.watcher_thread is None:
            self.watching = True
            self.watcher_thread = threading.Thread(target=self._config_watcher, daemon=True)
            self.watcher_thread.start()
    
    def stop_config_watcher(self):
        """停止配置监听器"""
        self.watching = False
        if self.watcher_thread:
            self.watcher_thread.join(timeout=5)
    
    def get_environment(self) -> Environment:
        """获取当前环境"""
        return self.environment
    
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.environment == Environment.DEVELOPMENT


# 全局配置管理器实例
config_manager = ConfigManager()