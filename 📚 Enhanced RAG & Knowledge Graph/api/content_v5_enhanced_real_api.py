"""
内容V5增强API - 使用真实业务管理器
完全连接前后端，实现真实内容创作功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/v5/content/real", tags=["Content-V5-Enhanced"])


# ==================== 数据模型 ====================

class MaterialCollectRequest(BaseModel):
    topic: str
    source_type: str = "hot"
    keywords: Optional[List[str]] = None


class ContentCreateRequest(BaseModel):
    topic: str
    content_type: str = "article"
    style: str = "professional"
    length: str = "medium"


class ContentPublishRequest(BaseModel):
    content: str
    title: str
    platform: str
    user_id: Optional[str] = None


# ==================== 素材收集API ====================

@router.post("/materials/collect")
async def collect_materials(request: MaterialCollectRequest):
    """素材收集（真实搜索）"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.collect_materials(
            topic=request.topic,
            source_type=request.source_type,
            keywords=request.keywords
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 内容创作API ====================

@router.post("/create")
async def create_content(request: ContentCreateRequest):
    """内容创作（真实AI生成）"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.create_content(
            topic=request.topic,
            content_type=request.content_type,
            style=request.style,
            length=request.length
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/protect")
async def protect_copyright(content: str, mode: str = "deai"):
    """版权保护（去AI化）"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.protect_copyright(content, mode)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 发布管理API ====================

@router.post("/publish")
async def publish_content(request: ContentPublishRequest):
    """发布内容（真实或草稿）"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.publish_content(
            content=request.content,
            title=request.title,
            platform=request.platform,
            user_id=request.user_id
        )
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def get_posts(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 20
):
    """获取内容列表"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.get_posts(status, platform, limit)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 效果分析API ====================

@router.get("/performance/{post_id}")
async def track_performance(post_id: str):
    """跟踪内容效果"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.track_performance(post_id)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/success-rate")
async def analyze_success_rate(platform: Optional[str] = None, period_days: int = 30):
    """成功率分析"""
    try:
        from business.content_manager import get_content_manager
        content_mgr = get_content_manager()
        
        result = await content_mgr.analyze_success_rate(platform, period_days)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """内容系统健康检查"""
    return {
        "status": "healthy",
        "module": "Content",
        "version": "5.5",
        "features": {
            "material_collection": True,
            "ai_creation": True,
            "copyright_protection": True,
            "platform_publishing": True,
            "performance_tracking": True,
            "analytics": True
        },
        "note": "真实发布需平台API授权"
    }


