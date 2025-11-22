#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈入库机制
P0-001: 实现反馈处理器，将检查结果、用户反馈、系统反馈入库存储
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
from .execution_checker import CheckReport

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """反馈类型"""
    CHECK_RESULT = "check_result"  # 检查结果反馈
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    SYSTEM_FEEDBACK = "system_feedback"  # 系统反馈
    AUTO_FEEDBACK = "auto_feedback"  # 自动反馈
    RE_EXECUTION = "re_execution"  # 再执行反馈


class FeedbackStatus(str, Enum):
    """反馈状态"""
    PENDING = "pending"  # 待处理
    PROCESSED = "processed"  # 已处理
    IGNORED = "ignored"  # 已忽略
    RESOLVED = "resolved"  # 已解决


@dataclass
class Feedback:
    """反馈实体"""
    feedback_id: str
    feedback_type: FeedbackType
    execution_id: str
    source: str
    status: FeedbackStatus
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    processed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class FeedbackHandler:
    """
    反馈处理器
    
    功能：
    - 接收检查结果反馈
    - 接收用户反馈
    - 接收系统反馈
    - 反馈入库存储
    - 反馈查询和分析
    - 触发再执行
    """
    
    def __init__(
        self,
        event_bus: Optional[UnifiedEventBus] = None,
        db_path: Optional[Path] = None,
    ):
        self.event_bus = event_bus or get_unified_event_bus()
        
        # 数据库路径
        if db_path is None:
            project_root = Path(__file__).resolve().parents[2]
            db_path = project_root / "artifacts" / "evidence" / "feedback.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 初始化数据库
        self._init_database()
        
        # 订阅检查事件
        self._subscribe_to_events()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # 创建反馈表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedbacks (
                    feedback_id TEXT PRIMARY KEY,
                    feedback_type TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    processed_at TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_execution_id 
                ON feedbacks(execution_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_type 
                ON feedbacks(feedback_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON feedbacks(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON feedbacks(timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"反馈数据库已初始化: {self.db_path}")
        except Exception as e:
            logger.error(f"反馈数据库初始化失败: {e}", exc_info=True)
    
    def _subscribe_to_events(self):
        """订阅事件"""
        from .unified_event_bus import EventFilter
        
        # 订阅检查事件
        check_filter = EventFilter(
            category=EventCategory.CHECK,
        )
        self.event_bus.subscribe(
            callback=self._handle_check_event,
            event_filter=check_filter,
            subscriber_id="feedback_handler_check",
        )
    
    async def _handle_check_event(self, event):
        """处理检查事件"""
        try:
            execution_id = event.payload.get("execution_id")
            check_result = event.payload.get("result")
            
            if check_result == "fail":
                # 自动创建反馈
                await self.create_feedback(
                    feedback_type=FeedbackType.CHECK_RESULT,
                    execution_id=execution_id,
                    source="execution_checker",
                    content={
                        "check_id": event.payload.get("check_id"),
                        "rule_id": event.payload.get("rule_id"),
                        "result": check_result,
                        "message": event.payload.get("message"),
                    },
                )
        except Exception as e:
            logger.error(f"处理检查事件失败: {e}", exc_info=True)
    
    async def create_feedback(
        self,
        feedback_type: FeedbackType,
        execution_id: str,
        source: str,
        content: Dict[str, Any],
        status: FeedbackStatus = FeedbackStatus.PENDING,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Feedback:
        """
        创建反馈
        
        Args:
            feedback_type: 反馈类型
            execution_id: 执行ID
            source: 反馈源
            content: 反馈内容
            status: 反馈状态
            metadata: 元数据
            
        Returns:
            反馈实体
        """
        feedback = Feedback(
            feedback_id=f"fb_{uuid4()}",
            feedback_type=feedback_type,
            execution_id=execution_id,
            source=source,
            status=status,
            content=content,
            metadata=metadata or {},
        )
        
        # 入库
        await self._save_feedback(feedback)
        
        # 发布反馈事件
        await self.event_bus.publish(
            category=EventCategory.FEEDBACK,
            event_type="feedback_created",
            source="feedback_handler",
            severity=EventSeverity.INFO,
            payload={
                "feedback_id": feedback.feedback_id,
                "feedback_type": feedback_type.value,
                "execution_id": execution_id,
            },
            correlation_id=execution_id,
        )
        
        logger.debug(f"反馈已创建: {feedback.feedback_id} ({feedback_type.value})")
        
        return feedback
    
    async def _save_feedback(self, feedback: Feedback):
        """保存反馈到数据库"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO feedbacks (
                        feedback_id, feedback_type, execution_id, source,
                        status, content, timestamp, processed_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feedback.feedback_id,
                    feedback.feedback_type.value,
                    feedback.execution_id,
                    feedback.source,
                    feedback.status.value,
                    json.dumps(feedback.content, ensure_ascii=False),
                    feedback.timestamp,
                    feedback.processed_at,
                    json.dumps(feedback.metadata, ensure_ascii=False),
                ))
                
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"保存反馈失败: {e}", exc_info=True)
    
    async def process_feedback(
        self,
        feedback_id: str,
        action: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        处理反馈
        
        Args:
            feedback_id: 反馈ID
            action: 处理动作（resolve/ignore/re_execute）
            result: 处理结果
            
        Returns:
            是否成功
        """
        try:
            feedback = self.get_feedback(feedback_id)
            if not feedback:
                return False
            
            # 更新状态
            if action == "resolve":
                feedback.status = FeedbackStatus.RESOLVED
            elif action == "ignore":
                feedback.status = FeedbackStatus.IGNORED
            elif action == "re_execute":
                feedback.status = FeedbackStatus.PROCESSED
                # 触发再执行事件
                await self.event_bus.publish(
                    category=EventCategory.EXECUTION,
                    event_type="re_execute",
                    source="feedback_handler",
                    severity=EventSeverity.INFO,
                    payload={
                        "feedback_id": feedback_id,
                        "execution_id": feedback.execution_id,
                        "action": action,
                        "result": result,
                    },
                    correlation_id=feedback.execution_id,
                )
            
            feedback.processed_at = datetime.utcnow().isoformat() + "Z"
            if result:
                feedback.metadata["process_result"] = result
            
            # 更新数据库
            await self._save_feedback(feedback)
            
            # 发布处理事件
            await self.event_bus.publish(
                category=EventCategory.FEEDBACK,
                event_type="feedback_processed",
                source="feedback_handler",
                severity=EventSeverity.INFO,
                payload={
                    "feedback_id": feedback_id,
                    "action": action,
                },
            )
            
            return True
        except Exception as e:
            logger.error(f"处理反馈失败: {e}", exc_info=True)
            return False
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取反馈"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT feedback_id, feedback_type, execution_id, source,
                           status, content, timestamp, processed_at, metadata
                    FROM feedbacks
                    WHERE feedback_id = ?
                """, (feedback_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return Feedback(
                        feedback_id=row[0],
                        feedback_type=FeedbackType(row[1]),
                        execution_id=row[2],
                        source=row[3],
                        status=FeedbackStatus(row[4]),
                        content=json.loads(row[5]),
                        timestamp=row[6],
                        processed_at=row[7],
                        metadata=json.loads(row[8]) if row[8] else {},
                    )
        except Exception as e:
            logger.error(f"获取反馈失败: {e}", exc_info=True)
        
        return None
    
    def get_feedbacks(
        self,
        execution_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        status: Optional[FeedbackStatus] = None,
        limit: int = 100,
    ) -> List[Feedback]:
        """获取反馈列表"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                query = "SELECT feedback_id, feedback_type, execution_id, source, status, content, timestamp, processed_at, metadata FROM feedbacks WHERE 1=1"
                params = []
                
                if execution_id:
                    query += " AND execution_id = ?"
                    params.append(execution_id)
                if feedback_type:
                    query += " AND feedback_type = ?"
                    params.append(feedback_type.value)
                if status:
                    query += " AND status = ?"
                    params.append(status.value)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()
                
                feedbacks = []
                for row in rows:
                    feedbacks.append(Feedback(
                        feedback_id=row[0],
                        feedback_type=FeedbackType(row[1]),
                        execution_id=row[2],
                        source=row[3],
                        status=FeedbackStatus(row[4]),
                        content=json.loads(row[5]),
                        timestamp=row[6],
                        processed_at=row[7],
                        metadata=json.loads(row[8]) if row[8] else {},
                    ))
                
                return feedbacks
        except Exception as e:
            logger.error(f"获取反馈列表失败: {e}", exc_info=True)
        
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                cursor = conn.cursor()
                
                # 总数
                cursor.execute("SELECT COUNT(*) FROM feedbacks")
                total = cursor.fetchone()[0]
                
                # 按类型统计
                cursor.execute("""
                    SELECT feedback_type, COUNT(*) 
                    FROM feedbacks 
                    GROUP BY feedback_type
                """)
                by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 按状态统计
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM feedbacks 
                    GROUP BY status
                """)
                by_status = {row[0]: row[1] for row in cursor.fetchall()}
                
                conn.close()
                
                return {
                    "total": total,
                    "by_type": by_type,
                    "by_status": by_status,
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}", exc_info=True)
            return {
                "total": 0,
                "by_type": {},
                "by_status": {},
            }

