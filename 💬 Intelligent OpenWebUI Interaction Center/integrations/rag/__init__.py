"""
OpenWebUI RAG Integration Module
OpenWebUI与RAG系统深度集成模块

功能：
1. 聊天内容自动保存到RAG库
2. 从RAG库检索知识增强回答
3. 文件上传自动处理
4. 知识图谱查询
5. 网络信息自动保存（需求1.4）
6. 智能体信息自动保存（需求1.4）
7. 增强的RAG检索（需求1.5）
"""

from .rag_integration import RAGIntegrationService, get_rag_service
from .chat_handler import ChatMessageHandler
from .file_upload_handler import FileUploadHandler
from .knowledge_enhancer import KnowledgeEnhancer
from .network_info_handler import get_network_info_handler, NetworkInfoHandler
from .enhanced_rag_retrieval import (
    get_rag_retrieval_orchestrator,
    RAGRetrievalOrchestrator,
    EnhancedRAGRetrieval,
)

__all__ = [
    "RAGIntegrationService",
    "get_rag_service",
    "ChatMessageHandler",
    "FileUploadHandler",
    "KnowledgeEnhancer",
    "get_network_info_handler",
    "NetworkInfoHandler",
    "get_rag_retrieval_orchestrator",
    "RAGRetrievalOrchestrator",
    "EnhancedRAGRetrieval",
]

__version__ = "1.1.0"
