"""
知识图谱可视化API
Knowledge Graph Visualization API

提供图谱数据序列化、节点/边查询、导出功能

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/kg/viz", tags=["Knowledge Graph Visualization"])


# ==================== 数据模型 ====================

class NodeInfo(BaseModel):
    """节点信息"""
    id: str = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    type: Optional[str] = Field(None, description="节点类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    degree: int = Field(0, description="节点度数（连接数）")


class EdgeInfo(BaseModel):
    """边信息"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: str = Field(..., description="边标签/关系类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="边属性")
    weight: float = Field(1.0, description="边权重")


class GraphData(BaseModel):
    """图谱数据"""
    nodes: List[NodeInfo] = Field(default_factory=list, description="节点列表")
    edges: List[EdgeInfo] = Field(default_factory=list, description="边列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class GraphStats(BaseModel):
    """图谱统计"""
    node_count: int = Field(0, description="节点总数")
    edge_count: int = Field(0, description="边总数")
    node_types: Dict[str, int] = Field(default_factory=dict, description="节点类型分布")
    edge_types: Dict[str, int] = Field(default_factory=dict, description="边类型分布")
    avg_degree: float = Field(0.0, description="平均度数")
    density: float = Field(0.0, description="图密度")


class SubgraphRequest(BaseModel):
    """子图查询请求"""
    node_ids: Optional[List[str]] = Field(None, description="节点ID列表")
    depth: int = Field(1, ge=1, le=3, description="查询深度（1-3）")
    max_nodes: int = Field(100, ge=1, le=1000, description="最大节点数")
    include_properties: bool = Field(True, description="是否包含属性")


# ==================== 模拟数据（后续替换为真实KG） ====================

def _get_mock_graph_data(limit: int = 100) -> GraphData:
    """获取模拟图谱数据"""
    nodes = [
        NodeInfo(
            id="n1",
            label="人工智能",
            type="concept",
            properties={"description": "计算机科学的一个分支", "created": "2024-01-01"},
            degree=3
        ),
        NodeInfo(
            id="n2",
            label="机器学习",
            type="concept",
            properties={"description": "AI的子领域", "created": "2024-01-02"},
            degree=2
        ),
        NodeInfo(
            id="n3",
            label="深度学习",
            type="concept",
            properties={"description": "机器学习的子领域", "created": "2024-01-03"},
            degree=1
        ),
        NodeInfo(
            id="n4",
            label="神经网络",
            type="technology",
            properties={"description": "深度学习的核心技术", "created": "2024-01-04"},
            degree=1
        ),
    ]
    
    edges = [
        EdgeInfo(
            id="e1",
            source="n1",
            target="n2",
            label="包含",
            properties={"confidence": 0.95},
            weight=1.0
        ),
        EdgeInfo(
            id="e2",
            source="n2",
            target="n3",
            label="包含",
            properties={"confidence": 0.90},
            weight=1.0
        ),
        EdgeInfo(
            id="e3",
            source="n3",
            target="n4",
            label="使用",
            properties={"confidence": 0.85},
            weight=0.8
        ),
    ]
    
    return GraphData(
        nodes=nodes[:limit],
        edges=edges[:limit],
        metadata={
            "generated_at": datetime.now().isoformat(),
            "source": "mock_data",
            "version": "1.0.0"
        }
    )


def _get_mock_stats() -> GraphStats:
    """获取模拟统计数据"""
    return GraphStats(
        node_count=4,
        edge_count=3,
        node_types={"concept": 3, "technology": 1},
        edge_types={"包含": 2, "使用": 1},
        avg_degree=1.75,
        density=0.5
    )


# ==================== API端点 ====================

@router.get("/graph", response_model=GraphData)
async def get_full_graph(
    limit: int = Query(100, ge=1, le=1000, description="最大节点数"),
    include_properties: bool = Query(True, description="是否包含属性")
):
    """
    获取完整图谱数据
    
    返回知识图谱的所有节点和边，适合前端可视化展示
    
    Args:
        limit: 最大节点数（防止数据过大）
        include_properties: 是否包含节点/边属性
    
    Returns:
        GraphData: 图谱数据
    """
    try:
        graph_data = _get_mock_graph_data(limit=limit)
        
        if not include_properties:
            # 移除属性以减小数据量
            for node in graph_data.nodes:
                node.properties = {}
            for edge in graph_data.edges:
                edge.properties = {}
        
        logger.info(f"返回图谱数据: {len(graph_data.nodes)}节点, {len(graph_data.edges)}边")
        return graph_data
    
    except Exception as e:
        logger.error(f"获取图谱数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=GraphStats)
async def get_graph_statistics():
    """
    获取图谱统计信息
    
    返回节点数、边数、类型分布等统计数据
    
    Returns:
        GraphStats: 统计信息
    """
    try:
        stats = _get_mock_stats()
        logger.info(f"返回图谱统计: {stats.node_count}节点, {stats.edge_count}边")
        return stats
    
    except Exception as e:
        logger.error(f"获取图谱统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", response_model=NodeInfo)
async def get_node_info(node_id: str):
    """
    获取单个节点信息
    
    Args:
        node_id: 节点ID
    
    Returns:
        NodeInfo: 节点详细信息
    """
    try:
        # TODO: 从真实KG获取节点
        graph_data = _get_mock_graph_data()
        
        for node in graph_data.nodes:
            if node.id == node_id:
                logger.info(f"返回节点信息: {node_id}")
                return node
        
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取节点信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}/neighbors", response_model=List[NodeInfo])
async def get_node_neighbors(
    node_id: str,
    depth: int = Query(1, ge=1, le=3, description="邻居深度（1-3跳）")
):
    """
    获取节点的邻居节点
    
    Args:
        node_id: 节点ID
        depth: 查询深度（1-3跳）
    
    Returns:
        List[NodeInfo]: 邻居节点列表
    """
    try:
        # TODO: 从真实KG获取邻居
        graph_data = _get_mock_graph_data()
        
        # 简单实现：找到所有连接到该节点的边
        neighbors = []
        for edge in graph_data.edges:
            if edge.source == node_id:
                for node in graph_data.nodes:
                    if node.id == edge.target:
                        neighbors.append(node)
            elif edge.target == node_id:
                for node in graph_data.nodes:
                    if node.id == edge.source:
                        neighbors.append(node)
        
        logger.info(f"返回节点 {node_id} 的 {len(neighbors)} 个邻居")
        return neighbors
    
    except Exception as e:
        logger.error(f"获取邻居节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subgraph", response_model=GraphData)
async def get_subgraph(request: SubgraphRequest):
    """
    获取子图
    
    根据指定的节点列表和深度，提取相关子图
    
    Args:
        request: 子图查询请求
    
    Returns:
        GraphData: 子图数据
    """
    try:
        # TODO: 从真实KG提取子图
        graph_data = _get_mock_graph_data()
        
        if request.node_ids:
            # 过滤节点
            filtered_nodes = [n for n in graph_data.nodes if n.id in request.node_ids]
            node_id_set = {n.id for n in filtered_nodes}
            
            # 过滤边（只保留两端都在子图中的边）
            filtered_edges = [
                e for e in graph_data.edges
                if e.source in node_id_set and e.target in node_id_set
            ]
            
            graph_data.nodes = filtered_nodes[:request.max_nodes]
            graph_data.edges = filtered_edges
        
        if not request.include_properties:
            for node in graph_data.nodes:
                node.properties = {}
            for edge in graph_data.edges:
                edge.properties = {}
        
        logger.info(f"返回子图: {len(graph_data.nodes)}节点, {len(graph_data.edges)}边")
        return graph_data
    
    except Exception as e:
        logger.error(f"获取子图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{format}")
async def export_graph(
    format: str
):
    """
    导出图谱数据
    
    支持多种格式：json, graphml, gexf, cytoscape
    
    Args:
        format: 导出格式（json, graphml, gexf, cytoscape）
    
    Returns:
        导出的图谱数据
    """
    try:
        graph_data = _get_mock_graph_data()
        
        if format == "json":
            # JSON格式（默认）
            return graph_data.model_dump()
        
        elif format == "cytoscape":
            # Cytoscape.js格式
            elements = []
            
            # 添加节点
            for node in graph_data.nodes:
                elements.append({
                    "data": {
                        "id": node.id,
                        "label": node.label,
                        "type": node.type,
                        **node.properties
                    }
                })
            
            # 添加边
            for edge in graph_data.edges:
                elements.append({
                    "data": {
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "label": edge.label,
                        "weight": edge.weight,
                        **edge.properties
                    }
                })
            
            return {"elements": elements}
        
        elif format == "graphml":
            # GraphML格式（简化版）
            graphml = '<?xml version="1.0" encoding="UTF-8"?>\n'
            graphml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
            graphml += '  <graph id="G" edgedefault="directed">\n'
            
            for node in graph_data.nodes:
                graphml += f'    <node id="{node.id}"/>\n'
            
            for edge in graph_data.edges:
                graphml += f'    <edge source="{edge.source}" target="{edge.target}"/>\n'
            
            graphml += '  </graph>\n'
            graphml += '</graphml>'
            
            return {"graphml": graphml}
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_nodes(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="最大返回数")
):
    """
    搜索节点
    
    根据关键词搜索节点（支持标签和属性搜索）
    
    Args:
        query: 搜索关键词
        limit: 最大返回数
    
    Returns:
        匹配的节点列表
    """
    try:
        graph_data = _get_mock_graph_data()
        
        # 简单的标签匹配
        results = [
            node for node in graph_data.nodes
            if query.lower() in node.label.lower()
        ]
        
        logger.info(f"搜索 '{query}' 返回 {len(results)} 个结果")
        return {"query": query, "results": results[:limit], "total": len(results)}
    
    except Exception as e:
        logger.error(f"搜索节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def kg_viz_health():
    """知识图谱可视化模块健康检查"""
    return {
        "status": "healthy",
        "module": "kg-visualization",
        "version": "1.0.0",
        "features": [
            "full-graph-export",
            "subgraph-extraction",
            "node-search",
            "multiple-export-formats"
        ]
    }

