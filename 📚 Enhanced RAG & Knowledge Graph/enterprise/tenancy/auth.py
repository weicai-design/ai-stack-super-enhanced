"""
多租户认证和授权模块
Multi-tenant Authentication and Authorization

功能：
1. JWT Token 校验与租户绑定
2. API Key 管理与验证
3. 命令白名单权限控制
4. 租户上下文绑定

版本: v3.1.0
"""

from __future__ import annotations

import os
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Any
from enum import Enum

import jwt
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from .models import Tenant, TenantStatus
from .manager import tenant_manager

logger = logging.getLogger(__name__)


# ==================== 配置 ====================

# JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# API Key 配置
API_KEY_PREFIX = "ak_"  # API Key 前缀
API_KEY_LENGTH = 32  # API Key 长度（不含前缀）


# ==================== 模型 ====================

class TokenType(str, Enum):
    """Token 类型"""
    ACCESS = "access"
    REFRESH = "refresh"


class APIKeyScope(str, Enum):
    """API Key 权限范围"""
    READ = "read"              # 只读
    WRITE = "write"            # 读写
    ADMIN = "admin"            # 管理员
    FULL = "full"              # 完全访问


class TokenPayload(BaseModel):
    """JWT Token 载荷"""
    tenant_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    token_type: TokenType = TokenType.ACCESS
    scopes: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID，用于撤销


class APIKey(BaseModel):
    """API Key 模型"""
    id: str
    tenant_id: str
    name: str
    key_hash: str  # 加密后的 key
    scopes: List[APIKeyScope] = Field(default_factory=list)
    allowed_commands: List[str] = Field(default_factory=list)  # 允许的命令列表
    rate_limit: Optional[int] = None  # 速率限制（每分钟）
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False

    def can_execute_command(self, command: str) -> bool:
        """检查是否可以执行命令"""
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        
        # 如果没有配置允许的命令列表，则根据权限范围判断
        if not self.allowed_commands:
            # 管理员或完全访问权限可以执行所有命令
            if APIKeyScope.ADMIN in self.scopes or APIKeyScope.FULL in self.scopes:
                return True
            # 读写权限可以执行大部分命令
            if APIKeyScope.WRITE in self.scopes:
                return True
            # 只读权限只能执行查询类命令
            if APIKeyScope.READ in self.scopes:
                return command.startswith(("查询", "查看", "获取", "列表", "search", "get", "list"))
            return False
        
        # 检查命令是否在白名单中
        return command in self.allowed_commands


class CommandWhitelist:
    """命令白名单管理器"""
    
    # 默认命令分类
    READ_COMMANDS = {
        "查询", "查看", "获取", "列表", "搜索", "统计",
        "search", "get", "list", "query", "stats", "status"
    }
    
    WRITE_COMMANDS = {
        "创建", "添加", "更新", "修改", "删除", "保存",
        "create", "add", "update", "modify", "delete", "save"
    }
    
    ADMIN_COMMANDS = {
        "配置", "设置", "管理", "授权", "撤销",
        "config", "set", "manage", "grant", "revoke"
    }
    
    DANGEROUS_COMMANDS = {
        "删除所有", "清空", "重置", "格式化",
        "delete_all", "clear", "reset", "format"
    }
    
    @classmethod
    def normalize_command(cls, command: str) -> str:
        """标准化命令"""
        command = command.strip().lower()
        # 移除多余空格
        command = " ".join(command.split())
        return command
    
    @classmethod
    def classify_command(cls, command: str) -> str:
        """分类命令"""
        normalized = cls.normalize_command(command)
        
        # 检查危险命令
        for dangerous in cls.DANGEROUS_COMMANDS:
            if dangerous in normalized:
                return "dangerous"
        
        # 检查管理员命令
        for admin in cls.ADMIN_COMMANDS:
            if admin in normalized:
                return "admin"
        
        # 检查写入命令
        for write in cls.WRITE_COMMANDS:
            if write in normalized:
                return "write"
        
        # 检查只读命令
        for read in cls.READ_COMMANDS:
            if read in normalized:
                return "read"
        
        return "unknown"


