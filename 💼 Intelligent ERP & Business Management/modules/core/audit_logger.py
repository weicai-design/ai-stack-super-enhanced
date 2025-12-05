"""
T013和T014模块审计日志系统
实现生产级日志记录和审计追踪功能
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .audit_config import AuditConfig, get_config, validate_config


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditAction(Enum):
    """审计动作类型"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    COMPLETE = "COMPLETE"
    CANCEL = "CANCEL"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class AuditCategory(Enum):
    """审计分类"""
    PROJECT = "PROJECT"
    PROCUREMENT = "PROCUREMENT"
    USER = "USER"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    DATA = "DATA"
    FINANCE = "FINANCE"


@dataclass
class AuditRecord:
    """审计记录"""
    id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    action: AuditAction
    category: AuditCategory
    resource_type: str
    resource_id: Optional[str]
    description: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['action'] = self.action.value
        data['category'] = self.category.value
        return data


class AuditLogger:
    """审计日志器"""
    
    def __init__(self, config: Optional[AuditConfig] = None, log_file: str = "audit.log", log_level: LogLevel = LogLevel.INFO):
        """初始化审计日志器"""
        self.config = config or get_config()
        self.log_file = log_file
        self.log_level = log_level
        self.records: List[AuditRecord] = []
        
        # 配置日志记录器
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志记录器"""
        # 验证配置
        if not validate_config(self.config):
            raise ValueError("Invalid audit configuration")
        
        # 根据配置设置日志文件路径
        if self.config.storage_type.value == "file":
            import os
            self.log_file = os.path.join(self.config.log_directory, "audit.log")
        
        # 确保日志目录存在
        import os
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 创建审计日志记录器
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not self.audit_logger.handlers:
            # 文件handler
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.INFO)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            self.audit_logger.addHandler(file_handler)
    
    def log_audit(
        self,
        action: AuditAction,
        category: AuditCategory,
        resource_type: str,
        description: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditRecord:
        """
        记录审计日志
        
        Args:
            action: 审计动作
            category: 审计分类
            resource_type: 资源类型
            description: 描述信息
            user_id: 用户ID
            session_id: 会话ID
            resource_id: 资源ID
            details: 详细信息
            ip_address: IP地址
            user_agent: 用户代理
            success: 是否成功
            error_message: 错误信息
            
        Returns:
            AuditRecord: 审计记录
        """
        audit_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        if details is None:
            details = {}
        
        # 创建审计记录
        record = AuditRecord(
            id=audit_id,
            timestamp=timestamp,
            user_id=user_id,
            session_id=session_id,
            action=action,
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        # 存储记录
        self.records.append(record)
        
        # 记录到日志文件
        log_data = record.to_dict()
        log_message = json.dumps(log_data, ensure_ascii=False)
        
        if success:
            self.audit_logger.info(log_message)
        else:
            self.audit_logger.error(log_message)
        
        return record
    
    def get_audit_records(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        category: Optional[AuditCategory] = None,
        resource_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditRecord]:
        """
        获取审计记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            user_id: 用户ID
            action: 动作类型
            category: 分类
            resource_type: 资源类型
            limit: 限制数量
            
        Returns:
            List[AuditRecord]: 审计记录列表
        """
        filtered_records = self.records.copy()
        
        # 时间过滤
        if start_time:
            filtered_records = [r for r in filtered_records if r.timestamp >= start_time]
        if end_time:
            filtered_records = [r for r in filtered_records if r.timestamp <= end_time]
        
        # 用户过滤
        if user_id:
            filtered_records = [r for r in filtered_records if r.user_id == user_id]
        
        # 动作过滤
        if action:
            filtered_records = [r for r in filtered_records if r.action == action]
        
        # 分类过滤
        if category:
            filtered_records = [r for r in filtered_records if r.category == category]
        
        # 资源类型过滤
        if resource_type:
            filtered_records = [r for r in filtered_records if r.resource_type == resource_type]
        
        # 排序和限制
        filtered_records.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_records[:limit]
    
    def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取审计统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        records = self.get_audit_records(start_time, end_time)
        
        # 按动作统计
        action_stats = {}
        for action in AuditAction:
            action_stats[action.value] = sum(1 for r in records if r.action == action)
        
        # 按分类统计
        category_stats = {}
        for category in AuditCategory:
            category_stats[category.value] = sum(1 for r in records if r.category == category)
        
        # 按用户统计
        user_stats = {}
        for record in records:
            if record.user_id:
                user_stats[record.user_id] = user_stats.get(record.user_id, 0) + 1
        
        # 成功率统计
        success_count = sum(1 for r in records if r.success)
        failure_count = len(records) - success_count
        
        return {
            "total_records": len(records),
            "success_rate": success_count / len(records) if records else 0,
            "action_distribution": action_stats,
            "category_distribution": category_stats,
            "user_activity": dict(sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            "success_count": success_count,
            "failure_count": failure_count
        }
    
    def export_audit_logs(self, file_path: str, format: str = "json"):
        """
        导出审计日志
        
        Args:
            file_path: 文件路径
            format: 导出格式 (json, csv)
        """
        records = self.records
        
        if format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)
        
        elif format == "csv":
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if records:
                    fieldnames = list(records[0].to_dict().keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for record in records:
                        writer.writerow(record.to_dict())


# 全局审计日志器实例
audit_logger = AuditLogger()


def audit_log_decorator(
    action: AuditAction,
    category: AuditCategory,
    resource_type: str,
    description: str
):
    """审计日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 提取用户信息（从参数或上下文）
            user_id = None
            resource_id = None
            
            # 尝试从参数中提取用户ID和资源ID
            if args and len(args) > 0:
                # 假设第一个参数是self（实例方法）
                if len(args) > 1:
                    # 尝试从参数中提取资源ID
                    for arg in args[1:]:
                        if isinstance(arg, str) and len(arg) > 10:
                            resource_id = arg
                            break
            
            # 执行函数
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                
                # 如果函数返回字典，尝试提取资源ID
                if isinstance(result, dict) and 'id' in result:
                    resource_id = result['id']
                
                return result
            
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            
            finally:
                # 记录审计日志
                execution_time = time.time() - start_time
                
                details = {
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "success": success
                }
                
                audit_logger.log_audit(
                    action=action,
                    category=category,
                    resource_type=resource_type,
                    description=description,
                    user_id=user_id,
                    resource_id=resource_id,
                    details=details,
                    success=success,
                    error_message=error_message
                )
        
        return wrapper
    return decorator


