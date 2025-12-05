#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T019 · 售后服务API

能力要求：
- 售后全生命周期（受理→诊断→调度→现场/远程处理→复盘）
- 15项能力清单（与ERP蓝图保持一致）
- 8维度分析（质量/成本/交付/安全/利润/效率/管理/技术）
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.super_agent_api import erp_process_service
from core.erp_process_service import BASE_STAGE_LIFECYCLES, DIMENSIONS

router = APIRouter(prefix="/api/after-sales", tags=["ERP After-Sales Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _after_sales_status(status: str) -> str:
    """判断售后服务状态"""
    status_mapping = {
        "open": "待受理",
        "acknowledged": "已受理",
        "diagnosing": "诊断中",
        "scheduled": "已调度",
        "in_progress": "处理中",
        "monitoring": "监控中",
        "resolved": "已解决",
        "closed": "已关闭",
        "cancelled": "已取消",
    }
    return status_mapping.get(status, status)


def _after_sales_source() -> List[Dict[str, Any]]:
    return erp_process_service.after_sales


def _find_case(ticket_id: str) -> Optional[Dict[str, Any]]:
    for case in _after_sales_source():
        if str(case.get("ticket_id")) == str(ticket_id):
            return case
    return None


class AfterSalesCreateRequest(BaseModel):
    customer: str = Field(..., description="客户名称")
    order_id: Optional[str] = Field(None, description="关联订单号")
    issue: str = Field(..., description="问题描述")
    severity: str = Field("medium", description="严重程度（low/medium/high/critical）")
    sla: Optional[str] = Field(None, description="SLA要求（如 48h）")
    contact: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    location: Optional[str] = Field(None, description="服务地点")
    category: Optional[str] = Field(None, description="问题类别（维修/升级/咨询等）")


class AfterSalesUpdateRequest(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    sla: Optional[str] = None
    assignee: Optional[str] = Field(None, description="处理人")
    diagnosis: Optional[str] = Field(None, description="诊断结果")
    solution: Optional[str] = Field(None, description="解决方案")
    resolution_time: Optional[str] = Field(None, description="解决时间（ISO8601）")
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="客户满意度（1-5分）")
    cost: Optional[float] = Field(None, ge=0, description="服务成本（元）")
    note: Optional[str] = None


@router.get("/overview")
async def get_after_sales_overview():
    """整体概览 + 8维度 + 15项能力"""
    view = erp_process_service.get_after_sales_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("after_sales")
    blueprint = erp_process_service.get_stage_blueprint("after_sales")
    lifecycle = BASE_STAGE_LIFECYCLES.get("after_sales", [])
    cases = _after_sales_source()

    # 统计售后状态
    status_counter = Counter(case.get("status", "unknown") for case in cases)
    
    # 统计严重程度
    severity_counter = Counter(case.get("severity", "未知") for case in cases)
    
    # 统计问题类别
    category_counter = Counter(case.get("category", "未分类") for case in cases)
    
    # 计算SLA达成率
    closed_cases = [c for c in cases if c.get("status") == "closed"]
    sla_met = len([c for c in closed_cases if _is_sla_met(c)])
    sla_rate = (sla_met / len(closed_cases) * 100) if closed_cases else 0
    
    # 计算一次解决率
    resolved_cases = [c for c in cases if c.get("status") in ("resolved", "closed")]
    first_time_fixed = len([c for c in resolved_cases if c.get("resolution_count", 1) == 1])
    first_time_fix_rate = (first_time_fixed / len(resolved_cases) * 100) if resolved_cases else 0
    
    # 计算平均客户满意度
    satisfaction_scores = [c.get("customer_satisfaction") for c in cases if c.get("customer_satisfaction")]
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
    
    # 统计超SLA的案例
    sla_breached = len([c for c in cases if _is_sla_breached(c)])
    
    # 蓝图已自动扩展能力清单到15项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "sla_rate": round(sla_rate, 2),
            "first_time_fix_rate": round(first_time_fix_rate, 2),
            "avg_satisfaction": round(avg_satisfaction, 2),
            "sla_breached": sla_breached,
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
        "status_distribution": {_after_sales_status(k): v for k, v in status_counter.items()},
        "severity_distribution": severity_counter,
        "category_distribution": category_counter,
        "risk_heatmap": {
            "critical": len([c for c in cases if c.get("severity") == "critical"]),
            "sla_breached": sla_breached,
            "low_satisfaction": len([c for c in cases if c.get("customer_satisfaction", 5) < 3]),
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
    }


def _is_sla_met(case: Dict[str, Any]) -> bool:
    """判断SLA是否达成"""
    sla = case.get("sla")
    created_at = case.get("created_at")
    resolved_at = case.get("resolution_time") or case.get("resolved_at")
    if not sla or not created_at or not resolved_at:
        return True  # 无数据视为达成
    
    try:
        # 解析SLA（如 "48h"）
        sla_hours = int(sla.replace("h", "").replace("H", ""))
        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        resolved_date = datetime.fromisoformat(resolved_at.replace("Z", "+00:00"))
        elapsed_hours = (resolved_date - created_date).total_seconds() / 3600
        return elapsed_hours <= sla_hours
    except Exception:
        return True


def _is_sla_breached(case: Dict[str, Any]) -> bool:
    """判断SLA是否超时"""
    if case.get("status") in ("closed", "resolved", "cancelled"):
        return not _is_sla_met(case)
    
    sla = case.get("sla")
    created_at = case.get("created_at")
    if not sla or not created_at:
        return False
    
    try:
        sla_hours = int(sla.replace("h", "").replace("H", ""))
        created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elapsed_hours = (datetime.now(timezone.utc) - created_date).total_seconds() / 3600
        return elapsed_hours > sla_hours
    except Exception:
        return False


@router.get("/")
async def list_after_sales_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    customer: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """售后服务列表 + 统计"""
    cases = _after_sales_source()
    filtered: List[Dict[str, Any]] = []
    
    for case in cases:
        # 状态筛选
        if status and case.get("status") != status:
            continue
        
        # 严重程度筛选
        if severity and case.get("severity") != severity:
            continue
        
        # 类别筛选
        if category and case.get("category") != category:
            continue
        
        # 客户筛选
        if customer and case.get("customer") != customer:
            continue
        
        # 关键词搜索
        if q:
            text = f"{case.get('ticket_id','')}{case.get('customer','')}{case.get('issue','')}{case.get('order_id','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(case)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个案例添加状态标签和SLA标记
    for case in page_items:
        case["status_label"] = _after_sales_status(case.get("status", "unknown"))
        case["is_sla_breached"] = _is_sla_breached(case)
        case["is_sla_met"] = _is_sla_met(case) if case.get("status") in ("closed", "resolved") else None
        # 计算处理时长
        if case.get("created_at") and case.get("resolution_time"):
            try:
                created = datetime.fromisoformat(case["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(case["resolution_time"].replace("Z", "+00:00"))
                case["resolution_hours"] = round((resolved - created).total_seconds() / 3600, 1)
            except Exception:
                case["resolution_hours"] = None
        else:
            case["resolution_hours"] = None

    status_counter = Counter(case.get("status", "unknown") for case in filtered)
    severity_counter = Counter(case.get("severity", "未知") for case in filtered)
    
    open_cases = len([c for c in filtered if c.get("status") not in ("closed", "cancelled")])

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "cases": page_items,
        "status_distribution": {_after_sales_status(k): v for k, v in status_counter.items()},
        "severity_distribution": severity_counter,
        "open_cases": open_cases,
    }


@router.post("/")
async def create_after_sales_case(payload: AfterSalesCreateRequest):
    """创建售后服务工单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    ticket_id = f"AS-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    data["ticket_id"] = ticket_id
    data.setdefault("status", "open")
    data.setdefault("severity", "medium")
    data.setdefault("sla", "48h")
    data.setdefault("resolution_count", 0)
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.after_sales.append(data)
    
    return {
        "success": True,
        "case": data,
        "message": "售后服务工单创建成功"
    }


@router.get("/{ticket_id}")
async def get_after_sales_detail(ticket_id: str):
    """单个售后工单 + 生命周期 + 8维度"""
    case = _find_case(ticket_id)
    if not case:
        raise HTTPException(status_code=404, detail="售后服务工单不存在")

    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("after_sales", [])
    status_mapping = {
        "open": 0,
        "acknowledged": 1,
        "diagnosing": 2,
        "scheduled": 3,
        "in_progress": 4,
        "monitoring": 4,
        "resolved": len(lifecycle_steps),
        "closed": len(lifecycle_steps),
        "cancelled": 0,
    }
    current_index = status_mapping.get(case.get("status"), 0)
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
    for dim, score in (case.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    # SLA信息
    sla_info = {
        "sla": case.get("sla", "N/A"),
        "is_breached": _is_sla_breached(case),
        "is_met": _is_sla_met(case) if case.get("status") in ("closed", "resolved") else None,
    }
    
    # 计算处理时长
    resolution_hours = None
    if case.get("created_at") and case.get("resolution_time"):
        try:
            created = datetime.fromisoformat(case["created_at"].replace("Z", "+00:00"))
            resolved = datetime.fromisoformat(case["resolution_time"].replace("Z", "+00:00"))
            resolution_hours = round((resolved - created).total_seconds() / 3600, 1)
        except Exception:
            pass
    
    insights = []
    if _is_sla_breached(case):
        insights.append("⚠️ SLA已超时，建议优先处理")
    if case.get("severity") == "critical":
        insights.append("🔴 严重问题，需要立即处理")
    if case.get("status") == "resolved" and not case.get("customer_satisfaction"):
        insights.append("📋 问题已解决，建议收集客户满意度")
    if case.get("customer_satisfaction") and case.get("customer_satisfaction", 5) < 3:
        insights.append("😞 客户满意度较低，建议回访改进")
    if case.get("resolution_count", 0) > 1:
        insights.append("🔄 多次处理，建议分析根因")

    return {
        "success": True,
        "case": case,
        "status_label": _after_sales_status(case.get("status", "unknown")),
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "sla_info": sla_info,
        "resolution_hours": resolution_hours,
        "insights": insights,
    }


@router.patch("/{ticket_id}")
async def update_after_sales_case(ticket_id: str, payload: AfterSalesUpdateRequest):
    """更新售后工单（状态/诊断/解决方案等）"""
    case = _find_case(ticket_id)
    if not case:
        raise HTTPException(status_code=404, detail="售后服务工单不存在")

    # 更新字段
    old_status = case.get("status")
    if payload.status:
        case["status"] = payload.status
        # 如果是解决状态，记录解决时间和次数
        if payload.status in ("resolved", "closed") and old_status not in ("resolved", "closed"):
            case["resolution_time"] = payload.resolution_time or _now()
            case["resolved_at"] = payload.resolution_time or _now()
            case["resolution_count"] = case.get("resolution_count", 0) + 1
    if payload.severity:
        case["severity"] = payload.severity
    if payload.sla:
        case["sla"] = payload.sla
    if payload.assignee:
        case["assignee"] = payload.assignee
    if payload.diagnosis:
        case["diagnosis"] = payload.diagnosis
    if payload.solution:
        case["solution"] = payload.solution
    if payload.resolution_time:
        case["resolution_time"] = payload.resolution_time
        case["resolved_at"] = payload.resolution_time
    if payload.customer_satisfaction:
        case["customer_satisfaction"] = payload.customer_satisfaction
    if payload.cost is not None:
        case["cost"] = payload.cost

    # 记录变更历史
    history = case.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "from_status": old_status,
            "to_status": case.get("status"),
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    case["updated_at"] = _now()
    
    return {"success": True, "case": case}


@router.post("/{ticket_id}/resolve")
async def resolve_case(ticket_id: str, solution: str, customer_satisfaction: Optional[int] = None):
    """解决售后工单"""
    case = _find_case(ticket_id)
    if not case:
        raise HTTPException(status_code=404, detail="售后服务工单不存在")

    case["status"] = "resolved"
    case["solution"] = solution
    case["resolution_time"] = _now()
    case["resolved_at"] = _now()
    case["resolution_count"] = case.get("resolution_count", 0) + 1
    
    if customer_satisfaction:
        case["customer_satisfaction"] = customer_satisfaction
    
    case["updated_at"] = _now()
    
    return {
        "success": True,
        "case": case,
        "message": "工单已标记为已解决"
    }


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("after_sales")
    cases = _after_sales_source()
    avg_dimension = defaultdict(list)
    for case in cases:
        for dim, score in (case.get("dimensions") or {}).items():
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
        "case_sample_size": len(cases),
    }


@router.get("/analytics/sla")
async def analyze_sla_performance():
    """SLA绩效分析"""
    cases = _after_sales_source()
    closed_cases = [c for c in cases if c.get("status") in ("closed", "resolved")]
    
    # SLA达成率
    sla_met_count = len([c for c in closed_cases if _is_sla_met(c)])
    sla_rate = (sla_met_count / len(closed_cases) * 100) if closed_cases else 0
    
    # SLA超时率
    all_cases_sla_breached = len([c for c in cases if _is_sla_breached(c)])
    sla_breach_rate = (all_cases_sla_breached / len(cases) * 100) if cases else 0
    
    # 按严重程度统计SLA
    severity_sla = defaultdict(lambda: {"total": 0, "met": 0, "breached": 0})
    for case in closed_cases:
        severity = case.get("severity", "未知")
        severity_sla[severity]["total"] += 1
        if _is_sla_met(case):
            severity_sla[severity]["met"] += 1
        else:
            severity_sla[severity]["breached"] += 1
    
    severity_stats = []
    for severity, stats in severity_sla.items():
        met_rate = (stats["met"] / stats["total"] * 100) if stats["total"] > 0 else 0
        severity_stats.append({
            "severity": severity,
            "total_cases": stats["total"],
            "sla_met": stats["met"],
            "sla_breached": stats["breached"],
            "sla_rate": round(met_rate, 2),
        })
    
    severity_stats.sort(key=lambda x: x["sla_rate"], reverse=True)
    
    return {
        "success": True,
        "overall_sla_rate": round(sla_rate, 2),
        "overall_sla_breach_rate": round(sla_breach_rate, 2),
        "severity_sla_stats": severity_stats,
        "total_closed_cases": len(closed_cases),
        "sla_met_cases": sla_met_count,
        "sla_breached_cases": all_cases_sla_breached,
    }


@router.get("/analytics/satisfaction")
async def analyze_customer_satisfaction():
    """客户满意度分析"""
    cases = _after_sales_source()
    
    # 统计满意度分布
    satisfaction_scores = [c.get("customer_satisfaction") for c in cases if c.get("customer_satisfaction")]
    satisfaction_distribution = Counter(satisfaction_scores)
    
    # 计算平均满意度
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
    
    # 计算一次解决率和满意度的关系
    resolved_cases = [c for c in cases if c.get("status") in ("resolved", "closed")]
    first_time_fixed = [c for c in resolved_cases if c.get("resolution_count", 1) == 1]
    first_time_fixed_satisfaction = [c.get("customer_satisfaction") for c in first_time_fixed if c.get("customer_satisfaction")]
    avg_first_time_satisfaction = sum(first_time_fixed_satisfaction) / len(first_time_fixed_satisfaction) if first_time_fixed_satisfaction else 0
    
    # 按客户统计满意度
    customer_satisfaction = defaultdict(lambda: {"count": 0, "total_score": 0})
    for case in cases:
        if case.get("customer_satisfaction"):
            customer = case.get("customer", "未知")
            customer_satisfaction[customer]["count"] += 1
            customer_satisfaction[customer]["total_score"] += case["customer_satisfaction"]
    
    customer_stats = []
    for customer, stats in customer_satisfaction.items():
        avg = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
        customer_stats.append({
            "customer": customer,
            "cases": stats["count"],
            "avg_satisfaction": round(avg, 2),
        })
    
    customer_stats.sort(key=lambda x: x["avg_satisfaction"], reverse=True)
    
    return {
        "success": True,
        "avg_satisfaction": round(avg_satisfaction, 2),
        "avg_first_time_satisfaction": round(avg_first_time_satisfaction, 2),
        "satisfaction_distribution": dict(satisfaction_distribution),
        "customer_satisfaction": customer_stats[:20],  # 返回前20个客户
        "total_rated_cases": len(satisfaction_scores),
    }


@router.get("/analytics/resolution")
async def analyze_resolution_performance():
    """解决绩效分析（一次解决率、平均处理时长等）"""
    cases = _after_sales_source()
    resolved_cases = [c for c in cases if c.get("status") in ("resolved", "closed")]
    
    # 一次解决率
    first_time_fixed = len([c for c in resolved_cases if c.get("resolution_count", 1) == 1])
    first_time_fix_rate = (first_time_fixed / len(resolved_cases) * 100) if resolved_cases else 0
    
    # 平均处理时长
    resolution_times = []
    for case in resolved_cases:
        if case.get("created_at") and case.get("resolution_time"):
            try:
                created = datetime.fromisoformat(case["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(case["resolution_time"].replace("Z", "+00:00"))
                hours = (resolved - created).total_seconds() / 3600
                resolution_times.append(hours)
            except Exception:
                pass
    
    avg_resolution_hours = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    # 按问题类别统计
    category_stats = defaultdict(lambda: {"count": 0, "first_time": 0, "total_hours": 0.0})
    for case in resolved_cases:
        category = case.get("category", "未分类")
        category_stats[category]["count"] += 1
        if case.get("resolution_count", 1) == 1:
            category_stats[category]["first_time"] += 1
        if case.get("created_at") and case.get("resolution_time"):
            try:
                created = datetime.fromisoformat(case["created_at"].replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(case["resolution_time"].replace("Z", "+00:00"))
                hours = (resolved - created).total_seconds() / 3600
                category_stats[category]["total_hours"] += hours
            except Exception:
                pass
    
    category_performance = []
    for category, stats in category_stats.items():
        first_time_rate = (stats["first_time"] / stats["count"] * 100) if stats["count"] > 0 else 0
        avg_hours = stats["total_hours"] / stats["count"] if stats["count"] > 0 else 0
        category_performance.append({
            "category": category,
            "total_cases": stats["count"],
            "first_time_fix_rate": round(first_time_rate, 2),
            "avg_resolution_hours": round(avg_hours, 1),
        })
    
    category_performance.sort(key=lambda x: x["first_time_fix_rate"], reverse=True)
    
    return {
        "success": True,
        "overall_first_time_fix_rate": round(first_time_fix_rate, 2),
        "avg_resolution_hours": round(avg_resolution_hours, 1),
        "category_performance": category_performance,
        "total_resolved_cases": len(resolved_cases),
        "first_time_fixed_cases": first_time_fixed,
    }

