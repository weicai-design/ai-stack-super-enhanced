"""内容创作数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field
import uuid

class Material(BaseModel):
    """创作素材"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    content: str
    source: str = ""
    tags: List[str] = Field(default_factory=list)
    collected_at: datetime = Field(default_factory=datetime.now)

class Content(BaseModel):
    """创作内容"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    body: str
    platform: str
    status: str = "draft"
    views: int = 0
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: datetime | None = None

class PublishPlan(BaseModel):
    """发布计划"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    content_id: str
    platform: str
    scheduled_at: datetime
    status: str = "pending"






































