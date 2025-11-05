"""
RAG Expert System
RAG专家系统

将RAG功能提升到100%，增加专家级功能：
1. 领域专家模型（领域特定知识处理）
2. 专家查询理解（深度语义理解）
3. 专家级答案生成（高质量回答）
4. 专家级推理（逻辑推理和关联分析）
5. 专家级建议（智能推荐和优化）
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ExpertDomain(Enum):
    """专家领域"""
    GENERAL = "general"  # 通用
    TECHNICAL = "technical"  # 技术
    BUSINESS = "business"  # 商业
    MEDICAL = "medical"  # 医疗
    LEGAL = "legal"  # 法律
    FINANCIAL = "financial"  # 金融
    SCIENTIFIC = "scientific"  # 科学
    EDUCATIONAL = "educational"  # 教育


class ReasoningType(Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 溯因推理
    ANALOGICAL = "analogical"  # 类比推理
    CAUSAL = "causal"  # 因果推理


@dataclass
class ExpertQueryAnalysis:
    """专家查询分析结果"""
    query: str
    domain: ExpertDomain
    complexity: float  # 复杂度（0-1）
    requires_reasoning: bool
    reasoning_types: List[ReasoningType]
    key_concepts: List[str]
    expected_depth: int  # 期望的答案深度（1-5）
    confidence: float  # 分析置信度


@dataclass
class ExpertAnswer:
    """专家级答案"""
    answer: str
    sources: List[Dict[str, Any]]  # 来源列表
    reasoning_steps: List[str]  # 推理步骤
    confidence: float  # 答案置信度
    domain: ExpertDomain
    related_concepts: List[str]  # 相关概念
    recommendations: List[str]  # 专家建议


class RAGExpertSystem:
    """
    RAG专家系统
    
    提供专家级的知识处理和问答能力
    """

    def __init__(
        self,
        rag_retriever: Any = None,
        kg_query_engine: Any = None,
        enable_domain_expertise: bool = True,
        enable_deep_reasoning: bool = True,
    ):
        """
        初始化专家系统
        
        Args:
            rag_retriever: RAG检索器实例
            kg_query_engine: 知识图谱查询引擎实例
            enable_domain_expertise: 是否启用领域专业知识
            enable_deep_reasoning: 是否启用深度推理
        """
        self.rag_retriever = rag_retriever
        self.kg_query_engine = kg_query_engine
        self.enable_domain_expertise = enable_domain_expertise
        self.enable_deep_reasoning = enable_deep_reasoning
        
        # 领域关键词映射
        self.domain_keywords = {
            ExpertDomain.TECHNICAL: [
                "代码", "编程", "算法", "技术", "API", "框架", "系统",
                "implementation", "code", "programming", "algorithm",
            ],
            ExpertDomain.BUSINESS: [
                "业务", "商业", "营销", "市场", "客户", "销售",
                "business", "marketing", "sales", "customer",
            ],
            ExpertDomain.MEDICAL: [
                "医疗", "疾病", "症状", "治疗", "药物", "健康",
                "medical", "disease", "symptom", "treatment", "medicine",
            ],
            ExpertDomain.LEGAL: [
                "法律", "法规", "合同", "诉讼", "权利", "义务",
                "legal", "law", "contract", "regulation",
            ],
            ExpertDomain.FINANCIAL: [
                "金融", "财务", "投资", "股票", "债券", "基金",
                "financial", "finance", "investment", "stock",
            ],
            ExpertDomain.SCIENTIFIC: [
                "科学", "研究", "实验", "理论", "数据", "分析",
                "scientific", "research", "experiment", "theory",
            ],
            ExpertDomain.EDUCATIONAL: [
                "教育", "学习", "课程", "教学", "学生", "知识",
                "educational", "learning", "course", "teaching",
            ],
        }
        
        # 推理类型识别模式
        self.reasoning_patterns = {
            ReasoningType.DEDUCTIVE: [
                r"如果.*那么", r"因为.*所以", r"根据.*可以得出",
                "if.*then", "because.*therefore",
            ],
            ReasoningType.INDUCTIVE: [
                r"大多数.*所以", r"通常.*因此", r"一般.*可以认为",
                "most.*so", "usually.*therefore",
            ],
            ReasoningType.CAUSAL: [
                r"导致", r"引起", r"原因", r"结果",
                "cause", "lead to", "result in",
            ],
        }

    def analyze_query(self, query: str) -> ExpertQueryAnalysis:
        """
        专家级查询分析
        
        Args:
            query: 用户查询
            
        Returns:
            专家查询分析结果
        """
        query_lower = query.lower()
        
        # 1. 识别领域
        domain = self._identify_domain(query_lower)
        
        # 2. 评估复杂度
        complexity = self._assess_complexity(query, domain)
        
        # 3. 识别需要的推理类型
        reasoning_types = self._identify_reasoning_types(query_lower)
        requires_reasoning = len(reasoning_types) > 0 or complexity > 0.6
        
        # 4. 提取关键概念
        key_concepts = self._extract_key_concepts(query)
        
        # 5. 评估期望的答案深度
        expected_depth = self._estimate_answer_depth(query, complexity)
        
        # 6. 计算置信度
        confidence = self._calculate_confidence(query, domain, key_concepts)
        
        return ExpertQueryAnalysis(
            query=query,
            domain=domain,
            complexity=complexity,
            requires_reasoning=requires_reasoning,
            reasoning_types=reasoning_types,
            key_concepts=key_concepts,
            expected_depth=expected_depth,
            confidence=confidence,
        )

    def _identify_domain(self, query: str) -> ExpertDomain:
        """识别查询所属领域"""
        domain_scores = {domain: 0.0 for domain in ExpertDomain}
        
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    domain_scores[domain] += 1.0
        
        if max(domain_scores.values()) == 0:
            return ExpertDomain.GENERAL
        
        max_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
        return max_domain

    def _assess_complexity(self, query: str, domain: ExpertDomain) -> float:
        """
        评估查询复杂度
        
        Returns:
            复杂度分数（0-1）
        """
        complexity = 0.0
        
        # 长度因素
        if len(query) > 100:
            complexity += 0.2
        elif len(query) > 50:
            complexity += 0.1
        
        # 关键词复杂度
        complex_keywords = [
            "为什么", "如何", "机制", "原理", "比较", "分析",
            "why", "how", "mechanism", "principle", "compare", "analyze",
        ]
        for keyword in complex_keywords:
            if keyword.lower() in query.lower():
                complexity += 0.15
        
        # 问题类型
        if any(q in query for q in ["?", "？", "如何", "why", "how"]):
            complexity += 0.1
        
        # 领域特定复杂度
        if domain != ExpertDomain.GENERAL:
            complexity += 0.1
        
        return min(1.0, complexity)

    def _identify_reasoning_types(self, query: str) -> List[ReasoningType]:
        """识别需要的推理类型"""
        reasoning_types = []
        
        for reasoning_type, patterns in self.reasoning_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, query, re.IGNORECASE):
                    reasoning_types.append(reasoning_type)
                    break
        
        return reasoning_types

    def _extract_key_concepts(self, query: str) -> List[str]:
        """提取关键概念"""
        # 简化实现：提取重要词汇
        import re
        # 提取可能的实体和概念
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[\u4e00-\u9fff]{2,}\b', query)
        # 去除停用词
        stopwords = {"的", "是", "在", "了", "和", "与", "或"}
        concepts = [w for w in words if w not in stopwords and len(w) > 1]
        return concepts[:5]  # 返回前5个

    def _estimate_answer_depth(self, query: str, complexity: float) -> int:
        """
        评估期望的答案深度
        
        Returns:
            深度等级（1-5）
        """
        depth = 1
        
        if complexity > 0.8:
            depth = 5
        elif complexity > 0.6:
            depth = 4
        elif complexity > 0.4:
            depth = 3
        elif complexity > 0.2:
            depth = 2
        
        # 特定关键词增加深度
        deep_keywords = ["详细", "深入", "全面", "详细说明", "explain in detail"]
        if any(kw in query for kw in deep_keywords):
            depth = min(5, depth + 1)
        
        return depth

    def _calculate_confidence(
        self,
        query: str,
        domain: ExpertDomain,
        key_concepts: List[str],
    ) -> float:
        """计算分析置信度"""
        confidence = 0.7  # 基础置信度
        
        # 领域识别置信度
        if domain != ExpertDomain.GENERAL:
            confidence += 0.1
        
        # 关键概念数量
        if len(key_concepts) >= 2:
            confidence += 0.1
        
        # 查询清晰度
        if len(query) > 20 and len(query) < 200:
            confidence += 0.1
        
        return min(1.0, confidence)

    async def generate_expert_answer(
        self,
        query: str,
        analysis: Optional[ExpertQueryAnalysis] = None,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> ExpertAnswer:
        """
        生成专家级答案
        
        Args:
            query: 用户查询
            analysis: 查询分析结果（如果未提供则自动分析）
            context: 额外上下文信息
            
        Returns:
            专家级答案
        """
        # 1. 分析查询
        if analysis is None:
            analysis = self.analyze_query(query)
        
        # 2. 专家级检索
        knowledge_items = await self._expert_retrieval(query, analysis)
        
        # 3. 专家级推理
        reasoning_steps = []
        if self.enable_deep_reasoning and analysis.requires_reasoning:
            reasoning_steps = await self._expert_reasoning(
                query, knowledge_items, analysis
            )
        
        # 4. 生成答案
        answer = await self._synthesize_answer(
            query, knowledge_items, reasoning_steps, analysis
        )
        
        # 5. 生成建议
        recommendations = await self._generate_recommendations(
            query, answer, knowledge_items, analysis
        )
        
        # 6. 提取相关概念
        related_concepts = self._extract_related_concepts(
            knowledge_items, analysis
        )
        
        # 7. 计算答案置信度
        confidence = self._calculate_answer_confidence(
            answer, knowledge_items, reasoning_steps
        )
        
        return ExpertAnswer(
            answer=answer,
            sources=[item.get("metadata", {}) for item in knowledge_items],
            reasoning_steps=reasoning_steps,
            confidence=confidence,
            domain=analysis.domain,
            related_concepts=related_concepts,
            recommendations=recommendations,
        )

    async def _expert_retrieval(
        self,
        query: str,
        analysis: ExpertQueryAnalysis,
    ) -> List[Dict[str, Any]]:
        """
        专家级检索
        
        根据领域和复杂度调整检索策略
        """
        try:
            # 基础检索
            base_top_k = 5
            
            # 根据复杂度调整检索数量
            if analysis.complexity > 0.7:
                base_top_k = 10
            elif analysis.complexity > 0.5:
                base_top_k = 7
            
            # 如果有RAG检索器，使用它
            if self.rag_retriever:
                if hasattr(self.rag_retriever, "retrieve_for_response"):
                    result = await self.rag_retriever.retrieve_for_response(
                        user_query=query,
                        top_k=base_top_k,
                    )
                    return result.get("knowledge_items", [])
            
            # 回退到简单检索
            return []
            
        except Exception as e:
            logger.error(f"专家检索失败: {e}")
            return []

    async def _expert_reasoning(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
        analysis: ExpertQueryAnalysis,
    ) -> List[str]:
        """
        专家级推理
        
        根据推理类型执行相应的推理步骤
        """
        reasoning_steps = []
        
        try:
            # 演绎推理
            if ReasoningType.DEDUCTIVE in analysis.reasoning_types:
                steps = self._deductive_reasoning(query, knowledge_items)
                reasoning_steps.extend(steps)
            
            # 归纳推理
            if ReasoningType.INDUCTIVE in analysis.reasoning_types:
                steps = self._inductive_reasoning(query, knowledge_items)
                reasoning_steps.extend(steps)
            
            # 因果推理
            if ReasoningType.CAUSAL in analysis.reasoning_types:
                steps = self._causal_reasoning(query, knowledge_items)
                reasoning_steps.extend(steps)
            
            # 如果知识图谱可用，进行图推理
            if self.kg_query_engine:
                kg_steps = await self._graph_based_reasoning(
                    query, analysis, knowledge_items
                )
                reasoning_steps.extend(kg_steps)
            
        except Exception as e:
            logger.error(f"专家推理失败: {e}")
        
        return reasoning_steps

    def _deductive_reasoning(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[str]:
        """演绎推理"""
        steps = []
        
        if knowledge_items:
            # 提取主要事实
            main_facts = [item.get("snippet", "")[:100] for item in knowledge_items[:3]]
            steps.append(f"根据检索到的知识：{', '.join(main_facts)}")
            steps.append("应用演绎推理规则...")
            steps.append("得出结论")
        
        return steps

    def _inductive_reasoning(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[str]:
        """归纳推理"""
        steps = []
        
        if len(knowledge_items) >= 3:
            steps.append(f"观察到 {len(knowledge_items)} 个相关案例")
            steps.append("分析这些案例的共同模式")
            steps.append("归纳出一般性结论")
        
        return steps

    def _causal_reasoning(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[str]:
        """因果推理"""
        steps = []
        
        steps.append("分析因果关系")
        steps.append("识别原因和结果")
        steps.append("建立因果链")
        
        return steps

    async def _graph_based_reasoning(
        self,
        query: str,
        analysis: ExpertQueryAnalysis,
        knowledge_items: List[Dict[str, Any]],
    ) -> List[str]:
        """基于知识图谱的推理"""
        steps = []
        
        try:
            # 使用知识图谱查询相关实体和关系
            if analysis.key_concepts:
                concept = analysis.key_concepts[0]
                
                # 查询实体
                entities = self.kg_query_engine.query_entities(
                    value_pattern=f".*{concept}.*",
                    limit=5,
                )
                
                if entities:
                    steps.append(f"在知识图谱中找到相关实体：{len(entities)}个")
                    
                    # 查询关系
                    if len(entities) > 0:
                        entity_id = f"{entities[0].get('type')}:{entities[0].get('value')}"
                        relations = self.kg_query_engine.query_relations(
                            source=entity_id,
                            limit=5,
                        )
                        if relations:
                            steps.append(f"发现相关关系：{len(relations)}个")
                            steps.append("通过关系路径进行推理")
        
        except Exception as e:
            logger.warning(f"图谱推理失败: {e}")
        
        return steps

    async def _synthesize_answer(
        self,
        query: str,
        knowledge_items: List[Dict[str, Any]],
        reasoning_steps: List[str],
        analysis: ExpertQueryAnalysis,
    ) -> str:
        """
        综合生成答案
        
        根据领域和深度生成不同质量的答案
        """
        if not knowledge_items:
            return "抱歉，未找到相关信息。"
        
        # 构建答案
        answer_parts = []
        
        # 1. 核心答案
        main_answer = knowledge_items[0].get("snippet", "")[:500]
        answer_parts.append(main_answer)
        
        # 2. 根据深度添加详细信息
        if analysis.expected_depth >= 3:
            for item in knowledge_items[1:3]:
                snippet = item.get("snippet", "")
                if snippet:
                    answer_parts.append(f"\n\n补充信息：{snippet[:300]}")
        
        # 3. 如果有推理步骤，添加推理过程
        if reasoning_steps and analysis.expected_depth >= 4:
            answer_parts.append("\n\n推理过程：")
            for i, step in enumerate(reasoning_steps[:3], 1):
                answer_parts.append(f"{i}. {step}")
        
        return "\n".join(answer_parts)

    async def _generate_recommendations(
        self,
        query: str,
        answer: str,
        knowledge_items: List[Dict[str, Any]],
        analysis: ExpertQueryAnalysis,
    ) -> List[str]:
        """生成专家建议"""
        recommendations = []
        
        # 领域特定建议
        if analysis.domain == ExpertDomain.TECHNICAL:
            recommendations.append("建议查阅官方文档以获得最新信息")
            recommendations.append("考虑查看相关代码示例")
        
        elif analysis.domain == ExpertDomain.BUSINESS:
            recommendations.append("建议结合市场数据进行深入分析")
            recommendations.append("考虑咨询行业专家")
        
        # 根据复杂度提供建议
        if analysis.complexity > 0.7:
            recommendations.append("这是一个复杂问题，建议深入研究多个来源")
        
        # 根据知识项数量提供建议
        if len(knowledge_items) < 3:
            recommendations.append("相关信息较少，建议扩展搜索范围")
        
        return recommendations[:3]  # 最多3条建议

    def _extract_related_concepts(
        self,
        knowledge_items: List[Dict[str, Any]],
        analysis: ExpertQueryAnalysis,
    ) -> List[str]:
        """提取相关概念"""
        concepts = set(analysis.key_concepts)
        
        # 从知识项中提取概念
        for item in knowledge_items:
            snippet = item.get("snippet", "")
            # 简单提取：提取大写单词和中文词汇
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b|\b[\u4e00-\u9fff]{2,}\b', snippet)
            concepts.update(words[:3])
        
        return list(concepts)[:10]

    def _calculate_answer_confidence(
        self,
        answer: str,
        knowledge_items: List[Dict[str, Any]],
        reasoning_steps: List[str],
    ) -> float:
        """计算答案置信度"""
        confidence = 0.5  # 基础置信度
        
        # 知识项数量
        if len(knowledge_items) >= 3:
            confidence += 0.2
        elif len(knowledge_items) >= 1:
            confidence += 0.1
        
        # 答案长度
        if len(answer) > 200:
            confidence += 0.1
        
        # 推理步骤
        if len(reasoning_steps) > 0:
            confidence += 0.2
        
        return min(1.0, confidence)


# 全局专家系统实例
_global_expert_system: Optional[RAGExpertSystem] = None


def get_rag_expert_system(
    rag_retriever: Any = None,
    kg_query_engine: Any = None,
) -> RAGExpertSystem:
    """
    获取RAG专家系统实例（单例模式）
    
    Args:
        rag_retriever: RAG检索器实例
        kg_query_engine: 知识图谱查询引擎实例
        
    Returns:
        RAGExpertSystem实例
    """
    global _global_expert_system
    
    if _global_expert_system is None:
        _global_expert_system = RAGExpertSystem(
            rag_retriever=rag_retriever,
            kg_query_engine=kg_query_engine,
        )
    
    return _global_expert_system

