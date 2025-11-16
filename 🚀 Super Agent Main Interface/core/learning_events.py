"""
学习事件总线
负责在智能任务 / 自我学习 / 资源管理之间传递事件
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4


class LearningEventType(str, Enum):
    """统一的事件类型"""

    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_BLOCKED = "task_blocked"
    RESOURCE_ALERT = "resource_alert"
    WORKFLOW_ANOMALY = "workflow_anomaly"
    PERFORMANCE = "performance"
    TERMINAL_ALERT = "terminal_alert"
    MEMO_EXTRACTED = "memo_extracted"
    RAG_ALERT = "rag_alert"
    CUSTOM = "custom"


@dataclass
class LearningEvent:
    """事件实体"""

    event_id: str
    event_type: LearningEventType
    source: str
    severity: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LearningEventBus:
    """
    轻量级事件总线

    - 支持发布/订阅
    - 内置最大事件缓存，便于查询
    - 异步安全，适配FastAPI
    """

    def __init__(self, max_events: int = 500):
        self.max_events = max_events
        self._events: List[LearningEvent] = []
        self._subscribers: List[Callable[[LearningEvent], Awaitable[None] | None]] = []
        self._lock = asyncio.Lock()

    async def publish_event(
        self,
        event_type: LearningEventType,
        source: str,
        severity: str = "info",
        payload: Optional[Dict[str, Any]] = None,
    ) -> LearningEvent:
        """发布事件并通知订阅者"""
        async with self._lock:
            event = LearningEvent(
                event_id=f"lge_{uuid4()}",
                event_type=event_type,
                source=source,
                severity=severity,
                payload=payload or {},
            )
            self._events.append(event)
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events :]

        await self._notify_subscribers(event)
        return event

    async def _notify_subscribers(self, event: LearningEvent):
        """异步通知订阅者，防止阻塞"""
        for callback in self._subscribers:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                # 避免订阅者异常影响主流程
                print(f"[LearningEventBus] subscriber error: {exc}")

    def subscribe(self, callback: Callable[[LearningEvent], Awaitable[None] | None]):
        """注册订阅者"""
        self._subscribers.append(callback)

    def get_recent_events(
        self, limit: int = 50, event_type: Optional[LearningEventType] = None
    ) -> List[LearningEvent]:
        """获取最近事件"""
        events = (
            [event for event in self._events if event.event_type == event_type]
            if event_type
            else self._events
        )
        return list(reversed(events[-limit:]))

    def get_statistics(self) -> Dict[str, Any]:
        """事件概览"""
        stats: Dict[str, int] = {}
        for event in self._events:
            stats[event.event_type.value] = stats.get(event.event_type.value, 0) + 1

        return {
            "total": len(self._events),
            "by_type": stats,
            "last_event": self._events[-1].__dict__ if self._events else None,
        }





