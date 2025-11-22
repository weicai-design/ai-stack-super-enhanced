"""
租户管理器
Tenant Manager

提供租户的创建、查询、更新、删除等管理功能

版本: v3.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    Tenant,
    TenantConfig,
    TenantQuota,
    TenantUser,
    TenantInvitation,
    TenantStatus,
    TenantPlan,
    PLAN_FEATURES
)

logger = logging.getLogger(__name__)


# ==================== 租户管理器 ====================

class TenantManager:
    """租户管理器"""
    
    def __init__(self):
        """初始化租户管理器"""
        # 内存存储（生产环境应使用数据库）
        self.tenants: Dict[str, Tenant] = {}
        self.users: Dict[str, TenantUser] = {}
        self.invitations: Dict[str, TenantInvitation] = {}
        
        # 索引
        self.tenant_by_slug: Dict[str, str] = {}  # slug -> tenant_id
        self.users_by_tenant: Dict[str, List[str]] = {}  # tenant_id -> [user_ids]
        self.users_by_email: Dict[str, str] = {}  # email -> user_id
        
        logger.info("✅ 租户管理器已初始化")
    
    # ==================== 租户操作 ====================
    
    def create_tenant(
        self,
        name: str,
        slug: str,
        owner_email: str,
        plan: TenantPlan = TenantPlan.FREE
    ) -> Tenant:
        """
        创建租户
        
        Args:
            name: 租户名称
            slug: 租户标识（唯一）
            owner_email: 所有者邮箱
            plan: 订阅套餐
        
        Returns:
            创建的租户对象
        """
        # 检查slug唯一性
        if slug in self.tenant_by_slug:
            raise ValueError(f"租户标识已存在: {slug}")
        
        # 创建租户
        tenant = Tenant(
            name=name,
            slug=slug,
            owner_email=owner_email,
            plan=plan,
            status=TenantStatus.TRIAL
        )
        
        # 设置试用期（14天）
        tenant.trial_end_at = datetime.now() + timedelta(days=14)
        
        # 根据套餐设置配额
        tenant.quota = tenant.get_plan_limits()
        
        # 存储
        self.tenants[tenant.id] = tenant
        self.tenant_by_slug[slug] = tenant.id
        self.users_by_tenant[tenant.id] = []
        
        logger.info(f"✅ 租户已创建: {tenant.name} ({tenant.id})")
        
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """获取租户"""
        return self.tenants.get(tenant_id)
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """通过slug获取租户"""
        tenant_id = self.tenant_by_slug.get(slug)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
        limit: int = 100
    ) -> List[Tenant]:
        """列出租户"""
        tenants = list(self.tenants.values())
        
        # 过滤
        if status:
            tenants = [t for t in tenants if t.status == status]
        if plan:
            tenants = [t for t in tenants if t.plan == plan]
        
        # 排序（按创建时间倒序）
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        
        return tenants[:limit]
    
    def update_tenant(
        self,
        tenant_id: str,
        **updates
    ) -> Optional[Tenant]:
        """更新租户"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.now()
        
        logger.info(f"✅ 租户已更新: {tenant_id}")
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户（软删除）"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        tenant.status = TenantStatus.DELETED
        tenant.updated_at = datetime.now()
        
        logger.info(f"✅ 租户已删除: {tenant_id}")
        return True
    
    def change_plan(
        self,
        tenant_id: str,
        new_plan: TenantPlan
    ) -> Optional[Tenant]:
        """变更套餐"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        old_plan = tenant.plan
        tenant.plan = new_plan
        
        # 更新配额
        new_quota = tenant.get_plan_limits()
        tenant.quota.max_users = new_quota.max_users
        tenant.quota.max_storage_gb = new_quota.max_storage_gb
        tenant.quota.max_api_calls_monthly = new_quota.max_api_calls_monthly
        tenant.quota.max_documents = new_quota.max_documents
        tenant.quota.max_ai_calls_monthly = new_quota.max_ai_calls_monthly
        tenant.quota.max_kg_nodes = new_quota.max_kg_nodes
        
        tenant.updated_at = datetime.now()
        
        logger.info(f"✅ 套餐已变更: {tenant_id} ({old_plan} → {new_plan})")
        return tenant
    
    # ==================== 用户操作 ====================
    
    def add_user(
        self,
        tenant_id: str,
        email: str,
        name: str,
        role: str = "member"
    ) -> Optional[TenantUser]:
        """添加用户到租户"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # 检查配额
        if tenant.quota.is_user_quota_exceeded():
            raise ValueError("用户配额已满")
        
        # 检查邮箱唯一性
        if email in self.users_by_email:
            raise ValueError(f"邮箱已存在: {email}")
        
        # 创建用户
        user = TenantUser(
            tenant_id=tenant_id,
            email=email,
            name=name,
            role=role
        )
        
        # 存储
        self.users[user.id] = user
        self.users_by_email[email] = user.id
        self.users_by_tenant[tenant_id].append(user.id)
        
        # 更新配额
        tenant.quota.current_users += 1
        
        logger.info(f"✅ 用户已添加: {email} → {tenant_id}")
        return user
    
    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """获取租户的所有用户"""
        user_ids = self.users_by_tenant.get(tenant_id, [])
        return [self.users[uid] for uid in user_ids if uid in self.users]
    
    def remove_user(self, user_id: str) -> bool:
        """移除用户"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        tenant = self.get_tenant(user.tenant_id)
        if tenant:
            tenant.quota.current_users -= 1
        
        # 删除
        del self.users[user_id]
        del self.users_by_email[user.email]
        self.users_by_tenant[user.tenant_id].remove(user_id)
        
        logger.info(f"✅ 用户已移除: {user_id}")
        return True
    
    # ==================== 配额管理 ====================
    
    def check_quota(
        self,
        tenant_id: str,
        quota_type: str,
        amount: int = 1
    ) -> bool:
        """
        检查配额
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型（users/storage/api_calls等）
            amount: 需要的数量
        
        Returns:
            是否在配额内
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        quota = tenant.quota
        
        if quota_type == "users":
            return quota.current_users + amount <= quota.max_users
        elif quota_type == "storage":
            return quota.current_storage_gb + amount <= quota.max_storage_gb
        elif quota_type == "api_calls":
            return quota.current_api_calls_monthly + amount <= quota.max_api_calls_monthly
        elif quota_type == "documents":
            return quota.current_documents + amount <= quota.max_documents
        elif quota_type == "ai_calls":
            return quota.current_ai_calls_monthly + amount <= quota.max_ai_calls_monthly
        elif quota_type == "kg_nodes":
            return quota.current_kg_nodes + amount <= quota.max_kg_nodes
        
        return True
    
    def increment_usage(
        self,
        tenant_id: str,
        quota_type: str,
        amount: int = 1
    ) -> bool:
        """增加使用量"""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        quota = tenant.quota
        
        if quota_type == "api_calls":
            quota.current_api_calls_monthly += amount
        elif quota_type == "storage":
            quota.current_storage_gb += amount
        elif quota_type == "documents":
            quota.current_documents += amount
        elif quota_type == "ai_calls":
            quota.current_ai_calls_monthly += amount
        elif quota_type == "kg_nodes":
            quota.current_kg_nodes += amount
        
        return True
    
    def reset_monthly_quotas(self):
        """重置月度配额（应该由定时任务调用）"""
        for tenant in self.tenants.values():
            tenant.quota.current_api_calls_monthly = 0
            tenant.quota.current_ai_calls_monthly = 0
        
        logger.info("✅ 月度配额已重置")
    
    # ==================== 邀请管理 ====================
    
    def create_invitation(
        self,
        tenant_id: str,
        email: str,
        role: str,
        invited_by: str
    ) -> TenantInvitation:
        """创建邀请"""
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            invited_by=invited_by,
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        self.invitations[invitation.id] = invitation
        
        logger.info(f"✅ 邀请已创建: {email} → {tenant_id}")
        return invitation
    
    def accept_invitation(
        self,
        invitation_id: str,
        user_name: str
    ) -> Optional[TenantUser]:
        """接受邀请"""
        invitation = self.invitations.get(invitation_id)
        if not invitation:
            return None
        
        if invitation.is_expired():
            raise ValueError("邀请已过期")
        
        if invitation.is_accepted():
            raise ValueError("邀请已被接受")
        
        # 创建用户
        user = self.add_user(
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            name=user_name,
            role=invitation.role
        )
        
        # 标记邀请为已接受
        invitation.accepted_at = datetime.now()
        
        logger.info(f"✅ 邀请已接受: {invitation_id}")
        return user
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        tenants_by_status = {}
        tenants_by_plan = {}
        
        for tenant in self.tenants.values():
            # 按状态统计
            status = tenant.status
            tenants_by_status[status] = tenants_by_status.get(status, 0) + 1
            
            # 按套餐统计
            plan = tenant.plan
            tenants_by_plan[plan] = tenants_by_plan.get(plan, 0) + 1
        
        return {
            "total_tenants": len(self.tenants),
            "total_users": len(self.users),
            "tenants_by_status": tenants_by_status,
            "tenants_by_plan": tenants_by_plan,
            "active_invitations": sum(
                1 for inv in self.invitations.values()
                if not inv.is_expired() and not inv.is_accepted()
            )
        }


# ==================== 全局实例 ====================

# 创建全局租户管理器
tenant_manager = TenantManager()


# ==================== 辅助函数 ====================

def get_tenant_manager() -> TenantManager:
    """获取租户管理器实例"""
    return tenant_manager


def create_default_tenant() -> Tenant:
    """创建默认租户（用于开发和测试）"""
    try:
        # 检查是否已存在
        existing = tenant_manager.get_tenant_by_slug("default")
        if existing:
            return existing
        
        # 创建默认租户
        tenant = tenant_manager.create_tenant(
            name="Default Tenant",
            slug="default",
            owner_email="admin@aistack.local",
            plan=TenantPlan.ENTERPRISE  # 开发环境使用企业版
        )
        
        # 创建默认用户
        tenant_manager.add_user(
            tenant_id=tenant.id,
            email="admin@aistack.local",
            name="Admin User",
            role="owner"
        )
        
        logger.info("✅ 默认租户已创建")
        return tenant
    
    except Exception as e:
        logger.error(f"创建默认租户失败: {e}")
        raise


# ==================== 导出 ====================

__all__ = [
    "TenantManager",
    "tenant_manager",
    "get_tenant_manager",
    "create_default_tenant"
]

































