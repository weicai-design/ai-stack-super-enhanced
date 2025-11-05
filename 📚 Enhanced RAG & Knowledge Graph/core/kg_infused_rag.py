"""
KG-Infused RAG
知识图谱深度融合RAG

实现KG-Infused RAG技术：
1. 知识图谱深度整合到RAG系统
2. 语义结构化的检索和生成
3. 基于KG的查询重写和扩展
4. 图谱结构的上下文注入
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KGEnhancedQuery:
    """KG增强的查询"""
    original_query: str
    expanded_query: str
    entity_queries: List[str]  # 基于实体的查询
    relation_queries: List[str]  # 基于关系的查询
    kg_context: str  # 知识图谱上下文


class KGInfusedRAG:
    """
    KG-Infused RAG系统
    
    深度整合知识图谱到RAG检索流程
    """

    def __init__(
        self,
        rag_retriever: Any = None,
        kg_query_engine: Any = None,
        enable_kg_expansion: bool = True,
        enable_kg_context: bool = True,
    ):
        """
        初始化KG-Infused RAG
        
        Args:
            rag_retriever: RAG检索器实例
            kg_query_engine: 知识图谱查询引擎
            enable_kg_expansion: 是否启用KG查询扩展
            enable_kg_context: 是否启用KG上下文注入
        """
        self.rag_retriever = rag_retriever
        self.kg_query_engine = kg_query_engine
        self.enable_kg_expansion = enable_kg_expansion
        self.enable_kg_context = enable_kg_context

    async def retrieve_with_kg(
        self,
        query: str,
        top_k: int = 5,
        use_kg_expansion: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        使用KG增强的检索
        
        Args:
            query: 用户查询
            top_k: 返回数量
            use_kg_expansion: 是否使用KG扩展（覆盖默认值）
            
        Returns:
            包含检索结果和KG上下文的字典
        """
        use_kg_expansion = use_kg_expansion if use_kg_expansion is not None else self.enable_kg_expansion
        
        # 第一步：分析查询中的实体和关系
        kg_query = await self._analyze_query_for_kg(query)
        
        # 第二步：基于KG扩展查询
        if use_kg_expansion:
            expanded_queries = await self._expand_query_with_kg(kg_query)
        else:
            expanded_queries = [query]
        
        # 第三步：从KG获取相关上下文
        kg_context = ""
        if self.enable_kg_context and self.kg_query_engine:
            kg_context = await self._get_kg_context(kg_query)
        
        # 第四步：执行RAG检索（使用扩展查询）
        rag_results = []
        for expanded_query in expanded_queries:
            if self.rag_retriever:
                try:
                    if hasattr(self.rag_retriever, "retrieve_for_response"):
                        result = await self.rag_retriever.retrieve_for_response(
                            user_query=expanded_query,
                            top_k=top_k,
                        )
                        items = result.get("knowledge_items", [])
                    elif hasattr(self.rag_retriever, "search"):
                        result = await self.rag_retriever.search(
                            query=expanded_query,
                            top_k=top_k,
                        )
                        items = result.get("items", [])
                    else:
                        items = []
                    
                    rag_results.extend(items)
                except Exception as e:
                    logger.warning(f"RAG检索失败: {e}")
        
        # 第五步：去重和合并结果
        merged_results = self._merge_results(rag_results)
        
        # 第六步：根据KG上下文调整结果排序
        if kg_context:
            merged_results = await self._rerank_with_kg_context(merged_results, kg_context, query)
        
        return {
            "documents": merged_results[:top_k],
            "kg_context": kg_context,
            "expanded_queries": expanded_queries,
            "kg_entities": kg_query.entity_queries,
            "kg_relations": kg_query.relation_queries,
        }

    async def _analyze_query_for_kg(self, query: str) -> KGEnhancedQuery:
        """
        分析查询中的实体和关系
        
        提取查询中的关键实体，用于KG查询
        """
        # 简化实现：提取可能的实体
        # 实际应该使用NER模型或实体链接
        
        # 提取关键词作为潜在实体
        words = query.split()
        entity_queries = []
        relation_queries = []
        
        # 简单策略：将查询中的名词短语作为实体查询
        for word in words:
            if len(word) > 2:  # 过滤短词
                entity_queries.append(word)
        
        # 提取关系词（简化）
        relation_keywords = ["的", "和", "与", "关系", "连接"]
        for keyword in relation_keywords:
            if keyword in query:
                # 提取关系两端的实体
                parts = query.split(keyword)
                if len(parts) >= 2:
                    relation_queries.append(f"{parts[0]} {keyword} {parts[1]}")
        
        return KGEnhancedQuery(
            original_query=query,
            expanded_query=query,
            entity_queries=entity_queries[:5],  # 最多5个实体查询
            relation_queries=relation_queries[:3],  # 最多3个关系查询
            kg_context="",
        )

    async def _expand_query_with_kg(self, kg_query: KGEnhancedQuery) -> List[str]:
        """
        基于KG扩展查询
        
        根据KG中的实体关系扩展查询
        """
        expanded = [kg_query.original_query]
        
        if not self.kg_query_engine:
            return expanded
        
        try:
            # 对于每个实体查询，查找相关实体
            for entity_query in kg_query.entity_queries:
                # 查询KG中的相关实体
                entities = await self._query_kg_entities(entity_query)
                
                # 构建扩展查询
                for entity in entities[:2]:  # 每个实体最多扩展2个查询
                    expanded_query = f"{kg_query.original_query} {entity}"
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)
            
            # 对于每个关系查询，查找相关关系
            for relation_query in kg_query.relation_queries:
                # 查询KG中的相关关系
                relations = await self._query_kg_relations(relation_query)
                
                # 构建扩展查询
                for relation in relations[:1]:  # 每个关系最多扩展1个查询
                    expanded_query = f"{kg_query.original_query} {relation}"
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)
        
        except Exception as e:
            logger.warning(f"KG查询扩展失败: {e}")
        
        return expanded[:5]  # 最多5个扩展查询

    async def _get_kg_context(self, kg_query: KGEnhancedQuery) -> str:
        """
        从KG获取相关上下文
        
        基于查询中的实体和关系构建KG上下文
        """
        if not self.kg_query_engine:
            return ""
        
        context_parts = []
        
        try:
            # 查询实体相关信息
            for entity_query in kg_query.entity_queries[:3]:  # 最多3个实体
                entities = await self._query_kg_entities(entity_query)
                if entities:
                    context_parts.append(f"相关实体: {', '.join(entities[:5])}")
            
            # 查询关系信息
            for relation_query in kg_query.relation_queries[:2]:  # 最多2个关系
                relations = await self._query_kg_relations(relation_query)
                if relations:
                    context_parts.append(f"相关关系: {', '.join(relations[:3])}")
        
        except Exception as e:
            logger.warning(f"获取KG上下文失败: {e}")
        
        return "\n".join(context_parts)

    async def _query_kg_entities(self, entity_query: str) -> List[str]:
        """
        查询KG中的实体
        """
        if not self.kg_query_engine:
            return []
        
        try:
            # 调用KG查询引擎
            if hasattr(self.kg_query_engine, "query_entities"):
                result = await self.kg_query_engine.query_entities(
                    type=None,  # 不限制类型
                    value_pattern=f".*{entity_query}.*",
                    limit=5,
                )
                return [e.get("value", "") for e in result.get("entities", []) if e.get("value")]
        except Exception as e:
            logger.debug(f"KG实体查询失败: {e}")
        
        return []

    async def _query_kg_relations(self, relation_query: str) -> List[str]:
        """
        查询KG中的关系
        """
        if not self.kg_query_engine:
            return []
        
        try:
            # 调用KG查询引擎
            if hasattr(self.kg_query_engine, "query_relations"):
                result = await self.kg_query_engine.query_relations(
                    relation_type=None,  # 不限制类型
                    limit=3,
                )
                # 提取关系描述
                relations = []
                for rel in result.get("relations", [])[:3]:
                    source = rel.get("source", "")
                    target = rel.get("target", "")
                    rel_type = rel.get("type", "")
                    if source and target:
                        relations.append(f"{source}-{rel_type}-{target}")
                return relations
        except Exception as e:
            logger.debug(f"KG关系查询失败: {e}")
        
        return []

    def _merge_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并和去重检索结果
        """
        seen_ids = set()
        merged = []
        
        for result in results:
            doc_id = result.get("id") or result.get("document_id", "")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                merged.append(result)
        
        # 按分数排序
        merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return merged

    async def _rerank_with_kg_context(
        self,
        results: List[Dict[str, Any]],
        kg_context: str,
        original_query: str,
    ) -> List[Dict[str, Any]]:
        """
        根据KG上下文调整结果排序
        """
        if not kg_context:
            return results
        
        # 简单策略：如果文档内容包含KG上下文中的关键词，提升排序
        kg_keywords = set(kg_context.lower().split())
        
        for result in results:
            content = str(result.get("content", result.get("snippet", ""))).lower()
            content_words = set(content.split())
            
            # 计算KG关键词匹配度
            overlap = len(kg_keywords & content_words)
            kg_bonus = min(0.2, overlap * 0.05)  # 最多20%奖励
            
            # 调整分数
            original_score = result.get("score", 0.0)
            result["kg_enhanced_score"] = original_score + kg_bonus
        
        # 按KG增强分数排序
        results.sort(key=lambda x: x.get("kg_enhanced_score", x.get("score", 0.0)), reverse=True)
        
        return results


# 全局KG-Infused RAG实例
_global_kg_infused_rag: Optional[KGInfusedRAG] = None


def get_kg_infused_rag(
    rag_retriever: Any = None,
    kg_query_engine: Any = None,
) -> KGInfusedRAG:
    """
    获取KG-Infused RAG实例（单例模式）
    
    Args:
        rag_retriever: RAG检索器实例
        kg_query_engine: 知识图谱查询引擎
        
    Returns:
        KGInfusedRAG实例
    """
    global _global_kg_infused_rag
    
    if _global_kg_infused_rag is None:
        _global_kg_infused_rag = KGInfusedRAG(
            rag_retriever=rag_retriever,
            kg_query_engine=kg_query_engine,
        )
    
    return _global_kg_infused_rag

