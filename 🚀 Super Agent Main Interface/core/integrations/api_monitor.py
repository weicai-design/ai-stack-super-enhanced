#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 调用监控器

功能：
- 记录第三方 API 调用耗时、状态、响应码、错误原因
- 提供系统/端点维度的聚合统计
- 为 P1-002 真实 API 对接提供可观测性
"""

from __future__ import annotations

from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Optional
from uuid import uuid4


@dataclass
class APICallRecord:
    call_id: str
    system: str
    endpoint: str
    method: str
    status_code: Optional[int]
    success: bool
    duration_ms: float
    started_at: str
    finished_at: str
    request_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class APIMonitor:
    """
    轻量 API 监控器，内存保存最近 N 条记录，便于前端/接口查询
    """

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self._records: Deque[APICallRecord] = deque(maxlen=max_records)

    def record_call(
        self,
        *,
        system: str,
        endpoint: str,
        method: str,
        status_code: Optional[int],
        success: bool,
        duration_ms: float,
        request_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> APICallRecord:
        now = datetime.utcnow()
        record = APICallRecord(
            call_id=str(uuid4()),
            system=system,
            endpoint=endpoint,
            method=method.upper(),
            status_code=status_code,
            success=success,
            duration_ms=round(duration_ms, 2),
            started_at=(now - timedelta(milliseconds=duration_ms)).isoformat() + "Z",
            finished_at=now.isoformat() + "Z",
            request_id=request_id,
            error=error,
            metadata=metadata or {},
        )
        self._records.append(record)
        return record

    def list_recent(self, limit: int = 100, system: Optional[str] = None) -> List[Dict[str, Any]]:
        records = list(self._records)
        if system:
            records = [rec for rec in records if rec.system == system]
        return [asdict(rec) for rec in records[-limit:]]

    def get_statistics(self, window_minutes: int = 60, system: Optional[str] = None) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        filtered = [
            rec
            for rec in self._records
            if datetime.fromisoformat(rec.finished_at.rstrip("Z")) >= cutoff and (system is None or rec.system == system)
        ]

        total = len(filtered)
        success = len([rec for rec in filtered if rec.success])
        failed = total - success

        by_endpoint = defaultdict(lambda: {"count": 0, "failures": 0, "avg_duration_ms": 0.0})
        for rec in filtered:
            key = f"{rec.system}:{rec.endpoint}"
            entry = by_endpoint[key]
            entry["count"] += 1
            if not rec.success:
                entry["failures"] += 1
            entry["avg_duration_ms"] += rec.duration_ms

        for entry in by_endpoint.values():
            if entry["count"] > 0:
                entry["avg_duration_ms"] = round(entry["avg_duration_ms"] / entry["count"], 2)

        return {
            "window_minutes": window_minutes,
            "system": system,
            "total_calls": total,
            "success_rate": round((success / total * 100) if total else 100.0, 2),
            "failure_rate": round((failed / total * 100) if total else 0.0, 2),
            "endpoints": dict(by_endpoint),
            "recent_errors": [
                {
                    "system": rec.system,
                    "endpoint": rec.endpoint,
                    "status_code": rec.status_code,
                    "error": rec.error,
                    "finished_at": rec.finished_at,
                }
                for rec in filtered
                if not rec.success
            ][:20],
        }


# 全局默认实例（可按需引用）
api_monitor = APIMonitor()

__all__ = ["APIMonitor", "APICallRecord", "api_monitor"]


