#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 11环节 API
提供11个环节的独立管理、试算、监控、导出功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from core.erp_11_stages_manager import erp_11_stages_manager, ERPStage
from analytics.erp_eight_dimensions_analyzer import ERPEightDimensionsAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/erp/stages", tags=["ERP 11环节"])


# ==================== 数据模型 ====================

class StageInstanceRequest(BaseModel):
    """创建环节实例请求"""
    process_id: str = Field(..., description="流程ID")
    initial_data: Optional[Dict[str, Any]] = Field(None, description="初始数据")


class StageMetricsUpdate(BaseModel):
    """更新环节指标请求"""
    metrics: Dict[str, Any] = Field(..., description="指标数据")


class StageTrialCalculate(BaseModel):
    """环节试算请求"""
    metrics: Dict[str, Any] = Field(..., description="试算指标数据")


class StageExportRequest(BaseModel):
    """导出请求"""
    stage_id: Optional[str] = Field(None, description="环节ID（None表示所有）")
    format: str = Field("json", description="导出格式（json/csv/excel）")


# ==================== 环节管理 API ====================

@router.get("/list")
async def list_all_stages():
    """获取所有11个环节信息"""
    try:
        result = erp_11_stages_manager.get_all_stages()
        return result
    except Exception as e:
        logger.error(f"List stages failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环节列表失败: {str(e)}")


@router.get("/{stage_id}")
async def get_stage_info(stage_id: str):
    """获取单个环节信息"""
    try:
        result = erp_11_stages_manager.get_stage_info(stage_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "环节不存在"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get stage info failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取环节信息失败: {str(e)}")


@router.post("/{stage_id}/instance")
async def create_stage_instance(
    stage_id: str,
    request: StageInstanceRequest
):
    """创建环节实例"""
    try:
        result = erp_11_stages_manager.create_stage_instance(
            stage_id=stage_id,
            process_id=request.process_id,
            initial_data=request.initial_data
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "创建失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create instance failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建实例失败: {str(e)}")


@router.post("/instance/{instance_id}/start")
async def start_stage(instance_id: str, data: Optional[Dict[str, Any]] = None):
    """启动环节"""
    try:
        result = erp_11_stages_manager.start_stage(instance_id, data)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "启动失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start stage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动环节失败: {str(e)}")


@router.post("/instance/{instance_id}/metrics")
async def update_stage_metrics(
    instance_id: str,
    request: StageMetricsUpdate
):
    """更新环节指标"""
    try:
        result = erp_11_stages_manager.update_stage_metrics(
            instance_id=instance_id,
            metrics=request.metrics
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "更新失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新指标失败: {str(e)}")


@router.post("/instance/{instance_id}/complete")
async def complete_stage(
    instance_id: str,
    final_data: Optional[Dict[str, Any]] = None
):
    """完成环节"""
    try:
        result = erp_11_stages_manager.complete_stage(instance_id, final_data)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "完成失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete stage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"完成环节失败: {str(e)}")


# ==================== 试算 API ====================

@router.post("/{stage_id}/trial")
async def trial_calculate(
    stage_id: str,
    request: StageTrialCalculate
):
    """试算环节KPI"""
    try:
        result = erp_11_stages_manager.trial_calculate(
            stage_id=stage_id,
            metrics=request.metrics
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "试算失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trial calculate failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试算失败: {str(e)}")


# ==================== 8维度分析 API ====================

@router.post("/{stage_id}/dimensions/analyze")
async def analyze_stage_dimensions(
    stage_id: str,
    instance_id: Optional[str] = None,
    erp_data: Optional[Dict[str, Any]] = None
):
    """
    分析环节的8维度表现
    
    Args:
        stage_id: 环节ID
        instance_id: 实例ID（可选，如果提供则使用实例数据）
        erp_data: ERP数据（可选，如果提供则使用此数据）
    """
    try:
        # 获取数据
        if instance_id:
            if instance_id not in erp_11_stages_manager.stage_instances:
                raise HTTPException(status_code=404, detail="实例不存在")
            instance = erp_11_stages_manager.stage_instances[instance_id]
            analysis_data = {
                "stage_id": stage_id,
                "metrics": instance.get("metrics", {}),
                "data": instance.get("data", {}),
            }
        elif erp_data:
            analysis_data = erp_data
        else:
            raise HTTPException(status_code=400, detail="需要提供 instance_id 或 erp_data")
        
        # 执行8维度分析
        analyzer = ERPEightDimensionsAnalyzer()
        analysis_result = analyzer.analyze(analysis_data)
        
        return {
            "success": True,
            "stage_id": stage_id,
            "instance_id": instance_id,
            "analysis": analysis_result,
            "analyzed_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dimension analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"维度分析失败: {str(e)}")


# ==================== 导出 API ====================

@router.post("/export")
async def export_stage_data(request: StageExportRequest):
    """导出环节数据"""
    try:
        result = erp_11_stages_manager.export_stage_data(
            stage_id=request.stage_id,
            format=request.format
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "导出失败"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ==================== 监听 API ====================

@router.get("/instance/{instance_id}/events")
async def get_stage_events(instance_id: str):
    """获取环节事件历史（监听记录）"""
    try:
        if instance_id not in erp_11_stages_manager.stage_instances:
            raise HTTPException(status_code=404, detail="实例不存在")
        
        instance = erp_11_stages_manager.stage_instances[instance_id]
        
        # 构建事件历史
        events = []
        if instance.get("created_at"):
            events.append({
                "type": "created",
                "timestamp": instance["created_at"],
                "description": "环节实例创建"
            })
        if instance.get("started_at"):
            events.append({
                "type": "started",
                "timestamp": instance["started_at"],
                "description": "环节启动"
            })
        if instance.get("calculated_at"):
            events.append({
                "type": "calculated",
                "timestamp": instance["calculated_at"],
                "description": f"KPI试算完成，得分: {instance.get('kpi_score', 0)}"
            })
        if instance.get("completed_at"):
            events.append({
                "type": "completed",
                "timestamp": instance["completed_at"],
                "description": "环节完成"
            })
        
        return {
            "success": True,
            "instance_id": instance_id,
            "events": events,
            "total_events": len(events)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get events failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取事件失败: {str(e)}")


@router.post("/listeners/register")
async def register_listener(listener_config: Dict[str, Any]):
    """注册监听器（Webhook/回调）"""
    try:
        # 这里可以实现Webhook注册逻辑
        # 简化版：记录到日志
        logger.info(f"Listener registered: {listener_config}")
        
        def listener_callback(event_type: str, data: Dict[str, Any]):
            logger.info(f"Event: {event_type}, Data: {data}")
            # 实际应调用Webhook URL
        
        erp_11_stages_manager.register_listener(listener_callback)
        
        return {
            "success": True,
            "message": "监听器已注册",
            "registered_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Register listener failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册监听器失败: {str(e)}")

