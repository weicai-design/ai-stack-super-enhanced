"""
Trend Analysis API
趋势分析API接口
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/🔍 Intelligent Trend Analysis')

from crawlers.news_crawler import default_crawler_manager
from analysis.trend_analyzer import TrendAnalyzer, ReportGenerator

router = APIRouter(prefix="/trend", tags=["Trend Analysis API"])

# 初始化分析器
analyzer = TrendAnalyzer()
report_generator = ReportGenerator()


# ============ Pydantic Models ============

class CrawlTaskRequest(BaseModel):
    """爬取任务请求"""
    categories: List[str] = ["policy", "tech", "industry", "hot"]
    frequency: Optional[str] = "daily"  # 爬取频率


class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: str  # industry/investment
    industry: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# ============ API Endpoints ============

@router.post("/crawl/start")
async def start_crawling(
    request: CrawlTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    启动爬虫任务
    
    根据需求6.1: 按照一定频率获取信息
    
    Args:
        request: 爬取任务配置
        background_tasks: 后台任务
        
    Returns:
        任务启动状态
    """
    try:
        # 在后台执行爬虫
        background_tasks.add_task(_execute_crawl_task, request.categories)
        
        return {
            "status": "started",
            "message": "爬虫任务已启动",
            "categories": request.categories,
            "frequency": request.frequency,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动爬虫失败: {str(e)}")


@router.get("/data/latest")
async def get_latest_data(
    category: Optional[str] = Query(None, description="类别筛选"),
    limit: int = Query(20, description="返回数量")
):
    """
    获取最新爬取的数据
    
    Args:
        category: 类别
        limit: 数量限制
        
    Returns:
        最新数据
    """
    try:
        results = default_crawler_manager.get_latest_results(limit)
        
        if category:
            results = [r for r in results if r.get("category") == category]
        
        return {
            "total": len(results),
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/analysis/summary")
async def get_trend_summary(
    category: Optional[str] = Query(None, description="类别筛选")
):
    """
    获取趋势汇总
    
    根据需求6.3: 汇总、总结
    
    Args:
        category: 类别
        
    Returns:
        趋势汇总
    """
    try:
        # 获取数据
        data = default_crawler_manager.get_latest_results(100)
        
        if category:
            data = [d for d in data if d.get("category") == category]
        
        # 分析汇总
        summary = analyzer.summarize_content(data)
        
        # 检测热点
        hot_topics = analyzer.detect_hot_topics(data)
        
        return {
            "summary": summary,
            "hot_topics": hot_topics[:10],
            "category": category or "全部",
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/report/generate")
async def generate_report(request: ReportRequest):
    """
    生成分析报告
    
    根据需求6.4: 输出报告（产业报告、行业报告、投资报告）
    
    Args:
        request: 报告请求
        
    Returns:
        生成的报告
    """
    try:
        # 获取相关数据
        data = default_crawler_manager.get_latest_results(200)
        
        # 根据报告类型生成
        if request.report_type == "industry":
            report = report_generator.generate_industry_report(
                industry=request.industry or "科技",
                data=data
            )
        elif request.report_type == "investment":
            report = report_generator.generate_investment_report(data)
        else:
            raise HTTPException(status_code=400, detail="不支持的报告类型")
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")


@router.get("/hot-topics")
async def get_hot_topics(limit: int = Query(10, description="返回数量")):
    """
    获取热点话题
    
    Args:
        limit: 返回数量
        
    Returns:
        热点话题列表
    """
    try:
        data = default_crawler_manager.get_latest_results(100)
        hot_topics = analyzer.detect_hot_topics(data)
        
        return {
            "hot_topics": hot_topics[:limit],
            "total": len(hot_topics),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热点失败: {str(e)}")


@router.get("/dashboard")
async def get_trend_dashboard():
    """
    获取趋势分析看板
    
    Returns:
        看板数据
    """
    try:
        # 获取最新数据
        data = default_crawler_manager.get_latest_results(100)
        
        # 汇总分析
        summary = analyzer.summarize_content(data)
        
        # 热点话题
        hot_topics = analyzer.detect_hot_topics(data)
        
        # 分类统计
        classified = analyzer.classify_content(data)
        
        # 模拟爬虫状态
        crawler_status = {
            "total_crawlers": 4,
            "active_crawlers": 4,
            "last_crawl_time": datetime.now().isoformat(),
            "total_articles": len(data),
            "today_articles": len([d for d in data if d.get("publish_date", "")[:10] == datetime.now().strftime("%Y-%m-%d")]),
        }
        
        return {
            "crawler_status": crawler_status,
            "summary": summary,
            "hot_topics": hot_topics[:10],
            "category_distribution": {k: len(v) for k, v in classified.items()},
            "latest_articles": data[-10:] if data else [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取看板数据失败: {str(e)}")


@router.get("/")
def root():
    """趋势分析模块根路径"""
    return {
        "module": "Intelligent Trend Analysis",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "crawl": "/trend/crawl/start",
            "data": "/trend/data/latest",
            "summary": "/trend/analysis/summary",
            "report": "/trend/report/generate",
            "hot_topics": "/trend/hot-topics",
            "dashboard": "/trend/dashboard"
        }
    }


# ============ 辅助函数 ============

async def _execute_crawl_task(categories: List[str]):
    """
    执行爬虫任务（后台）
    
    Args:
        categories: 爬取类别列表
    """
    print(f"🕷️ 开始执行爬虫任务: {categories}")
    
    try:
        # 执行爬虫
        results = default_crawler_manager.crawl_all()
        
        print(f"✅ 爬虫任务完成，获取 {len(results)} 条数据")
        
        # TODO: 保存到数据库或RAG
        
    except Exception as e:
        print(f"❌ 爬虫任务失败: {e}")

