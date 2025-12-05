#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T017 · 质量管理API（集成在生产）

能力要求：
- 质量全生命周期（计划→采样→检测→判定→纠正）
- SPC统计分析（Cp/Cpk、趋势线）
- 6σ分析（DPMO、Sigma Level）
- 不良品处理（8D报告、纠正措施）
- 与生产管理集成
"""
from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.super_agent_api import erp_process_service
from core.erp_process_service import BASE_STAGE_LIFECYCLES, DIMENSIONS

router = APIRouter(prefix="/api/quality", tags=["ERP Quality Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _quality_status(status: str) -> str:
    """判断质量状态"""
    status_mapping = {
        "scheduled": "已计划",
        "sampling": "采样中",
        "testing": "检测中",
        "in_progress": "进行中",
        "reviewing": "判定中",
        "passed": "合格",
        "failed": "不合格",
        "completed": "已完成",
        "cancelled": "已取消",
    }
    return status_mapping.get(status, status)


def _quality_source() -> List[Dict[str, Any]]:
    return erp_process_service.quality_checks


def _production_source() -> List[Dict[str, Any]]:
    return erp_process_service.production_jobs


def _find_quality_check(lot_id: str) -> Optional[Dict[str, Any]]:
    for qc in _quality_source():
        if str(qc.get("lot_id")) == str(lot_id):
            return qc
    return None


def _find_production_job(job_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not job_id:
        return None
    for job in _production_source():
        if str(job.get("job_id")) == str(job_id):
            return job
    return None


class QualityCheckInput(BaseModel):
    order_id: Optional[str] = None
    job_id: Optional[str] = Field(None, description="关联生产工单号")
    method: str = Field(..., description="检测方法（SPC/6σ/AQL等）")
    samples: int = Field(..., gt=0, description="抽样数量")
    planned_date: Optional[str] = Field(None, description="计划检测日期（ISO8601）")
    inspector: Optional[str] = None
    standard: Optional[str] = Field(None, description="质量标准")
    spec_lower: Optional[float] = Field(None, description="规格下限")
    spec_upper: Optional[float] = Field(None, description="规格上限")
    target: Optional[float] = Field(None, description="目标值")


class QualityCheckUpdateRequest(BaseModel):
    status: Optional[str] = None
    samples: Optional[int] = Field(None, gt=0)
    defects: Optional[int] = Field(None, ge=0, description="不良品数量")
    test_results: Optional[List[float]] = Field(None, description="检测结果数据（用于SPC分析）")
    defect_details: Optional[List[Dict[str, Any]]] = Field(None, description="不良品明细")
    passed: Optional[bool] = None
    note: Optional[str] = None


class DefectActionRequest(BaseModel):
    action_type: str = Field(..., description="措施类型（8D/5W2H/纠正措施等）")
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    responsible: Optional[str] = None
    due_date: Optional[str] = None
    note: Optional[str] = None


@router.get("/overview")
async def get_quality_overview():
    """整体概览 + 8维度 + 20项能力 + 生产集成"""
    view = erp_process_service.get_quality_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("quality_check")
    blueprint = erp_process_service.get_stage_blueprint("quality_check")
    lifecycle = BASE_STAGE_LIFECYCLES.get("quality_check", [])
    quality_checks = _quality_source()
    production_jobs = _production_source()

    # 统计质量状态
    status_counter = Counter(qc.get("status", "unknown") for qc in quality_checks)
    
    # 统计检测方法
    method_counter = Counter(qc.get("method", "未知") for qc in quality_checks)
    
    # 计算总抽样数和不良品数
    total_samples = sum(qc.get("samples", 0) for qc in quality_checks)
    total_defects = sum(qc.get("defects", 0) for qc in quality_checks)
    defect_rate = (total_defects / total_samples * 100) if total_samples > 0 else 0
    
    # 计算通过率
    completed = [qc for qc in quality_checks if qc.get("status") in ("passed", "failed", "completed")]
    passed = len([qc for qc in completed if qc.get("status") == "passed"])
    passed_rate = (passed / len(completed) * 100) if completed else 0
    
    # 统计待处理的不良品
    pending_defects = len([qc for qc in quality_checks if qc.get("defects", 0) > 0 and qc.get("status") not in ("completed", "passed")])
    
    # 统计关联生产工单的数量
    jobs_with_qc = len([job for job in production_jobs if job.get("qc_lot_id")])
    
    # 蓝图已自动扩展能力清单到20项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "total_checks": len(quality_checks),
            "total_samples": total_samples,
            "total_defects": total_defects,
            "defect_rate": round(defect_rate, 2),
            "passed_rate": round(passed_rate, 2),
            "pending_defects": pending_defects,
            "jobs_with_qc": jobs_with_qc,
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
        "status_distribution": {_quality_status(k): v for k, v in status_counter.items()},
        "method_distribution": method_counter,
        "risk_heatmap": {
            "high_defect_rate": len([qc for qc in quality_checks if _calculate_defect_rate(qc) > 5]),
            "pending_review": len([qc for qc in quality_checks if qc.get("status") == "reviewing"]),
            "failed": len([qc for qc in quality_checks if qc.get("status") == "failed"]),
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
        "production_integration": {
            "total_jobs": len(production_jobs),
            "jobs_with_qc": jobs_with_qc,
            "integration_rate": round((jobs_with_qc / len(production_jobs) * 100), 2) if production_jobs else 0,
        },
    }


def _calculate_defect_rate(qc: Dict[str, Any]) -> float:
    """计算不良率"""
    samples = qc.get("samples", 0)
    defects = qc.get("defects", 0)
    if samples <= 0:
        return 0.0
    return (defects / samples) * 100


@router.get("/")
async def list_quality_checks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    method: Optional[str] = None,
    order_id: Optional[str] = None,
    job_id: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """质量检查列表 + 统计"""
    quality_checks = _quality_source()
    filtered: List[Dict[str, Any]] = []
    
    for qc in quality_checks:
        # 状态筛选
        if status and qc.get("status") != status:
            continue
        
        # 方法筛选
        if method and qc.get("method") != method:
            continue
        
        # 订单筛选
        if order_id and qc.get("order_id") != order_id:
            continue
        
        # 工单筛选
        if job_id and qc.get("job_id") != job_id:
            continue
        
        # 关键词搜索
        if q:
            text = f"{qc.get('lot_id','')}{qc.get('order_id','')}{qc.get('job_id','')}{qc.get('method','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(qc)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个质检添加不良率和状态标签
    for qc in page_items:
        qc["defect_rate"] = round(_calculate_defect_rate(qc), 2)
        qc["status_label"] = _quality_status(qc.get("status", "unknown"))
        # 关联生产工单
        qc["production_job"] = _find_production_job(qc.get("job_id"))

    status_counter = Counter(qc.get("status", "unknown") for qc in filtered)
    method_counter = Counter(qc.get("method", "未知") for qc in filtered)
    
    total_samples = sum(qc.get("samples", 0) for qc in filtered)
    total_defects = sum(qc.get("defects", 0) for qc in filtered)

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "quality_checks": page_items,
        "status_distribution": {_quality_status(k): v for k, v in status_counter.items()},
        "method_distribution": method_counter,
        "total_samples": total_samples,
        "total_defects": total_defects,
        "overall_defect_rate": round((total_defects / total_samples * 100), 2) if total_samples > 0 else 0,
    }


@router.post("/")
async def create_quality_check(payload: QualityCheckInput):
    """创建质量检查（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    lot_id = f"QC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(_quality_source()) + 1:02d}"
    data["lot_id"] = lot_id
    data.setdefault("status", "scheduled")
    data.setdefault("defects", 0)
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.quality_checks.append(data)
    
    # 如果关联了生产工单，更新工单的 qc_lot_id
    if data.get("job_id"):
        job = _find_production_job(data["job_id"])
        if job:
            job["qc_lot_id"] = lot_id
    
    return {
        "success": True,
        "quality_check": data,
        "message": "质量检查创建成功"
    }


