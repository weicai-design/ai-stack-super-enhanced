#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限隔离与访问控制
P0-004: RBAC 权限守卫
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Set

from fastapi import Depends, Header, HTTPException, Request, status


class PermissionGuard:
    """简单的基于角色的权限守卫"""

    def __init__(self):
        self.role_permissions: Dict[str, Set[str]] = {
            "admin": {
                "security:read", "security:write",
                "finance:read", "finance:write",
                "operations:read", "operations:write",
                "trend:read", "trend:write",
            },
            "security": {"security:read", "security:write"},
            "auditor": {"security:read"},
            "finance_lead": {"finance:read", "finance:write"},
            "ops_lead": {"operations:read", "operations:write"},
            "trend_owner": {"trend:read", "trend:write"},
            "viewer": {"security:read", "finance:read", "operations:read", "trend:read"},
        }
        self.default_roles = {"viewer"}

    # ------- 接口 -------

    def require(self, permission: str):
        async def dependency(
            request: Request,
            x_user_id: str | None = Header(default=None, convert_underscores=False),
            x_user_roles: str | None = Header(default=None, convert_underscores=False),
        ) -> Dict[str, Any]:
            context = getattr(request.state, "security_context", None)
            if context:
                user_roles = set(context.roles)
                user_id = context.user_id
            else:
                user_roles = self.parse_roles(x_user_roles)
                user_id = x_user_id or "anonymous"
            if not self._has_permission(user_roles, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}",
                )
            if context:
                context.roles = user_roles
                context.user_id = user_id
            return {"user_id": user_id, "roles": list(user_roles)}

        return Depends(dependency)

    # ------- 工具 -------

    def parse_roles(self, roles_header: str | None) -> Set[str]:
        if not roles_header:
            return set(self.default_roles)
        roles = {role.strip().lower() for role in roles_header.split(",") if role.strip()}
        return roles or set(self.default_roles)

    def _parse_roles(self, roles_header: str | None) -> Set[str]:
        return self.parse_roles(roles_header)

    def _has_permission(self, roles: Set[str], permission: str) -> bool:
        for role in roles:
            perms = self.role_permissions.get(role, set())
            if permission in perms or permission.split(":")[0] + ":read" in perms and permission.endswith(":read"):
                return True
        return False


@lru_cache()
def get_permission_guard() -> PermissionGuard:
    return PermissionGuard()


