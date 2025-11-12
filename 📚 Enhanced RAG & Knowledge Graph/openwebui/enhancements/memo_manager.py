"""
备忘录管理模块
支持文字和语音备忘录，可与工作计划关联
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class MemoManager:
    """备忘录管理器"""
    
    def __init__(self, db_path: str = "memos.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化备忘录数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 备忘录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memo_type TEXT DEFAULT 'text',
                memo_title TEXT NOT NULL,
                memo_content TEXT NOT NULL,
                audio_path TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'active',
                due_date TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 备忘录提醒表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memo_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memo_id INTEGER NOT NULL,
                remind_time TEXT NOT NULL,
                remind_type TEXT DEFAULT 'notification',
                reminded BOOLEAN DEFAULT 0,
                FOREIGN KEY (memo_id) REFERENCES memos(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ 备忘录数据库初始化完成: {self.db_path}")
    
    def create_memo(self, user_id: str, memo_data: Dict[str, Any]) -> int:
        """创建备忘录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memos (
                user_id, memo_type, memo_title, memo_content,
                audio_path, priority, due_date, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            memo_data.get("type", "text"),
            memo_data.get("title", ""),
            memo_data.get("content", ""),
            memo_data.get("audio_path"),
            memo_data.get("priority", 2),
            memo_data.get("due_date"),
            json.dumps(memo_data.get("tags", []))
        ))
        
        memo_id = cursor.lastrowid
        
        # 添加提醒
        if memo_data.get("remind_time"):
            cursor.execute("""
                INSERT INTO memo_reminders (memo_id, remind_time)
                VALUES (?, ?)
            """, (memo_id, memo_data["remind_time"]))
        
        conn.commit()
        conn.close()
        
        return memo_id
    
    def create_voice_memo(self, user_id: str, title: str, audio_path: str, transcription: str = "") -> int:
        """创建语音备忘录"""
        return self.create_memo(user_id, {
            "type": "voice",
            "title": title,
            "content": transcription,
            "audio_path": audio_path,
            "priority": 3
        })
    
    def get_memos(self, user_id: str, status: str = "active", limit: int = 50) -> List[Dict[str, Any]]:
        """获取备忘录列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, memo_type, memo_title, memo_content, audio_path,
                   priority, status, due_date, tags, created_at
            FROM memos
            WHERE user_id = ? AND status = ?
            ORDER BY priority DESC, created_at DESC
            LIMIT ?
        """, (user_id, status, limit))
        
        memos = []
        for row in cursor.fetchall():
            memos.append({
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "content": row[3],
                "audio_path": row[4],
                "priority": row[5],
                "status": row[6],
                "due_date": row[7],
                "tags": json.loads(row[8]) if row[8] else [],
                "created_at": row[9]
            })
        
        conn.close()
        return memos
    
    def get_memo_by_id(self, memo_id: int) -> Optional[Dict[str, Any]]:
        """获取单个备忘录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, memo_type, memo_title, memo_content, audio_path,
                   priority, status, due_date, tags
            FROM memos
            WHERE id = ?
        """, (memo_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "type": row[2],
                "title": row[3],
                "content": row[4],
                "audio_path": row[5],
                "priority": row[6],
                "status": row[7],
                "due_date": row[8],
                "tags": json.loads(row[9]) if row[9] else []
            }
        return None
    
    def update_memo(self, memo_id: int, updates: Dict[str, Any]):
        """更新备忘录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ["memo_title", "memo_content", "priority", "status", "due_date"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key == "tags":
                set_clauses.append("tags = ?")
                values.append(json.dumps(value))
        
        if set_clauses:
            values.append(datetime.now().isoformat())
            values.append(memo_id)
            
            query = f"UPDATE memos SET {', '.join(set_clauses)}, updated_at = ? WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def delete_memo(self, memo_id: int):
        """删除备忘录（软删除）"""
        self.update_memo(memo_id, {"status": "deleted"})
    
    def archive_memo(self, memo_id: int):
        """归档备忘录"""
        self.update_memo(memo_id, {"status": "archived"})
    
    def search_memos(self, user_id: str, keyword: str) -> List[Dict[str, Any]]:
        """搜索备忘录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, memo_type, memo_title, memo_content, priority, created_at
            FROM memos
            WHERE user_id = ? AND status = 'active'
            AND (memo_title LIKE ? OR memo_content LIKE ?)
            ORDER BY priority DESC, created_at DESC
        """, (user_id, f"%{keyword}%", f"%{keyword}%"))
        
        memos = []
        for row in cursor.fetchall():
            memos.append({
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "content": row[3],
                "priority": row[4],
                "created_at": row[5]
            })
        
        conn.close()
        return memos

