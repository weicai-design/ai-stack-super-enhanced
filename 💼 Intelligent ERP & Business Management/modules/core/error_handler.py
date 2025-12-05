"""
T013和T014模块错误处理和重试策略
实现生产级错误处理和智能重试机制
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, Type, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类"""
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_SERVICE = "external_service"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    module: str
    function: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class ErrorRecord:
    """错误记录"""
    id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    timestamp: datetime
    stack_trace: Optional[str] = None
    resolved: bool = False
    retry_count: int = 0


class RetryStrategy:
    """重试策略"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_backoff: bool = True,
        jitter: bool = True
    ):
        """
        初始化重试策略
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            exponential_backoff: 是否使用指数退避
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.jitter = jitter
    
    def get_delay(self, retry_count: int) -> float:
        """计算重试延迟时间"""
        if not self.exponential_backoff:
            delay = self.base_delay
        else:
            delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
        
        if self.jitter:
            # 添加随机抖动，避免惊群效应
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return min(delay, self.max_delay)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化错误处理器"""
        self.logger = logger or logging.getLogger(__name__)
        self.error_records: Dict[str, ErrorRecord] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        
        # 默认重试策略
        self.default_retry_strategy = RetryStrategy()
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        retry_strategy: Optional[RetryStrategy] = None
    ) -> ErrorRecord:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            severity: 错误严重程度
            category: 错误分类
            retry_strategy: 重试策略
            
        Returns:
            ErrorRecord: 错误记录
        """
        import uuid
        import traceback
        
        error_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # 创建错误记录
        error_record = ErrorRecord(
            id=error_id,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            category=category,
            context=context,
            timestamp=timestamp,
            stack_trace=traceback.format_exc()
        )
        
        # 记录错误
        self.error_records[error_id] = error_record
        
        # 根据严重程度记录日志
        log_level = self._get_log_level(severity)
        self.logger.log(log_level, f"Error {error_id}: {error}", extra={
            "error_id": error_id,
            "error_type": error_record.error_type,
            "severity": severity.value,
            "category": category.value,
            "module": context.module,
            "function": context.function
        })
        
        return error_record
    
    def retry_with_backoff(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        retriable_errors: Optional[tuple] = None,
        context: Optional[ErrorContext] = None
    ) -> Any:
        """
        使用退避策略重试函数
        
        Args:
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            retry_strategy: 重试策略
            retriable_errors: 可重试的异常类型
            context: 错误上下文
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            Exception: 重试失败后的异常
        """
        if kwargs is None:
            kwargs = {}
        
        if retry_strategy is None:
            retry_strategy = self.default_retry_strategy
        
        if retriable_errors is None:
            retriable_errors = (Exception,)
        
        last_exception = None
        
        for attempt in range(retry_strategy.max_retries + 1):
            try:
                return func(*args, **kwargs)
            
            except retriable_errors as e:
                last_exception = e
                
                if attempt < retry_strategy.max_retries:
                    # 计算延迟时间
                    delay = retry_strategy.get_delay(attempt)
                    
                    # 记录重试信息
                    if context:
                        self.logger.warning(
                            f"Retry attempt {attempt + 1}/{retry_strategy.max_retries} "
                            f"after {delay:.2f}s for {context.module}.{context.function}"
                        )
                    
                    time.sleep(delay)
                else:
                    # 重试次数用尽
                    if context:
                        error_context = context
                    else:
                        error_context = ErrorContext(
                            module="unknown",
                            function=func.__name__,
                            parameters={"args": args, "kwargs": kwargs}
                        )
                    
                    self.handle_error(
                        e, error_context, 
                        severity=ErrorSeverity.HIGH,
                        category=self._classify_error(e)
                    )
                    raise
        
        # 理论上不会执行到这里
        raise last_exception
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """根据严重程度获取日志级别"""
        level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.ERROR)
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """分类错误类型"""
        error_type = type(error).__name__.lower()
        
        if any(keyword in error_type for keyword in ['validation', 'value']):
            return ErrorCategory.VALIDATION
        elif any(keyword in error_type for keyword in ['timeout', 'timed']):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_type for keyword in ['network', 'connection']):
            return ErrorCategory.NETWORK
        elif any(keyword in error_type for keyword in ['database', 'sql']):
            return ErrorCategory.DATABASE
        else:
            return ErrorCategory.UNKNOWN
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计信息"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_records.values()
            if error.timestamp >= cutoff_time
        ]
        
        # 按严重程度统计
        severity_stats = {}
        for severity in ErrorSeverity:
            severity_stats[severity.value] = sum(
                1 for error in recent_errors if error.severity == severity
            )
        
        # 按分类统计
        category_stats = {}
        for category in ErrorCategory:
            category_stats[category.value] = sum(
                1 for error in recent_errors if error.category == category
            )
        
        # 按模块统计
        module_stats = {}
        for error in recent_errors:
            module = error.context.module
            module_stats[module] = module_stats.get(module, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "severity_distribution": severity_stats,
            "category_distribution": category_stats,
            "module_distribution": module_stats,
            "time_range_hours": hours
        }
    
    def resolve_error(self, error_id: str) -> bool:
        """标记错误为已解决"""
        if error_id in self.error_records:
            self.error_records[error_id].resolved = True
            return True
        return False


# 全局错误处理器实例
error_handler = ErrorHandler()


def error_handler_decorator(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    retry_strategy: Optional[RetryStrategy] = None,
    retriable_errors: Optional[tuple] = None
):
    """错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 创建错误上下文
            module_name = func.__module__.split('.')[-1] if '.' in func.__module__ else func.__module__
            context = ErrorContext(
                module=module_name,
                function=func.__name__,
                parameters={"args": args, "kwargs": kwargs}
            )
            
            try:
                # 使用重试策略执行函数
                return error_handler.retry_with_backoff(
                    func, args, kwargs, retry_strategy, retriable_errors, context
                )
            
            except Exception as e:
                # 处理不可重试的错误
                error_handler.handle_error(e, context, severity, category)
                raise
        
        return wrapper
    return decorator


# 预定义的错误处理策略
class ErrorHandlingStrategies:
    """预定义错误处理策略"""
    
    @staticmethod
    def database_operation():
        """数据库操作错误处理策略"""
        return error_handler_decorator(
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            retry_strategy=RetryStrategy(max_retries=3, base_delay=2.0),
            retriable_errors=(ConnectionError, TimeoutError)
        )
    
    @staticmethod
    def external_service():
        """外部服务调用错误处理策略"""
        return error_handler_decorator(
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_SERVICE,
            retry_strategy=RetryStrategy(max_retries=5, base_delay=1.0, exponential_backoff=True),
            retriable_errors=(ConnectionError, TimeoutError)
        )
    
    @staticmethod
    def business_logic():
        """业务逻辑错误处理策略"""
        return error_handler_decorator(
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            retry_strategy=None,  # 业务逻辑错误通常不可重试
            retriable_errors=()
        )
    
    @staticmethod
    def validation():
        """验证错误处理策略"""
        return error_handler_decorator(
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            retry_strategy=None,  # 验证错误不可重试
            retriable_errors=()
        )