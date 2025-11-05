"""
Chat Message Handler
聊天消息处理器 - 处理OpenWebUI聊天消息

功能：
1. 自动保存聊天内容到RAG库
2. 从RAG库检索相关知识
3. 格式化消息用于RAG存储
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from rag_integration import get_rag_service
from network_info_handler import get_network_info_handler

logger = logging.getLogger(__name__)


class ChatMessageHandler:
    """
    聊天消息处理器
    
    处理OpenWebUI的聊天消息，自动保存到RAG库
    """

    def __init__(self, auto_save: bool = True, min_length: int = 10):
        """
        初始化聊天消息处理器
        
        Args:
            auto_save: 是否自动保存聊天内容
            min_length: 最小保存长度（字符数）
        """
        self.auto_save = auto_save
        self.min_length = min_length
        self.rag_service = get_rag_service()

    async def process_user_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            message: 用户消息内容
            user_id: 用户ID
            session_id: 会话ID
            metadata: 额外元数据
            
        Returns:
            处理结果字典
        """
        if not self.auto_save:
            return {"saved": False, "reason": "auto_save_disabled"}

        # 检查消息长度
        if len(message.strip()) < self.min_length:
            return {
                "saved": False,
                "reason": "message_too_short",
                "min_length": self.min_length,
            }

        try:
            # 格式化消息用于保存
            formatted_text = self._format_message_for_rag(
                message, user_id, session_id
            )

            # 生成文档ID
            doc_id = self._generate_doc_id(user_id, session_id)

            # 准备元数据
            doc_metadata = {
                "source": "openwebui_chat",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }

            # 保存到RAG库
            result = await self.rag_service.ingest_text(
                text=formatted_text,
                doc_id=doc_id,
                metadata=doc_metadata,
                save_index=True,
            )

            if result.get("success", False):
                logger.info(
                    f"用户消息已保存到RAG库: user={user_id}, session={session_id}"
                )
                return {
                    "saved": True,
                    "doc_id": result.get("ids", [doc_id])[0],
                    "size": result.get("size", 0),
                }
            else:
                logger.warning(f"保存用户消息失败: {result.get('error')}")
                return {"saved": False, "error": result.get("error")}

        except Exception as e:
            logger.error(f"处理用户消息时出错: {e}")
            return {"saved": False, "error": str(e)}

    async def process_assistant_message(
        self,
        message: str,
        user_message: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理助手消息（可选保存助手回答）
        
        Args:
            message: 助手消息内容
            user_message: 对应的用户消息（用于上下文）
            user_id: 用户ID
            session_id: 会话ID
            metadata: 额外元数据
            
        Returns:
            处理结果字典
        """
        # 默认不保存助手回答（可以根据需要启用）
        if not self.auto_save:
            return {"saved": False, "reason": "auto_save_disabled"}

        # 检查消息长度
        if len(message.strip()) < self.min_length:
            return {"saved": False, "reason": "message_too_short"}

        try:
            # 格式化消息（包含用户问题和助手回答）
            if user_message:
                formatted_text = f"问题: {user_message}\n\n回答: {message}"
            else:
                formatted_text = f"助手回答: {message}"

            # 生成文档ID
            doc_id = self._generate_doc_id(
                user_id, session_id, prefix="assistant"
            )

            # 准备元数据
            doc_metadata = {
                "source": "openwebui_chat_assistant",
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }

            # 保存到RAG库
            result = await self.rag_service.ingest_text(
                text=formatted_text,
                doc_id=doc_id,
                metadata=doc_metadata,
                save_index=True,
            )

            if result.get("success", False):
                logger.info(
                    f"助手消息已保存到RAG库: user={user_id}, session={session_id}"
                )
                return {
                    "saved": True,
                    "doc_id": result.get("ids", [doc_id])[0],
                }
            else:
                return {"saved": False, "error": result.get("error")}

        except Exception as e:
            logger.error(f"处理助手消息时出错: {e}")
            return {"saved": False, "error": str(e)}

    def _format_message_for_rag(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        格式化消息用于RAG存储
        
        Args:
            message: 原始消息
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            格式化后的文本
        """
        parts = []
        if user_id:
            parts.append(f"[用户: {user_id}]")
        if session_id:
            parts.append(f"[会话: {session_id}]")
        parts.append(message)
        return " ".join(parts)

    def _generate_doc_id(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        prefix: str = "chat",
    ) -> str:
        """
        生成文档ID
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            prefix: ID前缀
            
        Returns:
            文档ID
        """
        parts = [prefix]
        if user_id:
            parts.append(user_id)
        if session_id:
            parts.append(session_id)
        parts.append(uuid.uuid4().hex[:8])
        return "_".join(parts)

    async def search_relevant_context(
        self, query: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        搜索相关上下文（用于增强回答）
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            相关上下文列表
        """
        try:
            result = await self.rag_service.search(query, top_k=top_k)
            return result.get("items", [])
        except Exception as e:
            logger.error(f"搜索相关上下文失败: {e}")
            return []

    async def process_web_search_results(
        self,
        search_results: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理网络搜索结果（需求1.4）
        
        Args:
            search_results: 搜索结果列表
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            处理结果
        """
        try:
            network_handler = get_network_info_handler()
            result = await network_handler.process_web_search_results(
                search_results=search_results,
                user_id=user_id,
                session_id=session_id,
            )
            return result
        except Exception as e:
            logger.error(f"处理网络搜索结果失败: {e}")
            return {"saved": False, "error": str(e)}

    async def process_agent_info(
        self,
        agent_name: str,
        output: Any,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理智能体业务信息（需求1.4）
        
        Args:
            agent_name: 智能体名称
            output: 智能体输出
            task_id: 任务ID
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            处理结果
        """
        try:
            network_handler = get_network_info_handler()
            metadata = {
                "user_id": user_id,
                "session_id": session_id,
            }
            result = await network_handler.process_agent_info(
                agent_name=agent_name,
                output=output,
                task_id=task_id,
                metadata=metadata,
            )
            return result
        except Exception as e:
            logger.error(f"处理智能体信息失败: {e}")
            return {"saved": False, "error": str(e)}

