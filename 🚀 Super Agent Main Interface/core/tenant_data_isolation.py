#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租户数据隔离管理器
P3-402: 在DB/缓存/文件层面实现租户隔离
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class TenantDataIsolation:
    """
    租户数据隔离管理器
    
    功能：
    1. 数据库隔离（Schema/行级）
    2. 缓存隔离（Key前缀）
    3. 文件隔离（路径隔离）
    4. 配额管理
    """
    
    def __init__(self, base_storage_path: str = "./data/tenants"):
        """
        初始化数据隔离管理器
        
        Args:
            base_storage_path: 基础存储路径
        """
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
        
        # 租户隔离配置
        self.tenant_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"租户数据隔离管理器初始化完成，存储路径: {self.base_storage_path}")
    
    # ============ 数据库隔离 ============
    
    def get_tenant_db_config(
        self,
        tenant_id: str,
        isolation_strategy: str = "schema",
    ) -> Dict[str, Any]:
        """
        获取租户数据库配置
        
        Args:
            tenant_id: 租户ID
            isolation_strategy: 隔离策略 (schema/row/database)
            
        Returns:
            数据库配置
        """
        if isolation_strategy == "database":
            # 独立数据库
            return {
                "database_url": f"sqlite:///./data/tenants/{tenant_id}/tenant.db",
                "schema": None,
                "isolation_level": "database",
            }
        elif isolation_strategy == "schema":
            # Schema隔离
            return {
                "database_url": "sqlite:///./data/tenants/shared.db",
                "schema": f"tenant_{tenant_id}",
                "isolation_level": "schema",
            }
        else:  # row
            # 行级隔离
            return {
                "database_url": "sqlite:///./data/tenants/shared.db",
                "schema": None,
                "isolation_level": "row",
                "tenant_column": "tenant_id",
            }
    
    def apply_row_level_isolation(
        self,
        query,
        tenant_id: str,
        tenant_column: str = "tenant_id",
    ):
        """
        应用行级隔离到查询
        
        Args:
            query: SQLAlchemy查询对象
            tenant_id: 租户ID
            tenant_column: 租户列名
            
        Returns:
            过滤后的查询
        """
        return query.filter(getattr(query.column_descriptions[0]['entity'], tenant_column) == tenant_id)
    
    # ============ 缓存隔离 ============
    
    def get_tenant_cache_key(
        self,
        tenant_id: str,
        key: str,
    ) -> str:
        """
        获取租户隔离的缓存Key
        
        Args:
            tenant_id: 租户ID
            key: 原始Key
            
        Returns:
            隔离后的Key
        """
        # 使用租户ID作为前缀
        return f"tenant:{tenant_id}:{key}"
    
    def get_tenant_cache_pattern(
        self,
        tenant_id: str,
        pattern: str = "*",
    ) -> str:
        """
        获取租户缓存Key模式
        
        Args:
            tenant_id: 租户ID
            pattern: 原始模式
            
        Returns:
            隔离后的模式
        """
        return f"tenant:{tenant_id}:{pattern}"
    
    def clear_tenant_cache(
        self,
        tenant_id: str,
        cache_client: Any,
    ) -> bool:
        """
        清除租户缓存
        
        Args:
            tenant_id: 租户ID
            cache_client: 缓存客户端（Redis等）
            
        Returns:
            是否成功
        """
        try:
            pattern = self.get_tenant_cache_pattern(tenant_id, "*")
            if hasattr(cache_client, "delete_pattern"):
                # Redis
                cache_client.delete_pattern(pattern)
            elif hasattr(cache_client, "keys"):
                # 其他支持keys的缓存
                keys = cache_client.keys(pattern)
                if keys:
                    cache_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"清除租户缓存失败: {e}")
            return False
    
    # ============ 文件隔离 ============
    
    def get_tenant_storage_path(
        self,
        tenant_id: str,
        sub_path: Optional[str] = None,
    ) -> Path:
        """
        获取租户存储路径
        
        Args:
            tenant_id: 租户ID
            sub_path: 子路径
            
        Returns:
            完整路径
        """
        # 使用租户ID的哈希值作为目录名（避免特殊字符）
        tenant_hash = hashlib.md5(tenant_id.encode()).hexdigest()[:8]
        base_path = self.base_storage_path / tenant_hash
        
        if sub_path:
            full_path = base_path / sub_path
        else:
            full_path = base_path
        
        # 创建目录
        full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    def get_tenant_file_path(
        self,
        tenant_id: str,
        filename: str,
        category: Optional[str] = None,
    ) -> Path:
        """
        获取租户文件路径
        
        Args:
            tenant_id: 租户ID
            filename: 文件名
            category: 文件类别（documents/images/exports等）
            
        Returns:
            完整文件路径
        """
        if category:
            storage_path = self.get_tenant_storage_path(tenant_id, category)
        else:
            storage_path = self.get_tenant_storage_path(tenant_id)
        
        return storage_path / filename
    
    def list_tenant_files(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        pattern: str = "*",
    ) -> List[Path]:
        """
        列出租户文件
        
        Args:
            tenant_id: 租户ID
            category: 文件类别
            pattern: 文件模式
            
        Returns:
            文件路径列表
        """
        storage_path = self.get_tenant_storage_path(tenant_id, category)
        return list(storage_path.glob(pattern))
    
    def delete_tenant_files(
        self,
        tenant_id: str,
        category: Optional[str] = None,
        pattern: str = "*",
    ) -> int:
        """
        删除租户文件
        
        Args:
            tenant_id: 租户ID
            category: 文件类别
            pattern: 文件模式
            
        Returns:
            删除的文件数
        """
        files = self.list_tenant_files(tenant_id, category, pattern)
        deleted_count = 0
        
        for file_path in files:
            try:
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"删除文件失败: {file_path} - {e}")
        
        return deleted_count
    
    def get_tenant_storage_size(
        self,
        tenant_id: str,
    ) -> int:
        """
        获取租户存储大小（字节）
        
        Args:
            tenant_id: 租户ID
            
        Returns:
            存储大小（字节）
        """
        storage_path = self.get_tenant_storage_path(tenant_id)
        total_size = 0
        
        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    # ============ 配额检查 ============
    
    def check_storage_quota(
        self,
        tenant_id: str,
        required_size: int,
        quota_manager: Any,
    ) -> tuple[bool, Optional[str]]:
        """
        检查存储配额
        
        Args:
            tenant_id: 租户ID
            required_size: 所需大小（字节）
            quota_manager: 配额管理器
            
        Returns:
            (是否允许, 错误信息)
        """
        if not quota_manager:
            return True, None
        
        # 获取当前使用量
        current_size = self.get_tenant_storage_size(tenant_id)
        
        # 获取配额
        quota = quota_manager.get_quota(tenant_id, "storage")
        if not quota:
            return True, None
        
        # 检查配额
        if current_size + required_size > quota:
            return False, f"存储配额不足: 当前{current_size}字节 + 需要{required_size}字节 > 配额{quota}字节"
        
        return True, None
    
    def check_file_count_quota(
        self,
        tenant_id: str,
        required_count: int,
        quota_manager: Any,
    ) -> tuple[bool, Optional[str]]:
        """
        检查文件数量配额
        
        Args:
            tenant_id: 租户ID
            required_count: 所需文件数
            quota_manager: 配额管理器
            
        Returns:
            (是否允许, 错误信息)
        """
        if not quota_manager:
            return True, None
        
        # 获取当前文件数
        current_files = len(self.list_tenant_files(tenant_id))
        
        # 获取配额
        quota = quota_manager.get_quota(tenant_id, "file_count")
        if not quota:
            return True, None
        
        # 检查配额
        if current_files + required_count > quota:
            return False, f"文件数量配额不足: 当前{current_files} + 需要{required_count} > 配额{quota}"
        
        return True, None


_tenant_data_isolation: Optional[TenantDataIsolation] = None


def get_tenant_data_isolation() -> TenantDataIsolation:
    """获取租户数据隔离管理器实例"""
    global _tenant_data_isolation
    if _tenant_data_isolation is None:
        _tenant_data_isolation = TenantDataIsolation()
    return _tenant_data_isolation

