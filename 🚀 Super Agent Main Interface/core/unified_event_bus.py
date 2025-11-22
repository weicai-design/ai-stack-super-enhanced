#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一事件流（Event Bus）
P0-001: 实现统一的事件发布/订阅系统，支持异步、持久化、过滤、路由
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4
import threading

logger = logging.getLogger(__name__)


class EventCategory(str, Enum):
    """事件类别"""
    TASK = "task"
    EXECUTION = "execution"
    CHECK = "check"
    FEEDBACK = "feedback"
    RESOURCE = "resource"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    CUSTOM = "custom"


class EventSeverity(str, Enum):
    """事件严重程度"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class UnifiedEvent:
    """统一事件实体"""
    event_id: str
    category: EventCategory
    event_type: str
    source: str
    severity: EventSeverity
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EventFilter:
    """事件过滤器"""
    
    def __init__(
        self,
        category: Optional[EventCategory] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        severity: Optional[EventSeverity] = None,
        min_severity: Optional[EventSeverity] = None,
    ):
        self.category = category
        self.event_type = event_type
        self.source = source
        self.severity = severity
        self.min_severity = min_severity
    
    def matches(self, event: UnifiedEvent) -> bool:
        """检查事件是否匹配过滤器"""
        if self.category and event.category != self.category:
            return False
        if self.event_type and event.event_type != self.event_type:
            return False
        if self.source and event.source != self.source:
            return False
        if self.severity and event.severity != self.severity:
            return False
        if self.min_severity:
            severity_order = {
                EventSeverity.DEBUG: 0,
                EventSeverity.INFO: 1,
                EventSeverity.WARNING: 2,
                EventSeverity.ERROR: 3,
                EventSeverity.CRITICAL: 4,
            }
            if severity_order.get(event.severity, 0) < severity_order.get(self.min_severity, 0):
                return False
        return True


class UnifiedEventBus:
    """
    统一事件总线
    
    特性：
    - 异步发布/订阅
    - 事件持久化
    - 事件过滤和路由
    - 事件关联追踪
    - 线程安全
    - 事件统计和查询
    """
    
    def __init__(
        self,
        max_events: int = 10000,
        persist_events: bool = True,
        persist_path: Optional[Path] = None,
    ):
        self.max_events = max_events
        self.persist_events = persist_events
        
        # 事件存储
        self._events: List[UnifiedEvent] = []
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()
        
        # 订阅者（支持过滤）
        self._subscribers: List[Dict[str, Any]] = []
        
        # 持久化
        if persist_path is None:
            project_root = Path(__file__).resolve().parents[2]
            persist_path = project_root / "artifacts" / "evidence" / "unified_events.jsonl"
        self.persist_path = Path(persist_path)
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 统计
        self._stats = {
            "total_published": 0,
            "total_delivered": 0,
            "by_category": {},
            "by_severity": {},
            "by_source": {},
        }
    
    async def publish(
        self,
        category: EventCategory,
        event_type: str,
        source: str,
        severity: EventSeverity = EventSeverity.INFO,
        payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        parent_event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedEvent:
        """
        发布事件
        
        Args:
            category: 事件类别
            event_type: 事件类型
            source: 事件源
            severity: 严重程度
            payload: 事件负载
            correlation_id: 关联ID（用于追踪相关事件）
            parent_event_id: 父事件ID
            metadata: 元数据
            
        Returns:
            发布的事件
        """
        event = UnifiedEvent(
            event_id=f"ue_{uuid4()}",
            category=category,
            event_type=event_type,
            source=source,
            severity=severity,
            payload=payload or {},
            correlation_id=correlation_id,
            parent_event_id=parent_event_id,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]
            
            # 更新统计
            self._stats["total_published"] += 1
            self._stats["by_category"][category.value] = self._stats["by_category"].get(category.value, 0) + 1
            self._stats["by_severity"][severity.value] = self._stats["by_severity"].get(severity.value, 0) + 1
            self._stats["by_source"][source] = self._stats["by_source"].get(source, 0) + 1
        
        # 持久化
        if self.persist_events:
            await self._persist_event(event)
        
        # 通知订阅者
        await self._notify_subscribers(event)
        
        logger.debug(f"事件已发布: {event.event_id} ({category.value}/{event_type})")
        
        return event
    
    async def _persist_event(self, event: UnifiedEvent):
        """持久化事件到文件"""
        try:
            with self._thread_lock:
                with open(self.persist_path, "a", encoding="utf-8") as f:
                    f.write(event.to_json() + "\n")
        except Exception as e:
            logger.error(f"事件持久化失败: {e}")
    
    async def _notify_subscribers(self, event: UnifiedEvent):
        """通知订阅者"""
        for subscriber_info in self._subscribers:
            callback = subscriber_info["callback"]
            event_filter = subscriber_info.get("filter")
            
            # 应用过滤器
            if event_filter and not event_filter.matches(event):
                continue
            
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
                self._stats["total_delivered"] += 1
            except Exception as e:
                logger.error(f"订阅者处理事件失败: {e}", exc_info=True)
    
    def subscribe(
        self,
        callback: Callable[[UnifiedEvent], Awaitable[None] | None],
        event_filter: Optional[EventFilter] = None,
        subscriber_id: Optional[str] = None,
    ) -> str:
        """
        订阅事件
        
        Args:
            callback: 回调函数
            event_filter: 事件过滤器（可选）
            subscriber_id: 订阅者ID（可选）
            
        Returns:
            订阅者ID
        """
        if subscriber_id is None:
            subscriber_id = f"sub_{uuid4()}"
        
        self._subscribers.append({
            "subscriber_id": subscriber_id,
            "callback": callback,
            "filter": event_filter,
        })
        
        logger.debug(f"订阅者已注册: {subscriber_id}")
        
        return subscriber_id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """取消订阅"""
        original_count = len(self._subscribers)
        self._subscribers = [
            s for s in self._subscribers
            if s["subscriber_id"] != subscriber_id
        ]
        removed = len(self._subscribers) < original_count
        if removed:
            logger.debug(f"订阅者已取消: {subscriber_id}")
        return removed
    
    def get_events(
        self,
        limit: int = 100,
        category: Optional[EventCategory] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        severity: Optional[EventSeverity] = None,
        correlation_id: Optional[str] = None,
    ) -> List[UnifiedEvent]:
        """
        查询事件
        
        Args:
            limit: 返回数量限制
            category: 事件类别过滤
            event_type: 事件类型过滤
            source: 事件源过滤
            severity: 严重程度过滤
            correlation_id: 关联ID过滤
            
        Returns:
            事件列表
        """
        events = self._events
        
        # 应用过滤器
        if category:
            events = [e for e in events if e.category == category]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        if severity:
            events = [e for e in events if e.severity == severity]
        if correlation_id:
            events = [e for e in events if e.correlation_id == correlation_id]
        
        # 返回最近的
        return list(reversed(events[-limit:]))
    
    def get_event_by_id(self, event_id: str) -> Optional[UnifiedEvent]:
        """根据ID获取事件"""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None
    
    def get_related_events(self, event_id: str) -> List[UnifiedEvent]:
        """获取相关事件（通过correlation_id或parent_event_id）"""
        event = self.get_event_by_id(event_id)
        if not event:
            return []
        
        related = []
        correlation_id = event.correlation_id or event.event_id
        
        for e in self._events:
            if (e.correlation_id == correlation_id or 
                e.parent_event_id == event_id or
                e.event_id == event.parent_event_id):
                related.append(e)
        
        return related
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "current_events": len(self._events),
            "subscribers": len(self._subscribers),
        }
    
    def clear_events(self, keep_recent: int = 1000):
        """清理旧事件（保留最近的）"""
        async def _clear():
            async with self._lock:
                if len(self._events) > keep_recent:
                    self._events = self._events[-keep_recent:]
        
        asyncio.create_task(_clear())


# 全局事件总线实例
_unified_event_bus: Optional[UnifiedEventBus] = None


def get_unified_event_bus() -> UnifiedEventBus:
    """获取全局事件总线实例（单例）"""
    global _unified_event_bus
    if _unified_event_bus is None:
        _unified_event_bus = UnifiedEventBus()
    return _unified_event_bus

