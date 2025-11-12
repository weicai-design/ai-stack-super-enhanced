"""
ERP V5 增强API - 使用真实业务管理器
完全连接前后端，实现真实数据流转
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v5/erp/real", tags=["ERP-V5-Enhanced"])


# ==================== 数据模型 ====================

class CustomerCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    level: str = "normal"


class OrderCreate(BaseModel):
    customer_id: str
    items: List[Dict[str, Any]]
    delivery_date: Optional[str] = None
    notes: Optional[str] = None


# ==================== 客户管理API（真实实现）====================

@router.post("/customers/create")
async def create_customer(customer: CustomerCreate):
    """创建客户（真实数据库操作）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.create_customer(customer.dict())
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/list")
async def list_customers(
    skip: int = 0,
    limit: int = 20,
    level: Optional[str] = None
):
    """获取客户列表（真实数据库查询）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.list_customers(skip=skip, limit=limit, level=level)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """获取客户详情"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.get_customer(customer_id)
        
        if result:
            return {"success": True, "customer": result}
        else:
            raise HTTPException(status_code=404, detail="客户不存在")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 订单管理API（真实实现）====================

@router.post("/orders/create")
async def create_order(order: OrderCreate):
    """创建订单（真实业务逻辑）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.create_order(order.dict())
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/list")
async def list_orders(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    customer_id: Optional[str] = None
):
    """获取订单列表（真实数据库查询）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.list_orders(
            skip=skip,
            limit=limit,
            status=status,
            customer_id=customer_id
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """获取订单详情"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.get_order(order_id)
        
        if result:
            return {"success": True, "order": result}
        else:
            raise HTTPException(status_code=404, detail="订单不存在")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, new_status: str):
    """更新订单状态"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.update_order_status(order_id, new_status)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 8维度分析API（真实计算）====================

@router.get("/analysis/8d/{process_id}")
async def analyze_8_dimensions(process_id: str):
    """8维度综合分析（真实数据计算）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.analyze_8_dimensions(process_id)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 财务分析API（真实计算）====================

@router.get("/finance/profitability")
async def analyze_profitability(period: str = "month"):
    """盈亏分析（真实数据计算）"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        result = await erp.analyze_profitability(period)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计API ====================

@router.get("/statistics")
async def get_statistics():
    """获取ERP统计数据"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        stats = await erp.get_statistics()
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """ERP系统健康检查"""
    try:
        from business.erp_manager import get_erp_manager
        erp = get_erp_manager()
        
        stats = await erp.get_statistics()
        
        return {
            "status": "healthy",
            "module": "ERP",
            "version": "5.5",
            "data_source": "real_database",
            "statistics": stats,
            "features": {
                "customer_management": True,
                "order_management": True,
                "project_management": True,
                "8d_analysis": True,
                "finance_analysis": True
            }
        }
    
    except Exception as e:
        return {
            "status": "degraded",
            "module": "ERP",
            "error": str(e)
        }


if __name__ == "__main__":
    print("✅ ERP V5增强API已加载")
    print("📋 真实功能:")
    print("  • 客户管理（CRUD）")
    print("  • 订单管理（全流程）")
    print("  • 8维度分析（真实计算）")
    print("  • 财务分析（真实计算）")
    print("  • 数据统计")
    print("\n💡 所有API都使用真实的业务管理器！")


