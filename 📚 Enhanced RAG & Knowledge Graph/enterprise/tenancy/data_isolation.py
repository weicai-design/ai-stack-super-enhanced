"""
数据隔离策略
Data Isolation Strategy

实现租户间的数据隔离

版本: v3.0.0
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .models import Tenant, IsolationStrategy

logger = logging.getLogger(__name__)


# ==================== 数据隔离策略 ====================

class DataIsolationStrategy:
    """数据隔离策略基类"""
    
    def get_namespace(self, tenant: Tenant) -> str:
        """
        获取租户的命名空间
        
        Args:
            tenant: 租户对象
        
        Returns:
            命名空间字符串
        """
        raise NotImplementedError
    
    def filter_query(self, tenant: Tenant, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤查询（添加租户条件）
        
        Args:
            tenant: 租户对象
            query: 原始查询
        
        Returns:
            添加租户过滤后的查询
        """
        raise NotImplementedError


class SchemaIsolation(DataIsolationStrategy):
    """Schema级别隔离（推荐）"""
    
    def get_namespace(self, tenant: Tenant) -> str:
        """
        获取Schema名称
        
        返回: tenant_{tenant_id}
        """
        return f"tenant_{tenant.id.replace('-', '_')}"
    
    def get_cache_prefix(self, tenant: Tenant) -> str:
        """获取缓存key前缀"""
        return f"tenant:{tenant.id}"
    
    def get_storage_path(self, tenant: Tenant) -> str:
        """获取存储路径"""
        return f"tenants/{tenant.id}"
    
    def filter_query(self, tenant: Tenant, query: Dict[str, Any]) -> Dict[str, Any]:
        """Schema隔离不需要过滤查询（已在Schema级别隔离）"""
        return query


class RowLevelIsolation(DataIsolationStrategy):
    """行级安全隔离"""
    
    def get_namespace(self, tenant: Tenant) -> str:
        """行级隔离使用共享Schema"""
        return "shared"
    
    def filter_query(self, tenant: Tenant, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加租户过滤条件
        
        在所有查询中添加 WHERE tenant_id = 'xxx'
        """
        if "filters" not in query:
            query["filters"] = {}
        
        query["filters"]["tenant_id"] = tenant.id
        return query
    
    def get_cache_prefix(self, tenant: Tenant) -> str:
        """获取缓存key前缀"""
        return f"tenant:{tenant.id}"
    
    def get_storage_path(self, tenant: Tenant) -> str:
        """获取存储路径"""
        return f"tenants/{tenant.id}"


class DatabaseIsolation(DataIsolationStrategy):
    """数据库级别隔离（最强）"""
    
    def get_namespace(self, tenant: Tenant) -> str:
        """
        获取数据库名称
        
        返回: aistack_tenant_{tenant_id}
        """
        return f"aistack_tenant_{tenant.id.replace('-', '_')}"
    
    def get_cache_prefix(self, tenant: Tenant) -> str:
        """获取缓存key前缀"""
        return f"db:{self.get_namespace(tenant)}"
    
    def get_storage_path(self, tenant: Tenant) -> str:
        """获取存储路径"""
        return f"databases/{tenant.id}"
    
    def filter_query(self, tenant: Tenant, query: Dict[str, Any]) -> Dict[str, Any]:
        """数据库隔离不需要过滤（已在数据库级别隔离）"""
        return query


# ==================== 隔离策略工厂 ====================

class IsolationStrategyFactory:
    """隔离策略工厂"""
    
    @staticmethod
    def create(strategy_type: IsolationStrategy) -> DataIsolationStrategy:
        """
        创建隔离策略实例
        
        Args:
            strategy_type: 策略类型
        
        Returns:
            策略实例
        """
        strategies = {
            IsolationStrategy.SCHEMA: SchemaIsolation,
            IsolationStrategy.ROW_LEVEL: RowLevelIsolation,
            IsolationStrategy.DATABASE: DatabaseIsolation
        }
        
        strategy_class = strategies.get(strategy_type, SchemaIsolation)
        return strategy_class()


# ==================== 租户上下文管理 ====================

class TenantContext:
    """租户上下文管理"""
    
    def __init__(self, tenant: Tenant):
        """
        初始化租户上下文
        
        Args:
            tenant: 租户对象
        """
        self.tenant = tenant
        self.strategy = IsolationStrategyFactory.create(tenant.isolation_strategy)
    
    def get_cache_key(self, base_key: str) -> str:
        """获取带租户前缀的缓存key"""
        prefix = self.strategy.get_cache_prefix(self.tenant)
        return f"{prefix}:{base_key}"
    
    def get_storage_path(self, relative_path: str) -> str:
        """获取租户的存储路径"""
        base_path = self.strategy.get_storage_path(self.tenant)
        return f"{base_path}/{relative_path}"
    
    def filter_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """过滤查询添加租户条件"""
        return self.strategy.filter_query(self.tenant, query)
    
    def check_quota(self, quota_type: str, amount: int = 1) -> bool:
        """检查配额"""
        from .manager import tenant_manager
        return tenant_manager.check_quota(self.tenant.id, quota_type, amount)
    
    def increment_usage(self, quota_type: str, amount: int = 1):
        """增加使用量"""
        from .manager import tenant_manager
        tenant_manager.increment_usage(self.tenant.id, quota_type, amount)


# ==================== 辅助函数 ====================

def get_tenant_context(tenant: Tenant) -> TenantContext:
    """获取租户上下文"""
    return TenantContext(tenant)


# ==================== 导出 ====================

__all__ = [
    "TenantIdentifier",
    "TenantMiddleware",
    "TenantContext",
    "get_tenant_context",
    "IsolationStrategyFactory"
]






































