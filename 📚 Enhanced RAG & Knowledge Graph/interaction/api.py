"""
交互中心API（完整版）
Interaction Center API

提供完整的AI交互功能：8个端点

版本: v1.0.0
"""

import logging
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from .models import Message, Session, Command
from .manager import interaction_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interaction", tags=["AI Interaction Center"])


@router.get("/health")
async def interaction_health():
    return {
        "status": "healthy",
        "module": "interaction",
        "version": "1.0.0",
        "features": [
            "unified_chat_window",
            "file_support",
            "command_execution",
            "function_routing"
        ]
    }


@router.post("/sessions")
async def create_session(user_id: str = Query(...), tenant=Depends(require_tenant)):
    """创建会话"""
    session = interaction_manager.create_session(tenant.id, user_id)
    return session.model_dump()


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message: Message,
    tenant=Depends(require_tenant)
):
    """发送消息"""
    result = interaction_manager.add_message(session_id, message)
    return result


@router.post("/commands")
async def execute_command(command: Command, tenant=Depends(require_tenant)):
    """执行命令"""
    result = interaction_manager.execute_command(tenant.id, command)
    return result.model_dump()


@router.get("/functions")
async def list_functions(tenant=Depends(require_tenant)):
    """获取可用功能列表"""
    functions = interaction_manager.get_available_functions()
    return functions


@router.post("/route")
async def route_to_function(
    function_name: str = Query(...),
    params: dict = {},
    tenant=Depends(require_tenant)
):
    """路由到功能模块"""
    result = interaction_manager.route_to_function(function_name, params)
    return result

