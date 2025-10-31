#!/usr/bin/env python3
"""
图谱构建引擎 - 知识图谱自动构建与优化
功能：从融合知识自动构建知识图谱，支持实体识别、关系抽取、图谱优化
版本：1.0.0
"""

import asyncio
import logging
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """关系类型枚举"""

    SEMANTIC_SIMILARITY = "semantic_similarity"
    ENTITY_RELATION = "entity_relation"
    TOPIC_ASSOCIATION = "topic_association"
    TEMPORAL_RELATION = "temporal_relation"
    CAUSAL_RELATION = "causal_relation"
    HIERARCHICAL_RELATION = "hierarchical_relation"


class NodeType(Enum):
    """节点类型枚举"""

    KNOWLEDGE_PIECE = "knowledge_piece"
    ENTITY = "entity"
    TOPIC = "topic"
    CONCEPT = "concept"
    DOCUMENT = "document"


@dataclass
class GraphNode:
    """图谱节点数据结构"""

    id: str
    node_type: NodeType
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_references: List[str] = field(default_factory=list)
    created_time: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """图谱边数据结构"""

    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    weight: float = 1.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """知识图谱数据结构"""

    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: Dict[str, GraphEdge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: GraphNode):
        """添加节点"""
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        """添加边"""
        self.edges[edge.id] = edge

    def get_node_edges(self, node_id: str) -> List[GraphEdge]:
        """获取节点的所有边"""
        return [
            edge
            for edge in self.edges.values()
            if edge.source_node_id == node_id or edge.target_node_id == node_id
        ]

    def to_networkx(self) -> nx.Graph:
        """转换为NetworkX图对象"""
        G = nx.Graph()

        # 添加节点
        for node_id, node in self.nodes.items():
            G.add_node(
                node_id,
                node_type=node.node_type.value,
                content=node.content,
                confidence=node.confidence,
            )

        # 添加边
        for edge_id, edge in self.edges.items():
            G.add_edge(
                edge.source_node_id,
                edge.target_node_id,
                relationship_type=edge.relationship_type.value,
                weight=edge.weight,
                confidence=edge.confidence,
            )

        return G


