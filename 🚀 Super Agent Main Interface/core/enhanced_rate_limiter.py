"""
增强智能限流器系统
实现自适应限流、优先级管理、动态配额分配和智能限流策略
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import logging
import hashlib

logger = logging.getLogger(__name__)


class RateLimitPriority(Enum):
    """限流优先级"""
    LOW = "low"  # 低优先级
    NORMAL = "normal"  # 正常优先级
    HIGH = "high"  # 高优先级
    CRITICAL = "critical"  # 关键优先级


class RateLimitAlgorithm(Enum):
    """限流算法"""
    TOKEN_BUCKET = "token_bucket"  # 令牌桶算法
    LEAKY_BUCKET = "leaky_bucket"  # 漏桶算法
    SLIDING_WINDOW = "sliding_window"  # 滑动窗口算法
    ADAPTIVE = "adaptive"  # 自适应算法


@dataclass
class RateLimitConfig:
    """限流配置"""
    max_requests: int  # 最大请求数
    time_window: int  # 时间窗口（秒）
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    priority: RateLimitPriority = RateLimitPriority.NORMAL
    burst_capacity: Optional[int] = None  # 突发容量
    recovery_rate: Optional[float] = None  # 恢复速率


@dataclass
class RateLimitMetrics:
    """限流指标"""
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    wait_time: float = 0.0
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
    
    def record_request(self, allowed: bool, wait_time: float = 0.0, response_time: float = 0.0):
        """记录请求"""
        self.total_requests += 1
        if allowed:
            self.allowed_requests += 1
            self.response_times.append(response_time)
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
        else:
            self.rejected_requests += 1
        self.wait_time += wait_time
    
    def get_rejection_rate(self) -> float:
        """获取拒绝率"""
        if self.total_requests == 0:
            return 0.0
        return self.rejected_requests / self.total_requests
    
    def get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    def get_avg_wait_time(self) -> float:
        """获取平均等待时间"""
        if self.allowed_requests == 0:
            return 0.0
        return self.wait_time / self.allowed_requests


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶
        
        Args:
            capacity: 桶容量
            refill_rate: 令牌填充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill_time = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, wait: bool = True) -> Tuple[bool, float]:
        """
        获取令牌
        
        Args:
            tokens: 需要的令牌数
            wait: 是否等待
        
        Returns:
            Tuple[bool, float]: (是否成功, 等待时间)
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            
            if wait:
                # 计算需要等待的时间
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate
                return False, wait_time
            
            return False, 0.0
    
    def _refill(self):
        """填充令牌"""
        current_time = time.time()
        time_passed = current_time - self.last_refill_time
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = current_time


