"""
上下文感知检索器
负责基于查询上下文和用户意图进行智能检索，提供精准的相关信息
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """检索策略"""

    SEMANTIC = "semantic"  # 语义检索
    KEYWORD = "keyword"  # 关键词检索
    HYBRID = "hybrid"  # 混合检索
    CONTEXTUAL = "contextual"  # 上下文检索


class IntentType(Enum):
    """用户意图类型"""

    FACT_QUERY = "fact_query"  # 事实查询
    COMPARISON = "comparison"  # 比较查询
    ANALYSIS = "analysis"  # 分析查询
    RECOMMENDATION = "recommendation"  # 推荐查询
    EXPLANATION = "explanation"  # 解释查询


@dataclass
class RetrievalContext:
    """检索上下文"""

    user_id: str
    session_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    temporal_context: datetime
    geographic_context: Optional[str]


@dataclass
class RetrievalResult:
    """检索结果"""

    document_id: str
    content: str
    relevance_score: float
    confidence: float
    retrieval_strategy: RetrievalStrategy
    context_matches: List[str]
    metadata: Dict[str, Any]


@dataclass
class IntentAnalysis:
    """意图分析结果"""

    intent_type: IntentType
    confidence: float
    key_entities: List[str]
    key_concepts: List[str]
    expected_answer_type: str


class ContextAwareRetriever:
    """上下文感知检索器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vector_store = None  # 应该从外部注入
        self.knowledge_graph = None  # 应该从外部注入

        # 检索配置
        self.max_results = config.get("max_results", 10)
        self.min_relevance = config.get("min_relevance", 0.3)
        self.context_weight = config.get("context_weight", 0.4)
        self.recency_decay_days = config.get("recency_decay_days", 30)

        # 意图识别模式
        self.intent_patterns = self._initialize_intent_patterns()

        # 会话缓存
        self.session_cache: Dict[str, List[RetrievalResult]] = {}

        logger.info("上下文感知检索器初始化完成")

    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """初始化意图识别模式"""
        return {
            IntentType.FACT_QUERY: [
                r"什么是.*",
                r".*是什么",
                r"谁发明了.*",
                r".*的定义",
                r"何时.*",
            ],
            IntentType.COMPARISON: [
                r".*与.*的区别",
                r".*和.*哪个更好",
                r"比较.*和.*",
                r".*vs.*",
            ],
            IntentType.ANALYSIS: [
                r"分析.*",
                r".*的原因",
                r"为什么.*",
                r".*的影响",
                r"如何.*",
            ],
            IntentType.RECOMMENDATION: [
                r"推荐.*",
                r"应该选择.*",
                r".*建议",
                r"最好的.*",
            ],
            IntentType.EXPLANATION: [
                r"解释.*",
                r".*的原理",
                r"详细说明.*",
                r".*的工作机制",
            ],
        }

    async def set_dependencies(self, vector_store: Any, knowledge_graph: Any) -> None:
        """设置依赖组件"""
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        logger.info("依赖组件设置完成")

    async def retrieve(
        self,
        query: str,
        context: RetrievalContext,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    ) -> List[RetrievalResult]:
        """
        执行上下文感知检索

        Args:
            query: 查询文本
            context: 检索上下文
            strategy: 检索策略

        Returns:
            检索结果列表
        """
        try:
            # 1. 分析用户意图
            intent_analysis = await self._analyze_intent(query, context)

            # 2. 基于策略执行检索
            if strategy == RetrievalStrategy.HYBRID:
                results = await self._hybrid_retrieval(query, context, intent_analysis)
            elif strategy == RetrievalStrategy.CONTEXTUAL:
                results = await self._contextual_retrieval(
                    query, context, intent_analysis
                )
            elif strategy == RetrievalStrategy.SEMANTIC:
                results = await self._semantic_retrieval(query, context)
            else:  # KEYWORD
                results = await self._keyword_retrieval(query, context)

            # 3. 应用上下文重排序
            reranked_results = await self._context_reranking(
                results, context, intent_analysis
            )

            # 4. 过滤和限制结果
            final_results = await self._filter_results(reranked_results)

            # 5. 更新会话缓存
            await self._update_session_cache(context.session_id, final_results)

            logger.info(
                f"检索完成: 查询='{query}', 策略={strategy.value}, 结果数={len(final_results)}"
            )
            return final_results

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    async def _analyze_intent(
        self, query: str, context: RetrievalContext
    ) -> IntentAnalysis:
        """分析用户意图"""
        best_intent = IntentType.FACT_QUERY
        best_confidence = 0.0
        matched_patterns = []

        # 模式匹配
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matched_patterns.append((intent_type, pattern))

        # 计算置信度
        if matched_patterns:
            # 使用最具体的模式
            best_intent = max(matched_patterns, key=lambda x: len(x[1]))[0]
            best_confidence = min(len(matched_patterns) * 0.2, 1.0)
        else:
            # 基于关键词的意图识别
            best_confidence = 0.3

        # 提取关键实体和概念
        key_entities = await self._extract_entities(query)
        key_concepts = await self._extract_concepts(query)

        # 确定期望的回答类型
        expected_answer_type = self._get_expected_answer_type(best_intent)

        return IntentAnalysis(
            intent_type=best_intent,
            confidence=best_confidence,
            key_entities=key_entities,
            key_concepts=key_concepts,
            expected_answer_type=expected_answer_type,
        )

    async def _extract_entities(self, query: str) -> List[str]:
        """从查询中提取实体"""
        # 这里应该使用实体识别服务
        # 简化实现：返回名词短语
        words = query.split()
        entities = [word for word in words if len(word) > 1]
        return entities[:5]  # 限制数量

    async def _extract_concepts(self, query: str) -> List[str]:
        """从查询中提取概念"""
        # 这里应该使用概念提取服务
        # 简化实现：返回关键词
        concepts = []
        for word in query.split():
            if len(word) > 2:  # 过滤短词
                concepts.append(word)
        return concepts[:5]

    def _get_expected_answer_type(self, intent: IntentType) -> str:
        """获取期望的回答类型"""
        type_map = {
            IntentType.FACT_QUERY: "factual",
            IntentType.COMPARISON: "comparative",
            IntentType.ANALYSIS: "analytical",
            IntentType.RECOMMENDATION: "recommendation",
            IntentType.EXPLANATION: "explanatory",
        }
        return type_map.get(intent, "general")

    async def _hybrid_retrieval(
        self, query: str, context: RetrievalContext, intent_analysis: IntentAnalysis
    ) -> List[RetrievalResult]:
        """混合检索策略"""
        all_results = []

        # 并行执行多种检索
        semantic_task = asyncio.create_task(self._semantic_retrieval(query, context))
        keyword_task = asyncio.create_task(self._keyword_retrieval(query, context))
        contextual_task = asyncio.create_task(
            self._contextual_retrieval(query, context, intent_analysis)
        )

        semantic_results, keyword_results, contextual_results = await asyncio.gather(
            semantic_task, keyword_task, contextual_task
        )

        # 合并结果
        all_results.extend(semantic_results)
        all_results.extend(keyword_results)
        all_results.extend(contextual_results)

        return all_results

    async def _semantic_retrieval(
        self, query: str, context: RetrievalContext
    ) -> List[RetrievalResult]:
        """语义检索"""
        if not self.vector_store:
            return []

        try:
            # 使用向量存储进行语义搜索
            vector_results = await self.vector_store.semantic_search(
                query, top_k=self.max_results * 2  # 获取更多结果用于后续处理
            )

            results = []
            for doc_id, score, content, metadata in vector_results:
                if score >= self.min_relevance:
                    result = RetrievalResult(
                        document_id=doc_id,
                        content=content,
                        relevance_score=score,
                        confidence=score,
                        retrieval_strategy=RetrievalStrategy.SEMANTIC,
                        context_matches=[],
                        metadata=metadata or {},
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"语义检索失败: {e}")
            return []

    async def _keyword_retrieval(
        self, query: str, context: RetrievalContext
    ) -> List[RetrievalResult]:
        """关键词检索"""
        if not self.vector_store:
            return []

        try:
            # 使用向量存储进行关键词搜索
            keyword_results = await self.vector_store.keyword_search(
                query, top_k=self.max_results
            )

            results = []
            for doc_id, score, content, metadata in keyword_results:
                result = RetrievalResult(
                    document_id=doc_id,
                    content=content,
                    relevance_score=score,
                    confidence=score * 0.8,  # 关键词检索置信度较低
                    retrieval_strategy=RetrievalStrategy.KEYWORD,
                    context_matches=self._find_keyword_matches(query, content),
                    metadata=metadata or {},
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    async def _contextual_retrieval(
        self, query: str, context: RetrievalContext, intent_analysis: IntentAnalysis
    ) -> List[RetrievalResult]:
        """上下文检索"""
        results = []

        try:
            # 1. 基于会话历史的检索
            if context.conversation_history:
                session_context = await self._extract_session_context(
                    context.conversation_history
                )
                contextual_query = await self._expand_query_with_context(
                    query, session_context
                )

                # 使用扩展后的查询进行检索
                expanded_results = await self._semantic_retrieval(
                    contextual_query, context
                )
                for result in expanded_results:
                    result.retrieval_strategy = RetrievalStrategy.CONTEXTUAL
                    result.context_matches.append("session_context")
                results.extend(expanded_results)

            # 2. 基于知识图谱的检索
            if self.knowledge_graph and intent_analysis.key_entities:
                kg_results = await self._knowledge_graph_retrieval(
                    query, intent_analysis
                )
                results.extend(kg_results)

            # 3. 基于用户偏好的检索
            if context.user_preferences:
                preference_results = await self._preference_based_retrieval(
                    query, context
                )
                results.extend(preference_results)

            return results

        except Exception as e:
            logger.error(f"上下文检索失败: {e}")
            return []

    async def _extract_session_context(
        self, conversation_history: List[Dict[str, Any]]
    ) -> str:
        """提取会话上下文"""
        # 提取最近几轮对话作为上下文
        recent_turns = conversation_history[-3:]  # 最近3轮
        context_parts = []

        for turn in recent_turns:
            if "query" in turn:
                context_parts.append(turn["query"])
            if "response" in turn:
                context_parts.append(turn["response"])

        return " ".join(context_parts)

    async def _expand_query_with_context(self, query: str, context: str) -> str:
        """使用上下文扩展查询"""
        # 简单的查询扩展策略
        expanded_terms = []

        # 添加原始查询
        expanded_terms.append(query)

        # 添加上下文中的关键信息
        context_words = context.split()
        important_words = [word for word in context_words if len(word) > 2][
            :5
        ]  # 取前5个重要词

        expanded_terms.extend(important_words)

        return " ".join(expanded_terms)

    async def _knowledge_graph_retrieval(
        self, query: str, intent_analysis: IntentAnalysis
    ) -> List[RetrievalResult]:
        """基于知识图谱的检索"""
        results = []

        try:
            for entity in intent_analysis.key_entities:
                # 查询相关实体
                related_entities = await self.knowledge_graph.find_related_entities(
                    entity, max_depth=1
                )

                # 获取相关实体的文档
                for related_entity in related_entities["entities"]:
                    doc_ids = getattr(related_entity, "source_documents", [])
                    for doc_id in doc_ids[:3]:  # 每个实体取前3个文档
                        result = RetrievalResult(
                            document_id=doc_id,
                            content=f"实体关联: {related_entity.name}",
                            relevance_score=0.7,  # 中等相关性
                            confidence=related_entity.confidence,
                            retrieval_strategy=RetrievalStrategy.CONTEXTUAL,
                            context_matches=[f"entity:{entity}"],
                            metadata={"entity_based": True},
                        )
                        results.append(result)

            return results

        except Exception as e:
            logger.error(f"知识图谱检索失败: {e}")
            return []

    async def _preference_based_retrieval(
        self, query: str, context: RetrievalContext
    ) -> List[RetrievalResult]:
        """基于用户偏好的检索"""
        # 简化实现：根据用户偏好调整检索结果
        # 实际应该使用更复杂的偏好建模
        results = []

        user_preferences = context.user_preferences
        preferred_topics = user_preferences.get("preferred_topics", [])
        preferred_sources = user_preferences.get("preferred_sources", [])

        if preferred_topics or preferred_sources:
            # 这里应该实现基于偏好的检索逻辑
            # 目前返回空列表，表示需要其他检索策略补充
            pass

        return results

    def _find_keyword_matches(self, query: str, content: str) -> List[str]:
        """查找关键词匹配"""
        matches = []
        query_words = set(query.lower().split())
        content_words = content.lower().split()

        for word in query_words:
            if len(word) > 2 and word in content_words:
                matches.append(word)

        return matches[:3]  # 返回前3个匹配

    async def _context_reranking(
        self,
        results: List[RetrievalResult],
        context: RetrievalContext,
        intent_analysis: IntentAnalysis,
    ) -> List[RetrievalResult]:
        """上下文重排序"""
        if not results:
            return []

        scored_results = []

        for result in results:
            base_score = result.relevance_score
            context_score = await self._calculate_context_score(
                result, context, intent_analysis
            )

            # 综合评分
            final_score = (
                base_score * (1 - self.context_weight)
                + context_score * self.context_weight
            )

            # 创建新的结果对象（不可变）
            reranked_result = RetrievalResult(
                document_id=result.document_id,
                content=result.content,
                relevance_score=final_score,
                confidence=result.confidence,
                retrieval_strategy=result.retrieval_strategy,
                context_matches=result.context_matches,
                metadata=result.metadata,
            )
            scored_results.append((reranked_result, final_score))

        # 按最终分数排序
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return [result for result, score in scored_results]

    async def _calculate_context_score(
        self,
        result: RetrievalResult,
        context: RetrievalContext,
        intent_analysis: IntentAnalysis,
    ) -> float:
        """计算上下文评分"""
        score = 0.0

        # 1. 时效性评分
        if "timestamp" in result.metadata:
            doc_time = result.metadata["timestamp"]
            if isinstance(doc_time, str):
                try:
                    doc_time = datetime.fromisoformat(doc_time)
                except:
                    doc_time = context.temporal_context

            time_diff = (context.temporal_context - doc_time).days
            if time_diff <= self.recency_decay_days:
                recency_score = 1 - (time_diff / self.recency_decay_days)
                score += recency_score * 0.3

        # 2. 意图匹配评分
        intent_score = await self._calculate_intent_match(result, intent_analysis)
        score += intent_score * 0.4

        # 3. 个性化评分
        personalization_score = await self._calculate_personalization_score(
            result, context
        )
        score += personalization_score * 0.3

        return min(score, 1.0)

    async def _calculate_intent_match(
        self, result: RetrievalResult, intent_analysis: IntentAnalysis
    ) -> float:
        """计算意图匹配度"""
        # 简化实现：基于内容类型的匹配
        content_type = result.metadata.get("content_type", "general")

        intent_content_map = {
            IntentType.FACT_QUERY: ["fact", "definition", "encyclopedia"],
            IntentType.COMPARISON: ["comparison", "review", "analysis"],
            IntentType.ANALYSIS: ["analysis", "research", "study"],
            IntentType.RECOMMENDATION: ["recommendation", "guide", "tutorial"],
            IntentType.EXPLANATION: ["explanation", "manual", "guide"],
        }

        preferred_types = intent_content_map.get(intent_analysis.intent_type, [])
        if content_type in preferred_types:
            return 0.8
        else:
            return 0.3

    async def _calculate_personalization_score(
        self, result: RetrievalResult, context: RetrievalContext
    ) -> float:
        """计算个性化评分"""
        # 简化实现：基于用户偏好的匹配
        user_preferences = context.user_preferences
        preferred_difficulty = user_preferences.get("preferred_difficulty", "medium")

        content_difficulty = result.metadata.get("difficulty", "medium")
        if content_difficulty == preferred_difficulty:
            return 0.7
        else:
            return 0.3

    async def _filter_results(
        self, results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """过滤检索结果"""
        # 去重
        seen_docs = set()
        unique_results = []

        for result in results:
            if result.document_id not in seen_docs:
                seen_docs.add(result.document_id)
                unique_results.append(result)

        # 按相关性过滤和限制数量
        filtered_results = [
            result
            for result in unique_results
            if result.relevance_score >= self.min_relevance
        ]

        return filtered_results[: self.max_results]

    async def _update_session_cache(
        self, session_id: str, results: List[RetrievalResult]
    ) -> None:
        """更新会话缓存"""
        if session_id not in self.session_cache:
            self.session_cache[session_id] = []

        # 只保留最近的结果
        self.session_cache[session_id].extend(results)
        self.session_cache[session_id] = self.session_cache[session_id][
            -50:
        ]  # 最多50个结果

    async def get_retrieval_metrics(self) -> Dict[str, Any]:
        """获取检索指标"""
        total_sessions = len(self.session_cache)
        total_cached_results = sum(
            len(results) for results in self.session_cache.values()
        )

        return {
            "total_active_sessions": total_sessions,
            "total_cached_results": total_cached_results,
            "average_results_per_session": (
                total_cached_results / total_sessions if total_sessions > 0 else 0
            ),
        }


# 导出公共接口
__all__ = [
    "ContextAwareRetriever",
    "RetrievalContext",
    "RetrievalResult",
    "IntentAnalysis",
    "RetrievalStrategy",
    "IntentType",
]
