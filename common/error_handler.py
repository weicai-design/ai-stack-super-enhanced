"""
统一错误处理模块
所有服务共用的错误处理机制
"""

from typing import Optional, Dict, Any
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)


# ==================== 错误代码定义 ====================

class ErrorCode:
    """统一错误代码"""
    
    # 通用错误 (1000-1999)
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    INVALID_PARAMETER = 1001
    MISSING_PARAMETER = 1002
    INVALID_REQUEST = 1003
    
    # 认证授权错误 (2000-2999)
    UNAUTHORIZED = 2000
    FORBIDDEN = 2001
    TOKEN_EXPIRED = 2002
    INVALID_TOKEN = 2003
    
    # 资源错误 (3000-3999)
    RESOURCE_NOT_FOUND = 3000
    RESOURCE_ALREADY_EXISTS = 3001
    RESOURCE_LOCKED = 3002
    
    # 业务逻辑错误 (4000-4999)
    BUSINESS_RULE_VIOLATION = 4000
    INSUFFICIENT_BALANCE = 4001
    INVALID_STATE = 4002
    OPERATION_NOT_ALLOWED = 4003
    
    # 外部服务错误 (5000-5999)
    EXTERNAL_SERVICE_ERROR = 5000
    EXTERNAL_API_TIMEOUT = 5001
    EXTERNAL_API_UNAVAILABLE = 5002
    
    # 数据库错误 (6000-6999)
    DATABASE_ERROR = 6000
    DATABASE_CONNECTION_ERROR = 6001
    DUPLICATE_KEY_ERROR = 6002
    
    # 系统错误 (7000-7999)
    SYSTEM_ERROR = 7000
    SERVICE_UNAVAILABLE = 7001
    RESOURCE_EXHAUSTED = 7002
    TIMEOUT_ERROR = 7003


# ==================== 异常类定义 ====================

class APIException(Exception):
    """API异常基类"""
    
    def __init__(
        self,
        code: int = ErrorCode.UNKNOWN_ERROR,
        message: str = "未知错误",
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 500
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = http_status
        self.timestamp = datetime.now().isoformat()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }


class ValidationError(APIException):
    """参数验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            code=ErrorCode.INVALID_PARAMETER,
            message=message,
            details=details,
            http_status=400
        )


class NotFoundError(APIException):
    """资源不存在错误"""
    
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"{resource_type} 不存在",
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
            http_status=404
        )


class BusinessError(APIException):
    """业务逻辑错误"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.BUSINESS_RULE_VIOLATION,
            message=message,
            details=details,
            http_status=400
        )


class UnauthorizedError(APIException):
    """未授权错误"""
    
    def __init__(self, message: str = "未授权访问"):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            http_status=401
        )


class ExternalServiceError(APIException):
    """外部服务错误"""
    
    def __init__(self, service_name: str, error_message: str):
        super().__init__(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"外部服务 {service_name} 调用失败",
            details={"service": service_name, "error": error_message},
            http_status=503
        )


class DatabaseError(APIException):
    """数据库错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            details=details,
            http_status=500
        )


# ==================== 错误处理器 ====================

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_exception(exc: Exception) -> Dict[str, Any]:
        """
        处理异常，返回标准格式的错误响应
        
        Args:
            exc: 异常对象
            
        Returns:
            错误响应字典
        """
        # 如果是API异常，直接返回
        if isinstance(exc, APIException):
            logger.warning(f"API异常: {exc.code} - {exc.message}")
            return exc.to_dict()
        
        # 其他异常，记录详细信息
        error_trace = traceback.format_exc()
        logger.error(f"未处理的异常: {exc}")
        logger.error(error_trace)
        
        return {
            "success": False,
            "error": {
                "code": ErrorCode.UNKNOWN_ERROR,
                "message": "系统内部错误",
                "details": {
                    "type": type(exc).__name__,
                    "message": str(exc)
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def create_success_response(
        data: Any,
        message: str = "操作成功"
    ) -> Dict[str, Any]:
        """
        创建成功响应
        
        Args:
            data: 响应数据
            message: 成功消息
            
        Returns:
            成功响应字典
        """
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }


# ==================== FastAPI 中间件 ====================

from fastapi import Request, status
from fastapi.responses import JSONResponse


async def error_handler_middleware(request: Request, call_next):
    """
    FastAPI错误处理中间件
    
    捕获所有未处理的异常并返回标准格式
    """
    try:
        response = await call_next(request)
        return response
    except APIException as exc:
        # API异常
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict()
        )
    except Exception as exc:
        # 其他异常
        error_response = ErrorHandler.handle_exception(exc)
        return JSONResponse(
            status_code=500,
            content=error_response
        )


# ==================== 重试装饰器 ====================

import asyncio
from functools import wraps


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    错误重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        exponential_backoff: 是否使用指数退避
        exceptions: 需要重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"函数 {func.__name__} 执行失败（尝试 {attempt + 1}/{max_retries}），"
                            f"{current_delay}秒后重试..."
                        )
                        await asyncio.sleep(current_delay)
                        
                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        logger.error(
                            f"函数 {func.__name__} 在{max_retries}次重试后仍然失败"
                        )
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"函数 {func.__name__} 执行失败（尝试 {attempt + 1}/{max_retries}），"
                            f"{current_delay}秒后重试..."
                        )
                        import time
                        time.sleep(current_delay)
                        
                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        logger.error(
                            f"函数 {func.__name__} 在{max_retries}次重试后仍然失败"
                        )
            
            raise last_exception
        
        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


