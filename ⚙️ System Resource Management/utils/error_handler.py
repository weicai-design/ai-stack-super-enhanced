"""
统一错误处理和日志系统
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, service_name: str):
        """
        初始化错误处理器
        
        Args:
            service_name: 服务名称
        """
        self.service_name = service_name
        
        # 配置日志
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        fh = logging.FileHandler(f'logs/{service_name}.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "last_error": None
        }
    
    def log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外信息
        """
        log_data = {
            "service": self.service_name,
            "level": level.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if extra:
            log_data["extra"] = extra
        
        # 根据级别记录
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_data, ensure_ascii=False))
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理异常
        
        Args:
            exception: 异常对象
            context: 上下文信息
        
        Returns:
            错误响应
        """
        # 获取异常信息
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # 更新统计
        self.error_stats["total_errors"] += 1
        self.error_stats["error_types"][error_type] = \
            self.error_stats["error_types"].get(error_type, 0) + 1
        self.error_stats["last_error"] = datetime.now().isoformat()
        
        # 构建错误信息
        error_info = {
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name
        }
        
        if context:
            error_info["context"] = context
        
        # 记录日志
        self.log(
            LogLevel.ERROR,
            f"{error_type}: {error_message}",
            {
                "stack_trace": stack_trace,
                "context": context
            }
        )
        
        # 返回错误响应
        return {
            "success": False,
            "error": error_info,
            "message": "操作失败，请查看日志获取详细信息"
        }
    
    def wrap_endpoint(self, func):
        """
        装饰器：包装API端点，自动处理错误
        
        Usage:
            @error_handler.wrap_endpoint
            async def my_endpoint():
                ...
        """
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return self.handle_exception(e, {
                    "endpoint": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                })
        
        return wrapper
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        return self.error_stats


# 全局错误处理器实例
error_handlers = {}


def get_error_handler(service_name: str) -> ErrorHandler:
    """
    获取或创建错误处理器
    
    Args:
        service_name: 服务名称
    
    Returns:
        错误处理器实例
    """
    if service_name not in error_handlers:
        error_handlers[service_name] = ErrorHandler(service_name)
    
    return error_handlers[service_name]

