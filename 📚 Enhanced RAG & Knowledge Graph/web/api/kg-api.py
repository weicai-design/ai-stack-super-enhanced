#!/usr/bin/env python3
"""
Enhanced Knowledge Graph API
对应需求: 1.8 RAG数据形成知识图谱, 1.6 词义自主分组
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/api/114. kg-api.py
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 导入知识图谱模块
from core.dynamic_knowledge_graph import DynamicKnowledgeGraph
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from knowledge_graph.graph_construction_engine import GraphConstructionEngine
from knowledge_graph.knowledge_inference_engine import KnowledgeInferenceEngine
from pydantic import BaseModel, Field

logger = logging.getLogger("kg_api")

# 创建路由
router = APIRouter(
    prefix="/knowledge-graph",
    tags=["Knowledge Graph API"],
    responses={404: {"description": "Not found"}},
)


# Pydantic模型定义
class EntityRequest(BaseModel):
    """实体请求模型"""

    entity_id: Optional[str] = Field(None, description="实体ID")
    entity_name: Optional[str] = Field(None, description="实体名称")
    entity_type: Optional[str] = Field(None, description="实体类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")


class RelationshipRequest(BaseModel):
    """关系请求模型"""

    source_entity: str = Field(..., description="源实体ID")
    target_entity: str = Field(..., description="目标实体ID")
    relationship_type: str = Field(..., description="关系类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class GraphQuery(BaseModel):
    """图查询模型"""

    query_type: str = Field(..., description="查询类型")
    parameters: Dict[str, Any] = Field(..., description="查询参数")
    depth: int = Field(2, description="查询深度")
    limit: int = Field(100, description="结果限制")


class InferenceRequest(BaseModel):
    """推理请求模型"""

    entities: List[str] = Field(..., description="实体列表")
    relationship_types: Optional[List[str]] = Field(None, description="关系类型")
    inference_depth: int = Field(3, description="推理深度")


class InferenceResponse(BaseModel):
    """推理响应模型"""

    inferred_relationships: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    inference_paths: List[List[str]]


class GraphUpdateRequest(BaseModel):
    """图更新请求模型"""

    operations: List[Dict[str, Any]] = Field(..., description="更新操作列表")
    batch_size: int = Field(100, description="批处理大小")


# 全局组件实例
_knowledge_graph = None
_graph_construction_engine = None
_inference_engine = None


# 依赖注入
async def get_knowledge_graph() -> DynamicKnowledgeGraph:
    """获取知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        try:
            _knowledge_graph = DynamicKnowledgeGraph()
            await _knowledge_graph.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Knowledge graph not initialized"
            )
    return _knowledge_graph


async def get_graph_construction_engine() -> GraphConstructionEngine:
    """获取图构建引擎实例"""
    kg = await get_knowledge_graph()
    return kg.construction_engine


async def get_inference_engine() -> KnowledgeInferenceEngine:
    """获取推理引擎实例"""
    kg = await get_knowledge_graph()
    return kg.inference_engine


