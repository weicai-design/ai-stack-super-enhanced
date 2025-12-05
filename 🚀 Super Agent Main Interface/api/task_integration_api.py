#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能任务系统集成API
实现聊天框识别重要信息→备忘录→任务提炼→用户确认→执行的完整流程
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Query, status
from pydantic import BaseModel, Field

from core.task_integration import (
    get_task_integration_system,
    ChatMessage,
    TaskExtractionResult
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/task-integration", tags=["Task Integration"])


# ============ 请求/响应模型 ============

class ChatMessageRequest(BaseModel):
    """聊天消息请求"""
    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class TaskExtractionResponse(BaseModel):
    """任务提取响应"""
    success: bool = Field(..., description="是否成功")
    has_tasks: bool = Field(..., description="是否包含任务")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="提取的任务列表")
    confidence: float = Field(..., description="提取置信度")
    needs_confirmation: bool = Field(..., description="是否需要用户确认")
    extracted_info: Dict[str, Any] = Field(default_factory=dict, description="提取的信息")
    message: Optional[str] = Field(None, description="消息")


class TaskConfirmationRequest(BaseModel):
    """任务确认请求"""
    task_id: str = Field(..., description="任务ID")
    confirmed: bool = Field(True, description="是否确认")
    user_feedback: Optional[str] = Field(None, description="用户反馈")


class TaskExecutionRequest(BaseModel):
    """任务执行请求"""
    task_id: str = Field(..., description="任务ID")
    execution_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行参数")


class TaskExecutionResponse(BaseModel):
    """任务执行响应"""
    success: bool = Field(..., description="是否成功")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="执行状态")
    message: Optional[str] = Field(None, description="消息")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")


# ============ 聊天消息处理API ============

@router.post("/process-chat-message", response_model=TaskExtractionResponse)
async def process_chat_message(request: ChatMessageRequest):
    """
    处理聊天消息，提取任务信息
    
    Args:
        request: 聊天消息请求
        
    Returns:
        任务提取结果
    """
    try:
        integration_system = get_task_integration_system()
        
        # 创建聊天消息对象
        chat_message = ChatMessage(
            role=request.role,
            content=request.content,
            timestamp=request.timestamp or datetime.now(),
            metadata=request.metadata or {}
        )
        
        # 处理消息并提取任务
        result: TaskExtractionResult = await integration_system.process_chat_message(chat_message)
        
        return TaskExtractionResponse(
            success=True,
            has_tasks=result.has_tasks,
            tasks=result.tasks,
            confidence=result.confidence,
            needs_confirmation=result.needs_confirmation,
            extracted_info=result.extracted_info,
            message="任务提取完成" if result.has_tasks else "未检测到任务信息"
        )
        
    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理聊天消息失败: {str(e)}"
        )


@router.post("/confirm-task", response_model=TaskExtractionResponse)
async def confirm_task(request: TaskConfirmationRequest):
    """
    用户确认任务
    
    Args:
        request: 任务确认请求
        
    Returns:
        确认结果
    """
    try:
        integration_system = get_task_integration_system()
        
        # 用户确认任务
        success = await integration_system.confirm_task(
            task_id=request.task_id,
            user_confirmation=request.confirmed
        )
        
        if success:
            return TaskExtractionResponse(
                success=True,
                has_tasks=True,
                tasks=[],
                confidence=1.0,
                needs_confirmation=False,
                extracted_info={"confirmed": request.confirmed},
                message=f"任务{'已确认' if request.confirmed else '已拒绝'}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务确认失败"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"任务确认失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务确认失败: {str(e)}"
        )


@router.post("/execute-task", response_model=TaskExecutionResponse)
async def execute_task(request: TaskExecutionRequest):
    """
    执行任务
    
    Args:
        request: 任务执行请求
        
    Returns:
        执行结果
    """
    try:
        integration_system = get_task_integration_system()
        
        # 执行任务
        success = await integration_system.execute_task(request.task_id)
        
        if success:
            return TaskExecutionResponse(
                success=True,
                task_id=request.task_id,
                status="completed",
                message="任务执行成功",
                result={"execution_time": datetime.now().isoformat()}
            )
        else:
            return TaskExecutionResponse(
                success=False,
                task_id=request.task_id,
                status="failed",
                message="任务执行失败",
                result={"error": "执行过程中发生错误"}
            )
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {str(e)}"
        )


# ============ 任务管理API ============

@router.get("/extracted-tasks")
async def get_extracted_tasks(
    confirmed: Optional[bool] = Query(None, description="是否已确认"),
    limit: int = Query(10, description="返回数量限制")
):
    """
    获取已提取的任务列表
    
    Args:
        confirmed: 是否已确认
        limit: 返回数量限制
        
    Returns:
        任务列表
    """
    try:
        # 在实际系统中，这里会从数据库或存储中获取任务列表
        # 目前返回模拟数据
        
        tasks = [
            {
                "id": "task_001",
                "title": "示例任务1",
                "description": "这是一个示例任务",
                "priority": "medium",
                "status": "pending",
                "needs_confirmation": True,
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # 根据筛选条件过滤
        if confirmed is not None:
            tasks = [t for t in tasks if t.get("needs_confirmation") != confirmed]
        
        # 限制返回数量
        tasks = tasks[:limit]
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks),
            "total": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态
    """
    try:
        # 在实际系统中，这里会从任务生命周期管理器获取状态
        # 目前返回模拟数据
        
        status_info = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "last_updated": datetime.now().isoformat(),
            "estimated_completion": None,
            "current_step": None
        }
        
        return {
            "success": True,
            "task_status": status_info
        }
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )


# ============ 系统状态API ============

@router.get("/system-status")
async def get_system_status():
    """
    获取系统状态
    
    Returns:
        系统状态信息
    """
    try:
        integration_system = get_task_integration_system()
        
        # 获取系统统计信息
        stats = {
            "total_tasks_processed": 0,  # 在实际系统中从数据库获取
            "tasks_extracted": 0,
            "tasks_confirmed": 0,
            "tasks_executed": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0
        }
        
        return {
            "success": True,
            "system_status": "running",
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统状态失败: {str(e)}"
        )


# ============ 配置API ============

@router.get("/configuration")
async def get_configuration():
    """
    获取系统配置
    
    Returns:
        系统配置信息
    """
    try:
        integration_system = get_task_integration_system()
        
        # 返回配置信息
        config = {
            "task_keywords": integration_system.task_keywords[:10],  # 只显示前10个
            "time_patterns": integration_system.time_patterns,
            "priority_keywords": integration_system.priority_keywords,
            "auto_extraction_enabled": True,
            "confirmation_required": True,
            "max_tasks_per_message": 5
        }
        
        return {
            "success": True,
            "configuration": config
        }
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


# 配置日志
import logging
logger = logging.getLogger(__name__)