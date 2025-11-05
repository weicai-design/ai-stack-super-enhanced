"""
智能提醒模块
基于历史对话内容提供智能提醒
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re


class SmartReminder:
    """智能提醒系统"""
    
    def __init__(self, db_path: str = "smart_reminders.db"):
        self.db_path = db_path
        self.init_database()
        
        # 提醒关键词模式
        self.reminder_patterns = {
            "time": [
                r"明天|后天|下周|下个月|([0-9]+)点|([0-9]+)号",
                r"周[一二三四五六日]|星期[一二三四五六日天]",
                r"\d{1,2}:\d{2}|\d{1,2}点"
            ],
            "task": [
                r"记住|提醒|别忘了|不要忘记|一定要",
                r"需要|要做|计划|安排|准备"
            ],
            "event": [
                r"会议|开会|约|见面|活动|聚会|生日",
                r"面试|考试|deadline|截止"
            ]
        }
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 提醒表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source_message TEXT,
                due_time DATETIME,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                triggered_at DATETIME,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_status 
            ON reminders(user_id, status, due_time)
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ 智能提醒数据库初始化完成: {self.db_path}")
    
    def extract_reminders_from_message(
        self, 
        user_id: str,
        session_id: str,
        message: str
    ) -> List[Dict[str, Any]]:
        """
        从消息中提取可能的提醒
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 消息内容
        
        Returns:
            提醒列表
        """
        reminders = []
        
        # 检测是否包含提醒关键词
        has_time = any(
            re.search(pattern, message, re.IGNORECASE) 
            for pattern in self.reminder_patterns["time"]
        )
        has_task = any(
            re.search(pattern, message, re.IGNORECASE) 
            for pattern in self.reminder_patterns["task"]
        )
        has_event = any(
            re.search(pattern, message, re.IGNORECASE) 
            for pattern in self.reminder_patterns["event"]
        )
        
        # 如果包含提醒特征，创建提醒
        if (has_time and has_task) or (has_time and has_event) or (has_task and has_event):
            reminder = {
                "user_id": user_id,
                "session_id": session_id,
                "reminder_type": self._determine_type(message),
                "content": self._extract_reminder_content(message),
                "source_message": message,
                "due_time": self._extract_time(message),
                "priority": self._calculate_priority(message),
                "metadata": {
                    "has_time": has_time,
                    "has_task": has_task,
                    "has_event": has_event
                }
            }
            reminders.append(reminder)
        
        return reminders
    
    def _determine_type(self, message: str) -> str:
        """确定提醒类型"""
        event_keywords = ["会议", "开会", "约", "见面", "活动", "生日", "面试", "考试"]
        task_keywords = ["做", "完成", "准备", "提交", "检查"]
        deadline_keywords = ["截止", "deadline", "最后期限"]
        
        msg_lower = message.lower()
        
        if any(kw in message for kw in event_keywords):
            return "event"
        elif any(kw in msg_lower for kw in deadline_keywords):
            return "deadline"
        elif any(kw in message for kw in task_keywords):
            return "task"
        else:
            return "general"
    
    def _extract_reminder_content(self, message: str) -> str:
        """提取提醒内容"""
        # 简化：直接返回原消息，实际应用可以做更智能的提取
        # 去除"记住"、"提醒我"等前缀
        content = message
        
        prefixes = ["记住", "提醒我", "别忘了", "不要忘记", "一定要"]
        for prefix in prefixes:
            if message.startswith(prefix):
                content = message[len(prefix):].strip("，。、")
                break
        
        return content[:200]  # 限制长度
    
    def _extract_time(self, message: str) -> Optional[str]:
        """提取时间信息"""
        now = datetime.now()
        
        # 明天
        if "明天" in message:
            due_time = now + timedelta(days=1)
            # 尝试提取具体时间
            time_match = re.search(r'(\d{1,2})[点:](\d{0,2})', message)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                due_time = due_time.replace(hour=hour, minute=minute, second=0)
            else:
                due_time = due_time.replace(hour=9, minute=0, second=0)  # 默认早上9点
            return due_time.isoformat()
        
        # 后天
        elif "后天" in message:
            due_time = now + timedelta(days=2)
            due_time = due_time.replace(hour=9, minute=0, second=0)
            return due_time.isoformat()
        
        # 下周
        elif "下周" in message:
            due_time = now + timedelta(days=7)
            due_time = due_time.replace(hour=9, minute=0, second=0)
            return due_time.isoformat()
        
        # 具体日期（如"5号"）
        date_match = re.search(r'(\d{1,2})号', message)
        if date_match:
            day = int(date_match.group(1))
            due_time = now.replace(day=day, hour=9, minute=0, second=0)
            if due_time < now:
                # 如果日期已过，则为下个月
                if now.month == 12:
                    due_time = due_time.replace(year=now.year + 1, month=1)
                else:
                    due_time = due_time.replace(month=now.month + 1)
            return due_time.isoformat()
        
        # 默认：1小时后
        return (now + timedelta(hours=1)).isoformat()
    
    def _calculate_priority(self, message: str) -> int:
        """计算优先级（1-5，5最高）"""
        high_priority_keywords = ["紧急", "重要", "必须", "务必", "一定", "马上", "立即"]
        medium_priority_keywords = ["尽快", "早点", "尽量"]
        
        msg_lower = message.lower()
        
        if any(kw in message for kw in high_priority_keywords):
            return 5
        elif any(kw in message for kw in medium_priority_keywords):
            return 3
        else:
            return 2
    
    def save_reminder(self, reminder: Dict[str, Any]) -> int:
        """保存提醒"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders 
            (user_id, session_id, reminder_type, content, source_message, 
             due_time, priority, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reminder['user_id'],
            reminder['session_id'],
            reminder['reminder_type'],
            reminder['content'],
            reminder.get('source_message'),
            reminder.get('due_time'),
            reminder.get('priority', 1),
            json.dumps(reminder.get('metadata', {}), ensure_ascii=False)
        ))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return reminder_id
    
    def get_active_reminders(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取活跃的提醒"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, session_id, reminder_type, content,
                   source_message, due_time, priority, status, created_at, metadata
            FROM reminders
            WHERE user_id = ? AND status = 'active'
            ORDER BY due_time ASC, priority DESC
            LIMIT ?
        """, (user_id, limit))
        
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                "id": row[0],
                "user_id": row[1],
                "session_id": row[2],
                "reminder_type": row[3],
                "content": row[4],
                "source_message": row[5],
                "due_time": row[6],
                "priority": row[7],
                "status": row[8],
                "created_at": row[9],
                "metadata": json.loads(row[10]) if row[10] else {}
            })
        
        conn.close()
        return reminders
    
    def get_due_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """获取到期的提醒"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            SELECT id, user_id, session_id, reminder_type, content,
                   source_message, due_time, priority, status, created_at, metadata
            FROM reminders
            WHERE user_id = ? AND status = 'active' AND due_time <= ?
            ORDER BY priority DESC, due_time ASC
        """, (user_id, now))
        
        reminders = []
        for row in cursor.fetchall():
            reminders.append({
                "id": row[0],
                "user_id": row[1],
                "session_id": row[2],
                "reminder_type": row[3],
                "content": row[4],
                "source_message": row[5],
                "due_time": row[6],
                "priority": row[7],
                "status": row[8],
                "created_at": row[9],
                "metadata": json.loads(row[10]) if row[10] else {}
            })
        
        conn.close()
        return reminders
    
    def mark_as_completed(self, reminder_id: int):
        """标记提醒为已完成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reminders
            SET status = 'completed', triggered_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reminder_id,))
        
        conn.commit()
        conn.close()
    
    def mark_as_dismissed(self, reminder_id: int):
        """标记提醒为已忽略"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reminders
            SET status = 'dismissed', triggered_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reminder_id,))
        
        conn.commit()
        conn.close()
    
    def get_reminder_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取提醒统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总提醒数
        cursor.execute("""
            SELECT COUNT(*) FROM reminders WHERE user_id = ?
        """, (user_id,))
        total = cursor.fetchone()[0]
        
        # 活跃提醒数
        cursor.execute("""
            SELECT COUNT(*) FROM reminders WHERE user_id = ? AND status = 'active'
        """, (user_id,))
        active = cursor.fetchone()[0]
        
        # 已完成提醒数
        cursor.execute("""
            SELECT COUNT(*) FROM reminders WHERE user_id = ? AND status = 'completed'
        """, (user_id,))
        completed = cursor.fetchone()[0]
        
        # 到期提醒数
        now = datetime.now().isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM reminders 
            WHERE user_id = ? AND status = 'active' AND due_time <= ?
        """, (user_id, now))
        due = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "due": due,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }


# 全局实例
smart_reminder = SmartReminder()

