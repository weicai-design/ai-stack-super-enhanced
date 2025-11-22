"""
终端命令审计日志系统
提供独立的审计日志存储、查询和导出功能
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .security.audit_pipeline import SecurityAuditPipeline, get_audit_pipeline
from .security.risk_engine import SecurityRiskEngine, get_risk_engine

logger = logging.getLogger(__name__)

# 导出枚举类供其他模块使用
__all__ = ['AuditEventType', 'AuditSeverity', 'TerminalAuditLogger', 'AuditLogEntry']


class AuditEventType(Enum):
    """审计事件类型"""
    COMMAND_START = "command_start"
    COMMAND_BLOCKED = "command_blocked"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"
    COMMAND_TIMEOUT = "command_timeout"
    WHITELIST_UPDATE = "whitelist_update"
    SECURITY_ALERT = "security_alert"
    POLICY_VIOLATION = "policy_violation"


class AuditSeverity(Enum):
    """审计严重程度"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """审计日志条目"""
    log_id: str
    timestamp: str
    event_type: str
    severity: str
    command_id: Optional[str] = None
    command: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    cwd: Optional[str] = None
    return_code: Optional[int] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class TerminalAuditLogger:
    """
    终端命令审计日志系统
    
    功能：
    1. 记录所有终端命令执行事件
    2. 支持按条件查询审计日志
    3. 支持导出审计日志
    4. 支持日志轮转和归档
    """
    
    def __init__(
        self,
        audit_log_dir: Optional[str] = None,
        audit_pipeline: Optional[SecurityAuditPipeline] = None,
        risk_engine: Optional[SecurityRiskEngine] = None,
    ):
        """
        初始化审计日志系统
        
        Args:
            audit_log_dir: 审计日志目录
        """
        if audit_log_dir:
            self.audit_log_dir = Path(audit_log_dir)
        else:
            # 默认存储在项目data目录
            project_root = Path(__file__).parent.parent.parent
            self.audit_log_dir = project_root / "data" / "terminal_audit"
        
        self.audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径（按日期分割）
        self.current_log_file = self.audit_log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # 配置
        self.max_log_file_size = 100 * 1024 * 1024  # 100MB
        self.max_log_files = 30  # 保留30天的日志
        self.enable_compression = True
        
        self.audit_pipeline = audit_pipeline or get_audit_pipeline()
        self.risk_engine = risk_engine or get_risk_engine()
        logger.info(f"终端审计日志系统已初始化，日志目录: {self.audit_log_dir}")
    
    async def log_event(
        self,
        event_type: str,
        severity: str,
        command_id: Optional[str] = None,
        command: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        cwd: Optional[str] = None,
        return_code: Optional[int] = None,
        duration: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        记录审计事件
        
        Args:
            event_type: 事件类型
            severity: 严重程度
            command_id: 命令ID
            command: 命令内容
            user_id: 用户ID
            session_id: 会话ID
            cwd: 工作目录
            return_code: 返回码
            duration: 执行时长
            success: 是否成功
            error: 错误信息
            metadata: 元数据
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            日志ID
        """
        log_id = f"audit_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # 处理枚举类型或字符串
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        severity_str = severity.value if hasattr(severity, 'value') else str(severity)
        
        entry = AuditLogEntry(
            log_id=log_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type_str,
            severity=severity_str,
            command_id=command_id,
            command=command,
            user_id=user_id,
            session_id=session_id,
            cwd=cwd,
            return_code=return_code,
            duration=duration,
            success=success,
            error=error,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 写入日志文件
        try:
            with open(self.current_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
            
            # 检查文件大小，如果超过限制则轮转
            if self.current_log_file.stat().st_size > self.max_log_file_size:
                await self._rotate_log_file()
            
            if self.audit_pipeline:
                self.audit_pipeline.log_security_event(
                    event_type=event_type_str,
                    source="terminal_audit",
                    severity=severity_str,
                    status="success" if success else "failed",
                    metadata=entry.to_dict(),
                )
                self.audit_pipeline.log_command_event(
                    command=command or "",
                    actor=user_id or "anonymous",
                    severity=severity_str,
                    success=success,
                    metadata=entry.to_dict(),
                )
            if self.risk_engine and not success:
                self.risk_engine.record_command_event(
                    user_id=user_id or "anonymous",
                    success=success,
                    command=command or "",
                )
            return log_id
        except Exception as e:
            logger.error(f"写入审计日志失败: {e}")
            return log_id
    
    async def _rotate_log_file(self):
        """轮转日志文件"""
        try:
            # 创建新的日志文件
            self.current_log_file = self.audit_log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            # 清理旧日志文件
            await self._cleanup_old_logs()
        except Exception as e:
            logger.error(f"日志轮转失败: {e}")
    
    async def _cleanup_old_logs(self):
        """清理旧日志文件"""
        try:
            log_files = sorted(self.audit_log_dir.glob("audit_*.jsonl"), reverse=True)
            
            # 保留最新的N个文件
            for old_file in log_files[self.max_log_files:]:
                old_file.unlink()
                logger.info(f"已删除旧日志文件: {old_file.name}")
        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")
    
    def query_logs(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        command_id: Optional[str] = None,
        user_id: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志
        
        Args:
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            event_type: 事件类型
            severity: 严重程度
            command_id: 命令ID
            user_id: 用户ID
            success: 是否成功
            limit: 返回数量限制
            
        Returns:
            审计日志列表
        """
        results = []
        
        try:
            # 读取所有日志文件
            log_files = sorted(self.audit_log_dir.glob("audit_*.jsonl"), reverse=True)
            
            for log_file in log_files:
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            
                            try:
                                entry = json.loads(line)
                                
                                # 时间过滤
                                if start_time and entry.get("timestamp") < start_time:
                                    continue
                                if end_time and entry.get("timestamp") > end_time:
                                    continue
                                
                                # 事件类型过滤
                                if event_type and entry.get("event_type") != event_type:
                                    continue
                                
                                # 严重程度过滤
                                if severity and entry.get("severity") != severity:
                                    continue
                                
                                # 命令ID过滤
                                if command_id and entry.get("command_id") != command_id:
                                    continue
                                
                                # 用户ID过滤
                                if user_id and entry.get("user_id") != user_id:
                                    continue
                                
                                # 成功状态过滤
                                if success is not None and entry.get("success") != success:
                                    continue
                                
                                results.append(entry)
                                
                                if len(results) >= limit:
                                    return results
                                    
                            except json.JSONDecodeError:
                                continue
                                
                except Exception as e:
                    logger.warning(f"读取日志文件失败 {log_file}: {e}")
                    continue
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []
    
    def get_statistics(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取审计日志统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息
        """
        logs = self.query_logs(start_time=start_time, end_time=end_time, limit=10000)
        
        total = len(logs)
        by_event_type = {}
        by_severity = {}
        blocked_count = 0
        failed_count = 0
        success_count = 0
        
        for log in logs:
            event_type = log.get("event_type", "unknown")
            severity = log.get("severity", "unknown")
            success = log.get("success", True)
            
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            if event_type == AuditEventType.COMMAND_BLOCKED.value:
                blocked_count += 1
            elif not success:
                failed_count += 1
            else:
                success_count += 1
        
        return {
            "total": total,
            "by_event_type": by_event_type,
            "by_severity": by_severity,
            "blocked_count": blocked_count,
            "failed_count": failed_count,
            "success_count": success_count,
            "block_rate": (blocked_count / total * 100) if total > 0 else 0,
            "success_rate": (success_count / total * 100) if total > 0 else 0
        }
    
    def export_logs(
        self,
        output_path: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        导出审计日志
        
        Args:
            output_path: 输出路径
            start_time: 开始时间
            end_time: 结束时间
            format: 导出格式（json/csv）
            
        Returns:
            导出结果
        """
        logs = self.query_logs(start_time=start_time, end_time=end_time, limit=100000)
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                if not logs:
                    return {"success": False, "error": "没有日志可导出"}
                
                with open(output_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)
            else:
                return {"success": False, "error": f"不支持的格式: {format}"}
            
            return {
                "success": True,
                "exported_count": len(logs),
                "output_path": str(output_file),
                "format": format
            }
        except Exception as e:
            logger.error(f"导出审计日志失败: {e}")
            return {"success": False, "error": str(e)}

