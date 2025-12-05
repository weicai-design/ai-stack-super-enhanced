#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI编程助手专家模块API接口
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

from coding_experts import (
    get_coding_experts,
    get_coding_expert_monitor,
    CodingStage,
    CodingAnalysis
)

# 配置日志
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI编程助手专家模块API",
    description="提供生产级编程助手专家服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
coding_experts = get_coding_experts()
monitor = get_coding_expert_monitor()


class CodeGenerationRequest(BaseModel):
    """代码生成请求模型"""
    code_data: Dict[str, Any]
    language: str
    context: Dict[str, Any] = {}


class CodeReviewRequest(BaseModel):
    """代码审查请求模型"""
    code_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class PerformanceOptimizationRequest(BaseModel):
    """性能优化请求模型"""
    performance_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class BugFixRequest(BaseModel):
    """Bug修复请求模型"""
    bug_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class DocumentationRequest(BaseModel):
    """文档生成请求模型"""
    doc_data: Dict[str, Any]
    context: Dict[str, Any] = {}


class AnalysisResponse(BaseModel):
    """分析响应模型"""
    success: bool
    stage: str
    confidence: float
    score: float
    insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    processing_time: float
    expert_id: str


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "AI编程助手专家模块API",
        "version": "1.0.0",
        "available_experts": list(coding_experts.keys())
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "experts_available": len(coding_experts),
        "monitor_status": "active"
    }


@app.post("/analyze/code-generation", response_model=AnalysisResponse)
async def analyze_code_generation(
    request: CodeGenerationRequest,
    background_tasks: BackgroundTasks
):
    """代码生成分析接口"""
    start_time = time.time()
    
    try:
        expert = coding_experts["generation_expert"]
        
        # 执行分析
        analysis = await expert.analyze_generation(
            code_data=request.code_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "generation_expert",
            processing_time,
            True
        )
        
        return AnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            score=analysis.score,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="generation_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "generation_expert",
            processing_time,
            False
        )
        
        logger.error(f"代码生成分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/code-review", response_model=AnalysisResponse)
async def analyze_code_review(
    request: CodeReviewRequest,
    background_tasks: BackgroundTasks
):
    """代码审查分析接口"""
    start_time = time.time()
    
    try:
        expert = coding_experts["review_expert"]
        
        # 执行分析
        analysis = await expert.analyze_review(
            review_data=request.code_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "review_expert",
            processing_time,
            True
        )
        
        return AnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            score=analysis.score,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="review_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "review_expert",
            processing_time,
            False
        )
        
        logger.error(f"代码审查分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/performance-optimization", response_model=AnalysisResponse)
async def analyze_performance_optimization(
    request: PerformanceOptimizationRequest,
    background_tasks: BackgroundTasks
):
    """性能优化分析接口"""
    start_time = time.time()
    
    try:
        expert = coding_experts["optimization_expert"]
        
        # 执行分析
        analysis = await expert.analyze_performance(
            performance_data=request.performance_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "optimization_expert",
            processing_time,
            True
        )
        
        return AnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            score=analysis.score,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="optimization_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "optimization_expert",
            processing_time,
            False
        )
        
        logger.error(f"性能优化分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/bug-fix", response_model=AnalysisResponse)
async def analyze_bug_fix(
    request: BugFixRequest,
    background_tasks: BackgroundTasks
):
    """Bug修复分析接口"""
    start_time = time.time()
    
    try:
        expert = coding_experts["bug_fix_expert"]
        
        # 执行分析
        analysis = await expert.analyze_bug(
            bug_data=request.bug_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "bug_fix_expert",
            processing_time,
            True
        )
        
        return AnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            score=analysis.score,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="bug_fix_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "bug_fix_expert",
            processing_time,
            False
        )
        
        logger.error(f"Bug修复分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze/documentation", response_model=AnalysisResponse)
async def analyze_documentation(
    request: DocumentationRequest,
    background_tasks: BackgroundTasks
):
    """文档生成分析接口"""
    start_time = time.time()
    
    try:
        expert = coding_experts["documentation_expert"]
        
        # 执行分析
        analysis = await expert.analyze_documentation(
            doc_data=request.doc_data,
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        # 记录监控数据
        background_tasks.add_task(
            monitor.record_request,
            "documentation_expert",
            processing_time,
            True
        )
        
        return AnalysisResponse(
            success=True,
            stage=analysis.stage.value,
            confidence=analysis.confidence,
            score=analysis.score,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            metadata=analysis.metadata,
            processing_time=processing_time,
            expert_id="documentation_expert"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        background_tasks.add_task(
            monitor.record_request,
            "documentation_expert",
            processing_time,
            False
        )
        
        logger.error(f"文档生成分析失败: {str(e)}")
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
    for expert_id, expert in coding_experts.items():
        experts_info[expert_id] = {
            "name": expert.name,
            "stage": expert.stage.value,
            "data_sources": getattr(expert, 'data_sources', []),
            "analysis_dimensions": getattr(expert, 'analysis_dimensions', []),
            "supported_languages": getattr(expert, 'supported_languages', [])
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
    logger.info("AI编程助手专家模块API服务启动")
    logger.info(f"已加载 {len(coding_experts)} 个专家")
    logger.info("API文档地址: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("AI编程助手专家模块API服务关闭")


if __name__ == "__main__":
    import uvicorn
    
    # 生产级配置
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        workers=4
    )