"""
Self-RAG Implementation
Self-RAG实现

实现业界最先进的Self-RAG技术：
1. 自我评估检索结果相关性
2. 自主决定是否需要更多检索
3. 动态调整检索策略
4. 基于评估的迭代检索
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class RetrievalDecision(Enum):
    """检索决策"""
    RETRIEVE = "retrieve"  # 需要检索
    SKIP = "skip"  # 跳过检索
    ITERATE = "iterate"  # 迭代检索（需要更多信息）


class RelevanceLevel(Enum):
    """相关性级别"""
    HIGHLY_RELEVANT = "highly_relevant"  # 高度相关
    RELEVANT = "relevant"  # 相关
    PARTIALLY_RELEVANT = "partially_relevant"  # 部分相关
    IRRELEVANT = "irrelevant"  # 不相关


@dataclass
class RetrievalAssessment:
    """检索评估结果"""
    decision: RetrievalDecision
    relevance_level: RelevanceLevel
    confidence: float  # 评估置信度（0-1）
    reasoning: str  # 决策理由
    needs_more_info: bool  # 是否需要更多信息
    suggested_query: Optional[str] = None  # 建议的查询（用于迭代检索）


@dataclass
class SelfRAGState:
    """Self-RAG状态"""
    iteration_count: int = 0
    max_iterations: int = 3
    retrieved_documents: List[Dict[str, Any]] = field(default_factory=list)
    assessments: List[RetrievalAssessment] = field(default_factory=list)
    final_context: str = ""


class SelfRAG:
    """
    Self-RAG系统
    
    实现自我评估和迭代检索机制
    """

    def __init__(
        self,
        rag_retriever: Any = None,
        enable_self_assessment: bool = True,
        enable_iterative_retrieval: bool = True,
        max_iterations: int = 3,
        relevance_threshold: float = 0.7,
    ):
        """
        初始化Self-RAG
        
        Args:
            rag_retriever: RAG检索器实例
            enable_self_assessment: 是否启用自我评估
            enable_iterative_retrieval: 是否启用迭代检索
            max_iterations: 最大迭代次数
            relevance_threshold: 相关性阈值
        """
        self.rag_retriever = rag_retriever
        self.enable_self_assessment = enable_self_assessment
        self.enable_iterative_retrieval = enable_iterative_retrieval
        self.max_iterations = max_iterations
        self.relevance_threshold = relevance_threshold

    async def retrieve_with_assessment(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        带自我评估的检索
        
        Args:
            query: 用户查询
            context: 上下文信息（可选）
            top_k: 初始检索数量
            
        Returns:
            包含检索结果和评估信息的字典
        """
        state = SelfRAGState(max_iterations=self.max_iterations)
        
        # 第一阶段：初始检索决策
        assessment = await self._assess_retrieval_need(query, context)
        state.assessments.append(assessment)
        
        if assessment.decision == RetrievalDecision.SKIP:
            # 不需要检索
            return {
                "documents": [],
                "context": context or "",
                "iterations": state.iteration_count,
                "assessments": [a.decision.value for a in state.assessments],
            }
        
        # 第二阶段：执行检索
        while state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            
            # 确定检索查询
            retrieval_query = query
            if assessment.suggested_query:
                retrieval_query = assessment.suggested_query
            
            # 执行检索
            documents = await self._execute_retrieval(
                retrieval_query,
                top_k=top_k,
            )
            
            # 评估检索结果
            assessment = await self._assess_retrieval_results(
                query, documents, context
            )
            state.assessments.append(assessment)
            
            # 合并文档（去重）
            for doc in documents:
                doc_id = doc.get("id") or doc.get("document_id", "")
                if not any(d.get("id") == doc_id or d.get("document_id") == doc_id 
                           for d in state.retrieved_documents):
                    state.retrieved_documents.append(doc)
            
            # 判断是否需要继续迭代
            if not self.enable_iterative_retrieval:
                break
            
            if assessment.decision != RetrievalDecision.ITERATE:
                break
            
            # 如果相关性不够，尝试改进查询
            if assessment.needs_more_info and assessment.suggested_query:
                query = assessment.suggested_query
                logger.debug(f"迭代检索 {state.iteration_count}: 使用改进查询 '{query}'")
        
        # 构建最终上下文
        state.final_context = self._build_final_context(
            state.retrieved_documents, context
        )
        
        return {
            "documents": state.retrieved_documents,
            "context": state.final_context,
            "iterations": state.iteration_count,
            "assessments": [a.decision.value for a in state.assessments],
            "relevance_level": assessment.relevance_level.value,
            "confidence": assessment.confidence,
        }

    async def _assess_retrieval_need(
        self,
        query: str,
        context: Optional[str],
    ) -> RetrievalAssessment:
        """
        评估是否需要检索
        
        Args:
            query: 查询文本
            context: 现有上下文
            
        Returns:
            检索评估结果
        """
        # 如果已有丰富上下文，可能不需要检索
        if context and len(context) > 500:
            # 检查上下文是否包含查询相关信息
            query_words = set(query.lower().split())
            context_words = set(context.lower().split())
            overlap = len(query_words & context_words) / max(len(query_words), 1)
            
            if overlap > 0.5:
                return RetrievalAssessment(
                    decision=RetrievalDecision.SKIP,
                    relevance_level=RelevanceLevel.RELEVANT,
                    confidence=0.7,
                    reasoning="现有上下文已包含相关信息",
                    needs_more_info=False,
                )
        
        # 需要检索
        return RetrievalAssessment(
            decision=RetrievalDecision.RETRIEVE,
            relevance_level=RelevanceLevel.PARTIALLY_RELEVANT,
            confidence=0.8,
            reasoning="需要从知识库检索相关信息",
            needs_more_info=True,
        )

    async def _execute_retrieval(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        执行检索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        if not self.rag_retriever:
            return []
        
        try:
            # 调用检索器
            if hasattr(self.rag_retriever, "retrieve_for_response"):
                result = await self.rag_retriever.retrieve_for_response(
                    user_query=query,
                    top_k=top_k,
                )
                return result.get("knowledge_items", [])
            elif hasattr(self.rag_retriever, "search"):
                result = await self.rag_retriever.search(
                    query=query,
                    top_k=top_k,
                )
                return result.get("items", [])
            else:
                logger.warning("检索器不支持检索方法")
                return []
        except Exception as e:
            logger.error(f"检索执行失败: {e}")
            return []

    async def _assess_retrieval_results(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        context: Optional[str],
    ) -> RetrievalAssessment:
        """
        评估检索结果的相关性
        
        Args:
            query: 原始查询
            documents: 检索到的文档
            context: 现有上下文
            
        Returns:
            检索评估结果
        """
        if not documents:
            # 没有检索到文档，需要改进查询
            return RetrievalAssessment(
                decision=RetrievalDecision.ITERATE,
                relevance_level=RelevanceLevel.IRRELEVANT,
                confidence=0.9,
                reasoning="未检索到相关文档，需要改进查询",
                needs_more_info=True,
                suggested_query=self._suggest_improved_query(query),
            )
        
        # 评估文档相关性
        relevance_scores = []
        for doc in documents:
            score = doc.get("score", 0.0)
            relevance_scores.append(score)
        
        avg_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        max_score = max(relevance_scores) if relevance_scores else 0.0
        
        # 判断相关性级别
        if max_score >= 0.8 and avg_score >= self.relevance_threshold:
            relevance_level = RelevanceLevel.HIGHLY_RELEVANT
            decision = RetrievalDecision.RETRIEVE  # 已经足够，不需要继续
            needs_more = False
        elif avg_score >= self.relevance_threshold:
            relevance_level = RelevanceLevel.RELEVANT
            decision = RetrievalDecision.RETRIEVE
            needs_more = False
        elif avg_score >= 0.5:
            relevance_level = RelevanceLevel.PARTIALLY_RELEVANT
            decision = RetrievalDecision.ITERATE if self.enable_iterative_retrieval else RetrievalDecision.RETRIEVE
            needs_more = True
        else:
            relevance_level = RelevanceLevel.IRRELEVANT
            decision = RetrievalDecision.ITERATE
            needs_more = True
        
        # 生成建议查询
        suggested_query = None
        if needs_more:
            suggested_query = self._suggest_improved_query(query, documents)
        
        return RetrievalAssessment(
            decision=decision,
            relevance_level=relevance_level,
            confidence=min(1.0, avg_score * 1.2),  # 基于平均分数估算置信度
            reasoning=f"平均相关性分数: {avg_score:.2f}, 最高分数: {max_score:.2f}",
            needs_more_info=needs_more,
            suggested_query=suggested_query,
        )

    def _suggest_improved_query(
        self,
        query: str,
        documents: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        建议改进的查询
        
        Args:
            query: 原始查询
            documents: 检索到的文档（可选）
            
        Returns:
            改进后的查询
        """
        # 简单策略：提取查询中的关键词，添加相关术语
        query_words = query.lower().split()
        
        # 如果文档存在，尝试从中提取相关术语
        if documents:
            # 从文档中提取高频词（简单实现）
            all_text = " ".join([
                str(doc.get("snippet", doc.get("content", ""))).lower()
                for doc in documents[:3]
            ])
            text_words = all_text.split()
            
            # 找到与查询词相关但不完全相同的词
            related_terms = []
            for word in text_words:
                if word not in query_words and len(word) > 3:
                    if word not in related_terms:
                        related_terms.append(word)
                        if len(related_terms) >= 3:
                            break
            
            if related_terms:
                improved_query = f"{query} {' '.join(related_terms[:2])}"
                return improved_query
        
        # 回退：直接返回原始查询
        return query

    def _build_final_context(
        self,
        documents: List[Dict[str, Any]],
        existing_context: Optional[str],
    ) -> str:
        """
        构建最终上下文
        
        Args:
            documents: 检索到的文档
            existing_context: 现有上下文
            
        Returns:
            构建的上下文字符串
        """
        context_parts = []
        
        if existing_context:
            context_parts.append(existing_context)
        
        # 添加检索到的文档
        for i, doc in enumerate(documents[:5], 1):  # 最多5个文档
            content = doc.get("snippet") or doc.get("content", "")
            if content:
                context_parts.append(f"[文档{i}]: {content}")
        
        return "\n\n".join(context_parts)


# 全局Self-RAG实例
_global_self_rag: Optional[SelfRAG] = None


def get_self_rag(rag_retriever: Any = None) -> SelfRAG:
    """
    获取Self-RAG实例（单例模式）
    
    Args:
        rag_retriever: RAG检索器实例
        
    Returns:
        SelfRAG实例
    """
    global _global_self_rag
    
    if _global_self_rag is None:
        _global_self_rag = SelfRAG(rag_retriever=rag_retriever)
    
    return _global_self_rag

