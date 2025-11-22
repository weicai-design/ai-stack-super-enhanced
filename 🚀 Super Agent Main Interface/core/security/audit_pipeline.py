#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全审计管道
P0-004: 统一审计日志（文件 + 数据库 + 事件总线）
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..database_persistence import DatabasePersistence, get_persistence
from ..unified_event_bus import EventCategory, EventSeverity, UnifiedEventBus, get_unified_event_bus
from .audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)


@dataclass
class AuditRecord:
    record_id: str
    event_type: str
    source: str
    severity: str
    status: str
    timestamp: str
    request_path: Optional[str] = None
    method: Optional[str] = None
    ip: Optional[str] = None
    actor: Optional[str] = None
    metadata: Dict[str, Any] | None = None


class SecurityAuditPipeline:
    """统一的安全审计管道"""

    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        audit_logger: Optional[AuditLogger] = None,
        event_bus: Optional[UnifiedEventBus] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.audit_logger = audit_logger or get_audit_logger()
        self.event_bus = event_bus or get_unified_event_bus()
        self.table_name = "security_audit"
        self.http_table = "security_http_audit"
        self.task_table = "security_task_audit"
        self.command_table = "security_command_audit"

    # -------- 写入 --------

    def log_http_request(
        self,
        request,
        response_status: int,
        duration_ms: float,
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        client_ip = request.client.host if request.client else None
        actor_id = actor or request.headers.get("x-user-id") or "anonymous"
        record = AuditRecord(
            record_id=str(uuid4()),
            event_type="http_request",
            source="security_middleware",
            severity="info" if response_status < 400 else "warning",
            status="success" if response_status < 400 else "failed",
            timestamp=datetime.utcnow().isoformat() + "Z",
            request_path=request.url.path,
            method=request.method,
            ip=client_ip,
            actor=actor_id,
            metadata={
                "status_code": response_status,
                "duration_ms": duration_ms,
                **(metadata or {}),
            },
        )

        # 文件审计
        if self.audit_logger:
            try:
                self.audit_logger.log_http_request(
                    request=request,
                    response_status=response_status,
                    duration_ms=duration_ms,
                    metadata=metadata or {"status_code": response_status},
                )
            except Exception as exc:  # pragma: no cover - 审计失败不中断
                logger.warning("写入文件审计失败: %s", exc)

        # 持久化
        self._persist_record(record, table_name=self.http_table)
        self._publish_event(record)
        return record

    def log_security_event(
        self,
        event_type: str,
        source: str,
        severity: str = "info",
        status: str = "success",
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            record_id=str(uuid4()),
            event_type=event_type,
            source=source,
            severity=severity,
            status=status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            actor=actor,
            metadata=metadata or {},
        )
        self._persist_record(record)
        self._publish_event(record)
        return record

    # -------- 查询 --------

    def query_records(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {}
        if event_type:
            filters["event_type"] = event_type
        if severity:
            filters["severity"] = severity

        records = self.persistence.query(
            table_name=self.table_name,
            filters=filters or None,
            limit=limit,
            order_by="_created_at",
            order_desc=True,
        )
        return [
            {k: v for k, v in record.items() if not k.startswith("_")}
            for record in records
        ]

    def get_statistics(self) -> Dict[str, Any]:
        total = self.persistence.count(self.table_name)
        recent = self.persistence.query(
            table_name=self.table_name,
            limit=500,
            order_by="_created_at",
            order_desc=True,
        )

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        failure = 0

        for item in recent:
            etype = item.get("event_type", "unknown")
            sev = item.get("severity", "info")
            by_type[etype] = by_type.get(etype, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
            if item.get("status") == "failed":
                failure += 1

        return {
            "total": total,
            "recent": len(recent),
            "distribution_by_type": by_type,
            "distribution_by_severity": by_severity,
            "failure_rate": (failure / len(recent) * 100) if recent else 0,
        }

    # -------- 内部 --------

    def log_task_event(
        self,
        task_id: str,
        actor: str,
        module: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        data = {
            "task_id": task_id,
            "actor": actor,
            "module": module,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {},
        }
        return self.persistence.save(
            table_name=self.task_table,
            data=data,
            record_id=f"{self.task_table}_{uuid4()}",
            metadata={"status": status, "module": module},
        )

    def log_command_event(
        self,
        command: str,
        actor: str,
        severity: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        data = {
            "command": command,
            "actor": actor,
            "severity": severity,
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {},
        }
        return self.persistence.save(
            table_name=self.command_table,
            data=data,
            record_id=f"{self.command_table}_{uuid4()}",
            metadata={"severity": severity, "success": success},
        )

    def query_table(self, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self.persistence.query(
            table_name=table_name,
            limit=limit,
            order_by="_created_at",
            order_desc=True,
        )
        return [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]

    def get_http_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.query_table(self.http_table, limit)

    def get_task_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.query_table(self.task_table, limit)

    def get_command_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.query_table(self.command_table, limit)

    def _persist_record(self, record: AuditRecord, table_name: Optional[str] = None) -> None:
        try:
            self.persistence.save(
                table_name=table_name or self.table_name,
                record_id=record.record_id,
                data=asdict(record),
                metadata={"event_type": record.event_type},
            )
        except Exception as exc:  # pragma: no cover
            logger.error("审计记录持久化失败: %s", exc)

    def _publish_event(self, record: AuditRecord) -> None:
        try:
            payload = asdict(record)
            coroutine = self.event_bus.publish(
                category=EventCategory.SYSTEM,
                event_type=f"audit.{record.event_type}",
                source=record.source,
                severity=EventSeverity(record.severity if record.severity in EventSeverity._value2member_map_ else "info"),
                payload=payload,
                correlation_id=record.record_id,
            )
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(coroutine)
            else:
                loop.run_until_complete(coroutine)
        except RuntimeError:
            asyncio.run(coroutine)
        except Exception as exc:  # pragma: no cover
            logger.debug("审计事件发布失败: %s", exc)


_pipeline: Optional[SecurityAuditPipeline] = None


def get_audit_pipeline() -> SecurityAuditPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = SecurityAuditPipeline()
    return _pipeline


