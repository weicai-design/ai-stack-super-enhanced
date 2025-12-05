"""
增强动态熔断器系统
实现生产级智能熔断、动态阈值调整、服务降级和智能恢复机制
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class EnhancedCircuitState(Enum):
    """增强熔断器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"      # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态
    DEGRADED = "degraded"  # 降级状态


class DynamicThresholdStrategy(Enum):
    """动态阈值策略"""
    STATIC = "static"  # 静态阈值
    ADAPTIVE = "adaptive"  # 自适应阈值
    PREDICTIVE = "predictive"  # 预测性阈值


@dataclass
class EnhancedCircuitMetrics:
    """增强熔断器指标"""
    total_requests: int = 0
    failed_requests: int = 0
    success_requests: int = 0
    degraded_requests: int = 0
    response_times: List[float] = None
    error_rates: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
        if self.error_rates is None:
            self.error_rates = []
    
    def record_response_time(self, response_time: float):
        """记录响应时间"""
        self.response_times.append(response_time)
        # 保留最近1000个记录
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_error_rate(self, error_rate: float):
        """记录错误率"""
        self.error_rates.append(error_rate)
        if len(self.error_rates) > 100:
            self.error_rates = self.error_rates[-100:]
    
    def get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    def get_error_rate(self) -> float:
        """获取当前错误率"""
        if not self.error_rates:
            return 0.0
        return statistics.mean(self.error_rates)


class DegradationStrategy:
    """服务降级策略"""
    
    def __init__(self, fallback_func: Optional[Callable] = None, 
                 degraded_features: List[str] = None):
        """
        初始化降级策略
        
        Args:
            fallback_func: 降级备用函数
            degraded_features: 降级功能列表
        """
        self.fallback_func = fallback_func
        self.degraded_features = degraded_features or []
    
    def execute_fallback(self, *args, **kwargs) -> Any:
        """执行降级备用函数"""
        if self.fallback_func:
            return self.fallback_func(*args, **kwargs)
        raise Exception("No fallback function available")


class AdaptiveThresholdCalculator:
    """自适应阈值计算器"""
    
    def __init__(self, base_threshold: float = 0.5, 
                 sensitivity: float = 0.1,
                 learning_rate: float = 0.01):
        """
        初始化自适应阈值计算器
        
        Args:
            base_threshold: 基础阈值
            sensitivity: 敏感度
            learning_rate: 学习率
        """
        self.base_threshold = base_threshold
        self.sensitivity = sensitivity
        self.learning_rate = learning_rate
        self.historical_metrics = []
    
    def calculate_threshold(self, metrics: EnhancedCircuitMetrics, 
                           current_load: float) -> float:
        """
        计算动态阈值
        
        Args:
            metrics: 熔断器指标
            current_load: 当前系统负载
        
        Returns:
            float: 动态阈值
        """
        # 基于历史数据调整阈值
        if len(self.historical_metrics) > 0:
            avg_error_rate = statistics.mean([m.get_error_rate() for m in self.historical_metrics[-10:]])
            
            # 根据系统负载调整阈值
            load_factor = max(0.5, min(2.0, current_load / 0.8))  # 假设80%为正常负载
            
            # 动态调整阈值
            dynamic_threshold = self.base_threshold * load_factor
            
            # 根据历史错误率调整
            if avg_error_rate > 0.1:  # 错误率超过10%
                dynamic_threshold *= (1 - self.sensitivity)
            else:
                dynamic_threshold *= (1 + self.sensitivity)
            
            return max(0.1, min(0.9, dynamic_threshold))
        
        return self.base_threshold
    
    def update_metrics(self, metrics: EnhancedCircuitMetrics):
        """更新历史指标"""
        self.historical_metrics.append(metrics)
        if len(self.historical_metrics) > 100:
            self.historical_metrics = self.historical_metrics[-100:]


