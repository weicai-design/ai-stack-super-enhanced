"""
日志记录和审计模块
Logging and Auditing Module

功能：
1. 自动记录 API Key 操作
2. 自动记录 Token 操作
3. 审计日志查询
4. 日志中间件

版本: v3.1.0
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .database import get_database

logger = logging.getLogger(__name__)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self):
        """初始化审计日志记录器"""
        self.db = None
        try:
            self.db = get_database()
            logger.info("✅ 审计日志记录器已初始化（使用数据库）")
        except Exception as e:
            logger.warning(f"审计日志数据库初始化失败，使用文件日志: {e}")
    
    def log_api_key_action(
        self,
        tenant_id: str,
        action: str,
        api_key_id: Optional[str] = None,
        api_key_name: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录 API Key 操作
        
        Args:
            tenant_id: 租户ID
            action: 操作类型（create/update/revoke/verify/failed）
            api_key_id: API Key ID
            api_key_name: API Key 名称
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User Agent
            details: 详细信息
        """
        log_details = {
            "api_key_id": api_key_id,
            "api_key_name": api_key_name,
            **(details or {})
        }
        
        self._log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type="api_key",
            resource_id=api_key_id,
            details=log_details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_token_action(
        self,
        tenant_id: str,
        action: str,
        token_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录 Token 操作
        
        Args:
            tenant_id: 租户ID
            action: 操作类型（create/verify/revoke/failed）
            token_id: Token ID (JWT jti)
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User Agent
            details: 详细信息
        """
        log_details = {
            "token_id": token_id,
            **(details or {})
        }
        
        self._log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type="token",
            resource_id=token_id,
            details=log_details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_command_action(
        self,
        tenant_id: str,
        action: str,
        command: str,
        allowed: bool,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录命令操作
        
        Args:
            tenant_id: 租户ID
            action: 操作类型（execute/denied）
            command: 命令字符串
            allowed: 是否允许
            user_id: 用户ID
            api_key_id: API Key ID
            ip_address: IP地址
            user_agent: User Agent
            details: 详细信息
        """
        log_details = {
            "command": command,
            "allowed": allowed,
            "api_key_id": api_key_id,
            **(details or {})
        }
        
        self._log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type="command",
            resource_id=None,
            details=log_details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_tenant_action(
        self,
        tenant_id: str,
        action: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        记录租户相关操作
        
        Args:
            tenant_id: 租户ID
            action: 操作类型（login/logout/access_denied/cross_tenant_attempt）
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User Agent
            details: 详细信息
        """
        self._log(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type="tenant",
            resource_id=tenant_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _log(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        内部日志记录方法
        
        Args:
            tenant_id: 租户ID
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User Agent
        """
        # 记录到数据库（如果可用）
        if self.db:
            try:
                self.db.add_audit_log(
                    tenant_id=tenant_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                logger.error(f"记录审计日志到数据库失败: {e}")
        
        # 同时记录到文件日志
        log_message = f"[{tenant_id}] {action} {resource_type}"
        if resource_id:
            log_message += f" ({resource_id})"
        if user_id:
            log_message += f" by {user_id}"
        
        if details:
            log_message += f" - {json.dumps(details, ensure_ascii=False)}"
        
        # 根据操作类型选择日志级别
        if action.endswith("_failed") or action == "denied" or action == "access_denied":
            logger.warning(log_message)
        elif action == "cross_tenant_attempt":
            logger.error(log_message)
        else:
            logger.info(log_message)
    
    def get_audit_logs(
        self,
        tenant_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取审计日志
        
        Args:
            tenant_id: 租户ID（可选，用于过滤）
            action: 操作类型（可选，用于过滤）
            resource_type: 资源类型（可选，用于过滤）
            limit: 返回数量限制
        
        Returns:
            审计日志列表
        """
        if not self.db:
            return []
        
        try:
            logs = self.db.get_audit_logs(tenant_id=tenant_id, action=action, limit=limit)
            
            # 如果指定了资源类型，进行过滤
            if resource_type:
                logs = [log for log in logs if log.get("resource_type") == resource_type]
            
            return logs
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return []


# ==================== 全局实例 ====================

audit_logger = AuditLogger()


# ==================== 请求日志中间件 ====================

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """审计日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并记录日志"""
        
        # 跳过某些路径
        skip_paths = [
            "/health",
            "/readyz",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/gateway/health"
        ]
        
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # 获取请求信息
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 记录访问
        if tenant_id:
            try:
                audit_logger.log_tenant_action(
                    tenant_id=tenant_id,
                    action="access",
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params)
                    }
                )
            except Exception as e:
                logger.debug(f"记录访问日志失败: {e}")
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 记录错误（如果状态码 >= 400）
            if tenant_id and response.status_code >= 400:
                try:
                    audit_logger.log_tenant_action(
                        tenant_id=tenant_id,
                        action="error",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code
                        }
                    )
                except Exception as e:
                    logger.debug(f"记录错误日志失败: {e}")
            
            return response
            
        except Exception as e:
            # 记录异常
            if tenant_id:
                try:
                    audit_logger.log_tenant_action(
                        tenant_id=tenant_id,
                        action="exception",
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "error": str(e)
                        }
                    )
                except Exception:
                    pass
            
            raise


# ==================== 辅助函数 ====================

def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端 IP 地址"""
    if request.client:
        return request.client.host
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """获取 User Agent"""
    return request.headers.get("user-agent")


# ==================== 导出 ====================

__all__ = [
    "AuditLogger",
    "audit_logger",
    "AuditLoggingMiddleware",
    "get_client_ip",
    "get_user_agent"
]




