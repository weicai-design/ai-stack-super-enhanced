"""
业务管理API
- 客户管理
- 订单管理
- 项目管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import sys
sys.path.append('..')
from core.database import get_db
from modules.customer.customer_manager import CustomerManager
from modules.order.order_manager import OrderManager
from modules.project.project_manager import ProjectManager
from api.data_listener_api import data_listener


router = APIRouter(prefix="/business", tags=["business"])


# ============ 数据模型 ============

class CustomerCreate(BaseModel):
    name: str
    code: str
    category: str = "普通"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None


# ============ 客户管理API ============

@router.get("/customers")
async def get_customers(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取客户列表"""
    manager = CustomerManager(db)
    result = manager.list_customers(category, keyword, page, page_size)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """获取客户详情"""
    manager = CustomerManager(db)
    result = manager.get_customer(customer_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.post("/customers")
async def create_customer(
    customer: CustomerCreate, 
    db: Session = Depends(get_db)
):
    """创建新客户"""
    manager = CustomerManager(db)
    result = manager.create_customer(customer.dict())
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.put("/customers/{customer_id}")
async def update_customer(
    customer_id: int,
    update: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """更新客户信息"""
    manager = CustomerManager(db)
    result = manager.update_customer(customer_id, update.dict(exclude_unset=True))
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """删除客户"""
    manager = CustomerManager(db)
    result = manager.delete_customer(customer_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/customers/{customer_id}/analysis")
async def analyze_customer(customer_id: int, db: Session = Depends(get_db)):
    """客户价值分析"""
    manager = CustomerManager(db)
    result = manager.analyze_customer_value(customer_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/customers/{customer_id}/trend")
async def get_customer_trend(
    customer_id: int,
    period: str = "month",
    db: Session = Depends(get_db)
):
    """客户订单趋势"""
    manager = CustomerManager(db)
    result = manager.get_customer_order_trend(customer_id, period)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.post("/customers/{customer_id}/upgrade")
async def upgrade_customer(
    customer_id: int,
    new_category: str,
    reason: str = "",
    db: Session = Depends(get_db)
):
    """升级客户类别"""
    manager = CustomerManager(db)
    result = manager.upgrade_customer_category(customer_id, new_category, reason)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


# ============ 订单管理API（待实现） ============

@router.get("/orders")
async def get_orders(
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    manager = OrderManager(db, data_listener=data_listener)
    result = manager.list_orders(customer_id, status, None, None, page, page_size)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', '获取订单列表失败'))
    
    return result


# ============ 项目管理API（待实现） ============

@router.get("/projects")
async def get_projects(
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    # TODO: 实现项目管理器
    return {
        "success": True,
        "message": "项目管理功能开发中"
    }











