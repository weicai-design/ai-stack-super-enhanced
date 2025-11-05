"""
Query Enhancement Module
查询增强模块

根据需求1.5：检索精度优化
功能：
1. 查询理解增强（意图识别）
2. 查询扩展（同义词、相关词）
3. 查询重写优化
4. 结果多样性保证
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    """查询意图"""
    intent_type: str  # fact_query, comparison, analysis, recommendation, explanation
    confidence: float
    key_entities: List[str]
    key_concepts: List[str]
    expected_answer_type: str


class QueryEnhancer:
    """
    查询增强器
    
    提供查询理解、扩展和重写功能
    """

    def __init__(self):
        """初始化查询增强器"""
        # 意图识别模式
        self.intent_patterns = {
            "fact_query": [
                r"什么是.*", r".*是什么", r"谁.*", r"何时.*", r"哪里.*",
                r".*的定义", r".*含义", r"解释.*"
            ],
            "comparison": [
                r".*与.*的区别", r".*和.*哪个.*", r"比较.*和.*",
                r".*vs.*", r".*对比.*"
            ],
            "analysis": [
                r"分析.*", r".*的原因", r"为什么.*", r".*的影响",
                r"如何.*", r".*原理", r".*机制"
            ],
            "recommendation": [
                r"推荐.*", r"应该.*", r".*建议", r"最好的.*",
                r"哪个.*更好", r".*选择"
            ],
            "explanation": [
                r"详细说明.*", r"解释.*", r".*怎么.*",
                r".*如何实现", r".*步骤"
            ],
        }
        
        # 常用同义词库（简化版，实际可以使用更完善的同义词库）
        self.synonyms_cache: Dict[str, List[str]] = {}
        
        # 结果多样性控制
        self.diversity_threshold = 0.7  # 相似度阈值，超过此值认为结果过于相似

    def analyze_intent(self, query: str) -> QueryIntent:
        """
        分析查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            QueryIntent: 查询意图分析结果
        """
        query_lower = query.lower().strip()
        
        # 识别意图类型
        intent_type = "fact_query"  # 默认
        max_match = 0
        confidence = 0.5
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
                if matches > max_match:
                    max_match = matches
                    intent_type = intent
                    confidence = min(0.9, 0.5 + matches * 0.2)
        
        # 提取关键实体和概念
        key_entities = self._extract_entities(query)
        key_concepts = self._extract_concepts(query)
        
        # 确定期望答案类型
        expected_answer_type = self._determine_answer_type(intent_type, query)
        
        return QueryIntent(
            intent_type=intent_type,
            confidence=confidence,
            key_entities=key_entities,
            key_concepts=key_concepts,
            expected_answer_type=expected_answer_type,
        )

    def _extract_entities(self, query: str) -> List[str]:
        """
        提取查询中的实体（简化版）
        
        Args:
            query: 查询文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 提取可能的专有名词（大写开头的词）
        words = query.split()
        for word in words:
            if len(word) > 1 and word[0].isupper():
                entities.append(word)
        
        # 提取引号内的内容
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        return list(set(entities))

    def _extract_concepts(self, query: str) -> List[str]:
        """
        提取查询中的关键概念
        
        Args:
            query: 查询文本
            
        Returns:
            概念列表
        """
        # 移除停用词（简化版）
        stopwords = {"的", "了", "在", "是", "有", "和", "与", "或", "但", "而"}
        words = query.split()
        concepts = [w for w in words if w not in stopwords and len(w) > 1]
        
        return concepts[:5]  # 返回前5个关键概念

    def _determine_answer_type(self, intent_type: str, query: str) -> str:
        """
        确定期望答案类型
        
        Args:
            intent_type: 意图类型
            query: 查询文本
            
        Returns:
            答案类型
        """
        type_mapping = {
            "fact_query": "factual",
            "comparison": "comparative",
            "analysis": "analytical",
            "recommendation": "recommendation",
            "explanation": "explanatory",
        }
        
        return type_mapping.get(intent_type, "general")

    def expand_query(self, query: str, max_expansions: int = 5) -> List[str]:
        """
        扩展查询（添加同义词和相关词）
        
        Args:
            query: 原始查询
            max_expansions: 最大扩展数量
            
        Returns:
            扩展后的查询列表
        """
        expanded_queries = [query]  # 包含原始查询
        
        # 1. 同义词扩展
        synonyms = self._get_synonyms(query)
        for synonym_query in synonyms[:max_expansions]:
            if synonym_query != query:
                expanded_queries.append(synonym_query)
        
        # 2. 概念扩展
        concepts = self._extract_concepts(query)
        if concepts:
            # 为每个关键概念生成扩展查询
            for concept in concepts[:2]:  # 只为前2个概念扩展
                expanded_query = f"{query} {concept}相关内容"
                if expanded_query not in expanded_queries:
                    expanded_queries.append(expanded_query)
        
        return expanded_queries[:max_expansions + 1]

    def _get_synonyms(self, query: str) -> List[str]:
        """
        获取查询的同义词（简化实现）
        
        Args:
            query: 查询文本
            
        Returns:
            同义词查询列表
        """
        # 使用缓存的同义词
        if query in self.synonyms_cache:
            return self.synonyms_cache[query]
        
        synonyms = []
        
        # 常见同义词映射（实际可以使用更完善的词典）
        synonym_map = {
            "如何": ["怎样", "怎么", "方法"],
            "为什么": ["原因", "为何", "为何"],
            "区别": ["差异", "不同", "差别"],
            "定义": ["含义", "意思", "概念"],
        }
        
        # 查找同义词并生成扩展查询
        for word, synonyms_list in synonym_map.items():
            if word in query:
                for syn in synonyms_list:
                    expanded = query.replace(word, syn)
                    if expanded not in synonyms:
                        synonyms.append(expanded)
        
        self.synonyms_cache[query] = synonyms
        return synonyms

    def rewrite_query(self, query: str, intent: QueryIntent) -> str:
        """
        根据意图重写查询
        
        Args:
            query: 原始查询
            intent: 查询意图
            
        Returns:
            重写后的查询
        """
        if intent.intent_type == "comparison":
            # 比较类查询：确保包含对比关键词
            if "对比" not in query and "比较" not in query and "区别" not in query:
                # 自动添加对比意图
                query = f"对比 {query}"
        
        elif intent.intent_type == "analysis":
            # 分析类查询：强调分析角度
            if "分析" not in query:
                query = f"分析 {query}"
        
        elif intent.intent_type == "recommendation":
            # 推荐类查询：强调推荐视角
            if "推荐" not in query and "建议" not in query:
                query = f"推荐 {query}"
        
        # 添加关键实体以增强检索
        if intent.key_entities:
            entities_str = " ".join(intent.key_entities[:2])
            query = f"{query} {entities_str}"
        
        return query.strip()

    def ensure_diversity(
        self,
        results: List[Dict[str, Any]],
        max_similarity: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        确保结果多样性
        
        Args:
            results: 检索结果列表
            max_similarity: 最大相似度阈值
            
        Returns:
            去重后的结果列表，保证多样性
        """
        if not results:
            return []
        
        diverse_results = [results[0]]  # 保留第一个结果
        
        for result in results[1:]:
            # 检查与已有结果的相似度
            is_similar = False
            for existing in diverse_results:
                similarity = self._calculate_text_similarity(
                    result.get("text", ""),
                    existing.get("text", ""),
                )
                
                if similarity > max_similarity:
                    is_similar = True
                    break
            
            # 如果不够相似，添加结果
            if not is_similar:
                diverse_results.append(result)
        
        return diverse_results

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度（简化版，基于词汇重叠）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度值（0-1）
        """
        if not text1 or not text2:
            return 0.0
        
        # 提取关键词（去除停用词）
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 计算Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union


# 全局查询增强器实例
_global_enhancer: Optional[QueryEnhancer] = None


def get_query_enhancer() -> QueryEnhancer:
    """
    获取全局查询增强器实例（单例模式）
    
    Returns:
        QueryEnhancer实例
    """
    global _global_enhancer
    
    if _global_enhancer is None:
        _global_enhancer = QueryEnhancer()
    
    return _global_enhancer

