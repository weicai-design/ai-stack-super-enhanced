"""
多租户认证和授权 API 端点
Multi-tenant Authentication and Authorization API Endpoints

功能：
1. Token 生成和管理
2. API Key 创建、列表、撤销
3. 命令白名单管理
4. 租户上下文查询

版本: v3.1.0
"""

from __future__ import annotations

import logging
from typing import List, Optional
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from .auth import (
    token_service,
    api_key_service,
    APIKeyService,
    APIKey,
    APIKeyScope,
    CommandWhitelist,
    require_tenant_from_token,
    require_tenant_from_api_key,
    get_tenant_context
)
from .middleware import require_tenant, get_current_tenant
from .models import Tenant
from .audit_logging import audit_logger, get_client_ip, get_user_agent
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenant/auth", tags=["多租户认证"])


# ==================== 请求模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    tenant_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None  # 可选，用于验证用户


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    tenant_id: str
    tenant_name: str


class CreateAPIKeyRequest(BaseModel):
    """创建 API Key 请求"""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[APIKeyScope] = Field(default_factory=lambda: [APIKeyScope.READ])
    allowed_commands: Optional[List[str]] = Field(None, description="允许的命令列表")
    rate_limit: Optional[int] = Field(None, ge=1, description="速率限制（每分钟）")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="过期天数")


class APIKeyResponse(BaseModel):
    """API Key 响应"""
    api_key: str
    api_key_info: dict
    created_at: str
    expires_at: Optional[str] = None


class APIKeyListResponse(BaseModel):
    """API Key 列表响应"""
    keys: List[dict]
    total: int


class CommandPermissionRequest(BaseModel):
    """命令权限检查请求"""
    command: str


class CommandPermissionResponse(BaseModel):
    """命令权限检查响应"""
    allowed: bool
    command_type: str
    reason: Optional[str] = None


# ==================== Token 端点 ====================

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    tenant: Tenant = Depends(require_tenant)
):
    """
    登录并获取 Token
    
    需要先通过租户中间件识别租户
    """
    # 验证租户ID匹配
    if tenant.id != request.tenant_id:
        raise HTTPException(status_code=403, detail="租户ID不匹配")
    
    # TODO: 验证用户密码（如果需要）
    # 这里简化处理，直接生成 token
    
    # 生成访问令牌
    access_token = token_service.create_access_token(
        tenant_id=tenant.id,
        user_id=request.user_id,
        email=request.email,
        scopes=["read", "write"]  # 默认权限
    )
    
    # 生成刷新令牌
    refresh_token = token_service.create_refresh_token(
        tenant_id=tenant.id,
        user_id=request.user_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,  # 1小时
        tenant_id=tenant.id,
        tenant_name=tenant.name
    )


@router.get("/token/verify")
async def verify_token(
    tenant: Tenant = Depends(require_tenant_from_token)
):
    """验证当前 Token"""
    return {
        "valid": True,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "tenant_status": tenant.status.value
    }


# ==================== API Key 端点 ====================

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request_data: CreateAPIKeyRequest,
    http_request: Request,
    tenant: Tenant = Depends(require_tenant_from_token)
):
    """
    创建 API Key
    
    需要 JWT Token 认证
    """
    try:
        api_key_string, api_key_obj = api_key_service.create_api_key(
            tenant_id=tenant.id,
            name=request_data.name,
            scopes=request_data.scopes,
            allowed_commands=request_data.allowed_commands,
            rate_limit=request_data.rate_limit,
            expires_days=request_data.expires_days
        )
        
        # 记录审计日志
        user_id = getattr(http_request.state, "user_id", None)
        audit_logger.log_api_key_action(
            tenant_id=tenant.id,
            action="create",
            api_key_id=api_key_obj.id,
            api_key_name=api_key_obj.name,
            user_id=user_id,
            ip_address=get_client_ip(http_request),
            user_agent=get_user_agent(http_request),
            details={
                "scopes": [scope.value for scope in api_key_obj.scopes],
                "allowed_commands": api_key_obj.allowed_commands,
                "rate_limit": api_key_obj.rate_limit,
                "expires_days": request_data.expires_days
            }
        )
        
        return APIKeyResponse(
            api_key=api_key_string,
            api_key_info={
                "id": api_key_obj.id,
                "name": api_key_obj.name,
                "scopes": [scope.value for scope in api_key_obj.scopes],
                "allowed_commands": api_key_obj.allowed_commands,
                "rate_limit": api_key_obj.rate_limit,
                "is_active": api_key_obj.is_active
            },
            created_at=api_key_obj.created_at.isoformat(),
            expires_at=api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None
        )
    
    except Exception as e:
        logger.error(f"创建 API Key 失败: {e}")
        
        # 记录失败日志
        user_id = getattr(http_request.state, "user_id", None)
        audit_logger.log_api_key_action(
            tenant_id=tenant.id,
            action="create_failed",
            user_id=user_id,
            ip_address=get_client_ip(http_request),
            user_agent=get_user_agent(http_request),
            details={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=f"创建 API Key 失败: {str(e)}")


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    tenant: Tenant = Depends(require_tenant_from_token)
):
    """列出租户的 API Keys"""
    keys = api_key_service.list_tenant_api_keys(tenant.id)
    
    return APIKeyListResponse(
        keys=[
            {
                "id": key.id,
                "name": key.name,
                "scopes": [scope.value for scope in key.scopes],
                "allowed_commands": key.allowed_commands,
                "rate_limit": key.rate_limit,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "is_active": key.is_active,
                "created_at": key.created_at.isoformat()
            }
            for key in keys
        ],
        total=len(keys)
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    http_request: Request,
    tenant: Tenant = Depends(require_tenant_from_token)
):
    """撤销 API Key"""
    keys = api_key_service.list_tenant_api_keys(tenant.id)
    
    # 查找要撤销的 key
    key_to_revoke = None
    for key in keys:
        if key.id == key_id:
            key_to_revoke = key
            break
    
    if not key_to_revoke:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    
    # 撤销 key
    success = api_key_service.revoke_api_key(key_id=key_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="撤销 API Key 失败")
    
    # 记录审计日志
    user_id = getattr(http_request.state, "user_id", None)
    audit_logger.log_api_key_action(
        tenant_id=tenant.id,
        action="revoke",
        api_key_id=key_id,
        api_key_name=key_to_revoke.name,
        user_id=user_id,
        ip_address=get_client_ip(http_request),
        user_agent=get_user_agent(http_request)
    )
    
    logger.info(f"✅ API Key 已撤销: {key_id} (tenant: {tenant.id})")
    
    return {
        "success": True,
        "message": f"API Key {key_id} 已撤销"
    }


