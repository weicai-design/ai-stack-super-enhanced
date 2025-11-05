"""
采购管理API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


class SupplierCreate(BaseModel):
    """创建供应商"""
    code: str
    name: str
    category: Optional[str] = None
    level: str = "B"
    contact_person: Optional[str] = None
    phone: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    """创建采购订单"""
    supplier_id: int
    expected_delivery_date: str
    total_amount: float
    notes: Optional[str] = None


@router.get("/suppliers")
async def get_suppliers(category: Optional[str] = None, limit: int = 50):
    """获取供应商列表"""
    # 模拟数据
    suppliers = [
        {
            "id": 1,
            "code": "SUP001",
            "name": "深圳电子科技有限公司",
            "category": "电子元器件",
            "level": "A",
            "contact_person": "张经理",
            "phone": "138****1234",
            "total_purchase_amount": 1250000,
            "on_time_delivery_rate": 0.95,
            "quality_pass_rate": 0.98,
            "status": "active"
        },
        {
            "id": 2,
            "code": "SUP002",
            "name": "上海材料供应商",
            "category": "原材料",
            "level": "B",
            "contact_person": "李总",
            "phone": "139****5678",
            "total_purchase_amount": 850000,
            "on_time_delivery_rate": 0.92,
            "quality_pass_rate": 0.96,
            "status": "active"
        }
    ]
    
    return {
        "success": True,
        "total": len(suppliers),
        "suppliers": suppliers
    }


@router.post("/suppliers")
async def create_supplier(supplier: SupplierCreate):
    """创建供应商"""
    return {
        "success": True,
        "message": "供应商创建成功",
        "supplier_id": 1
    }


@router.get("/purchase-orders")
async def get_purchase_orders(status: Optional[str] = None, limit: int = 50):
    """获取采购订单列表"""
    orders = [
        {
            "id": 1,
            "po_no": "PO20251101001",
            "supplier_name": "深圳电子科技有限公司",
            "order_date": "2025-11-01",
            "expected_delivery_date": "2025-11-15",
            "total_amount": 125000,
            "paid_amount": 50000,
            "status": "in_transit"
        },
        {
            "id": 2,
            "po_no": "PO20251102001",
            "supplier_name": "上海材料供应商",
            "order_date": "2025-11-02",
            "expected_delivery_date": "2025-11-10",
            "total_amount": 85000,
            "paid_amount": 0,
            "status": "confirmed"
        }
    ]
    
    return {
        "success": True,
        "total": len(orders),
        "orders": orders
    }


@router.post("/purchase-orders")
async def create_purchase_order(order: PurchaseOrderCreate):
    """创建采购订单"""
    return {
        "success": True,
        "message": "采购订单创建成功",
        "po_no": f"PO{datetime.now().strftime('%Y%m%d')}001"
    }


@router.get("/statistics/summary")
async def get_procurement_summary():
    """获取采购统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_suppliers": 15,
            "active_suppliers": 12,
            "total_purchase_orders": 45,
            "pending_orders": 8,
            "in_transit_orders": 12,
            "total_purchase_amount_this_month": 1250000,
            "avg_delivery_rate": 0.93,
            "avg_quality_rate": 0.97
        }
    }


