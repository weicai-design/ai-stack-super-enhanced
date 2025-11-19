"""
财务管理API（修复版）
提供财务管理功能的REST API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

router = APIRouter(prefix="/finance", tags=["Financial Management"])
logger = logging.getLogger(__name__)

# 导入财务管理器
try:
    from enterprise.finance.finance_manager import finance_manager
    logger.info("✅ 财务管理器已加载")
except Exception as e:
    finance_manager = None
    logger.warning(f"财务管理器加载失败: {e}")


# ==================== 数据模型 ====================

class FinancialDataImport(BaseModel):
    """财务数据导入模型"""
    data: Dict[str, Any] = Field(..., description="财务数据")
    data_type: str = Field(..., description="数据类型")

# ==================== API端点 ====================

@router.get("/health")
async def health_check():
    """财务管理健康检查"""
    return {
        "status": "healthy",
        "module": "finance",
        "version": "3.2.0",
        "features": [
            "data_import_export",
            "dashboard",
            "profit_analysis",
            "expense_analysis",
            "revenue_analysis",
            "reports"
        ]
    }

@router.post("/import")
async def import_financial_data(request: FinancialDataImport):
    """导入财务数据"""
    if not finance_manager:
        raise HTTPException(status_code=503, detail="财务管理器未初始化")
    
    try:
        result = finance_manager.import_data(request.data, request.data_type)
        return {"status": "success", "message": "数据导入成功", "result": result}
    except Exception as e:
        logger.error(f"导入财务数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_financial_dashboard(period: str = "monthly"):
    """获取财务看板"""
    if not finance_manager:
        return {"status": "stub", "message": "财务管理器未初始化"}
    
    try:
        dashboard = finance_manager.get_dashboard(period)
        return dashboard
    except Exception as e:
        logger.error(f"获取看板失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/profit")
async def analyze_profit(period: str = "monthly"):
    """盈亏分析"""
    if not finance_manager:
        return {"status": "stub", "analysis": "模拟盈亏分析"}
    
    try:
        analysis = finance_manager.analyze_profit(period)
        return analysis
    except Exception as e:
        logger.error(f"盈亏分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/expenses")
async def analyze_expenses(period: str = "monthly"):
    """费用分析"""
    if not finance_manager:
        return {"status": "stub", "analysis": "模拟费用分析"}
    
    try:
        analysis = finance_manager.analyze_expenses(period)
        return analysis
    except Exception as e:
        logger.error(f"费用分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/revenue")
async def analyze_revenue(period: str = "monthly"):
    """收入分析"""
    if not finance_manager:
        return {"status": "stub", "analysis": "模拟收入分析"}
    
    try:
        analysis = finance_manager.analyze_revenue(period)
        return analysis
    except Exception as e:
        logger.error(f"收入分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/income")
async def generate_income_report(period: str = "monthly"):
    """生成利润表"""
    if not finance_manager:
        return {"status": "stub", "report": "模拟利润表"}
    
    try:
        report = finance_manager.generate_income_statement(period)
        return report
    except Exception as e:
        logger.error(f"生成利润表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics():
    """获取财务统计"""
    if not finance_manager:
        return {
            "total_revenue": 0,
            "total_expenses": 0,
            "total_profit": 0,
            "status": "stub"
        }
    
    try:
        stats = finance_manager.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))



























