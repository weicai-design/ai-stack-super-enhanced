"""
Analytics API
经营分析API

根据需求2.1.2：经营分析
功能：
1. 开源分析（需求2.1.2.1）
2. 成本分析（需求2.1.2.2）
3. 产出效益分析（需求2.1.2.3）
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.database import get_db
from core.database_models import (
    Order,
    OrderItem,
    Customer,
    FinancialData,
    CostCategory,
    PeriodType,
)

router = APIRouter(prefix="/analytics", tags=["Analytics API"])


# ============ Pydantic Models ============

class RevenueAnalysisResponse(BaseModel):
    """开源分析响应模型"""
    period_type: str
    start_date: date
    end_date: date
    total_revenue: float
    customer_category_stats: Dict[str, float]  # 按客户类别统计
    order_stats: Dict[str, Any]  # 订单统计
    order_detail_summary: List[Dict[str, Any]]  # 订单明细汇总
    time_dimension_data: Dict[str, List[Dict[str, Any]]]  # 多时间维度数据


class CostAnalysisResponse(BaseModel):
    """成本分析响应模型"""
    period_type: str
    start_date: date
    end_date: date
    total_cost: float
    cost_by_category: Dict[str, float]  # 按成本类别统计
    cost_reasonableness: Dict[str, Any]  # 费用合理性分析
    break_even_analysis: Dict[str, Any]  # 盈亏平衡分析


class EfficiencyAnalysisResponse(BaseModel):
    """产出效益分析响应模型"""
    period_type: str
    start_date: date
    end_date: date
    input_output_ratio: float  # 投入产出比
    efficiency_metrics: Dict[str, float]  # 效益效率指标
    analysis: Dict[str, Any]  # 详细分析


# ============ API Endpoints ============

@router.get("/revenue", response_model=RevenueAnalysisResponse)
async def revenue_analysis(
    period_type: str = Query(PeriodType.MONTHLY, description="周期类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    customer_category: Optional[str] = Query(None, description="客户类别过滤"),
    db: Session = Depends(get_db),
):
    """
    开源分析（需求2.1.2.1）
    
    功能：
    - 客户类别分析
    - 订单量分析
    - 订单明细分类汇总
    - 多时间维度分析（日/周/月/季/年/三年）
    - 行业对比分析（可扩展）
    
    Args:
        period_type: 周期类型
        start_date: 开始日期
        end_date: 结束日期
        customer_category: 客户类别过滤
        db: 数据库会话
        
    Returns:
        开源分析结果
    """
    try:
        # 确定日期范围
        if not start_date or not end_date:
            today = date.today()
            if period_type == PeriodType.DAILY:
                start_date = today
                end_date = today
            elif period_type == PeriodType.WEEKLY:
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period_type == PeriodType.MONTHLY:
                start_date = today.replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            elif period_type == PeriodType.QUARTERLY:
                quarter = (today.month - 1) // 3
                start_date = date(today.year, quarter * 3 + 1, 1)
                end_date = (start_date + timedelta(days=93)).replace(day=1) - timedelta(days=1)
            elif period_type == PeriodType.YEARLY:
                start_date = date(today.year, 1, 1)
                end_date = date(today.year, 12, 31)

        # 查询订单
        query = db.query(Order).filter(
            and_(
                Order.order_date >= start_date,
                Order.order_date <= end_date,
            )
        )

        # 客户类别过滤
        if customer_category:
            query = query.join(Customer).filter(Customer.category == customer_category)

        orders = query.all()

        # 计算总营收
        total_revenue = sum(float(order.total_amount) for order in orders)

        # 按客户类别统计
        customer_category_stats = {}
        for order in orders:
            if order.customer and order.customer.category:
                cat = order.customer.category
                customer_category_stats[cat] = customer_category_stats.get(cat, 0.0) + float(order.total_amount)

        # 订单统计
        order_stats = {
            "total_orders": len(orders),
            "average_order_amount": total_revenue / len(orders) if orders else 0,
            "max_order_amount": max((float(o.total_amount) for o in orders), default=0),
            "min_order_amount": min((float(o.total_amount) for o in orders), default=0),
        }

        # 订单明细分类汇总
        order_detail_summary = []
        for order in orders:
            for item in order.items:
                detail = {
                    "order_number": order.order_number,
                    "product_code": item.product_code,
                    "product_name": item.product_name,
                    "quantity": float(item.quantity),
                    "total_price": float(item.total_price),
                }
                order_detail_summary.append(detail)

        # 按产品汇总
        product_summary = {}
        for detail in order_detail_summary:
            code = detail["product_code"] or detail["product_name"]
            if code not in product_summary:
                product_summary[code] = {
                    "product_code": code,
                    "product_name": detail["product_name"],
                    "total_quantity": 0,
                    "total_amount": 0,
                    "order_count": 0,
                }
            product_summary[code]["total_quantity"] += detail["quantity"]
            product_summary[code]["total_amount"] += detail["total_price"]
            product_summary[code]["order_count"] += 1

        order_detail_summary = list(product_summary.values())

        # 多时间维度数据（简化实现）
        time_dimension_data = {
            "daily": _get_daily_revenue(orders, start_date, end_date),
            "weekly": _get_weekly_revenue(orders, start_date, end_date),
            "monthly": _get_monthly_revenue(orders, start_date, end_date),
        }

        return RevenueAnalysisResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            total_revenue=total_revenue,
            customer_category_stats=customer_category_stats,
            order_stats=order_stats,
            order_detail_summary=order_detail_summary,
            time_dimension_data=time_dimension_data,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开源分析失败: {str(e)}")


@router.get("/cost", response_model=CostAnalysisResponse)
async def cost_analysis(
    period_type: str = Query(PeriodType.MONTHLY, description="周期类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
):
    """
    成本分析（需求2.1.2.2）
    
    功能：
    - 各类费用分析（销售、财务、管理、生产、制造）
    - 费用合理性分析
    - 盈亏平衡分析
    
    Args:
        period_type: 周期类型
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        成本分析结果
    """
    try:
        # 确定日期范围（同上）
        if not start_date or not end_date:
            today = date.today()
            if period_type == PeriodType.MONTHLY:
                start_date = today.replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            else:
                # 其他周期类型的日期计算...
                start_date = today.replace(day=1)
                end_date = today

        # 查询成本数据（财务数据表中的expense类别）
        cost_query = db.query(FinancialData).filter(
            and_(
                FinancialData.date >= start_date,
                FinancialData.date <= end_date,
                FinancialData.category == "expense",
            )
        )

        cost_data = cost_query.all()

        # 计算总成本
        total_cost = sum(float(item.amount) for item in cost_data)

        # 按成本类别统计
        cost_by_category = {}
        for item in cost_data:
            # 从subcategory或metadata中获取成本类别
            cost_cat = item.subcategory or item.extra_metadata.get("cost_category", "other") if item.extra_metadata else "other"
            cost_by_category[cost_cat] = cost_by_category.get(cost_cat, 0.0) + float(item.amount)

        # 费用合理性分析（简化实现）
        cost_reasonableness = {
            "total_cost": total_cost,
            "cost_distribution": cost_by_category,
            "recommendations": [],  # 可以添加合理性建议
        }

        # 盈亏平衡分析
        # 查询同期收入
        revenue_query = db.query(FinancialData).filter(
            and_(
                FinancialData.date >= start_date,
                FinancialData.date <= end_date,
                FinancialData.category == "revenue",
            )
        )
        revenue_data = revenue_query.all()
        total_revenue = sum(float(item.amount) for item in revenue_data)

        break_even_analysis = {
            "revenue": total_revenue,
            "cost": total_cost,
            "profit": total_revenue - total_cost,
            "break_even_point": total_cost,  # 盈亏平衡点
            "profit_margin": ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0,
        }

        return CostAnalysisResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            total_cost=total_cost,
            cost_by_category=cost_by_category,
            cost_reasonableness=cost_reasonableness,
            break_even_analysis=break_even_analysis,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"成本分析失败: {str(e)}")


@router.get("/efficiency", response_model=EfficiencyAnalysisResponse)
async def efficiency_analysis(
    period_type: str = Query(PeriodType.MONTHLY, description="周期类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
):
    """
    产出效益分析（需求2.1.2.3）
    
    功能：
    - 投入产出分析
    - 效益效率分析
    
    Args:
        period_type: 周期类型
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        产出效益分析结果
    """
    try:
        # 确定日期范围
        if not start_date or not end_date:
            today = date.today()
            if period_type == PeriodType.MONTHLY:
                start_date = today.replace(day=1)
                end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # 查询投入（investment）
        investment_query = db.query(FinancialData).filter(
            and_(
                FinancialData.date >= start_date,
                FinancialData.date <= end_date,
                FinancialData.category == "investment",
            )
        )
        investment_data = investment_query.all()
        total_investment = sum(float(item.amount) for item in investment_data)

        # 查询产出（revenue）
        output_query = db.query(FinancialData).filter(
            and_(
                FinancialData.date >= start_date,
                FinancialData.date <= end_date,
                FinancialData.category == "revenue",
            )
        )
        output_data = output_query.all()
        total_output = sum(float(item.amount) for item in output_data)

        # 计算投入产出比
        input_output_ratio = total_output / total_investment if total_investment > 0 else 0

        # 效益效率指标
        efficiency_metrics = {
            "investment": total_investment,
            "output": total_output,
            "input_output_ratio": input_output_ratio,
            "roi": ((total_output - total_investment) / total_investment * 100) if total_investment > 0 else 0,
        }

        # 详细分析
        analysis = {
            "investment_breakdown": _get_investment_breakdown(investment_data),
            "output_breakdown": _get_output_breakdown(output_data),
            "trend_analysis": "待实现",  # 趋势分析
        }

        return EfficiencyAnalysisResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            input_output_ratio=input_output_ratio,
            efficiency_metrics=efficiency_metrics,
            analysis=analysis,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"产出效益分析失败: {str(e)}")


# ============ 辅助函数 ============

def _get_daily_revenue(orders: List[Order], start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """获取每日营收数据"""
    daily = {}
    current = start_date
    while current <= end_date:
        daily[current.isoformat()] = 0.0
        current += timedelta(days=1)

    for order in orders:
        day_key = order.order_date.isoformat()
        if day_key in daily:
            daily[day_key] += float(order.total_amount)

    return [{"date": k, "revenue": v} for k, v in sorted(daily.items())]


def _get_weekly_revenue(orders: List[Order], start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """获取每周营收数据"""
    weekly = {}
    for order in orders:
        week_start = order.order_date - timedelta(days=order.order_date.weekday())
        week_key = week_start.isoformat()
        weekly[week_key] = weekly.get(week_key, 0.0) + float(order.total_amount)

    return [{"week": k, "revenue": v} for k, v in sorted(weekly.items())]


def _get_monthly_revenue(orders: List[Order], start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """获取每月营收数据"""
    monthly = {}
    for order in orders:
        month_key = order.order_date.replace(day=1).isoformat()
        monthly[month_key] = monthly.get(month_key, 0.0) + float(order.total_amount)

    return [{"month": k, "revenue": v} for k, v in sorted(monthly.items())]


def _get_investment_breakdown(investment_data: List[FinancialData]) -> Dict[str, float]:
    """获取投入明细"""
    breakdown = {}
    for item in investment_data:
        subcat = item.subcategory or "其他"
        breakdown[subcat] = breakdown.get(subcat, 0.0) + float(item.amount)
    return breakdown


def _get_output_breakdown(output_data: List[FinancialData]) -> Dict[str, float]:
    """获取产出明细"""
    breakdown = {}
    for item in output_data:
        subcat = item.subcategory or "其他"
        breakdown[subcat] = breakdown.get(subcat, 0.0) + float(item.amount)
    return breakdown

