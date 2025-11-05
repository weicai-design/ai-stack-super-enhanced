"""
资源管理 - API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from core.resource_monitor import ResourceMonitor
from core.resource_allocator import ResourceAllocator
from core.conflict_detector import ConflictDetector
from core.startup_manager import StartupManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resources", tags=["resources"])

# 初始化核心组件
resource_monitor = ResourceMonitor()
resource_allocator = ResourceAllocator()
conflict_detector = ConflictDetector(resource_monitor, resource_allocator)
startup_manager = StartupManager()


# ==================== Pydantic 模型 ====================

class ServiceResourceRequest(BaseModel):
    """服务资源请求"""
    service_name: str
    memory_gb: Optional[float] = None
    cpu_percent: Optional[float] = None


class ConflictResolutionRequest(BaseModel):
    """冲突解决请求"""
    option_id: int


# ==================== 资源监控 API ====================

@router.get("/system")
async def get_system_resources():
    """获取系统资源使用情况"""
    try:
        resources = resource_monitor.get_system_resources()
        status = resource_monitor.check_resource_status(resources)
        
        return {
            "success": True,
            "resources": resources,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def get_available_resources():
    """获取可用资源"""
    try:
        available = resource_monitor.estimate_available_resources()
        
        return {
            "success": True,
            "available": available
        }
        
    except Exception as e:
        logger.error(f"获取可用资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service/{service_name}")
async def get_service_resources(service_name: str):
    """获取服务资源使用情况"""
    try:
        usage = resource_monitor.get_service_resource_usage(service_name)
        
        if not usage:
            return {
                "success": False,
                "message": f"服务 {service_name} 未运行或不存在"
            }
        
        return {
            "success": True,
            "usage": usage
        }
        
    except Exception as e:
        logger.error(f"获取服务资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend")
async def get_resource_trend(window_minutes: int = 5):
    """获取资源使用趋势"""
    try:
        trend = resource_monitor.get_resource_trend(window_minutes)
        
        return {
            "success": True,
            "trend": trend
        }
        
    except Exception as e:
        logger.error(f"获取资源趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_optimization_suggestions():
    """获取资源优化建议"""
    try:
        resources = resource_monitor.get_system_resources()
        suggestions = resource_monitor.suggest_resource_optimization(resources)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"获取优化建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 资源分配 API ====================

@router.post("/allocate")
async def allocate_resources(services: List[str]):
    """分配资源给服务"""
    try:
        available = resource_monitor.estimate_available_resources()
        
        allocation = resource_allocator.calculate_resource_allocation(
            available.get("memory_available_gb", 0),
            available.get("cpu_available_percent", 0),
            services
        )
        
        return {
            "success": True,
            "allocation": allocation
        }
        
    except Exception as e:
        logger.error(f"资源分配失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/adjust")
async def adjust_service_resources(request: ServiceResourceRequest):
    """调整服务资源"""
    try:
        result = resource_allocator.adjust_allocation_for_service(
            request.service_name,
            request.memory_gb,
            request.cpu_percent
        )
        
        return result
        
    except Exception as e:
        logger.error(f"调整资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendation/{service_name}")
async def get_allocation_recommendation(service_name: str):
    """获取服务资源分配建议"""
    try:
        usage = resource_monitor.get_service_resource_usage(service_name)
        
        if not usage:
            return {
                "success": False,
                "message": f"服务 {service_name} 未运行"
            }
        
        recommendation = resource_allocator.get_allocation_recommendation(
            service_name,
            {
                "memory_gb": usage.get("memory_percent", 0) * 32 / 100,  # 假设32GB总内存
                "cpu_percent": usage.get("cpu_percent", 0)
            }
        )
        
        return {
            "success": True,
            "recommendation": recommendation
        }
        
    except Exception as e:
        logger.error(f"获取分配建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/balance")
async def balance_resources(services: List[str]):
    """平衡服务资源分配"""
    try:
        all_usage = resource_monitor.get_all_services_usage(services)
        balance_result = resource_allocator.balance_resources(all_usage)
        
        return {
            "success": True,
            "balance_result": balance_result
        }
        
    except Exception as e:
        logger.error(f"资源平衡失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 冲突检测 API ====================

@router.get("/conflicts/detect")
async def detect_conflicts(services: List[str]):
    """检测资源冲突"""
    try:
        conflicts = conflict_detector.detect_conflicts(services)
        
        return {
            "success": True,
            "conflicts": conflicts
        }
        
    except Exception as e:
        logger.error(f"冲突检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts/solutions")
async def get_conflict_solutions(services: List[str]):
    """获取冲突解决方案"""
    try:
        conflicts = conflict_detector.detect_conflicts(services)
        
        if not conflicts.get("has_conflict"):
            return {
                "success": True,
                "message": "当前无资源冲突",
                "options": []
            }
        
        options = conflict_detector.generate_resolution_options(conflicts)
        
        return {
            "success": True,
            "conflicts": conflicts,
            "options": options
        }
        
    except Exception as e:
        logger.error(f"获取解决方案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts/resolve")
async def resolve_conflict(
    request: ConflictResolutionRequest,
    services: List[str]
):
    """应用冲突解决方案"""
    try:
        conflicts = conflict_detector.detect_conflicts(services)
        
        if not conflicts.get("has_conflict"):
            return {
                "success": False,
                "message": "当前无资源冲突"
            }
        
        result = conflict_detector.apply_resolution(
            request.option_id,
            conflicts
        )
        
        return result
        
    except Exception as e:
        logger.error(f"解决冲突失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts/history")
async def get_conflict_history(limit: int = 10):
    """获取冲突历史"""
    try:
        history = conflict_detector.get_conflict_history(limit)
        
        return {
            "success": True,
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"获取冲突历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts/predict")
async def predict_conflict(new_service: str, current_services: List[str]):
    """预测新服务是否会引起冲突"""
    try:
        prediction = conflict_detector.predict_conflict(
            new_service,
            current_services
        )
        
        return {
            "success": True,
            "prediction": prediction
        }
        
    except Exception as e:
        logger.error(f"预测冲突失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 启动管理 API ====================

@router.post("/startup/start-all")
async def start_all_services(
    background_tasks: BackgroundTasks,
    skip_optional: bool = False
):
    """启动所有服务"""
    try:
        # 在后台执行启动
        result = startup_manager.start_all_services(skip_optional)
        
        return {
            "success": True,
            "message": "服务启动完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"启动服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/startup/stop-all")
async def stop_all_services():
    """停止所有服务"""
    try:
        result = startup_manager.stop_all_services()
        
        return {
            "success": True,
            "message": "服务停止完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"停止服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/startup/restart/{service_name}")
async def restart_service(service_name: str):
    """重启服务"""
    try:
        result = startup_manager.restart_service(service_name)
        
        return result
        
    except Exception as e:
        logger.error(f"重启服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup/status")
async def get_all_services_status():
    """获取所有服务状态"""
    try:
        status = startup_manager.get_all_services_status()
        
        return {
            "success": True,
            "services": status
        }
        
    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup/status/{service_name}")
async def get_service_status(service_name: str):
    """获取服务状态"""
    try:
        status = startup_manager.get_service_status(service_name)
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup/script")
async def generate_startup_script():
    """生成自动启动脚本"""
    try:
        script = startup_manager.generate_auto_start_script()
        
        return {
            "success": True,
            "script": script
        }
        
    except Exception as e:
        logger.error(f"生成脚本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup/launchd")
async def generate_launchd_plist():
    """生成 macOS LaunchAgent 配置"""
    try:
        plist = startup_manager.create_launchd_plist()
        
        return {
            "success": True,
            "plist": plist
        }
        
    except Exception as e:
        logger.error(f"生成plist失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计 API ====================

@router.get("/statistics/overview")
async def get_resource_overview():
    """获取资源统计概览"""
    try:
        resources = resource_monitor.get_system_resources()
        status = resource_monitor.check_resource_status(resources)
        available = resource_monitor.estimate_available_resources()
        
        # 获取所有服务状态
        services_status = startup_manager.get_all_services_status()
        running_count = sum(1 for s in services_status if s.get("running", False))
        
        overview = {
            "timestamp": resources.get("timestamp"),
            "system": {
                "cpu_percent": resources.get("cpu", {}).get("total_percent", 0),
                "memory_percent": resources.get("memory", {}).get("percent", 0),
                "memory_used_gb": resources.get("memory", {}).get("used_gb", 0),
                "memory_total_gb": resources.get("memory", {}).get("total_gb", 0)
            },
            "status": {
                "overall": status.get("overall"),
                "warnings_count": len(status.get("warnings", [])),
                "critical_count": len(status.get("critical", []))
            },
            "services": {
                "total": len(services_status),
                "running": running_count,
                "stopped": len(services_status) - running_count
            },
            "available": available
        }
        
        return {
            "success": True,
            "overview": overview
        }
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

