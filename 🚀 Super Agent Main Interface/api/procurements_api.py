#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T014 · 采购管理API

能力要求：
- 采购全生命周期（需求→寻源→下单→跟催→到货→入库）
- 25项能力清单（与ERP蓝图保持一致）
- 8维度分析（质量/成本/交付/安全/利润/效率/管理/技术）
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.super_agent_api import erp_process_service
from core.erp_process_service import BASE_STAGE_LIFECYCLES, DIMENSIONS

router = APIRouter(prefix="/api/procurements", tags=["ERP Procurement Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _risk_bucket(value: Optional[str]) -> str:
    if not value or value in ("无", "none", "无风险"):
        return "none"
    keywords = {
        "供应": "supply",
        "供应商": "supply",
        "交期": "delivery",
        "延期": "delivery",
        "质量": "quality",
        "不合格": "quality",
        "价格": "finance",
        "成本": "finance",
        "合同": "legal",
        "法律": "legal",
    }
    for key, bucket in keywords.items():
        if key in value:
            return bucket
    return "general"


def _procurements_source() -> List[Dict[str, Any]]:
    return erp_process_service.procurements


def _find_procurement(po_id: str) -> Optional[Dict[str, Any]]:
    for po in _procurements_source():
        if str(po.get("po_id")) == str(po_id):
            return po
    return None


class ProcurementItemInput(BaseModel):
    material_code: str
    material_name: str
    quantity: float = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    required_date: Optional[str] = None


class ProcurementCreateRequest(BaseModel):
    po_id: Optional[str] = Field(None, description="自定义采购单号（可选）")
    supplier: str
    category: Optional[str] = None
    amount: float = Field(..., ge=0)
    currency: str = "CNY"
    status: str = "planned"
    stage: Optional[str] = Field(None, description="采购阶段（需求/寻源/下单/跟催/到货）")
    eta: Optional[str] = Field(None, description="预计到货日期（ISO8601，如 2025-11-30）")
    risk: Optional[str] = None
    dimensions: Optional[Dict[str, float]] = None
    tags: List[str] = Field(default_factory=list)
    items: List[ProcurementItemInput] = Field(default_factory=list)


class ProcurementStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="新的采购状态")
    stage: Optional[str] = Field(None, description="采购阶段（需求/寻源/下单/跟催/到货）")
    risk: Optional[str] = None
    eta: Optional[str] = None
    note: Optional[str] = None


@router.get("/overview")
async def get_procurement_overview():
    """整体概览 + 8维度 + 25项能力"""
    view = erp_process_service.get_procurement_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("procurement")
    blueprint = erp_process_service.get_stage_blueprint("procurement")
    lifecycle = BASE_STAGE_LIFECYCLES.get("procurement", [])
    procurements = _procurements_source()

    status_counter = Counter(po.get("status", "unknown") for po in procurements)
    stage_counter = Counter(po.get("stage", "未定义") for po in procurements)
    risk_counter = Counter(_risk_bucket(po.get("risk")) for po in procurements)

    # 蓝图已自动扩展能力清单到25项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": view.get("summary", {}),
        "dimension_analysis": dimension_analysis,
        "lifecycle": [
            {
                "name": step,
                "completed": index < len(lifecycle) - 1,
                "sequence": index + 1,
            }
            for index, step in enumerate(lifecycle)
        ],
        "status_distribution": status_counter,
        "stage_distribution": stage_counter,
        "risk_heatmap": risk_counter,
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
    }


@router.get("/")
async def list_procurements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    stage: Optional[str] = None,
    supplier: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """采购单列表 + 统计"""
    procurements = _procurements_source()
    filtered: List[Dict[str, Any]] = []
    for po in procurements:
        if status and po.get("status") != status:
            continue
        if stage and po.get("stage") != stage:
            continue
        if supplier and po.get("supplier") != supplier:
            continue
        if q:
            text = f"{po.get('po_id','')}{po.get('supplier','')}{po.get('category','')}{po.get('material_code','')}{po.get('risk','')}"
            if q.lower() not in text.lower():
                continue
        filtered.append(po)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    status_counter = Counter(po.get("status", "unknown") for po in filtered)
    stage_counter = Counter(po.get("stage", "未定义") for po in filtered)
    supplier_counter = Counter(po.get("supplier", "未知") for po in filtered)

    amount_by_status = defaultdict(float)
    for po in filtered:
        amount_by_status[po.get("status", "unknown")] += float(po.get("amount", 0))

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "procurements": page_items,
        "status_distribution": status_counter,
        "stage_distribution": stage_counter,
        "supplier_distribution": supplier_counter,
        "amount_by_status": amount_by_status,
    }


