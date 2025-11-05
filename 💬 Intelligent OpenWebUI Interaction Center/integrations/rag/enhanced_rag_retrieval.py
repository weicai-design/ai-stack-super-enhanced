"""
Enhanced RAG Retrieval for OpenWebUI
增强的RAG检索功能

根据需求1.5: open webui聊天、各种智能体也会检索、利用RAG库的知识、信息、数据

增强功能：
1. 智能检索策略
2. 上下文感知检索
3. 多轮对话检索优化
4. 检索结果融合
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 添加路径以导入查询增强模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "📚 Enhanced RAG & Knowledge Graph"))

from rag_integration import get_rag_service

# 尝试导入查询增强模块
try:
    from core.query_enhancement import get_query_enhancer, QueryEnhancer
    QUERY_ENHANCEMENT_AVAILABLE = True
except ImportError:
    try:
        # 尝试相对导入
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "📚 Enhanced RAG & Knowledge Graph"))
        from core.query_enhancement import get_query_enhancer, QueryEnhancer
        QUERY_ENHANCEMENT_AVAILABLE = True
    except ImportError:
        QUERY_ENHANCEMENT_AVAILABLE = False
        QueryEnhancer = None
        logger.warning("查询增强模块不可用，将使用基础检索")

logger = logging.getLogger(__name__)


class EnhancedRAGRetrieval:
    """
    增强的RAG检索器
    
    提供更智能的检索策略，更好地利用RAG库知识
    """

    def __init__(
        self,
        default_top_k: int = 5,
        max_context_length: int = 2000,
        use_reranking: bool = True,
        use_query_enhancement: bool = True,
    ):
        """
        初始化增强检索器
        
        Args:
            default_top_k: 默认检索数量
            max_context_length: 最大上下文长度
            use_reranking: 是否使用重排序
            use_query_enhancement: 是否使用查询增强
        """
        self.default_top_k = default_top_k
        self.max_context_length = max_context_length
        self.use_reranking = use_reranking
        self.use_query_enhancement = use_query_enhancement and QUERY_ENHANCEMENT_AVAILABLE
        self.rag_service = get_rag_service()
        
        # 初始化查询增强器
        if self.use_query_enhancement:
            self.query_enhancer = get_query_enhancer()
        else:
            self.query_enhancer = None

    async def retrieve_for_response(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        为回答检索相关知识（需求1.5）
        
        Args:
            user_query: 用户查询
            conversation_history: 对话历史
            top_k: 检索数量
            
        Returns:
            检索结果，包含知识片段和上下文
        """
        top_k = top_k or self.default_top_k

        try:
            # 0. 查询增强（如果启用）
            enhanced_query = user_query
            query_intent = None
            expanded_queries = [user_query]
            
            if self.use_query_enhancement and self.query_enhancer:
                # 分析查询意图
                query_intent = self.query_enhancer.analyze_intent(user_query)
                
                # 扩展查询（同义词和相关词）
                expanded_queries = self.query_enhancer.expand_query(user_query, max_expansions=3)
                
                # 重写查询（根据意图优化）
                enhanced_query = self.query_enhancer.rewrite_query(user_query, query_intent)
                
                logger.debug(f"查询增强: 原始='{user_query}', 增强='{enhanced_query}', 意图={query_intent.intent_type}")
            
            # 1. 基础检索（使用增强后的查询）
            base_results = await self.rag_service.search(
                query=enhanced_query, top_k=top_k * 2  # 检索更多以便后续处理
            )
            items = base_results.get("items", [])
            
            # 使用扩展查询进行补充检索
            if len(expanded_queries) > 1:
                for expanded_query in expanded_queries[1:]:  # 跳过原始查询
                    try:
                        expanded_results = await self.rag_service.search(
                            query=expanded_query, top_k=top_k
                        )
                        expanded_items = expanded_results.get("items", [])
                        items.extend(expanded_items)
                    except Exception as e:
                        logger.warning(f"扩展查询检索失败: {e}")

            # 2. 上下文感知检索（如果有对话历史）
            contextual_items = []
            if conversation_history and len(conversation_history) > 0:
                # 从对话历史中提取关键词进行检索
                contextual_query = self._extract_contextual_query(
                    user_query, conversation_history
                )
                if contextual_query:
                    contextual_results = await self.rag_service.search(
                        query=contextual_query, top_k=top_k
                    )
                    contextual_items = contextual_results.get("items", [])

            # 3. 合并和去重
            all_items = self._merge_and_deduplicate(items, contextual_items)

            # 4. 重排序（如果启用）
            if self.use_reranking:
                all_items = self._rerank_results(all_items, enhanced_query)

            # 5. 结果多样性保证（如果启用查询增强）
            if self.use_query_enhancement and self.query_enhancer:
                all_items = self.query_enhancer.ensure_diversity(all_items, max_similarity=0.7)

            # 6. 限制数量并构建上下文
            selected_items = all_items[:top_k]
            context = self._build_context(selected_items)

            return {
                "knowledge_items": selected_items,
                "context": context,
                "item_count": len(selected_items),
                "total_found": len(all_items),
                "retrieval_method": "enhanced",
            }

        except Exception as e:
            logger.error(f"增强检索失败: {e}")
            return {
                "knowledge_items": [],
                "context": "",
                "item_count": 0,
                "error": str(e),
            }

    async def retrieve_for_agent(
        self,
        agent_name: str,
        task_description: str,
        current_context: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        为智能体检索相关知识（需求1.5）
        
        Args:
            agent_name: 智能体名称
            task_description: 任务描述
            current_context: 当前上下文
            top_k: 检索数量
            
        Returns:
            检索结果
        """
        try:
            # 构建检索查询（结合智能体名称和任务）
            query = f"{agent_name} {task_description}"
            if current_context:
                query = f"{query} {current_context}"

            # 检索
            results = await self.rag_service.search(query=query, top_k=top_k)

            items = results.get("items", [])

            # 构建上下文
            context = self._build_context(items)

            return {
                "knowledge_items": items,
                "context": context,
                "item_count": len(items),
                "agent_name": agent_name,
                "task": task_description,
            }

        except Exception as e:
            logger.error(f"智能体检索失败: {e}")
            return {
                "knowledge_items": [],
                "context": "",
                "item_count": 0,
                "error": str(e),
            }

    def _extract_contextual_query(
        self, current_query: str, history: List[Dict[str, str]]
    ) -> Optional[str]:
        """
        从对话历史中提取上下文查询
        
        Args:
            current_query: 当前查询
            history: 对话历史
            
        Returns:
            上下文查询字符串
        """
        if not history:
            return None

        # 提取最近几轮对话的关键词
        recent_queries = []
        for msg in history[-3:]:  # 最近3轮
            if "user" in msg and msg["user"]:
                recent_queries.append(msg["user"])

        if not recent_queries:
            return None

        # 简单组合（可以优化为更智能的提取）
        return " ".join(recent_queries[-2:])  # 最近2个用户查询

    def _merge_and_deduplicate(
        self, items1: List[Dict[str, Any]], items2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并和去重检索结果
        
        Args:
            items1: 第一组结果
            items2: 第二组结果
            
        Returns:
            合并去重后的结果
        """
        seen_ids = set()
        merged = []

        # 按相似度排序合并
        all_items = items1 + items2
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        for item in all_items:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                merged.append(item)

        return merged

    def _rerank_results(
        self, items: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        重排序检索结果
        
        Args:
            items: 检索结果
            query: 查询
            
        Returns:
            重排序后的结果
        """
        # 简单重排序：基于分数和长度
        # 可以优化为使用专门的reranking模型
        for item in items:
            score = item.get("score", 0.0)
            snippet = item.get("snippet", "")
            
            # 长度归一化（偏好中等长度）
            length_factor = 1.0
            if len(snippet) < 50:
                length_factor = 0.9  # 太短
            elif len(snippet) > 1000:
                length_factor = 0.95  # 太长
            
            # 查询关键词匹配奖励
            query_words = set(query.lower().split())
            snippet_words = set(snippet.lower().split())
            overlap = len(query_words & snippet_words)
            keyword_bonus = min(0.1, overlap * 0.02)  # 最多10%奖励
            
            # 调整分数
            item["adjusted_score"] = score * length_factor + keyword_bonus

        # 按调整后的分数排序
        items.sort(key=lambda x: x.get("adjusted_score", x.get("score", 0)), reverse=True)

        return items

    def _build_context(self, items: List[Dict[str, Any]]) -> str:
        """
        构建检索到的知识上下文
        
        Args:
            items: 检索结果列表
            
        Returns:
            格式化的上下文文本
        """
        if not items:
            return ""

        parts = []
        current_length = 0

        for i, item in enumerate(items, 1):
            snippet = item.get("snippet", "")
            if not snippet:
                continue

            # 限制总长度
            if current_length + len(snippet) > self.max_context_length:
                break

            # 格式化
            source = item.get("path", "RAG库")
            parts.append(f"\n[{i}] {snippet}")
            if source:
                parts.append(f"    来源: {source}")

            current_length += len(snippet)

        return "\n".join(parts) if parts else ""


class RAGRetrievalOrchestrator:
    """
    RAG检索协调器
    
    统一管理各种检索需求
    """

    def __init__(self):
        self.retriever = EnhancedRAGRetrieval()

    async def get_knowledge_for_response(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        获取用于回答的知识（需求1.5）
        
        Args:
            user_query: 用户查询
            conversation_history: 对话历史
            
        Returns:
            知识上下文字符串
        """
        result = await self.retriever.retrieve_for_response(
            user_query=user_query,
            conversation_history=conversation_history,
        )

        return result.get("context", "")

    async def get_knowledge_for_agent(
        self,
        agent_name: str,
        task_description: str,
        current_context: Optional[str] = None,
    ) -> str:
        """
        获取用于智能体的知识（需求1.5）
        
        Args:
            agent_name: 智能体名称
            task_description: 任务描述
            current_context: 当前上下文
            
        Returns:
            知识上下文字符串
        """
        result = await self.retriever.retrieve_for_agent(
            agent_name=agent_name,
            task_description=task_description,
            current_context=current_context,
        )

        return result.get("context", "")


# 全局实例
_retrieval_orchestrator: Optional[RAGRetrievalOrchestrator] = None


def get_rag_retrieval_orchestrator() -> RAGRetrievalOrchestrator:
    """获取RAG检索协调器实例（单例）"""
    global _retrieval_orchestrator
    if _retrieval_orchestrator is None:
        _retrieval_orchestrator = RAGRetrievalOrchestrator()
    return _retrieval_orchestrator