# ==================== JWT Token 管理 ====================

class TokenService:
    """JWT Token 服务"""
    
    @staticmethod
    def create_access_token(
        tenant_id: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        
        Args:
            tenant_id: 租户ID
            user_id: 用户ID
            email: 用户邮箱
            scopes: 权限范围
            expires_delta: 过期时间差
        
        Returns:
            JWT token 字符串
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "email": email,
            "token_type": TokenType.ACCESS.value,
            "scopes": scopes or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def create_refresh_token(
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "token_type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    @classmethod
    def verify_token(cls, token: str, check_blacklist: bool = True) -> TokenPayload:
        """
        验证并解析 Token
        
        Args:
            token: JWT token 字符串
            check_blacklist: 是否检查黑名单（默认True）
        
        Returns:
            TokenPayload 对象
        
        Raises:
            HTTPException: Token 无效或过期
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            token_id = payload.get("jti")  # JWT ID
            
            # 检查黑名单（如果启用）
            if check_blacklist and token_id:
                try:
                    from .database import get_database
                    db = get_database()
                    if db.is_token_blacklisted(token_id):
                        raise HTTPException(status_code=401, detail="Token 已撤销")
                except HTTPException:
                    # HTTPException 应该直接抛出
                    raise
                except Exception as e:
                    # 其他异常（如数据库连接失败）记录日志但允许通过
                    # 生产环境应该启用数据库，开发环境可以容忍
                    logger.debug(f"检查黑名单失败（可能未启用数据库）: {e}")
            
            # 验证租户存在且有效
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                raise HTTPException(status_code=401, detail="Token 中缺少租户ID")
            
            tenant = tenant_manager.get_tenant(tenant_id)
            if not tenant:
                raise HTTPException(status_code=401, detail="租户不存在")
            
            if tenant.status != TenantStatus.ACTIVE:
                raise HTTPException(status_code=403, detail=f"租户状态异常: {tenant.status}")
            
            return TokenPayload(
                tenant_id=payload["tenant_id"],
                user_id=payload.get("user_id"),
                email=payload.get("email"),
                token_type=TokenType(payload.get("token_type", TokenType.ACCESS.value)),
                scopes=payload.get("scopes", []),
                exp=datetime.fromtimestamp(payload["exp"]) if payload.get("exp") else None,
                iat=datetime.fromtimestamp(payload["iat"]) if payload.get("iat") else None,
                jti=token_id
            )
        
        except HTTPException:
            raise
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token 已过期")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Token 无效: {str(e)}")
        except Exception as e:
            logger.error(f"Token 验证失败: {e}")
            raise HTTPException(status_code=401, detail="Token 验证失败")
    
    @staticmethod
    def revoke_token(token: str, reason: Optional[str] = None) -> bool:
        """
        撤销 Token（加入黑名单）
        
        Args:
            token: JWT token 字符串
            reason: 撤销原因
        
        Returns:
            是否成功撤销
        """
        try:
            # 解析 Token 获取信息
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            
            token_id = payload.get("jti")
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("user_id")
            exp = payload.get("exp")
            
            if not token_id or not tenant_id:
                return False
            
            # 计算过期时间
            expires_at = datetime.fromtimestamp(exp) if exp else datetime.now() + timedelta(minutes=60)
            
            # 添加到黑名单
            try:
                from .database import get_database
                db = get_database()
                db.add_token_to_blacklist(token_id, tenant_id, user_id, expires_at, reason)
                logger.info(f"✅ Token 已撤销: {token_id}")
                return True
            except Exception as e:
                logger.error(f"❌ 撤销 Token 失败: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 解析 Token 失败: {e}")
            return False


# ==================== API Key 管理 ====================

class APIKeyService:
    """API Key 管理服务"""
    
    def __init__(self, use_database: bool = True):
        """
        初始化 API Key 服务
        
        Args:
            use_database: 是否使用数据库存储（默认True，使用SQLite）
        """
        self.use_database = use_database
        
        if use_database:
            # 使用数据库存储
            try:
                from .database import get_database
                self.db = get_database()
                logger.info("✅ API Key 服务已初始化（使用数据库存储）")
            except Exception as e:
                logger.warning(f"数据库初始化失败，使用内存存储: {e}")
                self.use_database = False
                self._init_memory_storage()
        else:
            # 使用内存存储（开发/测试环境）
            self._init_memory_storage()
    
    def _init_memory_storage(self):
        """初始化内存存储"""
        self.api_keys: Dict[str, APIKey] = {}  # key_hash -> APIKey
        self.api_keys_by_tenant: Dict[str, List[str]] = {}  # tenant_id -> [key_ids]
        logger.info("✅ API Key 服务已初始化（使用内存存储）")
    
    def generate_api_key(self) -> str:
        """生成新的 API Key"""
        # 生成随机字符串
        random_bytes = secrets.token_bytes(API_KEY_LENGTH)
        key = API_KEY_PREFIX + secrets.token_urlsafe(API_KEY_LENGTH)[:API_KEY_LENGTH]
        return key
    
    def hash_api_key(self, api_key: str) -> str:
        """对 API Key 进行哈希"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(
        self,
        tenant_id: str,
        name: str,
        scopes: Optional[List[APIKeyScope]] = None,
        allowed_commands: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        expires_days: Optional[int] = None
    ) -> tuple[str, APIKey]:
        """
        创建 API Key
        
        Args:
            tenant_id: 租户ID
            name: Key 名称
            scopes: 权限范围
            allowed_commands: 允许的命令列表
            rate_limit: 速率限制
            expires_days: 过期天数
        
        Returns:
            (api_key_string, api_key_object) 元组
        """
        # 验证租户存在
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"租户不存在: {tenant_id}")
        
        # 生成 API Key
        api_key_string = self.generate_api_key()
        key_hash = self.hash_api_key(api_key_string)
        
        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        # 创建 API Key 对象
        api_key = APIKey(
            id=secrets.token_urlsafe(16),
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            scopes=scopes or [APIKeyScope.READ],
            allowed_commands=allowed_commands or [],
            rate_limit=rate_limit,
            expires_at=expires_at
        )
        
        # 存储
        if self.use_database:
            # 使用数据库存储
            self.db.save_api_key(api_key)
        else:
            # 使用内存存储
            self.api_keys[key_hash] = api_key
            if tenant_id not in self.api_keys_by_tenant:
                self.api_keys_by_tenant[tenant_id] = []
            self.api_keys_by_tenant[tenant_id].append(api_key.id)
        
        logger.info(f"✅ API Key 已创建: {name} (tenant: {tenant_id})")
        return api_key_string, api_key
    
    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        验证 API Key
        
        Args:
            api_key: API Key 字符串
        
        Returns:
            APIKey 对象，如果无效则返回 None
        """
        if not api_key or not api_key.startswith(API_KEY_PREFIX):
            return None
        
        key_hash = self.hash_api_key(api_key)
        
        # 获取 API Key 对象
        if self.use_database:
            api_key_obj = self.db.get_api_key_by_hash(key_hash)
        else:
            api_key_obj = self.api_keys.get(key_hash)
        
        if not api_key_obj:
            return None
        
        # 检查是否激活
        if not api_key_obj.is_active:
            logger.warning(f"API Key 未激活: {api_key_obj.id}")
            return None
        
        # 检查是否过期
        if api_key_obj.is_expired():
            logger.warning(f"API Key 已过期: {api_key_obj.id}")
            return None
        
        # 验证租户状态
        tenant = tenant_manager.get_tenant(api_key_obj.tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            logger.warning(f"租户状态异常: {api_key_obj.tenant_id}")
            return None
        
        # 更新最后使用时间
        api_key_obj.last_used_at = datetime.now()
        
        if self.use_database:
            self.db.update_last_used(api_key_obj.id, api_key_obj.last_used_at)
        
        return api_key_obj
    
    def revoke_api_key(self, api_key: str = None, key_id: str = None) -> bool:
        """
        撤销 API Key
        
        Args:
            api_key: API Key 字符串（可选）
            key_id: API Key ID（可选）
        
        Returns:
            是否成功撤销
        """
        if key_id:
            # 通过 ID 撤销
            if self.use_database:
                return self.db.revoke_api_key(key_id)
            else:
                # 内存存储中查找并撤销
                for key_hash, key_obj in self.api_keys.items():
                    if key_obj.id == key_id:
                        key_obj.is_active = False
                        logger.info(f"✅ API Key 已撤销: {key_id}")
                        return True
                return False
        elif api_key:
            # 通过 API Key 字符串撤销
            api_key_obj = self.verify_api_key(api_key)
            if not api_key_obj:
                return False
            
            if self.use_database:
                result = self.db.revoke_api_key(api_key_obj.id)
            else:
                api_key_obj.is_active = False
                result = True
            
            if result:
                logger.info(f"✅ API Key 已撤销: {api_key_obj.id}")
            return result
        
        return False
    
    def list_tenant_api_keys(self, tenant_id: str) -> List[APIKey]:
        """列出租户的 API Keys"""
        if self.use_database:
            return self.db.list_tenant_api_keys(tenant_id)
        else:
            key_ids = self.api_keys_by_tenant.get(tenant_id, [])
            return [
                key for key_hash, key in self.api_keys.items()
                if key.id in key_ids
            ]


# ==================== 全局实例 ====================

token_service = TokenService()
# 使用数据库存储 API Key（根据环境变量决定）
USE_DATABASE = os.getenv("API_KEY_USE_DATABASE", "true").lower() == "true"
api_key_service = APIKeyService(use_database=USE_DATABASE)


# ==================== FastAPI 依赖注入 ====================

security_scheme = HTTPBearer(auto_error=False)


async def get_current_tenant_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> Optional[Tenant]:
    """
    从 JWT Token 获取当前租户
    
    Usage:
        @app.get("/protected")
        async def protected(tenant: Optional[Tenant] = Depends(get_current_tenant_from_token)):
            if not tenant:
                raise HTTPException(401, "需要认证")
    """
    if not credentials:
        return None
    
    try:
        token_payload = token_service.verify_token(credentials.credentials)
        tenant = tenant_manager.get_tenant(token_payload.tenant_id)
        return tenant
    except HTTPException:
        return None


async def require_tenant_from_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> Tenant:
    """
    要求从 JWT Token 获取租户（必须有有效的 token）
    
    Usage:
        @app.get("/protected")
        async def protected(tenant: Tenant = Depends(require_tenant_from_token)):
            # tenant 保证不为 None
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="需要认证令牌")
    
    token_payload = token_service.verify_token(credentials.credentials)
    tenant = tenant_manager.get_tenant(token_payload.tenant_id)
    
    if not tenant:
        raise HTTPException(status_code=401, detail="租户不存在")
    
    return tenant


