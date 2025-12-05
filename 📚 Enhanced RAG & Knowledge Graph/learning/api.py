"""学习管理API"""
import logging
from fastapi import APIRouter, Depends
from .models import LearningRecord, UserPreference, Optimization
from .manager import learning_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/learning", tags=["Self-Learning"])

@router.get("/health")
async def learning_health():
    return {"status": "healthy", "module": "learning", "version": "1.0.0"}

@router.post("/records")
async def record_learning(record: LearningRecord, tenant=Depends(require_tenant)):
    result = learning_manager.record_learning(tenant.id, record)
    return result.model_dump()

@router.post("/preferences")
async def update_preference(user_id: str, pref: UserPreference, tenant=Depends(require_tenant)):
    result = learning_manager.update_preference(tenant.id, user_id, pref)
    return result.model_dump()

@router.post("/optimizations")
async def suggest_optimization(opt: Optimization, tenant=Depends(require_tenant)):
    result = learning_manager.suggest_optimization(tenant.id, opt)
    return result.model_dump()






































