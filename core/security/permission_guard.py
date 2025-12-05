"""
权限守卫模块
"""

from typing import List, Optional


class PermissionGuard:
    """权限守卫"""
    
    def __init__(self):
        self.permissions = {}
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查权限"""
        return True  # 简化实现


def get_permission_guard() -> PermissionGuard:
    """获取权限守卫实例"""
    return PermissionGuard()