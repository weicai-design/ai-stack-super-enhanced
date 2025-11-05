"""
OpenWebUI Plugin
OpenWebUI插件主入口

集成OpenWebUI的自定义功能：
1. 聊天消息钩子
2. 文件上传钩子
3. 知识增强钩子
"""

import logging
from typing import Dict, Any, Optional

from chat_handler import ChatMessageHandler
from file_upload_handler import FileUploadHandler
from knowledge_enhancer import KnowledgeEnhancer
from network_info_handler import get_network_info_handler

logger = logging.getLogger(__name__)

# 初始化组件（延迟初始化）
_chat_handler: Optional[ChatMessageHandler] = None
_file_handler: Optional[FileUploadHandler] = None
_knowledge_enhancer: Optional[KnowledgeEnhancer] = None


def get_chat_handler() -> ChatMessageHandler:
    """获取聊天消息处理器实例（单例）"""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatMessageHandler(auto_save=True, min_length=10)
    return _chat_handler


def get_file_handler() -> FileUploadHandler:
    """获取文件上传处理器实例（单例）"""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileUploadHandler(auto_process=True)
    return _file_handler


def get_knowledge_enhancer() -> KnowledgeEnhancer:
    """获取知识增强器实例（单例）"""
    global _knowledge_enhancer
    if _knowledge_enhancer is None:
        _knowledge_enhancer = KnowledgeEnhancer(
            enable_enhancement=True, top_k=3, similarity_threshold=0.5
        )
    return _knowledge_enhancer


# OpenWebUI钩子函数（需要根据OpenWebUI的插件API调整）

async def on_user_message(
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    OpenWebUI用户消息钩子
    
    当用户发送消息时调用，自动保存到RAG库
    
    Args:
        message: 用户消息
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        handler = get_chat_handler()
        result = await handler.process_user_message(
            message=message,
            user_id=user_id,
            session_id=session_id,
            metadata=kwargs,
        )
        return result
    except Exception as e:
        logger.error(f"处理用户消息钩子失败: {e}")
        return {"error": str(e)}


async def on_assistant_message(
    message: str,
    user_message: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    OpenWebUI助手消息钩子
    
    当助手回复消息时调用（可选保存）
    
    Args:
        message: 助手消息
        user_message: 对应的用户消息
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        handler = get_chat_handler()
        result = await handler.process_assistant_message(
            message=message,
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            metadata=kwargs,
        )
        return result
    except Exception as e:
        logger.error(f"处理助手消息钩子失败: {e}")
        return {"error": str(e)}


async def on_file_upload(
    file_path: str,
    filename: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    OpenWebUI文件上传钩子
    
    当用户上传文件时调用，自动处理并摄入RAG库
    
    Args:
        file_path: 文件路径
        filename: 文件名
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        handler = get_file_handler()
        result = await handler.process_uploaded_file(
            file_path=file_path,
            filename=filename,
            user_id=user_id,
            session_id=session_id,
            metadata=kwargs,
        )
        return result
    except Exception as e:
        logger.error(f"处理文件上传钩子失败: {e}")
        return {"error": str(e)}


async def enhance_response(
    user_query: str,
    original_response: Optional[str] = None,
    use_context: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    增强AI回答（在生成回答后调用）
    
    Args:
        user_query: 用户查询
        original_response: 原始AI回答
        use_context: 是否使用检索到的上下文
        **kwargs: 其他参数
        
    Returns:
        增强后的回答
    """
    try:
        enhancer = get_knowledge_enhancer()
        result = await enhancer.enhance_response(
            user_query=user_query,
            original_response=original_response,
            use_context=use_context,
        )
        return result
    except Exception as e:
        logger.error(f"知识增强失败: {e}")
        return {
            "enhanced_response": original_response or "",
            "error": str(e),
        }


async def on_web_search_results(
    search_results: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    OpenWebUI网络搜索结果钩子（需求1.4）
    
    当OpenWebUI进行网络搜索时调用，自动保存搜索结果到RAG库
    
    Args:
        search_results: 搜索结果列表
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        handler = get_chat_handler()
        result = await handler.process_web_search_results(
            search_results=search_results,
            user_id=user_id,
            session_id=session_id,
        )
        return result
    except Exception as e:
        logger.error(f"处理网络搜索结果钩子失败: {e}")
        return {"error": str(e)}


async def on_agent_output(
    agent_name: str,
    output: Any,
    task_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    OpenWebUI智能体输出钩子（需求1.4）
    
    当智能体产生输出时调用，自动保存到RAG库
    
    Args:
        agent_name: 智能体名称
        output: 智能体输出
        task_id: 任务ID
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        处理结果
    """
    try:
        handler = get_chat_handler()
        result = await handler.process_agent_info(
            agent_name=agent_name,
            output=output,
            task_id=task_id,
            user_id=user_id,
            session_id=session_id,
        )
        return result
    except Exception as e:
        logger.error(f"处理智能体输出钩子失败: {e}")
        return {"error": str(e)}


# 插件配置
PLUGIN_CONFIG = {
    "name": "RAG Integration",
    "version": "1.0.0",
    "description": "RAG系统深度集成，自动保存聊天内容和文件到知识库",
    "hooks": {
        "on_user_message": on_user_message,
        "on_assistant_message": on_assistant_message,
        "on_file_upload": on_file_upload,
        "enhance_response": enhance_response,
        "on_web_search_results": on_web_search_results,  # 需求1.4
        "on_agent_output": on_agent_output,  # 需求1.4
    },
}

