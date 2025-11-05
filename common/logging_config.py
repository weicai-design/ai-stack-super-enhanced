"""
统一日志配置模块
所有服务共用的日志配置
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: str = None,
    enable_file_log: bool = True,
    enable_console_log: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    配置日志系统
    
    Args:
        service_name: 服务名称
        log_level: 日志级别
        log_dir: 日志目录
        enable_file_log: 是否启用文件日志
        enable_console_log: 是否启用控制台日志
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量
    """
    # 确定日志目录
    if log_dir is None:
        log_dir = os.path.join(
            Path(__file__).parent.parent,
            "logs"
        )
    
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志格式
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 添加控制台处理器
    if enable_console_log:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    if enable_file_log:
        # 主日志文件（所有日志）
        main_log_file = os.path.join(log_dir, f"{service_name}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志文件（仅错误）
        error_log_file = os.path.join(log_dir, f"{service_name}_error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    logger.info(f"日志系统已配置: {service_name}")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"日志目录: {log_dir}")


class RequestLogger:
    """请求日志记录器"""
    
    @staticmethod
    def log_request(
        method: str,
        path: str,
        params: Dict[str, Any] = None,
        body: Any = None,
        user_id: str = None
    ):
        """记录API请求"""
        logger.info(
            f"API请求 - {method} {path}",
            extra={
                "method": method,
                "path": path,
                "params": params,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def log_response(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        success: bool = True
    ):
        """记录API响应"""
        level = logging.INFO if success else logging.WARNING
        
        logger.log(
            level,
            f"API响应 - {method} {path} - {status_code} - {duration_ms:.2f}ms",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
        )


class PerformanceLogger:
    """性能日志记录器"""
    
    @staticmethod
    def log_slow_query(
        query_type: str,
        query: str,
        duration_ms: float,
        threshold_ms: float = 100
    ):
        """记录慢查询"""
        if duration_ms > threshold_ms:
            logger.warning(
                f"慢查询警告 - {query_type} - {duration_ms:.2f}ms",
                extra={
                    "query_type": query_type,
                    "query": query[:200],  # 只记录前200个字符
                    "duration_ms": duration_ms,
                    "threshold_ms": threshold_ms
                }
            )
    
    @staticmethod
    def log_operation(
        operation_name: str,
        duration_ms: float,
        metadata: Dict[str, Any] = None
    ):
        """记录操作性能"""
        logger.debug(
            f"操作耗时 - {operation_name} - {duration_ms:.2f}ms",
            extra={
                "operation": operation_name,
                "duration_ms": duration_ms,
                "metadata": metadata or {}
            }
        )


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.audit_logger = logging.getLogger(f"{service_name}.audit")
    
    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        result: str,
        details: Dict[str, Any] = None
    ):
        """记录用户操作审计"""
        self.audit_logger.info(
            f"审计 - 用户:{user_id} 操作:{action} 资源:{resource_type}:{resource_id} 结果:{result}",
            extra={
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "result": result,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )


# ==================== 使用示例 ====================

"""
使用示例:

1. 在FastAPI应用中配置日志:

from common.logging_config import setup_logging

# 启动时配置
setup_logging(
    service_name="erp-backend",
    log_level="INFO",
    enable_file_log=True,
    enable_console_log=True
)

2. 使用统一异常:

from common.error_handler import NotFoundError, ValidationError

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("用户", user_id)
    return user

3. 使用重试装饰器:

from common.error_handler import retry_on_error

@retry_on_error(max_retries=3, delay=1.0)
async def call_external_api():
    response = await http_client.get("https://api.example.com")
    return response.json()

4. 记录请求日志:

from common.logging_config import RequestLogger

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    RequestLogger.log_request(
        method=request.method,
        path=request.url.path,
        params=dict(request.query_params)
    )
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    RequestLogger.log_response(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    return response
"""


