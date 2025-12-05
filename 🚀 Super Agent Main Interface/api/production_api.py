#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T016 · 生产管理API

能力要求：
- 生产全生命周期（计划→排程→执行→反馈→结案）
- 40项能力清单（与ERP蓝图保持一致）
- 8维度分析（质量/成本/交付/安全/利润/效率/管理/技术）
- 集成质量管理功能
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.super_agent_api import erp_process_service
from core.erp_process_service import BASE_STAGE_LIFECYCLES, DIMENSIONS

router = APIRouter(prefix="/api/production", tags=["ERP Production Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _production_status(status: str) -> str:
    """判断生产状态：计划中/排程中/执行中/已完成/已暂停"""
    status_mapping = {
        "planned": "计划中",
        "scheduled": "排程中",
        "ready": "就绪",
        "executing": "执行中",
        "paused": "已暂停",
        "completed": "已完成",
        "cancelled": "已取消",
    }
    return status_mapping.get(status, status)


def _production_source() -> List[Dict[str, Any]]:
    return erp_process_service.production_jobs


def _quality_source() -> List[Dict[str, Any]]:
    return erp_process_service.quality_checks


def _find_production_job(job_id: str) -> Optional[Dict[str, Any]]:
    for job in _production_source():
        if str(job.get("job_id")) == str(job_id):
            return job
    return None


def _find_quality_check(lot_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not lot_id:
        return None
    for qc in _quality_source():
        if str(qc.get("lot_id")) == str(lot_id):
            return qc
    return None


class ProductionJobInput(BaseModel):
    order_id: str
    line: str = Field(..., description="产线编号")
    quantity: float = Field(..., gt=0, description="计划数量")
    start_plan: Optional[str] = Field(None, description="计划开始日期（ISO8601）")
    end_plan: Optional[str] = Field(None, description="计划结束日期（ISO8601）")
    priority: Optional[str] = "normal"
    product_code: Optional[str] = None
    product_name: Optional[str] = None


class ProductionJobUpdateRequest(BaseModel):
    status: Optional[str] = None
    completed: Optional[float] = Field(None, ge=0, description="已完成数量")
    quantity: Optional[float] = Field(None, gt=0, description="计划数量（调整）")
    start_plan: Optional[str] = None
    end_plan: Optional[str] = None
    line: Optional[str] = None
    note: Optional[str] = None


class ProductionProgressRequest(BaseModel):
    completed: float = Field(..., ge=0, description="已完成数量")
    defects: Optional[float] = Field(0, ge=0, description="不良品数量")
    note: Optional[str] = None


@router.get("/overview")
async def get_production_overview():
    """整体概览 + 8维度 + 40项能力 + 质量集成"""
    view = erp_process_service.get_production_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("production")
    blueprint = erp_process_service.get_stage_blueprint("production")
    lifecycle = BASE_STAGE_LIFECYCLES.get("production", [])
    jobs = _production_source()
    quality_checks = _quality_source()

    # 统计生产状态
    status_counter = Counter(job.get("status", "unknown") for job in jobs)
    
    # 统计产线
    line_counter = Counter(job.get("line", "未知") for job in jobs)
    
    # 计算总计划数量和完成数量
    total_quantity = sum(job.get("quantity", 0) for job in jobs)
    total_completed = sum(job.get("completed", 0) for job in jobs)
    completion_rate = (total_completed / total_quantity * 100) if total_quantity > 0 else 0
    
    # 计算OEE（设备综合效率）简化算法
    executing_jobs = [job for job in jobs if job.get("status") == "executing"]
    oee = 0.85 if executing_jobs else 0.0  # 简化算法
    
    # 质量统计
    quality_pending = len([qc for qc in quality_checks if qc.get("status") not in ("completed", "passed")])
    quality_total = len(quality_checks)
    
    # 蓝图已自动扩展能力清单到40项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "total_quantity": round(total_quantity, 2),
            "total_completed": round(total_completed, 2),
            "completion_rate": round(completion_rate, 2),
            "oee": round(oee, 2),
            "quality_pending": quality_pending,
            "quality_total": quality_total,
        },
        "dimension_analysis": dimension_analysis,
        "lifecycle": [
            {
                "name": step,
                "completed": index < len(lifecycle) - 1,
                "sequence": index + 1,
            }
            for index, step in enumerate(lifecycle)
        ],
        "status_distribution": {_production_status(k): v for k, v in status_counter.items()},
        "line_distribution": line_counter,
        "risk_heatmap": {
            "delayed": len([job for job in jobs if _is_delayed(job)]),
            "low_progress": len([job for job in jobs if _is_low_progress(job)]),
            "quality_issues": quality_pending,
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
        "quality_summary": {
            "total_checks": quality_total,
            "pending_checks": quality_pending,
            "passed_rate": _calculate_passed_rate(quality_checks),
        },
    }


def _is_delayed(job: Dict[str, Any]) -> bool:
    """判断是否延期"""
    if job.get("status") in ("completed", "cancelled"):
        return False
    end_plan = job.get("end_plan")
    if not end_plan:
        return False
    try:
        end_date = datetime.fromisoformat(end_plan.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > end_date
    except Exception:
        return False


def _is_low_progress(job: Dict[str, Any]) -> bool:
    """判断进度是否偏低"""
    if job.get("status") not in ("executing", "ready"):
        return False
    quantity = job.get("quantity", 0)
    completed = job.get("completed", 0)
    if quantity <= 0:
        return False
    progress = completed / quantity
    start_plan = job.get("start_plan")
    if not start_plan:
        return False
    try:
        start_date = datetime.fromisoformat(start_plan.replace("Z", "+00:00"))
        total_days = (datetime.now(timezone.utc) - start_date).days
        expected_progress = min(1.0, total_days / 30.0) if total_days > 0 else 0
        return progress < expected_progress * 0.8
    except Exception:
        return False


def _calculate_passed_rate(quality_checks: List[Dict[str, Any]]) -> float:
    """计算质检通过率"""
    if not quality_checks:
        return 0.0
    completed = [qc for qc in quality_checks if qc.get("status") in ("completed", "passed", "failed")]
    if not completed:
        return 0.0
    passed = len([qc for qc in completed if qc.get("status") == "passed"])
    return round((passed / len(completed)) * 100, 2) if completed else 0.0


@router.get("/")
async def list_production_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    line: Optional[str] = None,
    order_id: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """生产工单列表 + 统计"""
    jobs = _production_source()
    filtered: List[Dict[str, Any]] = []
    
    for job in jobs:
        # 状态筛选
        if status and job.get("status") != status:
            continue
        
        # 产线筛选
        if line and job.get("line") != line:
            continue
        
        # 订单筛选
        if order_id and job.get("order_id") != order_id:
            continue
        
        # 关键词搜索
        if q:
            text = f"{job.get('job_id','')}{job.get('order_id','')}{job.get('line','')}{job.get('product_code','')}{job.get('product_name','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(job)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个工单添加进度和状态标签
    for job in page_items:
        quantity = job.get("quantity", 0)
        completed = job.get("completed", 0)
        job["progress"] = round((completed / quantity * 100), 2) if quantity > 0 else 0
        job["status_label"] = _production_status(job.get("status", "unknown"))
        job["is_delayed"] = _is_delayed(job)
        job["is_low_progress"] = _is_low_progress(job)
        # 关联质量检查
        job["quality_check"] = _find_quality_check(job.get("qc_lot_id"))

    status_counter = Counter(job.get("status", "unknown") for job in filtered)
    line_counter = Counter(job.get("line", "未知") for job in filtered)
    
    total_quantity = sum(job.get("quantity", 0) for job in filtered)
    total_completed = sum(job.get("completed", 0) for job in filtered)

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "jobs": page_items,
        "status_distribution": {_production_status(k): v for k, v in status_counter.items()},
        "line_distribution": line_counter,
        "total_quantity": round(total_quantity, 2),
        "total_completed": round(total_completed, 2),
    }


@router.post("/")
async def create_production_job(payload: ProductionJobInput):
    """创建生产工单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    job_id = f"MO-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    data["job_id"] = job_id
    data.setdefault("status", "planned")
    data.setdefault("completed", 0)
    data.setdefault("priority", "normal")
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.production_jobs.append(data)
    
    return {
        "success": True,
        "job": data,
        "message": "生产工单创建成功"
    }


@router.get("/{job_id}")
async def get_production_job_detail(job_id: str):
    """单个生产工单 + 生命周期 + 8维度 + 质量集成"""
    job = _find_production_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="生产工单不存在")

    # 计算进度和效率指标
    quantity = job.get("quantity", 0)
    completed = job.get("completed", 0)
    progress = round((completed / quantity * 100), 2) if quantity > 0 else 0
    
    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("production", [])
    status_mapping = {
        "planned": 0,
        "scheduled": 1,
        "ready": 2,
        "executing": 3,
        "paused": 2,
        "completed": len(lifecycle_steps),
        "cancelled": 0,
    }
    current_index = status_mapping.get(job.get("status"), 0)
    lifecycle = []
    for idx, step in enumerate(lifecycle_steps, start=1):
        lifecycle.append(
            {
                "stage": step,
                "sequence": idx,
                "status": "completed"
                if idx <= current_index
                else "current"
                if idx == current_index + 1
                else "pending",
            }
        )

    dimensions = []
    for dim, score in (job.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    # 关联质量检查
    quality_check = _find_quality_check(job.get("qc_lot_id"))
    
    insights = []
    if _is_delayed(job):
        insights.append("⚠️ 工单已延期，建议加快进度")
    if _is_low_progress(job):
        insights.append("🟡 生产进度偏低，建议检查瓶颈")
    if job.get("status") == "executing" and progress >= 95:
        insights.append("✅ 接近完成，可准备结案")
    if quality_check:
        qc_status = quality_check.get("status")
        if qc_status not in ("passed", "completed"):
            insights.append(f"🔍 关联质检：{qc_status}，请关注质量状态")
        defects = quality_check.get("defects", 0)
        samples = quality_check.get("samples", 0)
        if defects > 0 and samples > 0:
            defect_rate = (defects / samples) * 100
            insights.append(f"📊 不良率：{defect_rate:.2f}%")

    return {
        "success": True,
        "job": job,
        "progress": progress,
        "status_label": _production_status(job.get("status", "unknown")),
        "is_delayed": _is_delayed(job),
        "is_low_progress": _is_low_progress(job),
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "quality_check": quality_check,
        "insights": insights,
    }


@router.patch("/{job_id}")
async def update_production_job(job_id: str, payload: ProductionJobUpdateRequest):
    """更新生产工单（状态/进度/计划等）"""
    job = _find_production_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="生产工单不存在")

    # 更新字段
    if payload.status:
        job["status"] = payload.status
    if payload.completed is not None:
        job["completed"] = payload.completed
    if payload.quantity is not None:
        job["quantity"] = payload.quantity
    if payload.start_plan:
        job["start_plan"] = payload.start_plan
    if payload.end_plan:
        job["end_plan"] = payload.end_plan
    if payload.line:
        job["line"] = payload.line

    # 记录变更历史
    history = job.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    job["updated_at"] = _now()
    
    return {"success": True, "job": job}


@router.post("/{job_id}/progress")
async def update_production_progress(job_id: str, payload: ProductionProgressRequest):
    """更新生产进度（报工）"""
    job = _find_production_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="生产工单不存在")

    # 更新完成数量
    job["completed"] = payload.completed
    quantity = job.get("quantity", 0)
    
    # 如果完成数量达到计划数量，自动结案
    if payload.completed >= quantity and job.get("status") == "executing":
        job["status"] = "completed"
    
    # 记录报工历史
    progress_history = job.setdefault("progress_history", [])
    progress_history.append(
        {
            "completed": payload.completed,
            "defects": payload.defects,
            "defect_rate": round((payload.defects / payload.completed * 100), 2) if payload.completed > 0 else 0,
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    
    # 如果存在不良品，触发质量检查提醒
    if payload.defects > 0:
        insights = job.setdefault("insights", [])
        insights.append(f"⚠️ 发现不良品 {payload.defects} 件，建议启动质量检查")
    
    job["updated_at"] = _now()
    
    return {
        "success": True,
        "job": job,
        "progress": round((payload.completed / quantity * 100), 2) if quantity > 0 else 0,
    }


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("production")
    jobs = _production_source()
    avg_dimension = defaultdict(list)
    for job in jobs:
        for dim, score in (job.get("dimensions") or {}).items():
            avg_dimension[dim].append(score)

    avg_dimension = {
        dim: round(sum(values) / len(values), 3)
        for dim, values in avg_dimension.items()
        if values
    }

    return {
        "success": True,
        "dimension_analysis": dimension_analysis,
        "dimension_average": avg_dimension,
        "job_sample_size": len(jobs),
    }


@router.get("/analytics/efficiency")
async def analyze_production_efficiency():
    """生产效率分析（OEE、良品率、计划达成率等）"""
    jobs = _production_source()
    executing_jobs = [job for job in jobs if job.get("status") == "executing"]
    completed_jobs = [job for job in jobs if job.get("status") == "completed"]
    
    # OEE计算（简化）
    total_quantity = sum(job.get("quantity", 0) for job in executing_jobs)
    total_completed = sum(job.get("completed", 0) for job in executing_jobs)
    availability = 0.9  # 设备可用率
    performance = (total_completed / total_quantity) if total_quantity > 0 else 0
    quality_rate = 0.95  # 良品率（简化）
    oee = availability * performance * quality_rate
    
    # 计划达成率
    planned_total = sum(job.get("quantity", 0) for job in completed_jobs)
    actual_total = sum(job.get("completed", 0) for job in completed_jobs)
    achievement_rate = (actual_total / planned_total * 100) if planned_total > 0 else 0
    
    # 按产线统计
    line_stats = defaultdict(lambda: {"total": 0, "completed": 0, "jobs": 0})
    for job in jobs:
        line = job.get("line", "未知")
        line_stats[line]["total"] += job.get("quantity", 0)
        line_stats[line]["completed"] += job.get("completed", 0)
        line_stats[line]["jobs"] += 1
    
    line_efficiency = []
    for line, stats in line_stats.items():
        efficiency = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        line_efficiency.append({
            "line": line,
            "jobs": stats["jobs"],
            "planned": stats["total"],
            "completed": stats["completed"],
            "efficiency": round(efficiency, 2),
        })
    
    line_efficiency.sort(key=lambda x: x["efficiency"], reverse=True)
    
    return {
        "success": True,
        "oee": round(oee * 100, 2),
        "availability": round(availability * 100, 2),
        "performance": round(performance * 100, 2),
        "quality_rate": round(quality_rate * 100, 2),
        "achievement_rate": round(achievement_rate, 2),
        "line_efficiency": line_efficiency,
    }


@router.get("/analytics/quality")
async def analyze_production_quality():
    """生产质量分析（集成质量模块）"""
    jobs = _production_source()
    quality_checks = _quality_source()
    
    # 统计质检状态
    qc_status_counter = Counter(qc.get("status", "unknown") for qc in quality_checks)
    
    # 计算不良率
    total_samples = sum(qc.get("samples", 0) for qc in quality_checks)
    total_defects = sum(qc.get("defects", 0) for qc in quality_checks)
    defect_rate = (total_defects / total_samples * 100) if total_samples > 0 else 0
    
    # 计算通过率
    passed_rate = _calculate_passed_rate(quality_checks)
    
    # 按工单关联质量数据
    job_quality = []
    for job in jobs:
        qc = _find_quality_check(job.get("qc_lot_id"))
        if qc:
            samples = qc.get("samples", 0)
            defects = qc.get("defects", 0)
            job_defect_rate = (defects / samples * 100) if samples > 0 else 0
            job_quality.append({
                "job_id": job.get("job_id"),
                "order_id": job.get("order_id"),
                "line": job.get("line"),
                "qc_lot_id": qc.get("lot_id"),
                "samples": samples,
                "defects": defects,
                "defect_rate": round(job_defect_rate, 2),
                "status": qc.get("status"),
            })
    
    return {
        "success": True,
        "qc_status_distribution": dict(qc_status_counter),
        "total_samples": total_samples,
        "total_defects": total_defects,
        "defect_rate": round(defect_rate, 2),
        "passed_rate": passed_rate,
        "job_quality": job_quality[:20],  # 返回前20条
    }

