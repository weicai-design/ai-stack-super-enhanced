"""
售后服务API
包含工单、投诉、维修、退换货等完整功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import date

from core.database import get_db
import sys
sys.path.append('..')
from modules.after_sales.after_sales_manager import get_after_sales_manager

router = APIRouter(prefix="/after-sales", tags=["After Sales API"])


# ============ Pydantic Models ============

class TicketCreate(BaseModel):
    """创建工单请求"""
    order_id: int
    customer_id: int
    ticket_type: str  # complaint, repair, return, exchange, consultation
    priority: Optional[str] = "medium"
    title: str
    description: str
    assigned_to: Optional[str] = None
    reported_by: Optional[str] = None


class TicketUpdate(BaseModel):
    """更新工单请求"""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    customer_satisfaction: Optional[int] = None


class ComplaintCreate(BaseModel):
    """创建投诉请求"""
    ticket_id: Optional[int] = None
    customer_id: int
    order_id: Optional[int] = None
    complaint_type: str  # quality, delivery, service, price, other
    severity: Optional[str] = "medium"
    description: str
    expected_resolution: Optional[str] = None


class RepairCreate(BaseModel):
    """创建维修记录请求"""
    ticket_id: int
    order_id: Optional[int] = None
    product_name: str
    product_code: Optional[str] = None
    serial_number: Optional[str] = None
    issue_description: str
    repair_type: Optional[str] = "warranty"
    technician: Optional[str] = None
    repair_start_date: Optional[date] = None
    repair_cost: Optional[float] = 0
    parts_cost: Optional[float] = 0
    labor_cost: Optional[float] = 0
    warranty_status: Optional[str] = "in_warranty"


class ReturnCreate(BaseModel):
    """创建退换货请求"""
    ticket_id: int
    order_id: int
    return_type: str  # return, exchange
    reason: str
    product_name: str
    product_code: Optional[str] = None
    quantity: float
    return_amount: float
    requested_date: Optional[date] = None
    return_address: Optional[str] = None


# ============ 售后工单API ============

@router.post("/tickets")
async def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db)
):
    """创建售后工单"""
    manager = get_after_sales_manager(db)
    result = manager.create_ticket(ticket.dict())
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """获取工单详情"""
    manager = get_after_sales_manager(db)
    result = manager.get_ticket(ticket_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    
    return result


@router.get("/tickets")
async def list_tickets(
    status: Optional[str] = Query(None, description="工单状态"),
    ticket_type: Optional[str] = Query(None, description="工单类型"),
    priority: Optional[str] = Query(None, description="优先级"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取工单列表"""
    manager = get_after_sales_manager(db)
    return manager.list_tickets(
        status=status,
        ticket_type=ticket_type,
        priority=priority,
        customer_id=customer_id,
        page=page,
        page_size=page_size
    )


@router.put("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """更新工单"""
    manager = get_after_sales_manager(db)
    result = manager.update_ticket(ticket_id, ticket_update.dict(exclude_unset=True))
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


# ============ 客户投诉API ============

@router.post("/complaints")
async def create_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db)
):
    """创建客户投诉"""
    manager = get_after_sales_manager(db)
    result = manager.create_complaint(complaint.dict())
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/complaints")
async def list_complaints(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    complaint_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取投诉列表"""
    manager = get_after_sales_manager(db)
    return manager.list_complaints(
        status=status,
        severity=severity,
        complaint_type=complaint_type,
        page=page,
        page_size=page_size
    )


# ============ 维修记录API ============

@router.post("/repairs")
async def create_repair(
    repair: RepairCreate,
    db: Session = Depends(get_db)
):
    """创建维修记录"""
    manager = get_after_sales_manager(db)
    result = manager.create_repair_record(repair.dict())
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/repairs")
async def list_repairs(
    repair_status: Optional[str] = Query(None),
    repair_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取维修记录列表"""
    manager = get_after_sales_manager(db)
    return manager.list_repair_records(
        repair_status=repair_status,
        repair_type=repair_type,
        page=page,
        page_size=page_size
    )


# ============ 退换货API ============

@router.post("/returns")
async def create_return(
    return_record: ReturnCreate,
    db: Session = Depends(get_db)
):
    """创建退换货记录"""
    manager = get_after_sales_manager(db)
    result = manager.create_return_record(return_record.dict())
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/returns")
async def list_returns(
    return_status: Optional[str] = Query(None),
    return_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取退换货记录列表"""
    manager = get_after_sales_manager(db)
    return manager.list_return_records(
        return_status=return_status,
        return_type=return_type,
        page=page,
        page_size=page_size
    )


# ============ 售后数据分析API ============

@router.get("/statistics")
async def get_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取售后统计数据"""
    manager = get_after_sales_manager(db)
    return manager.get_statistics(start_date=start_date, end_date=end_date)


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "module": "after-sales",
        "version": "1.0.0"
    }


