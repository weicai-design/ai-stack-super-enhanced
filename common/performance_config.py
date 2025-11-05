"""
性能优化配置模块
提供各种性能优化工具和配置
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ==================== 缓存装饰器 ====================

class CacheManager:
    """简单的内存缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            item = self.cache[key]
            # 检查是否过期
            if time.time() < item["expire_at"]:
                logger.debug(f"缓存命中: {key}")
                return item["value"]
            else:
                # 删除过期项
                del self.cache[key]
                logger.debug(f"缓存过期: {key}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 简单的LRU：删除最早的项
            oldest_key = min(self.cache.items(), key=lambda x: x[1]["created_at"])[0]
            del self.cache[oldest_key]
        
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expire_at": time.time() + ttl
        }
        logger.debug(f"缓存设置: {key}, TTL={ttl}秒")
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"缓存删除: {key}")
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "total_items": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0
        }


# 全局缓存实例
global_cache = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 保存到缓存
            global_cache.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            cached_value = global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            global_cache.set(cache_key, result, ttl)
            
            return result
        
        # 根据函数类型返回对应包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 性能监控装饰器 ====================

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录性能指标"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {}
        })
        
        # 只保留最近100条
        if len(self.metrics[name]) > 100:
            self.metrics[name] = self.metrics[name][-100:]
    
    def get_metric_stats(self, name: str) -> Dict[str, Any]:
        """获取指标统计"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = [m["value"] for m in self.metrics[name]]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "recent": values[-10:]
        }


# 全局性能监控器
global_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str = None):
    """
    性能监控装饰器
    
    Args:
        metric_name: 指标名称（默认使用函数名）
    """
    def decorator(func):
        name = metric_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录成功执行时间
                global_monitor.record_metric(
                    f"{name}_duration",
                    duration_ms,
                    {"status": "success"}
                )
                
                # 记录慢操作
                if duration_ms > 1000:
                    logger.warning(f"慢操作: {name} 耗时 {duration_ms:.2f}ms")
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录失败执行时间
                global_monitor.record_metric(
                    f"{name}_duration",
                    duration_ms,
                    {"status": "error"}
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                global_monitor.record_metric(
                    f"{name}_duration",
                    duration_ms,
                    {"status": "success"}
                )
                
                if duration_ms > 1000:
                    logger.warning(f"慢操作: {name} 耗时 {duration_ms:.2f}ms")
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                global_monitor.record_metric(
                    f"{name}_duration",
                    duration_ms,
                    {"status": "error"}
                )
                
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== 性能配置 ====================

class PerformanceConfig:
    """性能配置"""
    
    # API配置
    API_TIMEOUT = 30  # API超时时间（秒）
    API_MAX_RETRIES = 3  # API最大重试次数
    API_RATE_LIMIT = 100  # 每分钟请求限制
    
    # 数据库配置
    DB_POOL_SIZE = 10  # 连接池大小
    DB_MAX_OVERFLOW = 20  # 最大溢出连接
    DB_POOL_TIMEOUT = 30  # 连接池超时
    DB_ECHO = False  # 是否打印SQL
    
    # 缓存配置
    CACHE_ENABLED = True  # 是否启用缓存
    CACHE_DEFAULT_TTL = 300  # 默认缓存时间（秒）
    CACHE_MAX_SIZE = 1000  # 最大缓存条目
    
    # 任务配置
    TASK_QUEUE_SIZE = 100  # 任务队列大小
    TASK_WORKER_COUNT = 4  # 工作线程数
    TASK_TIMEOUT = 600  # 任务超时（秒）
    
    # 文件上传配置
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = [
        'pdf', 'doc', 'docx', 'txt', 'md',
        'jpg', 'jpeg', 'png', 'gif',
        'mp3', 'wav', 'mp4', 'avi'
    ]
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith('_') and key.isupper()
        }


# ==================== 性能优化工具 ====================

class PerformanceOptimizer:
    """性能优化工具"""
    
    @staticmethod
    def batch_process(items: list, batch_size: int = 100):
        """批处理生成器"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    @staticmethod
    async def parallel_execute(tasks: list, max_concurrent: int = 10):
        """并行执行任务（限制并发数）"""
        results = []
        
        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    @staticmethod
    def compress_response(data: str, min_size: int = 1024) -> bytes:
        """压缩响应数据"""
        import gzip
        
        if len(data) < min_size:
            return data.encode('utf-8')
        
        return gzip.compress(data.encode('utf-8'))


