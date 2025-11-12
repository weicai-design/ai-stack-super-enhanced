"""专家模型API"""
import logging
from fastapi import APIRouter, Depends, Query
from .manager import expert_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/expert", tags=["Expert Models"])

@router.get("/health")
async def expert_health():
    return {"status": "healthy", "module": "expert", "version": "1.0.0"}

@router.get("/models")
async def list_experts(tenant=Depends(require_tenant)):
    return [expert.model_dump() for expert in expert_manager.experts.values()]

@router.get("/advice")
async def get_advice(
    domain: str = Query(...),
    question: str = Query(...),
    tenant=Depends(require_tenant)
):
    advice = expert_manager.get_advice(domain, question)
    return advice.model_dump()












