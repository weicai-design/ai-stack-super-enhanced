"""
服务降级和熔断恢复机制
实现优雅降级、智能恢复、渐进式重试和降级策略管理
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """降级级别"""
    NONE = "none"  # 无降级
    MINIMAL = "minimal"  # 最小降级
    PARTIAL = "partial"  # 部分降级
    FULL = "full"  # 完全降级


class RecoveryStrategy(Enum):
    """恢复策略"""
    IMMEDIATE = "immediate"  # 立即恢复
    GRADUAL = "gradual"  # 渐进恢复
    INTELLIGENT = "intelligent"  # 智能恢复


@dataclass
class DegradationRule:
    """降级规则"""
    feature_name: str  # 功能名称
    degradation_level: DegradationLevel  # 降级级别
    fallback_func: Optional[Callable]  # 降级备用函数
    conditions: List[Callable]  # 降级条件
    priority: int = 1  # 优先级


@dataclass
class RecoveryRule:
    """恢复规则"""
    feature_name: str  # 功能名称
    recovery_strategy: RecoveryStrategy  # 恢复策略
    conditions: List[Callable]  # 恢复条件
    retry_delay: float = 1.0  # 重试延迟（秒）
    max_retries: int = 3  # 最大重试次数


class FeatureDegradationManager:
    """功能降级管理器"""
    
    def __init__(self):
        self.degradation_rules: Dict[str, DegradationRule] = {}
        self.current_degradations: Dict[str, DegradationLevel] = {}
        self.degradation_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def register_degradation_rule(self, rule: DegradationRule):
        """注册降级规则"""
        with self.lock:
            self.degradation_rules[rule.feature_name] = rule
            logger.info(f"注册降级规则: {rule.feature_name} - {rule.degradation_level}")
    
    def should_degrade(self, feature_name: str, context: Dict[str, Any]) -> bool:
        """检查是否应该降级"""
        rule = self.degradation_rules.get(feature_name)
        if not rule:
            return False
        
        # 检查所有条件
        for condition in rule.conditions:
            try:
                if not condition(context):
                    return False
            except Exception as e:
                logger.error(f"降级条件检查失败: {feature_name} - {e}")
                return False
        
        return True
    
    def degrade_feature(self, feature_name: str, level: DegradationLevel, 
                       reason: str = ""):
        """降级功能"""
        with self.lock:
            self.current_degradations[feature_name] = level
            
            # 记录降级历史
            degradation_record = {
                "feature_name": feature_name,
                "level": level.value,
                "timestamp": datetime.now(),
                "reason": reason
            }
            self.degradation_history.append(degradation_record)
            
            # 保留最近100条记录
            if len(self.degradation_history) > 100:
                self.degradation_history = self.degradation_history[-100:]
            
            logger.warning(f"功能降级: {feature_name} -> {level.value}, 原因: {reason}")
    
    def restore_feature(self, feature_name: str):
        """恢复功能"""
        with self.lock:
            if feature_name in self.current_degradations:
                previous_level = self.current_degradations[feature_name]
                del self.current_degradations[feature_name]
                
                # 记录恢复历史
                recovery_record = {
                    "feature_name": feature_name,
                    "previous_level": previous_level.value,
                    "timestamp": datetime.now(),
                    "type": "manual"
                }
                self.degradation_history.append(recovery_record)
                
                logger.info(f"功能恢复: {feature_name}")
    
    def get_feature_level(self, feature_name: str) -> DegradationLevel:
        """获取功能降级级别"""
        return self.current_degradations.get(feature_name, DegradationLevel.NONE)
    
    def get_degradation_status(self) -> Dict[str, Any]:
        """获取降级状态"""
        return {
            "current_degradations": {
                feature: level.value for feature, level in self.current_degradations.items()
            },
            "total_degraded_features": len(self.current_degradations),
            "degradation_history_count": len(self.degradation_history)
        }


class IntelligentRecoveryManager:
    """智能恢复管理器"""
    
    def __init__(self):
        self.recovery_rules: Dict[str, RecoveryRule] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.last_recovery_attempt: Dict[str, datetime] = {}
        self.successful_recoveries: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
    
    def register_recovery_rule(self, rule: RecoveryRule):
        """注册恢复规则"""
        with self.lock:
            self.recovery_rules[rule.feature_name] = rule
            logger.info(f"注册恢复规则: {rule.feature_name} - {rule.recovery_strategy}")
    
    def should_recover(self, feature_name: str, context: Dict[str, Any]) -> bool:
        """检查是否应该恢复"""
        rule = self.recovery_rules.get(feature_name)
        if not rule:
            return False
        
        # 检查恢复条件
        for condition in rule.conditions:
            try:
                if not condition(context):
                    return False
            except Exception as e:
                logger.error(f"恢复条件检查失败: {feature_name} - {e}")
                return False
        
        # 检查重试限制
        attempts = self.recovery_attempts.get(feature_name, 0)
        if attempts >= rule.max_retries:
            return False
        
        # 检查重试延迟
        last_attempt = self.last_recovery_attempt.get(feature_name)
        if last_attempt:
            next_attempt_time = last_attempt + timedelta(seconds=rule.retry_delay)
            if datetime.now() < next_attempt_time:
                return False
        
        return True
    
    def attempt_recovery(self, feature_name: str, recovery_func: Callable, 
                        context: Dict[str, Any]) -> Tuple[bool, Any]:
        """尝试恢复功能"""
        rule = self.recovery_rules.get(feature_name)
        if not rule:
            return False, None
        
        with self.lock:
            # 记录恢复尝试
            self.recovery_attempts[feature_name] = self.recovery_attempts.get(feature_name, 0) + 1
            self.last_recovery_attempt[feature_name] = datetime.now()
            
            attempts = self.recovery_attempts[feature_name]
            logger.info(f"尝试恢复功能: {feature_name}, 尝试次数: {attempts}")
        
        try:
            # 根据恢复策略执行恢复
            result = self._execute_recovery_strategy(rule, recovery_func, context)
            
            # 如果恢复成功，重置尝试计数
            if result:
                with self.lock:
                    self.recovery_attempts[feature_name] = 0
                    
                    # 记录成功恢复
                    recovery_record = {
                        "feature_name": feature_name,
                        "timestamp": datetime.now(),
                        "attempts": attempts,
                        "strategy": rule.recovery_strategy.value
                    }
                    self.successful_recoveries.append(recovery_record)
                    
                    # 保留最近50条记录
                    if len(self.successful_recoveries) > 50:
                        self.successful_recoveries = self.successful_recoveries[-50:]
            
            return result, None
        
        except Exception as e:
            logger.error(f"恢复功能失败: {feature_name} - {e}")
            return False, e
    
    def _execute_recovery_strategy(self, rule: RecoveryRule, recovery_func: Callable,
                                 context: Dict[str, Any]) -> bool:
        """执行恢复策略"""
        if rule.recovery_strategy == RecoveryStrategy.IMMEDIATE:
            # 立即恢复
            return recovery_func(context)
        
        elif rule.recovery_strategy == RecoveryStrategy.GRADUAL:
            # 渐进恢复 - 逐步增加负载
            return self._gradual_recovery(rule, recovery_func, context)
        
        elif rule.recovery_strategy == RecoveryStrategy.INTELLIGENT:
            # 智能恢复 - 基于历史数据优化
            return self._intelligent_recovery(rule, recovery_func, context)
        
        return False
    
    def _gradual_recovery(self, rule: RecoveryRule, recovery_func: Callable,
                         context: Dict[str, Any]) -> bool:
        """渐进恢复策略"""
        attempts = self.recovery_attempts.get(rule.feature_name, 0)
        
        # 根据尝试次数调整恢复参数
        recovery_factor = min(1.0, attempts * 0.3)  # 逐步增加恢复强度
        
        # 修改上下文以反映渐进恢复
        modified_context = context.copy()
        modified_context["recovery_factor"] = recovery_factor
        modified_context["gradual_recovery"] = True
        
        return recovery_func(modified_context)
    
    def _intelligent_recovery(self, rule: RecoveryRule, recovery_func: Callable,
                             context: Dict[str, Any]) -> bool:
        """智能恢复策略"""
        # 分析历史恢复数据
        feature_recoveries = [
            r for r in self.successful_recoveries 
            if r["feature_name"] == rule.feature_name
        ]
        
        if feature_recoveries:
            # 计算平均恢复尝试次数
            avg_attempts = statistics.mean([r["attempts"] for r in feature_recoveries])
            current_attempts = self.recovery_attempts.get(rule.feature_name, 0)
            
            # 如果当前尝试次数远低于平均值，可能还需要更多尝试
            if current_attempts < avg_attempts * 0.5:
                # 等待更多尝试
                return False
        
        # 使用指数退避策略
        delay = rule.retry_delay * (2 ** (self.recovery_attempts.get(rule.feature_name, 0) - 1))
        time.sleep(min(delay, 60))  # 最大延迟60秒
        
        return recovery_func(context)
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """获取恢复状态"""
        return {
            "recovery_attempts": self.recovery_attempts.copy(),
            "successful_recoveries_count": len(self.successful_recoveries),
            "active_recovery_rules": len(self.recovery_rules)
        }


class GracefulDegradationExecutor:
    """优雅降级执行器"""
    
    def __init__(self, degradation_manager: FeatureDegradationManager):
        self.degradation_manager = degradation_manager
    
    def execute_with_graceful_degradation(self, feature_name: str, 
                                         primary_func: Callable,
                                         fallback_func: Optional[Callable] = None,
                                         context: Dict[str, Any] = None) -> Any:
        """
        执行优雅降级
        
        Args:
            feature_name: 功能名称
            primary_func: 主要功能函数
            fallback_func: 降级备用函数
            context: 执行上下文
        
        Returns:
            Any: 执行结果
        """
        context = context or {}
        
        # 检查当前降级级别
        current_level = self.degradation_manager.get_feature_level(feature_name)
        
        if current_level == DegradationLevel.FULL:
            # 完全降级，使用备用函数
            return self._execute_fallback(fallback_func, context, "完全降级")
        
        elif current_level == DegradationLevel.PARTIAL:
            # 部分降级，尝试主要功能，失败时使用备用
            try:
                return primary_func(context)
            except Exception as e:
                logger.warning(f"主要功能执行失败，使用降级: {feature_name} - {e}")
                return self._execute_fallback(fallback_func, context, "部分降级")
        
        elif current_level == DegradationLevel.MINIMAL:
            # 最小降级，正常执行主要功能
            return primary_func(context)
        
        else:  # NONE
            # 无降级，正常执行
            try:
                return primary_func(context)
            except Exception as e:
                # 检查是否应该降级
                if self.degradation_manager.should_degrade(feature_name, context):
                    # 自动降级
                    self.degradation_manager.degrade_feature(
                        feature_name, DegradationLevel.PARTIAL, f"执行失败: {str(e)}"
                    )
                    return self._execute_fallback(fallback_func, context, "自动降级")
                else:
                    # 不降级，直接抛出异常
                    raise e
    
    def _execute_fallback(self, fallback_func: Optional[Callable], 
                         context: Dict[str, Any], reason: str) -> Any:
        """执行降级备用函数"""
        if fallback_func:
            logger.info(f"执行降级备用函数: {reason}")
            return fallback_func(context)
        else:
            raise Exception(f"功能降级但无备用函数可用: {reason}")
    
    async def execute_with_graceful_degradation_async(self, feature_name: str,
                                                     primary_func: Callable,
                                                     fallback_func: Optional[Callable] = None,
                                                     context: Dict[str, Any] = None) -> Any:
        """异步执行优雅降级"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.execute_with_graceful_degradation, 
            feature_name, primary_func, fallback_func, context
        )


