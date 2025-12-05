#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证API（T001）

功能：
1. 提供工作流验证的REST API接口
2. 实时查询验证状态和结果
3. 验证报告生成和下载
4. 验证统计信息查询
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from core.workflow_enhanced_validator import (
    WorkflowEnhancedValidator,
    get_enhanced_validator,
    WorkflowValidationReport,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow/validation", tags=["工作流验证"])


class ValidationRequest(BaseModel):
    """验证请求"""
    workflow_id: str = Field(..., description="工作流ID")
    workflow_type: str = Field(..., description="工作流类型")
    user_input: str = Field(..., description="用户输入")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class ValidationResultResponse(BaseModel):
    """验证结果响应"""
    name: str = Field(..., description="验证名称")
    status: str = Field(..., description="验证状态")
    level: str = Field(..., description="验证级别")
    description: str = Field(..., description="验证描述")
    details: Dict[str, Any] = Field(default_factory=dict, description="验证详情")
    timestamp: str = Field(..., description="时间戳")
    error: Optional[str] = Field(None, description="错误信息")


class ValidationReportResponse(BaseModel):
    """验证报告响应"""
    validation_id: str = Field(..., description="验证ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_type: str = Field(..., description="工作流类型")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    total_duration: float = Field(..., description="总时长")
    overall_status: str = Field(..., description="整体状态")
    summary: Dict[str, Any] = Field(..., description="摘要信息")
    validation_results: List[ValidationResultResponse] = Field(..., description="验证结果列表")


class ValidationStatsResponse(BaseModel):
    """验证统计响应"""
    total_validations: int = Field(..., description="总验证次数")
    passed_validations: int = Field(..., description="通过验证次数")
    failed_validations: int = Field(..., description="失败验证次数")
    warning_validations: int = Field(..., description="警告验证次数")
    pass_rate: float = Field(..., description="通过率")
    last_updated: str = Field(..., description="最后更新时间")


class ValidationSummaryResponse(BaseModel):
    """验证摘要响应"""
    active_validations: int = Field(..., description="活跃验证数量")
    completed_validations: int = Field(..., description="完成验证数量")
    overall_pass_rate: float = Field(..., description="整体通过率")
    recent_validations: List[Dict[str, Any]] = Field(..., description="最近验证列表")


@router.post("/start", response_model=Dict[str, str])
async def start_workflow_validation(
    request: ValidationRequest,
    validator: WorkflowEnhancedValidator = Depends(get_enhanced_validator),
) -> Dict[str, str]:
    """
    开始工作流验证
    
    Args:
        request: 验证请求
        validator: 验证器实例
        
    Returns:
        验证ID
    """
    try:
        validation_id = await validator.start_workflow_validation(
            workflow_id=request.workflow_id,
            workflow_type=request.workflow_type,
            user_input=request.user_input,
            context=request.context,
        )
        
        logger.info(f"开始工作流验证: {validation_id}")
        
        return {
            "validation_id": validation_id,
            "message": "验证已开始",
            "workflow_id": request.workflow_id,
        }
        
    except Exception as e:
        logger.error(f"开始验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"开始验证失败: {str(e)}")


@router.get("/report/{validation_id}", response_model=ValidationReportResponse)
async def get_validation_report(
    validation_id: str,
    validator: WorkflowEnhancedValidator = Depends(get_enhanced_validator),
) -> ValidationReportResponse:
    """
    获取验证报告
    
    Args:
        validation_id: 验证ID
        validator: 验证器实例
        
    Returns:
        验证报告
    """
    try:
        report = await validator.get_validation_report(validation_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="验证报告不存在")
        
        # 转换为响应模型
        return ValidationReportResponse(
            validation_id=validation_id,
            workflow_id=report.workflow_id,
            workflow_type=report.workflow_type,
            start_time=report.start_time,
            end_time=report.end_time,
            total_duration=report.total_duration,
            overall_status=report.overall_status.value,
            summary=report.summary,
            validation_results=[
                ValidationResultResponse(
                    name=r.name,
                    status=r.status.value,
                    level=r.level.value,
                    description=r.description,
                    details=r.details,
                    timestamp=r.timestamp,
                    error=r.error,
                )
                for r in report.validation_results
            ],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取验证报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取验证报告失败: {str(e)}")


@router.get("/stats", response_model=ValidationStatsResponse)
async def get_validation_stats(
    validator: WorkflowEnhancedValidator = Depends(get_enhanced_validator),
) -> ValidationStatsResponse:
    """
    获取验证统计信息
    
    Args:
        validator: 验证器实例
        
    Returns:
        验证统计信息
    """
    try:
        stats = await validator.get_validation_stats()
        
        total = stats["total_validations"]
        passed = stats["passed_validations"]
        
        return ValidationStatsResponse(
            total_validations=total,
            passed_validations=passed,
            failed_validations=stats["failed_validations"],
            warning_validations=stats["warning_validations"],
            pass_rate=passed / total if total > 0 else 0,
            last_updated=datetime.utcnow().isoformat() + "Z",
        )
        
    except Exception as e:
        logger.error(f"获取验证统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取验证统计失败: {str(e)}")


@router.get("/summary", response_model=ValidationSummaryResponse)
async def get_validation_summary(
    limit: int = Query(default=10, ge=1, le=100, description="返回数量限制"),
    validator: WorkflowEnhancedValidator = Depends(get_enhanced_validator),
) -> ValidationSummaryResponse:
    """
    获取验证摘要
    
    Args:
        limit: 返回数量限制
        validator: 验证器实例
        
    Returns:
        验证摘要
    """
    try:
        # 获取活跃验证数量
        active_count = len(validator.active_validations)
        
        # 获取完成验证数量
        completed_count = len(validator.validation_reports)
        
        # 获取统计信息
        stats = await validator.get_validation_stats()
        total = stats["total_validations"]
        passed = stats["passed_validations"]
        overall_pass_rate = passed / total if total > 0 else 0
        
        # 获取最近的验证报告
        recent_reports = []
        for validation_id, report in list(validator.validation_reports.items())[-limit:]:
            recent_reports.append({
                "validation_id": validation_id,
                "workflow_id": report.workflow_id,
                "workflow_type": report.workflow_type,
                "overall_status": report.overall_status.value,
                "total_duration": report.total_duration,
                "start_time": report.start_time,
            })
        
        return ValidationSummaryResponse(
            active_validations=active_count,
            completed_validations=completed_count,
            overall_pass_rate=overall_pass_rate,
            recent_validations=recent_reports,
        )
        
    except Exception as e:
        logger.error(f"获取验证摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取验证摘要失败: {str(e)}")


@router.delete("/{validation_id}")
async def stop_validation(
    validation_id: str,
    validator: WorkflowEnhancedValidator = Depends(get_enhanced_validator),
) -> Dict[str, str]:
    """
    停止验证
    
    Args:
        validation_id: 验证ID
        validator: 验证器实例
        
    Returns:
        操作结果
    """
    try:
        success = await validator.stop_validation(validation_id)
        
        if success:
            return {"message": f"验证 {validation_id} 已停止"}
        else:
            raise HTTPException(status_code=404, detail="验证不存在或已完成")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止验证失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止验证失败: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "workflow_validation_api",
    }


# 验证回调示例
async def validation_callback_example(validation_id: str, report: WorkflowValidationReport):
    """验证回调示例"""
    logger.info(f"验证回调: {validation_id}, 状态: {report.overall_status.value}")
    
    # 这里可以添加自定义逻辑，比如发送通知、记录日志等
    if report.overall_status == ValidationStatus.FAILED:
        logger.warning(f"验证失败: {validation_id}")
    elif report.overall_status == ValidationStatus.WARNING:
        logger.info(f"验证警告: {validation_id}")
    else:
        logger.info(f"验证通过: {validation_id}")


# 注册回调函数（在应用启动时调用）
def register_validation_callbacks():
    """注册验证回调函数"""
    validator = get_enhanced_validator()
    validator.add_validation_callback(validation_callback_example)


# 应用启动时注册回调
register_validation_callbacks()