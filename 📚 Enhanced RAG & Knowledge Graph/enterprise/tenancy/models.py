"""
租户数据模型
Tenant Data Models

定义租户、配置、配额等数据结构

版本: v3.0.0
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ==================== 枚举类型 ====================

class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"           # 活跃
    SUSPENDED = "suspended"     # 暂停
    TRIAL = "trial"            # 试用
    EXPIRED = "expired"        # 过期
    DELETED = "deleted"        # 已删除


class TenantPlan(str, Enum):
    """租户套餐"""
    FREE = "free"              # 免费版
    BASIC = "basic"            # 基础版 $99/月
    PROFESSIONAL = "pro"       # 专业版 $299/月
    ENTERPRISE = "enterprise"  # 企业版 定制


class IsolationStrategy(str, Enum):
    """数据隔离策略"""
    SCHEMA = "schema"          # Schema级别隔离（推荐）
    DATABASE = "database"      # 数据库级别隔离
    ROW_LEVEL = "row_level"   # 行级安全隔离


# ==================== 配额模型 ====================

class TenantQuota(BaseModel):
    """租户配额"""
    
    # 用户配额
    max_users: int = Field(5, description="最大用户数")
    current_users: int = Field(0, description="当前用户数")
    
    # 存储配额（GB）
    max_storage_gb: float = Field(1.0, description="最大存储（GB）")
    current_storage_gb: float = Field(0.0, description="当前存储（GB）")
    
    # API配额
    max_api_calls_monthly: int = Field(1000, description="每月最大API调用")
    current_api_calls_monthly: int = Field(0, description="当月API调用")
    
    # 文档配额
    max_documents: int = Field(100, description="最大文档数")
    current_documents: int = Field(0, description="当前文档数")
    
    # AI配额
    max_ai_calls_monthly: int = Field(100, description="每月最大AI调用")
    current_ai_calls_monthly: int = Field(0, description="当月AI调用")
    
    # 图谱配额
    max_kg_nodes: int = Field(1000, description="最大知识图谱节点")
    current_kg_nodes: int = Field(0, description="当前图谱节点")
    
    def is_user_quota_exceeded(self) -> bool:
        """检查用户配额是否超限"""
        return self.current_users >= self.max_users
    
    def is_storage_quota_exceeded(self) -> bool:
        """检查存储配额是否超限"""
        return self.current_storage_gb >= self.max_storage_gb
    
    def is_api_quota_exceeded(self) -> bool:
        """检查API配额是否超限"""
        return self.current_api_calls_monthly >= self.max_api_calls_monthly
    
    def get_remaining_quota(self) -> Dict[str, Any]:
        """获取剩余配额"""
        return {
            "users": self.max_users - self.current_users,
            "storage_gb": self.max_storage_gb - self.current_storage_gb,
            "api_calls": self.max_api_calls_monthly - self.current_api_calls_monthly,
            "documents": self.max_documents - self.current_documents,
            "ai_calls": self.max_ai_calls_monthly - self.current_ai_calls_monthly,
            "kg_nodes": self.max_kg_nodes - self.current_kg_nodes
        }


# ==================== 租户配置 ====================

class TenantConfig(BaseModel):
    """租户配置"""
    
    # 基础配置
    custom_domain: Optional[str] = Field(None, description="自定义域名")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    primary_color: str = Field("#667eea", description="主题色")
    
    # 功能开关
    enable_smart_qa: bool = Field(True, description="启用智能问答")
    enable_kg_viz: bool = Field(True, description="启用图谱可视化")
    enable_api_access: bool = Field(True, description="启用API访问")
    
    # 安全配置
    require_mfa: bool = Field(False, description="要求多因素认证")
    allowed_ip_ranges: List[str] = Field(default_factory=list, description="允许的IP范围")
    session_timeout_minutes: int = Field(60, description="会话超时（分钟）")
    
    # 数据保留
    data_retention_days: int = Field(365, description="数据保留天数")
    auto_backup: bool = Field(True, description="自动备份")
    
    # 自定义设置
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="自定义设置")


# ==================== 租户模型 ====================

class Tenant(BaseModel):
    """租户模型"""
    
    # 基础信息
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="租户ID")
    name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    slug: str = Field(..., min_length=1, max_length=50, description="租户标识")
    
    # 状态和套餐
    status: TenantStatus = Field(TenantStatus.TRIAL, description="租户状态")
    plan: TenantPlan = Field(TenantPlan.FREE, description="订阅套餐")
    
    # 隔离策略
    isolation_strategy: IsolationStrategy = Field(
        IsolationStrategy.SCHEMA, 
        description="数据隔离策略"
    )
    
    # 关联信息
    owner_email: str = Field(..., description="所有者邮箱")
    owner_user_id: Optional[str] = Field(None, description="所有者用户ID")
    
    # 配置和配额
    config: TenantConfig = Field(default_factory=TenantConfig, description="租户配置")
    quota: TenantQuota = Field(default_factory=TenantQuota, description="租户配额")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    trial_end_at: Optional[datetime] = Field(None, description="试用结束时间")
    subscription_end_at: Optional[datetime] = Field(None, description="订阅结束时间")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        use_enum_values = True
    
    def is_active(self) -> bool:
        """检查租户是否活跃"""
        return self.status == TenantStatus.ACTIVE
    
    def is_trial(self) -> bool:
        """检查是否试用期"""
        if self.status == TenantStatus.TRIAL and self.trial_end_at:
            return datetime.now() < self.trial_end_at
        return False
    
    def is_quota_exceeded(self) -> bool:
        """检查配额是否超限"""
        return (
            self.quota.is_user_quota_exceeded() or
            self.quota.is_storage_quota_exceeded() or
            self.quota.is_api_quota_exceeded()
        )
    
    def get_plan_limits(self) -> TenantQuota:
        """根据套餐获取配额限制"""
        plan_quotas = {
            TenantPlan.FREE: TenantQuota(
                max_users=5,
                max_storage_gb=1.0,
                max_api_calls_monthly=1000,
                max_documents=100,
                max_ai_calls_monthly=100,
                max_kg_nodes=1000
            ),
            TenantPlan.BASIC: TenantQuota(
                max_users=20,
                max_storage_gb=10.0,
                max_api_calls_monthly=10000,
                max_documents=1000,
                max_ai_calls_monthly=1000,
                max_kg_nodes=10000
            ),
            TenantPlan.PROFESSIONAL: TenantQuota(
                max_users=50,
                max_storage_gb=50.0,
                max_api_calls_monthly=50000,
                max_documents=5000,
                max_ai_calls_monthly=5000,
                max_kg_nodes=50000
            ),
            TenantPlan.ENTERPRISE: TenantQuota(
                max_users=9999999,
                max_storage_gb=999999.0,
                max_api_calls_monthly=9999999,
                max_documents=9999999,
                max_ai_calls_monthly=9999999,
                max_kg_nodes=9999999
            )
        }
        return plan_quotas.get(self.plan, plan_quotas[TenantPlan.FREE])


# ==================== 租户用户模型 ====================

class TenantUser(BaseModel):
    """租户用户"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="用户ID")
    tenant_id: str = Field(..., description="所属租户ID")
    email: str = Field(..., description="邮箱")
    name: str = Field(..., description="姓名")
    role: str = Field("member", description="角色：owner/admin/member/viewer")
    
    # 状态
    is_active: bool = Field(True, description="是否活跃")
    is_verified: bool = Field(False, description="是否验证邮箱")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    def is_owner(self) -> bool:
        """是否所有者"""
        return self.role == "owner"
    
    def is_admin(self) -> bool:
        """是否管理员"""
        return self.role in ["owner", "admin"]


