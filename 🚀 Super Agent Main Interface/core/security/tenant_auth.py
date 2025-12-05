#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多租户认证系统（生产级实现）
5.1: 多租户Token校验、API Key、命令白名单；更新tenant_context绑定
"""

from __future__ import annotations

import os
import json
import logging
import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional, List, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

import jwt
from fastapi import HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..tenant_context import TenantContext, get_current_tenant, set_current_tenant, reset_tenant
from ..tenant_manager import tenant_manager

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# API Key配置
API_KEY_STORAGE_PATH = Path(os.getenv("API_KEY_STORAGE_PATH", "data/api_keys.json"))
API_KEY_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

# 命令白名单配置
COMMAND_WHITELIST_STORAGE_PATH = Path(os.getenv("COMMAND_WHITELIST_STORAGE_PATH", "data/command_whitelist.json"))
COMMAND_WHITELIST_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


class AuthType(str, Enum):
    """认证类型"""
    TOKEN = "token"
    API_KEY = "api_key"
    NONE = "none"


@dataclass
class TokenPayload:
    """Token载荷"""
    tenant_id: str
    user_id: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


@dataclass
class APIKeyInfo:
    """API Key信息"""
    key_id: str
    key_hash: str  # 存储哈希值，不存储明文
    tenant_id: str
    name: str
    permissions: List[str] = field(default_factory=list)
    commands_whitelist: List[str] = field(default_factory=list)
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used_at: Optional[str] = None
    usage_count: int = 0


@dataclass
class TenantCommandWhitelist:
    """租户命令白名单"""
    tenant_id: str
    commands: List[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TenantAuthManager:
    """
    多租户认证管理器（生产级）
    
    功能：
    1. Token校验（JWT验证、租户绑定、过期检查）
    2. API Key验证（存储、验证、租户绑定、权限控制）
    3. 命令白名单（存储、验证、租户绑定、更新机制）
    4. Tenant Context绑定（从token/API Key提取租户信息）
    """
    
    def __init__(self):
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_expiration_hours = JWT_EXPIRATION_HOURS
        
        # API Key存储
        self.api_keys: Dict[str, APIKeyInfo] = {}
        self._load_api_keys()
        
        # 命令白名单存储
        self.command_whitelists: Dict[str, TenantCommandWhitelist] = {}
        self._load_command_whitelists()
        
        logger.info("多租户认证管理器初始化完成")
    
    # ============ Token管理 ============
    
    def create_token(
        self,
        tenant_id: str,
        user_id: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        expiration_hours: Optional[int] = None,
    ) -> str:
        """
        创建JWT Token
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            roles: 角色列表
            permissions: 权限列表
            expiration_hours: 过期时间（小时）
            
        Returns:
            JWT Token字符串
            
        Raises:
            ValueError: 租户不存在或未激活
        """
        # 验证租户状态
        self._validate_tenant_active(tenant_id)
        
        # 构建Token载荷
        payload = self._build_token_payload(
            tenant_id, user_id, roles, permissions, expiration_hours
        )
        
        # 生成JWT Token
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.info(f"创建Token: tenant_id={tenant_id}, user_id={user_id}")
        
        return token
    
    def _validate_tenant_active(self, tenant_id: str) -> None:
        """验证租户是否存在且激活"""
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant or not tenant.active:
            raise ValueError(f"租户不存在或未激活: {tenant_id}")
    
    def _build_token_payload(
        self,
        tenant_id: str,
        user_id: str,
        roles: Optional[List[str]],
        permissions: Optional[List[str]],
        expiration_hours: Optional[int],
    ) -> Dict[str, Any]:
        """构建Token载荷"""
        now = datetime.utcnow()
        exp_hours = expiration_hours or self.jwt_expiration_hours
        exp = now + timedelta(hours=exp_hours)
        
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "roles": roles or [],
            "permissions": permissions or [],
            "iat": now,
            "exp": exp,
        }
    
    def verify_token(self, token: str) -> TokenPayload:
        """
        验证JWT Token
        
        Args:
            token: JWT Token字符串
            
        Returns:
            Token载荷
            
        Raises:
            HTTPException: Token无效或过期
        """
        try:
            # 解码Token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
            
            # 验证租户
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token缺少租户信息",
                )
            
            tenant = tenant_manager.get_tenant(tenant_id)
            if not tenant or not tenant.active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"租户不存在或未激活: {tenant_id}",
                )
            
            # 构建Token载荷
            token_payload = TokenPayload(
                tenant_id=tenant_id,
                user_id=payload.get("user_id", "unknown"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
                iat=datetime.fromtimestamp(payload.get("iat", 0)),
            )
            
            logger.debug(f"Token验证成功: tenant_id={tenant_id}, user_id={token_payload.user_id}")
            
            return token_payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token无效: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Token验证失败: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token验证失败",
            )
    
    # ============ API Key管理 ============
    
    def _load_api_keys(self):
        """加载API Key"""
        if not API_KEY_STORAGE_PATH.exists():
            self._save_api_keys()
            return
        
        try:
            data = json.loads(API_KEY_STORAGE_PATH.read_text(encoding="utf-8"))
            self.api_keys = {
                key_id: APIKeyInfo(**info)
                for key_id, info in data.get("api_keys", {}).items()
            }
            logger.info(f"加载API Key: {len(self.api_keys)}个")
        except Exception as e:
            logger.error(f"加载API Key失败: {e}", exc_info=True)
            self.api_keys = {}
    
    def _save_api_keys(self):
        """保存API Key"""
        try:
            data = {
                "api_keys": {
                    key_id: asdict(info)
                    for key_id, info in self.api_keys.items()
                }
            }
            API_KEY_STORAGE_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"保存API Key失败: {e}", exc_info=True)
    
    def _hash_api_key(self, api_key: str) -> str:
        """计算API Key的哈希值"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: Optional[List[str]] = None,
        commands_whitelist: Optional[List[str]] = None,
    ) -> tuple[str, str]:
        """
        创建API Key
        
        Args:
            tenant_id: 租户ID
            name: API Key名称
            permissions: 权限列表
            commands_whitelist: 命令白名单
            
        Returns:
            (key_id, api_key) 元组
        """
        # 验证租户
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant or not tenant.active:
            raise ValueError(f"租户不存在或未激活: {tenant_id}")
        
        # 生成API Key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        key_id = f"key_{secrets.token_urlsafe(16)}"
        key_hash = self._hash_api_key(api_key)
        
        # 创建API Key信息
        api_key_info = APIKeyInfo(
            key_id=key_id,
            key_hash=key_hash,
            tenant_id=tenant_id,
            name=name,
            permissions=permissions or [],
            commands_whitelist=commands_whitelist or [],
            active=True,
        )
        
        self.api_keys[key_id] = api_key_info
        self._save_api_keys()
        
        logger.info(f"创建API Key: key_id={key_id}, tenant_id={tenant_id}, name={name}")
        
        return (key_id, api_key)
    
    def verify_api_key(self, api_key: str) -> APIKeyInfo:
        """
        验证API Key
        
        Args:
            api_key: API Key字符串
            
        Returns:
            API Key信息
            
        Raises:
            HTTPException: API Key无效或未激活
        """
        key_hash = self._hash_api_key(api_key)
        
        # 查找匹配的API Key
        for key_id, info in self.api_keys.items():
            if hmac.compare_digest(info.key_hash, key_hash):
                # 验证状态
                if not info.active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="API Key未激活",
                    )
                
                # 验证租户
                tenant = tenant_manager.get_tenant(info.tenant_id)
                if not tenant or not tenant.active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"租户不存在或未激活: {info.tenant_id}",
                    )
                
                # 更新使用统计
                info.last_used_at = datetime.now().isoformat()
                info.usage_count += 1
                self._save_api_keys()
                
                logger.debug(f"API Key验证成功: key_id={key_id}, tenant_id={info.tenant_id}")
                
                return info
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key无效",
        )
    
    def revoke_api_key(self, key_id: str) -> bool:
        """撤销API Key"""
        if key_id not in self.api_keys:
            return False
        
        self.api_keys[key_id].active = False
        self._save_api_keys()
        
        logger.info(f"撤销API Key: key_id={key_id}")
        
        return True
    
    # ============ 命令白名单管理 ============
    
    def _load_command_whitelists(self):
        """加载命令白名单"""
        if not COMMAND_WHITELIST_STORAGE_PATH.exists():
            self._save_command_whitelists()
            return
        
        try:
            data = json.loads(COMMAND_WHITELIST_STORAGE_PATH.read_text(encoding="utf-8"))
            self.command_whitelists = {
                tenant_id: TenantCommandWhitelist(**info)
                for tenant_id, info in data.get("whitelists", {}).items()
            }
            logger.info(f"加载命令白名单: {len(self.command_whitelists)}个租户")
        except Exception as e:
            logger.error(f"加载命令白名单失败: {e}", exc_info=True)
            self.command_whitelists = {}
    
    def _save_command_whitelists(self):
        """保存命令白名单"""
        try:
            data = {
                "whitelists": {
                    tenant_id: asdict(whitelist)
                    for tenant_id, whitelist in self.command_whitelists.items()
                }
            }
            COMMAND_WHITELIST_STORAGE_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"保存命令白名单失败: {e}", exc_info=True)
    
    def get_command_whitelist(self, tenant_id: str) -> List[str]:
        """获取租户的命令白名单"""
        whitelist = self.command_whitelists.get(tenant_id)
        if whitelist:
            return whitelist.commands
        
        # 返回默认白名单
        return []
    
    def update_command_whitelist(
        self,
        tenant_id: str,
        commands: List[str],
    ) -> bool:
        """
        更新租户的命令白名单
        
        Args:
            tenant_id: 租户ID
            commands: 命令列表
            
        Returns:
            是否成功
        """
        # 验证租户
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        
        whitelist = TenantCommandWhitelist(
            tenant_id=tenant_id,
            commands=commands,
            updated_at=datetime.now().isoformat(),
        )
        
        self.command_whitelists[tenant_id] = whitelist
        self._save_command_whitelists()
        
        logger.info(f"更新命令白名单: tenant_id={tenant_id}, commands={len(commands)}个")
        
        return True
    
    def check_command_allowed(self, tenant_id: str, command: str) -> bool:
        """
        检查命令是否在白名单中
        
        Args:
            tenant_id: 租户ID
            command: 命令
            
        Returns:
            是否允许
        """
        whitelist = self.get_command_whitelist(tenant_id)
        
        # 检查完整命令
        if command in whitelist:
            return True
        
        # 检查命令前缀（支持通配符）
        command_base = command.split()[0] if command else ""
        if command_base in whitelist:
            return True
        
        return False
    
    # ============ 认证依赖注入 ============
    
    async def authenticate_request(
        self,
        request: Request,
        authorization: Optional[str] = Header(None),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    ) -> Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo]]:
        """
        认证请求（从请求头提取认证信息）
        
        Args:
            request: FastAPI请求对象
            authorization: Authorization头
            x_api_key: X-API-Key头
            
        Returns:
            (auth_type, token_payload, api_key_info) 元组
        """
        # 优先检查API Key
        if x_api_key:
            try:
                api_key_info = self.verify_api_key(x_api_key)
                return (AuthType.API_KEY, None, api_key_info)
            except HTTPException:
                raise
        
        # 检查Bearer Token
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # 移除"Bearer "前缀
            try:
                token_payload = self.verify_token(token)
                return (AuthType.TOKEN, token_payload, None)
            except HTTPException:
                raise
        
        # 无认证信息
        return (AuthType.NONE, None, None)
    
    def bind_tenant_context(
        self,
        request: Request,
        auth_type: AuthType,
        token_payload: Optional[TokenPayload] = None,
        api_key_info: Optional[APIKeyInfo] = None,
    ) -> TenantContext:
        """
        绑定Tenant Context（从认证信息提取租户信息）
        
        Args:
            request: FastAPI请求对象
            auth_type: 认证类型
            token_payload: Token载荷
            api_key_info: API Key信息
            
        Returns:
            TenantContext对象
        """
        tenant_id = None
        
        if auth_type == AuthType.TOKEN and token_payload:
            tenant_id = token_payload.tenant_id
        elif auth_type == AuthType.API_KEY and api_key_info:
            tenant_id = api_key_info.tenant_id
        else:
            # 从请求头或查询参数获取租户ID（向后兼容）
            tenant_id = (
                request.headers.get("X-Tenant-ID")
                or request.query_params.get("tenant_id")
                or "global"
            )
        
        # 获取租户信息
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            tenant = tenant_manager.get_tenant("global")
        
        # 创建Tenant Context
        tenant_context = TenantContext(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            metadata={
                **tenant.metadata,
                "auth_type": auth_type.value,
                "user_id": (
                    token_payload.user_id if token_payload
                    else api_key_info.name if api_key_info
                    else "anonymous"
                ),
            },
        )
        
        # 设置到请求状态
        request.state.tenant_context = tenant_context
        
        # 设置到ContextVar
        set_current_tenant(tenant_context)
        
        logger.debug(f"绑定Tenant Context: tenant_id={tenant_id}, auth_type={auth_type.value}")
        
        return tenant_context