class GraphConstructionEngine:
    """
    图谱构建引擎 - 自动构建和优化知识图谱
    支持多策略关系发现和图谱质量优化
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.entity_recognizer = None
        self.relation_extractor = None
        self.community_detector = None
        self._initialize_components()

        logger.info("图谱构建引擎初始化完成")

    def _initialize_components(self):
        """初始化组件"""
        # 初始化实体识别器
        self._initialize_entity_recognizer()

        # 初始化关系抽取器
        self._initialize_relation_extractor()

        # 初始化社区检测器
        self._initialize_community_detector()

        # 初始化缓存
        self.entity_cache = {}
        self.relation_cache = {}

    def _initialize_entity_recognizer(self):
        """初始化实体识别器"""
        # 这里可以集成spaCy、BERT等实体识别模型
        # 当前使用基于规则的简化实现
        self.entity_recognizer = SimpleEntityRecognizer(
            self.config.get("entity_recognition", {})
        )

    def _initialize_relation_extractor(self):
        """初始化关系抽取器"""
        self.relation_extractor = RelationExtractor(
            self.config.get("relation_extraction", {})
        )

    def _initialize_community_detector(self):
        """初始化社区检测器"""
        self.community_detector = CommunityDetector(
            self.config.get("community_detection", {})
        )

    async def build_knowledge_graph(
        self, fused_knowledge: List[Any], strategy: str = "comprehensive"
    ) -> KnowledgeGraph:
        """
        构建知识图谱 - 主要入口方法

        Args:
            fused_knowledge: 融合后的知识列表
            strategy: 构建策略 ('comprehensive', 'fast', 'accurate')

        Returns:
            构建的知识图谱
        """
        if not fused_knowledge:
            logger.warning("输入知识为空")
            return KnowledgeGraph()

        logger.info(
            f"开始构建知识图谱，输入知识: {len(fused_knowledge)} 个，策略: {strategy}"
        )

        try:
            # 步骤1: 创建基础节点
            knowledge_graph = await self._create_base_nodes(fused_knowledge)

            # 步骤2: 实体识别和提取
            await self._extract_and_link_entities(knowledge_graph)

            # 步骤3: 关系发现和构建
            await self._discover_and_build_relations(knowledge_graph, strategy)

            # 步骤4: 图谱优化和清理
            optimized_graph = await self._optimize_knowledge_graph(knowledge_graph)

            # 步骤5: 社区发现和标注
            await self._detect_and_label_communities(optimized_graph)

            logger.info(
                f"图谱构建完成，节点: {len(optimized_graph.nodes)}，边: {len(optimized_graph.edges)}"
            )
            return optimized_graph

        except Exception as e:
            logger.error(f"图谱构建失败: {e}")
            raise

    async def _create_base_nodes(self, fused_knowledge: List[Any]) -> KnowledgeGraph:
        """创建基础知识节点"""
        knowledge_graph = KnowledgeGraph()

        for i, knowledge in enumerate(fused_knowledge):
            # 创建知识节点
            knowledge_node = GraphNode(
                id=f"knowledge_{i}",
                node_type=NodeType.KNOWLEDGE_PIECE,
                content=knowledge.content,
                metadata=knowledge.fused_metadata,
                confidence=knowledge.confidence_score,
                source_references=knowledge.supporting_sources,
            )
            knowledge_graph.add_node(knowledge_node)

        logger.info(f"创建 {len(knowledge_graph.nodes)} 个基础节点")
        return knowledge_graph

    async def _extract_and_link_entities(self, knowledge_graph: KnowledgeGraph):
        """提取实体并链接到知识节点"""
        entity_nodes = {}
        entity_to_knowledge = defaultdict(list)

        # 从所有知识节点提取实体
        for node_id, node in knowledge_graph.nodes.items():
            if node.node_type != NodeType.KNOWLEDGE_PIECE:
                continue

            entities = await self.entity_recognizer.extract_entities(node.content)

            for entity_text, entity_info in entities.items():
                entity_id = self._generate_entity_id(entity_text)

                # 创建或获取实体节点
                if entity_id not in entity_nodes:
                    entity_node = GraphNode(
                        id=entity_id,
                        node_type=NodeType.ENTITY,
                        content=entity_text,
                        metadata=entity_info,
                        confidence=entity_info.get("confidence", 0.8),
                    )
                    entity_nodes[entity_id] = entity_node
                    knowledge_graph.add_node(entity_node)

                # 记录实体-知识关联
                entity_to_knowledge[entity_id].append(node_id)

        # 创建实体-知识关系边
        for entity_id, knowledge_ids in entity_to_knowledge.items():
            for knowledge_id in knowledge_ids:
                edge = GraphEdge(
                    id=f"entity_link_{entity_id}_{knowledge_id}",
                    source_node_id=entity_id,
                    target_node_id=knowledge_id,
                    relationship_type=RelationshipType.ENTITY_RELATION,
                    weight=1.0,
                    confidence=0.9,
                    metadata={"association_type": "mention"},
                )
                knowledge_graph.add_edge(edge)

        logger.info(
            f"提取 {len(entity_nodes)} 个实体，创建 {len(entity_to_knowledge)} 个关联"
        )

    async def _discover_and_build_relations(
        self, knowledge_graph: KnowledgeGraph, strategy: str
    ):
        """发现和构建关系"""
        # 获取所有知识节点
        knowledge_nodes = [
            node
            for node in knowledge_graph.nodes.values()
            if node.node_type == NodeType.KNOWLEDGE_PIECE
        ]

        if len(knowledge_nodes) < 2:
            logger.warning("知识节点数量不足，无法构建关系")
            return

        # 应用多种关系发现策略
        relation_strategies = self._get_relation_strategies(strategy)

        for strategy_name, strategy_func in relation_strategies.items():
            try:
                await strategy_func(knowledge_graph, knowledge_nodes)
                logger.debug(f"关系策略 {strategy_name} 完成")
            except Exception as e:
                logger.warning(f"关系策略 {strategy_name} 执行失败: {e}")

    def _get_relation_strategies(self, strategy: str) -> Dict[str, callable]:
        """获取关系发现策略"""
        base_strategies = {
            "semantic_similarity": self._build_semantic_relations,
            "temporal_relations": self._build_temporal_relations,
            "entity_cooccurrence": self._build_entity_cooccurrence_relations,
        }

        if strategy == "fast":
            return {"semantic_similarity": base_strategies["semantic_similarity"]}
        elif strategy == "accurate":
            return {
                "semantic_similarity": base_strategies["semantic_similarity"],
                "entity_cooccurrence": base_strategies["entity_cooccurrence"],
            }
        else:  # comprehensive
            return base_strategies

    async def _build_semantic_relations(
        self, knowledge_graph: KnowledgeGraph, knowledge_nodes: List[GraphNode]
    ):
        """构建语义相似度关系"""
        # 生成节点嵌入向量（如果尚未生成）
        nodes_with_embeddings = await self._generate_node_embeddings(knowledge_nodes)

        # 计算相似度矩阵
        embeddings = [node.embedding for node in nodes_with_embeddings]
        similarity_matrix = await self._calculate_similarity_matrix(embeddings)

        # 基于相似度创建关系边
        threshold = self.config.get("similarity_threshold", 0.7)
        edges_created = 0

        for i in range(len(nodes_with_embeddings)):
            for j in range(i + 1, len(nodes_with_embeddings)):
                similarity = similarity_matrix[i][j]

                if similarity > threshold:
                    node_i = nodes_with_embeddings[i]
                    node_j = nodes_with_embeddings[j]

                    edge = GraphEdge(
                        id=f"semantic_{node_i.id}_{node_j.id}",
                        source_node_id=node_i.id,
                        target_node_id=node_j.id,
                        relationship_type=RelationshipType.SEMANTIC_SIMILARITY,
                        weight=float(similarity),
                        confidence=float(similarity * 0.8),  # 基于相似度的置信度
                        metadata={"similarity_score": float(similarity)},
                    )
                    knowledge_graph.add_edge(edge)
                    edges_created += 1

        logger.info(f"创建 {edges_created} 个语义关系边")

    async def _generate_node_embeddings(
        self, nodes: List[GraphNode]
    ) -> List[GraphNode]:
        """生成节点嵌入向量"""
        from sentence_transformers import SentenceTransformer

        # 检查是否已有嵌入
        nodes_without_embedding = [node for node in nodes if node.embedding is None]

        if not nodes_without_embedding:
            return nodes

        # 加载模型
        model_name = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        model = SentenceTransformer(model_name)

        # 生成嵌入
        contents = [node.content for node in nodes_without_embedding]
        embeddings = model.encode(contents)

        # 关联嵌入到节点
        for node, embedding in zip(nodes_without_embedding, embeddings):
            node.embedding = embedding

        return nodes

    async def _calculate_similarity_matrix(
        self, embeddings: List[np.ndarray]
    ) -> np.ndarray:
        """计算相似度矩阵"""
        from sklearn.metrics.pairwise import cosine_similarity

        if not embeddings:
            return np.array([])

        return cosine_similarity(embeddings)

    async def _build_temporal_relations(
        self, knowledge_graph: KnowledgeGraph, knowledge_nodes: List[GraphNode]
    ):
        """构建时间关系"""
        # 提取时间信息并构建时序关系
        temporal_data = []

        for node in knowledge_nodes:
            timestamp = await self._extract_timestamp_from_metadata(node.metadata)
            if timestamp:
                temporal_data.append((node, timestamp))

        # 按时间排序
        temporal_data.sort(key=lambda x: x[1])

        # 创建时序关系
        edges_created = 0
        for i in range(len(temporal_data) - 1):
            node_i, time_i = temporal_data[i]
            node_j, time_j = temporal_data[i + 1]

            time_gap = (time_j - time_i).total_seconds()

            # 创建时序关系边
            edge = GraphEdge(
                id=f"temporal_{node_i.id}_{node_j.id}",
                source_node_id=node_i.id,
                target_node_id=node_j.id,
                relationship_type=RelationshipType.TEMPORAL_RELATION,
                weight=1.0 / (1 + time_gap / 86400),  # 时间差距的倒数，按天缩放
                confidence=0.7,
                metadata={"time_gap_seconds": time_gap, "sequence_order": i},
            )
            knowledge_graph.add_edge(edge)
            edges_created += 1

        logger.info(f"创建 {edges_created} 个时间关系边")

    async def _extract_timestamp_from_metadata(
        self, metadata: Dict[str, Any]
    ) -> Optional[datetime]:
        """从元数据中提取时间戳"""
        timestamp_str = metadata.get("timestamp")
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # 尝试其他时间字段
        for time_field in ["created_time", "timestamp", "date"]:
            time_value = metadata.get(time_field)
            if time_value and isinstance(time_value, str):
                try:
                    return datetime.fromisoformat(time_value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

        return None

    async def _build_entity_cooccurrence_relations(
        self, knowledge_graph: KnowledgeGraph, knowledge_nodes: List[GraphNode]
    ):
        """构建实体共现关系"""
        # 获取所有实体节点
        entity_nodes = [
            node
            for node in knowledge_graph.nodes.values()
            if node.node_type == NodeType.ENTITY
        ]

        if len(entity_nodes) < 2:
            return

        # 计算实体共现矩阵
        cooccurrence_matrix = await self._calculate_entity_cooccurrence(knowledge_graph)

        # 基于共现强度创建关系
        threshold = self.config.get("cooccurrence_threshold", 0.3)
        edges_created = 0

        entity_ids = list(cooccurrence_matrix.keys())

        for i, entity_id_i in enumerate(entity_ids):
            for j, entity_id_j in enumerate(entity_ids[i + 1 :], i + 1):
                cooccurrence_strength = cooccurrence_matrix[entity_id_i].get(
                    entity_id_j, 0
                )

                if cooccurrence_strength > threshold:
                    edge = GraphEdge(
                        id=f"cooccurrence_{entity_id_i}_{entity_id_j}",
                        source_node_id=entity_id_i,
                        target_node_id=entity_id_j,
                        relationship_type=RelationshipType.ENTITY_RELATION,
                        weight=float(cooccurrence_strength),
                        confidence=float(cooccurrence_strength * 0.9),
                        metadata={
                            "cooccurrence_strength": float(cooccurrence_strength)
                        },
                    )
                    knowledge_graph.add_edge(edge)
                    edges_created += 1

        logger.info(f"创建 {edges_created} 个实体共现关系边")

    async def _calculate_entity_cooccurrence(
        self, knowledge_graph: KnowledgeGraph
    ) -> Dict[str, Dict[str, float]]:
        """计算实体共现矩阵"""
        # 统计实体在知识节点中的共现
        entity_occurrences = defaultdict(set)

        # 收集每个实体出现的知识节点
        for edge in knowledge_graph.edges.values():
            if edge.relationship_type == RelationshipType.ENTITY_RELATION:
                source_type = knowledge_graph.nodes[edge.source_node_id].node_type
                target_type = knowledge_graph.nodes[edge.target_node_id].node_type

                if (
                    source_type == NodeType.ENTITY
                    and target_type == NodeType.KNOWLEDGE_PIECE
                ):
                    entity_occurrences[edge.source_node_id].add(edge.target_node_id)
                elif (
                    target_type == NodeType.ENTITY
                    and source_type == NodeType.KNOWLEDGE_PIECE
                ):
                    entity_occurrences[edge.target_node_id].add(edge.source_node_id)

        # 计算共现强度
        cooccurrence_matrix = defaultdict(dict)
        entity_ids = list(entity_occurrences.keys())

        for i, entity_id_i in enumerate(entity_ids):
            occurrences_i = entity_occurrences[entity_id_i]

            for j, entity_id_j in enumerate(entity_ids[i + 1 :], i + 1):
                occurrences_j = entity_occurrences[entity_id_j]

                # 计算Jaccard相似度作为共现强度
                intersection = len(occurrences_i.intersection(occurrences_j))
                union = len(occurrences_i.union(occurrences_j))

                if union > 0:
                    cooccurrence_strength = intersection / union
                    cooccurrence_matrix[entity_id_i][
                        entity_id_j
                    ] = cooccurrence_strength
                    cooccurrence_matrix[entity_id_j][
                        entity_id_i
                    ] = cooccurrence_strength

        return cooccurrence_matrix

    async def _optimize_knowledge_graph(
        self, knowledge_graph: KnowledgeGraph
    ) -> KnowledgeGraph:
        """优化知识图谱"""
        # 移除低权重边
        optimized_graph = await self._filter_low_weight_edges(knowledge_graph)

        # 合并相似节点
        optimized_graph = await self._merge_similar_nodes(optimized_graph)

        # 优化图结构
        optimized_graph = await self._optimize_graph_structure(optimized_graph)

        logger.info(
            f"图谱优化完成，节点: {len(optimized_graph.nodes)}，边: {len(optimized_graph.edges)}"
        )
        return optimized_graph

    async def _filter_low_weight_edges(
        self, knowledge_graph: KnowledgeGraph
    ) -> KnowledgeGraph:
        """过滤低权重边"""
        min_weight = self.config.get("min_edge_weight", 0.1)
        min_confidence = self.config.get("min_edge_confidence", 0.3)

        filtered_edges = {}

        for edge_id, edge in knowledge_graph.edges.items():
            if edge.weight >= min_weight and edge.confidence >= min_confidence:
                filtered_edges[edge_id] = edge

        knowledge_graph.edges = filtered_edges
        logger.info(f"边过滤完成，保留 {len(filtered_edges)} 个边")

        return knowledge_graph

    async def _merge_similar_nodes(
        self, knowledge_graph: KnowledgeGraph
    ) -> KnowledgeGraph:
        """合并相似节点"""
        # 主要合并实体节点
        entity_nodes = [
            node
            for node in knowledge_graph.nodes.values()
            if node.node_type == NodeType.ENTITY
        ]

        if len(entity_nodes) < 2:
            return knowledge_graph

        # 基于内容相似度聚类实体
        from sklearn.cluster import AgglomerativeClustering

        # 生成实体嵌入
        entity_embeddings = []
        valid_entities = []

        for entity in entity_nodes:
            if entity.embedding is not None:
                entity_embeddings.append(entity.embedding)
                valid_entities.append(entity)

        if len(valid_entities) < 2:
            return knowledge_graph

        # 层次聚类
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.config.get("node_merge_threshold", 0.3),
            metric="cosine",
        )

        cluster_labels = clustering.fit_predict(entity_embeddings)

        # 合并同一簇的节点
        clusters = defaultdict(list)
        for entity, label in zip(valid_entities, cluster_labels):
            clusters[label].append(entity)

        merged_nodes = {}
        nodes_to_remove = set()

        for cluster_id, cluster_entities in clusters.items():
            if len(cluster_entities) > 1:
                # 合并实体
                merged_entity = await self._merge_entity_nodes(cluster_entities)
                merged_nodes[merged_entity.id] = merged_entity

                # 标记要删除的原始节点
                for entity in cluster_entities:
                    nodes_to_remove.add(entity.id)

        # 更新图谱
        for node_id in nodes_to_remove:
            if node_id in knowledge_graph.nodes:
                del knowledge_graph.nodes[node_id]

        for merged_node in merged_nodes.values():
            knowledge_graph.add_node(merged_node)

        # 更新边连接
        await self._update_edges_after_merge(
            knowledge_graph, nodes_to_remove, merged_nodes
        )

        logger.info(f"节点合并完成，合并 {len(merged_nodes)} 组节点")
        return knowledge_graph

    async def _merge_entity_nodes(self, entities: List[GraphNode]) -> GraphNode:
        """合并实体节点"""
        # 选择最常用的实体文本作为合并后的内容
        content_counter = Counter([entity.content for entity in entities])
        most_common_content = content_counter.most_common(1)[0][0]

        # 合并元数据
        merged_metadata = {}
        merged_sources = []
        total_confidence = 0

        for entity in entities:
            merged_metadata.update(entity.metadata)
            merged_sources.extend(entity.source_references)
            total_confidence += entity.confidence

        # 创建合并节点
        merged_id = f"merged_entity_{uuid.uuid4().hex[:8]}"

        return GraphNode(
            id=merged_id,
            node_type=NodeType.ENTITY,
            content=most_common_content,
            metadata=merged_metadata,
            confidence=total_confidence / len(entities),
            source_references=list(set(merged_sources)),
        )

    async def _update_edges_after_merge(
        self,
        knowledge_graph: KnowledgeGraph,
        removed_nodes: Set[str],
        merged_nodes: Dict[str, GraphNode],
    ):
        """在节点合并后更新边连接"""
        updated_edges = {}

        for edge_id, edge in knowledge_graph.edges.items():
            # 检查边是否连接到被删除的节点
            source_removed = edge.source_node_id in removed_nodes
            target_removed = edge.target_node_id in removed_nodes

            if not source_removed and not target_removed:
                # 边保持不变
                updated_edges[edge_id] = edge
            else:
                # 需要重新连接边
                new_source = await self._find_replacement_node(
                    edge.source_node_id, removed_nodes, merged_nodes
                )
                new_target = await self._find_replacement_node(
                    edge.target_node_id, removed_nodes, merged_nodes
                )

                if new_source and new_target and new_source != new_target:
                    new_edge = GraphEdge(
                        id=f"merged_{new_source}_{new_target}",
                        source_node_id=new_source,
                        target_node_id=new_target,
                        relationship_type=edge.relationship_type,
                        weight=edge.weight,
                        confidence=edge.confidence * 0.9,  # 合并后置信度略有下降
                        metadata=edge.metadata,
                    )
                    updated_edges[new_edge.id] = new_edge

        knowledge_graph.edges = updated_edges

    async def _find_replacement_node(
        self,
        original_node_id: str,
        removed_nodes: Set[str],
        merged_nodes: Dict[str, GraphNode],
    ) -> Optional[str]:
        """查找替换节点"""
        if original_node_id not in removed_nodes:
            return original_node_id

        # 在合并节点中查找对应的节点
        original_content = None
        for removed_id in removed_nodes:
            if removed_id == original_node_id:
                # 这里需要访问原始节点内容，简化处理返回第一个合并节点
                if merged_nodes:
                    return next(iter(merged_nodes.keys()))

        return None

    async def _optimize_graph_structure(
        self, knowledge_graph: KnowledgeGraph
    ) -> KnowledgeGraph:
        """优化图结构"""
        # 移除孤立节点（没有边连接的节点）
        connected_nodes = set()

        for edge in knowledge_graph.edges.values():
            connected_nodes.add(edge.source_node_id)
            connected_nodes.add(edge.target_node_id)

        # 保留有连接的节点和实体节点
        nodes_to_keep = {}
        for node_id, node in knowledge_graph.nodes.items():
            if node_id in connected_nodes or node.node_type == NodeType.ENTITY:
                nodes_to_keep[node_id] = node

        knowledge_graph.nodes = nodes_to_keep
        logger.info(f"结构优化完成，保留 {len(nodes_to_keep)} 个节点")

        return knowledge_graph

    async def _detect_and_label_communities(self, knowledge_graph: KnowledgeGraph):
        """检测和标注社区"""
        if len(knowledge_graph.nodes) < 3:
            return

        # 转换为NetworkX图
        nx_graph = knowledge_graph.to_networkx()

        # 使用Louvain算法检测社区
        try:
            import community as community_louvain

            partition = community_louvain.best_partition(
                nx_graph,
                resolution=self.config.get("community_detection_resolution", 1.0),
            )

            # 标注社区信息
            communities = defaultdict(list)
            for node_id, community_id in partition.items():
                communities[community_id].append(node_id)

            # 为每个社区生成标签
            for community_id, node_ids in communities.items():
                if len(node_ids) >= self.config.get("min_community_size", 3):
                    community_label = await self._generate_community_label(
                        knowledge_graph, node_ids
                    )

                    # 在元数据中记录社区信息
                    for node_id in node_ids:
                        if node_id in knowledge_graph.nodes:
                            node_metadata = knowledge_graph.nodes[node_id].metadata
                            node_metadata["community_id"] = community_id
                            node_metadata["community_label"] = community_label

            logger.info(f"检测到 {len(communities)} 个社区")

        except ImportError:
            logger.warning("未安装python-louvain库，跳过社区检测")

    async def _generate_community_label(
        self, knowledge_graph: KnowledgeGraph, node_ids: List[str]
    ) -> str:
        """生成社区标签"""
        # 提取社区内节点的关键词
        all_contents = []
        for node_id in node_ids:
            node = knowledge_graph.nodes.get(node_id)
            if node:
                all_contents.append(node.content)

        if not all_contents:
            return f"Community_{hash(tuple(node_ids)) % 10000}"

        # 使用TF-IDF提取关键词（简化实现）
        from sklearn.feature_extraction.text import TfidfVectorizer

        try:
            vectorizer = TfidfVectorizer(max_features=5, stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(all_contents)

            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.sum(axis=0).A1

            top_indices = tfidf_scores.argsort()[-3:][::-1]  # 取前3个关键词
            top_keywords = [feature_names[i] for i in top_indices]

            return "_".join(top_keywords)

        except Exception as e:
            logger.warning(f"社区标签生成失败: {e}")
            return f"Community_{len(node_ids)}_nodes"

    def _generate_entity_id(self, entity_text: str) -> str:
        """生成实体ID"""
        import hashlib

        hash_object = hashlib.md5(entity_text.encode())
        return f"entity_{hash_object.hexdigest()[:10]}"

    async def export_graph(
        self, knowledge_graph: KnowledgeGraph, format: str = "networkx"
    ) -> Any:
        """导出图谱"""
        if format == "networkx":
            return knowledge_graph.to_networkx()
        elif format == "dict":
            return {
                "nodes": {
                    node_id: {
                        "id": node.id,
                        "type": node.node_type.value,
                        "content": node.content,
                        "confidence": node.confidence,
                    }
                    for node_id, node in knowledge_graph.nodes.items()
                },
                "edges": {
                    edge_id: {
                        "id": edge.id,
                        "source": edge.source_node_id,
                        "target": edge.target_node_id,
                        "type": edge.relationship_type.value,
                        "weight": edge.weight,
                    }
                    for edge_id, edge in knowledge_graph.edges.items()
                },
            }
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_engine_metrics(self) -> Dict[str, Any]:
        """获取引擎性能指标"""
        return {
            "entity_cache_size": len(self.entity_cache),
            "relation_cache_size": len(self.relation_cache),
            "status": "active",
        }


# 辅助类
class SimpleEntityRecognizer:
    """简单实体识别器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def extract_entities(self, text: str) -> Dict[str, Dict[str, Any]]:
        """提取实体"""
        # 这里可以集成真正的实体识别模型
        # 当前使用基于规则的简单实现

        entities = {}

        # 简单的名词短语识别（简化实现）
        import re

        # 匹配可能的名词短语
        noun_phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)

        for phrase in noun_phrases:
            if len(phrase.split()) <= 3:  # 限制短语长度
                entities[phrase] = {
                    "type": "ENTITY",
                    "confidence": 0.7,
                    "source": "rule_based",
                }

        return entities


