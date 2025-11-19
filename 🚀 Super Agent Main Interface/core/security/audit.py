from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from .config import get_security_settings


@dataclass
class AuditRecord:
    event_id: str
    event_type: str
    actor: str
    status: str
    timestamp: str
    duration_ms: Optional[float] = None
    request_path: Optional[str] = None
    method: Optional[str] = None
    ip: Optional[str] = None
    metadata: Dict[str, Any] | None = None


class AuditLogger:
    """Append-only JSONL logger for security events."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log_event(
        self,
        event_type: str,
        actor: str = "system",
        status: str = "success",
        duration_ms: Optional[float] = None,
        request_path: Optional[str] = None,
        method: Optional[str] = None,
        ip: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            event_id=str(uuid4()),
            event_type=event_type,
            actor=actor or "anonymous",
            status=status,
            timestamp=datetime.utcnow().isoformat() + "Z",
            duration_ms=duration_ms,
            request_path=request_path,
            method=method,
            ip=ip,
            metadata=metadata or {},
        )
        serialized = json.dumps(asdict(record), ensure_ascii=False)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as fp:
                fp.write(serialized + os.linesep)
        return record

    def log_http_request(
        self,
        request,
        response_status: int,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        client_ip = request.client.host if request.client else None
        actor = request.headers.get("x-user-id") or request.headers.get("x-api-client") or "anonymous"
        self.log_event(
            event_type="http_request",
            actor=actor,
            status="success" if response_status < 400 else "failed",
            duration_ms=duration_ms,
            request_path=request.url.path,
            method=request.method,
            ip=client_ip,
            metadata=metadata or {"status_code": response_status},
        )


_audit_logger: Optional[AuditLogger] = None
_audit_lock = threading.Lock()


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger:
        return _audit_logger
    with _audit_lock:
        if not _audit_logger:
            settings = get_security_settings()
            _audit_logger = AuditLogger(settings.audit_log_path)
        return _audit_logger


