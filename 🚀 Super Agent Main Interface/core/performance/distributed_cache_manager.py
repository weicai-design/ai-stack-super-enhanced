#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式缓存管理器
支持多级缓存、监控指标和性能优化
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """缓存级别"""
    L1 = "l1"  # 内存缓存
    L2 = "l2"  # Redis缓存
    L3 = "l3"  # 分布式缓存


class CacheOperation(str, Enum):
    """缓存操作类型"""
    GET = "get"
    SET = "set"
    DELETE = "delete"
    HIT = "hit"
    MISS = "miss"
    EXPIRE = "expire"


@dataclass
class CacheMetrics:
    """缓存指标"""
    total_operations: int = 0
    hit_count: int = 0
    miss_count: int = 0
    error_count: int = 0
    total_size_bytes: int = 0
    avg_response_time_ms: float = 0.0


@dataclass
class CacheConfig:
    """缓存配置"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 内存缓存配置
    memory_cache_max_size: int = 10000
    memory_cache_ttl: int = 300  # 5分钟
    
    # Redis缓存配置
    redis_cache_ttl: int = 3600  # 1小时
    
    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # 性能优化配置
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB
    enable_batching: bool = True
    batch_size: int = 100


class CacheBackend(ABC):
    """缓存后端接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> CacheMetrics:
        """获取缓存指标"""
        pass


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
    
    async def get(self, key: str) -> Optional[Any]:
        start_time = time.time()
        
        try:
            if key not in self.cache:
                self.metrics.miss_count += 1
                self.metrics.total_operations += 1
                return None
            
            item = self.cache[key]
            
            # 检查是否过期
            if time.time() > item['expire_time']:
                del self.cache[key]
                self.metrics.miss_count += 1
                self.metrics.total_operations += 1
                return None
            
            self.metrics.hit_count += 1
            self.metrics.total_operations += 1
            
            # 更新响应时间指标
            response_time = (time.time() - start_time) * 1000
            self.metrics.avg_response_time_ms = (
                self.metrics.avg_response_time_ms * (self.metrics.total_operations - 1) + response_time
            ) / self.metrics.total_operations
            
            return item['value']
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"内存缓存获取失败: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            # 检查缓存大小
            if len(self.cache) >= self.max_size:
                # LRU淘汰策略
                self._evict_oldest()
            
            expire_time = time.time() + (ttl or self.default_ttl)
            
            self.cache[key] = {
                'value': value,
                'expire_time': expire_time,
                'access_time': time.time(),
            }
            
            self.metrics.total_operations += 1
            self.metrics.total_size_bytes += self._estimate_size(value)
            
            return True
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"内存缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            if key in self.cache:
                old_size = self._estimate_size(self.cache[key]['value'])
                del self.cache[key]
                self.metrics.total_size_bytes -= old_size
                self.metrics.total_operations += 1
                return True
            return False
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"内存缓存删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            if key not in self.cache:
                return False
            
            item = self.cache[key]
            return time.time() <= item['expire_time']
            
        except Exception as e:
            logger.error(f"内存缓存检查失败: {e}")
            return False
    
    def get_metrics(self) -> CacheMetrics:
        return self.metrics
    
    def _evict_oldest(self) -> None:
        """淘汰最久未使用的缓存项"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['access_time'])
        old_size = self._estimate_size(self.cache[oldest_key]['value'])
        del self.cache[oldest_key]
        self.metrics.total_size_bytes -= old_size
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小"""
        try:
            return len(str(value).encode('utf-8'))
        except:
            return 1024  # 默认大小


class RedisCacheBackend(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, default_ttl: int = 3600):
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, password=password,
            decode_responses=True, socket_connect_timeout=5,
            socket_timeout=5, retry_on_timeout=True
        )
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
    
    async def get(self, key: str) -> Optional[Any]:
        start_time = time.time()
        
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                self.metrics.miss_count += 1
                self.metrics.total_operations += 1
                return None
            
            # 解析JSON值
            try:
                parsed_value = json.loads(value)
                self.metrics.hit_count += 1
                self.metrics.total_operations += 1
                
                # 更新响应时间指标
                response_time = (time.time() - start_time) * 1000
                self.metrics.avg_response_time_ms = (
                    self.metrics.avg_response_time_ms * (self.metrics.total_operations - 1) + response_time
                ) / self.metrics.total_operations
                
                return parsed_value
                
            except json.JSONDecodeError:
                self.metrics.miss_count += 1
                return None
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Redis缓存获取失败: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            # 序列化为JSON
            json_value = json.dumps(value)
            
            result = self.redis_client.setex(
                key, ttl or self.default_ttl, json_value
            )
            
            self.metrics.total_operations += 1
            self.metrics.total_size_bytes += len(json_value.encode('utf-8'))
            
            return bool(result)
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Redis缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            result = self.redis_client.delete(key)
            self.metrics.total_operations += 1
            return bool(result)
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Redis缓存删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis缓存检查失败: {e}")
            return False
    
    def get_metrics(self) -> CacheMetrics:
        return self.metrics