class RelationExtractor:
    """关系抽取器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def extract_relations(self, text: str) -> List[Dict[str, Any]]:
        """抽取关系"""
        # 这里可以集成真正的关系抽取模型
        # 当前返回空列表
        return []


class CommunityDetector:
    """社区检测器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config


# 工厂函数
async def create_graph_construction_engine(
    config: Dict[str, Any],
) -> GraphConstructionEngine:
    """创建图谱构建引擎实例"""
    return GraphConstructionEngine(config)


if __name__ == "__main__":
    # 测试代码
    async def test_graph_engine():
        config = {
            "similarity_threshold": 0.7,
            "min_edge_weight": 0.1,
            "min_edge_confidence": 0.3,
            "community_detection_resolution": 1.0,
            "min_community_size": 3,
        }

        engine = GraphConstructionEngine(config)

        # 创建测试数据
        from knowledge_fusion_engine import FusedKnowledge

        test_knowledge = [
            FusedKnowledge(
                id=f"knowledge_{i}",
                content=f"测试知识内容 {i}，包含一些实体提及",
                supporting_sources=[f"source_{i}"],
                confidence_score=0.9,
                resolution_strategy="test",
                fused_metadata={"timestamp": datetime.now().isoformat()},
                entities=[f"Entity_{i}"],
                creation_time=datetime.now(),
            )
            for i in range(5)
        ]

        knowledge_graph = await engine.build_knowledge_graph(test_knowledge)
        print(
            f"构建图谱完成，节点: {len(knowledge_graph.nodes)}，边: {len(knowledge_graph.edges)}"
        )

    asyncio.run(test_graph_engine())
