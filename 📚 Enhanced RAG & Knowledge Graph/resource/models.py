"""资源管理数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict
from pydantic import BaseModel, Field
import uuid

class ResourceUsage(BaseModel):
    """资源使用情况"""
    cpu_percent: float = 0
    memory_percent: float = 0
    disk_percent: float = 0
    timestamp: datetime = Field(default_factory=datetime.now)

class ResourceConfig(BaseModel):
    """资源配置"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    cpu_limit: int = 80
    memory_limit: int = 80
    disk_limit: int = 90
    auto_scale: bool = True

class Alert(BaseModel):
    """资源警报"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    message: str
    level: str = "warning"
    created_at: datetime = Field(default_factory=datetime.now)






















