"""
Knowledge Enhancer
知识增强器 - 使用RAG知识增强OpenWebUI回答

功能：
1. 从RAG库检索相关知识
2. 将知识注入到AI回答中
3. 提供上下文相关的增强回答
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from .rag_integration import get_rag_service
    from .enhanced_rag_retrieval import get_rag_retrieval_orchestrator
except ImportError:
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from rag_integration import get_rag_service
    from enhanced_rag_retrieval import get_rag_retrieval_orchestrator

logger = logging.getLogger(__name__)


class KnowledgeEnhancer:
    """
    知识增强器
    
    使用RAG库中的知识增强AI回答
    """

    def __init__(
        self,
        enable_enhancement: bool = True,
        top_k: int = 3,
        similarity_threshold: float = 0.5,
        use_enhanced_retrieval: bool = True,
    ):
        """
        初始化知识增强器
        
        Args:
            enable_enhancement: 是否启用知识增强
            top_k: 检索的知识片段数量
            similarity_threshold: 相似度阈值
            use_enhanced_retrieval: 是否使用增强检索（需求1.5）
        """
        self.enable_enhancement = enable_enhancement
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.use_enhanced_retrieval = use_enhanced_retrieval
        self.rag_service = get_rag_service()
        
        # 增强检索器（需求1.5）
        if use_enhanced_retrieval:
            try:
                self.retrieval_orchestrator = get_rag_retrieval_orchestrator()
            except Exception:
                self.retrieval_orchestrator = None
                logger.warning("增强检索器初始化失败，使用基础检索")
        else:
            self.retrieval_orchestrator = None

    async def enhance_response(
        self,
        user_query: str,
        original_response: Optional[str] = None,
        use_context: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        增强AI回答（通过检索相关知识，需求1.5）
        
        Args:
            user_query: 用户查询
            original_response: 原始AI回答（可选）
            use_context: 是否使用检索到的上下文
            conversation_history: 对话历史（用于上下文感知检索）
            
        Returns:
            增强后的结果字典，包含：
            - enhanced_response: 增强后的回答
            - knowledge_snippets: 检索到的知识片段
            - has_knowledge: 是否找到了相关知识
        """
        if not self.enable_enhancement:
            return {
                "enhanced_response": original_response or "",
                "knowledge_snippets": [],
                "has_knowledge": False,
            }

        try:
            # 使用增强检索（需求1.5）
            if self.use_enhanced_retrieval and self.retrieval_orchestrator:
                retrieval_result = await self.retrieval_orchestrator.retriever.retrieve_for_response(
                    user_query=user_query,
                    conversation_history=conversation_history,
                    top_k=self.top_k,
                )
                knowledge_items = retrieval_result.get("knowledge_items", [])
                enhanced_context = retrieval_result.get("context", "")
            else:
                # 回退到基础检索
                search_result = await self.rag_service.search(
                    query=user_query, top_k=self.top_k
                )
                knowledge_items = search_result.get("items", [])
                enhanced_context = ""

            # 过滤低相似度结果
            filtered_items = [
                item
                for item in knowledge_items
                if item.get("score", 0) >= self.similarity_threshold
            ]

            if not filtered_items:
                return {
                    "enhanced_response": original_response or "",
                    "knowledge_snippets": [],
                    "has_knowledge": False,
                    "message": "未找到相关知识",
                }

            # 格式化知识片段
            knowledge_snippets = [
                {
                    "text": item.get("snippet", "")[:200],
                    "score": item.get("score", 0),
                    "source": item.get("path", "RAG库"),
                }
                for item in filtered_items
            ]

            # 构建增强后的回答
            if use_context and original_response:
                # 如果使用了增强检索，优先使用enhanced_context
                if enhanced_context:
                    enhanced_response = self._build_enhanced_response(
                        original_response, knowledge_snippets, enhanced_context
                    )
                else:
                    enhanced_response = self._build_enhanced_response(
                        original_response, knowledge_snippets
                    )
            elif use_context:
                # 如果没有原始回答，直接使用检索到的知识
                if enhanced_context:
                    enhanced_response = enhanced_context
                else:
                    enhanced_response = self._build_response_from_knowledge(
                        knowledge_snippets
                    )
            else:
                enhanced_response = original_response or ""

            return {
                "enhanced_response": enhanced_response,
                "knowledge_snippets": knowledge_snippets,
                "has_knowledge": True,
                "knowledge_count": len(knowledge_snippets),
            }

        except Exception as e:
            logger.error(f"知识增强失败: {e}")
            return {
                "enhanced_response": original_response or "",
                "knowledge_snippets": [],
                "has_knowledge": False,
                "error": str(e),
            }

    def _build_enhanced_response(
        self,
        original_response: str,
        knowledge_snippets: List[Dict[str, Any]],
        enhanced_context: Optional[str] = None,
    ) -> str:
        """
        构建增强后的回答（结合原始回答和知识）
        
        Args:
            original_response: 原始回答
            knowledge_snippets: 知识片段列表
            enhanced_context: 增强的上下文（如果使用增强检索）
            
        Returns:
            增强后的回答文本
        """
        # 优先使用增强的上下文
        if enhanced_context:
            parts = [original_response]
            parts.append("\n\n--- 相关知识参考 ---\n")
            parts.append(enhanced_context)
            return "\n".join(parts)

        if not knowledge_snippets:
            return original_response

        # 提取知识文本
        knowledge_texts = [
            snippet["text"] for snippet in knowledge_snippets if snippet["text"]
        ]

        # 构建增强回答（简单示例，可以根据需要优化）
        parts = [original_response]
        if knowledge_texts:
            parts.append("\n\n--- 相关知识参考 ---\n")
            for i, text in enumerate(knowledge_texts, 1):
                parts.append(f"\n{i}. {text}...")

        return "\n".join(parts)

    def _build_response_from_knowledge(
        self, knowledge_snippets: List[Dict[str, Any]]
    ) -> str:
        """
        从知识片段构建回答
        
        Args:
            knowledge_snippets: 知识片段列表
            
        Returns:
            基于知识构建的回答文本
        """
        if not knowledge_snippets:
            return "抱歉，未找到相关信息。"

        texts = [
            snippet["text"]
            for snippet in knowledge_snippets
            if snippet.get("text")
        ]

        response = "根据知识库中的信息：\n\n"
        for i, text in enumerate(texts, 1):
            response += f"{i}. {text}\n\n"

        return response

    async def get_related_entities(
        self, query: str
    ) -> Dict[str, List[str]]:
        """
        获取查询相关的实体（从知识图谱）
        
        Args:
            query: 查询文本
            
        Returns:
            包含相关实体的字典（email, url, phone等）
        """
        try:
            # 先搜索获取相关文档
            search_result = await self.rag_service.search(query, top_k=5)
            items = search_result.get("items", [])

            # 获取知识图谱快照
            kg_snapshot = await self.rag_service.get_kg_snapshot()
            if not kg_snapshot.get("success"):
                return {}

            # 提取实体
            entities = {}
            sample = kg_snapshot.get("sample", {})
            if "emails" in sample:
                entities["emails"] = sample["emails"]
            if "urls" in sample:
                entities["urls"] = sample["urls"]

            return entities

        except Exception as e:
            logger.error(f"获取相关实体失败: {e}")
            return {}