# 单例实例
_auth_manager_instance: Optional[TenantAuthManager] = None


def get_tenant_auth_manager() -> TenantAuthManager:
    """获取多租户认证管理器实例（单例模式）"""
    global _auth_manager_instance
    
    if _auth_manager_instance is None:
        _auth_manager_instance = TenantAuthManager()
    
    return _auth_manager_instance


# FastAPI依赖
security = HTTPBearer(auto_error=False)


async def get_tenant_auth(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], TenantContext]:
    """
    FastAPI依赖：获取租户认证信息并绑定Tenant Context
    
    Returns:
        (auth_type, token_payload, api_key_info, tenant_context) 元组
    """
    auth_manager = get_tenant_auth_manager()
    
    # 认证请求
    auth_type, token_payload, api_key_info = await auth_manager.authenticate_request(
        request=request,
        authorization=authorization,
        x_api_key=x_api_key,
    )
    
    # 绑定Tenant Context
    tenant_context = auth_manager.bind_tenant_context(
        request=request,
        auth_type=auth_type,
        token_payload=token_payload,
        api_key_info=api_key_info,
    )
    
    return (auth_type, token_payload, api_key_info, tenant_context)


__all__ = [
    "TenantAuthManager",
    "TokenPayload",
    "APIKeyInfo",
    "TenantCommandWhitelist",
    "AuthType",
    "get_tenant_auth_manager",
    "get_tenant_auth",
]

