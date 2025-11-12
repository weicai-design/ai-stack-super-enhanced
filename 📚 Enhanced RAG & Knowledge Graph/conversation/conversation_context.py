"""
多轮对话上下文管理
Conversation Context Manager

功能：
1. 对话历史记录
2. 上下文关联分析
3. 智能上下文截断
4. 跨会话持久化

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class Message:
    """对话消息"""
    
    def __init__(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        message_id: Optional[str] = None
    ):
        """
        初始化消息
        
        Args:
            role: 角色（'user' 或 'assistant'）
            content: 消息内容
            metadata: 元数据（sources, quality_score等）
            timestamp: 时间戳
            message_id: 消息ID
        """
        self.message_id = message_id or str(uuid4())
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """从字典创建"""
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            role=data["role"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            message_id=data.get("message_id")
        )


class ConversationContext:
    """
    对话上下文管理器
    
    功能：
    - 管理对话历史
    - 智能上下文截断
    - 相关历史检索
    - 上下文统计分析
    """
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        max_history: int = 20,
        max_tokens: int = 4000
    ):
        """
        初始化对话上下文
        
        Args:
            conversation_id: 对话ID（如果为None则自动生成）
            max_history: 最大历史消息数
            max_tokens: 最大token数（用于截断）
        """
        self.conversation_id = conversation_id or str(uuid4())
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.history: List[Message] = []
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message_count": 0,
            "user_id": None
        }
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        添加消息到上下文
        
        Args:
            role: 角色（'user' 或 'assistant'）
            content: 消息内容
            metadata: 元数据
            
        Returns:
            创建的消息对象
        """
        if role not in ["user", "assistant"]:
            raise ValueError(f"无效的角色: {role}，必须是'user'或'assistant'")
        
        message = Message(role=role, content=content, metadata=metadata)
        self.history.append(message)
        
        # 更新元数据
        self.metadata["message_count"] = len(self.history)
        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # 自动截断
        if len(self.history) > self.max_history:
            self._truncate_history()
        
        logger.debug(f"添加消息: {role}, 长度: {len(content)}")
        
        return message
    
    def get_history(
        self,
        limit: Optional[int] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            limit: 限制返回的消息数
            include_metadata: 是否包含元数据
            
        Returns:
            消息列表
        """
        history = self.history[-limit:] if limit else self.history
        
        if include_metadata:
            return [msg.to_dict() for msg in history]
        else:
            return [
                {"role": msg.role, "content": msg.content}
                for msg in history
            ]
    
    def get_relevant_history(
        self,
        query: str,
        k: int = 5,
        min_relevance: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        获取与查询相关的历史消息
        
        Args:
            query: 查询内容
            k: 返回的最大消息数
            min_relevance: 最小相关度阈值
            
        Returns:
            相关消息列表（按相关度排序）
        """
        if not self.history:
            return []
        
        # 简单实现：基于关键词匹配计算相关度
        # TODO: 在v2.6.1中使用语义相似度
        relevant_messages = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for msg in self.history:
            if msg.role == "assistant":  # 只考虑助手的回答
                content_lower = msg.content.lower()
                content_words = set(content_lower.split())
                
                # 计算Jaccard相似度
                intersection = len(query_words & content_words)
                union = len(query_words | content_words)
                relevance = intersection / union if union > 0 else 0
                
                if relevance >= min_relevance:
                    msg_dict = msg.to_dict()
                    msg_dict["relevance"] = relevance
                    relevant_messages.append(msg_dict)
        
        # 按相关度排序并返回前k个
        relevant_messages.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant_messages[:k]
    
    def _truncate_history(self):
        """智能截断历史（保留最近的消息）"""
        if len(self.history) > self.max_history:
            # 保留最近的max_history条消息
            removed_count = len(self.history) - self.max_history
            self.history = self.history[-self.max_history:]
            logger.info(f"截断历史: 删除{removed_count}条旧消息")
    
    def clear_history(self):
        """清空历史"""
        self.history.clear()
        self.metadata["message_count"] = 0
        self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"清空对话历史: {self.conversation_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        user_messages = [m for m in self.history if m.role == "user"]
        assistant_messages = [m for m in self.history if m.role == "assistant"]
        
        total_content_length = sum(len(m.content) for m in self.history)
        avg_message_length = total_content_length / len(self.history) if self.history else 0
        
        return {
            "conversation_id": self.conversation_id,
            "total_messages": len(self.history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_message_length": round(avg_message_length, 2),
            "created_at": self.metadata["created_at"],
            "updated_at": self.metadata["updated_at"]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return {
            "conversation_id": self.conversation_id,
            "history": [msg.to_dict() for msg in self.history],
            "metadata": self.metadata,
            "max_history": self.max_history,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationContext:
        """从字典导入"""
        context = cls(
            conversation_id=data["conversation_id"],
            max_history=data.get("max_history", 20),
            max_tokens=data.get("max_tokens", 4000)
        )
        context.history = [Message.from_dict(m) for m in data.get("history", [])]
        context.metadata = data.get("metadata", {})
        return context
    
    def save_to_file(self, file_path: Path):
        """保存到文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"对话上下文已保存: {file_path}")
        except Exception as e:
            logger.error(f"保存对话上下文失败: {e}")
            raise
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> ConversationContext:
        """从文件加载"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            context = cls.from_dict(data)
            logger.info(f"对话上下文已加载: {file_path}")
            return context
        except Exception as e:
            logger.error(f"加载对话上下文失败: {e}")
            raise


class ConversationManager:
    """
    对话管理器
    
    管理多个对话上下文，提供统一接口
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        初始化对话管理器
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = storage_dir or (Path.cwd() / "data" / "conversations")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations: Dict[str, ConversationContext] = {}
    
    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ConversationContext:
        """
        创建新对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            对话上下文对象
        """
        context = ConversationContext(conversation_id=conversation_id)
        if user_id:
            context.metadata["user_id"] = user_id
        
        self.conversations[context.conversation_id] = context
        logger.info(f"创建新对话: {context.conversation_id}")
        
        return context
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        获取对话上下文
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话上下文对象或None
        """
        # 先从内存查找
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # 尝试从文件加载
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            try:
                context = ConversationContext.load_from_file(file_path)
                self.conversations[conversation_id] = context
                return context
            except Exception as e:
                logger.error(f"加载对话失败: {e}")
        
        return None
    
    def save_conversation(self, conversation_id: str) -> bool:
        """
        保存对话到文件
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功
        """
        context = self.conversations.get(conversation_id)
        if not context:
            logger.warning(f"对话不存在: {conversation_id}")
            return False
        
        try:
            file_path = self.storage_dir / f"{conversation_id}.json"
            context.save_to_file(file_path)
            return True
        except Exception as e:
            logger.error(f"保存对话失败: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功
        """
        # 从内存删除
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        
        # 从文件删除
        file_path = self.storage_dir / f"{conversation_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"删除对话: {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"删除对话失败: {e}")
                return False
        
        return True
    
    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        列出对话
        
        Args:
            user_id: 用户ID（过滤）
            limit: 最大数量
            
        Returns:
            对话列表
        """
        conversations = []
        
        # 从文件系统加载
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 用户ID过滤
                if user_id and data.get("metadata", {}).get("user_id") != user_id:
                    continue
                
                conversations.append({
                    "conversation_id": data["conversation_id"],
                    "message_count": len(data.get("history", [])),
                    "created_at": data.get("metadata", {}).get("created_at"),
                    "updated_at": data.get("metadata", {}).get("updated_at"),
                    "user_id": data.get("metadata", {}).get("user_id")
                })
            except Exception as e:
                logger.warning(f"加载对话文件失败 {file_path}: {e}")
                continue
        
        # 按更新时间排序
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return conversations[:limit]


# 全局对话管理器实例
default_conversation_manager = ConversationManager()


# ==================== 便捷函数 ====================

def create_conversation(
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> ConversationContext:
    """创建新对话"""
    return default_conversation_manager.create_conversation(
        conversation_id=conversation_id,
        user_id=user_id
    )


def get_conversation(conversation_id: str) -> Optional[ConversationContext]:
    """获取对话上下文"""
    return default_conversation_manager.get_conversation(conversation_id)


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Message]:
    """添加消息到对话"""
    context = get_conversation(conversation_id)
    if context:
        return context.add_message(role, content, metadata)
    return None


def save_conversation(conversation_id: str) -> bool:
    """保存对话"""
    return default_conversation_manager.save_conversation(conversation_id)

