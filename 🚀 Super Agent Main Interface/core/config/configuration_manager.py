#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理系统
支持多环境配置、热更新和配置验证
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import uuid4

import yaml
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Environment(str, Enum):
    """环境类型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigSource(str, Enum):
    """配置来源"""
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    CONSUL = "consul"
    ETCD = "etcd"


class ConfigStatus(str, Enum):
    """配置状态"""
    LOADED = "loaded"
    ERROR = "error"
    UPDATED = "updated"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class ConfigMetadata:
    """配置元数据"""
    config_id: str
    name: str
    environment: Environment
    source: ConfigSource
    version: str = "1.0.0"
    last_modified: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checksum: Optional[str] = None
    status: ConfigStatus = ConfigStatus.LOADED
    error_message: Optional[str] = None


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ConfigSchema(BaseModel):
    """配置模式基类"""
    class Config:
        extra = "forbid"  # 禁止额外字段


class DatabaseConfig(ConfigSchema):
    """数据库配置"""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    timeout: int = 30


class RedisConfig(ConfigSchema):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    timeout: int = 5
    retry_on_timeout: bool = True


class SecurityConfig(ConfigSchema):
    """安全配置"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: List[str] = field(default_factory=list)


class LoggingConfig(ConfigSchema):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_size_mb: int = 100
    backup_count: int = 5


class MonitoringConfig(ConfigSchema):
    """监控配置"""
    enabled: bool = True
    port: int = 9090
    interval_seconds: int = 30
    alert_rules: Dict[str, Any] = field(default_factory=dict)


class AppConfig(ConfigSchema):
    """应用配置"""
    name: str
    version: str
    environment: Environment
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4


class FullConfig(ConfigSchema):
    """完整配置"""
    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        pass


class SchemaConfigValidator(ConfigValidator):
    """基于模式的配置验证器"""
    
    def __init__(self, schema_class: Type[ConfigSchema]):
        self.schema_class = schema_class
    
    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置是否符合模式"""
        try:
            # 使用Pydantic验证
            self.schema_class(**config)
            return ConfigValidationResult(is_valid=True)
            
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                msg = error["msg"]
                errors.append(f"{field}: {msg}")
            
            return ConfigValidationResult(is_valid=False, errors=errors)


class RuleBasedConfigValidator(ConfigValidator):
    """基于规则的配置验证器"""
    
    def __init__(self):
        self.rules: List[Callable] = []
    
    def add_rule(self, rule: Callable[[Dict[str, Any]], Optional[str]]) -> None:
        """添加验证规则"""
        self.rules.append(rule)
    
    def validate(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """应用所有规则验证配置"""
        errors = []
        warnings = []
        
        for rule in self.rules:
            result = rule(config)
            if result:
                if result.startswith("WARNING:"):
                    warnings.append(result[8:].strip())
                else:
                    errors.append(result)
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class ConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def can_reload(self) -> bool:
        """是否可以重新加载"""
        pass


class FileConfigLoader(ConfigLoader):
    """文件配置加载器"""
    
    def __init__(self, file_path: str, file_type: str = "auto"):
        self.file_path = Path(file_path)
        self.file_type = file_type
        self.last_modified = None
    
    def load(self) -> Dict[str, Any]:
        """从文件加载配置"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.file_path}")
        
        # 确定文件类型
        file_type = self.file_type
        if file_type == "auto":
            if self.file_path.suffix in ['.yaml', '.yml']:
                file_type = "yaml"
            elif self.file_path.suffix == '.json':
                file_type = "json"
            else:
                file_type = "text"
        
        # 读取文件内容
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析内容
        if file_type == "yaml":
            config = yaml.safe_load(content)
        elif file_type == "json":
            config = json.loads(content)
        else:
            # 简单键值对格式
            config = {}
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        self.last_modified = self.file_path.stat().st_mtime
        return config or {}
    
    def can_reload(self) -> bool:
        """检查文件是否已修改"""
        if not self.file_path.exists():
            return False
        
        current_mtime = self.file_path.stat().st_mtime
        return self.last_modified is None or current_mtime > self.last_modified


