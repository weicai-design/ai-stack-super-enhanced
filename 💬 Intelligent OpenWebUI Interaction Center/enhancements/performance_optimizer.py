"""
性能优化模块
提供缓存和并发控制
"""
import time
from typing import Any, Optional, Callable
from functools import wraps
import hashlib


class SimpleCache:
    """简单的内存缓存"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl  # 存活时间（秒）
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            # 检查是否过期
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # 过期，删除
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        # 如果缓存满了，删除最旧的
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
    
    def make_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()


# 全局缓存实例
rag_cache = SimpleCache(max_size=200, ttl=300)  # RAG结果缓存5分钟
model_cache = SimpleCache(max_size=50, ttl=600)  # 模型响应缓存10分钟


def cache_result(cache_instance: SimpleCache, ttl: Optional[int] = None):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_instance.make_key(*args, **kwargs)
            
            # 尝试从缓存获取
            cached = cache_instance.get(cache_key)
            if cached is not None:
                return cached
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 保存到缓存
            cache_instance.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