@router.post("/")
async def create_procurement(payload: ProcurementCreateRequest):
    """创建采购单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    po_id = data.get("po_id") or f"PO-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    data["po_id"] = po_id
    data.setdefault("created_at", _now())
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    erp_process_service.procurements.append(data)
    return {
        "success": True,
        "procurement": data,
        "message": "采购单创建成功"
    }


@router.get("/{po_id}")
async def get_procurement_detail(po_id: str):
    """单个采购单 + 生命周期 + 8维度"""
    procurement = _find_procurement(po_id)
    if not procurement:
        raise HTTPException(status_code=404, detail="采购单不存在")

    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("procurement", [])
    status_mapping = {
        "planned": 0,
        "sourcing": 1,
        "sent": 2,
        "confirmed": 3,
        "in_transit": 4,
        "received": len(lifecycle_steps),
    }
    current_index = status_mapping.get(procurement.get("status"), 0)
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
    for dim, score in (procurement.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    insights = []
    if procurement.get("risk") and procurement["risk"] not in ("无", "none"):
        insights.append(f"⚠️ 风险提示：{procurement['risk']}")
    if procurement.get("status") in ("sent", "confirmed") and not procurement.get("eta"):
        insights.append("⏱️ 已下单但未设置预计到货日期")
    if procurement.get("status") == "received":
        insights.append("✅ 已到货，可进入入库流程")

    return {
        "success": True,
        "procurement": procurement,
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "insights": insights,
    }


@router.patch("/{po_id}/status")
async def update_procurement_status(po_id: str, payload: ProcurementStatusUpdateRequest):
    """更新采购单状态/阶段/风险"""
    procurement = _find_procurement(po_id)
    if not procurement:
        raise HTTPException(status_code=404, detail="采购单不存在")

    procurement["status"] = payload.status
    if payload.stage:
        procurement["stage"] = payload.stage
    if payload.risk is not None:
        procurement["risk"] = payload.risk
    if payload.eta:
        procurement["eta"] = payload.eta

    history = procurement.setdefault("status_history", [])
    history.append(
        {
            "to": payload.status,
            "stage": payload.stage or procurement.get("stage"),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    return {"success": True, "procurement": procurement}


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("procurement")
    procurements = _procurements_source()
    avg_dimension = defaultdict(list)
    for po in procurements:
        for dim, score in (po.get("dimensions") or {}).items():
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
        "procurement_sample_size": len(procurements),
    }


@router.get("/analytics/risk")
async def analyze_procurement_risk():
    """风险雷达"""
    procurements = _procurements_source()
    heatmap = Counter(_risk_bucket(po.get("risk")) for po in procurements)
    high_risk = [
        {
            "po_id": po.get("po_id"),
            "supplier": po.get("supplier"),
            "risk": po.get("risk"),
            "status": po.get("status"),
            "stage": po.get("stage"),
        }
        for po in procurements
        if po.get("risk") and po["risk"] not in ("无", "none")
    ][:10]

    return {"success": True, "heatmap": heatmap, "high_risk_procurements": high_risk}


@router.get("/analytics/supplier")
async def analyze_supplier_performance():
    """供应商绩效分析"""
    procurements = _procurements_source()
    supplier_stats = defaultdict(lambda: {"count": 0, "total_amount": 0.0, "risks": []})
    
    for po in procurements:
        supplier = po.get("supplier", "未知")
        supplier_stats[supplier]["count"] += 1
        supplier_stats[supplier]["total_amount"] += float(po.get("amount", 0))
        if po.get("risk") and po["risk"] not in ("无", "none"):
            supplier_stats[supplier]["risks"].append(po.get("risk"))

    performance = []
    for supplier, stats in supplier_stats.items():
        avg_amount = stats["total_amount"] / stats["count"] if stats["count"] > 0 else 0
        risk_rate = len(stats["risks"]) / stats["count"] if stats["count"] > 0 else 0
        performance.append({
            "supplier": supplier,
            "order_count": stats["count"],
            "total_amount": round(stats["total_amount"], 2),
            "avg_amount": round(avg_amount, 2),
            "risk_count": len(stats["risks"]),
            "risk_rate": round(risk_rate, 2),
            "performance_score": round((1 - risk_rate) * 100, 2),
        })
    
    performance.sort(key=lambda x: x["performance_score"], reverse=True)
    
    return {
        "success": True,
        "supplier_performance": performance,
        "total_suppliers": len(performance),
    }

