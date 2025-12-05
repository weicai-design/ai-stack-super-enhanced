#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习曲线API（生产级实现）
6.2: 提供行为日志聚合、模型策略更新、专家建议表的API端点
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query, status
from pydantic import BaseModel

from core.learning_curve_tracker import get_learning_curve_tracker

router = APIRouter(prefix="/api/learning-curve", tags=["Learning Curve"])


# ============ 请求/响应模型 ============

class BehaviorLogRecordRequest(BaseModel):
    """行为日志记录请求"""
    user_id: str
    action_type: str
    module: str
    function: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    success: bool = True
    duration: Optional[float] = None


class BehaviorAggregationRequest(BaseModel):
    """行为日志聚合请求"""
    user_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    action_type: Optional[str] = None
    module: Optional[str] = None
    group_by: str = "hour"  # hour/day/week/month


class StrategyCreateRequest(BaseModel):
    """策略创建请求"""
    model_name: str
    strategy_name: str
    strategy_config: Dict[str, Any]


class StrategyUpdateRequest(BaseModel):
    """策略更新请求"""
    strategy_id: str
    strategy_config: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class SuggestionGenerateRequest(BaseModel):
    """建议生成请求"""
    curve_id: Optional[str] = None
    user_id: Optional[str] = None
    suggestion_type: str = "general"
    title: str = ""
    content: str = ""
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


class SuggestionUpdateRequest(BaseModel):
    """建议更新请求"""
    suggestion_id: str
    status: str
    feedback: Optional[Dict[str, Any]] = None


# ============ 行为日志API ============

@router.post("/behavior/log")
async def record_behavior(request: BehaviorLogRecordRequest):
    """
    记录行为日志
    
    Args:
        request: 行为日志记录请求
        
    Returns:
        记录结果
    """
    tracker = get_learning_curve_tracker()
    log = tracker.record_behavior(
        user_id=request.user_id,
        action_type=request.action_type,
        module=request.module,
        function=request.function,
        context=request.context,
        success=request.success,
        duration=request.duration,
    )
    
    return {
        "success": True,
        "log": log.to_dict(),
    }


@router.post("/behavior/aggregate")
async def aggregate_behavior_logs(request: BehaviorAggregationRequest):
    """
    聚合行为日志
    
    Args:
        request: 行为日志聚合请求
        
    Returns:
        聚合结果
    """
    tracker = get_learning_curve_tracker()
    aggregated = tracker.aggregate_behavior_logs(
        user_id=request.user_id,
        start_time=request.start_time,
        end_time=request.end_time,
        action_type=request.action_type,
        module=request.module,
        group_by=request.group_by,
    )
    
    return {
        "success": True,
        "aggregated": aggregated,
    }


@router.get("/behavior/patterns")
async def analyze_behavior_patterns(
    user_id: Optional[str] = Query(None, description="用户ID（可选）"),
    days: int = Query(30, ge=1, le=365, description="分析天数"),
):
    """
    分析行为模式
    
    Args:
        user_id: 用户ID（可选）
        days: 分析天数
        
    Returns:
        行为模式分析结果
    """
    tracker = get_learning_curve_tracker()
    patterns = tracker.analyze_behavior_patterns(user_id=user_id, days=days)
    
    return {
        "success": True,
        "patterns": patterns,
    }


# ============ 模型策略API ============

@router.post("/strategy/create")
async def create_strategy(request: StrategyCreateRequest):
    """
    创建模型策略
    
    Args:
        request: 策略创建请求
        
    Returns:
        策略信息
    """
    tracker = get_learning_curve_tracker()
    strategy = tracker.create_strategy(
        model_name=request.model_name,
        strategy_name=request.strategy_name,
        strategy_config=request.strategy_config,
    )
    
    return {
        "success": True,
        "strategy": strategy.to_dict(),
    }


@router.post("/strategy/update")
async def update_strategy(request: StrategyUpdateRequest):
    """
    更新模型策略
    
    Args:
        request: 策略更新请求
        
    Returns:
        更新结果
    """
    tracker = get_learning_curve_tracker()
    strategy = tracker.update_strategy(
        strategy_id=request.strategy_id,
        strategy_config=request.strategy_config,
        performance_metrics=request.performance_metrics,
    )
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在: {request.strategy_id}"
        )
    
    return {
        "success": True,
        "strategy": strategy.to_dict(),
    }


@router.post("/strategy/activate/{strategy_id}")
async def activate_strategy(strategy_id: str):
    """
    激活模型策略
    
    Args:
        strategy_id: 策略ID
        
    Returns:
        激活结果
    """
    tracker = get_learning_curve_tracker()
    success = tracker.activate_strategy(strategy_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在: {strategy_id}"
        )
    
    return {
        "success": True,
        "message": f"策略已激活: {strategy_id}",
    }