async def get_current_tenant_from_api_key(
    request: Request
) -> Optional[Tenant]:
    """
    从 API Key 获取当前租户
    
    Usage:
        @app.get("/api")
        async def api(tenant: Optional[Tenant] = Depends(get_current_tenant_from_api_key)):
            if not tenant:
                raise HTTPException(401, "需要 API Key")
    """
    # 从请求头获取 API Key
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not api_key or not api_key.startswith(API_KEY_PREFIX):
        return None
    
    api_key_obj = api_key_service.verify_api_key(api_key)
    if not api_key_obj:
        return None
    
    tenant = tenant_manager.get_tenant(api_key_obj.tenant_id)
    
    # 将 API Key 信息添加到请求状态
    request.state.api_key = api_key_obj
    request.state.tenant_id = api_key_obj.tenant_id
    
    return tenant


async def require_tenant_from_api_key(
    request: Request
) -> tuple[Tenant, APIKey]:
    """
    要求从 API Key 获取租户和 API Key
    
    Returns:
        (Tenant, APIKey) 元组
    
    Usage:
        @app.get("/api")
        async def api(tenant_key: tuple = Depends(require_tenant_from_api_key)):
            tenant, api_key = tenant_key
    """
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="需要 API Key")
    
    if not api_key.startswith(API_KEY_PREFIX):
        raise HTTPException(status_code=401, detail="API Key 格式无效")
    
    api_key_obj = api_key_service.verify_api_key(api_key)
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="API Key 无效或已过期")
    
    tenant = tenant_manager.get_tenant(api_key_obj.tenant_id)
    if not tenant:
        raise HTTPException(status_code=401, detail="租户不存在")
    
    # 将信息添加到请求状态
    request.state.api_key = api_key_obj
    request.state.tenant_id = api_key_obj.tenant_id
    request.state.tenant = tenant
    
    return tenant, api_key_obj


