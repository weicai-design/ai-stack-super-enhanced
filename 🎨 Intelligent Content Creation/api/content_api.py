"""
Content Creation API
内容创作API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/🎨 Intelligent Content Creation')

from sources.material_collector import default_material_manager
from generation.content_generator import default_generator, default_content_plan, default_optimizer
from platforms.publisher import default_publish_manager

router = APIRouter(prefix="/content", tags=["Content Creation API"])


# ============ Pydantic Models ============

class ContentGenerateRequest(BaseModel):
    """内容生成请求"""
    topic: str
    platform: str = "xiaohongshu"
    style: str = "casual"


class ContentPlanRequest(BaseModel):
    """内容计划请求"""
    topic: str
    platforms: List[str]
    frequency: str = "daily"
    duration_days: int = 7


class PublishRequest(BaseModel):
    """发布请求"""
    content_id: str
    platforms: List[str]


# ============ API Endpoints ============

@router.get("/materials/hot-topics")
async def get_hot_topics(platform: Optional[str] = None, limit: int = 10):
    """
    获取热点话题
    
    根据需求4.1: 收集热点素材
    
    Args:
        platform: 平台筛选
        limit: 数量限制
        
    Returns:
        热点话题列表
    """
    try:
        all_topics = default_material_manager.collect_all_hot_topics(limit)
        
        if platform and platform in all_topics:
            return {
                "platform": platform,
                "topics": all_topics[platform],
                "count": len(all_topics[platform])
            }
        
        # 合并排序
        merged = default_material_manager.merge_and_rank(all_topics)
        
        return {
            "all_platforms": all_topics,
            "merged_top": merged[:limit],
            "total": len(merged)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热点失败: {str(e)}")


@router.post("/generate")
async def generate_content(request: ContentGenerateRequest):
    """
    生成内容
    
    根据需求4.4: 自主内容创作
    
    Args:
        request: 生成请求
        
    Returns:
        生成的内容
    """
    try:
        content = default_generator.generate_article(
            topic=request.topic,
            platform=request.platform,
            style=request.style
        )
        
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成内容失败: {str(e)}")


@router.post("/plan/create")
async def create_content_plan(request: ContentPlanRequest):
    """
    创建内容计划
    
    根据需求4.3: 制定内容计划
    
    Args:
        request: 计划请求
        
    Returns:
        创建的计划
    """
    try:
        plan = default_content_plan.create_plan(
            topic=request.topic,
            platforms=request.platforms,
            frequency=request.frequency,
            duration_days=request.duration_days
        )
        
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建计划失败: {str(e)}")


@router.get("/plan/list")
async def list_content_plans():
    """
    获取内容计划列表
    
    Returns:
        计划列表
    """
    try:
        plans = default_content_plan.get_active_plans()
        return {"plans": plans, "count": len(plans)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取计划失败: {str(e)}")


@router.post("/publish")
async def publish_content(
    request: PublishRequest,
    background_tasks: BackgroundTasks
):
    """
    发布内容
    
    根据需求4.5: 自主发布
    
    Args:
        request: 发布请求
        background_tasks: 后台任务
        
    Returns:
        发布结果
    """
    try:
        # 模拟内容
        content = {
            "id": request.content_id,
            "title": "测试内容",
            "content": "这是测试内容...",
        }
        
        # 发布到多个平台
        results = default_publish_manager.publish_to_platforms(
            content=content,
            platforms=request.platforms
        )
        
        return {
            "status": "success",
            "published_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@router.get("/stats/all")
async def get_all_stats():
    """
    获取所有内容的数据统计
    
    根据需求4.5: 跟踪
    
    Returns:
        统计数据
    """
    try:
        stats = default_publish_manager.track_all_posts()
        
        # 汇总
        total_views = sum(s.get("views", 0) for s in stats)
        total_likes = sum(s.get("likes", 0) for s in stats)
        
        return {
            "posts": stats,
            "summary": {
                "total_posts": len(stats),
                "total_views": total_views,
                "total_likes": total_likes,
                "avg_engagement": round(total_likes / max(total_views, 1) * 100, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/optimization/insights")
async def get_optimization_insights():
    """
    获取优化洞察
    
    根据需求4.6: 自我学习和进化
    
    Returns:
        优化洞察
    """
    try:
        insights = default_optimizer.get_optimization_insights()
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取洞察失败: {str(e)}")


@router.get("/dashboard")
async def get_content_dashboard():
    """
    获取内容创作看板
    
    Returns:
        看板数据
    """
    try:
        # 热点话题
        hot_topics = default_material_manager.collect_all_hot_topics(5)
        merged_topics = default_material_manager.merge_and_rank(hot_topics)
        
        # 内容计划
        plans = default_content_plan.get_active_plans()
        
        # 发布统计
        stats = default_publish_manager.track_all_posts()
        total_views = sum(s.get("views", 0) for s in stats)
        total_likes = sum(s.get("likes", 0) for s in stats)
        
        # 优化洞察
        insights = default_optimizer.get_optimization_insights()
        
        return {
            "hot_topics": merged_topics[:10],
            "active_plans": len(plans),
            "total_posts": len(stats),
            "total_views": total_views,
            "total_likes": total_likes,
            "engagement_rate": round(total_likes / max(total_views, 1) * 100, 2),
            "optimization_insights": insights,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取看板数据失败: {str(e)}")


@router.get("/")
def root():
    """内容创作模块根路径"""
    return {
        "module": "Intelligent Content Creation",
        "version": "1.0.0",
        "status": "running",
        "supported_platforms": ["xiaohongshu", "douyin", "zhihu", "toutiao"],
        "endpoints": {
            "hot_topics": "/content/materials/hot-topics",
            "generate": "/content/generate",
            "plan": "/content/plan/create",
            "publish": "/content/publish",
            "stats": "/content/stats/all",
            "dashboard": "/content/dashboard"
        }
    }

