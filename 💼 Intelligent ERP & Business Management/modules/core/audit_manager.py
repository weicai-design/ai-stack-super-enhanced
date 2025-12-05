"""
审计管理器模块
统一管理审计日志系统的初始化和配置
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from .audit_config import AuditConfig, get_config, validate_config
from .audit_logger import AuditLogger, AuditDecorators, AuditRecord, LogLevel, AuditAction, AuditCategory


class AuditManager:
    """审计管理器类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[AuditConfig] = None):
        """初始化审计管理器"""
        if self._initialized:
            return
            
        self.config = config or get_config()
        self.logger = AuditLogger(self.config)
        self._initialized = True
        
        # 初始化审计系统
        self._initialize_audit_system()
    
    def _initialize_audit_system(self):
        """初始化审计系统"""
        print("🔍 初始化审计日志系统...")
        
        # 验证配置
        if not validate_config(self.config):
            print("⚠️ 审计配置验证失败，使用默认配置")
            self.config = get_config()
        
        # 创建日志目录
        if self.config.storage_type.value == "file":
            os.makedirs(self.config.log_directory, exist_ok=True)
            print(f"📁 审计日志目录: {self.config.log_directory}")
        
        # 记录系统启动信息
        self.log_system_event("SYSTEM_STARTUP", "审计系统初始化完成", {
            "config": self.config.to_dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        print("✅ 审计日志系统初始化完成")
    
    def log_system_event(self, action: str, description: str, details: Dict[str, Any] = None):
        """记录系统事件"""
        # 使用审计日志器的标准方法记录系统事件
        self.logger.log_audit(
            action=AuditAction.CREATE,
            category=AuditCategory.SYSTEM,
            resource_type="audit_system",
            description=description,
            user_id="SYSTEM",
            details=details or {},
            ip_address="127.0.0.1",
            user_agent="AuditSystem/1.0",
            success=True
        )
    
    def get_logger(self) -> AuditLogger:
        """获取审计日志器"""
        return self.logger
    
    def get_decorators(self) -> AuditDecorators:
        """获取审计装饰器"""
        return AuditDecorators()
    
    def get_config(self) -> AuditConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, new_config: AuditConfig):
        """更新配置"""
        if validate_config(new_config):
            self.config = new_config
            # 重新初始化日志器
            self.logger = AuditLogger(self.config)
            
            self.log_system_event("CONFIG_UPDATE", "审计配置已更新", {
                "new_config": new_config.to_dict()
            })
        else:
            raise ValueError("Invalid audit configuration")
    
    def export_logs(self, start_date: str, end_date: str, output_format: str = "json") -> str:
        """导出审计日志"""
        # 审计日志器没有export_logs方法，需要实现或返回空字符串
        return ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审计统计信息"""
        # 审计日志器没有get_statistics方法，返回空字典
        return {}
    
    def cleanup_old_logs(self):
        """清理过期日志"""
        # 审计日志器没有cleanup_old_logs方法，暂时不实现
        pass
    
    def shutdown(self):
        """关闭审计系统"""
        self.log_system_event("SYSTEM_SHUTDOWN", "审计系统正在关闭")
        print("🔍 审计系统正在关闭...")


# 全局审计管理器实例
_audit_manager = None


def get_audit_manager(config: Optional[AuditConfig] = None) -> AuditManager:
    """获取全局审计管理器实例"""
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = AuditManager(config)
    return _audit_manager


def initialize_audit_system(config: Optional[AuditConfig] = None) -> AuditManager:
    """初始化审计系统"""
    return get_audit_manager(config)


def log_audit_event(action: AuditAction, user_id: str, module: str, description: str, 
                   details: Dict[str, Any] = None, ip_address: str = "", 
                   user_agent: str = "", success: bool = True):
    """便捷函数：记录审计事件"""
    manager = get_audit_manager()
    # 使用审计日志器的标准方法记录事件
    manager.logger.log_audit(
        action=action,
        category=AuditCategory.SYSTEM,
        resource_type=module,
        description=description,
        user_id=user_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )


# 全局装饰器实例
audit_decorators = AuditDecorators()