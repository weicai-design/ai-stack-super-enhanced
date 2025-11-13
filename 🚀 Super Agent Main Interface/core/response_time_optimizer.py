"""
响应时间优化器
专门用于优化2秒响应时间目标
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class ResponseTimeOptimizer:
    """
    响应时间优化器
    
    通过以下策略优化响应时间：
    1. 智能缓存（基于查询相似度）
    2. 快速路径（简单查询直接返回）
    3. 超时控制（避免长时间等待）
    4. 并行优化（最大化并行执行）
    """
    
    def __init__(self, max_cache_size: int = 2000, cache_ttl: int = 600):
        """
        初始化优化器
        
        Args:
            max_cache_size: 最大缓存条目数
            cache_ttl: 缓存生存时间（秒），默认10分钟
        """
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        
        # LRU缓存
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # 统计信息
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "fast_path_hits": 0,
            "timeout_count": 0,
            "total_requests": 0
        }
    
    def _make_cache_key(self, query: str, context: Optional[Dict] = None) -> str:
        """
        生成缓存键
        
        Args:
            query: 查询文本
            context: 上下文信息
            
        Returns:
            缓存键（MD5哈希）
        """
        # 标准化查询（去除多余空格，转小写）
        normalized_query = " ".join(query.lower().split())
        
        # 包含上下文信息
        key_data = {
            "query": normalized_query,
            "context": json.dumps(context or {}, sort_keys=True)
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cache(self, query: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        从缓存获取结果
        
        Args:
            query: 查询文本
            context: 上下文信息
            
        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        cache_key = self._make_cache_key(query, context)
        
        if cache_key not in self.cache:
            self.stats["cache_misses"] += 1
            return None
        
        cached_item = self.cache[cache_key]
        
        # 检查是否过期
        if (datetime.now() - cached_item["cached_at"]).total_seconds() > self.cache_ttl:
            del self.cache[cache_key]
            self.stats["cache_misses"] += 1
            return None
        
        # 命中缓存，移到末尾（LRU）
        self.cache.move_to_end(cache_key)
        self.stats["cache_hits"] += 1
        
        return cached_item["result"]
    
    def set_cache(self, query: str, result: Any, context: Optional[Dict] = None):
        """
        设置缓存
        
        Args:
            query: 查询文本
            result: 结果数据
            context: 上下文信息
        """
        cache_key = self._make_cache_key(query, context)
        
        # 限制缓存大小
        if len(self.cache) >= self.max_cache_size:
            # 删除最旧的条目
            self.cache.popitem(last=False)
        
        # 添加新条目
        self.cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now()
        }
        
        # 移到末尾（LRU）
        self.cache.move_to_end(cache_key)
    
    def is_simple_query(self, query: str) -> bool:
        """
        判断是否为简单查询（可以快速响应）
        
        Args:
            query: 查询文本
            
        Returns:
            是否为简单查询
        """
        # 简单查询的特征：
        # 1. 长度较短（<50字符）
        # 2. 不包含复杂关键词
        # 3. 常见问候语或简单问题
        
        if len(query) > 50:
            return False
        
        simple_keywords = [
            "你好", "hello", "hi", "谢谢", "thanks",
            "帮助", "help", "功能", "功能列表",
            "状态", "status", "健康", "health"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in simple_keywords)
    
    async def optimize_execution(
        self,
        func: Callable,
        query: str,
        context: Optional[Dict] = None,
        timeout: float = 2.0,
        use_cache: bool = True,
        fast_path_handler: Optional[Callable] = None
    ) -> Any:
        """
        优化执行函数
        
        Args:
            func: 要执行的异步函数
            query: 查询文本
            context: 上下文信息
            timeout: 超时时间（秒）
            use_cache: 是否使用缓存
            fast_path_handler: 快速路径处理器（可选）
            
        Returns:
            执行结果
        """
        self.stats["total_requests"] += 1
        
        # 1. 检查缓存
        if use_cache:
            cached_result = self.get_cache(query, context)
            if cached_result is not None:
                return cached_result
        
        # 2. 快速路径（简单查询）
        if fast_path_handler and self.is_simple_query(query):
            try:
                fast_result = await asyncio.wait_for(
                    fast_path_handler(query, context),
                    timeout=0.5  # 快速路径0.5秒超时
                )
                self.stats["fast_path_hits"] += 1
                
                # 缓存快速路径结果
                if use_cache:
                    self.set_cache(query, fast_result, context)
                
                return fast_result
            except asyncio.TimeoutError:
                logger.warning(f"快速路径超时: {query}")
            except Exception as e:
                logger.warning(f"快速路径失败: {e}")
        
        # 3. 正常执行（带超时）
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                func(),
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            
            # 缓存结果（只缓存快速响应的结果）
            if use_cache and elapsed_time < timeout * 0.8:
                self.set_cache(query, result, context)
            
            return result
            
        except asyncio.TimeoutError:
            self.stats["timeout_count"] += 1
            logger.warning(f"执行超时: {query} (timeout={timeout}s)")
            raise
        except Exception as e:
            logger.error(f"执行错误: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total = self.stats["total_requests"]
        cache_hit_rate = (
            self.stats["cache_hits"] / total
            if total > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.stats["cache_hits"] = 0
        self.stats["cache_misses"] = 0


# 全局优化器实例
response_time_optimizer = ResponseTimeOptimizer()

