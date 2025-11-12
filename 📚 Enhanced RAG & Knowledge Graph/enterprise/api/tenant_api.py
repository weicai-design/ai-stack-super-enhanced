"""
租户管理API
Tenant Management API

提供租户CRUD、用户管理、配额查询等功能

版本: v3.0.0
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

# 添加父目录到路径
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from enterprise.tenancy.models import (
    Tenant,
    TenantUser,
    TenantStatus,
    TenantPlan,
    PLAN_FEATURES
)
from enterprise.tenancy.manager import tenant_manager, create_default_tenant
from enterprise.tenancy.middleware import get_current_tenant, require_tenant

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/tenants", tags=["Tenant Management"])


# ==================== 请求模型 ====================

class CreateTenantRequest(BaseModel):
    """创建租户请求"""
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    slug: str = Field(..., min_length=1, max_length=50, description="租户标识")
    owner_email: str = Field(..., description="所有者邮箱")
    plan: TenantPlan = Field(TenantPlan.FREE, description="订阅套餐")


class UpdateTenantRequest(BaseModel):
    """更新租户请求"""
    name: Optional[str] = Field(None, description="租户名称")
    status: Optional[TenantStatus] = Field(None, description="状态")


class AddUserRequest(BaseModel):
    """添加用户请求"""
    email: str = Field(..., description="用户邮箱")
    name: str = Field(..., description="用户姓名")
    role: str = Field("member", description="角色")


# ==================== API端点 ====================

@router.post("/", response_model=Tenant)
async def create_tenant(request: CreateTenantRequest):
    """
    创建租户
    
    Args:
        request: 创建请求
    
    Returns:
        创建的租户
    """
    try:
        tenant = tenant_manager.create_tenant(
            name=request.name,
            slug=request.slug,
            owner_email=request.owner_email,
            plan=request.plan
        )
        
        logger.info(f"租户已创建: {tenant.id}")
        return tenant
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建租户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Tenant])
async def list_tenants(
    status: Optional[TenantStatus] = None,
    plan: Optional[TenantPlan] = None,
    limit: int = 100
):
    """
    列出租户
    
    Args:
        status: 按状态过滤
        plan: 按套餐过滤
        limit: 最大返回数
    
    Returns:
        租户列表
    """
    try:
        tenants = tenant_manager.list_tenants(status, plan, limit)
        return tenants
    
    except Exception as e:
        logger.error(f"列出租户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=Tenant)
async def get_current_tenant_info(
    tenant: Tenant = Depends(require_tenant)
):
    """
    获取当前租户信息
    
    Returns:
        当前租户
    """
    return tenant


@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str):
    """
    获取租户详情
    
    Args:
        tenant_id: 租户ID
    
    Returns:
        租户信息
    """
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    return tenant


@router.patch("/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest
):
    """
    更新租户
    
    Args:
        tenant_id: 租户ID
        request: 更新请求
    
    Returns:
        更新后的租户
    """
    try:
        updates = request.model_dump(exclude_unset=True)
        tenant = tenant_manager.update_tenant(tenant_id, **updates)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="租户不存在")
        
        return tenant
    
    except Exception as e:
        logger.error(f"更新租户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """
    删除租户
    
    Args:
        tenant_id: 租户ID
    
    Returns:
        操作结果
    """
    success = tenant_manager.delete_tenant(tenant_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    return {"message": "租户已删除", "tenant_id": tenant_id}


# ==================== 用户管理 ====================

@router.post("/{tenant_id}/users", response_model=TenantUser)
async def add_user_to_tenant(
    tenant_id: str,
    request: AddUserRequest
):
    """
    添加用户到租户
    
    Args:
        tenant_id: 租户ID
        request: 添加用户请求
    
    Returns:
        创建的用户
    """
    try:
        user = tenant_manager.add_user(
            tenant_id=tenant_id,
            email=request.email,
            name=request.name,
            role=request.role
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="租户不存在")
        
        return user
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加用户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/users", response_model=List[TenantUser])
async def list_tenant_users(tenant_id: str):
    """
    列出租户的所有用户
    
    Args:
        tenant_id: 租户ID
    
    Returns:
        用户列表
    """
    users = tenant_manager.get_tenant_users(tenant_id)
    return users


# ==================== 配额管理 ====================

@router.get("/{tenant_id}/quota")
async def get_tenant_quota(tenant_id: str):
    """
    获取租户配额信息
    
    Args:
        tenant_id: 租户ID
    
    Returns:
        配额信息
    """
    tenant = tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    
    return {
        "tenant_id": tenant_id,
        "plan": tenant.plan,
        "quota": tenant.quota,
        "remaining": tenant.quota.get_remaining_quota(),
        "is_exceeded": tenant.is_quota_exceeded()
    }


# ==================== 套餐管理 ====================

@router.post("/{tenant_id}/change-plan")
async def change_tenant_plan(
    tenant_id: str,
    new_plan: TenantPlan
):
    """
    变更租户套餐
    
    Args:
        tenant_id: 租户ID
        new_plan: 新套餐
    
    Returns:
        操作结果
    """
    try:
        tenant = tenant_manager.change_plan(tenant_id, new_plan)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="租户不存在")
        
        return {
            "message": "套餐已变更",
            "tenant_id": tenant_id,
            "old_plan": tenant.plan,
            "new_plan": new_plan,
            "new_quota": tenant.quota
        }
    
    except Exception as e:
        logger.error(f"变更套餐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def list_plans():
    """
    列出所有套餐
    
    Returns:
        套餐列表
    """
    return PLAN_FEATURES


# ==================== 统计信息 ====================

@router.get("/stats")
async def get_tenant_statistics():
    """
    获取租户统计信息
    
    Returns:
        统计数据
    """
    stats = tenant_manager.get_statistics()
    return stats


# ==================== 健康检查 ====================

@router.get("/health")
async def tenant_health():
    """租户模块健康检查"""
    stats = tenant_manager.get_statistics()
    
    return {
        "status": "healthy",
        "module": "tenancy",
        "version": "3.0.0-alpha",
        "total_tenants": stats["total_tenants"],
        "total_users": stats["total_users"],
        "features": [
            "multi-tenancy",
            "data-isolation",
            "quota-management",
            "plan-management",
            "user-management"
        ]
    }












