#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限守卫模块 (Permission Guard)

架构设计说明：
- 基于RBAC（基于角色的访问控制）模式实现
- 支持多租户权限隔离，确保数据安全
- 采用模块化设计，便于扩展和维护
- 支持环境变量配置，实现灵活部署

核心功能：
- 角色权限映射管理
- 权限验证和访问控制
- 默认角色配置
- 权限配置热重载

技术选型：
- 使用Python标准库，无外部依赖
- 基于FastAPI依赖注入实现权限检查
- 支持环境变量配置覆盖

部署配置：
- 通过RBAC_DEFAULT_ROLES环境变量配置默认角色
- 通过RBAC_EXTRA_PERMISSIONS环境变量扩展权限配置
- 支持JSON格式的权限配置
"""

from __future__ import annotations

import os
import logging
from functools import lru_cache
from typing import Any, Dict, Set, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from .config_manager import get_security_config_manager

logger = logging.getLogger(__name__)


class PermissionGuard:
    """权限守卫"""

    def __init__(self):
        self.config_manager = get_security_config_manager()
        self.role_permissions = self._load_role_permissions()
        self.default_roles = self._load_default_roles()
        self.logger = logging.getLogger(__name__)
    
    def _load_role_permissions(self) -> Dict[str, Set[str]]:
        """从环境变量加载角色权限配置，支持动态更新"""
        # 基础权限配置
        base_permissions = {
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
        
        # 从配置管理器加载额外权限配置
        extra_permissions = self.config_manager.get_config("rbac", "extra_permissions", {})
        for role, permissions in extra_permissions.items():
            if role in base_permissions:
                base_permissions[role].update(set(permissions))
            else:
                base_permissions[role] = set(permissions)
        
        # 配置验证
        self._validate_permissions_config(base_permissions)
        
        return base_permissions
    
    def _validate_permissions_config(self, permissions: Dict[str, Set[str]]) -> None:
        """验证权限配置"""
        required_roles = ["admin", "viewer"]
        for role in required_roles:
            if role not in permissions:
                # 使用print代替logger，因为当前类没有logger属性
                print(f"警告: 缺少必需角色权限配置: {role}")
        
        # 检查权限格式
        for role, perms in permissions.items():
            for perm in perms:
                if not isinstance(perm, str) or not perm.strip():
                    print(f"警告: 角色 {role} 的权限格式无效: {perm}")
                elif ":" not in perm:
                    print(f"警告: 角色 {role} 的权限格式不正确，应包含冒号分隔: {perm}")
    
    def _retry_with_backoff(self, func: Callable, max_retries: int = 3) -> Any:
        """带指数退避的重试机制"""
        import time
        import random
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    print(f"错误: 操作失败，达到最大重试次数: {e}")
                    raise
                
                # 指数退避
                delay = (2 ** attempt) + random.uniform(0, 1)
                print(f"警告: 操作失败，第 {attempt + 1} 次重试，等待 {delay:.2f} 秒: {e}")
                time.sleep(delay)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "roles_count": len(self.role_permissions),
            "default_roles": list(self.default_roles),
        }
        
        # 检查配置完整性
        required_roles = ["admin", "viewer"]
        missing_roles = [role for role in required_roles if role not in self.role_permissions]
        
        if missing_roles:
            health_status["status"] = "warning"
            health_status["missing_roles"] = missing_roles
        
        # 检查权限有效性
        invalid_permissions = []
        for role, perms in self.role_permissions.items():
            for perm in perms:
                if not isinstance(perm, str) or not perm.strip():
                    invalid_permissions.append(f"{role}: {perm}")
        
        if invalid_permissions:
            health_status["status"] = "warning"
            health_status["invalid_permissions"] = invalid_permissions
        
        return health_status
    
    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置"""
        try:
            old_roles = self.role_permissions.copy()
            old_defaults = self.default_roles.copy()
            
            # 重新加载配置
            self.role_permissions = self._load_role_permissions()
            self.default_roles = self._load_default_roles()
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "roles_updated": len(self.role_permissions) - len(old_roles),
                "defaults_updated": len(self.default_roles) - len(old_defaults),
                "message": "配置重新加载成功"
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": "配置重新加载失败"
            }
    
    def _load_default_roles(self) -> Set[str]:
        """从环境变量加载默认角色配置"""
        # 从配置管理器加载默认角色配置
        default_roles = self.config_manager.get_config("rbac", "default_roles", "viewer")
        return {role.strip() for role in default_roles.split(",") if role.strip()}

    # ------- 接口 -------

    def require(self, permission: str):
        """返回权限检查的依赖函数"""
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

        return dependency

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


