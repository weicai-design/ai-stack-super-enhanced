#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG双检索验证API接口（T002）

提供RAG双检索验证的HTTP接口，支持：
- 执行完整的双检索验证
- 获取验证统计信息
- 查询验证历史记录
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.rag_double_retrieval_validator import (
    RAGDoubleRetrievalValidator,
    get_double_retrieval_validator,
    DoubleRetrievalValidationReport,
    RetrievalValidationResult,
    ValidationStatus,
    RetrievalType,
)

router = APIRouter(prefix="/api/v1/rag-double-retrieval", tags=["RAG双检索验证"])


class ValidationRequest(BaseModel):
    """验证请求模型"""
    query: str = Field(..., description="用户查询")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="执行结果（用于第2次检索）")
    top_k_first: int = Field(5, description="第1次检索返回数量")
    top_k_second: int = Field(3, description="第2次检索返回数量")


class ValidationResponse(BaseModel):
    """验证响应模型"""
    success: bool = Field(..., description="验证是否成功")
    report: Dict[str, Any] = Field(..., description="验证报告")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


class StatsResponse(BaseModel):
    """统计信息响应模型"""
    success: bool = Field(..., description="请求是否成功")
    stats: Dict[str, Any] = Field(..., description="验证统计信息")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


class HistoryResponse(BaseModel):
    """历史记录响应模型"""
    success: bool = Field(..., description="请求是否成功")
    history: List[Dict[str, Any]] = Field(..., description="验证历史记录")
    total_count: int = Field(..., description="总记录数")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


@router.post("/validate", response_model=ValidationResponse)
async def validate_double_retrieval(request: ValidationRequest) -> ValidationResponse:
    """
    执行RAG双检索验证
    
    验证两次RAG检索的完整性和质量：
    - 第1次检索：理解需求
    - 第2次检索：整合经验知识（如果有执行结果）
    """
    try:
        # 获取验证器实例
        validator = get_double_retrieval_validator()
        
        # 执行验证
        report = await validator.validate_double_retrieval(
            query=request.query,
            execution_result=request.execution_result,
            top_k_first=request.top_k_first,
            top_k_second=request.top_k_second,
        )
        
        return ValidationResponse(
            success=True,
            report=report.to_dict(),
            message="RAG双检索验证完成",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"验证执行失败: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_validation_stats() -> StatsResponse:
    """获取验证统计信息"""
    try:
        validator = get_double_retrieval_validator()
        stats = await validator.get_validation_stats()
        
        return StatsResponse(
            success=True,
            stats=stats,
            message="验证统计信息获取成功",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"统计信息获取失败: {str(e)}"
        )


@router.get("/history", response_model=HistoryResponse)
async def get_validation_history(
    limit: int = Query(10, description="返回记录数量限制", ge=1, le=50),
    offset: int = Query(0, description="偏移量", ge=0),
) -> HistoryResponse:
    """获取验证历史记录"""
    try:
        validator = get_double_retrieval_validator()
        
        # 获取历史记录
        history = validator.validation_history
        total_count = len(history)
        
        # 分页处理
        start_idx = min(offset, total_count)
        end_idx = min(offset + limit, total_count)
        
        paginated_history = [
            report.to_dict() for report in history[start_idx:end_idx]
        ]
        
        return HistoryResponse(
            success=True,
            history=paginated_history,
            total_count=total_count,
            message="验证历史记录获取成功",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"历史记录获取失败: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    try:
        validator = get_double_retrieval_validator()
        stats = await validator.get_validation_stats()
        
        return {
            "status": "healthy",
            "validator_initialized": True,
            "total_validations": stats.get("total_validations", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "validator_initialized": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# API文档配置
router.operation_id = "rag_double_retrieval_validation_api"
router.description = "RAG双检索验证API接口"
router.summary = "提供RAG双检索验证的完整API接口"


def setup_rag_double_retrieval_validation_api(app):
    """设置RAG双检索验证API路由"""
    app.include_router(router)
    
    # 初始化验证器（确保单例模式正常工作）
    try:
        get_double_retrieval_validator()
        print("✅ RAG双检索验证器初始化成功")
    except Exception as e:
        print(f"⚠️ RAG双检索验证器初始化警告: {e}")


# 导出API设置函数
__all__ = ["setup_rag_double_retrieval_validation_api", "router"]