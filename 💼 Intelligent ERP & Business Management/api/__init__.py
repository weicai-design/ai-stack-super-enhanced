"""
ERP API Module
ERP API模块

整合所有ERP API路由
"""

from fastapi import APIRouter

from .finance_api import router as finance_router
from .analytics_api import router as analytics_router
from .process_api import router as process_router

# 创建主路由
erp_router = APIRouter(prefix="/erp", tags=["ERP API"])

# 注册子路由
erp_router.include_router(finance_router)
erp_router.include_router(analytics_router)
erp_router.include_router(process_router)

__all__ = ["erp_router", "finance_router", "analytics_router", "process_router"]

