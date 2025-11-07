"""
OAuth2认证系统
支持多种OAuth2流程
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os


# ==================== 配置 ====================

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==================== 数据模型 ====================

class Token:
    """Token响应"""
    def __init__(self, access_token: str, token_type: str = "bearer", 
                 refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.token_type = token_type
        self.refresh_token = refresh_token


class TokenData:
    """Token数据"""
    def __init__(self, username: Optional[str] = None, scopes: list = None):
        self.username = username
        self.scopes = scopes or []


class User:
    """用户模型"""
    def __init__(self, username: str, email: str = None, 
                 full_name: str = None, disabled: bool = False,
                 roles: list = None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.disabled = disabled
        self.roles = roles or ["user"]


# ==================== 密码处理 ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


# ==================== Token处理 ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问Token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """创建刷新Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """解码Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: list = payload.get("scopes", [])
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无法验证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(username=username, scopes=scopes)
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )


def refresh_access_token(refresh_token: str) -> str:
    """使用刷新Token获取新的访问Token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新Token"
            )
        
        username = payload.get("sub")
        scopes = payload.get("scopes", [])
        
        # 创建新的访问Token
        access_token = create_access_token(
            data={"sub": username, "scopes": scopes}
        )
        
        return access_token
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新Token无效或已过期"
        )


# ==================== 用户验证 ====================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    token_data = decode_token(token)
    
    # TODO: 从数据库获取用户信息
    # 这里简化为直接返回用户对象
    user = User(username=token_data.username)
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    return current_user


# ==================== 权限检查 ====================

def check_permission(required_roles: list):
    """检查用户权限的依赖函数"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        user_roles = set(current_user.roles)
        required_roles_set = set(required_roles)
        
        if not user_roles.intersection(required_roles_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return permission_checker


# ==================== RBAC权限系统 ====================

class RBACSystem:
    """基于角色的访问控制系统"""
    
    def __init__(self):
        self.permissions = {
            "admin": ["*"],  # 所有权限
            "manager": [
                "read:all",
                "write:customers",
                "write:orders",
                "write:production",
                "read:finance"
            ],
            "user": [
                "read:public",
                "write:own"
            ],
            "guest": [
                "read:public"
            ]
        }
    
    def has_permission(self, user: User, required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        for role in user.roles:
            role_permissions = self.permissions.get(role, [])
            
            # 管理员有所有权限
            if "*" in role_permissions:
                return True
            
            # 检查具体权限
            if required_permission in role_permissions:
                return True
            
            # 检查通配符权限
            permission_parts = required_permission.split(":")
            if len(permission_parts) == 2:
                action, resource = permission_parts
                wildcard = f"{action}:*"
                if wildcard in role_permissions:
                    return True
        
        return False


rbac = RBACSystem()


def require_permission(permission: str):
    """要求特定权限的装饰器"""
    async def permission_validator(
        current_user: User = Depends(get_current_active_user)
    ):
        if not rbac.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}"
            )
        return current_user
    
    return permission_validator

