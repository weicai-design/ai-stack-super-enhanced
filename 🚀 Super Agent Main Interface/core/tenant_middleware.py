#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant Middleware

从请求中解析租户信息并注入 TenantContext。
"""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .tenant_context import set_current_tenant, reset_tenant, TenantContext
from .tenant_manager import tenant_manager


class TenantContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "X-Tenant-ID", default_tenant: str = "global"):
        super().__init__(app)
        self.header_name = header_name
        self.default_tenant = default_tenant

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        tenant_id = self._extract_tenant_id(request)
        tenant = tenant_manager.get_tenant(tenant_id) or tenant_manager.get_tenant(self.default_tenant)
        ctx = TenantContext(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            metadata=tenant.metadata,
        )
        token = set_current_tenant(ctx)
        request.state.tenant = ctx
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = ctx.tenant_id
        reset_tenant(token)
        return response

    def _extract_tenant_id(self, request: Request) -> str:
        header_value = request.headers.get(self.header_name)
        if header_value:
            return header_value.strip()
        query_value = request.query_params.get("tenant_id")
        if query_value:
            return query_value.strip()
        return self.default_tenant


__all__ = ["TenantContextMiddleware"]