class ProgressiveRetryStrategy:
    """渐进式重试策略"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, jitter: bool = True):
        """
        初始化渐进式重试策略
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行带重试的函数"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 包括第一次尝试
            try:
                if attempt > 0:
                    # 计算延迟时间
                    delay = self._calculate_delay(attempt)
                    logger.info(f"重试 {attempt}/{self.max_retries}, 延迟 {delay:.2f}秒")
                    time.sleep(delay)
                
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                logger.warning(f"尝试 {attempt + 1} 失败: {str(e)}")
                
                if attempt == self.max_retries:
                    logger.error(f"达到最大重试次数: {self.max_retries}")
                    raise last_exception
        
        raise last_exception  # 理论上不会执行到这里
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        # 指数退避
        delay = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        
        # 添加随机抖动
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    async def execute_with_retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """异步执行带重试的函数"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"异步重试 {attempt}/{self.max_retries}, 延迟 {delay:.2f}秒")
                    await asyncio.sleep(delay)
                
                # 执行异步函数
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                logger.warning(f"异步尝试 {attempt + 1} 失败: {str(e)}")
                
                if attempt == self.max_retries:
                    logger.error(f"达到最大异步重试次数: {self.max_retries}")
                    raise last_exception
        
        raise last_exception


# 全局管理器实例
degradation_manager = FeatureDegradationManager()
recovery_manager = IntelligentRecoveryManager()
degradation_executor = GracefulDegradationExecutor(degradation_manager)


# 示例降级条件
def high_error_rate_condition(context: Dict[str, Any]) -> bool:
    """高错误率降级条件"""
    error_rate = context.get('error_rate', 0)
    return error_rate > 0.1  # 错误率超过10%


def high_latency_condition(context: Dict[str, Any]) -> bool:
    """高延迟降级条件"""
    latency = context.get('latency', 0)
    return latency > 5.0  # 延迟超过5秒


def system_overload_condition(context: Dict[str, Any]) -> bool:
    """系统过载降级条件"""
    system_load = context.get('system_load', 0)
    return system_load > 0.8  # 系统负载超过80%


# 示例恢复条件
def low_error_rate_condition(context: Dict[str, Any]) -> bool:
    """低错误率恢复条件"""
    error_rate = context.get('error_rate', 0)
    return error_rate < 0.01  # 错误率低于1%


def normal_latency_condition(context: Dict[str, Any]) -> bool:
    """正常延迟恢复条件"""
    latency = context.get('latency', 0)
    return latency < 1.0  # 延迟低于1秒


def system_normal_condition(context: Dict[str, Any]) -> bool:
    """系统正常恢复条件"""
    system_load = context.get('system_load', 0)
    return system_load < 0.6  # 系统负载低于60%


# 装饰器函数
def graceful_degradation(feature_name: str, fallback_func: Optional[Callable] = None):
    """优雅降级装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = kwargs.pop('degradation_context', {})
            return degradation_executor.execute_with_graceful_degradation(
                feature_name, func, fallback_func, context
            )
        return wrapper
    return decorator


async def graceful_degradation_async(feature_name: str, fallback_func: Optional[Callable] = None):
    """异步优雅降级装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            context = kwargs.pop('degradation_context', {})
            return await degradation_executor.execute_with_graceful_degradation_async(
                feature_name, func, fallback_func, context
            )
        return wrapper
    return decorator


def progressive_retry(max_retries: int = 3, base_delay: float = 1.0):
    """渐进式重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_strategy = ProgressiveRetryStrategy(max_retries, base_delay)
            return retry_strategy.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator


async def progressive_retry_async(max_retries: int = 3, base_delay: float = 1.0):
    """异步渐进式重试装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retry_strategy = ProgressiveRetryStrategy(max_retries, base_delay)
            return await retry_strategy.execute_with_retry_async(func, *args, **kwargs)
        return wrapper
    return decorator