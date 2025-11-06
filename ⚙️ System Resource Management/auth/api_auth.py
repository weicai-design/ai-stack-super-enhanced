"""
API认证和权限管理系统
支持API Key、JWT Token等多种认证方式
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from enum import Enum


class UserRole(Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class APIAuthManager:
    """API认证管理器"""
    
    def __init__(self, secret_key: str = None):
        """
        初始化认证管理器
        
        Args:
            secret_key: JWT密钥
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        
        # API Key存储
        self.api_keys = {}
        
        # 用户存储
        self.users = {}
        
        # Token黑名单
        self.token_blacklist = set()
        
        # 权限配置
        self.permissions = {
            UserRole.ADMIN: ["*"],  # 所有权限
            UserRole.USER: [
                "read:*",
                "write:own",
                "execute:task"
            ],
            UserRole.GUEST: [
                "read:public"
            ]
        }
    
    # ============ API Key认证 ============
    
    def generate_api_key(
        self,
        user_id: str,
        role: UserRole = UserRole.USER,
        expires_days: int = 365
    ) -> Dict[str, Any]:
        """
        生成API Key
        
        Args:
            user_id: 用户ID
            role: 用户角色
            expires_days: 过期天数
        
        Returns:
            API Key信息
        """
        # 生成随机API Key
        api_key = f"sk-{secrets.token_urlsafe(32)}"
        
        # API Key哈希（存储时不保存原始key）
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # 过期时间
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        # 保存API Key信息
        self.api_keys[api_key_hash] = {
            "user_id": user_id,
            "role": role.value,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_active": True,
            "last_used": None,
            "usage_count": 0
        }
        
        return {
            "api_key": api_key,  # 只返回一次
            "api_key_hash": api_key_hash,
            "user_id": user_id,
            "role": role.value,
            "expires_at": expires_at.isoformat()
        }
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        验证API Key
        
        Args:
            api_key: API Key
        
        Returns:
            验证结果
        """
        # 计算哈希
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # 查找API Key
        key_info = self.api_keys.get(api_key_hash)
        
        if not key_info:
            return {
                "valid": False,
                "error": "无效的API Key"
            }
        
        # 检查是否激活
        if not key_info["is_active"]:
            return {
                "valid": False,
                "error": "API Key已被禁用"
            }
        
        # 检查是否过期
        expires_at = datetime.fromisoformat(key_info["expires_at"])
        if datetime.now() > expires_at:
            return {
                "valid": False,
                "error": "API Key已过期"
            }
        
        # 更新使用记录
        key_info["last_used"] = datetime.now().isoformat()
        key_info["usage_count"] += 1
        
        return {
            "valid": True,
            "user_id": key_info["user_id"],
            "role": key_info["role"],
            "permissions": self.permissions.get(UserRole(key_info["role"]), [])
        }
    
    def revoke_api_key(self, api_key_hash: str) -> Dict[str, Any]:
        """
        撤销API Key
        
        Args:
            api_key_hash: API Key哈希
        
        Returns:
            撤销结果
        """
        if api_key_hash in self.api_keys:
            self.api_keys[api_key_hash]["is_active"] = False
            return {
                "success": True,
                "message": "API Key已撤销"
            }
        
        return {
            "success": False,
            "error": "API Key不存在"
        }
    
    # ============ JWT Token认证 ============
    
    def generate_token(
        self,
        user_id: str,
        role: UserRole = UserRole.USER,
        expires_hours: int = 24
    ) -> Dict[str, Any]:
        """
        生成JWT Token
        
        Args:
            user_id: 用户ID
            role: 用户角色
            expires_hours: 过期小时数
        
        Returns:
            Token信息
        """
        # Token过期时间
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # Token载荷
        payload = {
            "user_id": user_id,
            "role": role.value,
            "iat": datetime.now(),
            "exp": expires_at
        }
        
        # 生成Token
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": expires_hours * 3600,
            "expires_at": expires_at.isoformat()
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT Token
        
        Args:
            token: JWT Token
        
        Returns:
            验证结果
        """
        try:
            # 检查黑名单
            if token in self.token_blacklist:
                return {
                    "valid": False,
                    "error": "Token已被撤销"
                }
            
            # 解码Token
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            return {
                "valid": True,
                "user_id": payload["user_id"],
                "role": payload["role"],
                "permissions": self.permissions.get(UserRole(payload["role"]), [])
            }
        
        except jwt.ExpiredSignatureError:
            return {
                "valid": False,
                "error": "Token已过期"
            }
        except jwt.InvalidTokenError:
            return {
                "valid": False,
                "error": "无效的Token"
            }
    
    def revoke_token(self, token: str) -> Dict[str, Any]:
        """
        撤销Token（加入黑名单）
        
        Args:
            token: JWT Token
        
        Returns:
            撤销结果
        """
        self.token_blacklist.add(token)
        
        return {
            "success": True,
            "message": "Token已撤销"
        }
    
    # ============ 权限检查 ============
    
    def check_permission(
        self,
        role: UserRole,
        required_permission: str
    ) -> bool:
        """
        检查权限
        
        Args:
            role: 用户角色
            required_permission: 需要的权限
        
        Returns:
            是否有权限
        """
        user_permissions = self.permissions.get(role, [])
        
        # 管理员拥有所有权限
        if "*" in user_permissions:
            return True
        
        # 精确匹配
        if required_permission in user_permissions:
            return True
        
        # 通配符匹配
        for perm in user_permissions:
            if perm.endswith(":*"):
                prefix = perm[:-2]
                if required_permission.startswith(prefix):
                    return True
        
        return False
    
    # ============ 用户管理 ============
    
    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole = UserRole.USER
    ) -> Dict[str, Any]:
        """
        创建用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色
        
        Returns:
            用户信息
        """
        if username in self.users:
            return {
                "success": False,
                "error": "用户名已存在"
            }
        
        # 密码哈希
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user_id = f"user_{len(self.users) + 1}"
        
        self.users[username] = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "role": role.value,
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "role": role.value
        }
    
    def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            认证结果
        """
        user = self.users.get(username)
        
        if not user:
            return {
                "success": False,
                "error": "用户不存在"
            }
        
        # 验证密码
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user["password_hash"] != password_hash:
            return {
                "success": False,
                "error": "密码错误"
            }
        
        if not user["is_active"]:
            return {
                "success": False,
                "error": "用户已被禁用"
            }
        
        # 生成Token
        token_info = self.generate_token(
            user["user_id"],
            UserRole(user["role"])
        )
        
        return {
            "success": True,
            "user_id": user["user_id"],
            "username": username,
            "role": user["role"],
            **token_info
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取认证统计"""
        active_api_keys = sum(
            1 for key in self.api_keys.values()
            if key["is_active"]
        )
        
        return {
            "users_count": len(self.users),
            "api_keys_total": len(self.api_keys),
            "api_keys_active": active_api_keys,
            "tokens_revoked": len(self.token_blacklist)
        }


# 全局实例
api_auth = APIAuthManager()