# ==================== 租户邀请模型 ====================

class TenantInvitation(BaseModel):
    """租户邀请"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="邀请ID")
    tenant_id: str = Field(..., description="租户ID")
    email: str = Field(..., description="被邀请人邮箱")
    role: str = Field("member", description="角色")
    
    invited_by: str = Field(..., description="邀请人ID")
    token: str = Field(default_factory=lambda: str(uuid.uuid4()), description="邀请令牌")
    
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    expires_at: datetime = Field(..., description="过期时间")
    accepted_at: Optional[datetime] = Field(None, description="接受时间")
    
    def is_expired(self) -> bool:
        """是否已过期"""
        return datetime.now() > self.expires_at
    
    def is_accepted(self) -> bool:
        """是否已接受"""
        return self.accepted_at is not None


# ==================== 套餐定义 ====================

PLAN_FEATURES = {
    TenantPlan.FREE: {
        "name": "免费版",
        "price_monthly": 0,
        "features": [
            "基础RAG检索",
            "知识图谱查询",
            "5个用户",
            "1GB存储",
            "1000次API调用/月"
        ],
        "limits": {
            "users": 5,
            "storage_gb": 1,
            "api_calls": 1000
        }
    },
    TenantPlan.BASIC: {
        "name": "基础版",
        "price_monthly": 99,
        "features": [
            "所有免费版功能",
            "智能问答系统",
            "图谱可视化",
            "20个用户",
            "10GB存储",
            "10000次API调用/月",
            "邮件支持"
        ],
        "limits": {
            "users": 20,
            "storage_gb": 10,
            "api_calls": 10000
        }
    },
    TenantPlan.PROFESSIONAL: {
        "name": "专业版",
        "price_monthly": 299,
        "features": [
            "所有基础版功能",
            "企业SSO",
            "高级权限管理",
            "50个用户",
            "50GB存储",
            "50000次API调用/月",
            "优先支持",
            "自定义域名"
        ],
        "limits": {
            "users": 50,
            "storage_gb": 50,
            "api_calls": 50000
        }
    },
    TenantPlan.ENTERPRISE: {
        "name": "企业版",
        "price_monthly": -1,  # 定制
        "features": [
            "所有专业版功能",
            "无限用户",
            "无限存储",
            "无限API调用",
            "专属支持",
            "SLA保障",
            "数据隔离",
            "审计日志",
            "定制开发"
        ],
        "limits": {
            "users": 9999999,
            "storage_gb": 999999,
            "api_calls": 9999999
        }
    }
}


# ==================== 导出 ====================

__all__ = [
    "Tenant",
    "TenantConfig",
    "TenantQuota",
    "TenantUser",
    "TenantInvitation",
    "TenantStatus",
    "TenantPlan",
    "IsolationStrategy",
    "PLAN_FEATURES"
]



























