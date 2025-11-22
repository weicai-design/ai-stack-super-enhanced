#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API重试处理器
P2-304: 实现失败重试机制
4.4: 扩展集中化配置（固定/指数/线性策略）
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union, List
from functools import wraps
from enum import Enum
import httpx
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import threading
import importlib
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """重试策略"""
    FIXED = "fixed"  # 固定延迟
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性增长


@dataclass
class RetryConfig:
    """集中化的重试配置"""

    name: str
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    retryable_status_codes: Optional[List[int]] = None
    retryable_exceptions: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetryConfig":
        return cls(
            name=data["name"],
            strategy=RetryStrategy(data.get("strategy", RetryStrategy.EXPONENTIAL.value)),
            max_retries=data.get("max_retries", 3),
            initial_delay=data.get("initial_delay", 1.0),
            max_delay=data.get("max_delay", 60.0),
            retryable_status_codes=data.get("retryable_status_codes"),
            retryable_exceptions=data.get("retryable_exceptions"),
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["strategy"] = self.strategy.value
        return data


class RetryConfigManager:
    """重试配置集中管理器"""

    def __init__(self, config_file: Optional[str] = None):
        base_dir = Path(__file__).parent.parent.parent / ".configs"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = Path(config_file) if config_file else base_dir / "retry_configs.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.configs: Dict[str, RetryConfig] = {}
        self._exception_cache: Dict[str, type[Exception]] = {}
        self._load_configs()
        if not self.configs:
            self._create_default_configs()
            self._save_configs()

    def _load_configs(self):
        if not self.config_file.exists():
            return
        try:
            data = json.loads(self.config_file.read_text())
            for cfg in data.get("configs", []):
                config = RetryConfig.from_dict(cfg)
                self.configs[config.name] = config
        except Exception as exc:
            logger.warning(f"加载重试配置失败: {exc}")

    def _save_configs(self):
        try:
            payload = {
                "updated_at": datetime.utcnow().isoformat(),
                "configs": [cfg.to_dict() for cfg in self.configs.values()],
            }
            self.config_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            self.config_file.chmod(0o600)
        except Exception as exc:
            logger.error(f"保存重试配置失败: {exc}")

    def _create_default_configs(self):
        logger.info("创建默认重试配置 ...")
        defaults = [
            RetryConfig(
                name="fixed_default",
                strategy=RetryStrategy.FIXED,
                max_retries=3,
                initial_delay=2.0,
                max_delay=10.0,
            ),
            RetryConfig(
                name="exp_backoff",
                strategy=RetryStrategy.EXPONENTIAL,
                max_retries=5,
                initial_delay=1.0,
                max_delay=60.0,
            ),
            RetryConfig(
                name="linear_gentle",
                strategy=RetryStrategy.LINEAR,
                max_retries=4,
                initial_delay=1.5,
                max_delay=30.0,
            ),
        ]
        for cfg in defaults:
            self.configs[cfg.name] = cfg

    def list_configs(self) -> List[RetryConfig]:
        with self._lock:
            return list(self.configs.values())

    def get_config(self, name: str) -> RetryConfig:
        with self._lock:
            if name not in self.configs:
                raise ValueError(f"未找到重试配置: {name}")
            return self.configs[name]

    def register_config(self, config: RetryConfig, overwrite: bool = True):
        with self._lock:
            if not overwrite and config.name in self.configs:
                raise ValueError(f"重试配置已存在: {config.name}")
            self.configs[config.name] = config
            self._save_configs()

    def update_config(self, name: str, **kwargs):
        with self._lock:
            config = self.get_config(name)
            data = config.to_dict()
            data.update(kwargs)
            updated = RetryConfig.from_dict(data)
            self.configs[name] = updated
            self._save_configs()

    def resolve_exception(self, name: str) -> Optional[type[Exception]]:
        if not name:
            return None
        if name in self._exception_cache:
            return self._exception_cache[name]
        builtin_map = {
            "TimeoutError": TimeoutError,
            "ConnectionError": ConnectionError,
            "httpx.TimeoutException": httpx.TimeoutException,
            "httpx.ConnectError": httpx.ConnectError,
            "httpx.NetworkError": httpx.NetworkError,
        }
        resolved = builtin_map.get(name)
        if not resolved and "." in name:
            module_name, class_name = name.rsplit(".", 1)
            try:
                module = importlib.import_module(module_name)
                resolved = getattr(module, class_name)
            except (ImportError, AttributeError):
                resolved = None
        if resolved:
            self._exception_cache[name] = resolved
        else:
            logger.warning(f"无法解析异常类型: {name}")
        return resolved

    def get_handler(self, name: str) -> "APIRetryHandler":
        config = self.get_config(name)
        return APIRetryHandler(config=config)


_retry_config_manager = RetryConfigManager()


class RetryableError(Exception):
    """可重试的错误"""
    pass


class NonRetryableError(Exception):
    """不可重试的错误"""
    pass


class APIRetryHandler:
    """
    API重试处理器
    
    功能：
    1. 支持多种重试策略
    2. 可配置重试次数和延迟
    3. 错误分类（可重试/不可重试）
    4. 重试统计和日志
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_status_codes: Optional[List[int]] = None,
        retryable_exceptions: Optional[List[type[Exception]]] = None,
        config_name: Optional[str] = None,
        config: Optional[RetryConfig] = None,
    ):
        """
        初始化重试处理器
        
        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            strategy: 重试策略
            retryable_status_codes: 可重试的HTTP状态码
            retryable_exceptions: 可重试的异常类型
            config_name: 引用集中配置的名称
            config: 直接传入的RetryConfig实例
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.config_name = config_name
        
        # 默认可重试的状态码
        self.retryable_status_codes = retryable_status_codes or [
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ]
        
        # 默认可重试的异常
        self.retryable_exceptions = retryable_exceptions or [
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            ConnectionError,
            TimeoutError,
        ]

        # 如果提供了集中配置，覆盖默认值
        cfg = None
        if config_name:
            try:
                cfg = _retry_config_manager.get_config(config_name)
            except ValueError as exc:
                logger.warning(f"未找到重试配置 {config_name}: {exc}")
        elif config:
            cfg = config

        if cfg:
            self._apply_config(cfg)
    
    def _apply_config(self, cfg: RetryConfig):
        """根据集中配置应用参数"""
        self.strategy = RetryStrategy(cfg.strategy)
        self.max_retries = cfg.max_retries
        self.initial_delay = cfg.initial_delay
        self.max_delay = cfg.max_delay
        if cfg.retryable_status_codes:
            self.retryable_status_codes = cfg.retryable_status_codes
        if cfg.retryable_exceptions:
            resolved_exceptions: List[type[Exception]] = []
            for name in cfg.retryable_exceptions:
                exc_cls = _retry_config_manager.resolve_exception(name)
                if exc_cls:
                    resolved_exceptions.append(exc_cls)
            if resolved_exceptions:
                self.retryable_exceptions = resolved_exceptions
        
        # 统计信息
        self.stats = {
            "total_calls": 0,
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
        }
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * (attempt + 1)
        else:
            delay = self.initial_delay
        
        return min(delay, self.max_delay)
    
    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        # 检查异常类型
        if type(error) in self.retryable_exceptions:
            return True
        
        # 检查HTTP状态码
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code in self.retryable_status_codes:
                return True
        
        # 检查错误消息
        error_msg = str(error).lower()
        retryable_keywords = [
            "timeout", "connection", "network", "temporary",
            "rate limit", "too many requests", "service unavailable",
            "超时", "连接", "网络", "临时", "限流"
        ]
        
        if any(keyword in error_msg for keyword in retryable_keywords):
            return True
        
        return False
    
    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """
        执行函数并重试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        self.stats["total_calls"] += 1
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # 成功
                if attempt > 0:
                    self.stats["successful_retries"] += 1
                    logger.info(f"重试成功（尝试 {attempt + 1}/{self.max_retries + 1}）")
                
                return result
                
            except Exception as e:
                last_error = e
                
                # 判断是否可重试
                if not self._is_retryable(e):
                    logger.error(f"不可重试的错误: {e}")
                    raise NonRetryableError(f"不可重试的错误: {e}") from e
                
                # 检查是否还有重试机会
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.stats["total_retries"] += 1
                    
                    logger.warning(
                        f"执行失败（尝试 {attempt + 1}/{self.max_retries + 1}）: {e}"
                    )
                    logger.info(f"等待 {delay:.2f} 秒后重试...")
                    
                    await asyncio.sleep(delay)
                else:
                    self.stats["failed_retries"] += 1
                    logger.error(f"所有重试均失败（共 {self.max_retries + 1} 次）: {e}")
                    raise RetryableError(f"重试 {self.max_retries} 次后仍失败: {e}") from e
        
        # 理论上不会到达这里
        if last_error:
            raise last_error
        raise RuntimeError("执行失败，无更多信息")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "retry_rate": (
                self.stats["total_retries"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0
            ),
            "success_rate": (
                self.stats["successful_retries"] / self.stats["total_retries"]
                if self.stats["total_retries"] > 0 else 0
            ),
        }


def retry_on_failure(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟
        strategy: 重试策略
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = APIRetryHandler(
            max_retries=max_retries,
            initial_delay=initial_delay,
            strategy=strategy,
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await handler.execute_with_retry(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # 同步函数需要转换为异步执行
            async def async_func():
                return func(*args, **kwargs)
            return asyncio.run(handler.execute_with_retry(async_func))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 默认重试处理器实例
_default_retry_handler = APIRetryHandler()


def get_retry_config_manager() -> RetryConfigManager:
    """获取全局重试配置管理器"""
    return _retry_config_manager


def get_retry_handler(config_name: str) -> APIRetryHandler:
    """根据配置名称获取重试处理器"""
    return _retry_config_manager.get_handler(config_name)


async def execute_with_retry(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retryable_status_codes: Optional[List[int]] = None,
    retryable_exceptions: Optional[List[str]] = None,
    config_name: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    便捷函数：执行函数并重试
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        max_retries: 最大重试次数
        initial_delay: 初始延迟
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果
    """
    if config_name:
        handler = get_retry_handler(config_name)
    else:
        handler = APIRetryHandler(
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            strategy=strategy,
            retryable_status_codes=retryable_status_codes,
            retryable_exceptions=retryable_exceptions,
        )
    return await handler.execute_with_retry(func, *args, **kwargs)

