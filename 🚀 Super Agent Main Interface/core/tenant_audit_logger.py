#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租户审计日志记录器
P3-402: 提供审计报表
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """审计操作类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    QUOTA_EXCEEDED = "quota_exceeded"
    CONFIG_CHANGE = "config_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"


@dataclass
class AuditLog:
    """审计日志条目"""
    log_id: str
    tenant_id: str
    user_id: Optional[str]
    action: AuditAction
    resource_type: str  # 资源类型 (file/database/cache/quota等)
    resource_id: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action"] = self.action.value
        return data


class TenantAuditLogger:
    """
    租户审计日志记录器
    
    功能：
    1. 记录所有租户操作
    2. 生成审计报表
    3. 支持查询和导出
    """
    
    def __init__(self, log_dir: str = "./data/audit_logs"):
        """
        初始化审计日志记录器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的日志（用于快速查询）
        self.logs: List[AuditLog] = []
        self.max_memory_logs = 10000
        
        logger.info(f"租户审计日志记录器初始化完成，日志目录: {self.log_dir}")
    
    def log(
        self,
        tenant_id: str,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        记录审计日志
        
        Args:
            tenant_id: 租户ID
            action: 操作类型
            resource_type: 资源类型
            user_id: 用户ID
            resource_id: 资源ID
            details: 详细信息
            ip_address: IP地址
            user_agent: User Agent
            success: 是否成功
            error_message: 错误信息
            
        Returns:
            审计日志对象
        """
        log_id = f"audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.logs)}"
        
        log = AuditLog(
            log_id=log_id,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        
        # 添加到内存
        self.logs.append(log)
        
        # 如果内存日志过多，持久化到文件
        if len(self.logs) > self.max_memory_logs:
            self._persist_logs()
        
        # 立即持久化到文件（按租户和日期）
        self._persist_log(log)
        
        logger.debug(f"审计日志已记录: {tenant_id} - {action.value} - {resource_type}")
        
        return log
    
    def _persist_log(self, log: AuditLog):
        """持久化单个日志"""
        # 按租户和日期组织文件
        date_str = log.timestamp[:10]  # YYYY-MM-DD
        log_file = self.log_dir / log.tenant_id / f"{date_str}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 追加到文件
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log.to_dict(), ensure_ascii=False) + "\n")
    
    def _persist_logs(self):
        """批量持久化日志"""
        if not self.logs:
            return
        
        # 按租户和日期分组
        logs_by_tenant_date: Dict[str, List[AuditLog]] = {}
        for log in self.logs:
            date_str = log.timestamp[:10]
            key = f"{log.tenant_id}/{date_str}"
            if key not in logs_by_tenant_date:
                logs_by_tenant_date[key] = []
            logs_by_tenant_date[key].append(log)
        
        # 写入文件
        for key, logs in logs_by_tenant_date.items():
            tenant_id, date_str = key.split("/")
            log_file = self.log_dir / tenant_id / f"{date_str}.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, "a", encoding="utf-8") as f:
                for log in logs:
                    f.write(json.dumps(log.to_dict(), ensure_ascii=False) + "\n")
        
        # 清空内存日志
        self.logs = []
    
    def query_logs(
        self,
        tenant_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[AuditLog]:
        """
        查询审计日志
        
        Args:
            tenant_id: 租户ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            action: 操作类型
            resource_type: 资源类型
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            审计日志列表
        """
        logs = []
        
        # 从内存查询
        for log in self.logs:
            if log.tenant_id == tenant_id:
                if action and log.action != action:
                    continue
                if resource_type and log.resource_type != resource_type:
                    continue
                if user_id and log.user_id != user_id:
                    continue
                if start_date and log.timestamp < start_date:
                    continue
                if end_date and log.timestamp > end_date:
                    continue
                logs.append(log)
        
        # 从文件查询
        tenant_log_dir = self.log_dir / tenant_id
        if tenant_log_dir.exists():
            # 确定日期范围
            if start_date and end_date:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                current = start
                while current <= end:
                    date_str = current.strftime("%Y-%m-%d")
                    log_file = tenant_log_dir / f"{date_str}.jsonl"
                    if log_file.exists():
                        logs.extend(self._load_logs_from_file(log_file, action, resource_type, user_id))
                    current += timedelta(days=1)
            else:
                # 加载所有文件
                for log_file in tenant_log_dir.glob("*.jsonl"):
                    logs.extend(self._load_logs_from_file(log_file, action, resource_type, user_id))
        
        # 排序并限制数量
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]
    
    def _load_logs_from_file(
        self,
        log_file: Path,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[AuditLog]:
        """从文件加载日志"""
        logs = []
        
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    
                    # 过滤
                    if action and data.get("action") != action.value:
                        continue
                    if resource_type and data.get("resource_type") != resource_type:
                        continue
                    if user_id and data.get("user_id") != user_id:
                        continue
                    
                    # 重建AuditLog对象
                    log = AuditLog(
                        log_id=data["log_id"],
                        tenant_id=data["tenant_id"],
                        user_id=data.get("user_id"),
                        action=AuditAction(data["action"]),
                        resource_type=data["resource_type"],
                        resource_id=data.get("resource_id"),
                        details=data.get("details", {}),
                        ip_address=data.get("ip_address"),
                        user_agent=data.get("user_agent"),
                        timestamp=data["timestamp"],
                        success=data.get("success", True),
                        error_message=data.get("error_message"),
                    )
                    logs.append(log)
        except Exception as e:
            logger.error(f"加载日志文件失败: {log_file} - {e}")
        
        return logs
    
    def generate_audit_report(
        self,
        tenant_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        生成审计报表
        
        Args:
            tenant_id: 租户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            审计报表数据
        """
        logs = self.query_logs(tenant_id, start_date, end_date)
        
        # 统计
        total_actions = len(logs)
        actions_by_type: Dict[str, int] = {}
        actions_by_resource: Dict[str, int] = {}
        actions_by_user: Dict[str, int] = {}
        success_count = 0
        failure_count = 0
        
        for log in logs:
            # 按操作类型统计
            action_type = log.action.value
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1
            
            # 按资源类型统计
            resource = log.resource_type
            actions_by_resource[resource] = actions_by_resource.get(resource, 0) + 1
            
            # 按用户统计
            if log.user_id:
                actions_by_user[log.user_id] = actions_by_user.get(log.user_id, 0) + 1
            
            # 成功/失败统计
            if log.success:
                success_count += 1
            else:
                failure_count += 1
        
        # 生成报表
        report = {
            "tenant_id": tenant_id,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "summary": {
                "total_actions": total_actions,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": (success_count / total_actions * 100) if total_actions > 0 else 0,
            },
            "statistics": {
                "actions_by_type": actions_by_type,
                "actions_by_resource": actions_by_resource,
                "actions_by_user": actions_by_user,
            },
            "top_users": sorted(
                actions_by_user.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "recent_logs": [log.to_dict() for log in logs[:100]],
        }
        
        logger.info(f"生成审计报表: {tenant_id} - {start_date} to {end_date}")
        
        return report
    
    def export_audit_logs(
        self,
        tenant_id: str,
        start_date: str,
        end_date: str,
        format: str = "json",
    ) -> str:
        """
        导出审计日志
        
        Args:
            tenant_id: 租户ID
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式 (json/csv)
            
        Returns:
            导出文件路径
        """
        logs = self.query_logs(tenant_id, start_date, end_date)
        
        export_dir = self.log_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            export_file = export_dir / f"{tenant_id}_audit_{timestamp}.json"
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump([log.to_dict() for log in logs], f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            export_file = export_dir / f"{tenant_id}_audit_{timestamp}.csv"
            with open(export_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "log_id", "tenant_id", "user_id", "action", "resource_type",
                    "resource_id", "timestamp", "success", "ip_address"
                ])
                writer.writeheader()
                for log in logs:
                    writer.writerow({
                        "log_id": log.log_id,
                        "tenant_id": log.tenant_id,
                        "user_id": log.user_id or "",
                        "action": log.action.value,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id or "",
                        "timestamp": log.timestamp,
                        "success": log.success,
                        "ip_address": log.ip_address or "",
                    })
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        logger.info(f"审计日志已导出: {export_file}")
        
        return str(export_file)


_audit_logger: Optional[TenantAuditLogger] = None


def get_audit_logger() -> TenantAuditLogger:
    """获取审计日志记录器实例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = TenantAuditLogger()
    return _audit_logger

