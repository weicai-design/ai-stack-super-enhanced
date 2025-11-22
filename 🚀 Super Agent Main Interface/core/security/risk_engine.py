#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全风控引擎
P0-004: 风控规则、异常检测、统计与落库
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..database_persistence import DatabasePersistence, get_persistence

logger = logging.getLogger(__name__)


class SecurityRiskEngine:
    """简单的风控引擎，监控高风险行为"""

    def __init__(self, persistence: Optional[DatabasePersistence] = None):
        self.persistence = persistence or get_persistence()
        self.table_name = "security_risk_events"
        self._lock = threading.Lock()
        self._http_error_cache: Dict[str, List[datetime]] = {}
        self._command_block_cache: Dict[str, List[datetime]] = {}

    # -------- 记录事件 --------

    def observe_http_request(self, actor: str, status_code: int, path: str, duration_ms: float) -> None:
        if not actor:
            actor = "anonymous"
        is_error = status_code >= 500
        now = datetime.utcnow()
        with self._lock:
            entries = self._http_error_cache.setdefault(actor, [])
            if is_error:
                entries.append(now)
                self._http_error_cache[actor] = [t for t in entries if t > now - timedelta(minutes=5)]
                if len(self._http_error_cache[actor]) >= 5:
                    self._record_event(
                        event_type="http_error_burst",
                        severity="warning",
                        description=f"{actor} 5分钟内出现 {len(entries)} 次服务器错误",
                        metadata={"actor": actor, "path": path, "status": status_code},
                    )
            else:
                # 清理缓存
                self._http_error_cache[actor] = [t for t in entries if t > now - timedelta(minutes=5)]

        if duration_ms > 10_000:
            self._record_event(
                event_type="http_slow_request",
                severity="info",
                description=f"接口响应超时 {duration_ms:.0f}ms",
                metadata={"actor": actor, "path": path, "duration_ms": duration_ms},
            )

    def record_violation(self, violation: Dict[str, Any]) -> None:
        severity = violation.get("severity", "medium")
        self._record_event(
            event_type=f"violation.{violation.get('violation_type', 'unknown')}",
            severity=severity,
            description=violation.get("description", ""),
            metadata=violation,
        )

    def record_command_event(self, user_id: str, success: bool, command: str) -> None:
        now = datetime.utcnow()
        if success:
            return
        with self._lock:
            entries = self._command_block_cache.setdefault(user_id or "anonymous", [])
            entries.append(now)
            self._command_block_cache[user_id or "anonymous"] = [t for t in entries if t > now - timedelta(minutes=10)]
            if len(self._command_block_cache[user_id or "anonymous"]) >= 3:
                self._record_event(
                    event_type="command_block_spike",
                    severity="high",
                    description=f"{user_id or 'anonymous'} 连续触发命令拦截",
                    metadata={"user_id": user_id, "command": command},
                )

    # -------- 查询 --------

    def get_summary(self) -> Dict[str, Any]:
        total = self.persistence.count(self.table_name)
        last_24h = self.persistence.query(
            table_name=self.table_name,
            limit=500,
            filters=None,
            order_by="_created_at",
            order_desc=True,
        )
        return {
            "total_events": total,
            "recent_events": len(last_24h),
            "distribution": self._aggregate(last_24h),
        }

    def list_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        events = self.persistence.query(
            table_name=self.table_name,
            limit=limit,
            order_by="_created_at",
            order_desc=True,
        )
        return [{k: v for k, v in event.items() if not k.startswith("_")} for event in events]

    # -------- 内部 --------

    def _record_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            record_id = f"risk_{uuid4()}"
            self.persistence.save(
                table_name=self.table_name,
                record_id=record_id,
                data={
                    "event_id": record_id,
                    "event_type": event_type,
                    "severity": severity,
                    "description": description,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "metadata": metadata or {},
                },
                metadata={"event_type": event_type, "severity": severity},
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("记录风控事件失败: %s", exc)

    @staticmethod
    def _aggregate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        distribution: Dict[str, int] = {}
        severity: Dict[str, int] = {}
        for event in events:
            etype = event.get("event_type", "unknown")
            sev = event.get("severity", "info")
            distribution[etype] = distribution.get(etype, 0) + 1
            severity[sev] = severity.get(sev, 0) + 1
        return {"by_type": distribution, "by_severity": severity}


_risk_engine: Optional[SecurityRiskEngine] = None


def get_risk_engine() -> SecurityRiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = SecurityRiskEngine()
    return _risk_engine


