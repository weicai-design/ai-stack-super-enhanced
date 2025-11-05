"""
上下文记忆管理模块
支持100万字级别的对话上下文记忆
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import hashlib
import re


class ContextMemoryManager:
    """
    上下文记忆管理器 - 支持100万字长期记忆
    
    功能：
    1. 存储完整对话历史
    2. 智能检索相关上下文
    3. 会话摘要和压缩
    4. 多会话管理
    """
    
    def __init__(self, db_path: str = "context_memory.db"):
        self.db_path = db_path
        self.init_database()
        print(f"✅ 上下文记忆管理器初始化完成: {db_path}")
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT,
                metadata TEXT,
                word_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON conversation_history(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON conversation_history(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON conversation_history(timestamp)")
        
        # 会话摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                key_topics TEXT,
                total_messages INTEGER DEFAULT 0,
                total_words INTEGER DEFAULT 0,
                start_time DATETIME,
                last_active DATETIME,
                metadata TEXT
            )
        """)
        
        # 上下文关键信息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_keyinfo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                key_type TEXT,
                key_content TEXT,
                importance_score REAL DEFAULT 0.5,
                reference_count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_referenced DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_message(
        self, 
        session_id: str, 
        user_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        保存单条消息到对话历史
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 元数据
        
        Returns:
            消息ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算内容哈希（用于去重）
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # 统计字数
        word_count = len(content)
        
        cursor.execute("""
            INSERT INTO conversation_history 
            (session_id, user_id, role, content, content_hash, metadata, word_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            user_id,
            role,
            content,
            content_hash,
            json.dumps(metadata or {}, ensure_ascii=False),
            word_count
        ))
        
        message_id = cursor.lastrowid
        
        # 更新会话摘要
        self._update_session_summary(cursor, session_id, user_id, word_count)
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def _update_session_summary(
        self, 
        cursor: sqlite3.Cursor, 
        session_id: str, 
        user_id: str,
        word_count: int
    ):
        """更新会话摘要统计"""
        cursor.execute("""
            INSERT INTO session_summary 
            (session_id, user_id, total_messages, total_words, start_time, last_active)
            VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                total_messages = total_messages + 1,
                total_words = total_words + ?,
                last_active = CURRENT_TIMESTAMP
        """, (session_id, user_id, word_count, word_count))
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            limit: 返回条数
            offset: 偏移量
        
        Returns:
            消息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, role, content, metadata, word_count, timestamp
            FROM conversation_history
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (session_id, limit, offset))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "word_count": row[4],
                "timestamp": row[5]
            })
        
        conn.close()
        
        # 返回时间正序（最早的在前）
        return list(reversed(messages))
    
    def get_recent_context(
        self,
        session_id: str,
        max_words: int = 10000
    ) -> str:
        """
        获取最近的对话上下文（滑动窗口）
        
        Args:
            session_id: 会话ID
            max_words: 最大字数
        
        Returns:
            格式化的上下文字符串
        """
        messages = self.get_conversation_history(session_id, limit=100)
        
        context_parts = []
        total_words = 0
        
        # 从最新的消息开始累加
        for msg in reversed(messages):
            if total_words + msg["word_count"] > max_words:
                break
            
            role_label = "用户" if msg["role"] == "user" else "AI助手"
            context_parts.insert(0, f"{role_label}: {msg['content']}")
            total_words += msg["word_count"]
        
        return "\n\n".join(context_parts)
    
    def search_relevant_context(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        time_window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        搜索相关的历史对话上下文
        
        Args:
            session_id: 会话ID
            query: 查询内容
            top_k: 返回数量
            time_window_days: 时间窗口（天）
        
        Returns:
            相关消息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算时间范围
        time_threshold = (datetime.now() - timedelta(days=time_window_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 提取查询关键词
        keywords = self._extract_keywords(query)
        
        if not keywords:
            return []
        
        # 构建搜索条件（简单的关键词匹配）
        keyword_conditions = " OR ".join([f"content LIKE '%{kw}%'" for kw in keywords])
        
        cursor.execute(f"""
            SELECT id, role, content, metadata, word_count, timestamp
            FROM conversation_history
            WHERE session_id = ?
            AND timestamp >= ?
            AND ({keyword_conditions})
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, time_threshold, top_k))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "word_count": row[4],
                "timestamp": row[5]
            })
        
        conn.close()
        return results
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """提取关键词"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词（简单按空格和中文字符分）
        words = text.split()
        
        # 过滤停用词和短词
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
        
        return keywords[:max_keywords]
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, user_id, title, summary, key_topics, 
                   total_messages, total_words, start_time, last_active
            FROM session_summary
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "session_id": row[0],
            "user_id": row[1],
            "title": row[2],
            "summary": row[3],
            "key_topics": json.loads(row[4]) if row[4] else [],
            "total_messages": row[5],
            "total_words": row[6],
            "start_time": row[7],
            "last_active": row[8]
        }
    
    def generate_session_summary(self, session_id: str, ai_summary: Optional[str] = None) -> str:
        """
        生成或更新会话摘要
        
        Args:
            session_id: 会话ID
            ai_summary: AI生成的摘要（可选）
        
        Returns:
            摘要文本
        """
        messages = self.get_conversation_history(session_id, limit=100)
        
        if not messages:
            return "空会话"
        
        # 提取关键主题
        all_content = " ".join([msg["content"] for msg in messages])
        keywords = self._extract_keywords(all_content, max_keywords=10)
        
        # 生成标题（基于第一条用户消息）
        first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "新会话")
        title = first_user_msg[:50] + ("..." if len(first_user_msg) > 50 else "")
        
        # 使用AI摘要或生成简单摘要
        if ai_summary:
            summary = ai_summary
        else:
            summary = f"讨论了 {len(keywords)} 个主题：{', '.join(keywords[:5])}"
        
        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE session_summary
            SET title = ?, summary = ?, key_topics = ?
            WHERE session_id = ?
        """, (title, summary, json.dumps(keywords, ensure_ascii=False), session_id))
        
        conn.commit()
        conn.close()
        
        return summary
    
    def build_full_context(
        self,
        session_id: str,
        current_query: str,
        max_total_words: int = 50000
    ) -> Dict[str, Any]:
        """
        构建完整上下文（智能组合）
        
        Args:
            session_id: 会话ID
            current_query: 当前查询
            max_total_words: 最大总字数
        
        Returns:
            包含各种上下文的字典
        """
        # 1. 获取会话摘要
        summary = self.get_session_summary(session_id)
        
        # 2. 获取最近对话（占50%空间）
        recent_context = self.get_recent_context(session_id, max_words=max_total_words // 2)
        
        # 3. 搜索相关历史对话（占30%空间）
        relevant_messages = self.search_relevant_context(session_id, current_query, top_k=10)
        relevant_context = self._format_messages(relevant_messages, max_words=max_total_words * 3 // 10)
        
        # 4. 统计信息
        total_words_used = len(recent_context) + len(relevant_context)
        
        return {
            "session_summary": summary,
            "recent_context": recent_context,
            "relevant_context": relevant_context,
            "total_words_used": total_words_used,
            "context_capacity": max_total_words,
            "usage_percentage": (total_words_used / max_total_words * 100) if max_total_words > 0 else 0
        }
    
    def _format_messages(self, messages: List[Dict], max_words: int) -> str:
        """格式化消息列表"""
        parts = []
        total_words = 0
        
        for msg in messages:
            if total_words + msg["word_count"] > max_words:
                break
            
            role_label = "用户" if msg["role"] == "user" else "AI助手"
            time_str = msg["timestamp"][:16]  # YYYY-MM-DD HH:MM
            parts.append(f"[{time_str}] {role_label}: {msg['content']}")
            total_words += msg["word_count"]
        
        return "\n\n".join(parts)
    
    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, title, summary, total_messages, total_words,
                   start_time, last_active
            FROM session_summary
            WHERE user_id = ?
            ORDER BY last_active DESC
            LIMIT ?
        """, (user_id, limit))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "title": row[1] or "无标题会话",
                "summary": row[2],
                "total_messages": row[3],
                "total_words": row[4],
                "start_time": row[5],
                "last_active": row[6]
            })
        
        conn.close()
        return sessions
    
    def save_key_info(
        self,
        session_id: str,
        user_id: str,
        key_type: str,
        key_content: str,
        importance_score: float = 0.5
    ):
        """保存关键信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO context_keyinfo
            (session_id, user_id, key_type, key_content, importance_score)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_id, key_type, key_content, importance_score))
        
        conn.commit()
        conn.close()
    
    def get_context_stats(self, session_id: str) -> Dict[str, Any]:
        """获取上下文统计信息"""
        summary = self.get_session_summary(session_id)
        
        if not summary:
            return {
                "total_messages": 0,
                "total_words": 0,
                "capacity_used_mb": 0,
                "estimated_capacity": "0 / 100万字"
            }
        
        total_words = summary["total_words"]
        capacity_mb = total_words * 2 / 1024 / 1024  # 估算存储大小（UTF-8平均2字节/字）
        
        return {
            "total_messages": summary["total_messages"],
            "total_words": total_words,
            "capacity_used_mb": round(capacity_mb, 2),
            "estimated_capacity": f"{total_words:,} / 1,000,000字",
            "usage_percentage": round(total_words / 1000000 * 100, 2)
        }