@router.get("/{lot_id}")
async def get_quality_check_detail(lot_id: str):
    """单个质量检查 + 生命周期 + 8维度 + SPC/6σ分析 + 生产集成"""
    qc = _find_quality_check(lot_id)
    if not qc:
        raise HTTPException(status_code=404, detail="质量检查不存在")

    # 计算不良率
    defect_rate = _calculate_defect_rate(qc)
    
    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("quality_check", [])
    status_mapping = {
        "scheduled": 0,
        "sampling": 1,
        "testing": 2,
        "in_progress": 2,
        "reviewing": 3,
        "passed": 4,
        "failed": 3,
        "completed": len(lifecycle_steps),
        "cancelled": 0,
    }
    current_index = status_mapping.get(qc.get("status"), 0)
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
    for dim, score in (qc.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    # SPC分析（如果检测方法是SPC且有检测数据）
    spc_analysis = None
    if qc.get("method") == "SPC" and qc.get("test_results"):
        spc_analysis = _calculate_spc(qc.get("test_results", []), qc.get("spec_lower"), qc.get("spec_upper"), qc.get("target"))

    # 6σ分析
    sixsigma_analysis = None
    if qc.get("method") == "6σ" or qc.get("samples", 0) > 0:
        sixsigma_analysis = _calculate_sixsigma(qc.get("samples", 0), qc.get("defects", 0))

    # 关联生产工单
    production_job = _find_production_job(qc.get("job_id"))
    
    insights = []
    if defect_rate > 5:
        insights.append("⚠️ 不良率超过5%，建议立即启动纠正措施")
    if defect_rate > 0 and defect_rate <= 5:
        insights.append("🟡 存在不良品，建议加强监控")
    if qc.get("status") == "failed":
        insights.append("🔴 判定不合格，需要启动8D流程")
    if spc_analysis and spc_analysis.get("cpk", 0) < 1.0:
        insights.append("⚠️ Cpk值低于1.0，过程能力不足")
    if sixsigma_analysis and sixsigma_analysis.get("sigma_level", 0) < 3.0:
        insights.append("⚠️ Sigma Level低于3.0，需要改进")

    return {
        "success": True,
        "quality_check": qc,
        "defect_rate": round(defect_rate, 2),
        "status_label": _quality_status(qc.get("status", "unknown")),
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "spc_analysis": spc_analysis,
        "sixsigma_analysis": sixsigma_analysis,
        "production_job": production_job,
        "insights": insights,
    }


def _calculate_spc(test_results: List[float], spec_lower: Optional[float], spec_upper: Optional[float], target: Optional[float]) -> Optional[Dict[str, Any]]:
    """计算SPC统计指标（Cp、Cpk、均值、标准差等）"""
    if not test_results or len(test_results) < 2:
        return None
    
    if spec_lower is None or spec_upper is None:
        return None
    
    mean = statistics.mean(test_results)
    std_dev = statistics.stdev(test_results) if len(test_results) > 1 else 0
    usl = spec_upper  # 规格上限
    lsl = spec_lower  # 规格下限
    target_value = target or ((usl + lsl) / 2)
    
    # Cp计算：过程能力指数
    cp = (usl - lsl) / (6 * std_dev) if std_dev > 0 else 0
    
    # Cpu计算：上限能力指数
    cpu = (usl - mean) / (3 * std_dev) if std_dev > 0 else 0
    
    # Cpl计算：下限能力指数
    cpl = (mean - lsl) / (3 * std_dev) if std_dev > 0 else 0
    
    # Cpk计算：过程能力指数（取Cpu和Cpl的较小值）
    cpk = min(cpu, cpl) if std_dev > 0 else 0
    
    # 目标偏移
    target_offset = abs(mean - target_value)
    
    # 合格率（假设正态分布）
    if std_dev > 0:
        z_usl = (usl - mean) / std_dev
        z_lsl = (lsl - mean) / std_dev
        # 简化计算：使用标准正态分布CDF近似
        # 这里使用简化公式
        yield_rate = max(0, min(100, 100 * (1 - abs(z_usl) - abs(z_lsl)) / 6))
    else:
        yield_rate = 100 if lsl <= mean <= usl else 0
    
    return {
        "mean": round(mean, 4),
        "std_dev": round(std_dev, 4),
        "cp": round(cp, 4),
        "cpu": round(cpu, 4),
        "cpl": round(cpl, 4),
        "cpk": round(cpk, 4),
        "target": target_value,
        "target_offset": round(target_offset, 4),
        "yield_rate": round(yield_rate, 2),
        "usl": usl,
        "lsl": lsl,
        "sample_count": len(test_results),
    }


def _calculate_sixsigma(samples: int, defects: int) -> Optional[Dict[str, Any]]:
    """计算6σ指标（DPMO、Sigma Level、合格率等）"""
    if samples <= 0:
        return None
    
    # DPMO计算：每百万机会缺陷数
    dpmo = (defects / samples) * 1_000_000
    
    # 合格率
    yield_rate = ((samples - defects) / samples) * 100
    
    # Sigma Level计算（简化算法）
    # 使用标准正态分布的反函数近似
    dpmo_normalized = max(1, min(dpmo, 500000))  # 限制范围
    # 简化公式：Sigma Level ≈ (NORMSINV(1 - DPMO/1000000) + 1.5)
    # 这里使用查找表近似
    sigma_level = _dpmo_to_sigma_level(dpmo)
    
    # 缺陷率
    defect_rate = (defects / samples) * 100
    
    return {
        "samples": samples,
        "defects": defects,
        "dpmo": round(dpmo, 2),
        "defect_rate": round(defect_rate, 4),
        "yield_rate": round(yield_rate, 4),
        "sigma_level": round(sigma_level, 2),
        "quality_level": _sigma_level_to_quality(sigma_level),
    }


def _dpmo_to_sigma_level(dpmo: float) -> float:
    """将DPMO转换为Sigma Level（简化查找表）"""
    # Sigma Level查找表（简化）
    lookup_table = {
        0: 6.0,
        3.4: 6.0,
        233: 5.0,
        6210: 4.0,
        66807: 3.0,
        308537: 2.0,
        690000: 1.0,
    }
    
    for threshold, sigma in sorted(lookup_table.items(), reverse=True):
        if dpmo >= threshold:
            return sigma
    
    return 0.0


def _sigma_level_to_quality(sigma_level: float) -> str:
    """将Sigma Level转换为质量等级"""
    if sigma_level >= 6.0:
        return "世界级"
    elif sigma_level >= 5.0:
        return "优秀"
    elif sigma_level >= 4.0:
        return "良好"
    elif sigma_level >= 3.0:
        return "一般"
    else:
        return "需改进"


@router.patch("/{lot_id}")
async def update_quality_check(lot_id: str, payload: QualityCheckUpdateRequest):
    """更新质量检查（状态/结果/不良品等）"""
    qc = _find_quality_check(lot_id)
    if not qc:
        raise HTTPException(status_code=404, detail="质量检查不存在")

    # 更新字段
    if payload.status:
        qc["status"] = payload.status
    if payload.samples is not None:
        qc["samples"] = payload.samples
    if payload.defects is not None:
        qc["defects"] = payload.defects
    if payload.test_results is not None:
        qc["test_results"] = payload.test_results
    if payload.defect_details is not None:
        qc["defect_details"] = payload.defect_details
    if payload.passed is not None:
        qc["status"] = "passed" if payload.passed else "failed"

    # 记录变更历史
    history = qc.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    qc["updated_at"] = _now()
    
    # 如果判定不合格，自动触发不良品处理流程
    if qc.get("status") == "failed" or (qc.get("defects", 0) > 0 and qc.get("status") not in ("passed", "completed")):
        insights = qc.setdefault("insights", [])
        insights.append("🔴 发现不良品，建议启动8D流程")
    
    return {"success": True, "quality_check": qc}


@router.post("/{lot_id}/defect-action")
async def create_defect_action(lot_id: str, payload: DefectActionRequest):
    """创建不良品处理措施（8D/5W2H等）"""
    qc = _find_quality_check(lot_id)
    if not qc:
        raise HTTPException(status_code=404, detail="质量检查不存在")

    # 创建不良品处理记录
    action = {
        "action_id": f"DA-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "action_type": payload.action_type,
        "root_cause": payload.root_cause,
        "corrective_action": payload.corrective_action,
        "preventive_action": payload.preventive_action,
        "responsible": payload.responsible,
        "due_date": payload.due_date,
        "status": "open",
        "created_at": _now(),
        "note": payload.note,
    }
    
    # 保存到质检记录
    actions = qc.setdefault("defect_actions", [])
    actions.append(action)
    
    # 更新质检状态
    if qc.get("status") not in ("passed", "completed"):
        qc["status"] = "reviewing"
    
    qc["updated_at"] = _now()
    
    return {
        "success": True,
        "action": action,
        "quality_check": qc,
        "message": "不良品处理措施创建成功"
    }


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("quality_check")
    quality_checks = _quality_source()
    avg_dimension = defaultdict(list)
    for qc in quality_checks:
        for dim, score in (qc.get("dimensions") or {}).items():
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
        "quality_check_sample_size": len(quality_checks),
    }


