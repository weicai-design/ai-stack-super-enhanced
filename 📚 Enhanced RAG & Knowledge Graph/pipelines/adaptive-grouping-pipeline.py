#!/usr/bin/env python3
"""
自适应分组管道 - RAG内容智能分组引擎
功能：基于语义相似度、主题聚类和上下文关联的智能内容分组
版本：1.0.0
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class GroupingStrategy(Enum):
    """分组策略枚举"""

    SEMANTIC_SIMILARITY = "semantic_similarity"
    TOPIC_CLUSTERING = "topic_clustering"
    CONTEXTUAL_RELATION = "contextual_relation"
    HYBRID_APPROACH = "hybrid_approach"


@dataclass
class ContentChunk:
    """内容块数据结构"""

    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None
    source: str = ""
    chunk_type: str = "text"


@dataclass
class ContentGroup:
    """内容分组结构"""

    group_id: str
    chunks: List[ContentChunk]
    centroid_embedding: Optional[np.ndarray] = None
    group_metadata: Dict[str, Any] = None
    semantic_label: str = ""


class AdaptiveGroupingPipeline:
    """
    自适应分组管道 - 智能内容分组引擎
    支持多种分组策略和动态参数调整
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedding_model = None
        self.grouping_strategies = []
        self._initialize_components()

        logger.info("自适应分组管道初始化完成")

    def _initialize_components(self):
        """初始化组件"""
        # 加载嵌入模型
        model_name = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"嵌入模型加载成功: {model_name}")
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {e}")
            raise

        # 配置分组策略
        strategies_config = self.config.get("grouping_strategies", [])
        for strategy_config in strategies_config:
            strategy_name = strategy_config.get("name")
            if strategy_name == "semantic_similarity":
                self.grouping_strategies.append(self._semantic_similarity_grouping)
            elif strategy_name == "topic_clustering":
                self.grouping_strategies.append(self._topic_clustering_grouping)
            elif strategy_name == "contextual_relation":
                self.grouping_strategies.append(self._contextual_relation_grouping)

    async def process_batch(self, chunks: List[ContentChunk]) -> List[ContentGroup]:
        """
        处理内容块批次 - 主要入口方法

        Args:
            chunks: 内容块列表

        Returns:
            分组结果列表
        """
        if not chunks:
            logger.warning("输入内容块为空")
            return []

        logger.info(f"开始处理 {len(chunks)} 个内容块的分组")

        try:
            # 步骤1: 生成嵌入向量
            chunks_with_embeddings = await self._generate_embeddings(chunks)

            # 步骤2: 应用分组策略
            groups = await self._apply_grouping_strategies(chunks_with_embeddings)

            # 步骤3: 优化分组结果
            optimized_groups = await self._optimize_groups(groups)

            logger.info(f"分组完成，生成 {len(optimized_groups)} 个分组")
            return optimized_groups

        except Exception as e:
            logger.error(f"分组处理失败: {e}")
            raise

    async def _generate_embeddings(
        self, chunks: List[ContentChunk]
    ) -> List[ContentChunk]:
        """生成内容块的嵌入向量"""
        logger.info("开始生成嵌入向量")

        contents = [chunk.content for chunk in chunks]

        # 异步生成嵌入
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.embedding_model.encode, contents
        )

        # 关联嵌入到内容块
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        logger.info("嵌入向量生成完成")
        return chunks

    async def _apply_grouping_strategies(
        self, chunks: List[ContentChunk]
    ) -> List[ContentGroup]:
        """应用分组策略"""
        if not self.grouping_strategies:
            # 使用默认语义相似度分组
            return await self._semantic_similarity_grouping(chunks)

        all_groups = []

        for strategy in self.grouping_strategies:
            try:
                strategy_groups = await strategy(chunks)
                all_groups.extend(strategy_groups)
                logger.debug(
                    f"策略 {strategy.__name__} 生成 {len(strategy_groups)} 个分组"
                )
            except Exception as e:
                logger.warning(f"策略 {strategy.__name__} 执行失败: {e}")
                continue

        return await self._merge_overlapping_groups(all_groups)

    async def _semantic_similarity_grouping(
        self, chunks: List[ContentChunk]
    ) -> List[ContentGroup]:
        """基于语义相似度的分组"""
        if len(chunks) < 2:
            return [
                ContentGroup(
                    group_id="group_0",
                    chunks=chunks,
                    centroid_embedding=chunks[0].embedding if chunks else None,
                )
            ]

        # 提取嵌入向量
        embeddings = np.array([chunk.embedding for chunk in chunks])

        # 使用层次聚类
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.config.get("similarity_threshold", 0.6),
            metric="cosine",
            linkage="average",
        )

        cluster_labels = clustering.fit_predict(embeddings)

        # 构建分组
        groups_dict = defaultdict(list)
        for chunk, label in zip(chunks, cluster_labels):
            groups_dict[label].append(chunk)

        groups = []
        for i, (label, group_chunks) in enumerate(groups_dict.items()):
            group_embedding = np.mean(
                [chunk.embedding for chunk in group_chunks], axis=0
            )
            groups.append(
                ContentGroup(
                    group_id=f"semantic_group_{i}",
                    chunks=group_chunks,
                    centroid_embedding=group_embedding,
                )
            )

        return groups

    async def _topic_clustering_grouping(
        self, chunks: List[ContentChunk]
    ) -> List[ContentGroup]:
        """基于主题聚类的分组"""
        # 这里可以集成主题模型如LDA或BERTopic
        # 当前使用简化的基于关键词的聚类

        # 提取文本特征进行聚类
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.feature_extraction.text import TfidfVectorizer

        texts = [chunk.content for chunk in chunks]

        # TF-IDF向量化
        vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(texts)

        # LDA主题模型
        n_topics = min(10, len(chunks) // 5)  # 动态确定主题数量
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        topic_distributions = lda.fit_transform(tfidf_matrix)

        # 分配主题标签
        topic_labels = topic_distributions.argmax(axis=1)

        # 构建分组
        groups_dict = defaultdict(list)
        for chunk, label in zip(chunks, topic_labels):
            groups_dict[label].append(chunk)

        groups = []
        for i, (label, group_chunks) in enumerate(groups_dict.items()):
            groups.append(
                ContentGroup(
                    group_id=f"topic_group_{i}",
                    chunks=group_chunks,
                    group_metadata={"topic_id": label},
                )
            )

        return groups

    async def _contextual_relation_grouping(
        self, chunks: List[ContentChunk]
    ) -> List[ContentGroup]:
        """基于上下文关系的分组"""
        # 构建内容关联图
        G = nx.Graph()

        # 添加节点
        for i, chunk in enumerate(chunks):
            G.add_node(i, chunk=chunk)

        # 基于语义相似度添加边
        embeddings = np.array([chunk.embedding for chunk in chunks])
        similarity_matrix = cosine_similarity(embeddings)

        threshold = self.config.get("relation_threshold", 0.7)
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                if similarity_matrix[i][j] > threshold:
                    G.add_edge(i, j, weight=similarity_matrix[i][j])

        # 使用连通分量进行分组
        groups = []
        for i, component in enumerate(nx.connected_components(G)):
            component_chunks = [chunks[node] for node in component]
            group_embedding = np.mean(
                [chunk.embedding for chunk in component_chunks], axis=0
            )

            groups.append(
                ContentGroup(
                    group_id=f"context_group_{i}",
                    chunks=component_chunks,
                    centroid_embedding=group_embedding,
                )
            )

        return groups

    async def _merge_overlapping_groups(
        self, groups: List[ContentGroup]
    ) -> List[ContentGroup]:
        """合并重叠的分组"""
        if len(groups) <= 1:
            return groups

        # 计算分组间的重叠度
        merged = True
        while merged and len(groups) > 1:
            merged = False
            new_groups = []
            used_indices = set()

            for i in range(len(groups)):
                if i in used_indices:
                    continue

                current_group = groups[i]
                merged_group = current_group

                for j in range(i + 1, len(groups)):
                    if j in used_indices:
                        continue

                    other_group = groups[j]
                    overlap_score = self._calculate_group_overlap(
                        merged_group, other_group
                    )

                    if overlap_score > self.config.get("merge_threshold", 0.5):
                        # 合并分组
                        merged_chunks = list(
                            set(merged_group.chunks + other_group.chunks)
                        )
                        merged_embedding = (
                            np.mean(
                                [chunk.embedding for chunk in merged_chunks], axis=0
                            )
                            if all(
                                chunk.embedding is not None for chunk in merged_chunks
                            )
                            else None
                        )

                        merged_group = ContentGroup(
                            group_id=f"merged_{merged_group.group_id}_{other_group.group_id}",
                            chunks=merged_chunks,
                            centroid_embedding=merged_embedding,
                        )
                        used_indices.add(j)
                        merged = True

                new_groups.append(merged_group)
                used_indices.add(i)

            groups = new_groups

        return groups

    def _calculate_group_overlap(
        self, group1: ContentGroup, group2: ContentGroup
    ) -> float:
        """计算两个分组的重叠度"""
        chunks1 = set(chunk.id for chunk in group1.chunks)
        chunks2 = set(chunk.id for chunk in group2.chunks)

        if not chunks1 or not chunks2:
            return 0.0

        intersection = len(chunks1.intersection(chunks2))
        union = len(chunks1.union(chunks2))

        return intersection / union if union > 0 else 0.0

    async def _optimize_groups(self, groups: List[ContentGroup]) -> List[ContentGroup]:
        """优化分组结果"""
        optimized_groups = []

        for group in groups:
            if len(group.chunks) < self.config.get("min_group_size", 2):
                # 过小的分组，尝试合并到最近的其他分组
                if len(groups) > 1:
                    best_match = await self._find_best_match_group(group, groups)
                    if best_match and best_match != group:
                        best_match.chunks.extend(group.chunks)
                        continue

            # 计算分组质量分数
            quality_score = await self._calculate_group_quality(group)
            if quality_score >= self.config.get("min_quality_threshold", 0.3):
                optimized_groups.append(group)

        return optimized_groups

    async def _find_best_match_group(
        self, target_group: ContentGroup, all_groups: List[ContentGroup]
    ) -> Optional[ContentGroup]:
        """找到目标分组的最佳匹配分组"""
        if not target_group.centroid_embedding:
            return None

        best_match = None
        best_similarity = -1

        for group in all_groups:
            if group == target_group or not group.centroid_embedding:
                continue

            similarity = cosine_similarity(
                [target_group.centroid_embedding], [group.centroid_embedding]
            )[0][0]

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = group

        return (
            best_match
            if best_similarity > self.config.get("merge_similarity_threshold", 0.6)
            else None
        )

    async def _calculate_group_quality(self, group: ContentGroup) -> float:
        """计算分组质量分数"""
        if len(group.chunks) < 2:
            return 1.0  # 单元素分组质量最高

        # 计算组内相似度
        embeddings = [
            chunk.embedding for chunk in group.chunks if chunk.embedding is not None
        ]
        if not embeddings:
            return 0.0

        similarity_matrix = cosine_similarity(embeddings)
        intra_similarity = np.mean(similarity_matrix)

        # 考虑分组大小因素
        size_factor = min(
            1.0, len(group.chunks) / self.config.get("optimal_group_size", 10)
        )

        return float(intra_similarity * size_factor)

    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """获取管道性能指标"""
        return {
            "active_strategies": [s.__name__ for s in self.grouping_strategies],
            "embedding_model": self.embedding_model.__class__.__name__,
            "status": "active",
        }


# 工厂函数
async def create_adaptive_grouping_pipeline(
    config: Dict[str, Any],
) -> AdaptiveGroupingPipeline:
    """创建自适应分组管道实例"""
    return AdaptiveGroupingPipeline(config)


if __name__ == "__main__":
    # 测试代码
    async def test_pipeline():
        config = {
            "embedding_model": "all-MiniLM-L6-v2",
            "grouping_strategies": [
                {"name": "semantic_similarity"},
                {"name": "topic_clustering"},
            ],
            "similarity_threshold": 0.6,
            "min_group_size": 2,
        }

        pipeline = AdaptiveGroupingPipeline(config)

        # 创建测试数据
        test_chunks = [
            ContentChunk(id=f"chunk_{i}", content=f"测试内容 {i}") for i in range(10)
        ]

        groups = await pipeline.process_batch(test_chunks)
        print(f"生成 {len(groups)} 个分组")

    asyncio.run(test_pipeline())
