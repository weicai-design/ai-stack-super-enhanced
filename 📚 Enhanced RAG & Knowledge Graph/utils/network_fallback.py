"""
Network Fallback Strategy
网络降级策略

无VPN环境下的网络请求降级处理
"""

import logging
import time
from typing import Any, Callable, Optional, Tuple, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def with_network_fallback(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    fallback_value: Any = None,
    silent_fail: bool = False,
):
    """
    网络请求降级装饰器
    
    如果网络请求失败，自动重试，最终使用降级值或抛出异常
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        fallback_value: 降级返回值（如果为None，抛出异常）
        silent_fail: 是否静默失败（记录日志但不抛出异常）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    
                    # 判断是否是网络相关错误
                    is_network_error = any(keyword in error_msg.lower() for keyword in [
                        "connection", "timeout", "network", "resolve", "unreachable",
                        "连接", "超时", "网络", "无法访问"
                    ])
                    
                    if is_network_error and attempt < max_retries - 1:
                        delay = retry_delay * (attempt + 1)  # 指数退避
                        logger.warning(
                            f"网络请求失败（尝试 {attempt + 1}/{max_retries}）: {error_msg[:100]}"
                        )
                        logger.info(f"等待 {delay:.1f} 秒后重试...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"网络请求失败: {error_msg}")
                        break
            
            # 所有重试都失败
            if fallback_value is not None:
                logger.warning(f"网络请求失败，使用降级值: {fallback_value}")
                return fallback_value
            
            if silent_fail:
                logger.error(f"网络请求失败（静默）: {last_error}")
                return None
            
            if last_error:
                raise last_error
            
            raise RuntimeError("网络请求失败，无更多信息")
        
        return wrapper
    return decorator


def safe_http_request(
    request_func: Callable,
    *args,
    max_retries: int = 3,
    timeout: float = 30.0,
    **kwargs,
) -> Optional[Any]:
    """
    安全的HTTP请求（带重试和超时）
    
    Args:
        request_func: 请求函数（如httpx.get, requests.get等）
        *args: 请求函数的参数
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        **kwargs: 请求函数的关键字参数
        
    Returns:
        请求结果，失败返回None
    """
    kwargs.setdefault("timeout", timeout)
    
    for attempt in range(max_retries):
        try:
            return request_func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            is_network_error = any(keyword in error_msg.lower() for keyword in [
                "connection", "timeout", "network", "resolve", "unreachable"
            ])
            
            if is_network_error and attempt < max_retries - 1:
                delay = 1.0 * (attempt + 1)
                logger.warning(f"HTTP请求失败（尝试 {attempt + 1}/{max_retries}），{delay:.1f}秒后重试...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"HTTP请求失败: {error_msg[:200]}")
                return None
    
    return None


def test_mirror_connectivity(mirror: str) -> bool:
    """
    测试镜像连通性
    
    Args:
        mirror: 镜像URL
        
    Returns:
        是否可访问
    """
    try:
        import socket
        from urllib.parse import urlparse
        
        parsed = urlparse(mirror)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        
        return result == 0
    except Exception:
        return False

