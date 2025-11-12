"""
ERP集成API（完整版）
ERP Integration API

提供完整的ERP功能API端点：18个端点

版本: v1.0.0
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from .models import Customer, Order, Project, Purchase, Material, Production, Quality, Warehouse, Delivery
from .manager import erp_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/erp", tags=["ERP Management"])


@router.get("/health")
async def erp_health():
    """ERP模块健康检查"""
    return {
        "status": "healthy",
        "module": "erp",
        "version": "1.0.0",
        "features": [
            "customer_management", "order_management", "project_management",
            "purchase_management", "material_management", "production_management",
            "quality_management", "warehouse_management", "delivery_management"
        ]
    }


# ==================== 客户管理 ====================

@router.post("/customers")
async def add_customer(customer: Customer, tenant=Depends(require_tenant)):
    """添加客户"""
    result = erp_manager.add_customer(tenant.id, customer)
    return result.model_dump()


@router.get("/customers")
async def get_customers(
    tenant=Depends(require_tenant),
    industry: Optional[str] = Query(None, description="按行业过滤"),
    credit_level: Optional[str] = Query(None, description="按信用等级过滤")
):
    """获取客户列表"""
    filters = {}
    if industry:
        filters["industry"] = industry
    if credit_level:
        filters["credit_level"] = credit_level
    customers = erp_manager.get_customers(tenant.id, filters if filters else None)
    return [c.model_dump() for c in customers]


# ==================== 订单管理 ====================

@router.post("/orders")
async def create_order(order: Order, tenant=Depends(require_tenant)):
    """创建订单"""
    result = erp_manager.create_order(tenant.id, order)
    return result.model_dump()


@router.get("/orders")
async def get_orders(
    tenant=Depends(require_tenant),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None)
):
    """获取订单列表"""
    filters = {}
    if status:
        filters["status"] = status
    if customer_id:
        filters["customer_id"] = customer_id
    orders = erp_manager.get_orders(tenant.id, filters if filters else None)
    return [o.model_dump() for o in orders]


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str = Query(...),
    tenant=Depends(require_tenant)
):
    """更新订单状态"""
    result = erp_manager.update_order_status(tenant.id, order_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="订单不存在")
    return result.model_dump()


# ==================== 项目管理 ====================

@router.post("/projects")
async def create_project(project: Project, tenant=Depends(require_tenant)):
    """创建项目"""
    result = erp_manager.create_project(tenant.id, project)
    return result.model_dump()


@router.get("/projects")
async def get_projects(tenant=Depends(require_tenant)):
    """获取项目列表"""
    projects = erp_manager.get_projects(tenant.id)
    return [p.model_dump() for p in projects]


# ==================== 采购管理 ====================

@router.post("/purchases")
async def create_purchase(purchase: Purchase, tenant=Depends(require_tenant)):
    """创建采购单"""
    result = erp_manager.create_purchase(tenant.id, purchase)
    return result.model_dump()


@router.get("/purchases")
async def get_purchases(tenant=Depends(require_tenant)):
    """获取采购列表"""
    purchases = erp_manager.get_purchases(tenant.id)
    return [p.model_dump() for p in purchases]


# ==================== 物料管理 ====================

@router.post("/materials")
async def manage_material(material: Material, tenant=Depends(require_tenant)):
    """管理物料"""
    result = erp_manager.manage_material(tenant.id, material)
    return result.model_dump()


@router.get("/materials")
async def get_materials(tenant=Depends(require_tenant)):
    """获取物料列表"""
    materials = erp_manager.get_materials(tenant.id)
    return [m.model_dump() for m in materials]


# ==================== 生产管理 ====================

@router.post("/productions")
async def create_production(production: Production, tenant=Depends(require_tenant)):
    """创建生产计划"""
    result = erp_manager.create_production_plan(tenant.id, production)
    return result.model_dump()


@router.get("/productions")
async def get_productions(tenant=Depends(require_tenant)):
    """获取生产列表"""
    productions = erp_manager.get_productions(tenant.id)
    return [p.model_dump() for p in productions]


# ==================== 质量管理 ====================

@router.post("/quality")
async def record_quality(quality: Quality, tenant=Depends(require_tenant)):
    """记录质量检验"""
    result = erp_manager.record_quality_check(tenant.id, quality)
    return result.model_dump()


# ==================== 仓储管理 ====================

@router.post("/warehouse")
async def warehouse_in(warehouse: Warehouse, tenant=Depends(require_tenant)):
    """入库操作"""
    result = erp_manager.warehouse_in(tenant.id, warehouse)
    return result.model_dump()


@router.get("/inventory")
async def get_inventory(tenant=Depends(require_tenant)):
    """获取库存"""
    inventory = erp_manager.get_inventory(tenant.id)
    return [i.model_dump() for i in inventory]


# ==================== 交付管理 ====================

@router.post("/deliveries")
async def create_delivery(delivery: Delivery, tenant=Depends(require_tenant)):
    """创建交付单"""
    result = erp_manager.create_delivery(tenant.id, delivery)
    return result.model_dump()


@router.get("/deliveries")
async def get_deliveries(tenant=Depends(require_tenant)):
    """获取交付列表"""
    deliveries = erp_manager.get_deliveries(tenant.id)
    return [d.model_dump() for d in deliveries]


# ==================== 统计分析 ====================

@router.get("/stats")
async def get_statistics(tenant=Depends(require_tenant)):
    """获取ERP统计信息"""
    return erp_manager.get_statistics(tenant.id)
