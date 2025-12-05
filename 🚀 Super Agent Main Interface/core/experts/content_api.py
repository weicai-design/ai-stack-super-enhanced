"""
内容创作专家模块API接口
提供内容策划、生成、去AI化、发布、运营、版权等专家服务的REST API
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import time
import logging

from .content_experts import (
    ContentPlanningExpert, ContentGenerationExpert, ContentDeAIExpert,
    ContentPublishExpert, ContentOperationExpert, ContentCopyrightExpert,
    ContentDataConnector, ContentExpertCollaboration, get_content_experts
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="内容创作专家API",
    description="提供内容创作全流程专家分析服务",
    version="1.0.0"
)

# 全局变量
content_data_connector = ContentDataConnector()
content_collaboration = ContentExpertCollaboration(content_data_connector)

# 请求/响应模型
class ContentPlanningRequest(BaseModel):
    topics: List[str] = Field(..., description="内容主题列表")
    target_audience: Dict[str, Any] = Field(..., description="目标受众信息")
    publish_plan: Dict[str, Any] = Field(..., description="发布计划")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentGenerationRequest(BaseModel):
    content: str = Field(..., description="内容文本")
    has_title: bool = Field(True, description="是否有标题")
    has_intro: bool = Field(True, description="是否有引言")
    has_conclusion: bool = Field(True, description="是否有结论")
    multimodal: Optional[Dict[str, Any]] = Field(None, description="多模态信息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentDeAIRequest(BaseModel):
    ai_detection_rate: float = Field(..., description="AI检测率")
    naturalness: float = Field(..., description="自然度评分")
    originality: float = Field(..., description="原创性评分")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentPublishRequest(BaseModel):
    platforms: List[str] = Field(..., description="发布平台列表")
    publish_time: str = Field(..., description="发布时间")
    frequency: int = Field(..., description="发布频率")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentOperationRequest(BaseModel):
    read_data: Dict[str, Any] = Field(..., description="阅读数据")
    interaction_data: Dict[str, Any] = Field(..., description="互动数据")
    conversion_data: Dict[str, Any] = Field(..., description="转化数据")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentCopyrightRequest(BaseModel):
    originality_score: float = Field(..., description="原创性评分")
    similarity_analysis: Dict[str, Any] = Field(..., description="相似度分析")
    risk_assessment: Dict[str, Any] = Field(..., description="风险评估")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class CollaborativeAnalysisRequest(BaseModel):
    content_data: Dict[str, Any] = Field(..., description="内容数据")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ContentWorkflowRequest(BaseModel):
    topic: str = Field(..., description="内容主题")
    target_audience: str = Field(..., description="目标受众")
    content_type: str = Field("text", description="内容类型")

class AnalysisResponse(BaseModel):
    success: bool = Field(..., description="分析是否成功")
    score: float = Field(..., description="分析评分")
    confidence: float = Field(..., description="置信度")
    insights: List[str] = Field(..., description="分析洞察")
    recommendations: List[str] = Field(..., description="优化建议")
    metadata: Dict[str, Any] = Field(..., description="元数据")

class CollaborativeAnalysisResponse(BaseModel):
    success: bool = Field(..., description="分析是否成功")
    overall_score: float = Field(..., description="综合评分")
    overall_confidence: float = Field(..., description="综合置信度")
    expert_results: Dict[str, Any] = Field(..., description="专家结果")
    combined_insights: List[str] = Field(..., description="综合洞察")
    prioritized_recommendations: List[Dict[str, Any]] = Field(..., description="优先级建议")
    expert_count: int = Field(..., description="参与专家数量")

class WorkflowResponse(BaseModel):
    success: bool = Field(..., description="工作流是否成功")
    workflow_data: Dict[str, Any] = Field(..., description="工作流数据")
    analysis_result: Dict[str, Any] = Field(..., description="分析结果")
    workflow_id: str = Field(..., description="工作流ID")

class DashboardResponse(BaseModel):
    total_collaborations: int = Field(..., description="总协作次数")
    average_score: float = Field(..., description="平均评分")
    average_expert_count: float = Field(..., description="平均专家数量")
    success_rate: float = Field(..., description="成功率")

class ExpertInfo(BaseModel):
    expert_id: str = Field(..., description="专家ID")
    name: str = Field(..., description="专家名称")
    stage: str = Field(..., description="专家阶段")
    capabilities: List[str] = Field(..., description="专家能力")

# API端点
@app.post("/api/content/planning/analyze", response_model=AnalysisResponse)
async def analyze_content_planning(request: ContentPlanningRequest):
    """内容策划分析"""
    try:
        expert = ContentPlanningExpert()
        result = await expert.analyze_planning(
            {
                "topics": request.topics,
                "target_audience": request.target_audience,
                "publish_plan": request.publish_plan
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容策划分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/generation/analyze", response_model=AnalysisResponse)
async def analyze_content_generation(request: ContentGenerationRequest):
    """内容生成分析"""
    try:
        expert = ContentGenerationExpert(content_data_connector)
        result = await expert.analyze_generation(
            {
                "content": request.content,
                "has_title": request.has_title,
                "has_intro": request.has_intro,
                "has_conclusion": request.has_conclusion,
                "multimodal": request.multimodal
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容生成分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/generation/multimodal", response_model=Dict[str, Any])
async def generate_multimodal_content(request: ContentGenerationRequest):
    """生成多模态内容"""
    try:
        expert = ContentGenerationExpert(content_data_connector)
        result = await expert.generate_multimodal_content(
            request.content,
            request.multimodal or {}
        )
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"多模态内容生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/deai/analyze", response_model=AnalysisResponse)
async def analyze_content_deai(request: ContentDeAIRequest):
    """内容去AI化分析"""
    try:
        expert = ContentDeAIExpert(content_data_connector)
        result = await expert.analyze_deai(
            {
                "ai_detection_rate": request.ai_detection_rate,
                "naturalness": request.naturalness,
                "originality": request.originality
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容去AI化分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/deai/enhance", response_model=Dict[str, Any])
async def enhance_content_naturalness(request: ContentDeAIRequest):
    """增强内容自然度"""
    try:
        expert = ContentDeAIExpert(content_data_connector)
        result = await expert.enhance_naturalness(
            request.ai_detection_rate,
            request.naturalness
        )
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"内容自然度增强失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/publish/analyze", response_model=AnalysisResponse)
async def analyze_content_publish(request: ContentPublishRequest):
    """内容发布分析"""
    try:
        expert = ContentPublishExpert()
        result = await expert.analyze_publish(
            {
                "platforms": request.platforms,
                "publish_time": request.publish_time,
                "frequency": request.frequency
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容发布分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/operation/analyze", response_model=AnalysisResponse)
async def analyze_content_operation(request: ContentOperationRequest):
    """内容运营分析"""
    try:
        expert = ContentOperationExpert()
        result = await expert.analyze_operation(
            {
                "read_data": request.read_data,
                "interaction_data": request.interaction_data,
                "conversion_data": request.conversion_data
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容运营分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/copyright/analyze", response_model=AnalysisResponse)
async def analyze_content_copyright(request: ContentCopyrightRequest):
    """内容版权分析"""
    try:
        expert = ContentCopyrightExpert()
        result = await expert.analyze_copyright(
            {
                "originality_score": request.originality_score,
                "similarity_analysis": request.similarity_analysis,
                "risk_assessment": request.risk_assessment
            },
            request.context
        )
        
        return AnalysisResponse(
            success=True,
            score=result.score,
            confidence=result.confidence,
            insights=result.insights,
            recommendations=result.recommendations,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"内容版权分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/collaboration/analyze", response_model=CollaborativeAnalysisResponse)
async def collaborative_content_analysis(request: CollaborativeAnalysisRequest):
    """内容专家协作分析"""
    try:
        result = await content_collaboration.collaborative_analysis(
            request.content_data,
            request.context
        )
        
        return CollaborativeAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"协作分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/workflow/generate", response_model=WorkflowResponse)
async def generate_content_workflow(request: ContentWorkflowRequest):
    """生成内容创作工作流"""
    try:
        result = await content_collaboration.generate_content_workflow(
            request.topic,
            request.target_audience,
            request.content_type
        )
        
        return WorkflowResponse(**result)
    except Exception as e:
        logger.error(f"工作流生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/collaboration/dashboard", response_model=DashboardResponse)
async def get_collaboration_dashboard():
    """获取协作仪表板数据"""
    try:
        dashboard_data = content_collaboration.get_collaboration_dashboard()
        return DashboardResponse(**dashboard_data)
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/experts/list", response_model=List[ExpertInfo])
async def get_content_experts_list():
    """获取内容专家列表"""
    try:
        experts_list = content_collaboration.get_expert_list()
        return [ExpertInfo(**expert) for expert in experts_list]
    except Exception as e:
        logger.error(f"获取专家列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/data/connections", response_model=Dict[str, Any])
async def get_data_connections():
    """获取数据连接状态"""
    try:
        connections = content_data_connector.get_connection_status()
        return {"success": True, "connections": connections}
    except Exception as e:
        logger.error(f"获取数据连接状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/generation/dashboard", response_model=Dict[str, Any])
async def get_generation_dashboard():
    """获取生成仪表板数据"""
    try:
        expert = ContentGenerationExpert(content_data_connector)
        dashboard_data = expert.get_generation_dashboard()
        return {"success": True, "dashboard": dashboard_data}
    except Exception as e:
        logger.error(f"获取生成仪表板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/deai/dashboard", response_model=Dict[str, Any])
async def get_deai_dashboard():
    """获取去AI化仪表板数据"""
    try:
        expert = ContentDeAIExpert(content_data_connector)
        dashboard_data = expert.get_detection_dashboard()
        return {"success": True, "dashboard": dashboard_data}
    except Exception as e:
        logger.error(f"获取去AI化仪表板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "content_experts_api",
        "version": "1.0.0"
    }

@app.get("/api/content/dimensions", response_model=List[str])
async def get_content_dimensions():
    """获取内容分析维度列表"""
    return [
        "内容策划",
        "内容生成", 
        "去AI化处理",
        "内容发布",
        "内容运营",
        "版权检测"
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)