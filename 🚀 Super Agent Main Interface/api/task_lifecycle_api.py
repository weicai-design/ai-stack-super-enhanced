#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务生命周期API（生产级实现）
6.1: 提供任务模板、依赖解析、失败回滚、任务总结的API端点
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query, status
from pydantic import BaseModel

from core.task_lifecycle_manager import (
    get_task_lifecycle_manager,
    TaskPriority,
    TaskStatus,
)

router = APIRouter(prefix="/api/task-lifecycle", tags=["Task Lifecycle"])


# ============ 请求/响应模型 ============

class TemplateRegisterRequest(BaseModel):
    """模板注册请求"""
    template_id: str
    template_config: Dict[str, Any]


class TaskCreateFromTemplateRequest(BaseModel):
    """从模板创建任务请求"""
    template_id: str
    task_name: str
    custom_config: Optional[Dict[str, Any]] = None
    priority: str = "medium"


class DependencyAddRequest(BaseModel):
    """添加依赖请求"""
    task_id: str
    depends_on_task_id: str
    dependency_type: str = "required"
    condition: Optional[Dict[str, Any]] = None


class RollbackExecuteRequest(BaseModel):
    """执行回滚请求"""
    task_id: str


# ============ 任务模板API ============

@router.get("/templates")
async def list_templates():
    """
    列出所有任务模板
    
    Returns:
        模板列表
    """
    manager = get_task_lifecycle_manager()
    templates = manager.list_templates()
    
    return {
        "success": True,
        "templates": templates,
        "count": len(templates),
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    获取任务模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        模板配置
    """
    manager = get_task_lifecycle_manager()
    template = manager.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模板不存在: {template_id}"
        )
    
    return {
        "success": True,
        "template": template,
    }


@router.post("/templates/register")
async def register_template(request: TemplateRegisterRequest):
    """
    注册自定义任务模板
    
    Args:
        request: 模板注册请求
        
    Returns:
        注册结果
    """
    manager = get_task_lifecycle_manager()
    success = manager.register_template(
        template_id=request.template_id,
        template_config=request.template_config,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模板注册失败"
        )
    
    return {
        "success": True,
        "message": f"模板已注册: {request.template_id}",
    }


@router.post("/tasks/create-from-template")
async def create_task_from_template(request: TaskCreateFromTemplateRequest):
    """
    从模板创建任务
    
    Args:
        request: 创建任务请求
        
    Returns:
        任务信息
    """
    manager = get_task_lifecycle_manager()
    
    # 转换优先级
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "critical": TaskPriority.CRITICAL,
    }
    priority = priority_map.get(request.priority.lower(), TaskPriority.MEDIUM)
    
    task = manager.create_task_from_template(
        template_id=request.template_id,
        task_name=request.task_name,
        custom_config=request.custom_config,
        priority=priority,
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="从模板创建任务失败"
        )
    
    return {
        "success": True,
        "task": task.to_dict(),
    }


# ============ 依赖解析API ============

@router.post("/dependencies/add")
async def add_dependency(request: DependencyAddRequest):
    """
    添加任务依赖
    
    Args:
        request: 添加依赖请求
        
    Returns:
        添加结果
    """
    manager = get_task_lifecycle_manager()
    success = manager.add_dependency(
        task_id=request.task_id,
        depends_on_task_id=request.depends_on_task_id,
        dependency_type=request.dependency_type,
        condition=request.condition,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="添加依赖失败（可能是循环依赖或任务不存在）"
        )
    
    return {
        "success": True,
        "message": f"依赖已添加: {request.task_id} -> {request.depends_on_task_id}",
    }


@router.get("/dependencies/resolve/{task_id}")
async def resolve_dependencies(task_id: str):
    """
    解析任务依赖
    
    Args:
        task_id: 任务ID
        
    Returns:
        依赖解析结果
    """
    manager = get_task_lifecycle_manager()
    execution_order, conflicts = manager.resolve_dependencies(task_id)
    
    return {
        "success": True,
        "task_id": task_id,
        "execution_order": execution_order,
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0,
    }


@router.post("/dependencies/optimize")
async def optimize_execution_order(task_ids: List[str] = Body(...)):
    """
    优化任务执行顺序
    
    Args:
        task_ids: 任务ID列表
        
    Returns:
        优化后的执行顺序
    """
    manager = get_task_lifecycle_manager()
    execution_order = manager.optimize_execution_order(task_ids)
    
    return {
        "success": True,
        "original_order": task_ids,
        "optimized_order": execution_order,
    }


# ============ 失败回滚API ============

@router.post("/rollback/create/{task_id}")
async def create_rollback_plan(task_id: str):
    """
    创建回滚计划
    
    Args:
        task_id: 任务ID
        
    Returns:
        回滚计划
    """
    manager = get_task_lifecycle_manager()
    rollback_plan = manager.create_rollback_plan(task_id)
    
    if not rollback_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在或无法创建回滚计划: {task_id}"
        )
    
    return {
        "success": True,
        "rollback_plan": rollback_plan.to_dict(),
    }


@router.post("/rollback/execute")
async def execute_rollback(request: RollbackExecuteRequest):
    """
    执行回滚
    
    Args:
        request: 执行回滚请求
        
    Returns:
        回滚结果
    """
    manager = get_task_lifecycle_manager()
    result = await manager.execute_rollback(request.task_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "回滚执行失败")
        )
    
    return {
        "success": True,
        "result": result,
    }


@router.get("/rollback/history")
async def get_rollback_history(
    task_id: Optional[str] = Query(None, description="任务ID（可选）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取回滚历史
    
    Args:
        task_id: 任务ID（可选）
        limit: 返回数量限制
        
    Returns:
        回滚历史列表
    """
    manager = get_task_lifecycle_manager()
    history = manager.get_rollback_history(task_id=task_id, limit=limit)
    
    return {
        "success": True,
        "history": history,
        "count": len(history),
    }


# ============ 任务总结API ============

@router.post("/summary/generate/{task_id}")
async def generate_task_summary(task_id: str):
    """
    生成任务总结
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务总结
    """
    manager = get_task_lifecycle_manager()
    summary = manager.generate_task_summary(task_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )
    
    return {
        "success": True,
        "summary": summary.to_dict(),
    }


@router.get("/summary/{task_id}")
async def get_task_summary(task_id: str):
    """
    获取任务总结
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务总结
    """
    manager = get_task_lifecycle_manager()
    summary = manager.get_task_summary(task_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务总结不存在: {task_id}"
        )
    
    return {
        "success": True,
        "summary": summary.to_dict(),
    }


@router.get("/summary/list")
async def list_task_summaries(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    列出所有任务总结
    
    Args:
        limit: 返回数量限制
        
    Returns:
        任务总结列表
    """
    manager = get_task_lifecycle_manager()
    summaries = manager.get_all_summaries(limit=limit)
    
    return {
        "success": True,
        "summaries": summaries,
        "count": len(summaries),
    }


__all__ = ["router"]

