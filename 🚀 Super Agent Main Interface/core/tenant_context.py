#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant Context

为多租户架构提供 ContextVar 级别的租户隔离能力。
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional


@dataclass
class TenantContext:
    tenant_id: str
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


_tenant_ctx: ContextVar[Optional[TenantContext]] = ContextVar("tenant_context", default=None)
DEFAULT_TENANT_ID = "global"


def set_current_tenant(ctx: TenantContext) -> Token:
    return _tenant_ctx.set(ctx)


def reset_tenant(token: Token) -> None:
    _tenant_ctx.reset(token)


def get_current_tenant(default_id: str = DEFAULT_TENANT_ID) -> TenantContext:
    ctx = _tenant_ctx.get()
    if ctx is None:
        return TenantContext(tenant_id=default_id, name=default_id.title())
    return ctx


def get_current_tenant_id(default_id: str = DEFAULT_TENANT_ID) -> str:
    ctx = _tenant_ctx.get()
    return ctx.tenant_id if ctx else default_id


@contextmanager
def tenant_scope(tenant_id: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Iterator[None]:
    token = set_current_tenant(TenantContext(tenant_id=tenant_id, name=name, metadata=metadata or {}))
    try:
        yield
    finally:
        reset_tenant(token)


__all__ = [
    "TenantContext",
    "set_current_tenant",
    "reset_tenant",
    "get_current_tenant",
    "get_current_tenant_id",
    "tenant_scope",
    "DEFAULT_TENANT_ID",
]



