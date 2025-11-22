"""
财务管理API
Finance Management API

提供完整的财务管理API端点

版本: v1.0.0
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

# 添加父目录到路径
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from enterprise.finance.models import (
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    FinancialPeriod
)
from enterprise.finance.finance_manager import finance_manager
from enterprise.finance.analysis_engine import FinancialAnalysisEngine
from enterprise.finance.dashboard_generator import DashboardGenerator
from enterprise.finance.report_generator import ReportGenerator
from enterprise.tenancy.middleware import get_current_tenant, require_tenant

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/finance", tags=["Financial Management"])

# 初始化组件
analysis_engine = FinancialAnalysisEngine()
dashboard_gen = DashboardGenerator()
report_gen = ReportGenerator()


# ==================== 请求模型 ====================

class ImportDataRequest(BaseModel):
    """导入数据请求"""
    data: Dict[str, Any] = Field(..., description="财务数据")
    data_type: str = Field("income_statement", description="数据类型")


class ExportDataRequest(BaseModel):
    """导出数据请求"""
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    data_type: str = Field("all", description="数据类型")


# ==================== API端点 ====================

@router.get("/health")
async def finance_health():
    """
    财务模块健康检查
    """
    return {
        "status": "healthy",
        "module": "finance",
        "version": "1.0.0",
        "features": [
            "财务数据管理",
            "盈亏分析",
            "费用分析",
            "收入分析",
            "财务看板",
            "财务报表"
        ]
    }


@router.post("/import")
async def import_financial_data(
    request: ImportDataRequest,
    tenant = Depends(require_tenant)
):
    """
    导入财务数据
    
    支持导入：
    - 利润表（income_statement）
    - 资产负债表（balance_sheet）
    - 现金流量表（cash_flow）
    """
    try:
        result = finance_manager.import_financial_data(
            tenant_id=tenant.id,
            data=request.data,
            data_type=request.data_type
        )
        
        return {
            "success": True,
            "message": "数据导入成功",
            "data": result.model_dump()
        }
    
    except Exception as e:
        logger.error(f"导入财务数据失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export")
async def export_financial_data(
    request: ExportDataRequest,
    tenant = Depends(require_tenant)
):
    """
    导出财务数据
    
    可以导出指定日期范围和类型的财务数据
    """
    try:
        start_date = datetime.fromisoformat(request.start_date).date() if request.start_date else None
        end_date = datetime.fromisoformat(request.end_date).date() if request.end_date else None
        
        result = finance_manager.export_financial_data(
            tenant_id=tenant.id,
            start_date=start_date,
            end_date=end_date,
            data_type=request.data_type
        )
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        logger.error(f"导出财务数据失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statements/income")
async def get_income_statements(
    tenant = Depends(require_tenant),
    period: Optional[FinancialPeriod] = Query(None, description="财务周期"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期")
):
    """
    获取利润表
    
    可以按周期和日期范围筛选
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        statements = finance_manager.get_income_statements(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return {
            "count": len(statements),
            "data": [stmt.model_dump() for stmt in statements]
        }
    
    except Exception as e:
        logger.error(f"获取利润表失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statements/balance")
async def get_balance_sheets(
    tenant = Depends(require_tenant),
    period: Optional[FinancialPeriod] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取资产负债表
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        sheets = finance_manager.get_balance_sheets(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return {
            "count": len(sheets),
            "data": [sheet.model_dump() for sheet in sheets]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statements/cashflow")
async def get_cash_flows(
    tenant = Depends(require_tenant),
    period: Optional[FinancialPeriod] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    获取现金流量表
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        flows = finance_manager.get_cash_flows(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return {
            "count": len(flows),
            "data": [flow.model_dump() for flow in flows]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/profit")
async def analyze_profit(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY, description="分析周期"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    盈亏分析
    
    分析指定周期的盈亏情况，包括：
    - 收入、成本、利润
    - 盈亏平衡点
    - 关键影响因素
    - 优化建议
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        result = analysis_engine.analyze_profit(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return result.model_dump()
    
    except Exception as e:
        logger.error(f"盈亏分析失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/expenses")
async def analyze_expenses(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    费用分析
    
    分析费用结构和合理性，包括：
    - 各类费用明细
    - 费用占比
    - 合理性评估
    - 优化建议
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        result = analysis_engine.analyze_expenses(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return result.model_dump()
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analysis/revenue")
async def analyze_revenue(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    收入分析
    
    分析收入情况，包括：
    - 收入构成
    - 客户订单统计
    - 行业对比
    - 收入预测
    """
    try:
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        
        result = analysis_engine.analyze_revenue(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end
        )
        
        return result.model_dump()
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dashboard")
async def get_financial_dashboard(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY, description="看板周期")
):
    """
    获取财务看板
    
    生成综合财务看板，包括：
    - 核心指标
    - 趋势图表
    - 期间对比
    - 预警信息
    
    支持日/周/月/季/年看板
    """
    try:
        dashboard = dashboard_gen.generate_dashboard(
            tenant_id=tenant.id,
            period=period
        )
        
        return dashboard
    
    except Exception as e:
        logger.error(f"生成看板失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/income")
async def generate_income_report(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY),
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    format: str = Query("json", description="报表格式")
):
    """
    生成利润表报告
    
    支持格式：json, html, excel
    """
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        
        report = report_gen.generate_income_statement_report(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end,
            format=format
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/balance")
async def generate_balance_report(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY),
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query("json")
):
    """
    生成资产负债表报告
    """
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        
        report = report_gen.generate_balance_sheet_report(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end,
            format=format
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/cashflow")
async def generate_cashflow_report(
    tenant = Depends(require_tenant),
    period: FinancialPeriod = Query(FinancialPeriod.MONTHLY),
    start_date: str = Query(...),
    end_date: str = Query(...),
    format: str = Query("json")
):
    """
    生成现金流量表报告
    """
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        
        report = report_gen.generate_cash_flow_report(
            tenant_id=tenant.id,
            period=period,
            start_date=start,
            end_date=end,
            format=format
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_finance_statistics(
    tenant = Depends(require_tenant)
):
    """
    获取财务统计信息
    """
    try:
        stats = finance_manager.get_statistics(tenant.id)
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 导出 ====================

__all__ = ["router"]

































