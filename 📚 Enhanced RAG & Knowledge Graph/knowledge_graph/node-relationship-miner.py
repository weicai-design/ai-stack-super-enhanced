"""
知识图谱节点关系挖掘引擎
功能：从RAG处理后的数据中自动挖掘实体间的语义关系，构建丰富的知识网络
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

import networkx as nx
import numpy as np
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Entity:
    """实体数据类"""

    id: str
    name: str
    type: str
    confidence: float
    attributes: Dict[str, Any]
    source_documents: List[str]


@dataclass
class Relationship:
    """关系数据类"""

    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    evidence: List[str]
    attributes: Dict[str, Any]


class NodeRelationshipMiner:
    """节点关系挖掘引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 初始化NLP模型
        try:
import spacy
try:
    # 优先尝试中文模型
    import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

    print("中文模型加载成功\")
except OSError:
    try:
        # 回退到英文模型
        import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

        print("英文模型加载成功\")
    except OSError:
        # 如果都没有，下载英文模型
        print("下载英文模型中...\")
        import os
        os.system('python -m spacy download en_core_web_sm')
        import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

        print("英文模型下载并加载成功\")

        except OSError:
            self.logger.warning("中文模型未找到，使用英文模型")
import spacy
try:
    # 优先尝试中文模型
    import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

    print("中文模型加载成功\")
except OSError:
    try:
        # 回退到英文模型
        import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

        print("英文模型加载成功\")
    except OSError:
        # 如果都没有，下载英文模型
        print("下载英文模型中...\")
        import os
        os.system('python -m spacy download en_core_web_sm')
        import spacy
try:
    # 优先尝试中文模型
    nlp = spacy.load('zh_core_web_sm')
    print('中文模型加载成功')
except OSError:
    try:
        # 回退到英文模型
        nlp = spacy.load('en_core_web_sm')
        print('英文模型加载成功')
    except OSError:
        # 如果都没有，使用空模型
        print('spaCy模型未找到，使用空模型')
        nlp = spacy.blank('en')

        print("英文模型下载并加载成功\")


        # 关系类型映射
        self.relation_patterns = self._load_relation_patterns()
        self.entity_graph = nx.MultiDiGraph()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)

        self.logger.info("节点关系挖掘引擎初始化完成")

    def _load_relation_patterns(self) -> Dict[str, List[str]]:
        """加载关系模式配置"""
        return {
            "is_a": ["是", "属于", "作为", "当做", "视为"],
            "part_of": ["包含", "包括", "组成部分", "属于", "隶属于"],
            "has_property": ["具有", "拥有", "带有", "具备", "属性"],
            "located_in": ["位于", "处在", "在...地方", "坐落于", "位置"],
            "created_by": ["创建", "制作", "发明", "设计", "开发"],
            "used_for": ["用于", "用来", "用途", "功能", "作用"],
            "similar_to": ["类似", "相似", "像", "相同", "接近"],
            "related_to": ["相关", "关联", "联系", "涉及", "关系到"],
        }

    async def initialize(self):
        """异步初始化"""
        self.logger.info("开始异步初始化节点关系挖掘引擎")
        # 预加载必要的资源
        await self._preload_resources()
        self.logger.info("节点关系挖掘引擎异步初始化完成")

    async def _preload_resources(self):
        """预加载资源"""
        # 模拟资源加载
        await asyncio.sleep(0.1)

    async def mine_relationships(
        self, entities: List[Entity], text_chunks: List[str]
    ) -> List[Relationship]:
        """
        从实体和文本块中挖掘关系

        Args:
            entities: 实体列表
            text_chunks: 文本块列表

        Returns:
            关系列表
        """
        self.logger.info(
            f"开始挖掘关系，实体数量: {len(entities)}, 文本块数量: {len(text_chunks)}"
        )

        relationships = []

        try:
            # 1. 基于共现的关系挖掘
            cooccurrence_relations = await self._mine_cooccurrence_relationships(
                entities, text_chunks
            )
            relationships.extend(cooccurrence_relations)

            # 2. 基于语义的关系挖掘
            semantic_relations = await self._mine_semantic_relationships(
                entities, text_chunks
            )
            relationships.extend(semantic_relations)

            # 3. 基于模式的关系挖掘
            pattern_relations = await self._mine_pattern_relationships(
                text_chunks, entities
            )
            relationships.extend(pattern_relations)

            # 4. 关系去重和融合
            relationships = self._deduplicate_relationships(relationships)

            # 5. 更新知识图谱
            await self._update_knowledge_graph(entities, relationships)

        except Exception as e:
            self.logger.error(f"关系挖掘过程中发生错误: {str(e)}")
            raise

        self.logger.info(f"关系挖掘完成，共发现 {len(relationships)} 个关系")
        return relationships

    async def _mine_cooccurrence_relationships(
        self, entities: List[Entity], text_chunks: List[str]
    ) -> List[Relationship]:
        """基于共现的关系挖掘"""
        relationships = []
        entity_names = [entity.name for entity in entities]
        entity_dict = {entity.name: entity for entity in entities}

        # 构建共现矩阵
        cooccurrence_matrix = self._build_cooccurrence_matrix(entity_names, text_chunks)

        # 基于共现强度创建关系
        for i, entity1 in enumerate(entity_names):
            for j, entity2 in enumerate(entity_names):
                if i != j and cooccurrence_matrix[i][j] > 0:
                    confidence = min(cooccurrence_matrix[i][j] * 0.1, 1.0)

                    relationship = Relationship(
                        source_entity=entity_dict[entity1].id,
                        target_entity=entity_dict[entity2].id,
                        relation_type="related_to",
                        confidence=confidence,
                        evidence=self._find_cooccurrence_evidence(
                            entity1, entity2, text_chunks
                        ),
                        attributes={"cooccurrence_strength": cooccurrence_matrix[i][j]},
                    )
                    relationships.append(relationship)

        return relationships

    def _build_cooccurrence_matrix(
        self, entity_names: List[str], text_chunks: List[str]
    ) -> np.ndarray:
        """构建共现矩阵"""
        n_entities = len(entity_names)
        matrix = np.zeros((n_entities, n_entities))

        for chunk in text_chunks:
            chunk_lower = chunk.lower()
            present_entities = []

            for i, entity in enumerate(entity_names):
                if entity.lower() in chunk_lower:
                    present_entities.append(i)

            # 更新共现计数
            for i in present_entities:
                for j in present_entities:
                    if i != j:
                        matrix[i][j] += 1

        return matrix

    async def _mine_semantic_relationships(
        self, entities: List[Entity], text_chunks: List[str]
    ) -> List[Relationship]:
        """基于语义的关系挖掘"""
        relationships = []

        if len(text_chunks) < 2:
            return relationships

        try:
            # 使用TF-IDF计算文本相似度
            tfidf_matrix = self.vectorizer.fit_transform(text_chunks)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 基于语义相似度创建关系
            entity_chunk_mapping = self._map_entities_to_chunks(entities, text_chunks)

            for entity1 in entities:
                for entity2 in entities:
                    if entity1.id != entity2.id:
                        similarity = self._calculate_entity_similarity(
                            entity1, entity2, entity_chunk_mapping, similarity_matrix
                        )

                        if similarity > 0.3:  # 相似度阈值
                            relationship = Relationship(
                                source_entity=entity1.id,
                                target_entity=entity2.id,
                                relation_type="similar_to",
                                confidence=similarity,
                                evidence=[f"语义相似度: {similarity:.3f}"],
                                attributes={"semantic_similarity": similarity},
                            )
                            relationships.append(relationship)

        except Exception as e:
            self.logger.warning(f"语义关系挖掘失败: {str(e)}")

        return relationships

    def _map_entities_to_chunks(
        self, entities: List[Entity], text_chunks: List[str]
    ) -> Dict[str, List[int]]:
        """映射实体到文本块"""
        mapping = defaultdict(list)

        for chunk_idx, chunk in enumerate(text_chunks):
            chunk_lower = chunk.lower()
            for entity in entities:
                if entity.name.lower() in chunk_lower:
                    mapping[entity.id].append(chunk_idx)

        return mapping

    def _calculate_entity_similarity(
        self,
        entity1: Entity,
        entity2: Entity,
        mapping: Dict[str, List[int]],
        similarity_matrix: np.ndarray,
    ) -> float:
        """计算实体间相似度"""
        chunks1 = mapping.get(entity1.id, [])
        chunks2 = mapping.get(entity2.id, [])

        if not chunks1 or not chunks2:
            return 0.0

        # 计算平均相似度
        similarities = []
        for chunk1 in chunks1:
            for chunk2 in chunks2:
                if chunk1 != chunk2:
                    similarities.append(similarity_matrix[chunk1][chunk2])

        return np.mean(similarities) if similarities else 0.0

    async def _mine_pattern_relationships(
        self, text_chunks: List[str], entities: List[Entity]
    ) -> List[Relationship]:
        """基于模式的关系挖掘"""
        relationships = []
        entity_dict = {entity.name: entity for entity in entities}

        for chunk in text_chunks:
            doc = self.nlp(chunk)

            # 分析句子结构寻找关系
            for sent in doc.sents:
                sent_text = sent.text

                for rel_type, patterns in self.relation_patterns.items():
                    for pattern in patterns:
                        if pattern in sent_text:
                            # 在句子中寻找实体
                            found_entities = self._find_entities_in_sentence(
                                sent_text, entity_dict
                            )

                            if len(found_entities) >= 2:
                                # 创建关系
                                relationship = Relationship(
                                    source_entity=found_entities[0].id,
                                    target_entity=found_entities[1].id,
                                    relation_type=rel_type,
                                    confidence=0.7,  # 模式匹配的基础置信度
                                    evidence=[sent_text],
                                    attributes={
                                        "pattern": pattern,
                                        "sentence": sent_text,
                                    },
                                )
                                relationships.append(relationship)

        return relationships

    def _find_entities_in_sentence(
        self, sentence: str, entity_dict: Dict[str, Entity]
    ) -> List[Entity]:
        """在句子中查找实体"""
        found_entities = []
        sentence_lower = sentence.lower()

        for entity_name, entity in entity_dict.items():
            if entity_name.lower() in sentence_lower:
                found_entities.append(entity)

        # 按在句子中出现的位置排序
        found_entities.sort(key=lambda e: sentence_lower.find(e.name.lower()))
        return found_entities

    def _find_cooccurrence_evidence(
        self, entity1: str, entity2: str, text_chunks: List[str]
    ) -> List[str]:
        """查找共现证据"""
        evidence = []

        for chunk in text_chunks:
            chunk_lower = chunk.lower()
            if entity1.lower() in chunk_lower and entity2.lower() in chunk_lower:
                # 截取相关部分作为证据
                evidence.append(chunk[:200] + "..." if len(chunk) > 200 else chunk)
                if len(evidence) >= 3:  # 最多保存3个证据
                    break

        return evidence

    def _deduplicate_relationships(
        self, relationships: List[Relationship]
    ) -> List[Relationship]:
        """关系去重"""
        unique_relationships = {}

        for rel in relationships:
            key = (rel.source_entity, rel.target_entity, rel.relation_type)

            if key in unique_relationships:
                # 合并证据，取最高置信度
                existing_rel = unique_relationships[key]
                if rel.confidence > existing_rel.confidence:
                    existing_rel.confidence = rel.confidence
                existing_rel.evidence.extend(rel.evidence)
                # 合并属性
                existing_rel.attributes.update(rel.attributes)
            else:
                unique_relationships[key] = rel

        return list(unique_relationships.values())

    async def _update_knowledge_graph(
        self, entities: List[Entity], relationships: List[Relationship]
    ):
        """更新知识图谱"""
        # 添加节点
        for entity in entities:
            self.entity_graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                confidence=entity.confidence,
                attributes=entity.attributes,
            )

        # 添加边
        for relationship in relationships:
            self.entity_graph.add_edge(
                relationship.source_entity,
                relationship.target_entity,
                relation_type=relationship.relation_type,
                confidence=relationship.confidence,
                evidence=relationship.evidence,
                attributes=relationship.attributes,
            )

    def get_relationship_stats(self) -> Dict[str, Any]:
        """获取关系统计信息"""
        return {
            "total_nodes": self.entity_graph.number_of_nodes(),
            "total_relationships": self.entity_graph.number_of_edges(),
            "node_types": defaultdict(int),
            "relationship_types": defaultdict(int),
        }

    async def export_relationships(self, format: str = "json") -> Dict[str, Any]:
        """导出关系数据"""
        nodes_data = []
        edges_data = []

        for node_id, node_data in self.entity_graph.nodes(data=True):
            nodes_data.append({"id": node_id, **node_data})

        for source, target, edge_data in self.entity_graph.edges(data=True):
            edges_data.append({"source": source, "target": target, **edge_data})

        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "metadata": self.get_relationship_stats(),
        }

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理节点关系挖掘引擎资源")
        self.entity_graph.clear()
