"""
RAG专家模块API接口

提供RAG专家模块的RESTful API接口，支持知识专家、检索专家、图谱专家的功能调用
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio

from .rag_experts import (
    KnowledgeExpert, 
    RetrievalExpert, 
    GraphExpert,
    ExpertCollaboration,
    ExpertAnalysis
)

# 创建API路由
router = APIRouter(prefix="/api/rag", tags=["RAG专家"])

# 专家实例
knowledge_expert = KnowledgeExpert()
retrieval_expert = RetrievalExpert()
graph_expert = GraphExpert()

# 协作管理器
collaboration_manager = ExpertCollaboration()
collaboration_manager.register_expert("knowledge_expert", knowledge_expert)
collaboration_manager.register_expert("retrieval_expert", retrieval_expert)
collaboration_manager.register_expert("graph_expert", graph_expert)


class KnowledgeAnalysisRequest(BaseModel):
    """知识分析请求"""
    knowledge_content: str
    knowledge_type: Optional[str] = "general"
    context: Optional[Dict[str, Any]] = None


class RetrievalAnalysisRequest(BaseModel):
    """检索分析请求"""
    query: str
    search_results: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class GraphAnalysisRequest(BaseModel):
    """图谱分析请求"""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class CollaborativeAnalysisRequest(BaseModel):
    """协作分析请求"""
    expert_ids: List[str]
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    """分析响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float


@router.post("/knowledge/analyze", response_model=AnalysisResponse)
async def analyze_knowledge(request: KnowledgeAnalysisRequest):
    """知识分析接口"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await knowledge_expert.analyze_knowledge(
            knowledge_content=request.knowledge_content,
            knowledge_type=request.knowledge_type,
            context=request.context
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return AnalysisResponse(
            success=True,
            data={
                "domain": result.domain.value,
                "confidence": result.confidence,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return AnalysisResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@router.post("/retrieval/analyze", response_model=AnalysisResponse)
async def analyze_retrieval(request: RetrievalAnalysisRequest):
    """检索分析接口"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await retrieval_expert.analyze_quote(
            query=request.query,
            search_results=request.search_results,
            context=request.context
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return AnalysisResponse(
            success=True,
            data={
                "domain": result.domain.value,
                "confidence": result.confidence,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return AnalysisResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@router.post("/graph/analyze", response_model=AnalysisResponse)
async def analyze_graph(request: GraphAnalysisRequest):
    """图谱分析接口"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await graph_expert.analyze_knowledge_graph(
            entities=request.entities,
            relationships=request.relationships,
            context=request.context
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return AnalysisResponse(
            success=True,
            data={
                "domain": result.domain.value,
                "confidence": result.confidence,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "metadata": result.metadata
            },
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return AnalysisResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@router.post("/collaborative/analyze", response_model=AnalysisResponse)
async def collaborative_analysis(request: CollaborativeAnalysisRequest):
    """协作分析接口"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await collaboration_manager.collaborative_analysis(
            expert_ids=request.expert_ids,
            data=request.data,
            context=request.context
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        return AnalysisResponse(
            success=True,
            data=result,
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = asyncio.get_event_loop().time() - start_time
        return AnalysisResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )


@router.get("/collaboration/stats")
async def get_collaboration_stats():
    """获取协作统计信息"""
    try:
        stats = collaboration_manager.get_collaboration_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experts/list")
async def list_experts():
    """列出可用专家"""
    experts = [
        {
            "id": "knowledge_expert",
            "name": "知识专家",
            "description": "知识分类、质量评估、关联分析、更新建议",
            "capabilities": ["知识分类", "质量评估", "关联分析", "更新建议"]
        },
        {
            "id": "retrieval_expert",
            "name": "检索专家", 
            "description": "检索策略优化、质量评估、结果排序、性能优化",
            "capabilities": ["检索优化", "质量评估", "结果排序", "性能优化"]
        },
        {
            "id": "graph_expert",
            "name": "图谱专家",
            "description": "知识图谱构建、关系挖掘、推理查询、可视化建议",
            "capabilities": ["图谱构建", "关系挖掘", "推理查询", "可视化建议"]
        }
    ]
    
    return {
        "success": True,
        "data": {
            "total_experts": len(experts),
            "experts": experts
        }
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "module": "RAG Experts",
        "version": "1.0.0",
        "available_experts": 3,
        "collaboration_enabled": True
    }