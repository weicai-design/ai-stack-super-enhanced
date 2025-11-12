"""
ERP数据模型
ERP Models

版本: v1.0.0
"""

from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class Customer(BaseModel):
    """客户信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_level: str = "A"
    created_at: datetime = Field(default_factory=datetime.now)


class Order(BaseModel):
    """订单信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    customer_id: str
    order_no: str
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    status: str = "pending"
    order_date: date
    delivery_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Project(BaseModel):
    """项目信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    customer_id: Optional[str] = None
    description: str = ""
    budget: float = 0
    status: str = "planning"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Purchase(BaseModel):
    """采购信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    supplier: str
    material_name: str
    quantity: int
    unit_price: float
    total_amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)


class Material(BaseModel):
    """物料信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    code: str
    name: str
    category: str
    unit: str
    quantity: int = 0
    min_stock: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class Production(BaseModel):
    """生产信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_id: str
    product_name: str
    plan_quantity: int
    actual_quantity: int = 0
    status: str = "planned"
    created_at: datetime = Field(default_factory=datetime.now)


class Quality(BaseModel):
    """质量检验"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    production_id: str
    inspector: str
    result: str = "pending"
    remarks: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class Warehouse(BaseModel):
    """仓储信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    location: str
    material_id: str
    quantity: int
    created_at: datetime = Field(default_factory=datetime.now)


class Delivery(BaseModel):
    """交付信息"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    order_id: str
    delivery_no: str
    status: str = "preparing"
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)