class DistributedCacheManager:
    """
    分布式缓存管理器
    
    支持多级缓存策略：
    - L1: 内存缓存（快速访问）
    - L2: Redis缓存（分布式）
    - L3: 持久化存储（备用）
    """
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.backends: Dict[CacheLevel, CacheBackend] = {}
        self.metrics_enabled = config.enable_metrics
        
        # 初始化缓存后端
        self._initialize_backends()
        
        # 初始化Prometheus指标
        if self.metrics_enabled:
            self._initialize_metrics()
        
        logger.info("分布式缓存管理器初始化完成")
    
    def _initialize_backends(self) -> None:
        """初始化缓存后端"""
        # L1: 内存缓存
        self.backends[CacheLevel.L1] = MemoryCacheBackend(
            max_size=self.config.memory_cache_max_size,
            default_ttl=self.config.memory_cache_ttl
        )
        
        # L2: Redis缓存
        try:
            self.backends[CacheLevel.L2] = RedisCacheBackend(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                default_ttl=self.config.redis_cache_ttl
            )
        except Exception as e:
            logger.warning(f"Redis连接失败，将禁用L2缓存: {e}")
        
        # 启动指标服务器
        if self.metrics_enabled:
            try:
                start_http_server(self.config.metrics_port)
                logger.info(f"缓存指标服务器启动在端口 {self.config.metrics_port}")
            except Exception as e:
                logger.error(f"指标服务器启动失败: {e}")
    
    def _initialize_metrics(self) -> None:
        """初始化Prometheus指标"""
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'level']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            ['level']
        )
        
        self.cache_response_time = Histogram(
            'cache_response_time_seconds',
            'Cache response time in seconds',
            ['operation', 'level']
        )
        
        self.cache_size_bytes = Gauge(
            'cache_size_bytes',
            'Cache size in bytes',
            ['level']
        )
    
    async def get(self, key: str, levels: List[CacheLevel] = None) -> Optional[Any]:
        """
        获取缓存值（多级缓存策略）
        
        Args:
            key: 缓存键
            levels: 缓存级别顺序，默认 [L1, L2]
        
        Returns:
            缓存值或None
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2]
        
        # 按级别顺序查找
        for level in levels:
            if level not in self.backends:
                continue
            
            backend = self.backends[level]
            value = await backend.get(key)
            
            if value is not None:
                # 缓存命中，更新低级缓存
                await self._update_lower_levels(key, value, levels, level)
                
                # 更新指标
                if self.metrics_enabled:
                    self.cache_operations_total.labels(
                        operation=CacheOperation.HIT.value,
                        level=level.value
                    ).inc()
                
                return value
            
            # 更新指标
            if self.metrics_enabled:
                self.cache_operations_total.labels(
                    operation=CacheOperation.MISS.value,
                    level=level.value
                ).inc()
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  levels: List[CacheLevel] = None) -> bool:
        """
        设置缓存值（多级缓存策略）
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            levels: 缓存级别，默认 [L1, L2]
        
        Returns:
            是否设置成功
        """
        if levels is None:
            levels = [CacheLevel.L1, CacheLevel.L2]
        
        success = True
        
        for level in levels:
            if level not in self.backends:
                continue
            
            backend = self.backends[level]
            result = await backend.set(key, value, ttl)
            
            if not result:
                success = False
                logger.warning(f"缓存设置失败: {level} - {key}")
            
            # 更新指标
            if self.metrics_enabled:
                self.cache_operations_total.labels(
                    operation=CacheOperation.SET.value,
                    level=level.value
                ).inc()
        
        return success
    
    async def delete(self, key: str, levels: List[CacheLevel] = None) -> bool:
        """删除缓存值"""
        if levels is None:
            levels = list(self.backends.keys())
        
        success = True
        
        for level in levels:
            if level not in self.backends:
                continue
            
            backend = self.backends[level]
            result = await backend.delete(key)
            
            if not result:
                success = False
            
            # 更新指标
            if self.metrics_enabled:
                self.cache_operations_total.labels(
                    operation=CacheOperation.DELETE.value,
                    level=level.value
                ).inc()
        
        return success
    
    async def _update_lower_levels(self, key: str, value: Any, 
                                  levels: List[CacheLevel], hit_level: CacheLevel) -> None:
        """更新低级缓存"""
        hit_index = levels.index(hit_level)
        
        # 更新比命中级别低的缓存
        for lower_level in levels[:hit_index]:
            if lower_level in self.backends:
                await self.backends[lower_level].set(key, value)
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """获取缓存指标"""
        metrics = {}
        
        for level, backend in self.backends.items():
            backend_metrics = backend.get_metrics()
            
            hit_ratio = 0.0
            if backend_metrics.total_operations > 0:
                hit_ratio = backend_metrics.hit_count / backend_metrics.total_operations
            
            metrics[level.value] = {
                'total_operations': backend_metrics.total_operations,
                'hit_count': backend_metrics.hit_count,
                'miss_count': backend_metrics.miss_count,
                'error_count': backend_metrics.error_count,
                'hit_ratio': hit_ratio,
                'avg_response_time_ms': backend_metrics.avg_response_time_ms,
                'total_size_bytes': backend_metrics.total_size_bytes,
            }
        
        return metrics
    
    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        health_status = {}
        
        for level, backend in self.backends.items():
            try:
                # 测试连接
                test_key = f"health_check_{uuid4().hex}"
                test_value = {"timestamp": time.time()}
                
                set_result = await backend.set(test_key, test_value, 10)
                get_result = await backend.get(test_key)
                delete_result = await backend.delete(test_key)
                
                health_status[level.value] = all([set_result, get_result is not None, delete_result])
                
            except Exception as e:
                logger.error(f"缓存健康检查失败 {level}: {e}")
                health_status[level.value] = False
        
        return health_status


# 全局实例
_distributed_cache_manager: Optional[DistributedCacheManager] = None


def get_distributed_cache_manager(config: Optional[CacheConfig] = None) -> DistributedCacheManager:
    """获取分布式缓存管理器实例"""
    global _distributed_cache_manager
    if _distributed_cache_manager is None:
        if config is None:
            config = CacheConfig()
        _distributed_cache_manager = DistributedCacheManager(config)
    return _distributed_cache_manager