#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证API接口（T003）

提供SLO性能验证的HTTP接口，支持：
- 验证操作性能是否符合2秒SLO要求
- 获取性能统计信息和报告
- 查看性能告警和历史数据
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.slo_performance_validator import (
    SLOPerformanceValidator,
    get_slo_validator,
    ModuleType,
    SLOValidationResult,
    PerformanceReport,
)

router = APIRouter(prefix="/api/v1/slo-performance", tags=["SLO性能验证"])


class PerformanceValidationRequest(BaseModel):
    """性能验证请求模型"""
    module: str = Field(..., description="模块类型")
    operation: str = Field(..., description="操作名称")
    operation_data: Dict[str, Any] = Field(..., description="操作数据")
    timeout: float = Field(3.0, description="超时时间（秒）")


class PerformanceValidationResponse(BaseModel):
    """性能验证响应模型"""
    success: bool = Field(..., description="验证是否成功")
    validation_result: Dict[str, Any] = Field(..., description="验证结果")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


class PerformanceStatsResponse(BaseModel):
    """性能统计信息响应模型"""
    success: bool = Field(..., description="请求是否成功")
    stats: Dict[str, Any] = Field(..., description="性能统计信息")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


class PerformanceReportResponse(BaseModel):
    """性能报告响应模型"""
    success: bool = Field(..., description="请求是否成功")
    report: Dict[str, Any] = Field(..., description="性能报告")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


class AlertsResponse(BaseModel):
    """告警信息响应模型"""
    success: bool = Field(..., description="请求是否成功")
    alerts: List[Dict[str, Any]] = Field(..., description="告警列表")
    total_count: int = Field(..., description="总告警数")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")


@router.post("/validate", response_model=PerformanceValidationResponse)
async def validate_performance(request: PerformanceValidationRequest) -> PerformanceValidationResponse:
    """
    验证操作性能是否符合2秒SLO要求
    
    通过包装操作函数来测量响应时间并验证SLO合规性
    """
    try:
        # 获取验证器实例
        validator = get_slo_validator()
        
        # 解析模块类型
        try:
            module_type = ModuleType(request.module)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的模块类型: {request.module}"
            )
        
        # 创建操作函数（模拟实际操作）
        async def mock_operation(data: Dict[str, Any]) -> Dict[str, Any]:
            """模拟操作函数"""
            # 模拟处理时间（基于操作复杂度）
            complexity = data.get("complexity", 1.0)
            processing_time = min(complexity * 0.5, 2.5)  # 最大2.5秒
            
            await asyncio.sleep(processing_time)
            
            return {
                "result": "操作执行完成",
                "processing_time": processing_time,
                "data_received": data,
            }
        
        # 执行性能验证
        validation_result = await validator.validate_operation_performance(
            module=module_type,
            operation=request.operation,
            operation_func=mock_operation,
            data=request.operation_data
        )
        
        return PerformanceValidationResponse(
            success=True,
            validation_result=validation_result.to_dict(),
            message="性能验证完成",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"性能验证失败: {str(e)}"
        )


@router.get("/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats() -> PerformanceStatsResponse:
    """获取性能统计信息"""
    try:
        validator = get_slo_validator()
        stats = await validator.get_performance_stats()
        
        return PerformanceStatsResponse(
            success=True,
            stats=stats,
            message="性能统计信息获取成功",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"统计信息获取失败: {str(e)}"
        )


@router.get("/report", response_model=PerformanceReportResponse)
async def get_performance_report(
    hours: int = Query(24, description="报告时间范围（小时）", ge=1, le=168)
) -> PerformanceReportResponse:
    """获取性能报告"""
    try:
        validator = get_slo_validator()
        report = await validator.generate_performance_report(hours)
        
        return PerformanceReportResponse(
            success=True,
            report=report.to_dict(),
            message="性能报告生成成功",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"性能报告生成失败: {str(e)}"
        )


@router.get("/alerts", response_model=AlertsResponse)
async def get_alerts(
    limit: int = Query(10, description="返回告警数量限制", ge=1, le=50),
    severity: Optional[str] = Query(None, description="告警严重程度过滤")
) -> AlertsResponse:
    """获取性能告警信息"""
    try:
        validator = get_slo_validator()
        
        # 过滤告警
        alerts = validator.alerts
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        # 限制数量
        paginated_alerts = alerts[-limit:]
        
        return AlertsResponse(
            success=True,
            alerts=paginated_alerts,
            total_count=len(alerts),
            message="告警信息获取成功",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"告警信息获取失败: {str(e)}"
        )


@router.get("/modules")
async def get_supported_modules() -> Dict[str, Any]:
    """获取支持的模块列表"""
    modules = [
        {
            "name": module.value,
            "description": module.name,
            "slo_threshold": 2.0,
            "critical_operations": []  # 在实际应用中可以从配置中获取
        }
        for module in ModuleType
    ]
    
    return {
        "success": True,
        "modules": modules,
        "total_modules": len(modules),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    try:
        validator = get_slo_validator()
        stats = await validator.get_performance_stats()
        
        return {
            "status": "healthy",
            "validator_initialized": True,
            "total_operations": stats.get("total_operations", 0),
            "slo_threshold": 2.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "validator_initialized": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# API文档配置
router.operation_id = "slo_performance_validation_api"
router.description = "2秒SLO性能验证API接口"
router.summary = "提供系统性能监控和SLO合规性验证的完整API接口"


def setup_slo_performance_validation_api(app):
    """设置SLO性能验证API路由"""
    app.include_router(router)
    
    # 初始化验证器（确保单例模式正常工作）
    try:
        get_slo_validator()
        print("✅ 2秒SLO性能验证器初始化成功")
    except Exception as e:
        print(f"⚠️ 2秒SLO性能验证器初始化警告: {e}")


# 导出API设置函数
__all__ = ["setup_slo_performance_validation_api", "router"]