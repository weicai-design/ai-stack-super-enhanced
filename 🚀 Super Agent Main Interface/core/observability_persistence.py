"""
可观测性数据持久化
将Trace、指标、事件等数据持久化到数据库
"""

import sqlite3
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)


class ObservabilityPersistence:
    """可观测性数据持久化"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化持久化系统
        
        Args:
            db_path: 数据库路径（可选，默认使用项目data目录）
        """
        if not db_path:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "observability"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "observability.db")
        
        self.db_path = db_path
        self._lock = threading.Lock()
        
        # 初始化数据库
        self._init_database()
        
        logger.info(f"可观测性数据持久化系统初始化完成，数据库路径: {db_path}")
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Traces表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                service_name TEXT,
                start_time REAL NOT NULL,
                end_time REAL,
                duration REAL,
                status TEXT,
                tags TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Spans表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                span_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                parent_span_id TEXT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                duration REAL,
                tags TEXT,
                logs TEXT,
                error TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
            )
        """)
        
        # 长任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_tasks (
                task_id TEXT PRIMARY KEY,
                trace_id TEXT,
                name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                progress REAL DEFAULT 0.0,
                start_time REAL NOT NULL,
                end_time REAL,
                duration REAL,
                current_step TEXT,
                metadata TEXT,
                error TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # 任务快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                progress REAL NOT NULL,
                step TEXT,
                metadata TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (task_id) REFERENCES long_tasks(task_id)
            )
        """)
        
        # 指标表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp REAL NOT NULL,
                tags TEXT,
                metric_type TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # 事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_name TEXT NOT NULL,
                timestamp REAL NOT NULL,
                trace_id TEXT,
                span_id TEXT,
                properties TEXT,
                level TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_request_id ON traces(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_spans_start_time ON spans(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_long_tasks_trace_id ON long_tasks(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_long_tasks_start_time ON long_tasks(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_snapshots_task_id ON task_snapshots(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event_name ON events(event_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        
        conn.commit()
        conn.close()
    
    def save_trace(self, trace: Dict[str, Any]):
        """保存Trace"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO traces 
                (trace_id, request_id, service_name, start_time, end_time, duration, status, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace["trace_id"],
                trace["request_id"],
                trace.get("service_name"),
                trace["start_time"],
                trace.get("end_time"),
                trace.get("duration"),
                trace.get("status"),
                json.dumps(trace.get("tags", {}))
            ))
            
            conn.commit()
            conn.close()
    
    def save_span(self, span: Dict[str, Any]):
        """保存Span"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO spans 
                (span_id, trace_id, parent_span_id, name, type, status, start_time, end_time, duration, tags, logs, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                span["span_id"],
                span["trace_id"],
                span.get("parent_span_id"),
                span["name"],
                span["type"],
                span["status"],
                span["start_time"],
                span.get("end_time"),
                span.get("duration"),
                json.dumps(span.get("tags", {})),
                json.dumps(span.get("logs", [])),
                span.get("error")
            ))
            
            conn.commit()
            conn.close()
    
    def save_long_task(self, task: Dict[str, Any]):
        """保存长任务"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO long_tasks 
                (task_id, trace_id, name, task_type, status, progress, start_time, end_time, duration, current_step, metadata, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task["task_id"],
                task.get("trace_id"),
                task["name"],
                task["task_type"],
                task["status"],
                task.get("progress", 0.0),
                task["start_time"],
                task.get("end_time"),
                task.get("duration"),
                task.get("current_step"),
                json.dumps(task.get("metadata", {})),
                task.get("error")
            ))
            
            conn.commit()
            conn.close()
    
    def save_task_snapshot(self, task_id: str, snapshot: Dict[str, Any]):
        """保存任务快照"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO task_snapshots 
                (task_id, timestamp, progress, step, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                snapshot["timestamp"],
                snapshot["progress"],
                snapshot.get("step"),
                json.dumps(snapshot.get("metadata", {}))
            ))
            
            conn.commit()
            conn.close()
    
    def save_metric(self, metric: Dict[str, Any]):
        """保存指标"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO metrics 
                (name, value, timestamp, tags, metric_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric["name"],
                metric["value"],
                metric["timestamp"],
                json.dumps(metric.get("tags", {})),
                metric.get("metric_type", "gauge")
            ))
            
            conn.commit()
            conn.close()
    
    def save_event(self, event: Dict[str, Any]):
        """保存事件"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO events 
                (event_id, event_name, timestamp, trace_id, span_id, properties, level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event["event_id"],
                event["event_name"],
                event["timestamp"],
                event.get("trace_id"),
                event.get("span_id"),
                json.dumps(event.get("properties", {})),
                event.get("level", "info")
            ))
            
            conn.commit()
            conn.close()
    
    def get_traces(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取Traces"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM traces WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND start_time >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND start_time <= ?"
            params.append(end_time)
        
        query += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        traces = []
        for row in rows:
            trace = dict(row)
            trace["tags"] = json.loads(trace.get("tags") or "{}")
            traces.append(trace)
        
        conn.close()
        return traces
    
    def get_task_snapshots(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务快照"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM task_snapshots 
            WHERE task_id = ? 
            ORDER BY timestamp ASC
        """, (task_id,))
        
        rows = cursor.fetchall()
        snapshots = []
        for row in rows:
            snapshot = dict(row)
            snapshot["metadata"] = json.loads(snapshot.get("metadata") or "{}")
            snapshots.append(snapshot)
        
        conn.close()
        return snapshots
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with self._lock:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # 删除旧的Traces（同时删除关联的Spans）
            cursor.execute("DELETE FROM traces WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM spans WHERE start_time < ?", (cutoff_time,))
            
            # 删除旧的长任务和快照
            cursor.execute("DELETE FROM long_tasks WHERE start_time < ?", (cutoff_time,))
            cursor.execute("DELETE FROM task_snapshots WHERE timestamp < ?", (cutoff_time,))
            
            # 删除旧的指标
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff_time,))
            
            # 删除旧的事件
            cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"已清理 {days} 天前的数据")