# API路由
@router.post("/entities")
async def create_entity(
    request: EntityRequest, kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    创建实体

    Args:
        request: 实体请求
        kg: 知识图谱

    Returns:
        Dict: 创建的实体信息
    """
    try:
        entity_id = await kg.create_entity(
            name=request.entity_name,
            entity_type=request.entity_type,
            properties=request.properties,
            entity_id=request.entity_id,
        )

        logger.info(f"Entity created: {entity_id}")

        return {
            "success": True,
            "entity_id": entity_id,
            "message": f"Entity {entity_id} created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create entity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Entity creation failed: {str(e)}")


@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: str = Path(..., description="实体ID"),
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    获取实体信息

    Args:
        entity_id: 实体ID
        kg: 知识图谱

    Returns:
        Dict: 实体信息
    """
    try:
        entity = await kg.get_entity(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        return entity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Entity retrieval failed: {str(e)}"
        )


@router.post("/relationships")
async def create_relationship(
    request: RelationshipRequest,
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    创建关系

    Args:
        request: 关系请求
        kg: 知识图谱

    Returns:
        Dict: 创建的关系信息
    """
    try:
        relationship_id = await kg.create_relationship(
            source_entity=request.source_entity,
            target_entity=request.target_entity,
            relationship_type=request.relationship_type,
            properties=request.properties,
        )

        logger.info(f"Relationship created: {relationship_id}")

        return {
            "success": True,
            "relationship_id": relationship_id,
            "message": f"Relationship {relationship_id} created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Relationship creation failed: {str(e)}"
        )


@router.post("/query")
async def query_graph(
    query: GraphQuery, kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    图查询

    Args:
        query: 图查询
        kg: 知识图谱

    Returns:
        Dict: 查询结果
    """
    try:
        results = await kg.execute_query(
            query_type=query.query_type,
            parameters=query.parameters,
            depth=query.depth,
            limit=query.limit,
        )

        return {
            "success": True,
            "results": results,
            "result_count": len(results),
            "query_id": str(uuid.uuid4()),
        }

    except Exception as e:
        logger.error(f"Graph query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")


@router.post("/inference")
async def infer_relationships(
    request: InferenceRequest,
    inference_engine: KnowledgeInferenceEngine = Depends(get_inference_engine),
):
    """
    推理关系

    Args:
        request: 推理请求
        inference_engine: 推理引擎

    Returns:
        InferenceResponse: 推理结果
    """
    try:
        inference_results = await inference_engine.infer_relationships(
            entities=request.entities,
            relationship_types=request.relationship_types,
            depth=request.inference_depth,
        )

        return InferenceResponse(**inference_results)

    except Exception as e:
        logger.error(f"Relationship inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@router.get("/subgraph/{center_entity}")
async def get_subgraph(
    center_entity: str = Path(..., description="中心实体"),
    depth: int = Query(2, description="子图深度"),
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    获取子图

    Args:
        center_entity: 中心实体
        depth: 子图深度
        kg: 知识图谱

    Returns:
        Dict: 子图数据
    """
    try:
        subgraph = await kg.get_subgraph(center_entity, depth)

        return {
            "success": True,
            "center_entity": center_entity,
            "depth": depth,
            "subgraph": subgraph,
            "entity_count": len(subgraph.get("entities", [])),
            "relationship_count": len(subgraph.get("relationships", [])),
        }

    except Exception as e:
        logger.error(f"Failed to get subgraph: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Subgraph retrieval failed: {str(e)}"
        )


@router.post("/update")
async def batch_update_graph(
    request: GraphUpdateRequest,
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    批量更新图

    Args:
        request: 更新请求
        kg: 知识图谱

    Returns:
        Dict: 更新结果
    """
    try:
        update_results = await kg.batch_update(
            operations=request.operations, batch_size=request.batch_size
        )

        return {
            "success": True,
            "processed_operations": len(request.operations),
            "results": update_results,
            "update_id": str(uuid.uuid4()),
        }

    except Exception as e:
        logger.error(f"Batch graph update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph update failed: {str(e)}")


@router.get("/stats")
async def get_graph_stats(kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph)):
    """
    获取图统计信息

    Args:
        kg: 知识图谱

    Returns:
        Dict: 统计信息
    """
    try:
        stats = await kg.get_graph_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get graph stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str = Path(..., description="实体ID"),
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    删除实体

    Args:
        entity_id: 实体ID
        kg: 知识图谱

    Returns:
        Dict: 删除结果
    """
    try:
        success = await kg.delete_entity(entity_id)

        if success:
            logger.info(f"Entity deleted: {entity_id}")
            return {"success": True, "message": f"Entity {entity_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entity: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Entity deletion failed: {str(e)}")


@router.get("/visualization/data")
async def get_visualization_data(
    center_entity: Optional[str] = Query(None, description="中心实体"),
    depth: int = Query(2, description="可视化深度"),
    kg: DynamicKnowledgeGraph = Depends(get_knowledge_graph),
):
    """
    获取可视化数据

    Args:
        center_entity: 中心实体
        depth: 可视化深度
        kg: 知识图谱

    Returns:
        Dict: 可视化数据
    """
    try:
        if center_entity:
            data = await kg.get_subgraph(center_entity, depth)
        else:
            data = await kg.get_graph_snapshot(limit=500)  # 限制数据量

        return {
            "success": True,
            "visualization_data": data,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get visualization data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Visualization data retrieval failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        kg = await get_knowledge_graph()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "knowledge_graph": kg is not None,
                "graph_construction_engine": _graph_construction_engine is not None,
                "inference_engine": _inference_engine is not None,
            },
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
