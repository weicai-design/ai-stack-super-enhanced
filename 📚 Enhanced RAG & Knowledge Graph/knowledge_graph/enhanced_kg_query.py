"""
Enhanced Knowledge Graph Query Engine
增强的知识图谱查询引擎

根据需求1.8：优化知识图谱查询功能

功能：
1. 多维度查询（实体、关系、路径）
2. 语义查询
3. 图遍历查询
4. 统计查询
5. 查询性能优化
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


class EnhancedKGQueryEngine:
    """
    增强的知识图谱查询引擎
    
    提供多种查询方式和性能优化
    """

    def __init__(self, kg_nodes: Dict, kg_edges: List[Dict]):
        """
        初始化查询引擎
        
        Args:
            kg_nodes: 知识图谱节点字典
            kg_edges: 知识图谱边列表
        """
        self.kg_nodes = kg_nodes
        self.kg_edges = kg_edges
        
        # 构建索引以提高查询性能
        self._build_indices()

    def _build_indices(self):
        """构建查询索引"""
        # 按类型索引节点
        self.nodes_by_type: Dict[str, List[str]] = defaultdict(list)
        for node_id, node in self.kg_nodes.items():
            node_type = node.get("type", "unknown")
            self.nodes_by_type[node_type].append(node_id)

        # 构建边的索引
        self.edges_by_source: Dict[str, List[Dict]] = defaultdict(list)
        self.edges_by_target: Dict[str, List[Dict]] = defaultdict(list)
        self.edges_by_type: Dict[str, List[Dict]] = defaultdict(list)

        for edge in self.kg_edges:
            src = edge.get("src")
            dst = edge.get("dst")
            edge_type = edge.get("type", "unknown")

            if src:
                self.edges_by_source[src].append(edge)
            if dst:
                self.edges_by_target[dst].append(edge)
            self.edges_by_type[edge_type].append(edge)

    def query_entities(
        self,
        entity_type: Optional[str] = None,
        value_pattern: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询实体（支持缓存）
        
        Args:
            entity_type: 实体类型（可选）
            value_pattern: 值模式（正则表达式，可选）
            limit: 返回数量限制
            
        Returns:
            实体列表
        """
        # 尝试从缓存获取
        if self.cache:
            cached_result = self.cache.get(
                query_type="entities",
                entity_type=entity_type,
                value_pattern=value_pattern,
                limit=limit,
            )
            if cached_result is not None:
                return cached_result
        
        results = []

        # 确定要查询的节点
        if entity_type:
            node_ids = self.nodes_by_type.get(entity_type, [])
        else:
            node_ids = list(self.kg_nodes.keys())

        # 应用值模式过滤
        pattern = None
        if value_pattern:
            try:
                pattern = re.compile(value_pattern, re.IGNORECASE)
            except re.error:
                logger.warning(f"无效的正则表达式: {value_pattern}")
                pattern = None

        for node_id in node_ids[:limit]:
            node = self.kg_nodes.get(node_id)
            if not node:
                continue

            # 值模式匹配
            if pattern:
                node_value = node.get("value", "")
                if not pattern.search(node_value):
                    continue

            # 添加统计信息
            entity = {
                "id": node_id,
                "type": node.get("type"),
                "value": node.get("value"),
                "count": node.get("count", 0),
            }

            # 计算相关度（基于连接的边数）
            entity["degree"] = len(self.edges_by_source.get(node_id, [])) + len(
                self.edges_by_target.get(node_id, [])
            )

            results.append(entity)

        # 按度数排序（更相关的在前）
        results.sort(key=lambda x: x.get("degree", 0), reverse=True)

        # 存入缓存
        if self.cache:
            self.cache.set(
                query_type="entities",
                result=results,
                entity_type=entity_type,
                value_pattern=value_pattern,
                limit=limit,
            )

        return results

    def query_relations(
        self,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
        relation_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询关系
        
        Args:
            source_entity: 源实体ID（可选）
            target_entity: 目标实体ID（可选）
            relation_type: 关系类型（可选）
            limit: 返回数量限制
            
        Returns:
            关系列表
        """
        results = []

        # 确定候选边
        if source_entity:
            candidates = self.edges_by_source.get(source_entity, [])
        elif target_entity:
            candidates = self.edges_by_target.get(target_entity, [])
        elif relation_type:
            candidates = self.edges_by_type.get(relation_type, [])
        else:
            candidates = self.kg_edges

        # 应用过滤
        for edge in candidates[:limit]:
            if source_entity and edge.get("src") != source_entity:
                continue
            if target_entity and edge.get("dst") != target_entity:
                continue
            if relation_type and edge.get("type") != relation_type:
                continue

            # 获取实体信息
            src_node = self.kg_nodes.get(edge.get("src"))
            dst_node = self.kg_nodes.get(edge.get("dst"))

            relation = {
                "id": f"{edge.get('src')}_{edge.get('type')}_{edge.get('dst')}",
                "source": {
                    "id": edge.get("src"),
                    "type": src_node.get("type") if src_node else None,
                    "value": src_node.get("value") if src_node else None,
                },
                "target": {
                    "id": edge.get("dst"),
                    "type": dst_node.get("type") if dst_node else None,
                    "value": dst_node.get("value") if dst_node else None,
                },
                "type": edge.get("type"),
            }

            results.append(relation)

        # 存入缓存
        if self.cache:
            self.cache.set(
                query_type="relations",
                result=results,
                source_entity=source_entity,
                target_entity=target_entity,
                relation_type=relation_type,
                limit=limit,
            )

        return results

    def query_path(
        self,
        source_entity: str,
        target_entity: str,
        max_depth: int = 3,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        查询两个实体之间的路径
        
        Args:
            source_entity: 源实体ID
            target_entity: 目标实体ID
            max_depth: 最大深度
            
        Returns:
            路径列表（如果找到）
        """
        if source_entity not in self.kg_nodes or target_entity not in self.kg_nodes:
            return None

        # 使用BFS查找路径
        from collections import deque

        queue = deque([(source_entity, [source_entity])])
        visited = {source_entity}

        while queue:
            current, path = queue.popleft()

            if len(path) > max_depth:
                continue

            # 查找所有连接的节点
            for edge in self.edges_by_source.get(current, []):
                next_node = edge.get("dst")
                if not next_node:
                    continue

                if next_node == target_entity:
                    # 找到路径
                    return path + [target_entity]

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [next_node]))

        return None

    def query_subgraph(
        self,
        center_entity: str,
        max_depth: int = 2,
        max_nodes: int = 50,
    ) -> Dict[str, Any]:
        """
        查询子图（以某个实体为中心）
        
        Args:
            center_entity: 中心实体ID
            max_depth: 最大深度
            max_nodes: 最大节点数
            
        Returns:
            子图数据（节点和边）
        """
        if center_entity not in self.kg_nodes:
            return {"nodes": [], "edges": []}

        # BFS遍历
        from collections import deque

        nodes_set: Set[str] = {center_entity}
        edges_set: Set[Tuple[str, str, str]] = set()
        queue = deque([(center_entity, 0)])

        while queue and len(nodes_set) < max_nodes:
            current, depth = queue.popleft()

            if depth >= max_depth:
                continue

            # 查找出边
            for edge in self.edges_by_source.get(current, []):
                next_node = edge.get("dst")
                if not next_node:
                    continue

                edge_key = (current, edge.get("type"), next_node)
                if edge_key not in edges_set:
                    edges_set.add(edge_key)
                    nodes_set.add(next_node)

                    if next_node not in [n for n, _ in queue]:
                        queue.append((next_node, depth + 1))

            # 查找入边
            for edge in self.edges_by_target.get(current, []):
                prev_node = edge.get("src")
                if not prev_node:
                    continue

                edge_key = (prev_node, edge.get("type"), current)
                if edge_key not in edges_set:
                    edges_set.add(edge_key)
                    nodes_set.add(prev_node)

                    if prev_node not in [n for n, _ in queue]:
                        queue.append((prev_node, depth + 1))

        # 构建结果
        nodes = [self.kg_nodes.get(nid) for nid in nodes_set if nid in self.kg_nodes]
        edges = [
            {
                "src": src,
                "dst": dst,
                "type": etype,
            }
            for src, etype, dst in edges_set
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "center": center_entity,
            "depth": max_depth,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def query_statistics(self) -> Dict[str, Any]:
        """
        查询知识图谱统计信息
        
        Returns:
            统计信息字典
        """
        # 节点统计
        node_type_counts = defaultdict(int)
        total_nodes = len(self.kg_nodes)

        for node in self.kg_nodes.values():
            node_type = node.get("type", "unknown")
            node_type_counts[node_type] += 1

        # 边统计
        edge_type_counts = defaultdict(int)
        total_edges = len(self.kg_edges)

        for edge in self.kg_edges:
            edge_type = edge.get("type", "unknown")
            edge_type_counts[edge_type] += 1

        # 计算平均度数
        degrees = []
        all_node_ids = set(self.kg_nodes.keys())
        for node_id in all_node_ids:
            degree = len(self.edges_by_source.get(node_id, [])) + len(
                self.edges_by_target.get(node_id, [])
            )
            degrees.append(degree)

        avg_degree = sum(degrees) / len(degrees) if degrees else 0

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_types": dict(node_type_counts),
            "edge_types": dict(edge_type_counts),
            "average_degree": round(avg_degree, 2),
            "max_degree": max(degrees) if degrees else 0,
        }

    def query_by_semantic_search(
        self, query_text: str, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        基于语义搜索查询（需要结合向量检索）
        
        Args:
            query_text: 查询文本
            top_k: 返回数量
            
        Returns:
            相关实体列表
        """
        # 这是一个占位实现，实际应该结合向量检索
        # 先使用文本匹配
        query_lower = query_text.lower()
        results = []

        for node_id, node in self.kg_nodes.items():
            node_value = node.get("value", "").lower()
            if query_lower in node_value:
                score = len(query_lower) / max(len(node_value), 1)
                results.append(
                    {
                        "entity": node,
                        "score": score,
                        "match_type": "text_match",
                    }
                )

        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]


# 全局查询引擎实例
_kg_query_engine: Optional[EnhancedKGQueryEngine] = None


def get_kg_query_engine(kg_nodes: Dict, kg_edges: List[Dict]) -> EnhancedKGQueryEngine:
    """
    获取知识图谱查询引擎实例
    
    Args:
        kg_nodes: 知识图谱节点
        kg_edges: 知识图谱边
        
    Returns:
        EnhancedKGQueryEngine实例
    """
    global _kg_query_engine
    # 每次获取时重建（因为图谱可能已更新）
    _kg_query_engine = EnhancedKGQueryEngine(kg_nodes, kg_edges)
    return _kg_query_engine

