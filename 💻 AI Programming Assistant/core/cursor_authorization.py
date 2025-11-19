"""
Cursor授权与权限隔离系统
P0-016: 集成 Cursor（协议/插件/本地桥，授权与权限隔离）
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class AuthorizationLevel(Enum):
    """授权级别"""
    NONE = "none"  # 无授权
    READ_ONLY = "read_only"  # 只读
    LIMITED = "limited"  # 受限
    STANDARD = "standard"  # 标准
    FULL = "full"  # 完全授权


class AccessScope(Enum):
    """访问范围"""
    SINGLE_FILE = "single_file"  # 单个文件
    PROJECT = "project"  # 项目
    WORKSPACE = "workspace"  # 工作区
    SYSTEM = "system"  # 系统级


@dataclass
class AuthorizationToken:
    """授权令牌"""
    token_id: str
    client_id: str
    authorization_level: AuthorizationLevel
    access_scope: AccessScope
    allowed_paths: List[str] = field(default_factory=list)
    denied_paths: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessRequest:
    """访问请求"""
    request_id: str
    client_id: str
    resource_type: str  # file, command, network, system
    resource_path: str
    action: str  # read, write, execute
    requested_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CursorAuthorization:
    """
    Cursor授权与权限隔离系统
    
    功能：
    1. 令牌管理
    2. 权限验证
    3. 访问控制
    4. 审计日志
    5. 权限隔离
    """
    
    def __init__(self):
        self.tokens: Dict[str, AuthorizationToken] = {}
        self.access_requests: List[AccessRequest] = []
        self.audit_log: List[Dict[str, Any]] = []
        
        # 默认权限策略
        self.default_permissions = {
            AuthorizationLevel.NONE: [],
            AuthorizationLevel.READ_ONLY: ["read_file"],
            AuthorizationLevel.LIMITED: ["read_file", "get_completion"],
            AuthorizationLevel.STANDARD: ["read_file", "write_file", "get_completion", "detect_errors"],
            AuthorizationLevel.FULL: ["read_file", "write_file", "execute_command", "access_network", "access_system"]
        }
        
        logger.info("Cursor授权系统初始化完成")
    
    def create_token(
        self,
        client_id: str,
        authorization_level: AuthorizationLevel,
        access_scope: AccessScope,
        allowed_paths: Optional[List[str]] = None,
        denied_paths: Optional[List[str]] = None,
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuthorizationToken:
        """
        创建授权令牌
        
        Args:
            client_id: 客户端ID
            authorization_level: 授权级别
            access_scope: 访问范围
            allowed_paths: 允许的路径列表
            denied_paths: 拒绝的路径列表
            expires_in_hours: 过期时间（小时）
            metadata: 元数据
            
        Returns:
            授权令牌
        """
        token_id = self._generate_token_id(client_id)
        
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        permissions = self.default_permissions.get(authorization_level, [])
        
        token = AuthorizationToken(
            token_id=token_id,
            client_id=client_id,
            authorization_level=authorization_level,
            access_scope=access_scope,
            allowed_paths=allowed_paths or [],
            denied_paths=denied_paths or [],
            permissions=permissions,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.tokens[token_id] = token
        
        # 记录审计日志
        self._log_access(
            "token_created",
            client_id=client_id,
            token_id=token_id,
            authorization_level=authorization_level.value,
            access_scope=access_scope.value
        )
        
        logger.info(f"已创建授权令牌: {token_id} ({authorization_level.value})")
        return token
    
    def _generate_token_id(self, client_id: str) -> str:
        """生成令牌ID"""
        timestamp = datetime.now().isoformat()
        data = f"{client_id}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def validate_token(self, token_id: str) -> bool:
        """验证令牌"""
        if token_id not in self.tokens:
            return False
        
        token = self.tokens[token_id]
        
        # 检查是否过期
        if token.expires_at and datetime.now() > token.expires_at:
            self._log_access("token_expired", token_id=token_id)
            return False
        
        # 更新最后使用时间
        token.last_used = datetime.now()
        
        return True
    
    def check_permission(
        self,
        token_id: str,
        resource_type: str,
        resource_path: str,
        action: str
    ) -> bool:
        """
        检查权限
        
        Args:
            token_id: 令牌ID
            resource_type: 资源类型
            resource_path: 资源路径
            action: 操作
            
        Returns:
            是否有权限
        """
        if not self.validate_token(token_id):
            return False
        
        token = self.tokens[token_id]
        
        # 检查路径是否在拒绝列表中
        if self._is_path_denied(resource_path, token.denied_paths):
            self._log_access(
                "access_denied",
                token_id=token_id,
                reason="path_denied",
                resource_path=resource_path
            )
            return False
        
        # 检查路径是否在允许列表中（如果有）
        if token.allowed_paths and not self._is_path_allowed(resource_path, token.allowed_paths):
            self._log_access(
                "access_denied",
                token_id=token_id,
                reason="path_not_allowed",
                resource_path=resource_path
            )
            return False
        
        # 检查操作权限
        required_permission = f"{action}_{resource_type}"
        if required_permission not in token.permissions:
            # 检查通配符权限
            if f"{action}_*" not in token.permissions and "*" not in token.permissions:
                self._log_access(
                    "access_denied",
                    token_id=token_id,
                    reason="permission_denied",
                    required_permission=required_permission
                )
                return False
        
        # 记录访问
        self._log_access(
            "access_granted",
            token_id=token_id,
            resource_type=resource_type,
            resource_path=resource_path,
            action=action
        )
        
        return True
    
    def _is_path_denied(self, path: str, denied_paths: List[str]) -> bool:
        """检查路径是否被拒绝"""
        for denied_path in denied_paths:
            if path.startswith(denied_path) or denied_path in path:
                return True
        return False
    
    def _is_path_allowed(self, path: str, allowed_paths: List[str]) -> bool:
        """检查路径是否被允许"""
        if not allowed_paths:
            return True  # 如果没有限制，则允许
        
        for allowed_path in allowed_paths:
            if path.startswith(allowed_path) or allowed_path in path:
                return True
        return False
    
    def revoke_token(self, token_id: str, reason: Optional[str] = None):
        """撤销令牌"""
        if token_id in self.tokens:
            token = self.tokens[token_id]
            del self.tokens[token_id]
            
            self._log_access(
                "token_revoked",
                token_id=token_id,
                client_id=token.client_id,
                reason=reason or "manual_revocation"
            )
            
            logger.info(f"已撤销授权令牌: {token_id}")
    
    def get_token(self, token_id: str) -> Optional[AuthorizationToken]:
        """获取令牌"""
        return self.tokens.get(token_id)
    
    def list_tokens(self, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出令牌"""
        tokens = self.tokens.values()
        if client_id:
            tokens = [t for t in tokens if t.client_id == client_id]
        
        return [
            {
                "token_id": t.token_id,
                "client_id": t.client_id,
                "authorization_level": t.authorization_level.value,
                "access_scope": t.access_scope.value,
                "created_at": t.created_at.isoformat(),
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "last_used": t.last_used.isoformat() if t.last_used else None,
                "is_valid": self.validate_token(t.token_id)
            }
            for t in tokens
        ]
    
    def _log_access(self, event_type: str, **kwargs):
        """记录访问日志"""
        log_entry = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.audit_log.append(log_entry)
        
        # 保留最近10000条
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def get_audit_log(
        self,
        token_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        logs = self.audit_log
        
        if token_id:
            logs = [l for l in logs if l.get("token_id") == token_id]
        
        if event_type:
            logs = [l for l in logs if l.get("event_type") == event_type]
        
        return logs[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        valid_tokens = [t for t in self.tokens.values() if self.validate_token(t.token_id)]
        expired_tokens = [t for t in self.tokens.values() if t.expires_at and datetime.now() > t.expires_at]
        
        level_counts = {}
        for token in self.tokens.values():
            level = token.authorization_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_tokens": len(self.tokens),
            "valid_tokens": len(valid_tokens),
            "expired_tokens": len(expired_tokens),
            "level_distribution": level_counts,
            "total_access_requests": len(self.access_requests),
            "audit_log_entries": len(self.audit_log)
        }