@router.get("/analytics/spc")
async def analyze_spc():
    """SPC统计分析"""
    quality_checks = _quality_source()
    spc_checks = [qc for qc in quality_checks if qc.get("method") == "SPC" and qc.get("test_results")]
    
    if not spc_checks:
        return {
            "success": True,
            "message": "暂无SPC检测数据",
            "spc_summary": None,
        }
    
    spc_results = []
    for qc in spc_checks:
        spc_analysis = _calculate_spc(
            qc.get("test_results", []),
            qc.get("spec_lower"),
            qc.get("spec_upper"),
            qc.get("target")
        )
        if spc_analysis:
            spc_results.append({
                "lot_id": qc.get("lot_id"),
                "order_id": qc.get("order_id"),
                "job_id": qc.get("job_id"),
                **spc_analysis,
            })
    
    # 统计平均Cpk
    avg_cpk = statistics.mean([r["cpk"] for r in spc_results]) if spc_results else 0
    
    return {
        "success": True,
        "spc_summary": {
            "total_checks": len(spc_checks),
            "valid_checks": len(spc_results),
            "avg_cp": round(statistics.mean([r["cp"] for r in spc_results]), 4) if spc_results else 0,
            "avg_cpk": round(avg_cpk, 4),
            "process_capability": "优秀" if avg_cpk >= 1.33 else "良好" if avg_cpk >= 1.0 else "一般" if avg_cpk >= 0.67 else "不足",
        },
        "spc_details": spc_results[:20],  # 返回前20条
    }


