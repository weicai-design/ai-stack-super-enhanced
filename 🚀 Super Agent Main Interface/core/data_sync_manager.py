#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步管理器
P0-003: 实现前后端数据同步机制，确保数据一致性
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4

from .database_persistence import DatabasePersistence, get_persistence
from .unified_event_bus import UnifiedEventBus, EventCategory, EventSeverity, get_unified_event_bus

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """同步状态"""
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SyncDirection(str, Enum):
    """同步方向"""
    FRONTEND_TO_BACKEND = "frontend_to_backend"
    BACKEND_TO_FRONTEND = "backend_to_frontend"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncTask:
    """同步任务"""
    sync_id: str
    table_name: str
    record_id: str
    operation: str  # save/delete/update
    direction: SyncDirection
    status: SyncStatus = SyncStatus.PENDING
    data: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    synced_at: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sync_id": self.sync_id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "operation": self.operation,
            "direction": self.direction.value,
            "status": self.status.value,
            "data": self.data,
            "created_at": self.created_at,
            "synced_at": self.synced_at,
            "error": self.error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


class DataSyncManager:
    """
    数据同步管理器
    
    功能：
    - 前后端数据同步
    - 冲突检测和解决
    - 同步队列管理
    - 同步状态追踪
    - 自动重试机制
    """
    
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        event_bus: Optional[UnifiedEventBus] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.persistence = persistence or get_persistence()
        self.event_bus = event_bus or get_unified_event_bus()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 同步任务队列
        self._sync_queue: List[SyncTask] = []
        self._sync_lock = asyncio.Lock()
        
        # 同步处理器（可扩展）
        self._sync_handlers: Dict[str, Callable[[SyncTask], Awaitable[bool]]] = {}
        
        # 统计
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "pending_syncs": 0,
        }
        
        # 启动同步处理器
        self._sync_processor_task = None
    
    async def start(self):
        """启动同步管理器"""
        if self._sync_processor_task is None:
            self._sync_processor_task = asyncio.create_task(self._sync_processor())
            logger.info("数据同步管理器已启动")
    
    async def stop(self):
        """停止同步管理器"""
        if self._sync_processor_task:
            self._sync_processor_task.cancel()
            try:
                await self._sync_processor_task
            except asyncio.CancelledError:
                pass
            self._sync_processor_task = None
            logger.info("数据同步管理器已停止")
    
    async def sync(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加同步任务
        
        Args:
            table_name: 表名
            record_id: 记录ID
            operation: 操作类型（save/delete/update）
            direction: 同步方向
            data: 数据（可选）
            metadata: 元数据（可选）
            
        Returns:
            同步任务ID
        """
        sync_id = f"sync_{uuid4()}"
        
        task = SyncTask(
            sync_id=sync_id,
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            direction=direction,
            data=data,
            metadata=metadata or {},
        )
        
        async with self._sync_lock:
            self._sync_queue.append(task)
            self.stats["total_syncs"] += 1
            self.stats["pending_syncs"] += 1
        
        # 发布同步事件
        await self.event_bus.publish(
            category=EventCategory.SYSTEM,
            event_type="sync_task_created",
            source="data_sync_manager",
            severity=EventSeverity.INFO,
            payload={
                "sync_id": sync_id,
                "table_name": table_name,
                "record_id": record_id,
                "operation": operation,
            },
        )
        
        logger.debug(f"同步任务已创建: {sync_id} ({table_name}/{record_id})")
        
        return sync_id
    
    async def _sync_processor(self):
        """同步处理器（后台任务）"""
        while True:
            try:
                await asyncio.sleep(0.5)  # 每0.5秒处理一次
                
                async with self._sync_lock:
                    if not self._sync_queue:
                        continue
                    
                    # 获取待处理的任务
                    pending_tasks = [
                        task for task in self._sync_queue
                        if task.status == SyncStatus.PENDING
                    ]
                    
                    if not pending_tasks:
                        continue
                    
                    # 处理第一个待处理任务
                    task = pending_tasks[0]
                    task.status = SyncStatus.SYNCING
                
                # 执行同步
                success = await self._execute_sync(task)
                
                async with self._sync_lock:
                    if success:
                        task.status = SyncStatus.SUCCESS
                        task.synced_at = datetime.utcnow().isoformat() + "Z"
                        self.stats["successful_syncs"] += 1
                        self.stats["pending_syncs"] -= 1
                        # 从队列移除
                        self._sync_queue = [t for t in self._sync_queue if t.sync_id != task.sync_id]
                    else:
                        task.retry_count += 1
                        if task.retry_count >= self.max_retries:
                            task.status = SyncStatus.FAILED
                            self.stats["failed_syncs"] += 1
                            self.stats["pending_syncs"] -= 1
                            # 从队列移除
                            self._sync_queue = [t for t in self._sync_queue if t.sync_id != task.sync_id]
                        else:
                            task.status = SyncStatus.PENDING
                            # 等待重试
                            await asyncio.sleep(self.retry_delay * task.retry_count)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"同步处理器错误: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _execute_sync(self, task: SyncTask) -> bool:
        """执行同步任务"""
        try:
            # 检查是否有自定义处理器
            handler_key = f"{task.table_name}_{task.operation}"
            if handler_key in self._sync_handlers:
                handler = self._sync_handlers[handler_key]
                return await handler(task)
            
            # 默认同步逻辑
            if task.operation == "save":
                # 保存到持久化层
                self.persistence.save(
                    table_name=task.table_name,
                    record_id=task.record_id,
                    data=task.data or {},
                    metadata=task.metadata,
                )
                return True
            elif task.operation == "delete":
                # 从持久化层删除
                self.persistence.delete(
                    table_name=task.table_name,
                    record_id=task.record_id,
                )
                return True
            elif task.operation == "update":
                # 更新持久化层
                if task.data:
                    self.persistence.save(
                        table_name=task.table_name,
                        record_id=task.record_id,
                        data=task.data,
                        metadata=task.metadata,
                    )
                return True
            else:
                logger.warning(f"未知的同步操作: {task.operation}")
                return False
                
        except Exception as e:
            logger.error(f"执行同步失败: {e}", exc_info=True)
            task.error = str(e)
            return False
    
    def register_sync_handler(
        self,
        table_name: str,
        operation: str,
        handler: Callable[[SyncTask], Awaitable[bool]],
    ):
        """
        注册同步处理器
        
        Args:
            table_name: 表名
            operation: 操作类型
            handler: 处理器函数
        """
        handler_key = f"{table_name}_{operation}"
        self._sync_handlers[handler_key] = handler
        logger.debug(f"同步处理器已注册: {handler_key}")
    
    def get_sync_status(self, sync_id: str) -> Optional[SyncTask]:
        """获取同步任务状态"""
        async def _get():
            async with self._sync_lock:
                for task in self._sync_queue:
                    if task.sync_id == sync_id:
                        return task
        return asyncio.run(_get())
    
    def get_pending_syncs(self, limit: int = 100) -> List[SyncTask]:
        """获取待处理的同步任务"""
        async def _get():
            async with self._sync_lock:
                pending = [
                    task for task in self._sync_queue
                    if task.status == SyncStatus.PENDING
                ]
                return pending[:limit]
        return asyncio.run(_get())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        async def _get():
            async with self._sync_lock:
                return {
                    **self.stats,
                    "queue_size": len(self._sync_queue),
                    "handlers_count": len(self._sync_handlers),
                }
        return asyncio.run(_get())


# 全局同步管理器实例
_sync_manager: Optional[DataSyncManager] = None
_sync_manager_task: Optional[asyncio.Task] = None
_sync_manager_thread: Optional[threading.Thread] = None


def _ensure_sync_manager_running():
    """保证同步管理器在当前环境中运行"""
    global _sync_manager_task, _sync_manager_thread
    if _sync_manager is None:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        if _sync_manager_task is None or _sync_manager_task.done():
            _sync_manager_task = loop.create_task(_sync_manager.start())
    else:
        # 在无事件循环的环境（如同步测试）中，启动后台线程
        if _sync_manager_thread is None or not _sync_manager_thread.is_alive():
            def _runner():
                thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(thread_loop)
                thread_loop.run_until_complete(_sync_manager.start())

            _sync_manager_thread = threading.Thread(
                target=_runner,
                name="data-sync-manager",
                daemon=True,
            )
            _sync_manager_thread.start()


def get_sync_manager() -> DataSyncManager:
    """获取全局同步管理器实例（单例）"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = DataSyncManager()
    _ensure_sync_manager_running()
    return _sync_manager

