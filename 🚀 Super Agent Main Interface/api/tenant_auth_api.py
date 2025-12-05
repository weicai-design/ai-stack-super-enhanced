#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多租户认证API（生产级实现）
5.1: 提供Token、API Key、命令白名单的管理接口
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status, Body
from pydantic import BaseModel

from core.security.tenant_auth import (
    get_tenant_auth_manager,
    get_tenant_auth,
    AuthType,
    TokenPayload,
    APIKeyInfo,
)
from core.tenant_context import get_current_tenant

router = APIRouter(prefix="/api/tenant/auth", tags=["Tenant Authentication"])


# ============ 请求/响应模型 ============

class CreateTokenRequest(BaseModel):
    """创建Token请求"""
    tenant_id: str
    user_id: str
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    expiration_hours: Optional[int] = None


class CreateTokenResponse(BaseModel):
    """创建Token响应"""
    success: bool
    token: str
    expires_at: str
    tenant_id: str
    user_id: str


class CreateAPIKeyRequest(BaseModel):
    """创建API Key请求"""
    tenant_id: str
    name: str
    permissions: Optional[List[str]] = None
    commands_whitelist: Optional[List[str]] = None


class CreateAPIKeyResponse(BaseModel):
    """创建API Key响应"""
    success: bool
    key_id: str
    api_key: str
    tenant_id: str
    name: str
    message: str = "请妥善保管API Key，它只会显示一次"


class UpdateCommandWhitelistRequest(BaseModel):
    """更新命令白名单请求"""
    tenant_id: str
    commands: List[str]


class CommandWhitelistResponse(BaseModel):
    """命令白名单响应"""
    success: bool
    tenant_id: str
    commands: List[str]
    updated_at: str


# ============ Token管理 ============

