"""
租户中间件
Tenant Middleware

自动识别租户并实现数据隔离

版本: v3.0.0
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .manager import tenant_manager
from .models import Tenant, TenantStatus

logger = logging.getLogger(__name__)


# ==================== 租户识别 ====================

class TenantIdentifier:
    """租户识别器"""
    
    @staticmethod
    def from_header(request: Request) -> Optional[str]:
        """从请求头获取租户ID"""
        return request.headers.get("X-Tenant-ID")
    
    @staticmethod
    def from_subdomain(request: Request) -> Optional[str]:
        """从子域名获取租户slug"""
        host = request.headers.get("host", "")
        
        # 例如: tenant1.aistack.com → tenant1
        parts = host.split(".")
        if len(parts) >= 3:
            return parts[0]
        
        return None
    
    @staticmethod
    def from_query(request: Request) -> Optional[str]:
        """从查询参数获取租户ID"""
        return request.query_params.get("tenant_id")
    
    @staticmethod
    def from_token(request: Request) -> Optional[str]:
        """从JWT token获取租户ID"""
        # TODO: 解析JWT token提取租户ID
        return None
    
    @classmethod
    def identify_tenant(cls, request: Request) -> Optional[Tenant]:
        """
        识别租户
        
        优先级：
        1. 请求头 X-Tenant-ID
        2. JWT token
        3. 子域名
        4. 查询参数
        5. 默认租户
        
        Args:
            request: FastAPI请求对象
        
        Returns:
            识别的租户对象
        """
        # 1. 从请求头
        tenant_id = cls.from_header(request)
        if tenant_id:
            tenant = tenant_manager.get_tenant(tenant_id)
            if tenant:
                return tenant
        
        # 2. 从token
        tenant_id = cls.from_token(request)
        if tenant_id:
            tenant = tenant_manager.get_tenant(tenant_id)
            if tenant:
                return tenant
        
        # 3. 从子域名
        slug = cls.from_subdomain(request)
        if slug:
            tenant = tenant_manager.get_tenant_by_slug(slug)
            if tenant:
                return tenant
        
        # 4. 从查询参数
        tenant_id = cls.from_query(request)
        if tenant_id:
            tenant = tenant_manager.get_tenant(tenant_id)
            if tenant:
                return tenant
        
        # 5. 默认租户（开发环境）
        default_tenant = tenant_manager.get_tenant_by_slug("default")
        if default_tenant:
            return default_tenant
        
        return None


# ==================== 租户中间件 ====================

class TenantMiddleware(BaseHTTPMiddleware):
    """租户中间件"""
    
    def __init__(self, app, require_tenant: bool = False):
        """
        初始化中间件
        
        Args:
            app: FastAPI应用
            require_tenant: 是否强制要求租户（默认False）
        """
        super().__init__(app)
        self.require_tenant = require_tenant
        self.identifier = TenantIdentifier()
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        
        # 跳过某些路径（健康检查、文档等）
        skip_paths = [
            "/health",
            "/readyz",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/guide"
        ]
        
        if request.url.path in skip_paths or request.url.path.startswith("/docs"):
            return await call_next(request)
        
        # 识别租户
        tenant = self.identifier.identify_tenant(request)
        
        if tenant:
            # 检查租户状态
            if tenant.status == TenantStatus.SUSPENDED:
                raise HTTPException(
                    status_code=403,
                    detail="租户已暂停，请联系管理员"
                )
            
            if tenant.status == TenantStatus.EXPIRED:
                raise HTTPException(
                    status_code=402,
                    detail="租户订阅已过期，请续费"
                )
            
            if tenant.status == TenantStatus.DELETED:
                raise HTTPException(
                    status_code=410,
                    detail="租户已删除"
                )
            
            # 将租户信息添加到请求状态
            request.state.tenant = tenant
            request.state.tenant_id = tenant.id
            
            # 记录日志
            logger.debug(f"请求来自租户: {tenant.name} ({tenant.id})")
        
        elif self.require_tenant:
            # 如果强制要求租户但未找到
            raise HTTPException(
                status_code=401,
                detail="未识别租户，请提供租户信息"
            )
        else:
            # 未识别租户，但不强制
            request.state.tenant = None
            request.state.tenant_id = None
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加租户信息到响应头（用于调试）
        if tenant:
            response.headers["X-Tenant-ID"] = tenant.id
            response.headers["X-Tenant-Name"] = tenant.name
        
        return response


# ==================== 租户依赖注入 ====================

async def get_current_tenant(request: Request) -> Optional[Tenant]:
    """
    获取当前租户（FastAPI依赖注入）
    
    Usage:
        @app.get("/my-endpoint")
        async def my_endpoint(tenant: Tenant = Depends(get_current_tenant)):
            # 使用tenant
            ...
    """
    return getattr(request.state, "tenant", None)


async def require_tenant(request: Request) -> Tenant:
    """
    要求租户（必须有租户才能访问）
    
    Usage:
        @app.get("/protected-endpoint")
        async def protected(tenant: Tenant = Depends(require_tenant)):
            # tenant 保证不为None
            ...
    """
    tenant = getattr(request.state, "tenant", None)
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="需要租户认证"
        )
    return tenant


# ==================== 导出 ====================

__all__ = [
    "TenantIdentifier",
    "TenantMiddleware",
    "get_current_tenant",
    "require_tenant"
]



























