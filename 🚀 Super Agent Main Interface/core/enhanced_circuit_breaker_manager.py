"""
增强限流熔断集成管理器
整合动态熔断、智能限流、服务降级和恢复机制的统一管理
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List
from datetime import datetime, timedelta
import logging
import statistics

from .enhanced_circuit_breaker import (
    EnhancedCircuitBreaker, EnhancedCircuitState, enhanced_circuit_manager,
    enhanced_circuit_breaker, enhanced_circuit_breaker_async
)
from .enhanced_rate_limiter import (
    EnhancedRateLimitManager, RateLimitConfig, RateLimitPriority,
    enhanced_rate_limit_manager, enhanced_rate_limit, enhanced_rate_limit_async
)
from .service_degradation_recovery import (
    degradation_manager, recovery_manager, degradation_executor,
    graceful_degradation, graceful_degradation_async,
    progressive_retry, progressive_retry_async
)
from ..config.enhanced_circuit_breaker_config import (
    EnhancedCircuitBreakerConfigManager, ServiceCategory, ServiceProtectionConfig,
    enhanced_config_manager
)

logger = logging.getLogger(__name__)


class EnhancedCircuitBreakerIntegrationManager:
    """增强限流熔断集成管理器"""
    
    def __init__(self):
        self.circuit_manager = enhanced_circuit_manager
        self.rate_limit_manager = enhanced_rate_limit_manager
        self.config_manager = enhanced_config_manager
        
        # 系统监控
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'network_latency': 0.0,
            'request_rate': 0.0,
            'error_rate': 0.0
        }
        
        self.monitoring_thread = None
        self.monitoring_running = False
        self.lock = threading.Lock()
        
        # 自动注册默认服务
        self._register_default_services()
    
    def _register_default_services(self):
        """注册默认服务"""
        # 注册API服务
        self.config_manager.register_service(
            "api_gateway", ServiceCategory.API_SERVICE
        )
        
        # 注册数据库服务
        self.config_manager.register_service(
            "database_service", ServiceCategory.DATABASE_SERVICE
        )
        
        # 注册外部服务
        self.config_manager.register_service(
            "external_api", ServiceCategory.EXTERNAL_SERVICE
        )
        
        # 注册关键服务
        self.config_manager.register_service(
            "authentication_service", ServiceCategory.CRITICAL_SERVICE
        )
    
    def register_service(self, service_name: str, category: ServiceCategory,
                        custom_config: Optional[ServiceProtectionConfig] = None):
        """注册服务"""
        config = self.config_manager.register_service(service_name, category, custom_config)
        
        # 自动创建熔断器和限流器
        circuit_config = config.circuit_breaker_config
        rate_limit_config = config.rate_limit_config
        
        # 创建熔断器
        self.circuit_manager.get_breaker(
            circuit_config.name,
            base_failure_threshold=circuit_config.base_failure_threshold,
            recovery_timeout=circuit_config.recovery_timeout,
            half_open_max_requests=circuit_config.half_open_max_requests,
            threshold_strategy=circuit_config.threshold_strategy
        )
        
        # 创建限流器
        self.rate_limit_manager.create_limiter(
            rate_limit_config.name,
            RateLimitConfig(
                max_requests=rate_limit_config.max_requests,
                time_window=rate_limit_config.time_window,
                algorithm=rate_limit_config.algorithm,
                priority=RateLimitPriority.NORMAL
            ),
            priority_based=rate_limit_config.priority_based
        )
        
        logger.info(f"注册服务: {service_name} ({category.value})")
    
    def start_monitoring(self, interval: int = 30):
        """启动系统监控"""
        if self.monitoring_running:
            logger.warning("监控已启动")
            return
        
        self.monitoring_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"启动系统监控，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self.monitoring_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("停止系统监控")
    
    def _monitoring_loop(self, interval: int):
        """监控循环"""
        while self.monitoring_running:
            try:
                self._update_system_metrics()
                self._update_circuit_breakers()
                self._update_rate_limiters()
                self._check_degradation_conditions()
                
                time.sleep(interval)
            
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(interval)
    
    def _update_system_metrics(self):
        """更新系统指标"""
        # 这里应该从系统监控工具获取实际指标
        # 目前使用模拟数据
        import psutil
        
        with self.lock:
            self.system_metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            self.system_metrics['memory_usage'] = psutil.virtual_memory().percent
            
            # 模拟网络延迟和请求率
            self.system_metrics['network_latency'] = max(0.1, statistics.NormalDist(0.5, 0.2).samples(1)[0])
            self.system_metrics['request_rate'] = max(10, statistics.NormalDist(100, 30).samples(1)[0])
            
            # 计算系统负载（综合指标）
            system_load = (
                self.system_metrics['cpu_usage'] * 0.4 +
                self.system_metrics['memory_usage'] * 0.3 +
                min(1.0, self.system_metrics['request_rate'] / 1000) * 0.3
            ) / 100
            
            # 更新所有熔断器和限流器的系统负载
            self.circuit_manager.update_system_load(system_load)
            self.rate_limit_manager.update_system_load(system_load)
    
    def _update_circuit_breakers(self):
        """更新熔断器状态"""
        # 这里可以添加自动调整熔断器参数的逻辑
        # 例如基于系统负载动态调整阈值
        pass
    
    def _update_rate_limiters(self):
        """更新限流器状态"""
        # 这里可以添加自动调整限流器参数的逻辑
        pass
    
    def _check_degradation_conditions(self):
        """检查降级条件"""
        # 基于系统指标自动触发降级
        system_load = self.system_metrics['cpu_usage'] / 100
        
        if system_load > 0.8:  # 系统负载超过80%
            context = {'system_load': system_load}
            
            # 检查所有功能的降级条件
            for feature_name in degradation_manager.degradation_rules.keys():
                if degradation_manager.should_degrade(feature_name, context):
                    current_level = degradation_manager.get_feature_level(feature_name)
                    if current_level == DegradationLevel.NONE:
                        degradation_manager.degrade_feature(
                            feature_name, DegradationLevel.PARTIAL, "系统过载"
                        )
    
    def protect_service(self, service_name: str, func: Callable, 
                       priority: RateLimitPriority = RateLimitPriority.NORMAL,
                       enable_circuit_breaker: bool = True,
                       enable_rate_limit: bool = True,
                       enable_degradation: bool = True) -> Callable:
        """
        保护服务函数
        
        Args:
            service_name: 服务名称
            func: 要保护的函数
            priority: 请求优先级
            enable_circuit_breaker: 是否启用熔断器
            enable_rate_limit: 是否启用限流
            enable_degradation: 是否启用降级
        
        Returns:
            Callable: 受保护的函数
        """
        config = self.config_manager.get_service_config(service_name)
        if not config:
            logger.warning(f"未找到服务配置: {service_name}")
            return func
        
        circuit_config = config.circuit_breaker_config
        rate_limit_config = config.rate_limit_config
        
        protected_func = func
        
        # 应用降级保护
        if enable_degradation:
            protected_func = self._apply_degradation_protection(
                service_name, protected_func
            )
        
        # 应用限流保护
        if enable_rate_limit:
            protected_func = self._apply_rate_limit_protection(
                rate_limit_config.name, protected_func, priority
            )
        
        # 应用熔断器保护
        if enable_circuit_breaker:
            protected_func = self._apply_circuit_breaker_protection(
                circuit_config.name, protected_func
            )
        
        return protected_func
    
    def _apply_degradation_protection(self, service_name: str, func: Callable) -> Callable:
        """应用降级保护"""
        @graceful_degradation(service_name)
        def protected_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        return protected_func
    
    def _apply_rate_limit_protection(self, limiter_name: str, func: Callable,
                                   priority: RateLimitPriority) -> Callable:
        """应用限流保护"""
        # 获取限流器配置
        limiter = self.rate_limit_manager.get_limiter(limiter_name)
        if not limiter:
            return func
        
        def protected_func(*args, **kwargs):
            # 获取限流许可
            allowed, wait_time = limiter.acquire(priority)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for {limiter_name}")
            
            # 如果有等待时间，等待
            if wait_time > 0:
                time.sleep(wait_time)
            
            return func(*args, **kwargs)
        
        return protected_func
    
    def _apply_circuit_breaker_protection(self, breaker_name: str, func: Callable) -> Callable:
        """应用熔断器保护"""
        @enhanced_circuit_breaker(breaker_name)
        def protected_func(*args, **kwargs):
            return func(*args, **kwargs)
        
        return protected_func
    
    async def protect_service_async(self, service_name: str, func: Callable,
                                  priority: RateLimitPriority = RateLimitPriority.NORMAL,
                                  enable_circuit_breaker: bool = True,
                                  enable_rate_limit: bool = True,
                                  enable_degradation: bool = True) -> Callable:
        """异步保护服务函数"""
        config = self.config_manager.get_service_config(service_name)
        if not config:
            logger.warning(f"未找到服务配置: {service_name}")
            return func
        
        circuit_config = config.circuit_breaker_config
        rate_limit_config = config.rate_limit_config
        
        protected_func = func
        
        # 应用降级保护
        if enable_degradation:
            protected_func = await self._apply_degradation_protection_async(
                service_name, protected_func
            )
        
        # 应用限流保护
        if enable_rate_limit:
            protected_func = await self._apply_rate_limit_protection_async(
                rate_limit_config.name, protected_func, priority
            )
        
        # 应用熔断器保护
        if enable_circuit_breaker:
            protected_func = await self._apply_circuit_breaker_protection_async(
                circuit_config.name, protected_func
            )
        
        return protected_func
    
    async def _apply_degradation_protection_async(self, service_name: str, func: Callable) -> Callable:
        """异步应用降级保护"""
        @graceful_degradation_async(service_name)
        async def protected_func(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return protected_func
    
    async def _apply_rate_limit_protection_async(self, limiter_name: str, func: Callable,
                                               priority: RateLimitPriority) -> Callable:
        """异步应用限流保护"""
        limiter = self.rate_limit_manager.get_limiter(limiter_name)
        if not limiter:
            return func
        
        async def protected_func(*args, **kwargs):
            # 异步获取限流许可
            allowed, wait_time = await limiter.acquire_async(priority)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for {limiter_name}")
            
            # 如果有等待时间，异步等待
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            return await func(*args, **kwargs)
        
        return protected_func
    
    async def _apply_circuit_breaker_protection_async(self, breaker_name: str, func: Callable) -> Callable:
        """异步应用熔断器保护"""
        @enhanced_circuit_breaker_async(breaker_name)
        async def protected_func(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return protected_func
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'system_metrics': self.system_metrics.copy(),
            'circuit_breakers': self.circuit_manager.get_health_status(),
            'rate_limiters': self.rate_limit_manager.get_health_status(),
            'degradation_status': degradation_manager.get_degradation_status(),
            'recovery_status': recovery_manager.get_recovery_status(),
            'registered_services': list(self.config_manager.get_all_configs().keys())
        }
    
    def trigger_manual_degradation(self, feature_name: str, level: str, reason: str = ""):
        """手动触发降级"""
        from ..core.service_degradation_recovery import DegradationLevel
        
        degradation_level = DegradationLevel(level)
        degradation_manager.degrade_feature(feature_name, degradation_level, reason)
        logger.info(f"手动触发降级: {feature_name} -> {level}, 原因: {reason}")
    
    def trigger_manual_recovery(self, feature_name: str):
        """手动触发恢复"""
        degradation_manager.restore_feature(feature_name)
        logger.info(f"手动触发恢复: {feature_name}")


# 全局集成管理器实例
enhanced_integration_manager = EnhancedCircuitBreakerIntegrationManager()


# 便捷装饰器
def enhanced_service_protection(service_name: str, 
                              priority: RateLimitPriority = RateLimitPriority.NORMAL,
                              enable_circuit_breaker: bool = True,
                              enable_rate_limit: bool = True,
                              enable_degradation: bool = True):
    """增强服务保护装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            protected_func = enhanced_integration_manager.protect_service(
                service_name, func, priority, 
                enable_circuit_breaker, enable_rate_limit, enable_degradation
            )
            return protected_func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def enhanced_service_protection_async(service_name: str,
                                          priority: RateLimitPriority = RateLimitPriority.NORMAL,
                                          enable_circuit_breaker: bool = True,
                                          enable_rate_limit: bool = True,
                                          enable_degradation: bool = True):
    """异步增强服务保护装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            protected_func = await enhanced_integration_manager.protect_service_async(
                service_name, func, priority,
                enable_circuit_breaker, enable_rate_limit, enable_degradation
            )
            return await protected_func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 启动集成管理器
def initialize_enhanced_circuit_breaker_system(monitoring_interval: int = 30):
    """初始化增强限流熔断系统"""
    # 启动监控
    enhanced_integration_manager.start_monitoring(monitoring_interval)
    
    logger.info("增强限流熔断系统已初始化")
    return enhanced_integration_manager


# 示例用法
if __name__ == "__main__":
    # 初始化系统
    manager = initialize_enhanced_circuit_breaker_system()
    
    # 注册自定义服务
    manager.register_service("payment_service", ServiceCategory.CRITICAL_SERVICE)
    
    # 使用装饰器保护函数
    @enhanced_service_protection("payment_service", RateLimitPriority.HIGH)
    def process_payment(amount: float, user_id: str):
        """处理支付"""
        # 模拟支付处理
        time.sleep(0.1)
        return {"success": True, "amount": amount, "user_id": user_id}
    
    # 测试保护功能
    try:
        result = process_payment(100.0, "user123")
        print(f"支付处理结果: {result}")
    except Exception as e:
        print(f"支付处理失败: {e}")
    
    # 获取系统状态
    status = manager.get_system_status()
    print(f"系统状态: {status}")