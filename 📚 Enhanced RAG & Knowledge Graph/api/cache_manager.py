"""
缓存管理器
Cache Manager

提供Redis缓存支持，优化API性能

版本: 1.0.0 (v2.7.0新增)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Callable, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# 尝试导入Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    redis = None
    HAS_REDIS = False
    logger.warning("redis未安装，缓存系统将使用内存模式")


# ==================== 缓存配置 ====================

CACHE_CONFIG = {
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    "redis_password": None,
    "default_ttl": 3600,  # 默认1小时过期
}

# 端点特定缓存策略
ENDPOINT_CACHE_TTL = {
    "/rag/search": 600,           # 搜索结果：10分钟
    "/kg/viz/graph": 3600,        # 完整图谱：1小时
    "/kg/viz/stats": 300,         # 统计：5分钟
    "/kg/viz/nodes/*": 1800,      # 节点查询：30分钟
    "/smart-qa/chat": 0,          # 聊天：不缓存（每次都不同）
    "/index/info": 60,            # 索引信息：1分钟
    "/health": 10,                # 健康检查：10秒
}


# ==================== 缓存管理器 ====================

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, use_redis: bool = True):
        """
        初始化缓存管理器
        
        Args:
            use_redis: 是否使用Redis（False则使用内存缓存）
        """
        self.use_redis = use_redis and HAS_REDIS
        self.redis_client = None
        self.memory_cache = {}  # 内存缓存备份
        
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=CACHE_CONFIG["redis_host"],
                    port=CACHE_CONFIG["redis_port"],
                    db=CACHE_CONFIG["redis_db"],
                    password=CACHE_CONFIG["redis_password"],
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # 测试连接
                self.redis_client.ping()
                logger.info("✅ Redis缓存已连接")
            except Exception as e:
                logger.warning(f"Redis连接失败，切换到内存缓存: {e}")
                self.redis_client = None
                self.use_redis = False
        
        if not self.use_redis:
            logger.info("✅ 使用内存缓存模式")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成缓存key
        
        Args:
            prefix: key前缀
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            缓存key
        """
        # 组合所有参数
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # 生成hash
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"ai-stack:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存key
        
        Returns:
            缓存值或None
        """
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存key
            value: 缓存值
            ttl: 过期时间（秒）
        
        Returns:
            是否成功
        """
        try:
            ttl = ttl or CACHE_CONFIG["default_ttl"]
            value_str = json.dumps(value, ensure_ascii=False)
            
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, value_str)
            else:
                # 内存缓存不支持TTL，简化处理
                self.memory_cache[key] = value
                
                # 限制内存缓存大小
                if len(self.memory_cache) > 1000:
                    # 删除最旧的一半
                    keys_to_delete = list(self.memory_cache.keys())[:500]
                    for k in keys_to_delete:
                        del self.memory_cache[k]
            
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存key
        
        Returns:
            是否成功
        """
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """
        清空缓存
        
        Args:
            pattern: key模式（支持通配符）
        
        Returns:
            删除的key数量
        """
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(f"ai-stack:{pattern}")
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # 内存缓存：简单清空
                count = len(self.memory_cache)
                self.memory_cache.clear()
                return count
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        
        Returns:
            统计信息
        """
        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info()
                return {
                    "backend": "redis",
                    "connected": True,
                    "total_keys": self.redis_client.dbsize(),
                    "memory_used": info.get("used_memory_human", "N/A"),
                    "hit_rate": "N/A",  # 需要额外追踪
                    "uptime_seconds": info.get("uptime_in_seconds", 0)
                }
            else:
                return {
                    "backend": "memory",
                    "connected": True,
                    "total_keys": len(self.memory_cache),
                    "memory_used": "~估算",
                    "hit_rate": "N/A"
                }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {
                "backend": "unknown",
                "connected": False,
                "error": str(e)
            }


# ==================== 缓存装饰器 ====================

def cached(ttl: int = None, key_prefix: str = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存key前缀
    
    Usage:
        @cached(ttl=600, key_prefix="search")
        async def search_function(query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        prefix = key_prefix or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存写入: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"缓存写入: {cache_key}")
            
            return result
        
        # 根据函数类型返回对应wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 全局实例 ====================

# 创建全局缓存管理器
cache_manager = CacheManager(use_redis=True)


# ==================== 辅助函数 ====================

def invalidate_cache(pattern: str = "*") -> int:
    """
    使缓存失效
    
    Args:
        pattern: key模式
    
    Returns:
        删除的key数量
    """
    return cache_manager.clear(pattern)


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计"""
    return cache_manager.get_stats()


# ==================== 导出 ====================

__all__ = [
    "CacheManager",
    "cache_manager",
    "cached",
    "invalidate_cache",
    "get_cache_stats",
    "HAS_REDIS",
    "ENDPOINT_CACHE_TTL"
]






























