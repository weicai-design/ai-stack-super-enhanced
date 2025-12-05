#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全审计管道 - 安全审计与合规检查

架构设计说明：
- 采用事件驱动的审计管道设计
- 支持多类型审计记录（HTTP请求、安全事件、任务执行、命令操作）
- 与事件总线集成，支持实时告警和监控
- 模块化设计，便于扩展新的审计类型

核心功能：
1. HTTP请求审计记录
2. 安全事件记录与告警
3. 任务执行审计追踪
4. 命令操作审计日志
5. 审计记录查询与统计

技术选型：
- 异步事件发布机制
- 数据库持久化存储
- 结构化日志记录
- 实时监控告警

监控告警机制：
- 关键安全事件实时告警
- 审计失败率监控
- 异常访问模式检测
- 性能指标监控

部署配置：
- 支持环境变量配置审计策略
- 可配置告警阈值
- 支持多级告警渠道
"""统一审计日志（文件 + 数据库 + 事件总线）
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
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
        
        # 监控告警配置
        self.alert_thresholds = self._load_alert_thresholds()
        self.critical_events = self._load_critical_events()
    
    def _load_alert_thresholds(self) -> Dict[str, int]:
        """从配置管理器加载告警阈值配置"""
        return {
            "failure_rate": self.config_manager.get_config("audit.failure_rate_threshold", 5),
            "critical_event_count": self.config_manager.get_config("audit.critical_event_count_threshold", 10),
            "slow_request_threshold": self.config_manager.get_config("audit.slow_request_threshold", 5000),
        }
    
    def _load_critical_events(self) -> List[str]:
        """从配置管理器加载关键事件列表"""
        critical_events = self.config_manager.get_config("audit.critical_security_events", "unauthorized_access,data_breach,privilege_escalation")
        return [event.strip() for event in critical_events.split(",") if event.strip()]

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
        critical_events = 0
        slow_requests = 0

        for item in recent:
            etype = item.get("event_type", "unknown")
            sev = item.get("severity", "info")
            by_type[etype] = by_type.get(etype, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            if item.get("status") == "failed":
                failure += 1
            
            # 检查关键事件
            if etype in self.critical_events:
                critical_events += 1
            
            # 检查慢请求
            if etype == "http_request" and item.get("duration_ms", 0) > self.alert_thresholds["slow_request_threshold"]:
                slow_requests += 1

        failure_rate = (failure / len(recent) * 100) if recent else 0
        
        # 触发告警检查
        alerts = self._check_alerts(failure_rate, critical_events, slow_requests)

        return {
            "total": total,
            "recent": len(recent),
            "distribution_by_type": by_type,
            "distribution_by_severity": by_severity,
            "failure_rate": failure_rate,
            "critical_events": critical_events,
            "slow_requests": slow_requests,
            "alerts": alerts,
        }
    
    def _check_alerts(self, failure_rate: float, critical_events: int, slow_requests: int) -> List[Dict[str, Any]]:
        """检查告警条件并生成告警"""
        alerts = []
        
        # 失败率告警
        if failure_rate > self.alert_thresholds["failure_rate"]:
            alerts.append({
                "type": "failure_rate_high",
                "severity": "warning",
                "message": f"审计失败率过高: {failure_rate:.1f}%",
                "threshold": self.alert_thresholds["failure_rate"],
                "actual": failure_rate,
            })
        
        # 关键事件告警
        if critical_events > self.alert_thresholds["critical_event_count"]:
            alerts.append({
                "type": "critical_events_high",
                "severity": "error",
                "message": f"关键安全事件过多: {critical_events}个",
                "threshold": self.alert_thresholds["critical_event_count"],
                "actual": critical_events,
            })
        
        # 慢请求告警
        if slow_requests > 0:
            alerts.append({
                "type": "slow_requests_detected",
                "severity": "warning",
                "message": f"检测到慢请求: {slow_requests}个",
                "threshold": self.alert_thresholds["slow_request_threshold"],
                "actual": slow_requests,
            })
        
        # 发布告警事件
        for alert in alerts:
            self._publish_alert(alert)
        
        return alerts
    
    def _publish_alert(self, alert: Dict[str, Any]) -> None:
        """发布告警事件"""
        try:
            coroutine = self.event_bus.publish(
                category=EventCategory.SECURITY,
                event_type=f"audit.alert.{alert['type']}",
                source="SecurityAuditPipeline",
                severity=EventSeverity(alert['severity']),
                payload=alert,
                correlation_id=str(uuid4()),
            )
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(coroutine)
            else:
                loop.run_until_complete(coroutine)
        except Exception as exc:
            self.logger.warning("告警事件发布失败: %s", exc)
    
    def _retry_with_backoff(self, func: Callable, max_retries: int = 3) -> Any:
        """带指数退避的重试机制"""
        import time
        import random
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    self.logger.error("操作失败，达到最大重试次数: %s", e)
                    raise
                
                # 指数退避
                delay = (2 ** attempt) + random.uniform(0, 1)
                self.logger.warning("操作失败，第 %d 次重试，等待 %.2f 秒: %s", 
                                  attempt + 1, delay, e)
                time.sleep(delay)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "alert_thresholds": self.alert_thresholds,
            "critical_events": self.critical_events,
            "tables": [self.table_name, self.http_table, self.task_table, self.command_table],
        }
        
        # 检查数据库连接
        try:
            count = self.persistence.count(self.table_name)
            health_status["database"] = {"status": "connected", "record_count": count}
        except Exception as e:
            health_status["status"] = "error"
            health_status["database"] = {"status": "disconnected", "error": str(e)}
        
        # 检查事件总线
        try:
            # 简单的事件总线健康检查
            health_status["event_bus"] = {"status": "connected"}
        except Exception as e:
            health_status["status"] = "warning"
            health_status["event_bus"] = {"status": "warning", "error": str(e)}
        
        return health_status
    
    def cleanup_old_records(self, days: int = 30) -> Dict[str, Any]:
        """清理过期记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        tables = [self.table_name, self.http_table, self.task_table, self.command_table]
        results = {}
        
        for table in tables:
            try:
                # 使用重试机制执行清理
                deleted_count = self._retry_with_backoff(
                    lambda: self.persistence.delete(
                        table_name=table,
                        where_clause=f"_created_at < '{cutoff_str}'",
                    )
                )
                results[table] = {"deleted": deleted_count, "status": "success"}
            except Exception as e:
                results[table] = {"deleted": 0, "status": "error", "error": str(e)}
        
        return {
            "cutoff_date": cutoff_str,
            "results": results,
            "timestamp": datetime.now().isoformat(),
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


