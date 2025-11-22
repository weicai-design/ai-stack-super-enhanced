#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证据记录系统
P0-001: 实现证据记录器，记录执行证据、检查证据、反馈证据，支持查询和回溯
"""

import asyncio
import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .unified_event_bus import UnifiedEventBus, EventCategory, EventSeverity, get_unified_event_bus

logger = logging.getLogger(__name__)


class EvidenceType(str, Enum):
    """证据类型"""
    EXECUTION = "execution"  # 执行证据
    CHECK = "check"  # 检查证据
    FEEDBACK = "feedback"  # 反馈证据
    EVENT = "event"  # 事件证据
    LOG = "log"  # 日志证据
    SCREENSHOT = "screenshot"  # 截图证据
    FILE = "file"  # 文件证据


@dataclass
class Evidence:
    """证据实体"""
    evidence_id: str
    evidence_type: EvidenceType
    execution_id: str
    source: str
    content: Dict[str, Any]
    file_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class EvidenceRecorder:
    """
    证据记录器
    
    功能：
    - 记录执行证据
    - 记录检查证据
    - 记录反馈证据
    - 记录事件证据
    - 证据查询和回溯
    - 证据关联追踪
    """
    
    def __init__(
        self,
        event_bus: Optional[UnifiedEventBus] = None,
        db_path: Optional[Path] = None,
        evidence_dir: Optional[Path] = None,
    ):
        self.event_bus = event_bus or get_unified_event_bus()
        
        # 数据库路径
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "artifacts" / "evidence" / "evidence.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 证据文件目录
        if evidence_dir is None:
            project_root = Path(__file__).resolve().parents[2]
            evidence_dir = project_root / "artifacts" / "evidence" / "files"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 初始化数据库
        self._init_database()
        
        # 订阅事件
        self._subscribe_to_events()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # 创建证据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    evidence_type TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_id 
                ON evidence(execution_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_evidence_type 
                ON evidence(evidence_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON evidence(timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"证据数据库已初始化: {self.db_path}")
        except Exception as e:
            logger.error(f"证据数据库初始化失败: {e}", exc_info=True)
    
    def _subscribe_to_events(self):
        """订阅事件"""
        from .unified_event_bus import EventFilter
        
        # 订阅所有事件（用于记录事件证据）
        self.event_bus.subscribe(
            callback=self._handle_event,
            subscriber_id="evidence_recorder_events",
        )
    
    async def _handle_event(self, event):
        """处理事件（自动记录为证据）"""
        try:
            # 只记录重要事件
            if event.severity in (EventSeverity.ERROR, EventSeverity.CRITICAL, EventSeverity.WARNING):
                await self.record_evidence(
                    evidence_type=EvidenceType.EVENT,
                    execution_id=event.correlation_id or event.event_id,
                    source=event.source,
                    content={
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "category": event.category.value,
                        "severity": event.severity.value,
                        "payload": event.payload,
                    },
                    metadata={
                        "auto_recorded": True,
                        "parent_event_id": event.parent_event_id,
                    },
                )
        except Exception as e:
            logger.error(f"处理事件失败: {e}", exc_info=True)
    
    async def record_evidence(
        self,
        evidence_type: EvidenceType,
        execution_id: str,
        source: str,
        content: Dict[str, Any],
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Evidence:
        """
        记录证据
        
        Args:
            evidence_type: 证据类型
            execution_id: 执行ID
            source: 证据源
            content: 证据内容
            file_path: 文件路径（可选）
            metadata: 元数据
            
        Returns:
            证据实体
        """
        evidence = Evidence(
            evidence_id=f"ev_{uuid4()}",
            evidence_type=evidence_type,
            execution_id=execution_id,
            source=source,
            content=content,
            file_path=file_path,
            metadata=metadata or {},
        )
        
        # 如果有文件，保存文件
        if file_path and Path(file_path).exists():
            saved_path = await self._save_evidence_file(file_path, evidence.evidence_id)
            evidence.file_path = str(saved_path)
        
        # 入库
        await self._save_evidence(evidence)
        
        # 发布证据事件
        await self.event_bus.publish(
            category=EventCategory.SYSTEM,
            event_type="evidence_recorded",
            source="evidence_recorder",
            severity=EventSeverity.INFO,
            payload={
                "evidence_id": evidence.evidence_id,
                "evidence_type": evidence_type.value,
                "execution_id": execution_id,
            },
            correlation_id=execution_id,
        )
        
        logger.debug(f"证据已记录: {evidence.evidence_id} ({evidence_type.value})")
        
        return evidence
    
    async def _save_evidence_file(self, source_path: str, evidence_id: str) -> Path:
        """保存证据文件"""
        try:
            source = Path(source_path)
            if not source.exists():
                return Path(source_path)
            
            # 生成目标路径
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_ext = source.suffix
            target_path = self.evidence_dir / f"{evidence_id}_{timestamp}{file_ext}"
            
            # 复制文件
            import shutil
            shutil.copy2(source, target_path)
            
            return target_path
        except Exception as e:
            logger.error(f"保存证据文件失败: {e}", exc_info=True)
            return Path(source_path)
    
    async def _save_evidence(self, evidence: Evidence):
        """保存证据到数据库"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO evidence (
                        evidence_id, evidence_type, execution_id, source,
                        content, file_path, timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    evidence.evidence_id,
                    evidence.evidence_type.value,
                    evidence.execution_id,
                    evidence.source,
                    json.dumps(evidence.content, ensure_ascii=False),
                    evidence.file_path,
                    evidence.timestamp,
                    json.dumps(evidence.metadata, ensure_ascii=False),
                ))
                
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"保存证据失败: {e}", exc_info=True)
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """获取证据"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT evidence_id, evidence_type, execution_id, source,
                           content, file_path, timestamp, metadata
                    FROM evidence
                    WHERE evidence_id = ?
                """, (evidence_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return Evidence(
                        evidence_id=row[0],
                        evidence_type=EvidenceType(row[1]),
                        execution_id=row[2],
                        source=row[3],
                        content=json.loads(row[4]),
                        file_path=row[5],
                        timestamp=row[6],
                        metadata=json.loads(row[7]) if row[7] else {},
                    )
        except Exception as e:
            logger.error(f"获取证据失败: {e}", exc_info=True)
        
        return None
    
    def get_evidence_by_execution(
        self,
        execution_id: str,
        evidence_type: Optional[EvidenceType] = None,
        limit: int = 100,
    ) -> List[Evidence]:
        """根据执行ID获取证据"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                query = """
                    SELECT evidence_id, evidence_type, execution_id, source,
                           content, file_path, timestamp, metadata
                    FROM evidence
                    WHERE execution_id = ?
                """
                params = [execution_id]
                
                if evidence_type:
                    query += " AND evidence_type = ?"
                    params.append(evidence_type.value)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                evidence_list = []
                for row in rows:
                    evidence_list.append(Evidence(
                        evidence_id=row[0],
                        evidence_type=EvidenceType(row[1]),
                        execution_id=row[2],
                        source=row[3],
                        content=json.loads(row[4]),
                        file_path=row[5],
                        timestamp=row[6],
                        metadata=json.loads(row[7]) if row[7] else {},
                    ))
                
                return evidence_list
        except Exception as e:
            logger.error(f"获取证据列表失败: {e}", exc_info=True)
        
        return []
    
    def get_evidence_timeline(self, execution_id: str) -> List[Evidence]:
        """获取执行时间线（所有相关证据）"""
        return self.get_evidence_by_execution(execution_id, limit=1000)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                # 总数
                cursor.execute("SELECT COUNT(*) FROM evidence")
                total = cursor.fetchone()[0]
                
                # 按类型统计
                cursor.execute("""
                    SELECT evidence_type, COUNT(*) 
                    FROM evidence 
                    GROUP BY evidence_type
                """)
                by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 按执行ID统计
                cursor.execute("""
                    SELECT execution_id, COUNT(*) 
                    FROM evidence 
                    GROUP BY execution_id
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                top_executions = {row[0]: row[1] for row in cursor.fetchall()}
                
                conn.close()
                
                return {
                    "total": total,
                    "by_type": by_type,
                    "top_executions": top_executions,
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return {
                "total": 0,
                "by_type": {},
                "top_executions": {},
            }


_evidence_recorder: Optional[EvidenceRecorder] = None


def get_evidence_recorder() -> EvidenceRecorder:
    """获取证据记录器单例"""
    global _evidence_recorder
    if _evidence_recorder is None:
        _evidence_recorder = EvidenceRecorder()
    return _evidence_recorder

