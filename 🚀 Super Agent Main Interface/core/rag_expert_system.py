#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG专家系统（T004）
聚合知识专家、检索专家、图谱专家，提供统一的分析与回答能力。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .experts.rag_experts import (
    ExpertDomain,
    KnowledgeExpert,
    RetrievalExpert,
    GraphExpert,
    ExpertAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """查询分析结果"""

    domain: ExpertDomain
    complexity: float
    confidence: float
    focus_keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertAnswer:
    """专家回答"""

    answer: str
    confidence: float
    recommendations: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGExpertSystem:
    """
RAG专家系统聚合层
- 分析查询意图，自动选择知识/检索/图谱专家
- 汇总专家洞察，生成结构化回答
- 集成新配置系统，支持环境变量和配置文件管理
"""

    def __init__(self, experts: Optional[Dict[ExpertDomain, Any]] = None):
        # 加载配置系统
        from .experts.rag_config import get_rag_config
        self.config = get_rag_config()
        
        # 初始化专家系统，使用配置系统
        from .experts.rag_config import get_expert_config
        self.experts: Dict[ExpertDomain, Any] = experts or {
            ExpertDomain.KNOWLEDGE: KnowledgeExpert(get_expert_config("rag_knowledge_expert")),
            ExpertDomain.RETRIEVAL: RetrievalExpert(get_expert_config("rag_retrieval_expert")),
            ExpertDomain.GRAPH: GraphExpert(get_expert_config("rag_graph_expert")),
        }
        
        logger.info(f"RAG专家系统初始化完成 - 并发限制: {self.config.max_concurrent_requests}")

    def describe_capabilities(self) -> Dict[str, Any]:
        """返回各专家的能力介绍，方便外部展示"""
        return {
            ExpertDomain.KNOWLEDGE.value: [
                "知识分类/组织",
                "知识质量评估",
                "知识更新建议",
            ],
            ExpertDomain.RETRIEVAL.value: [
                "检索策略优化",
                "检索结果重排序",
                "查询质量诊断",
            ],
            ExpertDomain.GRAPH.value: [
                "知识图谱结构分析",
                "实体关系抽取建议",
                "图谱增强方案",
            ],
        }

    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        基于关键词与长度对查询进行分析，确定优先专家
        """
        normalized = query.lower()
        if any(k in normalized for k in ("graph", "图谱", "实体", "关系")):
            domain = ExpertDomain.GRAPH
        elif any(k in normalized for k in ("retrieval", "检索", "search", "查询性能")):
            domain = ExpertDomain.RETRIEVAL
        else:
            domain = ExpertDomain.KNOWLEDGE

        focus_keywords = self._extract_keywords(normalized)
        complexity = min(1.0, max(0.2, len(query) / 200))
        confidence = 0.85 if len(focus_keywords) >= 3 else 0.75

        logger.debug(
            "RAGExpertSystem.analyze_query domain=%s complexity=%.2f",
            domain,
            complexity,
        )

        return QueryAnalysis(
            domain=domain,
            complexity=complexity,
            confidence=confidence,
            focus_keywords=focus_keywords,
            metadata={
                "query_length": len(query),
                "keyword_count": len(focus_keywords),
            },
        )

    async def generate_expert_answer(
        self,
        query: str,
        analysis: QueryAnalysis,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> ExpertAnswer:
        """
        综合专家输出生成最终回答
        """
        context_items = [item for item in (context or []) if isinstance(item, dict)]
        knowledge_items = self._extract_context_list(context_items, ["knowledge_items", "items"])
        retrieval_results = self._extract_context_list(
            context_items,
            ["retrieval_results", "results", "knowledge_items"],
        )
        entities = self._extract_context_list(context_items, ["entities"])
        relations = self._extract_context_list(context_items, ["relations"])

        # 如果没有明确的知识条目，尝试从 result 字段中构造
        if not knowledge_items:
            for item in context_items:
                result_payload = item.get("result")
                if isinstance(result_payload, dict):
                    knowledge_items = [result_payload]
                    break

        insights: List[str] = []
        recommendations: List[str] = []
        related_concepts: List[str] = []
        expert_metadata: Dict[str, Any] = {}

        # 知识专家
        if knowledge_items:
            knowledge_analysis = await self.experts[ExpertDomain.KNOWLEDGE].analyze_knowledge(
                knowledge_items
            )
            self._merge_analysis(
                "knowledge",
                knowledge_analysis,
                insights,
                recommendations,
                related_concepts,
                expert_metadata,
            )

        # 检索专家
        if retrieval_results:
            retrieval_analysis = await self.experts[ExpertDomain.RETRIEVAL].optimize_retrieval(
                query,
                retrieval_results,
            )
            self._merge_analysis(
                "retrieval",
                retrieval_analysis,
                insights,
                recommendations,
                related_concepts,
                expert_metadata,
            )

        # 图谱专家
        if entities or relations:
            graph_analysis = await self.experts[ExpertDomain.GRAPH].analyze_graph_structure(
                entities,
                relations,
            )
            self._merge_analysis(
                "graph",
                graph_analysis,
                insights,
                recommendations,
                related_concepts,
                expert_metadata,
            )

        if not insights:
            insights.append("暂无上下文数据，建议提供相关知识或检索结果以便深入分析。")

        answer_sections = [
            f"🔍 **分析领域**: {analysis.domain.value}",
            f"🤖 **复杂度**: {analysis.complexity:.2f}",
            "",
            "📌 **核心洞察**:",
            *[f"- {item}" for item in insights],
        ]

        answer_text = "\n".join(answer_sections)

        return ExpertAnswer(
            answer=answer_text,
            confidence=analysis.confidence,
            recommendations=recommendations,
            related_concepts=list(dict.fromkeys(related_concepts)) or analysis.focus_keywords,
            metadata={
                "analysis": analysis.metadata,
                "experts_used": self.available_experts(),
                "context_items": len(context_items),
                **expert_metadata,
            },
        )

    def available_experts(self) -> List[str]:
        """返回当前系统中可用的专家域"""
        return [domain.value for domain in self.experts.keys()]

    def register_expert(self, domain: ExpertDomain, expert: Any) -> None:
        """注册自定义专家"""
        self.experts[domain] = expert
        logger.info("注册RAG专家: %s", domain.value)

    @staticmethod
    def _extract_keywords(text: str, limit: int = 5) -> List[str]:
        tokens = [word for word in text.replace("，", " ").replace("。", " ").split(" ") if word]
        keywords: List[str] = []
        for token in tokens:
            token = token.strip().lower()
            if len(token) <= 2:
                continue
            if token not in keywords:
                keywords.append(token)
            if len(keywords) >= limit:
                break
        return keywords

    @staticmethod
    def _extract_context_list(
        context_items: List[Dict[str, Any]],
        candidate_keys: List[str],
    ) -> List[Dict[str, Any]]:
        for item in context_items:
            for key in candidate_keys:
                value = item.get(key)
                if isinstance(value, list):
                    return value
        return []

    @staticmethod
    def _merge_analysis(
        label: str,
        analysis: Optional[ExpertAnalysis],
        insights: List[str],
        recommendations: List[str],
        related_concepts: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        if not analysis:
            return
        insights.extend(analysis.insights)
        recommendations.extend(analysis.recommendations)
        if "topics" in analysis.metadata:
            related_concepts.extend(
                str(topic) for topic in analysis.metadata["topics"] if topic
            )
        metadata[f"{label}_analysis"] = analysis.metadata


_rag_expert_system: Optional[RAGExpertSystem] = None


def get_rag_expert_system() -> RAGExpertSystem:
    """获取RAG专家系统单例"""
    global _rag_expert_system
    if _rag_expert_system is None:
        _rag_expert_system = RAGExpertSystem()
    return _rag_expert_system


__all__ = [
    "RAGExpertSystem",
    "get_rag_expert_system",
    "QueryAnalysis",
    "ExpertAnswer",
]