@router.post("/token/create", response_model=CreateTokenResponse)
async def create_token(
    request: CreateTokenRequest,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    创建JWT Token
    
    需要管理员权限或对应租户的权限
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 权限检查：只能为自己的租户创建Token，或管理员可以为任何租户创建
    if request.tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能为自己的租户创建Token",
        )
    
    try:
        token = auth_manager.create_token(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            roles=request.roles,
            permissions=request.permissions,
            expiration_hours=request.expiration_hours,
        )
        
        # 计算过期时间
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(hours=request.expiration_hours or 24)
        
        return CreateTokenResponse(
            success=True,
            token=token,
            expires_at=expires_at.isoformat(),
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/token/verify")
async def verify_token(
    token: str = Body(..., embed=True),
):
    """
    验证JWT Token
    
    返回Token的详细信息
    """
    auth_manager = get_tenant_auth_manager()
    
    try:
        token_payload = auth_manager.verify_token(token)
        
        return {
            "success": True,
            "tenant_id": token_payload.tenant_id,
            "user_id": token_payload.user_id,
            "roles": token_payload.roles,
            "permissions": token_payload.permissions,
            "expires_at": token_payload.exp.isoformat() if token_payload.exp else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token验证失败: {str(e)}",
        )


# ============ API Key管理 ============

@router.post("/api-key/create", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    创建API Key
    
    需要管理员权限或对应租户的权限
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 权限检查：只能为自己的租户创建API Key，或管理员可以为任何租户创建
    if request.tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能为自己的租户创建API Key",
        )
    
    try:
        key_id, api_key = auth_manager.create_api_key(
            tenant_id=request.tenant_id,
            name=request.name,
            permissions=request.permissions,
            commands_whitelist=request.commands_whitelist,
        )
        
        return CreateAPIKeyResponse(
            success=True,
            key_id=key_id,
            api_key=api_key,
            tenant_id=request.tenant_id,
            name=request.name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/api-key/list")
async def list_api_keys(
    tenant_id: Optional[str] = None,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    列出API Key
    
    只能查看自己租户的API Key，或管理员可以查看所有
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 权限检查
    if tenant_id and tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己租户的API Key",
        )
    
    # 过滤API Key
    target_tenant_id = tenant_id or current_tenant.tenant_id
    api_keys = [
        {
            "key_id": key_id,
            "tenant_id": info.tenant_id,
            "name": info.name,
            "permissions": info.permissions,
            "commands_whitelist": info.commands_whitelist,
            "active": info.active,
            "created_at": info.created_at,
            "last_used_at": info.last_used_at,
            "usage_count": info.usage_count,
        }
        for key_id, info in auth_manager.api_keys.items()
        if info.tenant_id == target_tenant_id or current_tenant.tenant_id == "global"
    ]
    
    return {
        "success": True,
        "api_keys": api_keys,
        "count": len(api_keys),
    }


@router.post("/api-key/revoke")
async def revoke_api_key(
    key_id: str = Body(..., embed=True),
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    撤销API Key
    
    只能撤销自己租户的API Key，或管理员可以撤销任何
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 检查API Key是否存在
    api_key_info = auth_manager.api_keys.get(key_id)
    if not api_key_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key不存在",
        )
    
    # 权限检查
    if api_key_info.tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能撤销自己租户的API Key",
        )
    
    success = auth_manager.revoke_api_key(key_id)
    
    return {
        "success": success,
        "message": "API Key已撤销" if success else "撤销失败",
    }


# ============ 命令白名单管理 ============

@router.get("/command-whitelist", response_model=CommandWhitelistResponse)
async def get_command_whitelist(
    tenant_id: Optional[str] = None,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    获取命令白名单
    
    只能查看自己租户的命令白名单，或管理员可以查看所有
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 确定目标租户
    target_tenant_id = tenant_id or current_tenant.tenant_id
    
    # 权限检查
    if target_tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能查看自己租户的命令白名单",
        )
    
    commands = auth_manager.get_command_whitelist(target_tenant_id)
    whitelist = auth_manager.command_whitelists.get(target_tenant_id)
    
    return CommandWhitelistResponse(
        success=True,
        tenant_id=target_tenant_id,
        commands=commands,
        updated_at=whitelist.updated_at if whitelist else datetime.now().isoformat(),
    )


@router.post("/command-whitelist/update", response_model=CommandWhitelistResponse)
async def update_command_whitelist(
    request: UpdateCommandWhitelistRequest,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    更新命令白名单
    
    只能更新自己租户的命令白名单，或管理员可以更新任何
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 权限检查
    if request.tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能更新自己租户的命令白名单",
        )
    
    success = auth_manager.update_command_whitelist(
        tenant_id=request.tenant_id,
        commands=request.commands,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新命令白名单失败",
        )
    
    whitelist = auth_manager.command_whitelists.get(request.tenant_id)
    
    return CommandWhitelistResponse(
        success=True,
        tenant_id=request.tenant_id,
        commands=request.commands,
        updated_at=whitelist.updated_at if whitelist else datetime.now().isoformat(),
    )


@router.post("/command-whitelist/check")
async def check_command_allowed(
    command: str = Body(..., embed=True),
    tenant_id: Optional[str] = None,
    auth: Tuple[AuthType, Optional[TokenPayload], Optional[APIKeyInfo], Any] = Depends(get_tenant_auth),
):
    """
    检查命令是否在白名单中
    
    只能检查自己租户的命令，或管理员可以检查任何
    """
    auth_manager = get_tenant_auth_manager()
    current_tenant = get_current_tenant()
    
    # 确定目标租户
    target_tenant_id = tenant_id or current_tenant.tenant_id
    
    # 权限检查
    if target_tenant_id != current_tenant.tenant_id and current_tenant.tenant_id != "global":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能检查自己租户的命令",
        )
    
    allowed = auth_manager.check_command_allowed(target_tenant_id, command)
    
    return {
        "success": True,
        "command": command,
        "tenant_id": target_tenant_id,
        "allowed": allowed,
    }


__all__ = ["router"]

