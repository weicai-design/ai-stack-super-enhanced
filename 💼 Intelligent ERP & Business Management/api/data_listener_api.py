"""
ERP数据监听API
提供事件监听和处理的RESTful接口
"""

from fastapi import APIRouter, HTTPException, Body, Request, Header
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# 修复相对导入问题 - T0006-3优化
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入ERP监听器相关模块
from core.data_listener import EventType, ERPEvent
from core.listener_container import data_listener
from erp_listener import get_erp_listener, ListenerMode

router = APIRouter(prefix="/api/erp/listener", tags=["ERP Data Listener"])

# 初始化ERP监听器
erp_listener = get_erp_listener()


class EventHandlerRequest(BaseModel):
    """事件处理器注册请求"""
    event_type: str
    handler_name: str
    handler_url: Optional[str] = None  # Webhook URL
    priority: int = 0


class EventEmitRequest(BaseModel):
    """事件发出请求"""
    event_type: str
    entity_type: str
    entity_id: str
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/start")
async def start_listening():
    """启动数据监听系统"""
    try:
        await data_listener.start_listening()
        return {
            "success": True,
            "message": "数据监听系统已启动",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_listening():
    """停止数据监听系统"""
    try:
        await data_listener.stop_listening()
        return {
            "success": True,
            "message": "数据监听系统已停止",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_listener_status():
    """获取监听系统状态"""
    stats = data_listener.get_statistics()
    return {
        "success": True,
        "status": {
            "is_listening": stats["is_listening"],
            "total_events": stats["total_events"],
            "queue_size": stats["queue_size"],
            "handlers_count": stats["handlers_count"],
            "history_size": stats["history_size"],
            "events_by_type": stats["events_by_type"],
            "errors": stats["errors"]
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post("/register-handler")
async def register_handler(request: EventHandlerRequest):
    """注册事件处理器"""
    try:
        # 解析事件类型
        try:
            event_type = EventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {request.event_type}"
            )
        
        # 创建处理器函数
        async def handler_wrapper(event: ERPEvent):
            if request.handler_url:
                # Webhook处理器
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            request.handler_url,
                            json={
                                "event_type": event.event_type.value,
                                "entity_type": event.entity_type,
                                "entity_id": event.entity_id,
                                "old_data": event.old_data,
                                "new_data": event.new_data,
                                "metadata": event.metadata,
                                "timestamp": event.timestamp.isoformat()
                            }
                        )
                        response.raise_for_status()
                except Exception as e:
                    logger.error(f"Webhook调用失败: {request.handler_url}, 错误: {e}")
                    raise
        
        # 注册处理器
        data_listener.register_handler(
            event_type=event_type,
            handler=handler_wrapper,
            priority=request.priority
        )
        
        return {
            "success": True,
            "message": f"事件处理器已注册: {request.event_type}",
            "handler_name": request.handler_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 4.3: ERP监听器Webhook端点 ============

@router.post("/webhook")
async def handle_erp_webhook(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
):
    """
    接收ERP系统Webhook请求
    
    这是4.3实现的核心端点，用于接收ERP系统的推送事件
    """
    try:
        # 获取请求头
        headers = dict(request.headers)
        
        # 处理Webhook
        result = await erp_listener.handle_webhook(
            payload=payload,
            signature=x_signature,
            headers=headers,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-polling")
async def start_erp_polling():
    """启动ERP轮询"""
    try:
        await erp_listener.start_polling()
        return {
            "success": True,
            "message": "轮询已启动",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-polling")
async def stop_erp_polling():
    """停止ERP轮询"""
    try:
        await erp_listener.stop_polling()
        return {
            "success": True,
            "message": "轮询已停止",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_erp_listener_status():
    """获取ERP监听器状态"""
    try:
        status = erp_listener.get_status()
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-queue/size")
async def get_task_queue_size():
    """获取任务队列大小"""
    try:
        size = await erp_listener.get_task_queue_size()
        return {
            "success": True,
            "queue_size": size,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task-queue/clear")
async def clear_task_queue():
    """清空任务队列"""
    try:
        await erp_listener.clear_task_queue()
        return {
            "success": True,
            "message": "任务队列已清空",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emit-event")
async def emit_event(request: EventEmitRequest):
    """手动发出事件"""
    try:
        # 解析事件类型
        try:
            event_type = EventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的事件类型: {request.event_type}"
            )
        
        # 创建事件
        event = ERPEvent(
            event_type=event_type,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            old_data=request.old_data,
            new_data=request.new_data,
            metadata=request.metadata
        )
        
        # 发出事件
        await data_listener.emit_event(event)
        
        return {
            "success": True,
            "message": "事件已发出",
            "event_id": f"{event.entity_type}:{event.entity_id}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/history")
async def get_event_history(
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100
):
    """获取事件历史"""
    try:
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的事件类型: {event_type}"
                )
        
        events = data_listener.get_event_history(
            event_type=event_type_enum,
            entity_type=entity_type,
            limit=limit
        )
        
        # 转换为字典格式
        events_data = [
            {
                "event_type": e.event_type.value,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "old_data": e.old_data,
                "new_data": e.new_data,
                "metadata": e.metadata,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ]
        
        return {
            "success": True,
            "events": events_data,
            "count": len(events_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/order-created")
async def on_order_created(order_data: Dict[str, Any] = Body(...)):
    """订单创建事件（便捷接口）"""
    await data_listener.on_order_created(order_data)
    return {"success": True, "message": "订单创建事件已发出"}


@router.post("/events/order-updated")
async def on_order_updated(
    order_id: str = Body(...),
    old_data: Dict[str, Any] = Body(...),
    new_data: Dict[str, Any] = Body(...)
):
    """订单更新事件（便捷接口）"""
    await data_listener.on_order_updated(order_id, old_data, new_data)
    return {"success": True, "message": "订单更新事件已发出"}


@router.post("/events/inventory-updated")
async def on_inventory_updated(
    inventory_id: str = Body(...),
    old_data: Dict[str, Any] = Body(...),
    new_data: Dict[str, Any] = Body(...)
):
    """库存更新事件（便捷接口）"""
    await data_listener.on_inventory_updated(inventory_id, old_data, new_data)
    return {"success": True, "message": "库存更新事件已发出"}


@router.post("/events/financial-updated")
async def on_financial_updated(
    financial_id: str = Body(...),
    old_data: Dict[str, Any] = Body(...),
    new_data: Dict[str, Any] = Body(...)
):
    """财务数据更新事件（便捷接口）"""
    await data_listener.on_financial_data_updated(financial_id, old_data, new_data)
    return {"success": True, "message": "财务数据更新事件已发出"}


@router.delete("/events/history")
async def clear_event_history():
    """清空事件历史"""
    data_listener.clear_history()
    return {
        "success": True,
        "message": "事件历史已清空",
        "timestamp": datetime.now().isoformat()
    }