@router.get("/strategy/{model_name}")
async def get_strategy(
    model_name: str,
    strategy_id: Optional[str] = Query(None, description="策略ID（可选，如果为空则返回激活的策略）"),
):
    """
    获取模型策略
    
    Args:
        model_name: 模型名称
        strategy_id: 策略ID（可选）
        
    Returns:
        策略信息
    """
    tracker = get_learning_curve_tracker()
    strategy = tracker.get_strategy(model_name=model_name, strategy_id=strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"策略不存在: {model_name} / {strategy_id}"
        )
    
    return {
        "success": True,
        "strategy": strategy.to_dict(),
    }


@router.get("/strategy/list")
async def list_strategies(
    model_name: Optional[str] = Query(None, description="模型名称（可选）"),
    active_only: bool = Query(False, description="是否只返回激活的策略"),
):
    """
    列出模型策略
    
    Args:
        model_name: 模型名称（可选）
        active_only: 是否只返回激活的策略
        
    Returns:
        策略列表
    """
    tracker = get_learning_curve_tracker()
    strategies = tracker.list_strategies(model_name=model_name, active_only=active_only)
    
    return {
        "success": True,
        "strategies": [s.to_dict() for s in strategies],
        "count": len(strategies),
    }


# ============ 专家建议API ============

@router.post("/suggestion/generate")
async def generate_suggestion(request: SuggestionGenerateRequest):
    """
    生成专家建议
    
    Args:
        request: 建议生成请求
        
    Returns:
        建议信息
    """
    tracker = get_learning_curve_tracker()
    suggestion = tracker.generate_expert_suggestion(
        curve_id=request.curve_id,
        user_id=request.user_id,
        suggestion_type=request.suggestion_type,
        title=request.title,
        content=request.content,
        priority=request.priority,
        metadata=request.metadata,
    )
    
    return {
        "success": True,
        "suggestion": suggestion.to_dict(),
    }


@router.post("/suggestion/generate-from-curve/{curve_id}")
async def generate_suggestions_from_curve(curve_id: str):
    """
    从学习曲线生成专家建议
    
    Args:
        curve_id: 学习曲线ID
        
    Returns:
        建议列表
    """
    tracker = get_learning_curve_tracker()
    suggestions = tracker.generate_suggestions_from_curve(curve_id)
    
    return {
        "success": True,
        "suggestions": [s.to_dict() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/suggestion/generate-from-behavior/{user_id}")
async def generate_suggestions_from_behavior(user_id: str):
    """
    从行为日志生成专家建议
    
    Args:
        user_id: 用户ID
        
    Returns:
        建议列表
    """
    tracker = get_learning_curve_tracker()
    suggestions = tracker.generate_suggestions_from_behavior(user_id)
    
    return {
        "success": True,
        "suggestions": [s.to_dict() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/suggestion/update")
async def update_suggestion(request: SuggestionUpdateRequest):
    """
    更新建议状态
    
    Args:
        request: 建议更新请求
        
    Returns:
        更新结果
    """
    tracker = get_learning_curve_tracker()
    success = tracker.update_suggestion_status(
        suggestion_id=request.suggestion_id,
        status=request.status,
        feedback=request.feedback,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"建议不存在: {request.suggestion_id}"
        )
    
    return {
        "success": True,
        "message": f"建议状态已更新: {request.suggestion_id}",
    }


@router.get("/suggestion/list")
async def list_suggestions(
    curve_id: Optional[str] = Query(None, description="学习曲线ID（可选）"),
    user_id: Optional[str] = Query(None, description="用户ID（可选）"),
    suggestion_type: Optional[str] = Query(None, description="建议类型（可选）"),
    status: Optional[str] = Query(None, description="状态（可选）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    获取专家建议列表
    
    Args:
        curve_id: 学习曲线ID（可选）
        user_id: 用户ID（可选）
        suggestion_type: 建议类型（可选）
        status: 状态（可选）
        limit: 返回数量限制
        
    Returns:
        建议列表
    """
    tracker = get_learning_curve_tracker()
    suggestions = tracker.get_suggestions(
        curve_id=curve_id,
        user_id=user_id,
        suggestion_type=suggestion_type,
        status=status,
        limit=limit,
    )
    
    return {
        "success": True,
        "suggestions": [s.to_dict() for s in suggestions],
        "count": len(suggestions),
    }


@router.post("/suggestion/link/{suggestion_id}/{curve_id}")
async def link_suggestion_to_curve(suggestion_id: str, curve_id: str):
    """
    将建议关联到学习曲线
    
    Args:
        suggestion_id: 建议ID
        curve_id: 学习曲线ID
        
    Returns:
        关联结果
    """
    tracker = get_learning_curve_tracker()
    success = tracker.link_suggestion_to_curve(suggestion_id, curve_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"建议或学习曲线不存在: {suggestion_id} / {curve_id}"
        )
    
    return {
        "success": True,
        "message": f"建议已关联到学习曲线: {suggestion_id} -> {curve_id}",
    }


__all__ = ["router"]

