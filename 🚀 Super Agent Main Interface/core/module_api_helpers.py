"""
模块API辅助函数
提供统一的错误处理、响应格式、请求验证和日志记录
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Callable, Awaitable
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


def standardize_response(
    data: Any,
    success: bool = True,
    message: Optional[str] = None,
    count: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """
    标准化API响应格式
    
    Args:
        data: 响应数据
        success: 是否成功
        message: 消息
        count: 总数（列表接口）
        limit: 限制（列表接口）
        offset: 偏移（列表接口）
        
    Returns:
        标准化响应
    """
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if message:
        response["message"] = message
    
    # 处理数据
    if isinstance(data, dict):
        if "data" in data:
            response["data"] = data["data"]
        elif "success" in data and "data" in data:
            # 已经是标准格式，直接使用
            response.update(data)
        else:
            response["data"] = data
    elif isinstance(data, list):
        response["data"] = data
        if count is not None:
            response["count"] = count
        if limit is not None:
            response["limit"] = limit
        if offset is not None:
            response["offset"] = offset
    else:
        response["data"] = data
    
    return response


def handle_api_error(
    error: Exception,
    operation: str,
    module: str,
    default_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    统一处理API错误
    
    Args:
        error: 异常对象
        operation: 操作名称
        module: 模块名称
        default_message: 默认错误消息
        
    Returns:
        错误响应
    """
    error_message = str(error)
    
    # 记录错误日志
    logger.error(
        f"{module}模块{operation}失败: {error_message}",
        exc_info=True,
        extra={
            "module": module,
            "operation": operation,
            "error": error_message,
        },
    )
    
    # 返回标准化错误响应
    return standardize_response(
        data={},
        success=False,
        message=default_message or f"{operation}失败: {error_message}",
    )


def validate_request(
    request: Dict[str, Any],
    required_fields: list[str],
    optional_fields: Optional[list[str]] = None,
) -> tuple[bool, Optional[str]]:
    """
    验证请求参数
    
    Args:
        request: 请求数据
        required_fields: 必需字段列表
        optional_fields: 可选字段列表
        
    Returns:
        (是否有效, 错误消息)
    """
    # 检查必需字段
    for field in required_fields:
        if field not in request or request[field] is None:
            return False, f"缺少必需字段: {field}"
    
    # 检查字段类型（可选）
    if optional_fields:
        for field in optional_fields:
            if field in request and request[field] is not None:
                # 可以在这里添加类型检查
                pass
    
    return True, None


def log_api_call(
    module: str,
    operation: str,
    request_data: Optional[Dict[str, Any]] = None,
    response_data: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
    success: bool = True,
):
    """
    记录API调用日志
    
    Args:
        module: 模块名称
        operation: 操作名称
        request_data: 请求数据
        response_data: 响应数据
        duration: 执行时长（秒）
        success: 是否成功
    """
    log_data = {
        "module": module,
        "operation": operation,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    if duration is not None:
        log_data["duration"] = duration
    
    if request_data:
        # 过滤敏感信息
        filtered_request = _filter_sensitive_data(request_data)
        log_data["request"] = filtered_request
    
    if response_data:
        # 限制响应数据大小
        if isinstance(response_data, dict) and "data" in response_data:
            # 只记录响应摘要
            log_data["response_summary"] = {
                "success": response_data.get("success"),
                "count": response_data.get("count"),
            }
        else:
            log_data["response"] = _limit_data_size(response_data)
    
    if success:
        logger.info(f"API调用: {module}.{operation}", extra=log_data)
    else:
        logger.error(f"API调用失败: {module}.{operation}", extra=log_data)


def _filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """过滤敏感数据"""
    sensitive_fields = [
        "password", "passwd", "pwd",
        "token", "api_key", "secret",
        "credit_card", "card_number",
        "ssn", "social_security",
    ]
    
    filtered = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            filtered[key] = "***MASKED***"
        elif isinstance(value, dict):
            filtered[key] = _filter_sensitive_data(value)
        elif isinstance(value, list):
            filtered[key] = [
                _filter_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            filtered[key] = value
    
    return filtered


def _limit_data_size(data: Any, max_size: int = 1000) -> Any:
    """限制数据大小"""
    if isinstance(data, str):
        return data[:max_size] + "..." if len(data) > max_size else data
    elif isinstance(data, dict):
        limited = {}
        for key, value in list(data.items())[:10]:  # 只保留前10个字段
            limited[key] = _limit_data_size(value, max_size)
        return limited
    elif isinstance(data, list):
        return [_limit_data_size(item, max_size) for item in data[:10]]  # 只保留前10项
    else:
        return data


def api_endpoint_wrapper(
    module: str,
    operation: str,
    required_fields: Optional[list[str]] = None,
):
    """
    API端点装饰器
    提供统一的错误处理、日志记录和响应格式化
    
    Args:
        module: 模块名称
        operation: 操作名称
        required_fields: 必需字段列表
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                # 验证请求（如果有request参数）
                if "request" in kwargs and required_fields:
                    request = kwargs["request"]
                    if isinstance(request, dict):
                        is_valid, error_msg = validate_request(
                            request, required_fields
                        )
                        if not is_valid:
                            return standardize_response(
                                data={},
                                success=False,
                                message=error_msg,
                            )
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 计算执行时长
                duration = time.time() - start_time
                
                # 标准化响应
                if isinstance(result, dict) and "success" in result:
                    standardized_result = result
                else:
                    standardized_result = standardize_response(data=result)
                
                # 记录日志
                log_api_call(
                    module=module,
                    operation=operation,
                    request_data=kwargs.get("request"),
                    response_data=standardized_result,
                    duration=duration,
                    success=True,
                )
                
                return standardized_result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # 记录错误日志
                log_api_call(
                    module=module,
                    operation=operation,
                    request_data=kwargs.get("request"),
                    duration=duration,
                    success=False,
                )
                
                # 返回错误响应
                return handle_api_error(e, operation, module)
        
        return wrapper
    return decorator

