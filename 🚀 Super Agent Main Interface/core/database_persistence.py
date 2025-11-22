#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库持久化层
P0-003: 实现统一的数据库持久化层，替换所有模拟数据
"""

import asyncio
import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import uuid4
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DataStatus(str, Enum):
    """数据状态"""
    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"


@dataclass
class PersistenceRecord:
    """持久化记录"""
    id: str
    table_name: str
    data: Dict[str, Any]
    status: DataStatus = DataStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class DatabasePersistence:
    """
    数据库持久化层
    
    功能：
    - 统一的数据库操作接口
    - 支持多表管理
    - 自动创建表结构
    - 数据同步支持
    - 事务支持
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        enable_sync: bool = True,
    ):
        # 数据库路径
        env_path = os.getenv("PERSISTENCE_DB_PATH")
        if db_path is None:
            if env_path:
                db_path = Path(env_path)
            else:
                project_root = Path(__file__).resolve().parents[2]
                db_path = project_root / "artifacts" / "data" / "persistence.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 同步标志
        self.enable_sync = enable_sync
        self._sync_queue: List[Dict[str, Any]] = []
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # 创建通用数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persistence_data (
                    id TEXT PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,
                    created_at_index DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_table_name 
                ON persistence_data(table_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON persistence_data(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON persistence_data(created_at_index)
            """)
            
            # 创建同步队列表
            if self.enable_sync:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id TEXT PRIMARY KEY,
                        table_name TEXT NOT NULL,
                        operation TEXT NOT NULL,
                        record_id TEXT NOT NULL,
                        data TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        processed_at TEXT,
                        retry_count INTEGER DEFAULT 0,
                        error_message TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sync_status 
                    ON sync_queue(status)
                """)
            
            conn.commit()
            conn.close()
            logger.info(f"数据库持久化层已初始化: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
    
    def save(
        self,
        table_name: str,
        data: Dict[str, Any],
        record_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        保存数据
        
        Args:
            table_name: 表名
            data: 数据字典
            record_id: 记录ID（可选，不提供则自动生成）
            metadata: 元数据
            
        Returns:
            记录ID
        """
        if record_id is None:
            record_id = f"{table_name}_{uuid4()}"
        
        record = PersistenceRecord(
            id=record_id,
            table_name=table_name,
            data=data,
            status=DataStatus.ACTIVE,
            metadata=metadata or {},
        )
        
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                # 检查是否存在
                cursor.execute("""
                    SELECT id FROM persistence_data 
                    WHERE id = ? AND table_name = ?
                """, (record_id, table_name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新
                    cursor.execute("""
                        UPDATE persistence_data 
                        SET data = ?, updated_at = ?, metadata = ?
                        WHERE id = ? AND table_name = ?
                    """, (
                        json.dumps(data, ensure_ascii=False),
                        record.updated_at,
                        json.dumps(metadata or {}, ensure_ascii=False),
                        record_id,
                        table_name,
                    ))
                else:
                    # 插入
                    cursor.execute("""
                        INSERT INTO persistence_data 
                        (id, table_name, data, status, created_at, updated_at, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.id,
                        record.table_name,
                        json.dumps(record.data, ensure_ascii=False),
                        record.status.value,
                        record.created_at,
                        record.updated_at,
                        json.dumps(record.metadata, ensure_ascii=False),
                    ))
                
                conn.commit()
                conn.close()
                
                # 添加到同步队列
                if self.enable_sync:
                    self._add_to_sync_queue(table_name, "save", record_id, data)
                
                logger.debug(f"数据已保存: {table_name}/{record_id}")
                return record_id
        except Exception as e:
            logger.error(f"保存数据失败: {e}", exc_info=True)
            raise
    
    def load(
        self,
        table_name: str,
        record_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        加载数据
        
        Args:
            table_name: 表名
            record_id: 记录ID
            
        Returns:
            数据字典或None
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT data, metadata FROM persistence_data
                    WHERE id = ? AND table_name = ? AND status = ?
                """, (record_id, table_name, DataStatus.ACTIVE.value))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    data = json.loads(row[0])
                    metadata = json.loads(row[1]) if row[1] else {}
                    return {**data, "_metadata": metadata, "_id": record_id}
        except Exception as e:
            logger.error(f"加载数据失败: {e}", exc_info=True)
        
        return None
    
    def query(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_desc: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            table_name: 表名
            filters: 过滤条件（字典，支持嵌套字段）
            limit: 返回数量限制
            offset: 偏移量
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            数据列表
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                # 构建查询
                query = "SELECT id, data, metadata, created_at, updated_at FROM persistence_data WHERE table_name = ? AND status = ?"
                params = [table_name, DataStatus.ACTIVE.value]
                
                # 应用过滤条件
                if filters:
                    for key, value in filters.items():
                        # 简单过滤（在JSON数据中搜索）
                        query += f" AND data LIKE ?"
                        params.append(f'%"{key}":{json.dumps(value)}%')
                
                # 排序
                if order_by:
                    query += f" ORDER BY {order_by} {'DESC' if order_desc else 'ASC'}"
                else:
                    query += " ORDER BY created_at_index DESC"
                
                # 限制
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    record_id, data_str, metadata_str, created_at, updated_at = row
                    data = json.loads(data_str)
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    results.append({
                        **data,
                        "_id": record_id,
                        "_metadata": metadata,
                        "_created_at": created_at,
                        "_updated_at": updated_at,
                    })
                
                return results
        except Exception as e:
            logger.error(f"查询数据失败: {e}", exc_info=True)
            return []
    
    def delete(
        self,
        table_name: str,
        record_id: str,
        soft_delete: bool = True,
    ) -> bool:
        """
        删除数据
        
        Args:
            table_name: 表名
            record_id: 记录ID
            soft_delete: 是否软删除（标记为deleted）
            
        Returns:
            是否成功
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                if soft_delete:
                    # 软删除
                    cursor.execute("""
                        UPDATE persistence_data 
                        SET status = ?, updated_at = ?
                        WHERE id = ? AND table_name = ?
                    """, (
                        DataStatus.DELETED.value,
                        datetime.utcnow().isoformat() + "Z",
                        record_id,
                        table_name,
                    ))
                else:
                    # 硬删除
                    cursor.execute("""
                        DELETE FROM persistence_data 
                        WHERE id = ? AND table_name = ?
                    """, (record_id, table_name))
                
                conn.commit()
                conn.close()
                
                # 添加到同步队列
                if self.enable_sync:
                    self._add_to_sync_queue(table_name, "delete", record_id, None)
                
                logger.debug(f"数据已删除: {table_name}/{record_id}")
                return True
        except Exception as e:
            logger.error(f"删除数据失败: {e}", exc_info=True)
            return False
    
    def count(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        统计数据数量
        
        Args:
            table_name: 表名
            filters: 过滤条件
            
        Returns:
            数量
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                query = "SELECT COUNT(*) FROM persistence_data WHERE table_name = ? AND status = ?"
                params = [table_name, DataStatus.ACTIVE.value]
                
                if filters:
                    for key, value in filters.items():
                        query += f" AND data LIKE ?"
                        params.append(f'%"{key}":{json.dumps(value)}%')
                
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                conn.close()
                
                return count
        except Exception as e:
            logger.error(f"统计数据失败: {e}", exc_info=True)
            return 0
    
    def _add_to_sync_queue(
        self,
        table_name: str,
        operation: str,
        record_id: str,
        data: Optional[Dict[str, Any]],
    ):
        """添加到同步队列"""
        try:
            sync_id = f"sync_{uuid4()}"
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sync_queue 
                    (id, table_name, operation, record_id, data, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sync_id,
                    table_name,
                    operation,
                    record_id,
                    json.dumps(data, ensure_ascii=False) if data else None,
                    "pending",
                    datetime.utcnow().isoformat() + "Z",
                ))
                
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"添加到同步队列失败: {e}", exc_info=True)
    
    def get_sync_queue(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取同步队列"""
        if not self.enable_sync:
            return []
        
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                query = "SELECT * FROM sync_queue WHERE 1=1"
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = []
                for row in rows:
                    result = dict(zip(columns, row))
                    if result.get("data"):
                        result["data"] = json.loads(result["data"])
                    results.append(result)
                
                return results
        except Exception as e:
            logger.error(f"获取同步队列失败: {e}", exc_info=True)
            return []
    
    def clear_sync_queue(self, status: str = "processed") -> int:
        """清理同步队列"""
        if not self.enable_sync:
            return 0
        
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM sync_queue WHERE status = ?
                """, (status,))
                
                count = cursor.rowcount
                conn.commit()
                conn.close()
                
                return count
        except Exception as e:
            logger.error(f"清理同步队列失败: {e}", exc_info=True)
            return 0


# 全局持久化实例
_persistence: Optional[DatabasePersistence] = None


def get_persistence() -> DatabasePersistence:
    """获取全局持久化实例（单例）"""
    global _persistence
    if _persistence is None:
        _persistence = DatabasePersistence()
    return _persistence

