"""
Process Management API
流程管理API

根据需求2.2：运营与管理
功能：
1. 流程定义（需求2.2.1）
2. 全流程管理（需求2.2.2）
3. 流程进度可视化（需求2.2.3）
4. 异常分析改进（需求2.2.5）
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

# 修复相对导入问题 - T0006-3优化
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import get_db
from core.database_models import (
    BusinessProcess,
    ProcessInstance,
    ProcessTracking,
    ProcessException,
    ImprovementPlan,
    ProcessStatus,
)

router = APIRouter(prefix="/process", tags=["Process Management API"])


# ============ Pydantic Models ============

class ProcessDefinitionInput(BaseModel):
    """流程定义输入模型"""
    name: str
    description: Optional[str] = None
    process_type: Optional[str] = None
    stages: List[Dict[str, Any]]  # 流程阶段定义
    kpi_metrics: Optional[Dict[str, Any]] = None


class ProcessInstanceInput(BaseModel):
    """流程实例输入模型"""
    process_id: int
    instance_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessTrackingInput(BaseModel):
    """流程跟踪输入模型"""
    instance_id: int
    stage: str
    status: Optional[str] = None
    action: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None


class ProcessProgressResponse(BaseModel):
    """流程进度响应模型"""
    instance_id: int
    process_name: str
    current_stage: str
    status: str
    progress_percentage: float
    completed_stages: List[str]
    remaining_stages: List[str]
    timeline: List[Dict[str, Any]]
    estimated_completion: Optional[datetime] = None


class FullProcessFlowResponse(BaseModel):
    """全流程响应模型"""
    flow_stages: List[Dict[str, Any]]
    current_stage_index: int
    instances: List[Dict[str, Any]]
    progress: Dict[str, Any]


# ============ API Endpoints ============

@router.post("/define")
async def define_process(
    process: ProcessDefinitionInput,
    db: Session = Depends(get_db),
):
    """
    定义业务流程（需求2.2.1）
    
    功能：
    - 流程名、环节、作业内容定义
    - 流程跟踪、改进、KPI定义
    - 扩展接口
    
    Args:
        process: 流程定义
        db: 数据库会话
        
    Returns:
        创建的流程定义
    """
    try:
        business_process = BusinessProcess(
            name=process.name,
            description=process.description,
            process_type=process.process_type,
            stages=process.stages,
            kpi_metrics=process.kpi_metrics or {},
        )
        
        db.add(business_process)
        db.commit()
        db.refresh(business_process)
        
        return {
            "success": True,
            "process_id": business_process.id,
            "process_name": business_process.name,
            "message": "流程定义创建成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"流程定义失败: {str(e)}")


@router.post("/instance/create")
async def create_process_instance(
    instance: ProcessInstanceInput,
    db: Session = Depends(get_db),
):
    """
    创建流程实例（需求2.2.2）
    
    全流程管理的第一步：创建流程实例
    
    Args:
        instance: 流程实例输入
        db: 数据库会话
        
    Returns:
        创建的流程实例
    """
    try:
        # 验证流程定义存在
        process = db.query(BusinessProcess).filter(
            BusinessProcess.id == instance.process_id
        ).first()
        
        if not process:
            raise HTTPException(status_code=404, detail="流程定义不存在")

        # 创建流程实例
        process_instance = ProcessInstance(
            process_id=instance.process_id,
            instance_name=instance.instance_name or f"{process.name}_实例",
            status=ProcessStatus.PENDING,
            current_stage=process.stages[0]["name"] if process.stages else "初始",
            started_at=datetime.utcnow(),
            extra_metadata=instance.extra_metadata or {},
        )
        
        db.add(process_instance)
        db.commit()
        db.refresh(process_instance)
        
        return {
            "success": True,
            "instance_id": process_instance.id,
            "instance_name": process_instance.instance_name,
            "status": process_instance.status,
            "message": "流程实例创建成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建流程实例失败: {str(e)}")


@router.post("/instance/{instance_id}/track")
async def track_process(
    instance_id: int,
    tracking: ProcessTrackingInput,
    db: Session = Depends(get_db),
):
    """
    跟踪流程进度（需求2.2.2）
    
    记录流程执行情况，更新流程状态
    
    Args:
        instance_id: 流程实例ID
        tracking: 跟踪信息
        db: 数据库会话
        
    Returns:
        跟踪结果
    """
    try:
        # 验证流程实例存在
        instance = db.query(ProcessInstance).filter(
            ProcessInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail="流程实例不存在")

        # 创建跟踪记录
        tracking_record = ProcessTracking(
            instance_id=instance_id,
            stage=tracking.stage,
            status=tracking.status,
            action=tracking.action,
            operator=tracking.operator,
            notes=tracking.notes,
        )
        
        db.add(tracking_record)
        
        # 更新流程实例状态
        instance.current_stage = tracking.stage
        if tracking.status:
            instance.status = tracking.status
        
        # 如果状态为完成，设置完成时间
        if tracking.status == ProcessStatus.COMPLETED:
            instance.completed_at = datetime.utcnow()
        
        instance.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "tracking_id": tracking_record.id,
            "message": "流程跟踪记录创建成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"流程跟踪失败: {str(e)}")


@router.get("/instance/{instance_id}/progress", response_model=ProcessProgressResponse)
async def get_process_progress(
    instance_id: int,
    db: Session = Depends(get_db),
):
    """
    获取流程进度（需求2.2.3）
    
    功能：
    - 全流程业务推进进度
    - 子流程进度
    - 进度可视化数据
    
    Args:
        instance_id: 流程实例ID
        db: 数据库会话
        
    Returns:
        流程进度信息
    """
    try:
        # 获取流程实例
        instance = db.query(ProcessInstance).filter(
            ProcessInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail="流程实例不存在")

        # 获取流程定义
        process = db.query(BusinessProcess).filter(
            BusinessProcess.id == instance.process_id
        ).first()

        if not process:
            raise HTTPException(status_code=404, detail="流程定义不存在")

        # 获取所有阶段
        all_stages = [stage.get("name", "") for stage in process.stages]
        
        # 获取跟踪记录
        tracking_records = db.query(ProcessTracking).filter(
            ProcessTracking.instance_id == instance_id
        ).order_by(ProcessTracking.created_at).all()

        # 确定已完成的阶段
        completed_stages = []
        for record in tracking_records:
            if record.stage not in completed_stages and record.status == "completed":
                completed_stages.append(record.stage)

        # 计算进度百分比
        if all_stages:
            progress_percentage = (len(completed_stages) / len(all_stages)) * 100
        else:
            progress_percentage = 0.0

        # 剩余阶段
        remaining_stages = [s for s in all_stages if s not in completed_stages]

        # 时间线
        timeline = []
        for record in tracking_records:
            timeline.append({
                "stage": record.stage,
                "status": record.status,
                "action": record.action,
                "operator": record.operator,
                "timestamp": record.created_at.isoformat(),
            })

        return ProcessProgressResponse(
            instance_id=instance_id,
            process_name=process.name,
            current_stage=instance.current_stage,
            status=instance.status,
            progress_percentage=round(progress_percentage, 2),
            completed_stages=completed_stages,
            remaining_stages=remaining_stages,
            timeline=timeline,
            estimated_completion=instance.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取流程进度失败: {str(e)}")


@router.get("/full-flow", response_model=FullProcessFlowResponse)
async def get_full_process_flow(
    process_id: Optional[int] = Query(None, description="流程ID（可选）"),
    db: Session = Depends(get_db),
):
    """
    获取全流程管理视图（需求2.2.2）
    
    全流程业务管理：
    市场调研→客户开发→项目开发→投产管理→订单管理
    生产计划→物料需求→采购计划→到料→生产执行
    检验→入库→储存→交付→发运→回款
    
    Args:
        process_id: 流程ID（如果提供，返回特定流程）
        db: 数据库会话
        
    Returns:
        全流程视图
    """
    try:
        # 定义标准全流程阶段
        standard_flow_stages = [
            {"name": "市场调研", "order": 1},
            {"name": "客户开发", "order": 2},
            {"name": "项目开发", "order": 3},
            {"name": "投产管理", "order": 4},
            {"name": "订单管理", "order": 5},
            {"name": "生产计划", "order": 6},
            {"name": "物料需求", "order": 7},
            {"name": "采购计划", "order": 8},
            {"name": "到料", "order": 9},
            {"name": "生产执行", "order": 10},
            {"name": "检验", "order": 11},
            {"name": "入库", "order": 12},
            {"name": "储存", "order": 13},
            {"name": "交付", "order": 14},
            {"name": "发运", "order": 15},
            {"name": "回款", "order": 16},
        ]

        # 查询流程实例
        query = db.query(ProcessInstance)
        if process_id:
            query = query.filter(ProcessInstance.process_id == process_id)
        
        instances = query.all()

        # 构建实例数据
        instances_data = []
        for instance in instances:
            # 获取进度信息
            progress_query = db.query(ProcessTracking).filter(
                ProcessTracking.instance_id == instance.id
            )
            
            tracking_count = progress_query.count()
            completed_count = progress_query.filter(
                ProcessTracking.status == "completed"
            ).count()

            instances_data.append({
                "instance_id": instance.id,
                "instance_name": instance.instance_name,
                "status": instance.status,
                "current_stage": instance.current_stage,
                "progress": {
                    "total_stages": len(standard_flow_stages),
                    "completed_stages": completed_count,
                    "current_stage_index": tracking_count,
                },
            })

        # 计算整体进度
        if instances_data:
            total_stages = len(standard_flow_stages)
            avg_progress = sum(
                inst["progress"]["completed_stages"] / total_stages * 100
                for inst in instances_data
            ) / len(instances_data)
        else:
            avg_progress = 0.0

        return FullProcessFlowResponse(
            flow_stages=standard_flow_stages,
            current_stage_index=0,  # 可以根据实际情况计算
            instances=instances_data,
            progress={
                "average_progress": round(avg_progress, 2),
                "total_instances": len(instances_data),
                "active_instances": len([i for i in instances_data if i["status"] == "in_progress"]),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全流程视图失败: {str(e)}")


@router.get("/exceptions")
async def get_process_exceptions(
    instance_id: Optional[int] = Query(None),
    exception_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    获取流程异常（需求2.2.5）
    
    功能：
    - 异常收集和分析
    - 改进进度跟踪
    - 闭环监控
    
    Args:
        instance_id: 流程实例ID（可选）
        exception_level: 异常级别（可选）
        status: 异常状态（可选）
        db: 数据库会话
        
    Returns:
        异常列表
    """
    try:
        query = db.query(ProcessException)

        if instance_id:
            query = query.filter(ProcessException.instance_id == instance_id)
        if exception_level:
            query = query.filter(ProcessException.exception_level == exception_level)
        if status:
            query = query.filter(ProcessException.status == status)

        exceptions = query.order_by(ProcessException.detected_at.desc()).all()

        return {
            "success": True,
            "exceptions": [
                {
                    "id": exc.id,
                    "instance_id": exc.instance_id,
                    "exception_type": exc.exception_type,
                    "exception_level": exc.exception_level,
                    "description": exc.description,
                    "status": exc.status,
                    "detected_at": exc.detected_at.isoformat(),
                    "resolved_at": exc.resolved_at.isoformat() if exc.resolved_at else None,
                }
                for exc in exceptions
            ],
            "count": len(exceptions),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取流程异常失败: {str(e)}")


@router.post("/exceptions")
async def create_process_exception(
    instance_id: int = Body(...),
    exception_type: str = Body(...),
    exception_level: str = Body("info"),
    description: str = Body(...),
    db: Session = Depends(get_db),
):
    """
    创建流程异常记录（需求2.2.5）
    
    Args:
        instance_id: 流程实例ID
        exception_type: 异常类型
        exception_level: 异常级别
        description: 异常描述
        db: 数据库会话
        
    Returns:
        创建的异常记录
    """
    try:
        exception = ProcessException(
            instance_id=instance_id,
            exception_type=exception_type,
            exception_level=exception_level,
            description=description,
            status="open",
        )
        
        db.add(exception)
        db.commit()
        db.refresh(exception)
        
        return {
            "success": True,
            "exception_id": exception.id,
            "message": "流程异常记录创建成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建流程异常失败: {str(e)}")


@router.get("/improvements")
async def get_improvement_plans(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    获取改进计划（需求2.2.5）
    
    Args:
        status: 计划状态
        priority: 优先级
        db: 数据库会话
        
    Returns:
        改进计划列表
    """
    try:
        query = db.query(ImprovementPlan)

        if status:
            query = query.filter(ImprovementPlan.status == status)
        if priority:
            query = query.filter(ImprovementPlan.priority == priority)

        plans = query.order_by(ImprovementPlan.created_at.desc()).all()

        return {
            "success": True,
            "plans": [
                {
                    "id": plan.id,
                    "description": plan.description,
                    "priority": plan.priority,
                    "status": plan.status,
                    "progress": float(plan.progress),
                    "responsible": plan.responsible,
                    "planned_start": plan.planned_start.isoformat() if plan.planned_start else None,
                    "planned_end": plan.planned_end.isoformat() if plan.planned_end else None,
                }
                for plan in plans
            ],
            "count": len(plans),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取改进计划失败: {str(e)}")

