#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据服务层
P0-003: 提供统一的数据服务接口，替换所有模拟数据
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from .database_persistence import DatabasePersistence, get_persistence
from .data_sync_manager import DataSyncManager, get_sync_manager, SyncDirection
from .tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)


class DataService:
    """
    数据服务层
    
    功能：
    - 统一的数据访问接口
    - 自动持久化
    - 自动同步
    - 数据验证
    """
    
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        sync_manager: Optional[DataSyncManager] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.sync_manager = sync_manager or get_sync_manager()
        self.multitenant_enabled = os.getenv("MULTITENANT_ENABLED", "1") == "1"
        
        # 表名映射（模块 -> 表名）
        self.table_mapping = {
            "memos": "memos",
            "tasks": "tasks",
            "plans": "plans",
            "workflows": "workflows",
            "events": "events",
            "resources": "resources",
            "learning": "learning",
            "rag": "rag_documents",
            "erp": "erp_data",
            "stock": "stock_data",
            "content": "content_data",
            "trend": "trend_data",
            "operations": "operations_data",
            "expert": "expert_data",
        }
    
    def get_table_name(self, module: str) -> str:
        """获取表名"""
        return self.table_mapping.get(module, f"{module}_data")
    
    async def save_data(
        self,
        module: str,
        data: Dict[str, Any],
        record_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sync: bool = True,
    ) -> str:
        """
        保存数据
        
        Args:
            module: 模块名
            data: 数据字典
            record_id: 记录ID（可选）
            metadata: 元数据（可选）
            sync: 是否同步
            
        Returns:
            记录ID
        """
        table_name = self.get_table_name(module)
        
        # 多租户注入
        metadata = metadata or {}
        if self.multitenant_enabled:
            tenant_id = get_current_tenant_id()
            data = {**data, "_tenant_id": tenant_id}
            metadata = {**metadata, "tenant_id": tenant_id}

        # 保存到持久化层
        record_id = self.persistence.save(
            table_name=table_name,
            record_id=record_id,
            data=data,
            metadata=metadata,
        )
        
        # 添加到同步队列
        if sync:
            await self.sync_manager.sync(
                table_name=table_name,
                record_id=record_id,
                operation="save",
                direction=SyncDirection.BIDIRECTIONAL,
                data=data,
                metadata=metadata,
            )
        
        return record_id
    
    async def load_data(
        self,
        module: str,
        record_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        加载数据
        
        Args:
            module: 模块名
            record_id: 记录ID
            
        Returns:
            数据字典或None
        """
        table_name = self.get_table_name(module)
        record = self.persistence.load(table_name, record_id)
        if self.multitenant_enabled and record:
            if record.get("_tenant_id") != get_current_tenant_id():
                return None
        return record
    
    async def query_data(
        self,
        module: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            module: 模块名
            filters: 过滤条件
            limit: 返回数量限制
            offset: 偏移量
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            数据列表
        """
        table_name = self.get_table_name(module)
        effective_filters = dict(filters or {})
        if self.multitenant_enabled:
            effective_filters["_tenant_id"] = get_current_tenant_id()
        return self.persistence.query(
            table_name=table_name,
            filters=effective_filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
    
    async def delete_data(
        self,
        module: str,
        record_id: str,
        soft_delete: bool = True,
        sync: bool = True,
    ) -> bool:
        """
        删除数据
        
        Args:
            module: 模块名
            record_id: 记录ID
            soft_delete: 是否软删除
            sync: 是否同步
            
        Returns:
            是否成功
        """
        table_name = self.get_table_name(module)
        if self.multitenant_enabled:
            existing = await self.load_data(module, record_id)
            if not existing:
                return False
        
        # 从持久化层删除
        success = self.persistence.delete(
            table_name=table_name,
            record_id=record_id,
            soft_delete=soft_delete,
        )
        
        # 添加到同步队列
        if success and sync:
            await self.sync_manager.sync(
                table_name=table_name,
                record_id=record_id,
                operation="delete",
                direction=SyncDirection.BIDIRECTIONAL,
            )
        
        return success
    
    async def count_data(
        self,
        module: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        统计数据数量
        
        Args:
            module: 模块名
            filters: 过滤条件
            
        Returns:
            数量
        """
        table_name = self.get_table_name(module)
        effective_filters = dict(filters or {})
        if self.multitenant_enabled:
            effective_filters["_tenant_id"] = get_current_tenant_id()
        return self.persistence.count(table_name, effective_filters)
    
    async def batch_save(
        self,
        module: str,
        data_list: List[Dict[str, Any]],
        sync: bool = True,
    ) -> List[str]:
        """
        批量保存数据
        
        Args:
            module: 模块名
            data_list: 数据列表
            sync: 是否同步
            
        Returns:
            记录ID列表
        """
        record_ids = []
        for data in data_list:
            record_id = await self.save_data(
                module=module,
                data=data,
                sync=sync,
            )
            record_ids.append(record_id)
        return record_ids
    
    async def batch_delete(
        self,
        module: str,
        record_ids: List[str],
        soft_delete: bool = True,
        sync: bool = True,
    ) -> int:
        """
        批量删除数据
        
        Args:
            module: 模块名
            record_ids: 记录ID列表
            soft_delete: 是否软删除
            sync: 是否同步
            
        Returns:
            成功删除的数量
        """
        success_count = 0
        for record_id in record_ids:
            if await self.delete_data(
                module=module,
                record_id=record_id,
                soft_delete=soft_delete,
                sync=sync,
            ):
                success_count += 1
        return success_count


# 全局数据服务实例
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """获取全局数据服务实例（单例）"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service

