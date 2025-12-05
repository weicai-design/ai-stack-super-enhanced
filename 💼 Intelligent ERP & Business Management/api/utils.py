"""
ERP API Utilities
ERP API工具函数

生产级API工具和缓存管理
"""

import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from fastapi import HTTPException


# 简单的内存缓存实现
class APICache:
    """API缓存管理器"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{func_name}:{str(args)}:{str(kwargs)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _clean_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, value in self._cache.items()
            if value["expires"] < current_time
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        self._clean_expired()
        
        if key in self._cache:
            item = self._cache[key]
            return item["value"]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        self._clean_expired()
        
        # 检查缓存大小
        if len(self._cache) >= self.max_size:
            # 删除最旧的缓存项
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created"])
            del self._cache[oldest_key]
        
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            "value": value,
            "created": time.time(),
            "expires": time.time() + ttl
        }
    
    def delete(self, key: str):
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()


# 全局缓存实例
api_cache = APICache()


def cache_response(ttl: int = 300):
    """缓存API响应装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = api_cache._generate_key(func.__name__, *args, **kwargs)
            
            # 检查缓存
            cached_result = api_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            api_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """根据模式删除缓存项"""
    keys_to_delete = [key for key in api_cache._cache.keys() if pattern in key]
    for key in keys_to_delete:
        api_cache.delete(key)


class APIResponse:
    """标准化的API响应类"""
    
    @staticmethod
    def success(
        data: Any = None, 
        message: str = "操作成功",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """成功响应"""
        response = {
            "success": True,
            "message": message,
            "timestamp": time.time(),
            "data": data
        }
        
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    @staticmethod
    def error(
        message: str = "操作失败",
        error_code: str = None,
        details: Any = None
    ) -> Dict[str, Any]:
        """错误响应"""
        response = {
            "success": False,
            "message": message,
            "timestamp": time.time(),
            "error_code": error_code
        }
        
        if details:
            response["details"] = details
            
        return response
    
    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "查询成功"
    ) -> Dict[str, Any]:
        """分页响应"""
        return {
            "success": True,
            "message": message,
            "timestamp": time.time(),
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        }


def validate_pagination_params(page: int, page_size: int) -> tuple[int, int]:
    """验证分页参数"""
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于0")
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="每页大小必须在1-100之间")
    
    return page, page_size


def build_pagination_query(query, model, page: int, page_size: int):
    """构建分页查询"""
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def format_datetime(dt) -> Optional[str]:
    """格式化日期时间"""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)


def sanitize_input(data: Any) -> Any:
    """清理输入数据"""
    if isinstance(data, str):
        # 移除潜在的恶意字符
        data = data.replace('<', '&lt;').replace('>', '&gt;')
        data = data.replace('"', '&quot;').replace("'", '&#x27;')
        return data.strip()
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data


def measure_execution_time(func: Callable) -> Callable:
    """测量函数执行时间装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            # 记录执行时间（可以发送到监控系统）
            print(f"Function {func.__name__} executed in {execution_time:.3f}s")
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """失败重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
                    else:
                        raise last_exception
            return None
        return wrapper
    return decorator


# 导入asyncio用于重试装饰器
import asyncio