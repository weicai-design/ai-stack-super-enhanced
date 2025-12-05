"""
多租户系统
Multi-tenant System

版本: v3.1.0
"""

from .models import (
    Tenant,
    TenantConfig,
    TenantQuota,
    TenantUser,
    TenantInvitation,
    TenantStatus,
    TenantPlan,
    IsolationStrategy,
    PLAN_FEATURES
)

from .manager import (
    TenantManager,
    tenant_manager,
    get_tenant_manager,
    create_default_tenant
)

from .middleware import (
    TenantIdentifier,
    TenantMiddleware,
    get_current_tenant,
    require_tenant
)

from .auth import (
    TokenService,
    token_service,
    APIKeyService,
    api_key_service,
    TokenPayload,
    APIKey,
    APIKeyScope,
    CommandWhitelist,
    get_current_tenant_from_token,
    require_tenant_from_token,
    get_current_tenant_from_api_key,
    require_tenant_from_api_key,
    check_command_permission,
    bind_tenant_context,
    get_tenant_context
)

__all__ = [
    # Models
    "Tenant",
    "TenantConfig",
    "TenantQuota",
    "TenantUser",
    "TenantInvitation",
    "TenantStatus",
    "TenantPlan",
    "IsolationStrategy",
    "PLAN_FEATURES",
    # Manager
    "TenantManager",
    "tenant_manager",
    "get_tenant_manager",
    "create_default_tenant",
    # Middleware
    "TenantIdentifier",
    "TenantMiddleware",
    "get_current_tenant",
    "require_tenant",
    # Auth
    "TokenService",
    "token_service",
    "APIKeyService",
    "api_key_service",
    "TokenPayload",
    "APIKey",
    "APIKeyScope",
    "CommandWhitelist",
    "get_current_tenant_from_token",
    "require_tenant_from_token",
    "get_current_tenant_from_api_key",
    "require_tenant_from_api_key",
    "check_command_permission",
    "bind_tenant_context",
    "get_tenant_context"
]
