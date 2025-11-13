"""
Finance API
财务API接口

根据需求2.1.1：财务看板
功能：
1. 财务数据导入导出
2. 日/周/月/季/年财务看板
3. 财务数据查询统计
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.database_models import (
    FinancialData,
    FinancialReport,
    FinancialCategory,
    PeriodType,
)
from core.database import get_db
from .data_listener_api import data_listener

router = APIRouter(prefix="/finance", tags=["Finance API"])


# ============ Pydantic Models ============

class FinancialDataInput(BaseModel):
    """财务数据输入模型"""
    date: date
    period_type: str = PeriodType.DAILY
    category: str  # FinancialCategory
    subcategory: Optional[str] = None
    amount: float
    description: Optional[str] = None
    source_document: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FinancialDataOutput(BaseModel):
    """财务数据输出模型"""
    id: int
    date: date
    period_type: str
    category: str
    subcategory: Optional[str]
    amount: float
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """财务看板响应模型"""
    period_type: str
    start_date: date
    end_date: date
    summary: Dict[str, float]  # 各类别汇总
    revenue: float
    expense: float
    profit: float
    assets: float
    liabilities: float
    investment: float
    daily_data: List[Dict[str, Any]]


# ============ API Endpoints ============

@router.post("/data", response_model=FinancialDataOutput)
async def create_financial_data(
    data: FinancialDataInput,
    db: Session = Depends(get_db),
):
    """
    创建财务数据
    
    Args:
        data: 财务数据输入
        db: 数据库会话
        
    Returns:
        创建的财务数据
    """
    try:
        financial_data = FinancialData(
            date=data.date,
            period_type=data.period_type,
            category=data.category,
            subcategory=data.subcategory,
            amount=data.amount,
            description=data.description,
            source_document=data.source_document,
            extra_metadata=data.metadata,
        )
        
        db.add(financial_data)
        db.commit()
        db.refresh(financial_data)
        
        # 自动发布财务数据创建事件
        if data_listener:
            try:
                import asyncio
                financial_dict = {
                    "id": financial_data.id,
                    "date": financial_data.date.isoformat() if financial_data.date else None,
                    "period_type": financial_data.period_type,
                    "category": financial_data.category,
                    "subcategory": financial_data.subcategory,
                    "amount": float(financial_data.amount),
                    "description": financial_data.description,
                    "source_document": financial_data.source_document
                }
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            data_listener.on_financial_data_created(
                                str(financial_data.id), financial_dict
                            )
                        )
                    else:
                        loop.run_until_complete(
                            data_listener.on_financial_data_created(
                                str(financial_data.id), financial_dict
                            )
                        )
                except RuntimeError:
                    asyncio.run(
                        data_listener.on_financial_data_created(
                            str(financial_data.id), financial_dict
                        )
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"财务数据创建事件发布失败: {e}")
        
        return financial_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建财务数据失败: {str(e)}")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_finance_dashboard(
    period_type: str = Query(PeriodType.MONTHLY, description="周期类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
):
    """
    获取财务看板数据（需求2.1.1）
    
    支持日/周/月/季/年财务看板
    
    Args:
        period_type: 周期类型（daily, weekly, monthly, quarterly, yearly）
        start_date: 开始日期
        end_date: 结束日期
        db: 数据库会话
        
    Returns:
        财务看板数据
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

        # 查询财务数据
        query = db.query(FinancialData).filter(
            and_(
                FinancialData.date >= start_date,
                FinancialData.date <= end_date,
            )
        )

        all_data = query.all()

        # 汇总统计
        summary = {}
        revenue = 0.0
        expense = 0.0
        profit = 0.0
        assets = 0.0
        liabilities = 0.0
        investment = 0.0

        for item in all_data:
            amount = float(item.amount)
            summary[item.category] = summary.get(item.category, 0.0) + amount

            if item.category == FinancialCategory.REVENUE:
                revenue += amount
            elif item.category == FinancialCategory.EXPENSE:
                expense += amount
            elif item.category == FinancialCategory.PROFIT:
                profit += amount
            elif item.category == FinancialCategory.ASSET:
                assets += amount
            elif item.category == FinancialCategory.LIABILITY:
                liabilities += amount
            elif item.category == FinancialCategory.INVESTMENT:
                investment += amount

        # 计算利润（如果没有直接记录）
        if profit == 0:
            profit = revenue - expense

        # 按日期分组数据
        daily_data = {}
        for item in all_data:
            day_key = item.date.isoformat()
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "date": day_key,
                    "revenue": 0.0,
                    "expense": 0.0,
                    "profit": 0.0,
                }
            
            amount = float(item.amount)
            if item.category == FinancialCategory.REVENUE:
                daily_data[day_key]["revenue"] += amount
            elif item.category == FinancialCategory.EXPENSE:
                daily_data[day_key]["expense"] += amount

        # 计算每日利润
        for day_data in daily_data.values():
            day_data["profit"] = day_data["revenue"] - day_data["expense"]

        return DashboardResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            revenue=revenue,
            expense=expense,
            profit=profit,
            assets=assets,
            liabilities=liabilities,
            investment=investment,
            daily_data=list(daily_data.values()),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取财务看板失败: {str(e)}")


