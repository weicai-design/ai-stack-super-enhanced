#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP专家模块API接口
提供ERP专家系统的RESTful API服务
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import uvicorn

# 导入ERP专家模块
from .erp_experts import (
    ERPDimension, ERPAnalysis, ERPDataConnector,
    QualityExpert, CostExpert, DeliveryExpert, SafetyExpert,
    ProfitExpert, EfficiencyExpert, ManagementExpert, TechnologyExpert,
    QualityImprovementExpert, CostOptimizationExpert, DeliveryResilienceExpert,
    SafetyComplianceExpert, ProfitGrowthExpert, EfficiencyAutomationExpert,
    TechnologyInnovationExpert, ERPProcessExpert, ERPExpertCollaboration
)

# 创建FastAPI应用
app = FastAPI(
    title="ERP专家系统API",
    description="提供ERP专家系统的智能分析和协作功能",
    version="1.0.0"
)

# 初始化专家和协作管理器
data_connector = ERPDataConnector({"timeout": 30, "max_retries": 3})
collaboration_manager = ERPExpertCollaboration(data_connector)

# 请求模型
class QualityAnalysisRequest(BaseModel):
    quality_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class CostAnalysisRequest(BaseModel):
    cost_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class DeliveryAnalysisRequest(BaseModel):
    delivery_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class CollaborativeAnalysisRequest(BaseModel):
    business_data: Dict[str, Any]
    dimensions: List[str]
    context: Optional[Dict[str, Any]] = None

# 响应模型
class AnalysisResponse(BaseModel):
    dimension: str
    confidence: float
    score: float
    insights: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]

class CollaborativeResponse(BaseModel):
    overall_score: float
    dimension_analyses: List[AnalysisResponse]
    failed_analyses: List[Dict[str, Any]]
    comprehensive_insights: List[str]
    priority_recommendations: List[str]
    collaboration_stats: Dict[str, Any]

class DashboardResponse(BaseModel):
    total_collaborations: int
    recent_dimensions: List[str]
    recent_score: float
    avg_execution_time: float
    success_rate: float

class ExpertInfo(BaseModel):
    expert_id: str
    name: str
    dimension: str

# API端点
@app.post("/api/erp/quality/analyze", response_model=AnalysisResponse)
async def analyze_quality(request: QualityAnalysisRequest):
    """质量维度分析"""
    try:
        expert = QualityExpert(data_connector)
        result = await expert.analyze_quality(request.quality_data, request.context)
        
        return AnalysisResponse(
            dimension=result.dimension.value,
            confidence=result.confidence,
            score=result.score,
            insights=result.insights,
            recommendations=result.recommendations,
            metrics=result.metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"质量分析失败: {str(e)}")

@app.post("/api/erp/cost/analyze", response_model=AnalysisResponse)
async def analyze_cost(request: CostAnalysisRequest):
    """成本维度分析"""
    try:
        expert = CostExpert(data_connector)
        result = await expert.analyze_cost(request.cost_data, request.context)
        
        return AnalysisResponse(
            dimension=result.dimension.value,
            confidence=result.confidence,
            score=result.score,
            insights=result.insights,
            recommendations=result.recommendations,
            metrics=result.metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"成本分析失败: {str(e)}")

@app.post("/api/erp/delivery/analyze", response_model=AnalysisResponse)
async def analyze_delivery(request: DeliveryAnalysisRequest):
    """交期维度分析"""
    try:
        expert = DeliveryExpert(data_connector)
        result = await expert.analyze_delivery(request.delivery_data, request.context)
        
        return AnalysisResponse(
            dimension=result.dimension.value,
            confidence=result.confidence,
            score=result.score,
            insights=result.insights,
            recommendations=result.recommendations,
            metrics=result.metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"交期分析失败: {str(e)}")

@app.post("/api/erp/collaborative/analyze", response_model=CollaborativeResponse)
async def collaborative_analysis(request: CollaborativeAnalysisRequest):
    """多维度协作分析"""
    try:
        # 转换维度字符串为枚举
        dimensions = []
        for dim_str in request.dimensions:
            try:
                dimension = ERPDimension(dim_str)
                dimensions.append(dimension)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的维度: {dim_str}")
        
        result = await collaboration_manager.collaborative_analysis(
            request.business_data, dimensions, request.context
        )
        
        # 转换分析结果
        dimension_analyses = []
        for analysis in result["dimension_analyses"]:
            dimension_analyses.append(AnalysisResponse(**analysis))
        
        return CollaborativeResponse(
            overall_score=result["overall_score"],
            dimension_analyses=dimension_analyses,
            failed_analyses=result["failed_analyses"],
            comprehensive_insights=result["comprehensive_insights"],
            priority_recommendations=result["priority_recommendations"],
            collaboration_stats=result["collaboration_stats"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"协作分析失败: {str(e)}")

@app.get("/api/erp/collaborative/dashboard", response_model=DashboardResponse)
async def get_collaboration_dashboard():
    """获取协作仪表板"""
    try:
        dashboard_data = await collaboration_manager.get_collaboration_dashboard()
        
        if "message" in dashboard_data:
            return DashboardResponse(
                total_collaborations=0,
                recent_dimensions=[],
                recent_score=0.0,
                avg_execution_time=0.0,
                success_rate=0.0
            )
        
        return DashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板失败: {str(e)}")

@app.get("/api/erp/experts", response_model=List[ExpertInfo])
async def get_expert_list():
    """获取专家列表"""
    try:
        experts = collaboration_manager.get_expert_list()
        return [ExpertInfo(**expert) for expert in experts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取专家列表失败: {str(e)}")

@app.get("/api/erp/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ERP专家系统API",
        "version": "1.0.0",
        "connected_systems": data_connector.get_connection_status()["connected_systems"]
    }

@app.get("/api/erp/dimensions")
async def get_dimensions():
    """获取支持的维度列表"""
    return {
        "dimensions": [dim.value for dim in ERPDimension],
        "description": "ERP分析支持的8个核心维度"
    }

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )