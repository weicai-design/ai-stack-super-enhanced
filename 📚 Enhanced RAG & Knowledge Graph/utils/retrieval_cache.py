"""
Retrieval Cache Module
检索缓存模块

性能优化：添加检索结果缓存以提升响应速度
"""

import hashlib
import json
import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger(__name__)


class RetrievalCache:
    """
    检索结果缓存
    
    使用LRU缓存策略，自动过期机制
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,  # 1小时过期
        enable_cache: bool = True,
    ):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间（秒）
            enable_cache: 是否启用缓存
        """
        self.max_size = max_size
        self.ttl = ttl
        self.enable_cache = enable_cache
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(
        self,
        query: str,
        top_k: int,
        modality: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """生成缓存键"""
        key_data = {
            "query": query,
            "top_k": top_k,
            "modality": modality,
            "filters": filters or {},
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self,
        query: str,
        top_k: int,
        modality: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存结果
        
        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        if not self.enable_cache:
            return None
        
        key = self._make_key(query, top_k, modality, filters)
        
        if key not in self._cache:
            self._misses += 1
            return None
        
        cached_item = self._cache[key]
        
        # 检查是否过期
        if time.time() - cached_item["timestamp"] > self.ttl:
            del self._cache[key]
            self._misses += 1
            return None
        
        # 移到末尾（LRU）
        self._cache.move_to_end(key)
        self._hits += 1
        
        return cached_item["results"]

    def set(
        self,
        query: str,
        top_k: int,
        results: List[Dict[str, Any]],
        modality: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """设置缓存结果"""
        if not self.enable_cache:
            return
        
        key = self._make_key(query, top_k, modality, filters)
        
        # 如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)  # 删除最旧的（FIFO）
        
        # 添加新条目
        self._cache[key] = {
            "results": results,
            "timestamp": time.time(),
        }
        
        # 移到末尾（LRU）
        self._cache.move_to_end(key)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "enabled": self.enable_cache,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl": self.ttl,
        }

    def cleanup_expired(self):
        """清理过期条目"""
        if not self.enable_cache:
            return
        
        current_time = time.time()
        expired_keys = [
            key
            for key, item in self._cache.items()
            if current_time - item["timestamp"] > self.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]


# 全局缓存实例
_global_cache: Optional[RetrievalCache] = None


def get_retrieval_cache(
    max_size: int = 1000,
    ttl: int = 3600,
    enable_cache: bool = True,
) -> RetrievalCache:
    """
    获取检索缓存实例（单例模式）
    
    Args:
        max_size: 最大缓存条目数
        ttl: 缓存过期时间（秒）
        enable_cache: 是否启用缓存
        
    Returns:
        RetrievalCache实例
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = RetrievalCache(
            max_size=max_size,
            ttl=ttl,
            enable_cache=enable_cache,
        )
    
    return _global_cache

