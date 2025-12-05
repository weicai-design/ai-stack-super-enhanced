#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势分析专家模块API接口
提供生产级RESTful API接口，支持外部系统调用
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from trend_experts import (
    get_trend_experts,
    get_trend_expert_monitor,
    TrendStage,
    TrendAnalysis
)

# 配置日志
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="趋势分析专家模块API",
    description="提供生产级趋势分析专家服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
trend_experts = get_trend_experts()
monitor = get_trend_expert_monitor()


class TrendCollectionRequest(BaseModel):
    """趋势采集请求模型"""
    collection_data: Dict[str, Any]
    platforms: List[str] = ["financial", "social_media", "news"]
    context: Dict[str, Any] = {}


class TrendProcessingRequest(BaseModel):
    """趋势处理请求模型"""
    processing_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class TrendAnalysisRequest(BaseModel):
    """趋势分析请求模型"""
    analysis_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class TrendPredictionRequest(BaseModel):
    """趋势预测请求模型"""
    prediction_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class TrendReportRequest(BaseModel):
    """趋势报告请求模型"""
    report_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class TrendAlertRequest(BaseModel):
    """趋势预警请求模型"""
    alert_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class TrendAnalysisResponse(BaseModel):
    """趋势分析响应模型"""
    success: bool
    stage: str
    confidence: float
    accuracy: float
    insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    processing_time: float
    expert_id: str


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "趋势分析专家模块API",
        "version": "1.0.0",
        "available_experts": list(trend_experts.keys())
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "experts_available": len(trend_experts),
        "monitor_status": "active"
    }


@app.post("/analyze/collection", response_model=TrendAnalysisResponse)
async def analyze_trend_collection(
    request: TrendCollectionRequest,
    background_tasks: BackgroundTasks
):
    """趋势采集分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["collection_expert"]
        
        # 执行分析
        analysis = await expert.analyze_collection(
            collection_data=request.collection_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "collection_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="collection_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "collection_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势采集分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/processing", response_model=TrendAnalysisResponse)
async def analyze_trend_processing(
    request: TrendProcessingRequest,
    background_tasks: BackgroundTasks
):
    """趋势处理分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["processing_expert"]
        
        # 执行分析
        analysis = await expert.analyze_processing(
            processing_data=request.processing_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "processing_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="processing_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "processing_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势处理分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/analysis", response_model=TrendAnalysisResponse)
async def analyze_trend_analysis(
    request: TrendAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """趋势分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["analysis_expert"]
        
        # 执行分析
        analysis = await expert.analyze_analysis(
            analysis_data=request.analysis_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "analysis_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="analysis_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "analysis_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/prediction", response_model=TrendAnalysisResponse)
async def analyze_trend_prediction(
    request: TrendPredictionRequest,
    background_tasks: BackgroundTasks
):
    """趋势预测分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["prediction_expert"]
        
        # 执行分析
        analysis = await expert.analyze_prediction(
            prediction_data=request.prediction_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "prediction_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="prediction_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "prediction_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势预测分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/report", response_model=TrendAnalysisResponse)
async def analyze_trend_report(
    request: TrendReportRequest,
    background_tasks: BackgroundTasks
):
    """趋势报告分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["report_expert"]
        
        # 执行分析
        analysis = await expert.analyze_report(
            report_data=request.report_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "report_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="report_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "report_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势报告分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/alert", response_model=TrendAnalysisResponse)
async def analyze_trend_alert(
    request: TrendAlertRequest,
    background_tasks: BackgroundTasks
):
    """趋势预警分析接口"""
    start_time = time.time()
    
    try:
        expert = trend_experts["alert_expert"]
        
        # 执行分析
        analysis = await expert.analyze_alert(
            alert_data=request.alert_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "alert_expert",
            processing_time,
            True
        )
        
        return TrendAnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            accuracy=analysis.accuracy,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="alert_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "alert_expert",
            processing_time,
            False
        )
        
        logger.error(f"趋势预警分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.get("/monitor/performance")
async def get_performance_report():
    """获取性能监控报告"""
    try:
        report = monitor.get_performance_report()
        return {
            "success": True,
            "report": report,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"获取性能报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报告失败: {str(e)}")


@app.get("/experts")
async def list_experts():
    """列出所有可用专家"""
    experts_info = {}
    for expert_id, expert in trend_experts.items():
        experts_info[expert_id] = {
            "name": expert.name,
            "stage": expert.stage.value,
            "data_sources": getattr(expert, 'data_sources', []),
            "analysis_dimensions": getattr(expert, 'analysis_dimensions', []),
            "supported_platforms": getattr(expert, 'supported_platforms', [])
        }
    
    return {
        "success": True,
        "experts": experts_info,
        "total_experts": len(experts_info)
    }


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("趋势分析专家模块API服务启动")
    logger.info(f"已加载 {len(trend_experts)} 个专家")
    logger.info("API文档地址: http://localhost:8001/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("趋势分析专家模块API服务关闭")


if __name__ == "__main__":
    import uvicorn
    
    # 生产级配置
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True,
        workers=4
    )