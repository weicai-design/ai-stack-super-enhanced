"""
跨文档分析器
负责分析多个文档间的关联关系，发现跨文档的知识模式和主题关联
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import jieba
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class CrossDocumentRelation:
    """跨文档关系"""

    source_doc: str
    target_doc: str
    relation_type: str
    strength: float
    evidence: List[str]
    common_entities: List[str]
    common_topics: List[str]


@dataclass
class DocumentCluster:
    """文档聚类"""

    cluster_id: int
    documents: List[str]
    centroid: np.ndarray
    keywords: List[Tuple[str, float]]
    topic_label: str


class CrossDocumentAnalyzer:
    """跨文档分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.document_contents: Dict[str, str] = {}
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        self.entity_document_index: Dict[str, Set[str]] = defaultdict(set)
        self.topic_document_index: Dict[str, Set[str]] = defaultdict(set)

        # 初始化分析参数
        self.min_relation_strength = config.get("min_relation_strength", 0.3)
        self.tfidf_min_df = config.get("tfidf_min_df", 2)
        self.clustering_eps = config.get("clustering_eps", 0.5)

        # 初始化分析组件
        self.tfidf_vectorizer = TfidfVectorizer(
            min_df=self.tfidf_min_df,
            max_features=1000,
            tokenizer=self._chinese_tokenizer,
        )

        logger.info("跨文档分析器初始化完成")

    def _chinese_tokenizer(self, text: str) -> List[str]:
        """中文文本分词器"""
        return list(jieba.cut(text))

    async def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        entities: Optional[List[Dict]] = None,
        topics: Optional[List[str]] = None,
    ) -> None:
        """
        添加文档到分析器

        Args:
            doc_id: 文档ID
            content: 文档内容
            metadata: 文档元数据
            entities: 文档实体列表
            topics: 文档主题列表
        """
        try:
            self.document_contents[doc_id] = content
            self.document_metadata[doc_id] = metadata or {}

            # 更新实体-文档索引
            if entities:
                for entity in entities:
                    entity_id = entity.get("id")
                    if entity_id:
                        self.entity_document_index[entity_id].add(doc_id)

            # 更新主题-文档索引
            if topics:
                for topic in topics:
                    self.topic_document_index[topic].add(doc_id)

            logger.debug(f"文档 {doc_id} 已添加到跨文档分析器")

        except Exception as e:
            logger.error(f"添加文档失败 {doc_id}: {e}")
            raise

    async def analyze_cross_document_relations(self) -> List[CrossDocumentRelation]:
        """
        分析跨文档关系

        Returns:
            跨文档关系列表
        """
        if len(self.document_contents) < 2:
            logger.warning("文档数量不足，无法进行跨文档分析")
            return []

        try:
            relations = []
            doc_ids = list(self.document_contents.keys())

            # 1. 基于内容的相似性分析
            content_relations = await self._analyze_content_similarity(doc_ids)
            relations.extend(content_relations)

            # 2. 基于实体的关联分析
            entity_relations = await self._analyze_entity_relations(doc_ids)
            relations.extend(entity_relations)

            # 3. 基于主题的关联分析
            topic_relations = await self._analyze_topic_relations(doc_ids)
            relations.extend(topic_relations)

            # 过滤和去重
            filtered_relations = await self._filter_relations(relations)

            logger.info(f"跨文档分析完成，发现 {len(filtered_relations)} 个关系")
            return filtered_relations

        except Exception as e:
            logger.error(f"跨文档分析失败: {e}")
            return []

    async def _analyze_content_similarity(
        self, doc_ids: List[str]
    ) -> List[CrossDocumentRelation]:
        """基于内容相似性的关系分析"""
        relations = []

        try:
            # 准备文档内容
            contents = [self.document_contents[doc_id] for doc_id in doc_ids]

            # 计算TF-IDF向量
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
            similarity_matrix = (tfidf_matrix * tfidf_matrix.T).A

            # 分析文档对
            for i, doc1 in enumerate(doc_ids):
                for j, doc2 in enumerate(doc_ids):
                    if i < j:  # 避免重复和自比较
                        similarity = similarity_matrix[i, j]

                        if similarity > self.min_relation_strength:
                            relation = CrossDocumentRelation(
                                source_doc=doc1,
                                target_doc=doc2,
                                relation_type="content_similarity",
                                strength=similarity,
                                evidence=[f"内容相似度: {similarity:.3f}"],
                                common_entities=await self._get_common_entities(
                                    doc1, doc2
                                ),
                                common_topics=await self._get_common_topics(doc1, doc2),
                            )
                            relations.append(relation)

            return relations

        except Exception as e:
            logger.error(f"内容相似性分析失败: {e}")
            return []

    async def _analyze_entity_relations(
        self, doc_ids: List[str]
    ) -> List[CrossDocumentRelation]:
        """基于实体关联的关系分析"""
        relations = []

        try:
            # 找出共享实体的文档对
            entity_cooccurrence = defaultdict(set)

            for entity_id, docs in self.entity_document_index.items():
                if len(docs) > 1:  # 只在多个文档中出现的实体
                    doc_list = list(docs)
                    for i, doc1 in enumerate(doc_list):
                        for doc2 in doc_list[i + 1 :]:
                            entity_cooccurrence[(doc1, doc2)].add(entity_id)

            # 创建基于实体的关系
            for (doc1, doc2), common_entities in entity_cooccurrence.items():
                if doc1 in doc_ids and doc2 in doc_ids:
                    strength = len(common_entities) / min(
                        len(self.entity_document_index) / 10, 1.0  # 归一化
                    )
                    strength = min(strength, 1.0)  # 限制最大强度

                    if strength > self.min_relation_strength:
                        relation = CrossDocumentRelation(
                            source_doc=doc1,
                            target_doc=doc2,
                            relation_type="entity_cooccurrence",
                            strength=strength,
                            evidence=[f"共享实体: {len(common_entities)} 个"],
                            common_entities=list(common_entities),
                            common_topics=await self._get_common_topics(doc1, doc2),
                        )
                        relations.append(relation)

            return relations

        except Exception as e:
            logger.error(f"实体关系分析失败: {e}")
            return []

    async def _analyze_topic_relations(
        self, doc_ids: List[str]
    ) -> List[CrossDocumentRelation]:
        """基于主题关联的关系分析"""
        relations = []

        try:
            # 找出共享主题的文档对
            topic_cooccurrence = defaultdict(set)

            for topic, docs in self.topic_document_index.items():
                if len(docs) > 1:
                    doc_list = list(docs)
                    for i, doc1 in enumerate(doc_list):
                        for doc2 in doc_list[i + 1 :]:
                            topic_cooccurrence[(doc1, doc2)].add(topic)

            # 创建基于主题的关系
            for (doc1, doc2), common_topics in topic_cooccurrence.items():
                if doc1 in doc_ids and doc2 in doc_ids:
                    strength = len(common_topics) / 5.0  # 简单归一化
                    strength = min(strength, 1.0)

                    if strength > self.min_relation_strength:
                        relation = CrossDocumentRelation(
                            source_doc=doc1,
                            target_doc=doc2,
                            relation_type="topic_similarity",
                            strength=strength,
                            evidence=[f"共享主题: {len(common_topics)} 个"],
                            common_entities=await self._get_common_entities(doc1, doc2),
                            common_topics=list(common_topics),
                        )
                        relations.append(relation)

            return relations

        except Exception as e:
            logger.error(f"主题关系分析失败: {e}")
            return []

    async def _get_common_entities(self, doc1: str, doc2: str) -> List[str]:
        """获取两个文档共享的实体"""
        entities1 = {
            eid for eid, docs in self.entity_document_index.items() if doc1 in docs
        }
        entities2 = {
            eid for eid, docs in self.entity_document_index.items() if doc2 in docs
        }
        return list(entities1 & entities2)

    async def _get_common_topics(self, doc1: str, doc2: str) -> List[str]:
        """获取两个文档共享的主题"""
        topics1 = {
            topic for topic, docs in self.topic_document_index.items() if doc1 in docs
        }
        topics2 = {
            topic for topic, docs in self.topic_document_index.items() if doc2 in docs
        }
        return list(topics1 & topics2)

    async def _filter_relations(
        self, relations: List[CrossDocumentRelation]
    ) -> List[CrossDocumentRelation]:
        """过滤和去重关系"""
        # 按关系强度排序
        relations.sort(key=lambda x: x.strength, reverse=True)

        # 去重：每个文档对只保留最强的关系
        seen_pairs = set()
        filtered = []

        for relation in relations:
            pair = tuple(sorted([relation.source_doc, relation.target_doc]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                filtered.append(relation)

        return filtered

    async def cluster_documents(self) -> List[DocumentCluster]:
        """
        对文档进行聚类分析

        Returns:
            文档聚类列表
        """
        if len(self.document_contents) < 2:
            return []

        try:
            doc_ids = list(self.document_contents.keys())
            contents = [self.document_contents[doc_id] for doc_id in doc_ids]

            # 使用TF-IDF进行向量化
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)

            # 使用DBSCAN进行聚类
            clustering = DBSCAN(eps=self.clustering_eps, min_samples=2)
            clusters = clustering.fit_predict(tfidf_matrix.toarray())

            # 构建聚类结果
            document_clusters = []
            unique_clusters = set(clusters)

            for cluster_id in unique_clusters:
                if cluster_id == -1:  # 噪声点
                    continue

                # 获取该聚类的文档
                cluster_docs = [
                    doc_ids[i] for i, c in enumerate(clusters) if c == cluster_id
                ]

                # 计算聚类中心
                cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
                cluster_vectors = tfidf_matrix[cluster_indices]
                centroid = cluster_vectors.mean(axis=0).A[0]

                # 提取关键词
                keywords = await self._extract_cluster_keywords(
                    cluster_docs, self.tfidf_vectorizer, centroid
                )

                # 生成主题标签
                topic_label = await self._generate_topic_label(keywords)

                cluster_obj = DocumentCluster(
                    cluster_id=cluster_id,
                    documents=cluster_docs,
                    centroid=centroid,
                    keywords=keywords,
                    topic_label=topic_label,
                )
                document_clusters.append(cluster_obj)

            logger.info(f"文档聚类完成，发现 {len(document_clusters)} 个聚类")
            return document_clusters

        except Exception as e:
            logger.error(f"文档聚类失败: {e}")
            return []

    async def _extract_cluster_keywords(
        self, doc_ids: List[str], vectorizer: TfidfVectorizer, centroid: np.ndarray
    ) -> List[Tuple[str, float]]:
        """提取聚类关键词"""
        feature_names = vectorizer.get_feature_names_out()
        keyword_scores = []

        for i, score in enumerate(centroid):
            if score > 0:
                keyword_scores.append((feature_names[i], score))

        # 按分数排序并返回前10个
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        return keyword_scores[:10]

    async def _generate_topic_label(self, keywords: List[Tuple[str, float]]) -> str:
        """生成主题标签"""
        if not keywords:
            return "未知主题"

        # 使用前3个关键词生成标签
        top_keywords = [kw for kw, score in keywords[:3]]
        return " | ".join(top_keywords)

    async def get_document_network(self) -> Dict[str, Any]:
        """
        获取文档网络图

        Returns:
            文档网络数据
        """
        relations = await self.analyze_cross_document_relations()

        nodes = []
        links = []

        # 构建节点
        for doc_id in self.document_contents.keys():
            nodes.append(
                {
                    "id": doc_id,
                    "title": self.document_metadata.get(doc_id, {}).get(
                        "title", doc_id
                    ),
                    "size": len(self.document_contents[doc_id]),
                }
            )

        # 构建边
        for relation in relations:
            links.append(
                {
                    "source": relation.source_doc,
                    "target": relation.target_doc,
                    "type": relation.relation_type,
                    "strength": relation.strength,
                }
            )

        return {"nodes": nodes, "links": links, "total_relations": len(relations)}


# 导出公共接口
__all__ = ["CrossDocumentAnalyzer", "CrossDocumentRelation", "DocumentCluster"]