@router.get("/analytics/sixsigma")
async def analyze_sixsigma():
    """6σ分析统计"""
    quality_checks = _quality_source()
    
    sixsigma_results = []
    for qc in quality_checks:
        if qc.get("samples", 0) > 0:
            sixsigma_analysis = _calculate_sixsigma(qc.get("samples", 0), qc.get("defects", 0))
            if sixsigma_analysis:
                sixsigma_results.append({
                    "lot_id": qc.get("lot_id"),
                    "order_id": qc.get("order_id"),
                    "job_id": qc.get("job_id"),
                    "method": qc.get("method"),
                    **sixsigma_analysis,
                })
    
    if not sixsigma_results:
        return {
            "success": True,
            "message": "暂无6σ检测数据",
            "sixsigma_summary": None,
        }
    
    # 统计平均Sigma Level
    avg_sigma_level = statistics.mean([r["sigma_level"] for r in sixsigma_results])
    
    # 统计质量等级分布
    quality_levels = Counter(r["quality_level"] for r in sixsigma_results)
    
    # 统计平均DPMO
    avg_dpmo = statistics.mean([r["dpmo"] for r in sixsigma_results])
    
    return {
        "success": True,
        "sixsigma_summary": {
            "total_checks": len(sixsigma_results),
            "avg_dpmo": round(avg_dpmo, 2),
            "avg_sigma_level": round(avg_sigma_level, 2),
            "avg_yield_rate": round(statistics.mean([r["yield_rate"] for r in sixsigma_results]), 2),
            "quality_level_distribution": dict(quality_levels),
        },
        "sixsigma_details": sixsigma_results[:20],  # 返回前20条
    }


