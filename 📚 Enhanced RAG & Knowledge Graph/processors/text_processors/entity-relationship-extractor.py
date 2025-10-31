"""
Entity and Relationship Extractor
版本: 1.0.0
功能: 实体关系提取器
描述: 基于深度学习的实体识别和关系提取，构建知识图谱基础
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import networkx as nx
import spacy

from . import TextProcessingConfig, TextProcessorBase, register_processor

logger = logging.getLogger("text_processor.entity_extractor")


@dataclass
class Entity:
    """实体数据类"""

    text: str
    type: str
    start_pos: int
    end_pos: int
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class Relationship:
    """关系数据类"""

    subject: Entity
    predicate: str
    object: Entity
    confidence: float
    context: str
    metadata: Dict[str, Any]


class EntityRelationshipExtractor(TextProcessorBase):
    """实体关系提取器"""

    def __init__(self, config: TextProcessingConfig):
        super().__init__(config)
        self.nlp = None
        self.entity_types = {}
        self.relationship_patterns = []
        self.knowledge_graph = nx.MultiDiGraph()

    async def _initialize_components(self):
        """初始化实体关系提取组件"""
        try:
            # 加载spacy模型（简化实现，实际应使用更复杂的NLP模型）
            await self._load_nlp_model()

            # 初始化实体类型定义
            await self._initialize_entity_types()

            # 编译关系提取模式
            await self._compile_relationship_patterns()

            logger.info("实体关系提取器组件初始化完成")

        except Exception as e:
            logger.error(f"实体关系提取器初始化失败: {str(e)}")
            raise

    async def _load_nlp_model(self):
        """加载NLP模型"""
        try:
            # 这里使用spacy的英文小模型作为示例
            # 实际应用中应该根据语言选择合适模型，或使用自定义训练模型
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spacy模型未找到，使用基于规则的实体识别")
            self.nlp = None

    async def _initialize_entity_types(self):
        """初始化实体类型定义"""
        self.entity_types = {
            "PERSON": {
                "patterns": [
                    r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",  # 英文人名
                    r"\b([\u4e00-\u9fff]{2,4})\b",  # 中文人名
                ],
                "description": "人物实体",
                "priority": 1,
            },
            "ORGANIZATION": {
                "patterns": [
                    r"\b([A-Z][a-zA-Z& ]+ (?:Inc|Corp|Company|Ltd|Co\.))\b",
                    r"\b(大学|学院|公司|集团|医院|学校)\b",
                ],
                "description": "组织机构",
                "priority": 2,
            },
            "LOCATION": {
                "patterns": [
                    r"\b([A-Z][a-zA-Z ]+ (?:City|State|Country|Street|Avenue))\b",
                    r"\b(北京|上海|广州|深圳|纽约|伦敦|东京)\b",
                ],
                "description": "地理位置",
                "priority": 3,
            },
            "DATE": {
                "patterns": [
                    r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b",
                    r"\b(今天|昨天|明天|今年|去年|明年)\b",
                ],
                "description": "时间日期",
                "priority": 4,
            },
            "PRODUCT": {
                "patterns": [
                    r"\b([A-Z][a-zA-Z0-9]+ (?:Pro|Max|Lite|Edition))\b",
                    r"\b(产品|软件|系统|应用|平台)\b",
                ],
                "description": "产品服务",
                "priority": 5,
            },
        }

    async def _compile_relationship_patterns(self):
        """编译关系提取模式"""
        self.relationship_patterns = [
            # 雇佣关系
            {
                "name": "employment",
                "patterns": [
                    r"(\w+)在(\w+)工作",
                    r"(\w+)就职于(\w+)",
                    r"(\w+)是(\w+)的(员工|职员|雇员)",
                ],
                "subject_type": "PERSON",
                "object_type": "ORGANIZATION",
                "predicate": "works_at",
            },
            # 位置关系
            {
                "name": "location",
                "patterns": [
                    r"(\w+)位于(\w+)",
                    r"(\w+)在(\w+)的(位置|地方)",
                    r"(\w+)的地址是(\w+)",
                ],
                "subject_type": "ORGANIZATION",
                "object_type": "LOCATION",
                "predicate": "located_in",
            },
            # 时间关系
            {
                "name": "event_time",
                "patterns": [
                    r"在(\w+)发生",
                    r"(\w+)于(\w+)举行",
                    r"(\w+)的日期是(\w+)",
                ],
                "subject_type": "PRODUCT",
                "object_type": "DATE",
                "predicate": "happened_at",
            },
        ]

    async def _process_impl(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行实体关系提取"""
        try:
            extraction_result = {
                "entities": [],
                "relationships": [],
                "knowledge_graph": {},
                "extraction_metrics": {},
            }

            # 实体识别
            entities = await self._extract_entities(text)
            extraction_result["entities"] = entities

            # 关系提取
            relationships = await self._extract_relationships(text, entities)
            extraction_result["relationships"] = relationships

            # 构建知识图谱
            knowledge_graph = await self._build_knowledge_graph(entities, relationships)
            extraction_result["knowledge_graph"] = knowledge_graph

            # 计算提取指标
            metrics = await self._calculate_extraction_metrics(
                entities, relationships, text
            )
            extraction_result["extraction_metrics"] = metrics

            logger.info(
                f"实体关系提取完成: {len(entities)} 实体, {len(relationships)} 关系"
            )
            return extraction_result

        except Exception as e:
            logger.error(f"实体关系提取失败: {str(e)}")
            raise

    async def _extract_entities(self, text: str) -> List[Entity]:
        """提取文本中的实体"""
        entities = []

        # 使用spacy进行实体识别（如果可用）
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                entity = Entity(
                    text=ent.text,
                    type=ent.label_,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    confidence=0.9,  # spacy的默认置信度
                    metadata={
                        "source": "spacy",
                        "lemma": ent.lemma_,
                        "is_oov": ent.is_oov,
                    },
                )
                entities.append(entity)

        # 使用基于规则的实体识别作为补充
        rule_based_entities = await self._rule_based_entity_extraction(text)
        entities.extend(rule_based_entities)

        # 去重和合并
        entities = await self._deduplicate_entities(entities)

        return entities

    async def _rule_based_entity_extraction(self, text: str) -> List[Entity]:
        """基于规则的实体识别"""
        entities = []

        for entity_type, type_config in self.entity_types.items():
            for pattern_str in type_config["patterns"]:
                try:
                    pattern = re.compile(pattern_str, re.UNICODE)
                    for match in pattern.finditer(text):
                        entity_text = (
                            match.group(1) if match.groups() else match.group()
                        )

                        entity = Entity(
                            text=entity_text,
                            type=entity_type,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            confidence=0.7,  # 规则匹配的置信度
                            metadata={
                                "source": "rule_based",
                                "pattern": pattern_str,
                                "match_group": match.groups(),
                            },
                        )
                        entities.append(entity)

                except Exception as e:
                    logger.warning(f"实体模式匹配失败 {pattern_str}: {str(e)}")
                    continue

        return entities

    async def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """实体去重和合并"""
        unique_entities = {}

        for entity in entities:
            key = (entity.text.lower(), entity.type, entity.start_pos)

            if key not in unique_entities:
                unique_entities[key] = entity
            else:
                # 合并重叠的实体，选择置信度更高的
                existing = unique_entities[key]
                if entity.confidence > existing.confidence:
                    unique_entities[key] = entity

        return list(unique_entities.values())

    async def _extract_relationships(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """提取实体间的关系"""
        relationships = []

        # 基于模式的关系提取
        for pattern_config in self.relationship_patterns:
            pattern_relationships = await self._pattern_based_relationship_extraction(
                text, entities, pattern_config
            )
            relationships.extend(pattern_relationships)

        # 基于依赖分析的关系提取（如果spacy可用）
        if self.nlp:
            dependency_relationships = (
                await self._dependency_based_relationship_extraction(text, entities)
            )
            relationships.extend(dependency_relationships)

        # 去重关系
        relationships = await self._deduplicate_relationships(relationships)

        return relationships

    async def _pattern_based_relationship_extraction(
        self, text: str, entities: List[Entity], pattern_config: Dict[str, Any]
    ) -> List[Relationship]:
        """基于模式的关系提取"""
        relationships = []

        for pattern_str in pattern_config["patterns"]:
            try:
                pattern = re.compile(pattern_str, re.UNICODE)
                for match in pattern.finditer(text):
                    if len(match.groups()) >= 2:
                        subject_text = match.group(1)
                        object_text = match.group(2)

                        # 查找匹配的实体
                        subject_entity = self._find_matching_entity(
                            entities, subject_text, pattern_config["subject_type"]
                        )
                        object_entity = self._find_matching_entity(
                            entities, object_text, pattern_config["object_type"]
                        )

                        if subject_entity and object_entity:
                            relationship = Relationship(
                                subject=subject_entity,
                                predicate=pattern_config["predicate"],
                                object=object_entity,
                                confidence=0.8,
                                context=match.group(),
                                metadata={
                                    "source": "pattern_based",
                                    "pattern_name": pattern_config["name"],
                                    "match_text": match.group(),
                                },
                            )
                            relationships.append(relationship)

            except Exception as e:
                logger.warning(f"关系模式匹配失败 {pattern_str}: {str(e)}")
                continue

        return relationships

    async def _dependency_based_relationship_extraction(
        self, text: str, entities: List[Entity]
    ) -> List[Relationship]:
        """基于依赖分析的关系提取"""
        relationships = []

        if not self.nlp:
            return relationships

        try:
            doc = self.nlp(text)

            # 简化的依赖关系分析
            for sent in doc.sents:
                sent_entities = [
                    e
                    for e in entities
                    if e.start_pos >= sent.start_char and e.end_pos <= sent.end_char
                ]

                # 分析句子中的实体对
                for i, subj_entity in enumerate(sent_entities):
                    for j, obj_entity in enumerate(sent_entities):
                        if i != j:
                            # 检查是否存在语法路径连接这两个实体
                            relationship = await self._analyze_entity_relationship(
                                subj_entity, obj_entity, sent, text
                            )
                            if relationship:
                                relationships.append(relationship)

        except Exception as e:
            logger.warning(f"依赖分析关系提取失败: {str(e)}")

        return relationships

    async def _analyze_entity_relationship(
        self, subject: Entity, object: Entity, sentence, text: str
    ) -> Optional[Relationship]:
        """分析两个实体间的语法关系"""
        try:
            # 获取实体在句子中的位置
            subj_start = subject.start_pos - sentence.start_char
            subj_end = subject.end_pos - sentence.start_char
            obj_start = object.start_pos - sentence.start_char
            obj_end = object.end_pos - sentence.start_char

            # 简化的关系判断逻辑
            # 实际应使用更复杂的语法分析和语义角色标注

            # 检查实体间的距离和语法结构
            distance = abs(subj_start - obj_start)
            if distance > 100:  # 实体距离太远，关系可能性低
                return None

            # 基于实体类型和位置猜测关系类型
            predicate = self._infer_relationship_type(subject.type, object.type)
            if not predicate:
                return None

            # 提取关系上下文
            context_start = min(subj_start, obj_start)
            context_end = max(subj_end, obj_end)
            context = (
                sentence.text[context_start:context_end]
                if context_end <= len(sentence.text)
                else sentence.text
            )

            relationship = Relationship(
                subject=subject,
                predicate=predicate,
                object=object,
                confidence=0.6,  # 依赖分析的置信度较低
                context=context,
                metadata={
                    "source": "dependency_based",
                    "sentence_length": len(sentence.text),
                    "entity_distance": distance,
                },
            )

            return relationship

        except Exception as e:
            logger.debug(f"实体关系分析失败: {str(e)}")
            return None

    def _find_matching_entity(
        self, entities: List[Entity], text: str, entity_type: str
    ) -> Optional[Entity]:
        """查找匹配的实体"""
        for entity in entities:
            # 检查文本匹配和类型匹配
            if (
                entity.text == text or text in entity.text
            ) and entity.type == entity_type:
                return entity
        return None

    def _infer_relationship_type(
        self, subject_type: str, object_type: str
    ) -> Optional[str]:
        """基于实体类型推断关系类型"""
        relationship_mapping = {
            ("PERSON", "ORGANIZATION"): "works_at",
            ("ORGANIZATION", "LOCATION"): "located_in",
            ("PERSON", "LOCATION"): "lives_in",
            ("PRODUCT", "ORGANIZATION"): "developed_by",
            ("PERSON", "DATE"): "born_on",
        }

        return relationship_mapping.get((subject_type, object_type))

    async def _deduplicate_relationships(
        self, relationships: List[Relationship]
    ) -> List[Relationship]:
        """关系去重"""
        unique_relationships = {}

        for rel in relationships:
            key = (rel.subject.text, rel.predicate, rel.object.text)

            if key not in unique_relationships:
                unique_relationships[key] = rel
            else:
                # 选择置信度更高的关系
                existing = unique_relationships[key]
                if rel.confidence > existing.confidence:
                    unique_relationships[key] = rel

        return list(unique_relationships.values())

    async def _build_knowledge_graph(
        self, entities: List[Entity], relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """构建知识图谱"""
        graph = nx.MultiDiGraph()

        # 添加实体节点
        for entity in entities:
            graph.add_node(
                entity.text,
                type=entity.type,
                confidence=entity.confidence,
                metadata=entity.metadata,
            )

        # 添加关系边
        for relationship in relationships:
            graph.add_edge(
                relationship.subject.text,
                relationship.object.text,
                predicate=relationship.predicate,
                confidence=relationship.confidence,
                context=relationship.context,
                metadata=relationship.metadata,
            )

        # 计算图指标
        graph_metrics = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "connected_components": nx.number_connected_components(
                graph.to_undirected()
            ),
            "density": nx.density(graph),
            "average_degree": (
                sum(dict(graph.degree()).values()) / graph.number_of_nodes()
                if graph.number_of_nodes() > 0
                else 0
            ),
        }

        # 转换为可序列化的格式
        graph_data = {
            "nodes": [
                {
                    "id": node,
                    "type": graph.nodes[node].get("type", "UNKNOWN"),
                    "confidence": graph.nodes[node].get("confidence", 0.0),
                }
                for node in graph.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "predicate": graph[u][v][0].get("predicate", "related_to"),
                    "confidence": graph[u][v][0].get("confidence", 0.0),
                }
                for u, v in graph.edges()
            ],
            "metrics": graph_metrics,
        }

        return graph_data

    async def _calculate_extraction_metrics(
        self, entities: List[Entity], relationships: List[Relationship], text: str
    ) -> Dict[str, float]:
        """计算提取质量指标"""
        metrics = {}

        # 实体提取指标
        metrics["entity_density"] = (
            len(entities) / len(text.split()) if text.split() else 0
        )
        metrics["entity_coverage"] = (
            sum(len(e.text) for e in entities) / len(text) if text else 0
        )

        # 关系提取指标
        metrics["relationship_density"] = (
            len(relationships) / len(entities) if entities else 0
        )

        # 置信度指标
        metrics["avg_entity_confidence"] = (
            sum(e.confidence for e in entities) / len(entities) if entities else 0
        )
        metrics["avg_relationship_confidence"] = (
            sum(r.confidence for r in relationships) / len(relationships)
            if relationships
            else 0
        )

        # 多样性指标
        entity_types = set(e.type for e in entities)
        metrics["entity_type_diversity"] = (
            len(entity_types) / len(self.entity_types) if self.entity_types else 0
        )

        relationship_types = set(r.predicate for r in relationships)
        metrics["relationship_type_diversity"] = len(relationship_types)

        # 综合质量分数
        metrics["overall_quality"] = (
            metrics["avg_entity_confidence"] * 0.4
            + metrics["avg_relationship_confidence"] * 0.3
            + metrics["entity_type_diversity"] * 0.2
            + min(metrics["relationship_density"], 1.0) * 0.1
        )

        return metrics


# 注册处理器
register_processor("entity_relationship_extractor", EntityRelationshipExtractor)
logger.info("实体关系提取器注册完成")