class AdaptiveRateLimiter:
    """自适应限流器"""
    
    def __init__(
        self,
        name: str,
        base_config: RateLimitConfig,
        adaptive_factor: float = 0.1,
        load_sensitive: bool = True
    ):
        """
        初始化自适应限流器
        
        Args:
            name: 限流器名称
            base_config: 基础配置
            adaptive_factor: 自适应因子
            load_sensitive: 是否负载敏感
        """
        self.name = name
        self.base_config = base_config
        self.adaptive_factor = adaptive_factor
        self.load_sensitive = load_sensitive
        
        # 指标跟踪
        self.metrics = RateLimitMetrics()
        self.historical_metrics = []
        
        # 令牌桶
        self.token_bucket = TokenBucket(
            capacity=base_config.max_requests,
            refill_rate=base_config.max_requests / base_config.time_window
        )
        
        # 系统负载
        self.current_load = 0.0
        self.last_load_update = datetime.now()
        
        self.lock = threading.Lock()
    
    def get_dynamic_limit(self) -> int:
        """获取动态限制"""
        if not self.load_sensitive:
            return self.base_config.max_requests
        
        # 基于系统负载调整限制
        load_factor = max(0.5, min(2.0, 1.0 / max(0.1, self.current_load)))
        
        # 基于历史拒绝率调整
        if len(self.historical_metrics) >= 5:
            recent_rejection_rates = [m.get_rejection_rate() for m in self.historical_metrics[-5:]]
            avg_rejection_rate = statistics.mean(recent_rejection_rates)
            
            # 如果拒绝率较高，增加限制
            if avg_rejection_rate > 0.1:
                load_factor *= (1 + self.adaptive_factor)
            # 如果拒绝率较低，减少限制（更严格）
            elif avg_rejection_rate < 0.01:
                load_factor *= (1 - self.adaptive_factor)
        
        dynamic_limit = int(self.base_config.max_requests * load_factor)
        return max(1, dynamic_limit)
    
    def update_system_load(self, load: float):
        """更新系统负载"""
        self.current_load = load
        self.last_load_update = datetime.now()
    
    def acquire(self, priority: RateLimitPriority = RateLimitPriority.NORMAL, 
               tokens: int = 1) -> Tuple[bool, float]:
        """
        获取限流许可
        
        Args:
            priority: 请求优先级
            tokens: 需要的令牌数
        
        Returns:
            Tuple[bool, float]: (是否允许, 等待时间)
        """
        start_time = time.time()
        
        # 根据优先级调整令牌需求
        adjusted_tokens = self._adjust_tokens_by_priority(tokens, priority)
        
        # 获取动态限制
        dynamic_limit = self.get_dynamic_limit()
        
        # 更新令牌桶配置
        self._update_token_bucket(dynamic_limit)
        
        # 尝试获取令牌
        success, wait_time = self.token_bucket.acquire(adjusted_tokens, wait=False)
        
        # 记录指标
        response_time = time.time() - start_time
        self.metrics.record_request(success, wait_time, response_time)
        
        # 定期更新历史指标
        if self.metrics.total_requests % 100 == 0:
            self.historical_metrics.append(self.metrics)
            if len(self.historical_metrics) > 10:
                self.historical_metrics = self.historical_metrics[-10:]
            # 创建新的指标对象
            self.metrics = RateLimitMetrics()
        
        return success, wait_time
    
    def _adjust_tokens_by_priority(self, tokens: int, priority: RateLimitPriority) -> int:
        """根据优先级调整令牌需求"""
        priority_factors = {
            RateLimitPriority.LOW: 1.5,      # 低优先级需要更多令牌
            RateLimitPriority.NORMAL: 1.0,   # 正常优先级
            RateLimitPriority.HIGH: 0.7,     # 高优先级需要更少令牌
            RateLimitPriority.CRITICAL: 0.5  # 关键优先级需要最少令牌
        }
        
        factor = priority_factors.get(priority, 1.0)
        return max(1, int(tokens * factor))
    
    def _update_token_bucket(self, dynamic_limit: int):
        """更新令牌桶配置"""
        # 如果动态限制变化较大，重新创建令牌桶
        if abs(dynamic_limit - self.token_bucket.capacity) > self.base_config.max_requests * 0.2:
            new_refill_rate = dynamic_limit / self.base_config.time_window
            self.token_bucket = TokenBucket(dynamic_limit, new_refill_rate)
    
    async def acquire_async(self, priority: RateLimitPriority = RateLimitPriority.NORMAL,
                          tokens: int = 1) -> Tuple[bool, float]:
        """异步获取限流许可"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.acquire, priority, tokens
        )
    
    def get_metrics(self) -> RateLimitMetrics:
        """获取指标"""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "name": self.name,
            "dynamic_limit": self.get_dynamic_limit(),
            "base_limit": self.base_config.max_requests,
            "current_load": self.current_load,
            "total_requests": self.metrics.total_requests,
            "allowed_requests": self.metrics.allowed_requests,
            "rejected_requests": self.metrics.rejected_requests,
            "rejection_rate": self.metrics.get_rejection_rate(),
            "avg_response_time": self.metrics.get_avg_response_time(),
            "avg_wait_time": self.metrics.get_avg_wait_time()
        }


class PriorityBasedRateLimiter:
    """基于优先级的限流器"""
    
    def __init__(self, base_config: RateLimitConfig):
        """初始化优先级限流器"""
        self.base_config = base_config
        
        # 为每个优先级创建独立的限流器
        self.limiters = {}
        for priority in RateLimitPriority:
            # 为不同优先级分配不同的配额
            quota_factor = self._get_quota_factor(priority)
            priority_config = RateLimitConfig(
                max_requests=int(base_config.max_requests * quota_factor),
                time_window=base_config.time_window,
                algorithm=base_config.algorithm,
                priority=priority
            )
            
            self.limiters[priority] = AdaptiveRateLimiter(
                f"{priority.value}_limiter", priority_config
            )
        
        self.lock = threading.Lock()
    
    def _get_quota_factor(self, priority: RateLimitPriority) -> float:
        """获取配额因子"""
        quota_factors = {
            RateLimitPriority.LOW: 0.2,      # 20%配额
            RateLimitPriority.NORMAL: 0.5,   # 50%配额
            RateLimitPriority.HIGH: 0.2,     # 20%配额
            RateLimitPriority.CRITICAL: 0.1  # 10%配额（保留给关键请求）
        }
        return quota_factors.get(priority, 0.5)
    
    def acquire(self, priority: RateLimitPriority = RateLimitPriority.NORMAL,
               tokens: int = 1) -> Tuple[bool, float]:
        """获取限流许可"""
        limiter = self.limiters.get(priority)
        if not limiter:
            # 默认使用正常优先级
            limiter = self.limiters[RateLimitPriority.NORMAL]
        
        return limiter.acquire(priority, tokens)
    
    def update_system_load(self, load: float):
        """更新所有限流器的系统负载"""
        for limiter in self.limiters.values():
            limiter.update_system_load(load)
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        status = {}
        for priority, limiter in self.limiters.items():
            status[priority.value] = limiter.get_health_status()
        return status


class EnhancedRateLimitManager:
    """增强限流管理器"""
    
    def __init__(self):
        self.limiters: Dict[str, Union[AdaptiveRateLimiter, PriorityBasedRateLimiter]] = {}
        self.lock = threading.Lock()
    
    def create_limiter(self, name: str, config: RateLimitConfig,
                      priority_based: bool = False) -> Union[AdaptiveRateLimiter, PriorityBasedRateLimiter]:
        """创建限流器"""
        with self.lock:
            if name in self.limiters:
                return self.limiters[name]
            
            if priority_based:
                limiter = PriorityBasedRateLimiter(config)
            else:
                limiter = AdaptiveRateLimiter(name, config)
            
            self.limiters[name] = limiter
            return limiter
    
    def get_limiter(self, name: str) -> Optional[Union[AdaptiveRateLimiter, PriorityBasedRateLimiter]]:
        """获取限流器"""
        return self.limiters.get(name)
    
    def update_system_load(self, load: float):
        """更新所有限流器的系统负载"""
        with self.lock:
            for limiter in self.limiters.values():
                if hasattr(limiter, 'update_system_load'):
                    limiter.update_system_load(load)
    
    def get_all_limiters(self) -> Dict[str, Union[AdaptiveRateLimiter, PriorityBasedRateLimiter]]:
        """获取所有限流器"""
        return self.limiters.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取所有限流器的健康状态"""
        status = {}
        for name, limiter in self.limiters.items():
            status[name] = limiter.get_health_status()
        return status


