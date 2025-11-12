"""
趋势分析API（完整版）
Trend Analysis API

提供完整的趋势分析功能：12个端点

版本: v1.0.0
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from .models import TrendData, Report, Analysis
from .manager import trend_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trend", tags=["Trend Analysis"])


class CrawlRequest(BaseModel):
    """爬取请求"""
    category: str
    keywords: List[str]


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    analysis_id: str
    report_type: str


@router.get("/health")
async def trend_health():
    return {
        "status": "healthy",
        "module": "trend",
        "version": "1.0.0",
        "features": [
            "web_crawling",
            "data_processing",
            "report_generation",
            "trend_prediction"
        ]
    }


# ==================== 数据采集 ====================

@router.post("/data")
async def collect_data(data: TrendData, tenant=Depends(require_tenant)):
    """收集趋势数据"""
    result = trend_manager.collect_data(tenant.id, data)
    return result.model_dump()


@router.post("/data/crawl")
async def crawl_news(request: CrawlRequest, tenant=Depends(require_tenant)):
    """爬取新闻资讯"""
    data_list = trend_manager.crawl_news(tenant.id, request.category, request.keywords)
    return [d.model_dump() for d in data_list]


@router.get("/data")
async def list_data(
    tenant=Depends(require_tenant),
    category: str = Query(None, description="按类别过滤")
):
    """获取趋势数据列表"""
    data = trend_manager.get_data(tenant.id, category)
    return [d.model_dump() for d in data]


# ==================== 分析处理 ====================

@router.post("/analyses")
async def create_analysis(analysis: Analysis, tenant=Depends(require_tenant)):
    """创建分析"""
    result = trend_manager.create_analysis(tenant.id, analysis)
    return result.model_dump()


@router.post("/analyses/process")
async def process_and_analyze(
    tenant=Depends(require_tenant),
    category: str = Query(None)
):
    """处理和分析数据"""
    analysis = trend_manager.process_and_analyze(tenant.id, category)
    return analysis.model_dump()


@router.get("/analyses")
async def list_analyses(tenant=Depends(require_tenant)):
    """获取分析列表"""
    analyses = trend_manager.get_analyses(tenant.id)
    return [a.model_dump() for a in analyses]


# ==================== 报告生成 ====================

@router.post("/reports")
async def generate_report(report: Report, tenant=Depends(require_tenant)):
    """生成报告"""
    result = trend_manager.generate_report(tenant.id, report)
    return result.model_dump()


@router.post("/reports/from-analysis")
async def generate_from_analysis(request: GenerateReportRequest, tenant=Depends(require_tenant)):
    """基于分析生成报告"""
    report = trend_manager.generate_from_analysis(
        tenant.id,
        request.analysis_id,
        request.report_type
    )
    return report.model_dump()


@router.get("/reports")
async def list_reports(tenant=Depends(require_tenant)):
    """获取报告列表"""
    reports = trend_manager.get_reports(tenant.id)
    return [r.model_dump() for r in reports]

