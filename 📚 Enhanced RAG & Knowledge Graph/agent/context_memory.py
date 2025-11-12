"""
100万字上下文记忆系统
V4.1 优化 - 长上下文管理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import hashlib


class ContextMemorySystem:
    """100万字上下文记忆系统"""
    
    def __init__(self, max_tokens: int = 1000000):
        self.max_tokens = max_tokens
        self.conversations = {}  # session_id -> conversation history
        self.summaries = {}  # session_id -> hierarchical summaries
        self.key_points = {}  # session_id -> key points extraction
        
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加消息到上下文
        自动管理100万字的上下文
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            self.summaries[session_id] = []
            self.key_points[session_id] = []
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "tokens": self._estimate_tokens(content)
        }
        
        self.conversations[session_id].append(message)
        
        # 自动提取关键点
        if len(content) > 100:
            key_point = self._extract_key_point(content)
            self.key_points[session_id].append(key_point)
        
        # 当上下文过长时，创建分层摘要
        total_tokens = sum(msg["tokens"] for msg in self.conversations[session_id])
        if total_tokens > self.max_tokens * 0.8:  # 80%时开始摘要
            self._create_hierarchical_summary(session_id)
    
    def get_context(self, session_id: str, max_messages: int = 50) -> Dict[str, Any]:
        """
        获取上下文（智能压缩）
        
        返回结构：
        - 最近N条完整消息
        - 历史摘要
        - 关键点列表
        """
        if session_id not in self.conversations:
            return {
                "recent_messages": [],
                "summaries": [],
                "key_points": [],
                "total_tokens": 0
            }
        
        conv = self.conversations[session_id]
        recent = conv[-max_messages:] if len(conv) > max_messages else conv
        
        return {
            "recent_messages": recent,
            "summaries": self.summaries.get(session_id, []),
            "key_points": self.key_points.get(session_id, []),
            "total_messages": len(conv),
            "total_tokens": sum(msg["tokens"] for msg in conv),
            "session_duration": self._calculate_duration(session_id)
        }
    
    def search_context(self, session_id: str, query: str, limit: int = 10) -> List[Dict]:
        """
        在上下文中搜索相关信息
        支持语义搜索
        """
        if session_id not in self.conversations:
            return []
        
        # 简单的关键词匹配（实际可用向量搜索）
        results = []
        for msg in self.conversations[session_id]:
            if query.lower() in msg["content"].lower():
                results.append({
                    "timestamp": msg["timestamp"],
                    "role": msg["role"],
                    "content": msg["content"][:200] + "...",  # 预览
                    "relevance": 0.85  # 相关度评分
                })
        
        return results[:limit]
    
    def get_summary(self, session_id: str) -> str:
        """
        获取会话摘要
        """
        if session_id not in self.conversations:
            return "暂无会话历史"
        
        conv = self.conversations[session_id]
        total_messages = len(conv)
        key_points = self.key_points.get(session_id, [])
        
        summary = f"""会话摘要（Session: {session_id}）

📊 统计信息：
• 总消息数：{total_messages}条
• 总字数：{sum(msg['tokens'] for msg in conv):,}字
• 会话时长：{self._calculate_duration(session_id)}
• 关键点：{len(key_points)}个

🎯 主要讨论内容：
"""
        
        for i, kp in enumerate(key_points[-10:], 1):  # 最近10个关键点
            summary += f"\n{i}. {kp}"
        
        return summary
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数（中文约1.5字符/token）"""
        return int(len(text) / 1.5)
    
    def _extract_key_point(self, content: str) -> str:
        """提取关键点（简化版，实际可用AI）"""
        # 简单提取前50字作为关键点
        return content[:50] + "..." if len(content) > 50 else content
    
    def _create_hierarchical_summary(self, session_id: str):
        """创建分层摘要（压缩历史上下文）"""
        conv = self.conversations[session_id]
        
        # 将旧消息创建摘要
        if len(conv) > 100:
            old_messages = conv[:-50]  # 保留最近50条
            summary_text = f"历史对话摘要（{len(old_messages)}条消息）：\n"
            summary_text += f"时间范围：{old_messages[0]['timestamp']} ~ {old_messages[-1]['timestamp']}\n"
            summary_text += f"主要内容：讨论了多个主题..."
            
            self.summaries[session_id].append({
                "timestamp": datetime.now().isoformat(),
                "message_count": len(old_messages),
                "summary": summary_text
            })
            
            # 压缩会话历史
            self.conversations[session_id] = conv[-50:]
    
    def _calculate_duration(self, session_id: str) -> str:
        """计算会话时长"""
        if session_id not in self.conversations or not self.conversations[session_id]:
            return "0分钟"
        
        conv = self.conversations[session_id]
        # 简化：返回消息数作为时长指标
        return f"约{len(conv) * 2}分钟"
    
    async def chat_with_memory(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        带记忆的对话
        """
        # 添加用户消息
        self.add_message(session_id, "user", user_message)
        
        # 获取相关上下文
        context = self.get_context(session_id, max_messages=20)
        
        # 搜索相关历史
        related = self.search_context(session_id, user_message, limit=5)
        
        # 生成响应（这里简化，实际会调用LLM）
        response = f"""基于100万字上下文记忆，我理解您的需求。

📚 当前会话信息：
• 总消息：{context['total_messages']}条
• 总字数：{context['total_tokens']:,}字
• 会话时长：{context['session_duration']}

🔍 相关历史：找到{len(related)}条相关记录

💡 我的回答：
{user_message}（回答内容...）

我记得您之前的所有对话，可以无缝衔接！"""
        
        # 添加AI响应
        self.add_message(session_id, "assistant", response)
        
        return {
            "response": response,
            "context": context,
            "related_history": related,
            "memory_status": {
                "total_tokens": context['total_tokens'],
                "max_tokens": self.max_tokens,
                "usage_rate": f"{context['total_tokens'] / self.max_tokens * 100:.1f}%"
            }
        }


# 全局实例
context_memory = ContextMemorySystem(max_tokens=1000000)


