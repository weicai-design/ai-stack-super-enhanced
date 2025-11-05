"""
Graph Database Adapter
图数据库适配器

实现图数据库可选集成（差距5）：
1. 支持内存图结构（默认，向后兼容）
2. 可选集成NebulaGraph
3. 可选集成Neo4j
4. 统一接口，无缝切换
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """图谱节点"""
    id: str
    type: str
    value: str
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GraphEdge:
    """图谱边"""
    source: str
    target: str
    relation: str
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class GraphDatabaseAdapter(ABC):
    """
    图数据库适配器抽象基类
    
    提供统一的图数据库接口
    """

    @abstractmethod
    async def add_node(self, node: GraphNode) -> bool:
        """添加节点"""
        pass

    @abstractmethod
    async def add_edge(self, edge: GraphEdge) -> bool:
        """添加边"""
        pass

    @abstractmethod
    async def query_nodes(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphNode]:
        """查询节点"""
        pass

    @abstractmethod
    async def query_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """查询边"""
        pass

    @abstractmethod
    async def query_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """查询路径"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """清空图谱"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class InMemoryGraphAdapter(GraphDatabaseAdapter):
    """
    内存图数据库适配器（默认实现）
    
    向后兼容，使用NetworkX在内存中存储
    """

    def __init__(self):
        """初始化内存图适配器"""
        import networkx as nx
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    async def add_node(self, node: GraphNode) -> bool:
        """添加节点"""
        try:
            self.nodes[node.id] = node
            self.graph.add_node(
                node.id,
                type=node.type,
                value=node.value,
                **{**(node.properties or {}), **(node.metadata or {})}
            )
            return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False

    async def add_edge(self, edge: GraphEdge) -> bool:
        """添加边"""
        try:
            # 确保源节点和目标节点存在
            if edge.source not in self.nodes:
                await self.add_node(GraphNode(
                    id=edge.source,
                    type="unknown",
                    value=edge.source,
                ))
            if edge.target not in self.nodes:
                await self.add_node(GraphNode(
                    id=edge.target,
                    type="unknown",
                    value=edge.target,
                ))
            
            self.edges.append(edge)
            self.graph.add_edge(
                edge.source,
                edge.target,
                relation=edge.relation,
                **{**(edge.properties or {}), **(edge.metadata or {})}
            )
            return True
        except Exception as e:
            logger.error(f"添加边失败: {e}")
            return False

    async def query_nodes(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphNode]:
        """查询节点"""
        nodes = list(self.nodes.values())
        
        # 应用过滤器
        if filters:
            filtered = []
            for node in nodes:
                match = True
                for key, value in filters.items():
                    if key == "type" and node.type != value:
                        match = False
                        break
                    elif key == "value_pattern":
                        import re
                        if not re.search(value, node.value):
                            match = False
                            break
                if match:
                    filtered.append(node)
            nodes = filtered
        
        return nodes[:limit]

    async def query_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """查询边"""
        edges = self.edges
        
        # 应用过滤器
        filtered = []
        for edge in edges:
            match = True
            if source and edge.source != source:
                match = False
            if target and edge.target != target:
                match = False
            if relation and edge.relation != relation:
                match = False
            if match:
                filtered.append(edge)
        
        return filtered[:limit]

    async def query_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """查询路径（BFS）"""
        try:
            import networkx as nx
            
            # 使用BFS查找所有路径（限制深度）
            paths = []
            
            def dfs(current: str, path: List[str], depth: int):
                if depth > max_depth:
                    return
                if current == target:
                    paths.append(path + [current])
                    return
                
                for neighbor in self.graph.successors(current):
                    if neighbor not in path:  # 避免循环
                        dfs(neighbor, path + [current], depth + 1)
            
            if source in self.graph and target in self.graph:
                dfs(source, [], 0)
            
            return paths[:10]  # 最多返回10条路径
        except Exception as e:
            logger.error(f"路径查询失败: {e}")
            return []

    async def clear(self) -> bool:
        """清空图谱"""
        try:
            self.graph.clear()
            self.nodes.clear()
            self.edges.clear()
            return True
        except Exception as e:
            logger.error(f"清空图谱失败: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        node_types = {}
        relation_types = {}
        
        for node in self.nodes.values():
            node_types[node.type] = node_types.get(node.type, 0) + 1
        
        for edge in self.edges:
            relation_types[edge.relation] = relation_types.get(edge.relation, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "relation_types": relation_types,
        }


class NebulaGraphAdapter(GraphDatabaseAdapter):
    """
    NebulaGraph适配器（可选）
    
    需要安装: pip install nebula3-python
    """

    def __init__(self, host: str = "localhost", port: int = 9669, space: str = "ai_stack"):
        """
        初始化NebulaGraph适配器
        
        Args:
            host: NebulaGraph服务器地址
            port: 端口
            space: 图空间名称
        """
        self.host = host
        self.port = port
        self.space = space
        self.client = None
        self.session = None
        self._connected = False

    async def _connect(self) -> bool:
        """连接到NebulaGraph"""
        if self._connected:
            return True
        
        try:
            from nebula3.gclient.net import ConnectionPool
            from nebula3.Config import Config
            
            config = Config()
            config.max_connection_pool_size = 10
            
            self.client = ConnectionPool()
            if not self.client.init([(self.host, self.port)], config):
                logger.error("NebulaGraph连接池初始化失败")
                return False
            
            self.session = self.client.get_session("root", "password")
            self.session.execute(f"USE {self.space}")
            self._connected = True
            logger.info(f"✅ 已连接到NebulaGraph: {self.host}:{self.port}")
            return True
        except ImportError:
            logger.warning("NebulaGraph客户端未安装，使用内存适配器")
            return False
        except Exception as e:
            logger.error(f"NebulaGraph连接失败: {e}")
            return False

    async def add_node(self, node: GraphNode) -> bool:
        """添加节点"""
        if not await self._connect():
            return False
        
        try:
            # 创建或更新节点
            query = f"""
            INSERT VERTEX {node.type} (
                id, value, properties
            ) VALUES "{node.id}":(
                "{node.id}", "{node.value}", {self._dict_to_properties(node.properties or {})}
            )
            """
            result = self.session.execute(query)
            return result.is_succeeded()
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False

    async def add_edge(self, edge: GraphEdge) -> bool:
        """添加边"""
        if not await self._connect():
            return False
        
        try:
            query = f"""
            INSERT EDGE {edge.relation} (
                properties
            ) VALUES "{edge.source}" -> "{edge.target}":(
                {self._dict_to_properties(edge.properties or {})}
            )
            """
            result = self.session.execute(query)
            return result.is_succeeded()
        except Exception as e:
            logger.error(f"添加边失败: {e}")
            return False

    async def query_nodes(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphNode]:
        """查询节点"""
        if not await self._connect():
            return []
        
        try:
            where_clause = ""
            if filters:
                conditions = []
                if "type" in filters:
                    conditions.append(f"type == '{filters['type']}'")
                where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"MATCH (n) {where_clause} RETURN n LIMIT {limit}"
            result = self.session.execute(query)
            
            nodes = []
            if result.is_succeeded():
                for row in result:
                    # 解析结果（简化）
                    nodes.append(GraphNode(
                        id=row[0],
                        type=row.get("type", "unknown"),
                        value=row.get("value", ""),
                    ))
            return nodes
        except Exception as e:
            logger.error(f"查询节点失败: {e}")
            return []

    async def query_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """查询边"""
        if not await self._connect():
            return []
        
        try:
            where_conditions = []
            if source:
                where_conditions.append(f"source == '{source}'")
            if target:
                where_conditions.append(f"target == '{target}'")
            if relation:
                where_conditions.append(f"relation == '{relation}'")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            query = f"MATCH (a)-[r]->(b) {where_clause} RETURN a, r, b LIMIT {limit}"
            result = self.session.execute(query)
            
            edges = []
            if result.is_succeeded():
                for row in result:
                    edges.append(GraphEdge(
                        source=row[0],
                        target=row[2],
                        relation=row[1].get("relation", ""),
                    ))
            return edges
        except Exception as e:
            logger.error(f"查询边失败: {e}")
            return []

    async def query_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """查询路径"""
        if not await self._connect():
            return []
        
        try:
            query = f"""
            FIND SHORTEST PATH FROM "{source}" TO "{target}" 
            OVER * UPTO {max_depth} STEPS
            """
            result = self.session.execute(query)
            
            paths = []
            if result.is_succeeded():
                for row in result:
                    paths.append(row)
            return paths
        except Exception as e:
            logger.error(f"路径查询失败: {e}")
            return []

    async def clear(self) -> bool:
        """清空图谱"""
        if not await self._connect():
            return False
        
        try:
            query = "MATCH (n) DETACH DELETE n"
            result = self.session.execute(query)
            return result.is_succeeded()
        except Exception as e:
            logger.error(f"清空图谱失败: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not await self._connect():
            return {}
        
        try:
            # 节点统计
            node_query = "MATCH (n) RETURN count(n) as count"
            edge_query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            node_result = self.session.execute(node_query)
            edge_result = self.session.execute(edge_query)
            
            return {
                "total_nodes": node_result.rows[0][0] if node_result.is_succeeded() else 0,
                "total_edges": edge_result.rows[0][0] if edge_result.is_succeeded() else 0,
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def _dict_to_properties(self, props: Dict[str, Any]) -> str:
        """将字典转换为NebulaGraph属性字符串"""
        if not props:
            return "{}"
        items = [f'"{k}": "{v}"' for k, v in props.items()]
        return "{" + ", ".join(items) + "}"


class Neo4jAdapter(GraphDatabaseAdapter):
    """
    Neo4j适配器（可选）
    
    需要安装: pip install neo4j
    """

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """
        初始化Neo4j适配器
        
        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connected = False

    async def _connect(self) -> bool:
        """连接到Neo4j"""
        if self._connected:
            return True
        
        try:
            from neo4j import GraphDatabase
            
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self._connected = True
            logger.info(f"✅ 已连接到Neo4j: {self.uri}")
            return True
        except ImportError:
            logger.warning("Neo4j客户端未安装，使用内存适配器")
            return False
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            return False

    async def add_node(self, node: GraphNode) -> bool:
        """添加节点"""
        if not await self._connect():
            return False
        
        try:
            def create_node(tx, node):
                props = {**(node.properties or {}), "value": node.value}
                query = f"MERGE (n:{node.type} {{id: $id}}) SET n += $props"
                tx.run(query, id=node.id, props=props)
            
            with self.driver.session() as session:
                session.execute_write(create_node, node)
            return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False

    async def add_edge(self, edge: GraphEdge) -> bool:
        """添加边"""
        if not await self._connect():
            return False
        
        try:
            def create_edge(tx, edge):
                props = edge.properties or {}
                query = f"""
                MATCH (a), (b)
                WHERE a.id = $source AND b.id = $target
                MERGE (a)-[r:{edge.relation}]->(b)
                SET r += $props
                """
                tx.run(query, source=edge.source, target=edge.target, props=props)
            
            with self.driver.session() as session:
                session.execute_write(create_edge, edge)
            return True
        except Exception as e:
            logger.error(f"添加边失败: {e}")
            return False

    async def query_nodes(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphNode]:
        """查询节点"""
        if not await self._connect():
            return []
        
        try:
            where_clause = ""
            if filters and "type" in filters:
                where_clause = f"WHERE n:{filters['type']}"
            
            query = f"MATCH (n) {where_clause} RETURN n LIMIT {limit}"
            
            with self.driver.session() as session:
                result = session.run(query)
                nodes = []
                for record in result:
                    node_data = record["n"]
                    nodes.append(GraphNode(
                        id=node_data.get("id", ""),
                        type=list(node_data.labels)[0] if node_data.labels else "unknown",
                        value=node_data.get("value", ""),
                        properties=dict(node_data),
                    ))
                return nodes
        except Exception as e:
            logger.error(f"查询节点失败: {e}")
            return []

    async def query_edges(
        self,
        source: Optional[str] = None,
        target: Optional[str] = None,
        relation: Optional[str] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """查询边"""
        if not await self._connect():
            return []
        
        try:
            where_conditions = []
            if source:
                where_conditions.append("a.id = $source")
            if target:
                where_conditions.append("b.id = $target")
            if relation:
                where_conditions.append(f"type(r) = '{relation}'")
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            query = f"MATCH (a)-[r]->(b) {where_clause} RETURN a, r, b LIMIT {limit}"
            
            with self.driver.session() as session:
                result = session.run(query, source=source, target=target)
                edges = []
                for record in result:
                    edges.append(GraphEdge(
                        source=record["a"]["id"],
                        target=record["b"]["id"],
                        relation=type(record["r"]).__name__,
                        properties=dict(record["r"]),
                    ))
                return edges
        except Exception as e:
            logger.error(f"查询边失败: {e}")
            return []

    async def query_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """查询路径"""
        if not await self._connect():
            return []
        
        try:
            query = f"""
            MATCH path = shortestPath((a)-[*1..{max_depth}]->(b))
            WHERE a.id = $source AND b.id = $target
            RETURN [node in nodes(path) | node.id] as path
            """
            
            with self.driver.session() as session:
                result = session.run(query, source=source, target=target)
                paths = []
                for record in result:
                    paths.append(record["path"])
                return paths
        except Exception as e:
            logger.error(f"路径查询失败: {e}")
            return []

    async def clear(self) -> bool:
        """清空图谱"""
        if not await self._connect():
            return False
        
        try:
            query = "MATCH (n) DETACH DELETE n"
            with self.driver.session() as session:
                session.run(query)
            return True
        except Exception as e:
            logger.error(f"清空图谱失败: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not await self._connect():
            return {}
        
        try:
            node_query = "MATCH (n) RETURN count(n) as count"
            edge_query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            with self.driver.session() as session:
                node_result = session.run(node_query)
                edge_result = session.run(edge_query)
                
                node_count = node_result.single()["count"]
                edge_count = edge_result.single()["count"]
                
                return {
                    "total_nodes": node_count,
                    "total_edges": edge_count,
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 全局图数据库适配器实例
_global_graph_adapter: Optional[GraphDatabaseAdapter] = None


def get_graph_adapter(
    adapter_type: str = "memory",
    **kwargs,
) -> GraphDatabaseAdapter:
    """
    获取图数据库适配器实例（单例模式）
    
    Args:
        adapter_type: 适配器类型 ("memory", "nebula", "neo4j")
        **kwargs: 适配器特定参数
        
    Returns:
        GraphDatabaseAdapter实例
    """
    global _global_graph_adapter
    
    if _global_graph_adapter is None:
        if adapter_type == "nebula":
            _global_graph_adapter = NebulaGraphAdapter(**kwargs)
        elif adapter_type == "neo4j":
            _global_graph_adapter = Neo4jAdapter(**kwargs)
        else:
            # 默认使用内存适配器
            _global_graph_adapter = InMemoryGraphAdapter()
    
    return _global_graph_adapter

