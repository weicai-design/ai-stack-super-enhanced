"""
ERP数据集成API
实现ERP与运营管理、财务管理的数据打通
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from sqlalchemy.orm import Session

from core.database import get_db
from core.data_integration import DataIntegrationService

router = APIRouter(prefix="/api/integration", tags=["Data Integration API"])


class SyncRequest(BaseModel):
    """同步请求模型"""
    sync_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_create: bool = False  # 是否自动创建目标数据


@router.post("/sync/operations")
async def sync_to_operations(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    同步ERP数据到运营管理模块
    
    Args:
        request: 同步请求
        db: 数据库会话
        
    Returns:
        同步结果
    """
    try:
        service = DataIntegrationService(db)
        
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date).date()
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date).date()
        
        result = await service.sync_to_operations(
            sync_type=request.sync_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/sync/finance")
async def sync_to_finance(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    同步ERP数据到财务管理模块
    
    Args:
        request: 同步请求
        db: 数据库会话
        
    Returns:
        同步结果
    """
    try:
        service = DataIntegrationService(db)
        
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date).date()
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date).date()
        
        result = await service.sync_to_finance(
            sync_type=request.sync_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # 如果设置了自动创建，将数据写入财务表
        if request.auto_create and result.get("success"):
            from core.database_models import FinancialData, FinancialCategory, PeriodType
            
            created_count = 0
            for item in result.get("data", []):
                try:
                    financial_data = FinancialData(
                        date=datetime.fromisoformat(item["date"]).date() if item.get("date") else date.today(),
                        period_type=PeriodType.DAILY.value,
                        category=item.get("category", FinancialCategory.REVENUE.value),
                        subcategory=item.get("subcategory"),
                        amount=item.get("amount", 0),
                        description=item.get("description"),
                        source_document=item.get("source_no")
                    )
                    db.add(financial_data)
                    created_count += 1
                except Exception as e:
                    continue
            
            if created_count > 0:
                db.commit()
                result["auto_created"] = created_count
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/consistency/check")
async def check_data_consistency(
    check_type: str = Query("all", description="检查类型: all/orders/finance/processes"),
    db: Session = Depends(get_db)
):
    """
    检查数据一致性
    
    Args:
        check_type: 检查类型
        db: 数据库会话
        
    Returns:
        一致性检查结果
    """
    try:
        service = DataIntegrationService(db)
        result = await service.check_data_consistency(check_type=check_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.get("/sync/types")
async def get_sync_types():
    """
    获取支持的同步类型
    
    Returns:
        同步类型列表
    """
    return {
        "success": True,
        "operations_sync_types": [
            {
                "type": "orders",
                "name": "订单数据",
                "description": "同步订单数据到运营管理模块"
            },
            {
                "type": "processes",
                "name": "流程数据",
                "description": "同步流程数据到运营管理模块"
            },
            {
                "type": "production",
                "name": "生产数据",
                "description": "同步生产数据到运营管理模块"
            },
            {
                "type": "inventory",
                "name": "库存数据",
                "description": "同步库存数据到运营管理模块"
            }
        ],
        "finance_sync_types": [
            {
                "type": "revenue",
                "name": "收入数据",
                "description": "同步收入数据到财务管理模块"
            },
            {
                "type": "expense",
                "name": "支出数据",
                "description": "同步支出数据到财务管理模块"
            },
            {
                "type": "payment",
                "name": "回款数据",
                "description": "同步回款数据到财务管理模块"
            },
            {
                "type": "invoice",
                "name": "发票数据",
                "description": "同步发票数据到财务管理模块"
            }
        ]
    }


@router.post("/sync/batch/operations")
async def batch_sync_to_operations(
    sync_types: List[str] = Body(...),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    批量同步ERP数据到运营管理模块
    
    Args:
        sync_types: 同步类型列表
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        批量同步结果
    """
    try:
        service = DataIntegrationService(db)
        
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date).date()
        if end_date:
            end = datetime.fromisoformat(end_date).date()
        
        result = await service.batch_sync_to_operations(
            sync_types=sync_types,
            start_date=start,
            end_date=end
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量同步失败: {str(e)}")


@router.post("/sync/batch/finance")
async def batch_sync_to_finance(
    sync_types: List[str] = Body(...),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    auto_create: bool = False,
    db: Session = Depends(get_db)
):
    """
    批量同步ERP数据到财务管理模块
    
    Args:
        sync_types: 同步类型列表
        start_date: 开始日期
        end_date: 结束日期
        auto_create: 是否自动创建财务数据
        db: 数据库会话
        
    Returns:
        批量同步结果
    """
    try:
        service = DataIntegrationService(db)
        
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date).date()
        if end_date:
            end = datetime.fromisoformat(end_date).date()
        
        result = await service.batch_sync_to_finance(
            sync_types=sync_types,
            start_date=start,
            end_date=end,
            auto_create=auto_create
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量同步失败: {str(e)}")


@router.get("/sync/history")
async def get_sync_history(
    limit: int = Query(50, description="返回记录数限制"),
    db: Session = Depends(get_db)
):
    """
    获取同步历史记录
    
    Args:
        limit: 返回记录数限制
        db: 数据库会话
        
    Returns:
        同步历史记录列表
    """
    try:
        service = DataIntegrationService(db)
        result = await service.get_sync_history(limit=limit)
        return {"success": True, "history": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/sync/statistics")
async def get_sync_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取数据同步统计信息
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        同步统计信息
    """
    try:
        service = DataIntegrationService(db)
        
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date).date()
        if end_date:
            end = datetime.fromisoformat(end_date).date()
        
        result = await service.get_sync_statistics(start_date=start, end_date=end)
        return {"success": True, "statistics": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/status")
async def get_integration_status(db: Session = Depends(get_db)):
    """
    获取数据集成状态
    
    Returns:
        集成状态信息
    """
    try:
        from core.database_models import Order, FinancialData, ProcessInstance
        
        # 统计各模块数据量
        order_count = db.query(Order).count()
        finance_count = db.query(FinancialData).count()
        process_count = db.query(ProcessInstance).count()
        
        # 获取同步统计
        service = DataIntegrationService(db)
        sync_stats = await service.get_sync_statistics()
        
        return {
            "success": True,
            "data_counts": {
                "orders": order_count,
                "financial_data": finance_count,
                "processes": process_count
            },
            "sync_statistics": sync_stats,
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")

