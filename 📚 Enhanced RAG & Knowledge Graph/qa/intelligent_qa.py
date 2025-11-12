"""
RAG智能问答系统
支持对话式检索、上下文理解、多轮对话
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """对话消息"""
    role: str  # user/assistant/system
    content: str
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """对话会话"""
    id: str
    messages: List[Message]
    context: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class QAResponse(BaseModel):
    """问答响应"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    context_used: List[str]
    reasoning: Optional[str] = None


class IntelligentQA:
    """
    智能问答系统
    
    功能：
    - 对话式检索
    - 多轮对话支持
    - 上下文理解
    - 答案生成和评分
    """
    
    def __init__(self):
        """初始化智能问答系统"""
        self.conversations: Dict[str, Conversation] = {}
        self.max_context_messages = 10
    
    def create_conversation(self, conversation_id: str) -> Conversation:
        """
        创建对话会话
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            会话对象
        """
        conversation = Conversation(
            id=conversation_id,
            messages=[],
            context={}
        )
        
        self.conversations[conversation_id] = conversation
        logger.info(f"创建对话会话: {conversation_id}")
        
        return conversation
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Message:
        """
        添加消息到对话
        
        Args:
            conversation_id: 会话ID
            role: 角色
            content: 内容
            metadata: 元数据
            
        Returns:
            消息对象
        """
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )
        
        conversation = self.conversations[conversation_id]
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # 保持上下文窗口大小
        if len(conversation.messages) > self.max_context_messages:
            conversation.messages = conversation.messages[-self.max_context_messages:]
        
        logger.debug(f"添加消息: {conversation_id} - {role}")
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话会话"""
        return self.conversations.get(conversation_id)
    
    def extract_intent(self, query: str, conversation: Conversation) -> Dict[str, Any]:
        """
        提取用户意图
        
        Args:
            query: 用户查询
            conversation: 对话上下文
            
        Returns:
            意图信息
        """
        # TODO: 使用NLP或LLM进行意图识别
        # 这里是简化实现
        
        intent = {
            "type": "search",  # search/question/chitchat
            "entities": [],
            "query_expansion": query
        }
        
        # 基于关键词的简单意图识别
        if any(word in query for word in ["是什么", "什么是", "定义"]):
            intent["type"] = "definition"
        elif any(word in query for word in ["怎么", "如何", "步骤"]):
            intent["type"] = "howto"
        elif any(word in query for word in ["为什么", "原因"]):
            intent["type"] = "reason"
        
        # 从上下文中提取相关信息
        if conversation.messages:
            recent_messages = conversation.messages[-3:]
            intent["context"] = [msg.content for msg in recent_messages]
        
        return intent
    
    def enhance_query_with_context(
        self,
        query: str,
        conversation: Conversation
    ) -> str:
        """
        使用上下文增强查询
        
        Args:
            query: 原始查询
            conversation: 对话上下文
            
        Returns:
            增强后的查询
        """
        if not conversation.messages:
            return query
        
        # 获取最近的消息作为上下文
        recent_messages = conversation.messages[-3:]
        context_texts = []
        
        for msg in recent_messages:
            if msg.role in ["user", "assistant"]:
                context_texts.append(msg.content)
        
        if context_texts:
            # 将上下文和当前查询组合
            enhanced = f"基于之前的对话：{' '.join(context_texts[-2:])}\n当前问题：{query}"
            return enhanced
        
        return query
    
    async def answer_question(
        self,
        conversation_id: str,
        query: str,
        use_context: bool = True
    ) -> QAResponse:
        """
        回答问题
        
        Args:
            conversation_id: 会话ID
            query: 用户问题
            use_context: 是否使用上下文
            
        Returns:
            问答响应
        """
        # 获取或创建对话
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            conversation = self.create_conversation(conversation_id)
        
        # 添加用户消息
        self.add_message(conversation_id, "user", query)
        
        # 提取意图
        intent = self.extract_intent(query, conversation)
        
        # 增强查询
        if use_context:
            enhanced_query = self.enhance_query_with_context(query, conversation)
        else:
            enhanced_query = query
        
        # TODO: 实际的检索和答案生成
        # from rag.core import semantic_search
        # sources = semantic_search(enhanced_query)
        # answer = generate_answer(query, sources, context)
        
        # 模拟响应
        answer = f"这是对'{query}'的回答"
        sources = []
        confidence = 0.85
        
        response = QAResponse(
            answer=answer,
            confidence=confidence,
            sources=sources,
            context_used=[msg.content for msg in conversation.messages[-3:-1]],
            reasoning="基于知识库检索和上下文理解生成答案"
        )
        
        # 添加助手回复
        self.add_message(conversation_id, "assistant", answer, metadata={
            "confidence": confidence,
            "sources_count": len(sources)
        })
        
        logger.info(f"回答问题: {query} (置信度: {confidence})")
        
        return response
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取对话摘要
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            对话摘要
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        user_messages = [m for m in conversation.messages if m.role == "user"]
        assistant_messages = [m for m in conversation.messages if m.role == "assistant"]
        
        summary = {
            "conversation_id": conversation_id,
            "message_count": len(conversation.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "duration_minutes": (
                conversation.updated_at - conversation.created_at
            ).total_seconds() / 60
        }
        
        return summary


# 全局实例
_qa_system: Optional[IntelligentQA] = None


def get_qa_system() -> IntelligentQA:
    """获取全局智能问答系统实例"""
    global _qa_system
    if _qa_system is None:
        _qa_system = IntelligentQA()
    return _qa_system


# 使用示例
async def example_usage():
    """使用示例"""
    
    qa = get_qa_system()
    
    # 1. 创建对话
    conv_id = "conv_123"
    
    # 2. 多轮问答
    response1 = await qa.answer_question(conv_id, "什么是人工智能？")
    print(f"Q1: 什么是人工智能？")
    print(f"A1: {response1.answer}\n")
    
    response2 = await qa.answer_question(conv_id, "它有哪些应用场景？")
    print(f"Q2: 它有哪些应用场景？")
    print(f"A2: {response2.answer}")
    print(f"使用的上下文: {response2.context_used}\n")
    
    # 3. 查看对话摘要
    summary = qa.get_conversation_summary(conv_id)
    print(f"对话摘要: {summary}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())


