class EnhancedCircuitBreaker:
    """增强动态熔断器"""
    
    def __init__(
        self,
        name: str,
        base_failure_threshold: float = 0.5,  # 基础失败阈值
        recovery_timeout: int = 60,
        half_open_max_requests: int = 3,
        threshold_strategy: DynamicThresholdStrategy = DynamicThresholdStrategy.ADAPTIVE,
        degradation_strategy: Optional[DegradationStrategy] = None
    ):
        """
        初始化增强熔断器
        
        Args:
            name: 熔断器名称
            base_failure_threshold: 基础失败阈值
            recovery_timeout: 恢复超时时间（秒）
            half_open_max_requests: 半开状态最大请求数
            threshold_strategy: 阈值策略
            degradation_strategy: 降级策略
        """
        self.name = name
        self.base_failure_threshold = base_failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests
        self.threshold_strategy = threshold_strategy
        self.degradation_strategy = degradation_strategy
        
        # 状态管理
        self.state = EnhancedCircuitState.CLOSED
        self.metrics = EnhancedCircuitMetrics()
        self.last_state_change = datetime.now()
        self.half_open_attempts = 0
        self.lock = threading.Lock()
        
        # 自适应阈值计算器
        self.threshold_calculator = AdaptiveThresholdCalculator(
            base_threshold=base_failure_threshold
        )
        
        # 系统负载监控
        self.current_load = 0.0
        self.last_load_update = datetime.now()
    
    def get_dynamic_threshold(self) -> float:
        """获取动态阈值"""
        if self.threshold_strategy == DynamicThresholdStrategy.STATIC:
            return self.base_failure_threshold
        
        elif self.threshold_strategy == DynamicThresholdStrategy.ADAPTIVE:
            return self.threshold_calculator.calculate_threshold(
                self.metrics, self.current_load
            )
        
        else:  # PREDICTIVE
            # 简单的预测性阈值（基于趋势分析）
            if len(self.metrics.error_rates) >= 5:
                recent_errors = self.metrics.error_rates[-5:]
                trend = statistics.mean(recent_errors[-3:]) - statistics.mean(recent_errors[:2])
                predictive_threshold = self.base_failure_threshold * (1 - trend * 0.5)
                return max(0.1, min(0.9, predictive_threshold))
            
            return self.base_failure_threshold
    
    def update_system_load(self, load: float):
        """更新系统负载"""
        self.current_load = load
        self.last_load_update = datetime.now()
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """异步执行受保护的函数"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.call, func, *args, **kwargs
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行受保护的函数"""
        with self.lock:
            # 检查熔断器状态
            if self.state == EnhancedCircuitState.OPEN:
                if self._should_try_recovery():
                    self.state = EnhancedCircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                    self.last_state_change = datetime.now()
                    logger.info(f"熔断器 {self.name} 进入半开状态")
                else:
                    # 尝试降级策略
                    if self.degradation_strategy:
                        logger.warning(f"熔断器 {self.name} 打开，执行降级策略")
                        return self._execute_degraded(func, *args, **kwargs)
                    else:
                        raise Exception(f"Circuit breaker {self.name} is OPEN")
            
            elif self.state == EnhancedCircuitState.HALF_OPEN:
                if self.half_open_attempts >= self.half_open_max_requests:
                    if self.degradation_strategy:
                        return self._execute_degraded(func, *args, **kwargs)
                    else:
                        raise Exception(f"Circuit breaker {self.name} is HALF_OPEN and reached max attempts")
            
            elif self.state == EnhancedCircuitState.DEGRADED:
                # 直接执行降级策略
                return self._execute_degraded(func, *args, **kwargs)
        
        # 执行函数
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time
            
            self._on_success(response_time)
            return result
        
        except Exception as e:
            response_time = time.time() - start_time
            self._on_failure(response_time)
            raise e
    
    def _should_try_recovery(self) -> bool:
        """检查是否应该尝试恢复"""
        if self.state != EnhancedCircuitState.OPEN:
            return False
        
        recovery_time = self.last_state_change + timedelta(seconds=self.recovery_timeout)
        return datetime.now() >= recovery_time
    
    def _execute_degraded(self, func: Callable, *args, **kwargs) -> Any:
        """执行降级策略"""
        if self.degradation_strategy:
            self.metrics.degraded_requests += 1
            logger.info(f"执行降级策略: {self.name}")
            return self.degradation_strategy.execute_fallback(*args, **kwargs)
        else:
            raise Exception(f"No degradation strategy available for {self.name}")
    
    def _on_success(self, response_time: float):
        """成功回调"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.success_requests += 1
            self.metrics.last_success_time = datetime.now()
            self.metrics.record_response_time(response_time)
            
            # 更新错误率
            current_error_rate = self.metrics.failed_requests / max(1, self.metrics.total_requests)
            self.metrics.record_error_rate(current_error_rate)
            
            if self.state == EnhancedCircuitState.HALF_OPEN:
                self.half_open_attempts += 1
                
                # 如果半开状态下连续成功，则关闭熔断器
                if self.half_open_attempts >= self.half_open_max_requests:
                    self.state = EnhancedCircuitState.CLOSED
                    self.metrics.failed_requests = 0
                    self.last_state_change = datetime.now()
                    logger.info(f"熔断器 {self.name} 恢复正常状态")
            
            elif self.state == EnhancedCircuitState.DEGRADED:
                # 降级状态下成功，检查是否恢复正常
                dynamic_threshold = self.get_dynamic_threshold()
                current_error_rate = self.metrics.failed_requests / max(1, self.metrics.total_requests)
                
                if current_error_rate < dynamic_threshold * 0.5:  # 错误率低于阈值50%
                    self.state = EnhancedCircuitState.CLOSED
                    logger.info(f"熔断器 {self.name} 从降级状态恢复正常")
    
    def _on_failure(self, response_time: float):
        """失败回调"""
        with self.lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = datetime.now()
            self.metrics.record_response_time(response_time)
            
            # 更新错误率
            current_error_rate = self.metrics.failed_requests / max(1, self.metrics.total_requests)
            self.metrics.record_error_rate(current_error_rate)
            
            dynamic_threshold = self.get_dynamic_threshold()
            
            if self.state == EnhancedCircuitState.HALF_OPEN:
                # 半开状态下失败，重新打开熔断器
                self.state = EnhancedCircuitState.OPEN
                self.last_state_change = datetime.now()
                logger.warning(f"熔断器 {self.name} 半开测试失败，重新打开")
            
            elif (self.state == EnhancedCircuitState.CLOSED and 
                  current_error_rate >= dynamic_threshold):
                # 达到动态失败阈值，打开熔断器
                self.state = EnhancedCircuitState.OPEN
                self.last_state_change = datetime.now()
                logger.warning(f"熔断器 {self.name} 打开，错误率: {current_error_rate:.2f} >= {dynamic_threshold:.2f}")
            
            elif (self.state == EnhancedCircuitState.CLOSED and 
                  current_error_rate >= dynamic_threshold * 0.7):
                # 错误率较高但未达到阈值，进入降级状态
                if self.degradation_strategy:
                    self.state = EnhancedCircuitState.DEGRADED
                    logger.warning(f"熔断器 {self.name} 进入降级状态，错误率: {current_error_rate:.2f}")
    
    def get_state(self) -> EnhancedCircuitState:
        """获取当前状态"""
        return self.state
    
    def get_metrics(self) -> EnhancedCircuitMetrics:
        """获取指标"""
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.metrics.total_requests,
            "success_requests": self.metrics.success_requests,
            "failed_requests": self.metrics.failed_requests,
            "degraded_requests": self.metrics.degraded_requests,
            "error_rate": self.metrics.get_error_rate(),
            "avg_response_time": self.metrics.get_avg_response_time(),
            "dynamic_threshold": self.get_dynamic_threshold(),
            "half_open_attempts": self.half_open_attempts,
            "current_load": self.current_load
        }


class EnhancedCircuitBreakerManager:
    """增强熔断器管理器"""
    
    def __init__(self):
        self.breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, name: str, **kwargs) -> EnhancedCircuitBreaker:
        """获取或创建熔断器"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = EnhancedCircuitBreaker(name, **kwargs)
            return self.breakers[name]
    
    def update_system_load(self, load: float):
        """更新所有熔断器的系统负载"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.update_system_load(load)
    
    def get_all_breakers(self) -> Dict[str, EnhancedCircuitBreaker]:
        """获取所有熔断器"""
        return self.breakers.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取所有熔断器的健康状态"""
        status = {}
        for name, breaker in self.breakers.items():
            status[name] = breaker.get_health_status()
        return status


# 全局增强熔断器管理器实例
enhanced_circuit_manager = EnhancedCircuitBreakerManager()


def enhanced_circuit_breaker(name: str, **kwargs):
    """增强熔断器装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs_inner):
            breaker = enhanced_circuit_manager.get_breaker(name, **kwargs)
            return breaker.call(func, *args, **kwargs_inner)
        return wrapper
    return decorator


async def enhanced_circuit_breaker_async(name: str, **kwargs):
    """异步增强熔断器装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs_inner):
            breaker = enhanced_circuit_manager.get_breaker(name, **kwargs)
            return await breaker.call_async(func, *args, **kwargs_inner)
        return wrapper
    return decorator


# 示例降级策略
def default_fallback(*args, **kwargs):
    """默认降级函数"""
    return {
        "success": False,
        "error": "Service temporarily unavailable due to circuit breaker",
        "degraded": True,
        "message": "Please try again later"
    }


def create_degradation_strategy(fallback_func=None, degraded_features=None):
    """创建降级策略"""
    return DegradationStrategy(
        fallback_func=fallback_func or default_fallback,
        degraded_features=degraded_features or []
    )