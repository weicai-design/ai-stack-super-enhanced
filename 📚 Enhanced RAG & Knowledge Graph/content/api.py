"""
内容创作API（完整版）
Content Creation API

提供完整的内容创作功能：12个端点

版本: v1.0.0
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from .models import Content, Material, PublishPlan
from .manager import content_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["Content Creation"])


class CollectRequest(BaseModel):
    """收集请求"""
    keywords: List[str] = Field(..., description="关键词")


class CreateFromMaterialRequest(BaseModel):
    """基于素材创作请求"""
    material_id: str
    platform: str


@router.get("/health")
async def content_health():
    return {
        "status": "healthy",
        "module": "content",
        "version": "1.0.0",
        "features": [
            "material_collection",
            "content_creation",
            "auto_publishing",
            "performance_tracking"
        ]
    }


# ==================== 素材管理 ====================

@router.post("/materials")
async def collect_material(material: Material, tenant=Depends(require_tenant)):
    """收集素材"""
    result = content_manager.collect_material(tenant.id, material)
    return result.model_dump()


@router.post("/materials/collect-web")
async def collect_from_web(request: CollectRequest, tenant=Depends(require_tenant)):
    """从网络收集素材"""
    materials = content_manager.collect_from_web(tenant.id, request.keywords)
    return [m.model_dump() for m in materials]


@router.get("/materials")
async def list_materials(tenant=Depends(require_tenant)):
    """获取素材列表"""
    materials = content_manager.get_materials(tenant.id)
    return [m.model_dump() for m in materials]


# ==================== 内容创作 ====================

@router.post("/contents")
async def create_content(content: Content, tenant=Depends(require_tenant)):
    """创作内容"""
    result = content_manager.create_content(tenant.id, content)
    return result.model_dump()


@router.post("/contents/from-material")
async def create_from_material(request: CreateFromMaterialRequest, tenant=Depends(require_tenant)):
    """基于素材创作"""
    content = content_manager.create_from_material(tenant.id, request.material_id, request.platform)
    return content.model_dump()


@router.get("/contents")
async def list_contents(tenant=Depends(require_tenant)):
    """获取内容列表"""
    contents = content_manager.get_contents(tenant.id)
    return [c.model_dump() for c in contents]


# ==================== 发布管理 ====================

@router.post("/publish-plans")
async def schedule_publish(plan: PublishPlan, tenant=Depends(require_tenant)):
    """计划发布"""
    result = content_manager.schedule_publish(tenant.id, plan)
    return result.model_dump()


@router.post("/contents/{content_id}/publish")
async def publish_now(
    content_id: str,
    platform: str = Query(...),
    tenant=Depends(require_tenant)
):
    """立即发布"""
    content = content_manager.publish_now(tenant.id, content_id, platform)
    return content.model_dump()


@router.get("/publish-plans")
async def list_plans(tenant=Depends(require_tenant)):
    """获取发布计划"""
    plans = content_manager.get_publish_plans(tenant.id)
    return [p.model_dump() for p in plans]


# ==================== 效果跟踪 ====================

@router.get("/contents/{content_id}/performance")
async def track_performance(content_id: str, tenant=Depends(require_tenant)):
    """跟踪效果"""
    performance = content_manager.track_performance(tenant.id, content_id)
    return performance

