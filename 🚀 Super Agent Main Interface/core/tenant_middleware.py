#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant Middleware（生产级实现）

从请求中解析租户信息并注入 TenantContext。
支持Token和API Key认证，自动绑定Tenant Context。
"""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .tenant_context import set_current_tenant, reset_tenant, TenantContext
from .tenant_manager import tenant_manager
from .security.tenant_auth import get_tenant_auth_manager, AuthType


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    租户上下文中间件（生产级实现）
    
    功能：
    1. 从Token/API Key中提取租户信息
    2. 自动绑定Tenant Context
    3. 向后兼容（支持X-Tenant-ID头）
    """
    
    def __init__(self, app, header_name: str = "X-Tenant-ID", default_tenant: str = "global"):
        super().__init__(app)
        self.header_name = header_name
        self.default_tenant = default_tenant
        self.auth_manager = get_tenant_auth_manager()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # 尝试从认证信息中提取租户
        tenant_context = None
        
        try:
            # 从Token/API Key中提取租户信息
            auth_type, token_payload, api_key_info = await self.auth_manager.authenticate_request(
                request=request,
                authorization=request.headers.get("Authorization"),
                x_api_key=request.headers.get("X-API-Key"),
            )
            
            if auth_type != AuthType.NONE:
                # 绑定Tenant Context
                tenant_context = self.auth_manager.bind_tenant_context(
                    request=request,
                    auth_type=auth_type,
                    token_payload=token_payload,
                    api_key_info=api_key_info,
                )
        except Exception:
            # 认证失败，使用向后兼容方式
            pass
        
        # 如果没有从认证信息中获取到租户，使用向后兼容方式
        if not tenant_context:
            tenant_id = self._extract_tenant_id(request)
            tenant = tenant_manager.get_tenant(tenant_id) or tenant_manager.get_tenant(self.default_tenant)
            tenant_context = TenantContext(
                tenant_id=tenant.tenant_id,
                name=tenant.name,
                metadata=tenant.metadata,
            )
            set_current_tenant(tenant_context)
            request.state.tenant = tenant_context
        
        # 设置到请求状态
        request.state.tenant_context = tenant_context
        
        # 执行请求
        response = await call_next(request)
        
        # 在响应头中添加租户ID
        response.headers["X-Tenant-ID"] = tenant_context.tenant_id
        
        return response

    def _extract_tenant_id(self, request: Request) -> str:
        """从请求中提取租户ID（向后兼容）"""
        header_value = request.headers.get(self.header_name)
        if header_value:
            return header_value.strip()
        query_value = request.query_params.get("tenant_id")
        if query_value:
            return query_value.strip()
        return self.default_tenant


__all__ = ["TenantContextMiddleware"]


