#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源调度器API（生产级实现）
6.2: 提供GPU/CPU/容器状态、冲突队列、调度策略、前端推送的API端点
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

from core.resource_scheduler_with_hints import (
    get_resource_scheduler,
    ResourceType,
    SchedulingStrategy,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resource-scheduler", tags=["Resource Scheduler"])


# ============ 请求/响应模型 ============

class ResourceAllocateRequest(BaseModel):
    """资源分配请求"""
    task_id: str
    resource_type: str
    requested_amount: float
    priority: int = 5
    metadata: Optional[Dict[str, Any]] = None


class StrategySetRequest(BaseModel):
    """策略设置请求"""
    strategy: str
    config: Optional[Dict[str, Any]] = None


class ConflictResolveRequest(BaseModel):
    """冲突解决请求"""
    conflict_id: str
    strategy: Optional[str] = None


# ============ 资源状态API ============

@router.get("/status/cpu")
async def get_cpu_state():
    """
    获取CPU状态
    
    Returns:
        CPU状态
    """
    scheduler = get_resource_scheduler()
    cpu_state = scheduler.get_cpu_state()
    
    if not cpu_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPU状态未初始化，请先启动监控"
        )
    
    return {
        "success": True,
        "cpu_state": cpu_state.to_dict(),
    }


@router.get("/status/gpu")
async def get_gpu_states():
    """
    获取GPU状态
    
    Returns:
        GPU状态列表
    """
    scheduler = get_resource_scheduler()
    gpu_states = scheduler.get_gpu_states()
    
    return {
        "success": True,
        "gpu_states": {gpu_id: gpu.to_dict() for gpu_id, gpu in gpu_states.items()},
        "count": len(gpu_states),
    }


@router.get("/status/containers")
async def get_container_states():
    """
    获取容器状态
    
    Returns:
        容器状态列表
    """
    scheduler = get_resource_scheduler()
    container_states = scheduler.get_container_states()
    
    return {
        "success": True,
        "container_states": {cid: c.to_dict() for cid, c in container_states.items()},
        "count": len(container_states),
    }


@router.get("/status/all")
async def get_all_resource_status():
    """
    获取所有资源状态
    
    Returns:
        所有资源状态
    """
    scheduler = get_resource_scheduler()
    
    return {
        "success": True,
        "cpu": scheduler.get_cpu_state().to_dict() if scheduler.get_cpu_state() else None,
        "gpus": {gpu_id: gpu.to_dict() for gpu_id, gpu in scheduler.get_gpu_states().items()},
        "containers": {cid: c.to_dict() for cid, c in scheduler.get_container_states().items()},
        "resource_status": scheduler.get_resource_status(),
    }


@router.post("/monitoring/start")
async def start_monitoring():
    """
    启动资源监控
    
    Returns:
        启动结果
    """
    scheduler = get_resource_scheduler()
    await scheduler.start_monitoring()
    
    return {
        "success": True,
        "message": "资源监控已启动",
    }


@router.post("/monitoring/stop")
async def stop_monitoring():
    """
    停止资源监控
    
    Returns:
        停止结果
    """
    scheduler = get_resource_scheduler()
    await scheduler.stop_monitoring()
    
    return {
        "success": True,
        "message": "资源监控已停止",
    }


# ============ 冲突队列API ============

@router.get("/conflicts/queue")
async def get_conflict_queue(
    use_priority: bool = Query(False, description="是否使用优先级队列"),
):
    """
    获取冲突队列
    
    Args:
        use_priority: 是否使用优先级队列
        
    Returns:
        冲突队列
    """
    scheduler = get_resource_scheduler()
    conflicts = scheduler.get_conflict_queue(use_priority=use_priority)
    
    return {
        "success": True,
        "conflicts": [c.to_dict() for c in conflicts],
        "count": len(conflicts),
    }


@router.post("/conflicts/resolve")
async def resolve_conflict(request: ConflictResolveRequest):
    """
    解决冲突
    
    Args:
        request: 冲突解决请求
        
    Returns:
        解决结果
    """
    scheduler = get_resource_scheduler()
    
    strategy = None
    if request.strategy:
        try:
            strategy = SchedulingStrategy(request.strategy)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的调度策略: {request.strategy}"
            )
    
    success = scheduler.resolve_conflict(request.conflict_id, strategy)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"冲突不存在或已解决: {request.conflict_id}"
        )
    
    return {
        "success": True,
        "message": f"冲突已解决: {request.conflict_id}",
    }


# ============ 调度策略API ============

@router.post("/strategy/set")
async def set_scheduling_strategy(request: StrategySetRequest):
    """
    设置调度策略
    
    Args:
        request: 策略设置请求
        
    Returns:
        设置结果
    """
    scheduler = get_resource_scheduler()
    
    try:
        strategy = SchedulingStrategy(request.strategy)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的调度策略: {request.strategy}"
        )
    
    success = scheduler.set_scheduling_strategy(strategy, request.config)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="设置调度策略失败"
        )
    
    return {
        "success": True,
        "message": f"调度策略已设置为: {request.strategy}",
    }


@router.get("/strategy/current")
async def get_current_strategy():
    """
    获取当前调度策略
    
    Returns:
        当前策略
    """
    scheduler = get_resource_scheduler()
    strategy = scheduler.get_scheduling_strategy()
    
    return {
        "success": True,
        "strategy": strategy,
    }


@router.get("/strategy/performance")
async def get_strategy_performance(
    strategy: Optional[str] = Query(None, description="策略名称（可选）"),
):
    """
    获取策略性能
    
    Args:
        strategy: 策略名称（可选）
        
    Returns:
        性能指标
    """
    scheduler = get_resource_scheduler()
    
    eval_strategy = None
    if strategy:
        try:
            eval_strategy = SchedulingStrategy(strategy)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的调度策略: {strategy}"
            )
    
    performance = scheduler.evaluate_strategy_performance(eval_strategy)
    
    return {
        "success": True,
        "performance": performance,
    }


# ============ 前端推送API ============

@router.websocket("/push/ws")
async def websocket_push(websocket: WebSocket):
    """
    WebSocket推送端点
    
    Args:
        websocket: WebSocket连接
    """
    await websocket.accept()
    scheduler = get_resource_scheduler()
    
    # 定义推送回调
    async def push_callback(message: Dict[str, Any]):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"WebSocket推送失败: {e}")
            raise
    
    # 订阅推送
    scheduler.subscribe_push(push_callback)
    
    try:
        # 保持连接
        while True:
            # 接收客户端消息（心跳等）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # 处理客户端消息（如果需要）
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # 发送心跳
                await websocket.send_json({"type": "heartbeat"})
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        # 取消订阅
        scheduler.unsubscribe_push(push_callback)
        logger.info("WebSocket连接已关闭")


@router.get("/push/sse")
async def sse_push():
    """
    Server-Sent Events (SSE) 推送端点
    
    Returns:
        SSE流
    """
    scheduler = get_resource_scheduler()
    
    async def event_generator():
        # 定义推送回调
        queue = asyncio.Queue()
        
        async def push_callback(message: Dict[str, Any]):
            await queue.put(message)
        
        # 订阅推送
        scheduler.subscribe_push(push_callback)
        
        try:
            # 发送初始连接消息
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE连接已建立'}, ensure_ascii=False)}\n\n"
            
            # 持续推送消息
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield f"data: {json.dumps({'type': 'heartbeat'}, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # 取消订阅
            scheduler.unsubscribe_push(push_callback)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


__all__ = ["router"]