@router.get("/analytics/defect-trend")
async def analyze_defect_trend():
    """不良品趋势分析"""
    quality_checks = _quality_source()
    
    # 按日期分组统计
    date_groups = defaultdict(lambda: {"samples": 0, "defects": 0, "count": 0})
    for qc in quality_checks:
        created_at = qc.get("created_at", _now())
        date_key = created_at[:10] if len(created_at) >= 10 else "unknown"
        date_groups[date_key]["samples"] += qc.get("samples", 0)
        date_groups[date_key]["defects"] += qc.get("defects", 0)
        date_groups[date_key]["count"] += 1
    
    trend_data = []
    for date_key in sorted(date_groups.keys()):
        group = date_groups[date_key]
        defect_rate = (group["defects"] / group["samples"] * 100) if group["samples"] > 0 else 0
        trend_data.append({
            "date": date_key,
            "checks": group["count"],
            "samples": group["samples"],
            "defects": group["defects"],
            "defect_rate": round(defect_rate, 2),
        })
    
    # 计算趋势（简单线性回归斜率）
    if len(trend_data) >= 2:
        rates = [d["defect_rate"] for d in trend_data]
        trend_slope = statistics.mean(rates[-3:]) - statistics.mean(rates[:3]) if len(rates) >= 3 else 0
        trend_direction = "上升" if trend_slope > 0.1 else "下降" if trend_slope < -0.1 else "平稳"
    else:
        trend_direction = "数据不足"
    
    return {
        "success": True,
        "trend_data": trend_data[-30:],  # 返回最近30天
        "trend_direction": trend_direction,
        "current_defect_rate": trend_data[-1]["defect_rate"] if trend_data else 0,
    }

