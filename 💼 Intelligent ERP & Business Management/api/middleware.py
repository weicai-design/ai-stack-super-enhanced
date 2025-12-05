"""
ERP API Middleware and Error Handling
ERP API中间件和错误处理

生产级API性能优化和错误处理机制 - T0006-3增强版 + T0006-4性能监控集成
"""

import time
import logging
import traceback
import asyncio
import redis
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import contextmanager
from functools import wraps
import json

# 导入性能监控系统 - T0006-4
from .performance_monitor import record_api_performance, get_performance_monitor

# 配置日志记录器
logger = logging.getLogger("erp_api")

# Redis缓存客户端（可选）
redis_client: Optional[redis.Redis] = None

try:
    redis_client = redis.Redis(
        host='localhost', 
        port=6379, 
        db=0, 
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    # 测试连接
    redis_client.ping()
    logger.info("✅ Redis缓存已连接")
except Exception as e:
    logger.warning(f"❌ Redis连接失败: {e}, 将使用内存缓存")
    redis_client = None


class PerformanceMiddleware(BaseHTTPMiddleware):
    """增强版性能监控中间件 - T0006-3优化 + T0006-4性能监控集成"""
    
    def __init__(self, app, enable_metrics: bool = True, enable_cache: bool = True, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.enable_metrics = enable_metrics
        self.enable_cache = enable_cache
        self.redis_client = redis_client
        
        # 初始化性能监控器 - T0006-4
        self.performance_monitor = get_performance_monitor(redis_client)
        
        # 传统统计信息（向后兼容）
        self.request_stats = {
            "total_requests": 0,
            "slow_requests": 0,
            "error_requests": 0,
            "avg_response_time": 0.0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录性能指标 - T0006-4集成版本"""
        start_time = time.time()
        
        # 请求标识
        request_id = f"{int(start_time * 1000)}_{request.method}_{request.url.path}"
        
        # 检查缓存（如果启用）
        cache_key = None
        if self.enable_cache and self.redis_client and request.method == "GET":
            cache_key = f"api_cache:{request_id}"
            try:
                cached_response = self.redis_client.get(cache_key)
                if cached_response:
                    logger.info(f"📦 缓存命中: {request.url.path}")
                    
                    # 记录缓存命中性能指标 - T0006-4
                    if self.enable_metrics:
                        record_api_performance(
                            endpoint=request.url.path,
                            method=request.method,
                            response_time=0.001,  # 缓存命中响应时间极短
                            status_code=200,
                            cache_hit=True
                        )
                    
                    return JSONResponse(content=json.loads(cached_response))
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 记录响应时间
            response_time = time.time() - start_time
            
            # 更新统计信息
            self.request_stats["total_requests"] += 1
            self.request_stats["avg_response_time"] = (
                (self.request_stats["avg_response_time"] * (self.request_stats["total_requests"] - 1) + response_time) / 
                self.request_stats["total_requests"]
            )
            
            # 记录慢请求
            if response_time > 2.0:  # 超过2秒视为慢请求
                self.request_stats["slow_requests"] += 1
                logger.warning(f"🐌 慢请求: {request.url.path} - {response_time:.2f}s")
            
            # 缓存响应（如果启用）
            if self.enable_cache and cache_key and self.redis_client and response.status_code == 200:
                try:
                    # 只缓存成功的GET请求
                    if hasattr(response, 'body'):
                        self.redis_client.setex(cache_key, 300, response.body.decode())  # 缓存5分钟
                        logger.info(f"💾 缓存写入: {request.url.path}")
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")
            
            # 记录性能指标 - T0006-4集成
            if self.enable_metrics:
                logger.info(f"📊 请求完成: {request.url.path} - {response_time:.3f}s")
                
                # 使用新的性能监控系统记录指标
                record_api_performance(
                    endpoint=request.url.path,
                    method=request.method,
                    response_time=response_time,
                    status_code=response.status_code,
                    cache_hit=False
                )
            
            return response
            
        except Exception as e:
            # 记录错误
            response_time = time.time() - start_time
            self.request_stats["error_requests"] += 1
            
            logger.error(f"❌ 请求错误: {request.url.path} - {str(e)}")
            logger.error(traceback.format_exc())
            
            # 记录错误性能指标 - T0006-4
            if self.enable_metrics:
                record_api_performance(
                    endpoint=request.url.path,
                    method=request.method,
                    response_time=response_time,
                    status_code=500,
                    cache_hit=False,
                    error_type=type(e).__name__
                )
            
            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "服务器内部错误，请稍后重试",
                    "request_id": request_id
                }
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """增强版全局错误处理中间件 - T0006-3优化"""
    
    def __init__(self, app, enable_recovery: bool = True, retry_count: int = 0):
        super().__init__(app)
        self.enable_recovery = enable_recovery
        self.retry_count = retry_count
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 错误分类和恢复机制
        retry_attempts = 0
        
        while retry_attempts <= self.retry_count:
            try:
                response = await call_next(request)
                return response
            except HTTPException as e:
                # FastAPI的HTTP异常直接抛出
                logger.warning(
                    f"HTTP Exception - Method: {request.method}, Path: {request.url.path}, "
                    f"Status: {e.status_code}, Detail: {e.detail}"
                )
                raise
            except ConnectionError as e:
                # 连接错误（数据库、外部API等）
                error_id = f"CONN-{int(time.time())}"
                logger.error(
                    f"Connection Error - ID: {error_id}, Method: {request.method}, "
                    f"Path: {request.url.path}, Error: {str(e)}, Attempt: {retry_attempts}"
                )
                
                if retry_attempts < self.retry_count and self.enable_recovery:
                    retry_attempts += 1
                    await asyncio.sleep(1)  # 等待1秒后重试
                    continue
                
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service Unavailable",
                        "error_id": error_id,
                        "message": "服务暂时不可用，请稍后重试",
                        "retry_after": 30,
                        "timestamp": time.time()
                    }
                )
            except TimeoutError as e:
                # 超时错误
                error_id = f"TIMEOUT-{int(time.time())}"
                logger.error(
                    f"Timeout Error - ID: {error_id}, Method: {request.method}, "
                    f"Path: {request.url.path}, Error: {str(e)}, Attempt: {retry_attempts}"
                )
                
                if retry_attempts < self.retry_count and self.enable_recovery:
                    retry_attempts += 1
                    await asyncio.sleep(2)  # 等待2秒后重试
                    continue
                
                return JSONResponse(
                    status_code=504,
                    content={
                        "error": "Gateway Timeout",
                        "error_id": error_id,
                        "message": "请求超时，请稍后重试",
                        "timeout": 30,
                        "timestamp": time.time()
                    }
                )
            except ValueError as e:
                # 数据验证错误
                error_id = f"VALIDATION-{int(time.time())}"
                logger.warning(
                    f"Validation Error - ID: {error_id}, Method: {request.method}, "
                    f"Path: {request.url.path}, Error: {str(e)}"
                )
                
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Bad Request",
                        "error_id": error_id,
                        "message": "输入数据格式错误",
                        "details": str(e),
                        "timestamp": time.time()
                    }
                )
            except Exception as e:
                # 其他未处理异常
                error_id = f"UNHANDLED-{int(time.time())}"
                logger.error(
                    f"Unhandled API Error - ID: {error_id}, Method: {request.method}, "
                    f"Path: {request.url.path}, Error: {str(e)}, Traceback: {traceback.format_exc()}"
                )
                
                if retry_attempts < self.retry_count and self.enable_recovery:
                    retry_attempts += 1
                    await asyncio.sleep(1)  # 等待1秒后重试
                    continue
                
                # 返回标准化的错误响应
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal Server Error",
                        "error_id": error_id,
                        "message": "服务器内部错误，请稍后重试",
                        "timestamp": time.time()
                    }
                )
        
        # 如果所有重试都失败
        error_id = f"FATAL-{int(time.time())}"
        logger.critical(
            f"Fatal API Error - ID: {error_id}, Method: {request.method}, "
            f"Path: {request.url.path}, All retry attempts failed"
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Service Unavailable",
                "error_id": error_id,
                "message": "服务暂时不可用，请稍后联系管理员",
                "timestamp": time.time()
            }
        )


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """增强版智能速率限制中间件 - T0006-3优化"""
    
    def __init__(self, app, 
                 max_requests: int = 100, 
                 window_seconds: int = 60,
                 burst_limit: int = 20,
                 enable_redis: bool = False,
                 redis_client = None):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_limit = burst_limit
        self.enable_redis = enable_redis
        self.redis_client = redis_client
        
        # 本地内存存储（用于单机模式）
        self.request_counts = {}
        self.burst_counts = {}
        
        # 智能限流策略：不同API路径的不同限制
        self.api_limits = {
            "/api/customer/": {"max_requests": 200, "window_seconds": 60},
            "/api/order/": {"max_requests": 150, "window_seconds": 60},
            "/api/inventory/": {"max_requests": 100, "window_seconds": 60},
            "/api/finance/": {"max_requests": 50, "window_seconds": 60},
            "/api/production/": {"max_requests": 80, "window_seconds": 60},
            "/api/quality/": {"max_requests": 120, "window_seconds": 60}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        api_path = request.url.path
        
        # 获取特定API路径的限制配置
        api_limit = self._get_api_limit(api_path)
        max_requests = api_limit.get("max_requests", self.max_requests)
        window_seconds = api_limit.get("window_seconds", self.window_seconds)
        
        # 分布式限流（如果启用Redis）
        if self.enable_redis and self.redis_client:
            return await self._distributed_rate_limit(
                client_ip, api_path, max_requests, window_seconds, request, call_next
            )
        else:
            # 本地内存限流
            return await self._local_rate_limit(
                client_ip, api_path, max_requests, window_seconds, request, call_next
            )
    
    async def _distributed_rate_limit(self, client_ip: str, api_path: str, 
                                     max_requests: int, window_seconds: int,
                                     request: Request, call_next: Callable) -> Response:
        """分布式速率限制（Redis支持）"""
        current_time = time.time()
        redis_key = f"rate_limit:{client_ip}:{api_path}"
        
        try:
            # 使用Redis有序集合实现滑动窗口
            pipeline = self.redis_client.pipeline()
            pipeline.zadd(redis_key, {str(current_time): current_time})
            pipeline.zremrangebyscore(redis_key, 0, current_time - window_seconds)
            pipeline.zcard(redis_key)
            pipeline.expire(redis_key, window_seconds)
            
            results = pipeline.execute()
            request_count = results[2]
            
            if request_count > max_requests:
                # 计算剩余时间
                oldest_request = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest_request:
                    oldest_time = oldest_request[0][1]
                    retry_after = int(window_seconds - (current_time - oldest_time))
                else:
                    retry_after = window_seconds
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": f"请求过于频繁，请{retry_after}秒后再试",
                        "retry_after": retry_after,
                        "current_requests": request_count,
                        "max_requests": max_requests
                    }
                )
            
            # 继续处理请求
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Redis rate limiting failed: {str(e)}")
            # Redis失败时降级到本地限流
            return await self._local_rate_limit(
                client_ip, api_path, max_requests, window_seconds, request, call_next
            )
    
    async def _local_rate_limit(self, client_ip: str, api_path: str,
                               max_requests: int, window_seconds: int,
                               request: Request, call_next: Callable) -> Response:
        """本地内存速率限制"""
        current_time = time.time()
        client_key = f"{client_ip}:{api_path}"
        
        # 清理过期记录
        self._cleanup_expired_records(current_time, window_seconds)
        
        # 获取或初始化客户端请求计数
        if client_key not in self.request_counts:
            self.request_counts[client_key] = []
        
        # 检查突发流量限制
        if client_key not in self.burst_counts:
            self.burst_counts[client_key] = {"count": 0, "last_reset": current_time}
        
        burst_info = self.burst_counts[client_key]
        
        # 每5秒重置突发计数
        if current_time - burst_info["last_reset"] > 5:
            burst_info["count"] = 0
            burst_info["last_reset"] = current_time
        
        # 检查突发限制
        burst_info["count"] += 1
        if burst_info["count"] > self.burst_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Burst Limit Exceeded",
                    "message": "突发流量超过限制，请稍后重试",
                    "retry_after": 5
                }
            )
        
        # 添加当前请求时间
        self.request_counts[client_key].append(current_time)
        
        # 检查是否超过限制
        recent_requests = [t for t in self.request_counts[client_key] 
                          if current_time - t <= window_seconds]
        
        if len(recent_requests) > max_requests:
            # 计算最早的有效请求时间
            oldest_valid_time = current_time - window_seconds
            valid_requests = [t for t in recent_requests if t > oldest_valid_time]
            
            if valid_requests:
                oldest_request = min(valid_requests)
                retry_after = int(window_seconds - (current_time - oldest_request))
            else:
                retry_after = window_seconds
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"请求过于频繁，请{retry_after}秒后再试",
                    "retry_after": retry_after,
                    "current_requests": len(recent_requests),
                    "max_requests": max_requests
                }
            )
        
        # 更新请求计数
        self.request_counts[client_key] = recent_requests
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加速率限制头信息
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max_requests - len(recent_requests))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + window_seconds))
        
        return response
    
    def _get_api_limit(self, api_path: str) -> dict:
        """获取特定API路径的限制配置"""
        for path_prefix, limit_config in self.api_limits.items():
            if api_path.startswith(path_prefix):
                return limit_config
        return {"max_requests": self.max_requests, "window_seconds": self.window_seconds}
    
    def _cleanup_expired_records(self, current_time: float, window_seconds: int):
        """清理过期记录"""
        expired_keys = []
        for key, timestamps in self.request_counts.items():
            valid_timestamps = [t for t in timestamps 
                               if current_time - t <= window_seconds]
            if not valid_timestamps:
                expired_keys.append(key)
            else:
                self.request_counts[key] = valid_timestamps
        
        for key in expired_keys:
            del self.request_counts[key]
            if key in self.burst_counts:
                del self.burst_counts[key]


@contextmanager
def api_performance_monitor(endpoint_name: str):
    """API性能监控上下文管理器"""
    start_time = time.time()
    try:
        yield
    finally:
        process_time = time.time() - start_time
        if process_time > 1.0:
            logger.warning(f"Slow API Endpoint - {endpoint_name}: {process_time:.3f}s")
        elif process_time > 0.5:
            logger.info(f"API Endpoint - {endpoint_name}: {process_time:.3f}s")


def create_error_response(
    status_code: int, 
    message: str, 
    error_type: str = None,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """创建标准化的错误响应"""
    error_id = f"ERR-{int(time.time())}"
    
    response_content = {
        "error": error_type or "API Error",
        "error_id": error_id,
        "message": message,
        "timestamp": time.time()
    }
    
    if details:
        response_content["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=response_content
    )


def validate_api_input(data: Any, validation_rules: Dict[str, Callable]) -> Dict[str, Any]:
    """API输入验证工具"""
    errors = {}
    
    for field, validator in validation_rules.items():
        try:
            if hasattr(data, field):
                value = getattr(data, field)
                validator(value)
        except Exception as e:
            errors[field] = str(e)
    
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation Error",
                "message": "输入数据验证失败",
                "validation_errors": errors
            }
        )
    
    return data


# 常用的验证规则
VALIDATION_RULES = {
    "positive_number": lambda x: x > 0 or ValueError("必须为正数"),
    "non_empty_string": lambda x: len(str(x).strip()) > 0 or ValueError("不能为空"),
    "valid_date": lambda x: isinstance(x, str) and len(x) == 10 or ValueError("日期格式无效"),
    "valid_email": lambda x: "@" in str(x) or ValueError("邮箱格式无效"),
}