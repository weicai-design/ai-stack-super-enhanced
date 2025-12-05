#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG专家系统API（T004）
生产级RAG专家系统API接口，集成知识专家、检索专家、图谱专家
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from core.rag_expert_system import RAGExpertSystem, QueryAnalysis, ExpertAnswer
from core.experts.rag_experts import ExpertDomain

# 创建API路由
router = APIRouter(prefix="/rag-experts", tags=["RAG专家系统"])


# 请求/响应模型定义
class QueryAnalysisRequest(BaseModel):
    """查询分析请求"""
    query: str = Field(..., description="用户查询文本", example="如何优化RAG检索性能？")
    

class QueryAnalysisResponse(BaseModel):
    """查询分析响应"""
    domain: str = Field(..., description="推荐专家领域")
    complexity: float = Field(..., description="查询复杂度(0-1)")
    confidence: float = Field(..., description="分析置信度(0-1)")
    focus_keywords: List[str] = Field(..., description="关键关键词")
    metadata: Dict[str, Any] = Field(..., description="分析元数据")
    timestamp: str = Field(..., description="分析时间戳")


class ExpertAnswerRequest(BaseModel):
    """专家回答请求"""
    query: str = Field(..., description="用户查询文本")
    context: Optional[List[Dict[str, Any]]] = Field(None, description="上下文信息")
    

class ExpertAnswerResponse(BaseModel):
    """专家回答响应"""
    answer: str = Field(..., description="专家回答内容")
    confidence: float = Field(..., description="回答置信度")
    recommendations: List[str] = Field(..., description="专家建议")
    related_concepts: List[str] = Field(..., description="相关概念")
    metadata: Dict[str, Any] = Field(..., description="回答元数据")
    timestamp: str = Field(..., description="回答时间戳")


class KnowledgeAnalysisRequest(BaseModel):
    """知识分析请求"""
    knowledge_items: List[Dict[str, Any]] = Field(..., description="知识条目列表")
    

class KnowledgeAnalysisResponse(BaseModel):
    """知识分析响应"""
    insights: List[str] = Field(..., description="分析洞察")
    recommendations: List[str] = Field(..., description="优化建议")
    metadata: Dict[str, Any] = Field(..., description="分析元数据")
    timestamp: str = Field(..., description="分析时间戳")


class RetrievalOptimizationRequest(BaseModel):
    """检索优化请求"""
    query: str = Field(..., description="查询文本")
    retrieval_results: List[Dict[str, Any]] = Field(..., description="检索结果列表")
    

class RetrievalOptimizationResponse(BaseModel):
    """检索优化响应"""
    insights: List[str] = Field(..., description="优化洞察")
    recommendations: List[str] = Field(..., description="优化建议")
    metadata: Dict[str, Any] = Field(..., description="优化元数据")
    timestamp: str = Field(..., description="优化时间戳")


class GraphAnalysisRequest(BaseModel):
    """图谱分析请求"""
    entities: List[Dict[str, Any]] = Field(..., description="实体列表")
    relations: List[Dict[str, Any]] = Field(..., description="关系列表")
    

class GraphAnalysisResponse(BaseModel):
    """图谱分析响应"""
    insights: List[str] = Field(..., description="分析洞察")
    recommendations: List[str] = Field(..., description="优化建议")
    metadata: Dict[str, Any] = Field(..., description="分析元数据")
    timestamp: str = Field(..., description="分析时间戳")


class CapabilitiesResponse(BaseModel):
    """能力描述响应"""
    capabilities: Dict[str, List[str]] = Field(..., description="各专家能力描述")
    timestamp: str = Field(..., description="响应时间戳")


# 全局专家系统实例
_expert_system: Optional[RAGExpertSystem] = None


