"""
用户行为学习模块
自动学习用户的使用习惯、偏好和工作模式
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any
import json


class UserBehaviorLearning:
    """用户行为学习系统"""
    
    def __init__(self, db_path: str = "user_behavior.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化用户行为数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户偏好表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                update_count INTEGER DEFAULT 1
            )
        """)
        
        # 使用模式表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 工作习惯表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                habit_type TEXT NOT NULL,
                habit_description TEXT,
                time_pattern TEXT,
                frequency INTEGER DEFAULT 1,
                last_observed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 用户行为历史
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_data TEXT,
                context TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ 用户行为学习数据库初始化完成: {self.db_path}")
    
    def record_behavior(self, user_id: str, action_type: str, action_data: Dict[str, Any], context: str = ""):
        """记录用户行为"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO behavior_history (user_id, action_type, action_data, context, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, action_type, json.dumps(action_data), context, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def learn_from_chat(self, user_id: str, message: str, response: str, metadata: Dict[str, Any]):
        """从聊天中学习用户偏好"""
        # 记录行为
        self.record_behavior(user_id, "chat", {
            "message": message,
            "model_used": metadata.get("model_used"),
            "detected_system": metadata.get("detected_system")
        })
        
        # 学习模型偏好
        if metadata.get("model_used"):
            self._update_preference(user_id, "preferred_model", metadata["model_used"])
        
        # 学习使用的功能
        if metadata.get("detected_system"):
            self._update_pattern(user_id, "frequently_used_system", metadata["detected_system"])
    
    def learn_from_file_upload(self, user_id: str, filename: str, file_type: str):
        """从文件上传学习用户偏好"""
        self.record_behavior(user_id, "file_upload", {
            "filename": filename,
            "file_type": file_type
        })
        
        self._update_pattern(user_id, "file_type_preference", file_type)
    
    def learn_work_schedule(self, user_id: str):
        """学习用户工作时间模式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最近的行为记录
        cursor.execute("""
            SELECT timestamp FROM behavior_history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (user_id,))
        
        timestamps = cursor.fetchall()
        
        if timestamps:
            # 分析时间模式
            hours = [datetime.fromisoformat(t[0]).hour for t in timestamps]
            most_active_hour = max(set(hours), key=hours.count)
            
            self._update_habit(user_id, "active_hours", f"{most_active_hour}:00-{most_active_hour+1}:00")
        
        conn.close()
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        profile = {
            "user_id": user_id,
            "preferences": {},
            "patterns": {},
            "habits": {}
        }
        
        # 获取偏好
        cursor.execute("""
            SELECT preference_type, preference_value, confidence
            FROM user_preferences
            WHERE user_id = ?
            ORDER BY confidence DESC
        """, (user_id,))
        
        for row in cursor.fetchall():
            profile["preferences"][row[0]] = {
                "value": row[1],
                "confidence": row[2]
            }
        
        # 获取使用模式
        cursor.execute("""
            SELECT pattern_type, pattern_data, frequency
            FROM usage_patterns
            WHERE user_id = ?
            ORDER BY frequency DESC
            LIMIT 10
        """, (user_id,))
        
        for row in cursor.fetchall():
            profile["patterns"][row[0]] = {
                "data": row[1],
                "frequency": row[2]
            }
        
        # 获取工作习惯
        cursor.execute("""
            SELECT habit_type, habit_description, time_pattern
            FROM work_habits
            WHERE user_id = ?
        """, (user_id,))
        
        for row in cursor.fetchall():
            profile["habits"][row[0]] = {
                "description": row[1],
                "time_pattern": row[2]
            }
        
        conn.close()
        return profile
    
    def _update_preference(self, user_id: str, pref_type: str, pref_value: str):
        """更新用户偏好"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否存在
        cursor.execute("""
            SELECT id, confidence, update_count FROM user_preferences
            WHERE user_id = ? AND preference_type = ? AND preference_value = ?
        """, (user_id, pref_type, pref_value))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新已有偏好
            new_confidence = min(1.0, existing[1] + 0.1)
            new_count = existing[2] + 1
            
            cursor.execute("""
                UPDATE user_preferences
                SET confidence = ?, update_count = ?, last_updated = ?
                WHERE id = ?
            """, (new_confidence, new_count, datetime.now().isoformat(), existing[0]))
        else:
            # 插入新偏好
            cursor.execute("""
                INSERT INTO user_preferences (user_id, preference_type, preference_value, confidence)
                VALUES (?, ?, ?, 0.5)
            """, (user_id, pref_type, pref_value))
        
        conn.commit()
        conn.close()
    
    def _update_pattern(self, user_id: str, pattern_type: str, pattern_data: str):
        """更新使用模式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, frequency FROM usage_patterns
            WHERE user_id = ? AND pattern_type = ? AND pattern_data = ?
        """, (user_id, pattern_type, pattern_data))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE usage_patterns
                SET frequency = ?, last_seen = ?
                WHERE id = ?
            """, (existing[1] + 1, datetime.now().isoformat(), existing[0]))
        else:
            cursor.execute("""
                INSERT INTO usage_patterns (user_id, pattern_type, pattern_data)
                VALUES (?, ?, ?)
            """, (user_id, pattern_type, pattern_data))
        
        conn.commit()
        conn.close()
    
    def _update_habit(self, user_id: str, habit_type: str, habit_description: str):
        """更新工作习惯"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM work_habits
            WHERE user_id = ? AND habit_type = ?
        """, (user_id, habit_type))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE work_habits
                SET habit_description = ?, last_observed = ?
                WHERE id = ?
            """, (habit_description, datetime.now().isoformat(), existing[0]))
        else:
            cursor.execute("""
                INSERT INTO work_habits (user_id, habit_type, habit_description)
                VALUES (?, ?, ?)
            """, (user_id, habit_type, habit_description))
        
        conn.commit()
        conn.close()

