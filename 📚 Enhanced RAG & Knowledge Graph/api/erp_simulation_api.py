"""
ERP试算功能API
支持各种业务场景的试算和预测
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

router = APIRouter(prefix="/api/v5/erp/simulation", tags=["ERP试算功能"])


# ==================== 数据模型 ====================

class SimulationRequest(BaseModel):
    """试算请求模型"""
    scenario: str  # 试算场景
    parameters: Dict[str, Any]  # 输入参数
    erp_data_source: Optional[str] = None  # ERP数据源


# ==================== API端点 ====================

@router.post("/production/daily-output")
async def simulate_daily_output(target_weekly: int, working_days: int = 5):
    """
    试算：达到周目标需要的每日交付量
    
    Args:
        target_weekly: 周目标产量
        working_days: 工作天数
        
    Returns:
        每日所需产量及可行性分析
    """
    daily_required = math.ceil(target_weekly / working_days)
    
    # 从ERP获取历史产能数据（模拟）
    historical_capacity = {
        "avg_daily": 850,
        "max_daily": 1200,
        "min_daily": 600,
        "std_dev": 120
    }
    
    # 可行性分析
    feasibility = "可行" if daily_required <= historical_capacity["avg_daily"] * 1.2 else "困难"
    if daily_required > historical_capacity["max_daily"]:
        feasibility = "不可行"
    
    # 建议
    recommendations = []
    if daily_required > historical_capacity["avg_daily"]:
        recommendations.append(f"需要提升产能{((daily_required/historical_capacity['avg_daily']-1)*100):.1f}%")
        recommendations.append("考虑加班或增加人手")
        recommendations.append("优化生产流程")
    
    return {
        "success": True,
        "scenario": "每日产量试算",
        "inputs": {
            "weekly_target": target_weekly,
            "working_days": working_days
        },
        "results": {
            "daily_required": daily_required,
            "feasibility": feasibility,
            "feasibility_score": min(100, int(historical_capacity["avg_daily"] / daily_required * 100)),
            "capacity_utilization": f"{(daily_required/historical_capacity['avg_daily']*100):.1f}%"
        },
        "historical_data": historical_capacity,
        "recommendations": recommendations,
        "calculated_at": datetime.now().isoformat()
    }


@router.post("/cost/break-even")
async def simulate_break_even(
    fixed_cost: float,
    variable_cost_per_unit: float,
    selling_price: float
):
    """
    试算：盈亏平衡点分析
    
    Args:
        fixed_cost: 固定成本
        variable_cost_per_unit: 单位变动成本
        selling_price: 销售单价
        
    Returns:
        盈亏平衡点及分析
    """
    if selling_price <= variable_cost_per_unit:
        return {
            "success": False,
            "error": "销售价格必须大于单位变动成本"
        }
    
    # 盈亏平衡点计算
    break_even_quantity = math.ceil(fixed_cost / (selling_price - variable_cost_per_unit))
    break_even_revenue = break_even_quantity * selling_price
    
    # 边际贡献
    contribution_margin = selling_price - variable_cost_per_unit
    contribution_rate = contribution_margin / selling_price * 100
    
    # 敏感性分析
    scenarios = []
    for price_change in [-10, -5, 0, 5, 10]:
        new_price = selling_price * (1 + price_change/100)
        new_be = math.ceil(fixed_cost / (new_price - variable_cost_per_unit))
        scenarios.append({
            "price_change": f"{price_change:+d}%",
            "new_price": round(new_price, 2),
            "break_even_qty": new_be,
            "change": f"{((new_be - break_even_quantity)/break_even_quantity*100):+.1f}%"
        })
    
    return {
        "success": True,
        "scenario": "盈亏平衡分析",
        "inputs": {
            "fixed_cost": fixed_cost,
            "variable_cost": variable_cost_per_unit,
            "selling_price": selling_price
        },
        "results": {
            "break_even_quantity": break_even_quantity,
            "break_even_revenue": round(break_even_revenue, 2),
            "contribution_margin": round(contribution_margin, 2),
            "contribution_rate": f"{contribution_rate:.1f}%"
        },
        "sensitivity_analysis": scenarios,
        "recommendations": [
            f"至少需要销售{break_even_quantity}件才能不亏损",
            f"每多卖1件，利润增加¥{contribution_margin:.2f}",
            "建议关注价格和成本的变化对盈亏的影响"
        ]
    }


@router.post("/inventory/safety-stock")
async def simulate_safety_stock(
    avg_daily_demand: float,
    lead_time_days: int,
    service_level: float = 0.95
):
    """
    试算：安全库存计算
    
    Args:
        avg_daily_demand: 平均日需求
        lead_time_days: 交货提前期（天）
        service_level: 服务水平（如0.95表示95%）
        
    Returns:
        安全库存建议
    """
    import math
    
    # Z值（正态分布）
    z_scores = {
        0.90: 1.28,
        0.95: 1.65,
        0.99: 2.33
    }
    z = z_scores.get(service_level, 1.65)
    
    # 假设需求标准差为平均需求的20%
    demand_std = avg_daily_demand * 0.2
    
    # 安全库存 = Z × σ × √L
    safety_stock = math.ceil(z * demand_std * math.sqrt(lead_time_days))
    reorder_point = math.ceil(avg_daily_demand * lead_time_days + safety_stock)
    
    return {
        "success": True,
        "scenario": "安全库存计算",
        "inputs": {
            "avg_daily_demand": avg_daily_demand,
            "lead_time_days": lead_time_days,
            "service_level": f"{service_level*100}%"
        },
        "results": {
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "avg_inventory": reorder_point + safety_stock / 2,
            "stockout_risk": f"{(1-service_level)*100:.1f}%"
        },
        "recommendations": [
            f"建议安全库存保持{safety_stock}件",
            f"当库存低于{reorder_point}件时补货",
            f"可满足{service_level*100}%的订单需求"
        ]
    }


@router.post("/capacity/requirement")
async def simulate_capacity_requirement(
    monthly_orders: int,
    production_time_per_unit: float,
    working_hours_per_day: int = 8,
    working_days_per_month: int = 22
):
    """
    试算：产能需求分析
    
    Args:
        monthly_orders: 月订单量
        production_time_per_unit: 单件生产时间（小时）
        working_hours_per_day: 每日工时
        working_days_per_month: 每月工作天数
        
    Returns:
        产能需求和资源配置建议
    """
    # 总所需工时
    total_hours_required = monthly_orders * production_time_per_unit
    
    # 可用总工时
    total_hours_available = working_hours_per_day * working_days_per_month
    
    # 所需人数
    workers_required = math.ceil(total_hours_required / total_hours_available)
    
    # 设备需求
    equipment_required = math.ceil(workers_required / 2)  # 假设2人共用1台设备
    
    # 产能利用率
    utilization = total_hours_required / (total_hours_available * workers_required) * 100
    
    return {
        "success": True,
        "scenario": "产能需求分析",
        "inputs": {
            "monthly_orders": monthly_orders,
            "time_per_unit": production_time_per_unit,
            "working_hours_day": working_hours_per_day,
            "working_days_month": working_days_per_month
        },
        "results": {
            "total_hours_required": round(total_hours_required, 1),
            "total_hours_available": total_hours_available,
            "workers_required": workers_required,
            "equipment_required": equipment_required,
            "utilization_rate": f"{utilization:.1f}%",
            "buffer_capacity": f"{(100-utilization):.1f}%"
        },
        "recommendations": [
            f"建议配置{workers_required}名工人",
            f"建议配置{equipment_required}台设备",
            f"预留{100-utilization:.1f}%的产能缓冲" if utilization < 90 else "产能紧张，考虑扩产"
        ]
    }


@router.post("/financial/pricing")
async def simulate_pricing(
    cost: float,
    target_margin: float,
    market_price_range: Optional[Dict[str, float]] = None
):
    """
    试算：定价模拟
    
    Args:
        cost: 成本
        target_margin: 目标利润率（如0.25表示25%）
        market_price_range: 市场价格区间
        
    Returns:
        定价建议和分析
    """
    # 基于成本加成定价
    cost_plus_price = cost / (1 - target_margin)
    
    # 不同利润率下的价格
    pricing_options = []
    for margin in [0.15, 0.20, 0.25, 0.30, 0.35]:
        price = cost / (1 - margin)
        pricing_options.append({
            "margin": f"{margin*100:.0f}%",
            "price": round(price, 2),
            "profit_per_unit": round(price - cost, 2),
            "competitiveness": "高" if margin < 0.25 else "中" if margin < 0.30 else "低"
        })
    
    return {
        "success": True,
        "scenario": "定价模拟",
        "inputs": {
            "cost": cost,
            "target_margin": f"{target_margin*100}%"
        },
        "results": {
            "recommended_price": round(cost_plus_price, 2),
            "break_even_price": cost,
            "profit_per_unit": round(cost_plus_price - cost, 2)
        },
        "pricing_options": pricing_options,
        "market_analysis": {
            "market_low": market_price_range.get("low", cost * 1.1) if market_price_range else cost * 1.1,
            "market_high": market_price_range.get("high", cost * 1.5) if market_price_range else cost * 1.5,
            "recommended_position": "适中偏上"
        }
    }


@router.get("/scenarios")
async def get_simulation_scenarios():
    """获取所有可用的试算场景"""
    scenarios = [
        {
            "id": "daily_output",
            "name": "每日产量试算",
            "description": "根据周目标计算每日所需产量",
            "category": "生产"
        },
        {
            "id": "break_even",
            "name": "盈亏平衡分析",
            "description": "计算盈亏平衡点和边际贡献",
            "category": "财务"
        },
        {
            "id": "safety_stock",
            "name": "安全库存计算",
            "description": "基于需求和交期计算安全库存",
            "category": "库存"
        },
        {
            "id": "capacity",
            "name": "产能需求分析",
            "description": "计算所需人力和设备资源",
            "category": "生产"
        },
        {
            "id": "pricing",
            "name": "定价模拟",
            "description": "基于成本和市场的定价建议",
            "category": "财务"
        }
    ]
    
    return {
        "success": True,
        "scenarios": scenarios,
        "count": len(scenarios)
    }


@router.get("/health")
async def simulation_health():
    """试算系统健康检查"""
    return {
        "status": "healthy",
        "service": "erp_simulation",
        "version": "5.1.0",
        "available_scenarios": 5,
        "features": [
            "产量试算",
            "成本试算",
            "库存试算",
            "产能试算",
            "定价试算"
        ]
    }


if __name__ == "__main__":
    print("✅ ERP试算功能API已加载")
    print("📋 支持场景:")
    print("  • 每日产量试算")
    print("  • 盈亏平衡分析")
    print("  • 安全库存计算")
    print("  • 产能需求分析")
    print("  • 定价模拟")