def get_expert_system() -> RAGExpertSystem:
    """获取专家系统实例（单例模式）"""
    global _expert_system
    if _expert_system is None:
        _expert_system = RAGExpertSystem()
    return _expert_system


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    获取RAG专家系统能力描述
    
    返回各专家的专业能力和服务范围
    """
    try:
        capabilities = expert_system.describe_capabilities()
        return CapabilitiesResponse(
            capabilities=capabilities,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取能力描述失败: {str(e)}")


@router.post("/analyze-query", response_model=QueryAnalysisResponse)
async def analyze_query(
    request: QueryAnalysisRequest,
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    分析用户查询意图
    
    基于查询内容自动选择最适合的专家领域
    """
    try:
        analysis = expert_system.analyze_query(request.query)
        return QueryAnalysisResponse(
            domain=analysis.domain.value,
            complexity=analysis.complexity,
            confidence=analysis.confidence,
            focus_keywords=analysis.focus_keywords,
            metadata=analysis.metadata,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询分析失败: {str(e)}")


@router.post("/generate-answer", response_model=ExpertAnswerResponse)
async def generate_expert_answer(
    request: ExpertAnswerRequest,
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    生成专家综合回答
    
    综合知识专家、检索专家、图谱专家的分析结果
    """
    try:
        # 分析查询意图
        analysis = expert_system.analyze_query(request.query)
        
        # 生成专家回答
        answer = await expert_system.generate_expert_answer(
            query=request.query,
            analysis=analysis,
            context=request.context
        )
        
        return ExpertAnswerResponse(
            answer=answer.answer,
            confidence=answer.confidence,
            recommendations=answer.recommendations,
            related_concepts=answer.related_concepts,
            metadata=answer.metadata,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成专家回答失败: {str(e)}")


@router.post("/knowledge/analyze", response_model=KnowledgeAnalysisResponse)
async def analyze_knowledge(
    request: KnowledgeAnalysisRequest,
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    知识专家分析
    
    对知识条目进行质量评估、分类分析和优化建议
    """
    try:
        knowledge_expert = expert_system.experts[ExpertDomain.KNOWLEDGE]
        analysis = await knowledge_expert.analyze_knowledge(request.knowledge_items)
        
        return KnowledgeAnalysisResponse(
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识分析失败: {str(e)}")


@router.post("/retrieval/optimize", response_model=RetrievalOptimizationResponse)
async def optimize_retrieval(
    request: RetrievalOptimizationRequest,
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    检索优化专家分析
    
    对检索结果进行质量评估、排序优化和策略建议
    """
    try:
        retrieval_expert = expert_system.experts[ExpertDomain.RETRIEVAL]
        analysis = await retrieval_expert.optimize_retrieval(
            query=request.query,
            retrieval_results=request.retrieval_results
        )
        
        return RetrievalOptimizationResponse(
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索优化失败: {str(e)}")


@router.post("/graph/analyze", response_model=GraphAnalysisResponse)
async def analyze_graph(
    request: GraphAnalysisRequest,
    expert_system: RAGExpertSystem = Depends(get_expert_system)
):
    """
    图谱专家分析
    
    对知识图谱结构进行密度分析、实体关系分析和优化建议
    """
    try:
        graph_expert = expert_system.experts[ExpertDomain.GRAPH]
        analysis = await graph_expert.analyze_graph_structure(
            entities=request.entities,
            relations=request.relations
        )
        
        return GraphAnalysisResponse(
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱分析失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    
    验证RAG专家系统服务状态
    """
    try:
        # 测试专家系统初始化
        expert_system = get_expert_system()
        
        return {
            "status": "healthy",
            "service": "rag_expert_system",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "experts_count": len(expert_system.experts),
                "domains": [domain.value for domain in expert_system.experts.keys()]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")


# API文档配置
router.operation_id = "rag_expert_system_api"
router.description = "RAG专家系统API接口"
router.summary = "提供RAG模块3个专家的智能分析服务"


def setup_rag_expert_system_api(app):
    """设置RAG专家系统API路由"""
    app.include_router(router)
    
    # 初始化专家系统（确保单例模式正常工作）
    try:
        get_expert_system()
        print("✅ RAG专家系统API初始化成功")
    except Exception as e:
        print(f"⚠️ RAG专家系统API初始化警告: {e}")


# 导出API设置函数
__all__ = ["setup_rag_expert_system_api", "router"]