# 全局增强限流管理器实例
enhanced_rate_limit_manager = EnhancedRateLimitManager()


def enhanced_rate_limit(name: str, config: RateLimitConfig, priority_based: bool = False):
    """增强限流装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取或创建限流器
            limiter = enhanced_rate_limit_manager.create_limiter(name, config, priority_based)
            
            # 从参数中提取优先级（如果存在）
            priority = kwargs.pop('rate_limit_priority', RateLimitPriority.NORMAL)
            
            # 获取限流许可
            allowed, wait_time = limiter.acquire(priority)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for {name}. Wait time: {wait_time:.2f}s")
            
            # 执行函数
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def enhanced_rate_limit_async(name: str, config: RateLimitConfig, priority_based: bool = False):
    """异步增强限流装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取或创建限流器
            limiter = enhanced_rate_limit_manager.create_limiter(name, config, priority_based)
            
            # 从参数中提取优先级（如果存在）
            priority = kwargs.pop('rate_limit_priority', RateLimitPriority.NORMAL)
            
            # 异步获取限流许可
            allowed, wait_time = await limiter.acquire_async(priority)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for {name}. Wait time: {wait_time:.2f}s")
            
            # 执行异步函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 示例配置
def create_api_rate_limit_config() -> RateLimitConfig:
    """创建API限流配置"""
    return RateLimitConfig(
        max_requests=1000,  # 每秒1000个请求
        time_window=60,     # 60秒窗口
        algorithm=RateLimitAlgorithm.ADAPTIVE,
        priority=RateLimitPriority.NORMAL
    )


def create_user_rate_limit_config() -> RateLimitConfig:
    """创建用户限流配置"""
    return RateLimitConfig(
        max_requests=100,   # 每秒100个请求
        time_window=60,     # 60秒窗口
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        priority=RateLimitPriority.NORMAL
    )


def create_critical_rate_limit_config() -> RateLimitConfig:
    """创建关键请求限流配置"""
    return RateLimitConfig(
        max_requests=50,    # 每秒50个关键请求
        time_window=60,     # 60秒窗口
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        priority=RateLimitPriority.CRITICAL
    )