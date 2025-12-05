"""
T013和T014模块限流熔断器
实现生产级限流和熔断机制，提升系统稳定性
"""

import time
import threading
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"      # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class RateLimitExceeded(Exception):
    """限流异常"""
    pass


class CircuitOpen(Exception):
    """熔断器打开异常"""
    pass


@dataclass
class CircuitMetrics:
    """熔断器指标"""
    total_requests: int = 0
    failed_requests: int = 0
    success_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class RateLimiter:
    """限流器"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self.lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        尝试获取请求许可
        
        Returns:
            bool: 是否允许请求
        """
        with self.lock:
            current_time = time.time()
            
            # 清理过期的请求记录
            cutoff_time = current_time - self.window_seconds
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                return False
            
            # 记录当前请求
            self.requests.append(current_time)
            return True
    
    def get_remaining_requests(self) -> int:
        """获取剩余请求数"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            return max(0, self.max_requests - len(self.requests))


class CircuitBreaker:
    """熔断器"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_requests: int = 3
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间（秒）
            half_open_max_requests: 半开状态最大请求数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.last_state_change = datetime.now()
        self.half_open_attempts = 0
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行受保护的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            CircuitOpen: 熔断器打开时抛出
        """
        with self.lock:
            # 检查熔断器状态
            if self.state == CircuitState.OPEN:
                if self._should_try_recovery():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    self.last_state_change = datetime.now()
                else:
                    raise CircuitOpen("Circuit breaker is OPEN")
            
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_attempts >= self.half_open_max_requests:
                    raise CircuitOpen("Circuit breaker is HALF_OPEN and reached max attempts")
        
        # 执行函数
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_try_recovery(self) -> bool:
        """检查是否应该尝试恢复"""
        if self.state != CircuitState.OPEN:
            return False
        
        recovery_time = self.last_state_change + timedelta(seconds=self.recovery_timeout)
        return datetime.now() >= recovery_time
    
    def _on_success(self):
        """成功回调"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.success_requests += 1
            self.metrics.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_attempts += 1
                
                # 如果半开状态下连续成功，则关闭熔断器
                if self.half_open_attempts >= self.half_open_max_requests:
                    self.state = CircuitState.CLOSED
                    self.metrics.failed_requests = 0
                    self.last_state_change = datetime.now()
    
    def _on_failure(self):
        """失败回调"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态下失败，重新打开熔断器
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
            
            elif (self.state == CircuitState.CLOSED and 
                  self.metrics.failed_requests >= self.failure_threshold):
                # 达到失败阈值，打开熔断器
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state
    
    def get_metrics(self) -> CircuitMetrics:
        """获取指标"""
        return self.metrics


class CircuitBreakerManager:
    """熔断器管理器"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """获取或创建熔断器"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(**kwargs)
            return self.breakers[name]
    
    def get_rate_limiter(self, name: str, max_requests: int, window_seconds: int) -> RateLimiter:
        """获取或创建限流器"""
        with self.lock:
            if name not in self.rate_limiters:
                self.rate_limiters[name] = RateLimiter(max_requests, window_seconds)
            return self.rate_limiters[name]
    
    def call_with_protection(
        self, 
        name: str, 
        func: Callable, 
        *args, 
        rate_limit: Optional[tuple] = None,
        **kwargs
    ) -> Any:
        """
        使用熔断和限流保护执行函数
        
        Args:
            name: 服务名称
            func: 要执行的函数
            rate_limit: 限流配置 (max_requests, window_seconds)
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Any: 函数执行结果
        """
        # 限流检查
        if rate_limit:
            max_requests, window_seconds = rate_limit
            limiter = self.get_rate_limiter(name, max_requests, window_seconds)
            
            if not limiter.acquire():
                raise RateLimitExceeded(f"Rate limit exceeded for {name}")
        
        # 熔断保护
        breaker = self.get_breaker(name)
        return breaker.call(func, *args, **kwargs)
    
    def get_all_breakers(self) -> Dict[str, CircuitBreaker]:
        """获取所有熔断器"""
        return self.breakers.copy()
    
    def get_all_rate_limiters(self) -> Dict[str, RateLimiter]:
        """获取所有限流器"""
        return self.rate_limiters.copy()


# 全局熔断器管理器实例
circuit_manager = CircuitBreakerManager()


def circuit_breaker(name: str, **breaker_kwargs):
    """熔断器装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return circuit_manager.call_with_protection(name, func, *args, **breaker_kwargs)
        return wrapper
    return decorator


def rate_limit(name: str, max_requests: int, window_seconds: int):
    """限流装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return circuit_manager.call_with_protection(
                name, func, *args, rate_limit=(max_requests, window_seconds), **kwargs
            )
        return wrapper
    return decorator