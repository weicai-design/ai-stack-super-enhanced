#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试配置集中管理器
4.4: 统一管理所有API的重试配置（固定/指数/线性策略）
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
from enum import Enum

from .api_retry_handler import RetryStrategy, APIRetryHandler

logger = logging.getLogger(__name__)


class RetryConfigManager:
    """
    重试配置集中管理器
    
    功能：
    1. 统一管理所有API的重试配置
    2. 支持固定/指数/线性三种策略
    3. 支持平台级别的配置
    4. 支持全局默认配置
    5. 配置持久化存储
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化重试配置管理器
        
        Args:
            config_file: 配置文件路径（默认：项目根目录/.retry_config.json）
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path(__file__).parent.parent.parent / ".retry_config.json"
        
        # 默认配置
        self.default_config = {
            "max_retries": 3,
            "initial_delay": 1.0,
            "max_delay": 60.0,
            "strategy": RetryStrategy.EXPONENTIAL.value,
            "retryable_status_codes": [429, 500, 502, 503, 504],
        }
        
        # 平台配置
        self.platform_configs: Dict[str, Dict[str, Any]] = {}
        
        # 加载配置
        self._load_config()
        
        logger.info(f"重试配置管理器初始化完成，配置文件: {self.config_file}")
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.platform_configs = data.get("platforms", {})
                    if "default" in data:
                        self.default_config.update(data["default"])
            except Exception as e:
                logger.warning(f"加载重试配置失败: {e}，使用默认配置")
                self.platform_configs = {}
        else:
            # 创建默认配置文件
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            data = {
                "default": self.default_config,
                "platforms": self.platform_configs,
                "updated_at": datetime.utcnow().isoformat(),
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.config_file.chmod(0o600)  # 仅所有者可读写
        except Exception as e:
            logger.error(f"保存重试配置失败: {e}")
    
    def get_retry_config(
        self,
        platform: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取重试配置
        
        Args:
            platform: 平台名称（douyin/ths123/erp/content等）
            api_endpoint: API端点（可选，用于更细粒度的配置）
            
        Returns:
            重试配置字典
        """
        # 1. 尝试获取端点级别的配置
        if platform and api_endpoint:
            endpoint_key = f"{platform}:{api_endpoint}"
            if endpoint_key in self.platform_configs:
                config = self.default_config.copy()
                config.update(self.platform_configs[endpoint_key])
                return config
        
        # 2. 尝试获取平台级别的配置
        if platform and platform in self.platform_configs:
            config = self.default_config.copy()
            config.update(self.platform_configs[platform])
            return config
        
        # 3. 返回默认配置
        return self.default_config.copy()
    
    def set_retry_config(
        self,
        platform: str,
        config: Dict[str, Any],
        api_endpoint: Optional[str] = None,
    ) -> bool:
        """
        设置重试配置
        
        Args:
            platform: 平台名称
            config: 配置字典（支持：max_retries, initial_delay, max_delay, strategy）
            api_endpoint: API端点（可选，用于更细粒度的配置）
            
        Returns:
            是否成功
        """
        try:
            # 验证配置
            validated_config = self._validate_config(config)
            
            # 确定配置键
            if api_endpoint:
                config_key = f"{platform}:{api_endpoint}"
            else:
                config_key = platform
            
            # 更新配置
            self.platform_configs[config_key] = validated_config
            
            # 保存配置
            self._save_config()
            
            logger.info(f"已设置重试配置: {config_key}")
            return True
            
        except Exception as e:
            logger.error(f"设置重试配置失败: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置"""
        validated = {}
        
        # max_retries
        if "max_retries" in config:
            max_retries = int(config["max_retries"])
            if max_retries < 0 or max_retries > 10:
                raise ValueError("max_retries 必须在 0-10 之间")
            validated["max_retries"] = max_retries
        
        # initial_delay
        if "initial_delay" in config:
            initial_delay = float(config["initial_delay"])
            if initial_delay < 0:
                raise ValueError("initial_delay 必须 >= 0")
            validated["initial_delay"] = initial_delay
        
        # max_delay
        if "max_delay" in config:
            max_delay = float(config["max_delay"])
            if max_delay < 0:
                raise ValueError("max_delay 必须 >= 0")
            validated["max_delay"] = max_delay
        
        # strategy
        if "strategy" in config:
            strategy = config["strategy"]
            if strategy not in [RetryStrategy.FIXED.value, RetryStrategy.EXPONENTIAL.value, RetryStrategy.LINEAR.value]:
                raise ValueError(f"strategy 必须是 {RetryStrategy.FIXED.value}, {RetryStrategy.EXPONENTIAL.value}, 或 {RetryStrategy.LINEAR.value}")
            validated["strategy"] = strategy
        
        # retryable_status_codes
        if "retryable_status_codes" in config:
            codes = config["retryable_status_codes"]
            if not isinstance(codes, list):
                raise ValueError("retryable_status_codes 必须是列表")
            validated["retryable_status_codes"] = [int(c) for c in codes]
        
        return validated
    
    def get_retry_handler(
        self,
        platform: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> APIRetryHandler:
        """
        获取重试处理器实例
        
        Args:
            platform: 平台名称
            api_endpoint: API端点
            
        Returns:
            APIRetryHandler实例
        """
        config = self.get_retry_config(platform, api_endpoint)
        
        return APIRetryHandler(
            max_retries=config.get("max_retries", 3),
            initial_delay=config.get("initial_delay", 1.0),
            max_delay=config.get("max_delay", 60.0),
            strategy=RetryStrategy(config.get("strategy", RetryStrategy.EXPONENTIAL.value)),
            retryable_status_codes=config.get("retryable_status_codes", [429, 500, 502, 503, 504]),
        )
    
    def set_default_config(self, config: Dict[str, Any]) -> bool:
        """
        设置默认配置
        
        Args:
            config: 配置字典
            
        Returns:
            是否成功
        """
        try:
            validated_config = self._validate_config(config)
            self.default_config.update(validated_config)
            self._save_config()
            logger.info("已更新默认重试配置")
            return True
        except Exception as e:
            logger.error(f"设置默认配置失败: {e}")
            return False
    
    def delete_retry_config(
        self,
        platform: str,
        api_endpoint: Optional[str] = None,
    ) -> bool:
        """
        删除重试配置
        
        Args:
            platform: 平台名称
            api_endpoint: API端点
            
        Returns:
            是否成功
        """
        try:
            if api_endpoint:
                config_key = f"{platform}:{api_endpoint}"
            else:
                config_key = platform
            
            if config_key in self.platform_configs:
                del self.platform_configs[config_key]
                self._save_config()
                logger.info(f"已删除重试配置: {config_key}")
                return True
            else:
                logger.warning(f"重试配置不存在: {config_key}")
                return False
                
        except Exception as e:
            logger.error(f"删除重试配置失败: {e}")
            return False
    
    def list_platforms(self) -> List[str]:
        """列出所有已配置的平台"""
        platforms = set()
        for key in self.platform_configs.keys():
            if ":" in key:
                platform = key.split(":")[0]
            else:
                platform = key
            platforms.add(platform)
        return sorted(list(platforms))
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "default": self.default_config,
            "platforms": self.platform_configs,
        }
    
    def reset_to_defaults(self) -> bool:
        """重置为默认配置"""
        try:
            self.platform_configs = {}
            self.default_config = {
                "max_retries": 3,
                "initial_delay": 1.0,
                "max_delay": 60.0,
                "strategy": RetryStrategy.EXPONENTIAL.value,
                "retryable_status_codes": [429, 500, 502, 503, 504],
            }
            self._save_config()
            logger.info("已重置为默认配置")
            return True
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False


# 单例实例
_retry_config_manager: Optional[RetryConfigManager] = None


def get_retry_config_manager() -> RetryConfigManager:
    """获取重试配置管理器实例（单例）"""
    global _retry_config_manager
    if _retry_config_manager is None:
        _retry_config_manager = RetryConfigManager()
    return _retry_config_manager