@router.get("/api-keys/verify")
async def verify_api_key(
    tenant_key: tuple = Depends(require_tenant_from_api_key)
):
    """验证当前 API Key"""
    tenant, api_key = tenant_key
    
    return {
        "valid": True,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "api_key_id": api_key.id,
        "api_key_name": api_key.name,
        "scopes": [scope.value for scope in api_key.scopes],
        "allowed_commands": api_key.allowed_commands
    }


# ==================== 命令权限端点 ====================

@router.post("/command/check", response_model=CommandPermissionResponse)
async def check_command_permission(
    request: CommandPermissionRequest,
    tenant: Tenant = Depends(require_tenant),
    http_request: Request = None
):
    """检查命令执行权限"""
    from .auth import check_command_permission
    
    try:
        # 标准化命令
        normalized_command = CommandWhitelist.normalize_command(request.command)
        command_type = CommandWhitelist.classify_command(request.command)
        
        # 检查权限（如果使用 API Key）
        if hasattr(http_request.state, "api_key"):
            api_key = http_request.state.api_key
            allowed = api_key.can_execute_command(normalized_command)
            
            return CommandPermissionResponse(
                allowed=allowed,
                command_type=command_type,
                reason=None if allowed else f"API Key 无权限执行 {command_type} 类型命令"
            )
        
        # 如果使用 JWT Token，默认允许（除了危险命令）
        if command_type == "dangerous":
            return CommandPermissionResponse(
                allowed=False,
                command_type=command_type,
                reason="危险命令需要管理员权限"
            )
        
        return CommandPermissionResponse(
            allowed=True,
            command_type=command_type,
            reason=None
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"检查命令权限失败: {e}")
        return CommandPermissionResponse(
            allowed=False,
            command_type="unknown",
            reason=f"检查失败: {str(e)}"
        )


@router.get("/command/whitelist")
async def get_command_whitelist(
    tenant: Tenant = Depends(require_tenant)
):
    """获取命令白名单配置"""
    return {
        "read_commands": list(CommandWhitelist.READ_COMMANDS),
        "write_commands": list(CommandWhitelist.WRITE_COMMANDS),
        "admin_commands": list(CommandWhitelist.ADMIN_COMMANDS),
        "dangerous_commands": list(CommandWhitelist.DANGEROUS_COMMANDS)
    }


# ==================== 租户上下文端点 ====================

@router.get("/context")
async def get_context(
    tenant: Tenant = Depends(require_tenant),
    request: Request = None
):
    """获取当前租户上下文"""
    context = get_tenant_context(request) if request else None
    
    if not context:
        context = {
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "tenant_plan": tenant.plan.value,
            "tenant_status": tenant.status.value,
            "quota": tenant.quota.dict(),
            "config": tenant.config.dict()
        }
    
    return {
        "context": context,
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "plan": tenant.plan.value,
            "status": tenant.status.value
        }
    }


@router.get("/audit-logs")
async def get_audit_logs(
    tenant: Tenant = Depends(require_tenant_from_token),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100
):
    """获取审计日志"""
    logs = audit_logger.get_audit_logs(
        tenant_id=tenant.id,
        action=action,
        resource_type=resource_type,
        limit=limit
    )
    
    return {
        "tenant_id": tenant.id,
        "total": len(logs),
        "logs": logs
    }


# ==================== 导出 ====================

__all__ = ["router"]