async def check_command_permission(
    command: str,
    request: Request
) -> bool:
    """
    检查命令执行权限
    
    Args:
        command: 命令字符串
        request: FastAPI 请求对象
    
    Returns:
        是否有权限执行
    
    Raises:
        HTTPException: 权限不足
    """
    # 优先检查 API Key
    api_key = getattr(request.state, "api_key", None)
    if api_key:
        if not api_key.can_execute_command(command):
            command_type = CommandWhitelist.classify_command(command)
            raise HTTPException(
                status_code=403,
                detail=f"API Key 无权限执行此命令: {command} (类型: {command_type})"
            )
        return True
    
    # 检查 JWT Token 的权限
    tenant = getattr(request.state, "tenant", None)
    if tenant:
        # TODO: 从 JWT token payload 中检查权限
        # 目前允许所有已认证用户执行命令
        command_type = CommandWhitelist.classify_command(command)
        
        # 危险命令需要额外权限
        if command_type == "dangerous":
            raise HTTPException(
                status_code=403,
                detail="执行危险命令需要管理员权限"
            )
        
        return True
    
    raise HTTPException(status_code=401, detail="需要认证才能执行命令")


# ==================== 租户上下文绑定 ====================

def bind_tenant_context(request: Request, tenant: Tenant) -> None:
    """
    绑定租户上下文到请求
    
    Args:
        request: FastAPI 请求对象
        tenant: 租户对象
    """
    request.state.tenant = tenant
    request.state.tenant_id = tenant.id
    # 处理 plan 和 status 可能是 Enum 或字符串的情况（Pydantic 的 use_enum_values=True）
    plan_value = tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan
    status_value = tenant.status.value if hasattr(tenant.status, 'value') else tenant.status
    request.state.tenant_context = {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "tenant_plan": plan_value,
        "tenant_status": status_value,
        "quota": tenant.quota.dict(),
        "config": tenant.config.dict()
    }


async def get_tenant_context(request: Request) -> Optional[Dict[str, Any]]:
    """
    获取租户上下文
    
    Args:
        request: FastAPI 请求对象
    
    Returns:
        租户上下文字典，如果不存在则返回 None
    """
    return getattr(request.state, "tenant_context", None)


# ==================== 导出 ====================

__all__ = [
    "TokenService",
    "token_service",
    "APIKeyService",
    "api_key_service",
    "CommandWhitelist",
    "TokenPayload",
    "APIKey",
    "APIKeyScope",
    "get_current_tenant_from_token",
    "require_tenant_from_token",
    "get_current_tenant_from_api_key",
    "require_tenant_from_api_key",
    "check_command_permission",
    "bind_tenant_context",
    "get_tenant_context"
]

