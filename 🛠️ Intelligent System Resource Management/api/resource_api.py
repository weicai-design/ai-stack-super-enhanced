"""
资源管理系统API
集成自动启动、自适应进化、问题交互等功能
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from scheduler.auto_start_manager import AutoStartManager, AutoStartConfig
from resource_manager.adaptive_evolver import AdaptiveEvolver, EvolutionStrategy
from resource_manager.user_interaction_manager import UserInteractionManager, InteractionType

router = APIRouter(prefix="/api/resources", tags=["Resource Management API"])

# 初始化管理器
auto_start_manager = AutoStartManager()
adaptive_evolver = AdaptiveEvolver()
user_interaction_manager = UserInteractionManager()


# ============ Pydantic Models ============

class AutoStartRequest(BaseModel):
    """自动启动请求"""
    enabled: bool = True
    services: Optional[List[str]] = None
    delay_seconds: int = 5


class EvolutionConfigRequest(BaseModel):
    """进化配置请求"""
    strategy: str = "balanced"  # conservative, balanced, aggressive
    interval: int = 300  # 秒


class UserInteractionRequest(BaseModel):
    """用户交互请求"""
    interaction_id: str
    user_response: str


# ============ 自动启动API ============

@router.post("/auto-start/enable")
async def enable_auto_start(request: AutoStartRequest):
    """
    启用自动启动
    
    Args:
        request: 自动启动配置
        
    Returns:
        启用结果
    """
    try:
        success = await auto_start_manager.enable_auto_start(request.services)
        if success:
            await auto_start_manager.start_monitoring()
        
        return {
            "success": success,
            "message": "自动启动已启用" if success else "自动启动启用失败",
            "status": await auto_start_manager.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用自动启动失败: {str(e)}")


@router.post("/auto-start/disable")
async def disable_auto_start():
    """禁用自动启动"""
    try:
        success = await auto_start_manager.disable_auto_start()
        await auto_start_manager.stop_monitoring()
        
        return {
            "success": success,
            "message": "自动启动已禁用" if success else "自动启动禁用失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用自动启动失败: {str(e)}")


@router.get("/auto-start/status")
async def get_auto_start_status():
    """获取自动启动状态"""
    try:
        status = await auto_start_manager.get_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


# ============ 自适应进化API ============

@router.post("/evolution/start")
async def start_evolution(config: Optional[EvolutionConfigRequest] = None):
    """
    启动自适应进化
    
    Args:
        config: 进化配置
        
    Returns:
        启动结果
    """
    try:
        if config:
            evolution_config = {
                "strategy": config.strategy,
                "interval": config.interval
            }
            await adaptive_evolver.initialize(config=evolution_config)
        
        await adaptive_evolver.start()
        
        return {
            "success": True,
            "message": "自适应进化已启动",
            "status": await adaptive_evolver.get_evolution_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动自适应进化失败: {str(e)}")


@router.post("/evolution/stop")
async def stop_evolution():
    """停止自适应进化"""
    try:
        await adaptive_evolver.stop()
        
        return {
            "success": True,
            "message": "自适应进化已停止"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止自适应进化失败: {str(e)}")


@router.get("/evolution/status")
async def get_evolution_status():
    """获取进化状态"""
    try:
        status = await adaptive_evolver.get_evolution_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取进化状态失败: {str(e)}")


# ============ 用户交互API ============

@router.post("/interaction/confirm")
async def request_confirmation(
    title: str = Body(...),
    message: str = Body(...),
    options: Optional[List[str]] = Body(None),
    timeout_seconds: Optional[int] = Body(None),
    priority: str = Body("normal")
):
    """
    请求用户确认
    
    Args:
        title: 标题
        message: 消息内容
        options: 选项列表
        timeout_seconds: 超时时间
        priority: 优先级
        
    Returns:
        用户响应
    """
    try:
        response = await user_interaction_manager.request_user_confirmation(
            title=title,
            message=message,
            options=options,
            timeout_seconds=timeout_seconds,
            priority=priority
        )
        
        return {
            "success": True,
            "user_response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"请求确认失败: {str(e)}")


@router.post("/interaction/notify")
async def show_notification(
    title: str = Body(...),
    message: str = Body(...),
    priority: str = Body("normal"),
    duration_seconds: int = Body(5)
):
    """显示通知"""
    try:
        await user_interaction_manager.show_notification(
            title=title,
            message=message,
            priority=priority,
            duration_seconds=duration_seconds
        )
        
        return {
            "success": True,
            "message": "通知已发送"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"显示通知失败: {str(e)}")


@router.post("/interaction/alert")
async def show_alert(
    title: str = Body(...),
    message: str = Body(...),
    priority: str = Body("high")
):
    """显示警告"""
    try:
        await user_interaction_manager.show_alert(
            title=title,
            message=message,
            priority=priority
        )
        
        return {
            "success": True,
            "message": "警告已发送"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"显示警告失败: {str(e)}")


@router.post("/interaction/response")
async def handle_user_response(request: UserInteractionRequest):
    """
    处理用户响应
    
    Args:
        request: 用户响应请求
        
    Returns:
        处理结果
    """
    try:
        success = await user_interaction_manager.handle_user_response(
            request.interaction_id,
            request.user_response
        )
        
        return {
            "success": success,
            "message": "响应已处理" if success else "响应处理失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理用户响应失败: {str(e)}")


@router.get("/interaction/pending")
async def get_pending_interactions():
    """获取待处理的交互列表"""
    try:
        interactions = await user_interaction_manager.get_pending_interactions()
        return {
            "success": True,
            "interactions": interactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待处理交互失败: {str(e)}")


@router.get("/interaction/history")
async def get_interaction_history(limit: int = 20):
    """获取交互历史"""
    try:
        history = await user_interaction_manager.get_interaction_history(limit)
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交互历史失败: {str(e)}")


# ============ 综合状态API ============

@router.get("/status")
async def get_resource_status():
    """获取资源管理综合状态"""
    try:
        auto_start_status = await auto_start_manager.get_status()
        evolution_status = await adaptive_evolver.get_evolution_status()
        interaction_status = await user_interaction_manager.get_health_status()
        
        return {
            "success": True,
            "auto_start": auto_start_status,
            "evolution": evolution_status,
            "interaction": interaction_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取资源状态失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "auto_start": "available",
            "evolution": "available",
            "interaction": "available"
        }
    }


