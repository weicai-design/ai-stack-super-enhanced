"""学习数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import uuid

class LearningRecord(BaseModel):
    """学习记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    module: str
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    learned_at: datetime = Field(default_factory=datetime.now)

class UserPreference(BaseModel):
    """用户偏好"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.now)

class Optimization(BaseModel):
    """优化建议"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    category: str
    suggestion: str
    priority: str = "medium"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)

















