"""
动态知识图谱引擎
负责构建、更新和查询动态知识图谱，支持实体关系挖掘和图结构优化
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import networkx as nx

logger = logging.getLogger(__name__)


class GraphUpdateType(Enum):
    """知识图谱更新类型"""

    ENTITY_ADD = "entity_add"
    ENTITY_UPDATE = "entity_update"
    ENTITY_REMOVE = "entity_remove"
    RELATION_ADD = "relation_add"
    RELATION_UPDATE = "relation_update"
    RELATION_REMOVE = "relation_remove"


@dataclass
class KnowledgeEntity:
    """知识实体"""

    id: str
    name: str
    entity_type: str
    properties: Dict[str, Any]
    confidence: float
    source_documents: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class KnowledgeRelation:
    """知识关系"""

    id: str
    source_entity: str
    target_entity: str
    relation_type: str
    properties: Dict[str, Any]
    confidence: float
    source_documents: List[str]
    created_at: datetime


class DynamicKnowledgeGraph:
    """动态知识图谱引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = nx.MultiDiGraph()
        self.entity_index: Dict[str, KnowledgeEntity] = {}
        self.relation_index: Dict[str, KnowledgeRelation] = {}
        self.document_entity_map: Dict[str, Set[str]] = {}
        self.entity_document_map: Dict[str, Set[str]] = {}

        # 初始化配置参数
        self.min_confidence = config.get("min_confidence", 0.7)
        self.max_entities_per_doc = config.get("max_entities_per_doc", 50)
        self.enable_auto_merge = config.get("enable_auto_merge", True)

        logger.info("动态知识图谱引擎初始化完成")

    async def initialize(self) -> None:
        """初始化知识图谱"""
        try:
            # 加载现有知识图谱数据（如果有）
            await self._load_existing_knowledge()
            logger.info("知识图谱初始化完成")
        except Exception as e:
            logger.error(f"知识图谱初始化失败: {e}")
            raise

    async def add_document_knowledge(
        self,
        document_id: str,
        entities: List[KnowledgeEntity],
        relations: List[KnowledgeRelation],
    ) -> Dict[str, Any]:
        """
        添加文档知识到图谱

        Args:
            document_id: 文档ID
            entities: 实体列表
            relations: 关系列表

        Returns:
            添加结果的统计信息
        """
        try:
            stats = {
                "entities_added": 0,
                "entities_merged": 0,
                "relations_added": 0,
                "conflicts_resolved": 0,
            }

            # 处理实体
            for entity in entities:
                if entity.confidence >= self.min_confidence:
                    result = await self._process_entity(entity, document_id)
                    stats["entities_added"] += result["added"]
                    stats["entities_merged"] += result["merged"]

            # 处理关系
            for relation in relations:
                if (
                    relation.confidence >= self.min_confidence
                    and relation.source_entity in self.entity_index
                    and relation.target_entity in self.entity_index
                ):
                    await self._add_relation(relation, document_id)
                    stats["relations_added"] += 1

            # 更新文档映射
            await self._update_document_mappings(document_id, entities)

            logger.info(f"文档 {document_id} 知识添加完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"添加文档知识失败 {document_id}: {e}")
            raise

    async def _process_entity(
        self, entity: KnowledgeEntity, document_id: str
    ) -> Dict[str, int]:
        """处理实体添加或合并"""
        result = {"added": 0, "merged": 0}

        if entity.id in self.entity_index:
            # 实体已存在，进行合并
            if self.enable_auto_merge:
                await self._merge_entities(self.entity_index[entity.id], entity)
                result["merged"] = 1
        else:
            # 添加新实体
            self.entity_index[entity.id] = entity
            self.graph.add_node(entity.id, **entity.properties)
            result["added"] = 1

        return result

    async def _merge_entities(
        self, existing_entity: KnowledgeEntity, new_entity: KnowledgeEntity
    ) -> None:
        """合并实体信息"""
        # 合并属性
        for key, value in new_entity.properties.items():
            if key not in existing_entity.properties:
                existing_entity.properties[key] = value
            elif isinstance(value, (int, float)) and isinstance(
                existing_entity.properties[key], (int, float)
            ):
                # 数值类型属性取平均值
                existing_entity.properties[key] = (
                    existing_entity.properties[key] + value
                ) / 2

        # 合并来源文档
        existing_entity.source_documents.extend(
            doc
            for doc in new_entity.source_documents
            if doc not in existing_entity.source_documents
        )

        # 更新置信度和时间戳
        existing_entity.confidence = max(
            existing_entity.confidence, new_entity.confidence
        )
        existing_entity.updated_at = datetime.now()

    async def _add_relation(
        self, relation: KnowledgeRelation, document_id: str
    ) -> None:
        """添加关系到图谱"""
        self.relation_index[relation.id] = relation
        self.graph.add_edge(
            relation.source_entity,
            relation.target_entity,
            key=relation.id,
            relation_type=relation.relation_type,
            **relation.properties,
        )

    async def _update_document_mappings(
        self, document_id: str, entities: List[KnowledgeEntity]
    ) -> None:
        """更新文档-实体映射关系"""
        entity_ids = {entity.id for entity in entities}
        self.document_entity_map[document_id] = entity_ids

        for entity_id in entity_ids:
            if entity_id not in self.entity_document_map:
                self.entity_document_map[entity_id] = set()
            self.entity_document_map[entity_id].add(document_id)

    async def query_entities(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> List[KnowledgeEntity]:
        """
        查询实体

        Args:
            query: 查询文本
            entity_types: 实体类型过滤
            min_confidence: 最小置信度

        Returns:
            匹配的实体列表
        """
        results = []

        for entity in self.entity_index.values():
            if entity.confidence >= min_confidence and (
                not entity_types or entity.entity_type in entity_types
            ):

                # 简单名称匹配（实际应使用更复杂的语义匹配）
                if query.lower() in entity.name.lower():
                    results.append(entity)

        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    async def find_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        查找相关实体

        Args:
            entity_id: 实体ID
            relation_types: 关系类型过滤
            max_depth: 最大搜索深度

        Returns:
            相关实体和路径信息
        """
        if entity_id not in self.graph:
            return {"entities": [], "paths": []}

        related_entities = set()
        paths = []

        # BFS搜索相关实体
        visited = {entity_id}
        queue = [(entity_id, [entity_id])]

        while queue and len(visited) < 100:  # 限制最大节点数
            current_entity, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor in self.graph.neighbors(current_entity):
                if neighbor not in visited:
                    visited.add(neighbor)

                    # 检查关系类型过滤
                    edge_data = self.graph.get_edge_data(current_entity, neighbor)
                    if edge_data:
                        should_include = True
                        if relation_types:
                            should_include = any(
                                edge_data[key]["relation_type"] in relation_types
                                for key in edge_data
                            )

                        if should_include:
                            related_entities.add(neighbor)
                            new_path = path + [neighbor]
                            paths.append(new_path)
                            queue.append((neighbor, new_path))

        return {
            "entities": [self.entity_index[eid] for eid in related_entities],
            "paths": paths,
        }

    async def get_graph_metrics(self) -> Dict[str, Any]:
        """获取图谱指标"""
        return {
            "total_entities": len(self.entity_index),
            "total_relations": len(self.relation_index),
            "total_documents": len(self.document_entity_map),
            "graph_density": nx.density(self.graph),
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "average_clustering": nx.average_clustering(self.graph.to_undirected()),
            "degree_centrality": dict(nx.degree_centrality(self.graph)),
        }

    async def _load_existing_knowledge(self) -> None:
        """加载现有知识图谱数据"""
        # 从持久化存储加载数据（如果存在）
        try:
            import os
            import pickle

            storage_path = self.config.get("storage_path", "./data")
            os.makedirs(storage_path, exist_ok=True)

            kg_file = os.path.join(storage_path, "knowledge_graph.pkl")
            if os.path.exists(kg_file):
                with open(kg_file, "rb") as f:
                    data = pickle.load(f)

                # 恢复索引与映射
                self.entity_index = data.get("entity_index", {})
                self.relation_index = data.get("relation_index", {})
                self.document_entity_map = {
                    k: set(v) for k, v in data.get("document_entity_map", {}).items()
                }
                self.entity_document_map = {
                    k: set(v) for k, v in data.get("entity_document_map", {}).items()
                }

                # 恢复 networkx 图（如果有序列化数据）
                graph_data = data.get("graph")
                if graph_data is not None:
                    try:
                        import networkx as nx

                        self.graph = nx.node_link_graph(graph_data)
                    except Exception:
                        # fallback: ignore graph restore
                        pass

                # Convert stored simple entities back to KnowledgeEntity dataclass if necessary
                # (stored objects may already be KnowledgeEntity instances)
                logger.info("Loaded existing knowledge graph snapshot")
            else:
                logger.info("No existing knowledge graph snapshot found")

        except Exception as e:
            logger.error(f"Failed to load existing knowledge graph: {e}")

    async def save_knowledge_graph(self) -> None:
        """保存知识图谱数据"""
        try:
            import os
            import pickle
            from copy import deepcopy

            storage_path = self.config.get("storage_path", "./data")
            os.makedirs(storage_path, exist_ok=True)

            kg_file = os.path.join(storage_path, "knowledge_graph.pkl")

            # 序列化 networkx graph 为 node-link 数据，以确保跨版本兼容
            try:
                from networkx.readwrite import json_graph

                graph_data = json_graph.node_link_data(self.graph)
            except Exception:
                graph_data = None

            data = {
                "entity_index": deepcopy(self.entity_index),
                "relation_index": deepcopy(self.relation_index),
                "document_entity_map": {
                    k: list(v) for k, v in self.document_entity_map.items()
                },
                "entity_document_map": {
                    k: list(v) for k, v in self.entity_document_map.items()
                },
                "graph": graph_data,
            }

            with open(kg_file, "wb") as f:
                pickle.dump(data, f)

            logger.info(f"Knowledge graph saved to {kg_file}")

        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")

    # Compatibility adapter methods expected by external components
    def query(self, query_text: str, **kwargs) -> List[KnowledgeEntity]:
        """
        同步适配器：兼容旧接口名称 `query`，内部调用异步 `query_entities`。
        返回匹配的实体列表（同步阻塞风格）。
        """
        try:
            # 调用异步方法以兼容现有逻辑
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.query_entities(query_text, **kwargs))
            loop.close()
            return results
        except Exception as e:
            logger.error(f"query adapter failed: {e}")
            return []

    def get_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        同步适配器：兼容 `get_related_entities` 名称，映射到 `find_related_entities`。
        返回包含实体和路径信息的字典。
        """
        try:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self.find_related_entities(
                    entity_id, relation_types=relation_types, max_depth=max_depth
                )
            )
            loop.close()
            return results
        except Exception as e:
            logger.error(f"get_related_entities adapter failed: {e}")
            return {"entities": [], "paths": []}


# 导出公共接口
__all__ = [
    "DynamicKnowledgeGraph",
    "KnowledgeEntity",
    "KnowledgeRelation",
    "GraphUpdateType",
]