@router.get("/data", response_model=List[FinancialDataOutput])
async def get_financial_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
    查询财务数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        category: 类别过滤
        limit: 返回数量限制
        db: 数据库会话
        
    Returns:
        财务数据列表
    """
    try:
        query = db.query(FinancialData)

        if start_date:
            query = query.filter(FinancialData.date >= start_date)
        if end_date:
            query = query.filter(FinancialData.date <= end_date)
        if category:
            query = query.filter(FinancialData.category == category)

        query = query.order_by(FinancialData.date.desc()).limit(limit)

        return query.all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询财务数据失败: {str(e)}")


@router.put("/data/{financial_id}", response_model=FinancialDataOutput)
async def update_financial_data(
    financial_id: int,
    data: FinancialDataInput,
    db: Session = Depends(get_db),
):
    """
    更新财务数据
    
    Args:
        financial_id: 财务数据ID
        data: 财务数据输入
        db: 数据库会话
        
    Returns:
        更新后的财务数据
    """
    try:
        financial_data = db.query(FinancialData).filter(
            FinancialData.id == financial_id
        ).first()
        
        if not financial_data:
            raise HTTPException(status_code=404, detail="财务数据不存在")
        
        # 保存旧数据用于事件发布
        old_data = {
            "id": financial_data.id,
            "date": financial_data.date.isoformat() if financial_data.date else None,
            "period_type": financial_data.period_type,
            "category": financial_data.category,
            "subcategory": financial_data.subcategory,
            "amount": float(financial_data.amount),
            "description": financial_data.description,
            "source_document": financial_data.source_document
        }
        
        # 更新数据
        financial_data.date = data.date
        financial_data.period_type = data.period_type
        financial_data.category = data.category
        financial_data.subcategory = data.subcategory
        financial_data.amount = data.amount
        financial_data.description = data.description
        financial_data.source_document = data.source_document
        if data.metadata:
            financial_data.extra_metadata = data.metadata
        financial_data.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(financial_data)
        
        # 自动发布财务数据更新事件
        if data_listener:
            try:
                import asyncio
                new_data = {
                    "id": financial_data.id,
                    "date": financial_data.date.isoformat() if financial_data.date else None,
                    "period_type": financial_data.period_type,
                    "category": financial_data.category,
                    "subcategory": financial_data.subcategory,
                    "amount": float(financial_data.amount),
                    "description": financial_data.description,
                    "source_document": financial_data.source_document
                }
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            data_listener.on_financial_data_updated(
                                str(financial_id), old_data, new_data
                            )
                        )
                    else:
                        loop.run_until_complete(
                            data_listener.on_financial_data_updated(
                                str(financial_id), old_data, new_data
                            )
                        )
                except RuntimeError:
                    asyncio.run(
                        data_listener.on_financial_data_updated(
                            str(financial_id), old_data, new_data
                        )
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"财务数据更新事件发布失败: {e}")
        
        return financial_data
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新财务数据失败: {str(e)}")


@router.delete("/data/{financial_id}")
async def delete_financial_data(
    financial_id: int,
    db: Session = Depends(get_db),
):
    """
    删除财务数据
    
    Args:
        financial_id: 财务数据ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    try:
        financial_data = db.query(FinancialData).filter(
            FinancialData.id == financial_id
        ).first()
        
        if not financial_data:
            raise HTTPException(status_code=404, detail="财务数据不存在")
        
        # 保存旧数据用于事件发布
        old_data = {
            "id": financial_data.id,
            "date": financial_data.date.isoformat() if financial_data.date else None,
            "period_type": financial_data.period_type,
            "category": financial_data.category,
            "subcategory": financial_data.subcategory,
            "amount": float(financial_data.amount),
            "description": financial_data.description,
            "source_document": financial_data.source_document
        }
        
        db.delete(financial_data)
        db.commit()
        
        # 自动发布财务数据删除事件
        if data_listener:
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            data_listener.on_financial_data_deleted(
                                str(financial_id), old_data
                            )
                        )
                    else:
                        loop.run_until_complete(
                            data_listener.on_financial_data_deleted(
                                str(financial_id), old_data
                            )
                        )
                except RuntimeError:
                    asyncio.run(
                        data_listener.on_financial_data_deleted(
                            str(financial_id), old_data
                        )
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"财务数据删除事件发布失败: {e}")
        
        return {
            "success": True,
            "message": "财务数据已删除",
            "financial_id": financial_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除财务数据失败: {str(e)}")


# get_db函数已从core.database导入

