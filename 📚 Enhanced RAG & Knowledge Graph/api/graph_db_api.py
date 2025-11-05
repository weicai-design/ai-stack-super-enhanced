"""
Graph Database API
图数据库API端点

提供图数据库管理功能的API接口（差距5：图数据库集成）
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

# 使用绝对导入避免相对导入问题
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from knowledge_graph.graph_database_adapter import (
        get_graph_adapter,
        GraphNode,
        GraphEdge,
    )
except ImportError:
    from ..knowledge_graph.graph_database_adapter import (
        get_graph_adapter,
        GraphNode,
        GraphEdge,
    )

# 延迟导入require_api_key以避免循环依赖
def _get_require_api_key():
    """获取API密钥验证依赖（延迟导入）"""
    try:
        from api.app import require_api_key
    except ImportError:
        from .app import require_api_key
    return require_api_key

router = APIRouter(prefix="/graph-db", tags=["Graph Database API"])


class GraphNodeRequest(BaseModel):
    """图节点请求"""
    id: str
    type: str
    value: str
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class GraphEdgeRequest(BaseModel):
    """图边请求"""
    source: str
    target: str
    relation: str
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/node", response_model=Dict[str, Any])
async def add_graph_node(
    request: GraphNodeRequest,
    adapter_type: str = Query("memory", description="适配器类型: memory, nebula, neo4j"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    添加图节点（差距5：图数据库集成）
    
    Args:
        request: 图节点请求
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        添加结果
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        node = GraphNode(
            id=request.id,
            type=request.type,
            value=request.value,
            properties=request.properties,
            metadata=request.metadata,
        )
        
        success = await adapter.add_node(node)
        
        return {
            "success": success,
            "node_id": request.id,
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"添加图节点失败: {str(e)}"
        )


@router.post("/edge", response_model=Dict[str, Any])
async def add_graph_edge(
    request: GraphEdgeRequest,
    adapter_type: str = Query("memory", description="适配器类型: memory, nebula, neo4j"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    添加图边（差距5：图数据库集成）
    
    Args:
        request: 图边请求
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        添加结果
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        edge = GraphEdge(
            source=request.source,
            target=request.target,
            relation=request.relation,
            properties=request.properties,
            metadata=request.metadata,
        )
        
        success = await adapter.add_edge(edge)
        
        return {
            "success": success,
            "source": request.source,
            "target": request.target,
            "relation": request.relation,
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"添加图边失败: {str(e)}"
        )


@router.get("/nodes", response_model=Dict[str, Any])
async def query_graph_nodes(
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    value_pattern: Optional[str] = Query(None, description="值模式过滤（正则）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    adapter_type: str = Query("memory", description="适配器类型"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    查询图节点（差距5：图数据库集成）
    
    Args:
        node_type: 节点类型过滤
        value_pattern: 值模式过滤
        limit: 返回数量限制
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        节点列表
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        filters = {}
        if node_type:
            filters["type"] = node_type
        if value_pattern:
            filters["value_pattern"] = value_pattern
        
        nodes = await adapter.query_nodes(filters=filters, limit=limit)
        
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "value": n.value,
                    "properties": n.properties,
                }
                for n in nodes
            ],
            "count": len(nodes),
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询图节点失败: {str(e)}"
        )


@router.get("/edges", response_model=Dict[str, Any])
async def query_graph_edges(
    source: Optional[str] = Query(None, description="源节点"),
    target: Optional[str] = Query(None, description="目标节点"),
    relation: Optional[str] = Query(None, description="关系类型"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    adapter_type: str = Query("memory", description="适配器类型"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    查询图边（差距5：图数据库集成）
    
    Args:
        source: 源节点
        target: 目标节点
        relation: 关系类型
        limit: 返回数量限制
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        边列表
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        edges = await adapter.query_edges(
            source=source,
            target=target,
            relation=relation,
            limit=limit,
        )
        
        return {
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relation": e.relation,
                    "properties": e.properties,
                }
                for e in edges
            ],
            "count": len(edges),
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询图边失败: {str(e)}"
        )


@router.get("/path", response_model=Dict[str, Any])
async def query_graph_path(
    source: str = Query(..., description="源节点"),
    target: str = Query(..., description="目标节点"),
    max_depth: int = Query(5, ge=1, le=10, description="最大深度"),
    adapter_type: str = Query("memory", description="适配器类型"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    查询图路径（差距5：图数据库集成）
    
    Args:
        source: 源节点
        target: 目标节点
        max_depth: 最大深度
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        路径列表
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        paths = await adapter.query_path(source, target, max_depth=max_depth)
        
        return {
            "paths": paths,
            "count": len(paths),
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询图路径失败: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_graph_stats(
    adapter_type: str = Query("memory", description="适配器类型"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    获取图数据库统计信息（差距5：图数据库集成）
    
    Args:
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        统计信息
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        stats = await adapter.get_stats()
        
        return {
            **stats,
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.delete("/clear", response_model=Dict[str, Any])
async def clear_graph(
    adapter_type: str = Query("memory", description="适配器类型"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    清空图数据库（差距5：图数据库集成）
    
    Args:
        adapter_type: 适配器类型
        _: API密钥验证
        
    Returns:
        清空结果
    """
    try:
        adapter = get_graph_adapter(adapter_type=adapter_type)
        
        success = await adapter.clear()
        
        return {
            "success": success,
            "adapter_type": adapter_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空图数据库失败: {str(e)}"
        )