class EnvironmentConfigLoader(ConfigLoader):
    """环境变量配置加载器"""
    
    def __init__(self, prefix: str = "APP_", separator: str = "__"):
        self.prefix = prefix
        self.separator = separator
    
    def load(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # 移除前缀并分割层级
                config_key = key[len(self.prefix):].lower()
                
                # 将下划线分隔的键转换为嵌套字典
                keys = config_key.split(self.separator)
                current_dict = config
                
                for k in keys[:-1]:
                    if k not in current_dict:
                        current_dict[k] = {}
                    current_dict = current_dict[k]
                
                # 设置最终值
                final_key = keys[-1]
                
                # 尝试解析为适当类型
                current_dict[final_key] = self._parse_value(value)
        
        return config
    
    def can_reload(self) -> bool:
        """环境变量不支持热重载"""
        return False
    
    def _parse_value(self, value: str) -> Any:
        """解析环境变量值为适当类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        if value.isdigit():
            return int(value)
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 列表（逗号分隔）
        if ',' in value:
            return [self._parse_value(item.strip()) for item in value.split(',')]
        
        # 默认返回字符串
        return value


class ConfigurationManager:
    """
    配置管理器
    
    支持功能：
    1. 多环境配置管理
    2. 配置热更新
    3. 配置验证
    4. 配置变更监听
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.config: Dict[str, Any] = {}
        self.metadata: Dict[str, ConfigMetadata] = {}
        self.loaders: List[ConfigLoader] = []
        self.validators: List[ConfigValidator] = []
        self.watchers: List[Callable] = []
        
        # 默认配置
        self._set_default_config()
        
        logger.info(f"配置管理器初始化完成，环境: {environment}")
    
    def _set_default_config(self) -> None:
        """设置默认配置"""
        self.config = {
            "app": {
                "name": "AI-STACK",
                "version": "1.0.0",
                "environment": self.environment.value,
                "debug": self.environment == Environment.DEVELOPMENT,
                "host": "0.0.0.0",
                "port": 8000,
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": f"ai_stack_{self.environment.value}",
                "username": "postgres",
                "password": "password",
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
            },
            "security": {
                "secret_key": "change_this_in_production",
                "algorithm": "HS256",
            },
            "logging": {
                "level": "INFO",
            },
        }
    
    def add_loader(self, loader: ConfigLoader) -> None:
        """添加配置加载器"""
        self.loaders.append(loader)
    
    def add_validator(self, validator: ConfigValidator) -> None:
        """添加配置验证器"""
        self.validators.append(validator)
    
    def add_watcher(self, watcher: Callable[[Dict[str, Any]], None]) -> None:
        """添加配置变更监听器"""
        self.watchers.append(watcher)
    
    def load_config(self) -> bool:
        """加载所有配置"""
        try:
            new_config = {}
            
            # 按顺序加载配置
            for loader in self.loaders:
                try:
                    loaded_config = loader.load()
                    self._merge_config(new_config, loaded_config)
                    
                    # 记录元数据
                    metadata = ConfigMetadata(
                        config_id=str(uuid4()),
                        name=f"loader_{len(self.metadata)}",
                        environment=self.environment,
                        source=ConfigSource.FILE if isinstance(loader, FileConfigLoader) else ConfigSource.ENVIRONMENT,
                        status=ConfigStatus.LOADED,
                    )
                    self.metadata[metadata.config_id] = metadata
                    
                except Exception as e:
                    logger.error(f"配置加载失败: {e}")
                    metadata = ConfigMetadata(
                        config_id=str(uuid4()),
                        name=f"loader_{len(self.metadata)}",
                        environment=self.environment,
                        source=ConfigSource.FILE if isinstance(loader, FileConfigLoader) else ConfigSource.ENVIRONMENT,
                        status=ConfigStatus.ERROR,
                        error_message=str(e),
                    )
                    self.metadata[metadata.config_id] = metadata
            
            # 验证配置
            validation_result = self.validate_config(new_config)
            
            if not validation_result.is_valid:
                logger.error(f"配置验证失败: {validation_result.errors}")
                return False
            
            # 应用新配置
            old_config = self.config.copy()
            self.config = new_config
            
            # 通知监听器
            if old_config != new_config:
                self._notify_watchers(new_config)
            
            logger.info("配置加载成功")
            return True
            
        except Exception as e:
            logger.error(f"配置加载过程失败: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """验证配置"""
        errors = []
        warnings = []
        
        for validator in self.validators:
            result = validator.validate(config)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值"""
        keys = key.split('.')
        current = self.config
        
        # 导航到父级
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # 设置值
        final_key = keys[-1]
        old_value = current.get(final_key)
        current[final_key] = value
        
        # 验证新配置
        validation_result = self.validate_config(self.config)
        
        if not validation_result.is_valid:
            # 回滚更改
            if old_value is not None:
                current[final_key] = old_value
            else:
                del current[final_key]
            
            logger.error(f"配置设置失败: {validation_result.errors}")
            return False
        
        # 通知监听器
        self._notify_watchers(self.config)
        
        return True
    
    def reload_if_needed(self) -> bool:
        """检查并重新加载配置"""
        needs_reload = any(loader.can_reload() for loader in self.loaders)
        
        if needs_reload:
            logger.info("检测到配置变更，重新加载配置")
            return self.load_config()
        
        return False
    
    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照"""
        return self.config.copy()
    
    def get_metadata(self) -> Dict[str, ConfigMetadata]:
        """获取配置元数据"""
        return self.metadata.copy()
    
    def _merge_config(self, base: Dict[str, Any], new: Dict[str, Any]) -> None:
        """合并配置（深度合并）"""
        for key, value in new.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _notify_watchers(self, new_config: Dict[str, Any]) -> None:
        """通知配置变更监听器"""
        for watcher in self.watchers:
            try:
                watcher(new_config)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败: {e}")


# 全局实例
_configuration_manager: Optional[ConfigurationManager] = None


def get_configuration_manager(environment: Environment = Environment.DEVELOPMENT) -> ConfigurationManager:
    """获取配置管理器实例"""
    global _configuration_manager
    if _configuration_manager is None:
        _configuration_manager = ConfigurationManager(environment)
    return _configuration_manager


def create_default_config_files() -> None:
    """创建默认配置文件"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # 开发环境配置
    dev_config = {
        "app": {
            "name": "AI-STACK",
            "version": "1.0.0",
            "environment": "development",
            "debug": True,
            "host": "0.0.0.0",
            "port": 8000,
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "database": "ai_stack_development",
            "username": "postgres",
            "password": "password",
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
        },
        "security": {
            "secret_key": "dev_secret_key_change_in_production",
            "algorithm": "HS256",
            "access_token_expire_minutes": 60,
        },
        "logging": {
            "level": "DEBUG",
        },
    }
    
    with open(config_dir / "development.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(dev_config, f, default_flow_style=False, allow_unicode=True)
    
    # 生产环境配置
    prod_config = {
        "app": {
            "name": "AI-STACK",
            "version": "1.0.0",
            "environment": "production",
            "debug": False,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
        },
        "database": {
            "host": "db.example.com",
            "port": 5432,
            "database": "ai_stack_production",
            "username": "ai_stack_user",
            "password": "${DB_PASSWORD}",  # 从环境变量读取
        },
        "redis": {
            "host": "redis.example.com",
            "port": 6379,
            "password": "${REDIS_PASSWORD}",
        },
        "security": {
            "secret_key": "${SECRET_KEY}",  # 从环境变量读取
            "algorithm": "HS256",
            "access_token_expire_minutes": 30,
        },
        "logging": {
            "level": "INFO",
            "file_path": "/var/log/ai_stack/app.log",
            "max_size_mb": 100,
            "backup_count": 10,
        },
        "monitoring": {
            "enabled": True,
            "port": 9090,
        },
    }
    
    with open(config_dir / "production.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(prod_config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info("默认配置文件创建完成")