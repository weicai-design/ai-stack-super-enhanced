"""
ERP API Configuration
ERP API配置管理

生产级API配置和性能优化设置
"""

import os
from typing import Dict, Any, List
from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API配置类"""
    
    # API基础配置
    api_title: str = "ERP Backend API - 生产版"
    api_description: str = "智能ERP系统后端API - 企业级生产环境"
    api_version: str = "2.5.0"
    api_docs_url: str = "/docs"
    api_redoc_url: str = "/redoc"
    
    # 性能配置
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30  # 30秒
    rate_limit_requests: int = 100  # 每分钟最大请求数
    rate_limit_window: int = 60  # 时间窗口（秒）
    
    # 数据库配置
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5分钟
    cache_max_size: int = 1000
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/erp_api.log"
    
    # 安全配置
    cors_origins: List[str] = [
        "http://localhost:8012",
        "http://127.0.0.1:8012", 
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://erp.example.com"  # 生产环境域名
    ]
    
    # 监控配置
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30  # 健康检查间隔（秒）
    
    # 环境配置
    environment: str = "production"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_prefix = "ERP_API_"


# 全局配置实例
config = APIConfig()


def get_api_config() -> APIConfig:
    """获取API配置"""
    return config


def setup_logging():
    """配置日志系统"""
    import logging
    from logging.handlers import RotatingFileHandler
    
    # 创建日志目录
    log_dir = os.path.dirname(config.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level))
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        config.log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(config.log_format))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.log_format))
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def get_cors_config() -> Dict[str, Any]:
    """获取CORS配置"""
    return {
        "allow_origins": config.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
    }


def get_database_config() -> Dict[str, Any]:
    """获取数据库连接配置"""
    return {
        "pool_size": config.db_pool_size,
        "max_overflow": config.db_max_overflow,
        "pool_timeout": config.db_pool_timeout,
        "pool_recycle": config.db_pool_recycle,
    }


# API端点配置
API_ENDPOINT_CONFIG = {
    "finance": {
        "cache_ttl": 60,  # 财务数据缓存1分钟
        "rate_limit": 50,  # 每分钟50次
        "timeout": 10,     # 10秒超时
    },
    "analytics": {
        "cache_ttl": 300,  # 分析数据缓存5分钟
        "rate_limit": 30,  # 每分钟30次
        "timeout": 30,     # 30秒超时
    },
    "customer": {
        "cache_ttl": 120,  # 客户数据缓存2分钟
        "rate_limit": 100, # 每分钟100次
        "timeout": 15,     # 15秒超时
    },
    "process": {
        "cache_ttl": 180,  # 流程数据缓存3分钟
        "rate_limit": 80,  # 每分钟80次
        "timeout": 20,     # 20秒超时
    },
    "production": {
        "cache_ttl": 90,   # 生产数据缓存1.5分钟
        "rate_limit": 60,  # 每分钟60次
        "timeout": 25,     # 25秒超时
    },
}


def get_endpoint_config(endpoint_type: str) -> Dict[str, Any]:
    """获取特定端点的配置"""
    return API_ENDPOINT_CONFIG.get(endpoint_type, {
        "cache_ttl": 60,
        "rate_limit": 100,
        "timeout": 15,
    })