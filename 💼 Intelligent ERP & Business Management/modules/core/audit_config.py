"""
审计日志配置模块
用于配置审计日志系统的各项参数
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class LogStorageType(Enum):
    """日志存储类型"""
    FILE = "file"
    DATABASE = "database"
    ELASTICSEARCH = "elasticsearch"


class RetentionPolicy(Enum):
    """日志保留策略"""
    SHORT_TERM = "short_term"  # 30天
    MEDIUM_TERM = "medium_term"  # 90天
    LONG_TERM = "long_term"  # 365天
    PERMANENT = "permanent"  # 永久保留


@dataclass
class AuditConfig:
    """审计日志配置类"""
    
    # 基本配置
    log_level: str = "INFO"
    storage_type: LogStorageType = LogStorageType.FILE
    retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM_TERM
    
    # 文件存储配置
    log_directory: str = "/var/log/erp/audit"
    max_file_size_mb: int = 100
    backup_count: int = 5
    
    # 数据库存储配置
    database_url: str = ""
    table_name: str = "audit_logs"
    
    # 性能配置
    batch_size: int = 100
    flush_interval_seconds: int = 30
    
    # 安全配置
    encrypt_logs: bool = True
    compress_logs: bool = True
    
    # 审计范围配置
    enable_user_audit: bool = True
    enable_system_audit: bool = True
    enable_business_audit: bool = True
    enable_security_audit: bool = True
    
    # 告警配置
    enable_alerting: bool = True
    alert_threshold: int = 10  # 10分钟内异常操作次数
    alert_email: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'log_level': self.log_level,
            'storage_type': self.storage_type.value,
            'retention_policy': self.retention_policy.value,
            'log_directory': self.log_directory,
            'max_file_size_mb': self.max_file_size_mb,
            'backup_count': self.backup_count,
            'database_url': self.database_url,
            'table_name': self.table_name,
            'batch_size': self.batch_size,
            'flush_interval_seconds': self.flush_interval_seconds,
            'encrypt_logs': self.encrypt_logs,
            'compress_logs': self.compress_logs,
            'enable_user_audit': self.enable_user_audit,
            'enable_system_audit': self.enable_system_audit,
            'enable_business_audit': self.enable_business_audit,
            'enable_security_audit': self.enable_security_audit,
            'enable_alerting': self.enable_alerting,
            'alert_threshold': self.alert_threshold,
            'alert_email': self.alert_email
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AuditConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)


# 默认配置
DEFAULT_CONFIG = AuditConfig()

# 开发环境配置
DEVELOPMENT_CONFIG = AuditConfig(
    log_level="DEBUG",
    log_directory="./logs/audit",
    enable_alerting=False,
    encrypt_logs=False
)

# 生产环境配置
PRODUCTION_CONFIG = AuditConfig(
    log_level="WARNING",
    retention_policy=RetentionPolicy.LONG_TERM,
    enable_alerting=True,
    alert_threshold=5
)


def get_config(environment: str = "development") -> AuditConfig:
    """根据环境获取配置"""
    configs = {
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "default": DEFAULT_CONFIG
    }
    return configs.get(environment, DEFAULT_CONFIG)


def validate_config(config: AuditConfig) -> bool:
    """验证配置有效性"""
    # 检查日志目录
    if config.storage_type == LogStorageType.FILE:
        if not config.log_directory:
            return False
        
        # 尝试创建目录
        try:
            os.makedirs(config.log_directory, exist_ok=True)
        except Exception:
            return False
    
    # 检查数据库配置
    if config.storage_type == LogStorageType.DATABASE:
        if not config.database_url:
            return False
    
    # 检查告警配置
    if config.enable_alerting and not config.alert_email:
        return False
    
    return True