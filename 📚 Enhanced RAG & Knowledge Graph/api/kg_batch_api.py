"""
Knowledge Graph Batch API
知识图谱批量操作API

实现批量查询、批量更新等功能（知识图谱100%完成度的一部分）
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

# 使用绝对导入避免相对导入问题
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from knowledge_graph.enhanced_kg_query import get_kg_query_engine
except ImportError:
    from ..knowledge_graph.enhanced_kg_query import get_kg_query_engine

# 延迟导入require_api_key以避免循环依赖
def _get_require_api_key():
    """获取API密钥验证依赖（延迟导入）"""
    try:
        from api.app import require_api_key
    except ImportError:
        from .app import require_api_key
    return require_api_key

# 延迟导入内部变量
def _get_kg_data():
    """获取KG数据（延迟导入）"""
    try:
        from api.app import _kg_nodes, _kg_edges
    except ImportError:
        from .app import _kg_nodes, _kg_edges
    return _kg_nodes, _kg_edges

router = APIRouter(prefix="/kg/batch", tags=["Knowledge Graph Batch API"])


class BatchQueryRequest(BaseModel):
    """批量查询请求"""
    queries: List[Dict[str, Any]]  # 查询列表
    query_type: str = "entities"  # 默认查询类型


class BatchQueryResponse(BaseModel):
    """批量查询响应"""
    results: List[Dict[str, Any]]
    success_count: int
    total_count: int


@router.post("/query", response_model=BatchQueryResponse)
async def batch_query(
    request: BatchQueryRequest,
    _: bool = Depends(_get_require_api_key()),
) -> BatchQueryResponse:
    """
    批量查询实体或关系
    
    Args:
        request: 批量查询请求
        _: API密钥验证
        
    Returns:
        批量查询结果
    """
    try:
        _kg_nodes, _kg_edges = _get_kg_data()
        query_engine = get_kg_query_engine(_kg_nodes, _kg_edges)
        results = []
        success_count = 0
        
        for query in request.queries:
            try:
                if request.query_type == "entities":
                    result = query_engine.query_entities(
                        entity_type=query.get("entity_type"),
                        value_pattern=query.get("value_pattern"),
                        limit=query.get("limit", 100),
                    )
                    results.append({
                        "query": query,
                        "success": True,
                        "result": result,
                        "count": len(result),
                    })
                    success_count += 1
                elif request.query_type == "relations":
                    result = query_engine.query_relations(
                        source_entity=query.get("source_entity"),
                        target_entity=query.get("target_entity"),
                        relation_type=query.get("relation_type"),
                        limit=query.get("limit", 100),
                    )
                    results.append({
                        "query": query,
                        "success": True,
                        "result": result,
                        "count": len(result),
                    })
                    success_count += 1
                else:
                    results.append({
                        "query": query,
                        "success": False,
                        "error": f"不支持的查询类型: {request.query_type}",
                    })
            except Exception as e:
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                })
        
        return BatchQueryResponse(
            results=results,
            success_count=success_count,
            total_count=len(request.queries),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量查询失败: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    获取查询缓存统计信息
    
    Returns:
        缓存统计信息
    """
    try:
        from ..knowledge_graph.kg_query_cache import get_kg_query_cache
        cache = get_kg_query_cache()
        stats = cache.get_stats()
        return {
            "success": True,
            "cache_stats": stats,
        }
    except ImportError:
        return {
            "success": False,
            "error": "查询缓存模块不可用",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    清空查询缓存
    
    Returns:
        清理结果
    """
    try:
        from ..knowledge_graph.kg_query_cache import get_kg_query_cache
        cache = get_kg_query_cache()
        cache.clear()
        return {
            "success": True,
            "message": "缓存已清空",
        }
    except ImportError:
        return {
            "success": False,
            "error": "查询缓存模块不可用",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空缓存失败: {str(e)}"
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    query_type: Optional[str] = Query(None, description="查询类型，如果为空则清空所有缓存"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    使缓存失效
    
    Args:
        query_type: 查询类型（可选）
        _: API密钥验证
        
    Returns:
        失效结果
    """
    try:
        from ..knowledge_graph.kg_query_cache import get_kg_query_cache
        cache = get_kg_query_cache()
        count = cache.invalidate(query_type)
        return {
            "success": True,
            "invalidated_count": count,
            "query_type": query_type or "all",
        }
    except ImportError:
        return {
            "success": False,
            "error": "查询缓存模块不可用",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"使缓存失效失败: {str(e)}"
        )

