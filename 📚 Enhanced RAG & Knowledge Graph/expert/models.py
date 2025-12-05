"""专家模型数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field
import uuid

class ExpertModel(BaseModel):
    """专家模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str
    name: str
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    prompts: Dict[str, str] = Field(default_factory=dict)

class ExpertPrompt(BaseModel):
    """专家提示词"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expert_id: str
    scenario: str
    prompt: str
    created_at: datetime = Field(default_factory=datetime.now)

class ExpertAdvice(BaseModel):
    """专家建议"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expert_id: str
    question: str
    advice: str
    confidence: float = 0.8
    created_at: datetime = Field(default_factory=datetime.now)






































