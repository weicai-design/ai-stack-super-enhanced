"""股票交易数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

class Stock(BaseModel):
    """股票信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    market: str
    price: float = 0
    change: float = 0
    volume: int = 0
    updated_at: datetime = Field(default_factory=datetime.now)

class Strategy(BaseModel):
    """交易策略"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: str = ""
    rules: Dict = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

class Trade(BaseModel):
    """交易记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    stock_code: str
    action: str
    quantity: int
    price: float
    amount: float
    executed_at: datetime = Field(default_factory=datetime.now)

class Portfolio(BaseModel):
    """投资组合"""
    tenant_id: str
    total_value: float = 0
    cash: float = 0
    holdings: List[Dict] = Field(default_factory=list)
    total_return: float = 0






