# 预定义的审计装饰器
class AuditDecorators:
    """预定义审计装饰器"""
    
    @staticmethod
    def project_create():
        """项目创建审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROJECT,
            resource_type="project",
            description="创建新项目"
        )
    
    @staticmethod
    def project_update():
        """项目更新审计"""
        return audit_log_decorator(
            action=AuditAction.UPDATE,
            category=AuditCategory.PROJECT,
            resource_type="project",
            description="更新项目信息"
        )
    
    @staticmethod
    def procurement_order_create():
        """采购订单创建审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROCUREMENT,
            resource_type="procurement_order",
            description="创建采购订单"
        )
    
    @staticmethod
    def purchase_request_create():
        """采购申请创建审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROCUREMENT,
            resource_type="purchase_request",
            description="创建采购申请"
        )
    
    @staticmethod
    def milestone_complete():
        """里程碑完成审计"""
        return audit_log_decorator(
            action=AuditAction.COMPLETE,
            category=AuditCategory.PROJECT,
            resource_type="milestone",
            description="完成项目里程碑"
        )
    
    @staticmethod
    def approval_action():
        """审批操作审计"""
        return audit_log_decorator(
            action=AuditAction.APPROVE,
            category=AuditCategory.SYSTEM,
            resource_type="approval",
            description="执行审批操作"
        )
    
    @staticmethod
    def project_status_update():
        """项目状态更新审计"""
        return audit_log_decorator(
            action=AuditAction.UPDATE,
            category=AuditCategory.PROJECT,
            resource_type="project_status",
            description="更新项目状态"
        )
    
    @staticmethod
    def resource_allocate():
        """资源分配审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROJECT,
            resource_type="resource_allocation",
            description="分配项目资源"
        )
    
    @staticmethod
    def document_upload():
        """文档上传审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.DATA,
            resource_type="document",
            description="上传项目文档"
        )
    
    @staticmethod
    def communication_log():
        """沟通记录审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROJECT,
            resource_type="communication",
            description="记录项目沟通"
        )
    
    @staticmethod
    def budget_update():
        """预算更新审计"""
        return audit_log_decorator(
            action=AuditAction.UPDATE,
            category=AuditCategory.FINANCE,
            resource_type="project_budget",
            description="更新项目预算"
        )
    
    @staticmethod
    def change_request():
        """变更请求审计"""
        return audit_log_decorator(
            action=AuditAction.CREATE,
            category=AuditCategory.PROJECT,
            resource_type="change_request",
            description="提交项目变更请求"
        )
    
    @staticmethod
    def quality_check():
        """质量检查审计"""
        return audit_log_decorator(
            action=AuditAction.READ,
            category=AuditCategory.PROJECT,
            resource_type="quality_check",
            description="执行项目质量检查"
        )
    
    @staticmethod
    def team_assignment():
        """团队分配审计"""
        return audit_log_decorator(
            action=AuditAction.UPDATE,
            category=AuditCategory.PROJECT,
            resource_type="team_assignment",
            description="分配项目团队成员"
        )