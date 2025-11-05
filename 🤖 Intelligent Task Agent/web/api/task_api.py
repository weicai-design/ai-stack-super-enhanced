"""
智能任务代理 - API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# 假设我们有这些模块
from planning.task_planner import TaskPlanner
from execution.task_executor import TaskExecutor
from monitoring.task_monitor import TaskMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 初始化核心组件
task_monitor = TaskMonitor()
task_executor = TaskExecutor(monitor=task_monitor)
task_planner = TaskPlanner()


# ==================== Pydantic 模型 ====================

class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str
    description: str
    task_type: str = "general"
    priority: int = 5
    config: Dict[str, Any] = {}
    schedule_config: Optional[Dict[str, Any]] = None


class TaskStepCreate(BaseModel):
    """创建任务步骤"""
    order: int
    name: str
    description: Optional[str] = None
    step_type: str
    config: Dict[str, Any] = {}
    dependencies: List[int] = []


class TaskExecuteRequest(BaseModel):
    """执行任务请求"""
    task_id: int
    trigger_type: str = "manual"
    trigger_info: Dict[str, Any] = {}


class TaskUpdateRequest(BaseModel):
    """更新任务请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# ==================== 任务管理 API ====================

@router.post("/create")
async def create_task(task: TaskCreate):
    """
    创建新任务
    
    根据任务描述自动生成执行计划
    """
    try:
        logger.info(f"创建任务: {task.name}")
        
        # 使用任务规划引擎生成执行计划
        execution_plan = task_planner.create_task_plan(
            task.description,
            task.dict()
        )
        
        # 这里应该保存到数据库，现在先返回规划结果
        task_data = {
            "id": 1,  # 模拟生成的ID
            "name": task.name,
            "description": task.description,
            "type": task.task_type,
            "priority": task.priority,
            "status": "pending",
            "execution_plan": execution_plan,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "任务创建成功",
            "task": task_data
        }
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    获取任务列表
    
    支持按状态、类型筛选
    """
    try:
        # 模拟任务列表
        tasks = [
            {
                "id": 1,
                "name": "每日数据采集任务",
                "type": "data_collection",
                "status": "running",
                "priority": 7,
                "progress": 45.0,
                "created_at": "2025-11-03T14:00:00",
                "next_run": "2025-11-04T14:00:00"
            },
            {
                "id": 2,
                "name": "市场趋势分析",
                "type": "data_analysis",
                "status": "completed",
                "priority": 8,
                "progress": 100.0,
                "created_at": "2025-11-03T10:00:00",
                "completed_at": "2025-11-03T10:15:00"
            },
            {
                "id": 3,
                "name": "内容生成与发布",
                "type": "content_generation",
                "status": "pending",
                "priority": 6,
                "progress": 0.0,
                "created_at": "2025-11-03T12:00:00",
                "scheduled_time": "2025-11-03T18:00:00"
            }
        ]
        
        # 简单的筛选
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if task_type:
            tasks = [t for t in tasks if t["type"] == task_type]
        
        return {
            "success": True,
            "total": len(tasks),
            "tasks": tasks[offset:offset+limit]
        }
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: int):
    """获取任务详情"""
    try:
        # 模拟任务详情
        task = {
            "id": task_id,
            "name": "市场趋势分析",
            "description": "分析最近一周的市场趋势，生成分析报告",
            "type": "data_analysis",
            "status": "completed",
            "priority": 8,
            "progress": 100.0,
            "config": {
                "data_source": "market_api",
                "analysis_period": "7d"
            },
            "steps": [
                {
                    "order": 1,
                    "name": "加载数据",
                    "type": "data_loading",
                    "status": "completed",
                    "duration": 65
                },
                {
                    "order": 2,
                    "name": "数据预处理",
                    "type": "preprocessing",
                    "status": "completed",
                    "duration": 125
                },
                {
                    "order": 3,
                    "name": "执行分析",
                    "type": "analysis",
                    "status": "completed",
                    "duration": 195
                },
                {
                    "order": 4,
                    "name": "生成报告",
                    "type": "reporting",
                    "status": "completed",
                    "duration": 92
                }
            ],
            "created_at": "2025-11-03T10:00:00",
            "started_at": "2025-11-03T10:00:05",
            "completed_at": "2025-11-03T10:15:22",
            "result": {
                "success": True,
                "report_path": "/reports/market_trend_20251103.pdf",
                "insights": [
                    "市场整体呈上升趋势",
                    "科技股表现强劲",
                    "消费类股票震荡"
                ]
            }
        }
        
        return {
            "success": True,
            "task": task
        }
        
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=404, detail="任务不存在")


@router.put("/{task_id}")
async def update_task(task_id: int, update: TaskUpdateRequest):
    """更新任务"""
    try:
        logger.info(f"更新任务 {task_id}")
        
        # 这里应该更新数据库
        return {
            "success": True,
            "message": "任务更新成功",
            "task_id": task_id,
            "updated_fields": {k: v for k, v in update.dict().items() if v is not None}
        }
        
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    """删除任务"""
    try:
        logger.info(f"删除任务 {task_id}")
        
        # 这里应该从数据库删除
        return {
            "success": True,
            "message": "任务删除成功",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 任务执行 API ====================

@router.post("/{task_id}/execute")
async def execute_task(task_id: int, background_tasks: BackgroundTasks):
    """
    执行任务
    
    在后台异步执行任务
    """
    try:
        logger.info(f"开始执行任务 {task_id}")
        
        # 模拟从数据库获取任务
        task = {
            "id": task_id,
            "name": "测试任务",
            "type": "general",
            "steps": [
                {
                    "order": 1,
                    "name": "初始化",
                    "type": "initialization",
                    "estimated_duration": 30
                },
                {
                    "order": 2,
                    "name": "执行",
                    "type": "execution",
                    "estimated_duration": 180,
                    "dependencies": [1]
                },
                {
                    "order": 3,
                    "name": "清理",
                    "type": "cleanup",
                    "estimated_duration": 15,
                    "dependencies": [2]
                }
            ]
        }
        
        # 在后台执行任务
        background_tasks.add_task(task_executor.execute_task, task)
        
        return {
            "success": True,
            "message": "任务已提交执行",
            "task_id": task_id,
            "status": "submitted"
        }
        
    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/pause")
async def pause_task(task_id: int):
    """暂停任务"""
    try:
        logger.info(f"暂停任务 {task_id}")
        
        return {
            "success": True,
            "message": "任务已暂停",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/resume")
async def resume_task(task_id: int):
    """恢复任务"""
    try:
        logger.info(f"恢复任务 {task_id}")
        
        return {
            "success": True,
            "message": "任务已恢复",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: int):
    """取消任务"""
    try:
        logger.info(f"取消任务 {task_id}")
        
        return {
            "success": True,
            "message": "任务已取消",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 监控 API ====================

@router.get("/monitoring/active")
async def get_active_tasks():
    """获取活跃任务监控数据"""
    try:
        active_tasks = task_monitor.get_active_tasks()
        
        return {
            "success": True,
            "count": len(active_tasks),
            "tasks": active_tasks
        }
        
    except Exception as e:
        logger.error(f"获取活跃任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/system")
async def get_system_metrics():
    """获取系统监控指标"""
    try:
        metrics = task_monitor.get_system_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts")
async def get_alerts(count: int = 10):
    """获取最近告警"""
    try:
        alerts = task_monitor.get_recent_alerts(count)
        
        return {
            "success": True,
            "count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"获取告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/history")
async def get_performance_history(count: int = 50):
    """获取性能历史"""
    try:
        history = task_monitor.get_performance_history(count)
        
        return {
            "success": True,
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"获取性能历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 任务模板 API ====================

@router.get("/templates")
async def list_templates():
    """获取任务模板列表"""
    try:
        templates = [
            {
                "id": 1,
                "name": "每日数据采集",
                "category": "data_collection",
                "description": "每日定时采集目标网站数据",
                "usage_count": 152,
                "success_rate": 0.97
            },
            {
                "id": 2,
                "name": "市场分析报告",
                "category": "data_analysis",
                "description": "生成市场趋势分析报告",
                "usage_count": 89,
                "success_rate": 0.94
            },
            {
                "id": 3,
                "name": "内容创作发布",
                "category": "content_generation",
                "description": "AI内容创作并发布到多平台",
                "usage_count": 234,
                "success_rate": 0.91
            }
        ]
        
        return {
            "success": True,
            "total": len(templates),
            "templates": templates
        }
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/create_task")
async def create_task_from_template(template_id: int, config: Dict[str, Any] = {}):
    """从模板创建任务"""
    try:
        logger.info(f"从模板 {template_id} 创建任务")
        
        return {
            "success": True,
            "message": "任务创建成功",
            "task_id": 1
        }
        
    except Exception as e:
        logger.error(f"从模板创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计 API ====================

@router.get("/statistics/overview")
async def get_statistics_overview():
    """获取统计概览"""
    try:
        stats = {
            "total_tasks": 156,
            "running_tasks": 3,
            "completed_today": 24,
            "failed_today": 2,
            "success_rate": 0.92,
            "avg_duration_seconds": 285,
            "task_types": {
                "data_collection": 45,
                "data_analysis": 38,
                "content_generation": 52,
                "monitoring": 12,
                "trading": 9
            },
            "recent_executions": [
                {
                    "task_name": "每日数据采集",
                    "duration": 320,
                    "success": True,
                    "completed_at": "2025-11-03T20:15:00"
                },
                {
                    "task_name": "市场分析",
                    "duration": 245,
                    "success": True,
                    "completed_at": "2025-11-03T19:50:00"
                }
            ]
        }
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

