"""
试算功能API
提供各种试算计算功能
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from core.trial_balance import TrialBalanceCalculator
from core.trial_history import TrialHistoryManager
from core.database import get_db

router = APIRouter(prefix="/api/trial-balance", tags=["Trial Balance API"])

# 初始化试算器
calculator = TrialBalanceCalculator()


class DailyDeliveryRequest(BaseModel):
    """每日交付量试算请求"""
    target_weekly_revenue: float
    product_id: Optional[int] = None
    start_date: Optional[str] = None


class CustomTrialRequest(BaseModel):
    """自定义试算请求"""
    calculation_type: str  # daily_delivery, production_capacity, cost_breakdown
    target_value: float
    parameters: Dict[str, Any] = {}


@router.post("/daily-delivery")
async def calculate_daily_delivery(request: DailyDeliveryRequest):
    """
    试算达到周目标需要的每日交付量
    
    Args:
        request: 试算请求
        
    Returns:
        试算结果
    """
    try:
        result = await calculator.calculate_daily_delivery(
            target_weekly_revenue=request.target_weekly_revenue,
            product_id=request.product_id,
            start_date=request.start_date
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试算失败: {str(e)}")


@router.post("/custom")
async def custom_trial_calculation(
    request: CustomTrialRequest,
    save_history: bool = False,
    created_by: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    自定义试算
    
    Args:
        request: 试算请求
        save_history: 是否保存历史记录
        created_by: 创建人
        notes: 备注
        db: 数据库会话
        
    Returns:
        试算结果
    """
    try:
        result = await calculator.custom_trial_calculation(
            calculation_type=request.calculation_type,
            target_value=request.target_value,
            parameters=request.parameters
        )
        
        # 保存历史记录
        if save_history and result.get("success"):
            history_manager = TrialHistoryManager(db)
            await history_manager.save_trial(
                calculation_type=request.calculation_type,
                target_value=request.target_value,
                parameters=request.parameters,
                result=result,
                created_by=created_by,
                notes=notes
            )
        
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"试算失败: {str(e)}")


@router.get("/history")
async def get_trial_history(
    calculation_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取试算历史记录
    
    Args:
        calculation_type: 计算类型（可选）
        limit: 返回数量限制
        db: 数据库会话
        
    Returns:
        历史记录列表
    """
    try:
        history_manager = TrialHistoryManager(db)
        history = await history_manager.get_trial_history(
            calculation_type=calculation_type,
            limit=limit
        )
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.post("/compare")
async def compare_trials(
    trial_ids: List[int] = Body(...),
    db: Session = Depends(get_db)
):
    """
    对比多个试算结果
    
    Args:
        trial_ids: 试算记录ID列表
        db: 数据库会话
        
    Returns:
        对比结果
    """
    try:
        history_manager = TrialHistoryManager(db)
        comparison = await history_manager.compare_trials(trial_ids)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比失败: {str(e)}")


@router.post("/inventory-requirement")
async def calculate_inventory_requirement(
    target_production: float = Body(...),
    parameters: Dict[str, Any] = Body(...)
):
    """
    计算物料需求
    
    Args:
        target_production: 目标产量
        parameters: 参数
        
    Returns:
        物料需求计算结果
    """
    try:
        result = await calculator.calculate_inventory_requirement(
            target_production=target_production,
            parameters=parameters
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/delivery-schedule")
async def calculate_delivery_schedule(
    order_list: List[Dict[str, Any]] = Body(...),
    parameters: Dict[str, Any] = Body(...)
):
    """
    计算交付计划
    
    Args:
        order_list: 订单列表
        parameters: 参数
        
    Returns:
        交付计划计算结果
    """
    try:
        result = await calculator.calculate_delivery_schedule(
            order_list=order_list,
            parameters=parameters
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/calculation-types")
async def get_calculation_types():
    """
    获取支持的试算类型
    
    Returns:
        试算类型列表
    """
    return {
        "success": True,
        "types": [
            {
                "type": "daily_delivery",
                "name": "每日交付量试算",
                "description": "计算达到周目标需要的每日交付量",
                "required_params": ["target_weekly_revenue"],
                "optional_params": ["product_id", "start_date"]
            },
            {
                "type": "production_capacity",
                "name": "生产产能试算",
                "description": "计算生产产能和所需设备数量",
                "required_params": ["target_value"],
                "optional_params": ["equipment_count", "single_equipment_capacity", "working_hours_per_day", "working_days_per_month"]
            },
            {
                "type": "cost_breakdown",
                "name": "成本分解试算",
                "description": "计算成本分解和单位成本",
                "required_params": ["target_value"],
                "optional_params": ["material_cost_ratio", "labor_cost_ratio", "overhead_cost_ratio", "quantity"]
            },
            {
                "type": "inventory_requirement",
                "name": "物料需求试算",
                "description": "计算生产所需的物料需求和安全库存",
                "required_params": ["target_production", "material_list"],
                "optional_params": ["safety_stock_ratio", "lead_time_days"]
            },
            {
                "type": "delivery_schedule",
                "name": "交付计划试算",
                "description": "计算订单交付计划和产能分配",
                "required_params": ["order_list"],
                "optional_params": ["daily_capacity", "working_days_per_week"]
            }
        ]
    }
