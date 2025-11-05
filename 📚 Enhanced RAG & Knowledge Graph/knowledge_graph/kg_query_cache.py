"""
Knowledge Graph Query Cache
知识图谱查询缓存

实现查询结果缓存以提高性能（知识图谱100%完成度的一部分）
"""

import logging
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KGQueryCache:
    """
    知识图谱查询缓存
    
    提供LRU缓存机制，支持TTL（生存时间）
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,  # 1小时
    ):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认生存时间（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # LRU缓存：使用OrderedDict实现
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
        }

    def _generate_cache_key(
        self,
        query_type: str,
        **kwargs: Any,
    ) -> str:
        """
        生成缓存键
        
        Args:
            query_type: 查询类型
            **kwargs: 查询参数
            
        Returns:
            缓存键（MD5哈希）
        """
        # 构建键字符串（排除None值）
        params = {k: v for k, v in kwargs.items() if v is not None}
        key_data = f"{query_type}:{sorted(params.items())}"
        
        # 生成MD5哈希
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"kg_cache:{key_hash}"

    def get(
        self,
        query_type: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存获取查询结果
        
        Args:
            query_type: 查询类型
            **kwargs: 查询参数
            
        Returns:
            缓存的结果，如果未命中或已过期则返回None
        """
        cache_key = self._generate_cache_key(query_type, **kwargs)
        
        # 检查缓存
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            
            # 检查是否过期
            if self._is_expired(entry):
                # 过期，删除
                del self._cache[cache_key]
                self.stats["misses"] += 1
                self.stats["size"] = len(self._cache)
                return None
            
            # 命中，移到末尾（LRU）
            self._cache.move_to_end(cache_key)
            self.stats["hits"] += 1
            
            return entry.get("result")
        
        # 未命中
        self.stats["misses"] += 1
        return None

    def set(
        self,
        query_type: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        将查询结果存入缓存
        
        Args:
            query_type: 查询类型
            result: 查询结果
            ttl: 生存时间（秒），如果为None则使用默认值
            **kwargs: 查询参数
        """
        cache_key = self._generate_cache_key(query_type, **kwargs)
        
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.max_size:
            # 删除最旧的条目
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self.stats["evictions"] += 1
        
        # 设置TTL
        expire_time = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        
        # 存入缓存
        self._cache[cache_key] = {
            "result": result,
            "expire_time": expire_time,
            "query_type": query_type,
            "created_at": datetime.now(),
        }
        
        # 移到末尾（LRU）
        self._cache.move_to_end(cache_key)
        self.stats["size"] = len(self._cache)

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """检查缓存条目是否过期"""
        expire_time = entry.get("expire_time")
        if not expire_time:
            return True
        
        return datetime.now() > expire_time

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self.stats["size"] = 0
        self.stats["hits"] = 0
        self.stats["misses"] = 0
        self.stats["evictions"] = 0

    def invalidate(self, query_type: Optional[str] = None) -> int:
        """
        使缓存失效
        
        Args:
            query_type: 查询类型，如果为None则使所有缓存失效
            
        Returns:
            失效的条目数
        """
        if query_type is None:
            # 使所有缓存失效
            count = len(self._cache)
            self.clear()
            return count
        
        # 使特定类型的缓存失效
        keys_to_remove = [
            key for key, entry in self._cache.items()
            if entry.get("query_type") == query_type
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        self.stats["size"] = len(self._cache)
        return len(keys_to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total_requests,
            "max_size": self.max_size,
        }

    def prune_expired(self) -> int:
        """
        清理过期的缓存条目
        
        Returns:
            清理的条目数
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        self.stats["size"] = len(self._cache)
        return len(expired_keys)


# 全局缓存实例
_kg_query_cache: Optional[KGQueryCache] = None


def get_kg_query_cache() -> KGQueryCache:
    """获取知识图谱查询缓存实例（单例）"""
    global _kg_query_cache
    if _kg_query_cache is None:
        _kg_query_cache = KGQueryCache()
    return _kg_query_cache

