"""交互中心数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import uuid

class Message(BaseModel):
    """消息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: str
    content: str
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

class Session(BaseModel):
    """会话"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class Command(BaseModel):
    """命令"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    command: str
    args: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    executed_at: datetime | None = None






































