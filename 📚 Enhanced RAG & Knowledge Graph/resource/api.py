"""资源管理API"""
import logging
from fastapi import APIRouter, Depends
from .models import ResourceConfig, Alert
from .manager import resource_manager
from enterprise.tenancy.middleware import require_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resource", tags=["Resource Management"])

@router.get("/health")
async def resource_health():
    return {"status": "healthy", "module": "resource", "version": "1.0.0"}

@router.get("/usage")
async def get_usage(tenant=Depends(require_tenant)):
    usage = resource_manager.get_usage()
    return usage.model_dump()

@router.post("/config")
async def set_config(config: ResourceConfig, tenant=Depends(require_tenant)):
    result = resource_manager.set_config(tenant.id, config)
    return result.model_dump()

@router.get("/alerts")
async def get_alerts():
    return [alert.model_dump() for alert in resource_manager.alerts]


































