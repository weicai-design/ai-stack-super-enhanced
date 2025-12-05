#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T018 · 物流管理API

能力要求：
- 物流全生命周期（装运准备→干线运输→清关/交接→签收）
- 20项能力清单（与ERP蓝图保持一致）
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

router = APIRouter(prefix="/api/logistics", tags=["ERP Logistics Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _logistics_status(status: str) -> str:
    """判断物流状态"""
    status_mapping = {
        "ready": "待发运",
        "packing": "打包中",
        "picked_up": "已提货",
        "in_transit": "运输中",
        "customs": "清关中",
        "in_delivery": "配送中",
        "delivered": "已签收",
        "completed": "已完成",
        "cancelled": "已取消",
        "exception": "异常",
    }
    return status_mapping.get(status, status)


def _logistics_source() -> List[Dict[str, Any]]:
    return erp_process_service.logistics


def _find_shipment(shipment_id: str) -> Optional[Dict[str, Any]]:
    for shipment in _logistics_source():
        if str(shipment.get("shipment_id")) == str(shipment_id):
            return shipment
    return None


class ShipmentItemInput(BaseModel):
    product_code: str
    product_name: str
    quantity: float = Field(..., ge=0)
    weight: Optional[float] = Field(None, ge=0, description="重量（kg）")
    volume: Optional[float] = Field(None, ge=0, description="体积（m³）")
    value: Optional[float] = Field(None, ge=0, description="价值（元）")


class LogisticsCreateRequest(BaseModel):
    order_id: str = Field(..., description="订单号")
    carrier: str = Field(..., description="承运商")
    transport_mode: Optional[str] = Field(None, description="运输方式（海运/空运/陆运/多式联运）")
    origin: Optional[str] = Field(None, description="起运地")
    destination: Optional[str] = Field(None, description="目的地")
    eta: Optional[str] = Field(None, description="预计到达时间（ISO8601）")
    cost: Optional[float] = Field(None, ge=0, description="物流成本（元）")
    insurance: Optional[float] = Field(None, ge=0, description="保险费用（元）")
    customs_cost: Optional[float] = Field(None, ge=0, description="清关费用（元）")
    priority: Optional[str] = "normal"
    items: List[ShipmentItemInput] = Field(default_factory=list)


class LogisticsUpdateRequest(BaseModel):
    status: Optional[str] = None
    carrier: Optional[str] = None
    transport_mode: Optional[str] = None
    eta: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    insurance: Optional[float] = Field(None, ge=0)
    customs_cost: Optional[float] = Field(None, ge=0)
    current_location: Optional[str] = None
    milestones: Optional[List[str]] = None
    tracking_number: Optional[str] = None
    note: Optional[str] = None


@router.get("/overview")
async def get_logistics_overview():
    """整体概览 + 8维度 + 20项能力"""
    view = erp_process_service.get_logistics_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("delivery")
    blueprint = erp_process_service.get_stage_blueprint("delivery")
    lifecycle = BASE_STAGE_LIFECYCLES.get("delivery", [])
    shipments = _logistics_source()

    # 统计物流状态
    status_counter = Counter(shipment.get("status", "unknown") for shipment in shipments)
    
    # 统计承运商
    carrier_counter = Counter(shipment.get("carrier", "未知") for shipment in shipments)
    
    # 统计运输方式
    transport_mode_counter = Counter(shipment.get("transport_mode", "未知") for shipment in shipments)
    
    # 计算总成本和准时交付率
    total_cost = sum(shipment.get("cost", 0) for shipment in shipments)
    total_insurance = sum(shipment.get("insurance", 0) for shipment in shipments)
    total_customs = sum(shipment.get("customs_cost", 0) for shipment in shipments)
    
    # 计算准时交付率（简化算法）
    delivered = [s for s in shipments if s.get("status") in ("delivered", "completed")]
    on_time = len([s for s in delivered if _is_on_time(s)])
    on_time_rate = (on_time / len(delivered) * 100) if delivered else 0
    
    # 在途货物数量
    in_transit = len([s for s in shipments if s.get("status") == "in_transit"])
    
    # 蓝图已自动扩展能力清单到20项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "total_cost": round(total_cost, 2),
            "total_insurance": round(total_insurance, 2),
            "total_customs": round(total_customs, 2),
            "total_landed_cost": round(total_cost + total_insurance + total_customs, 2),
            "on_time_rate": round(on_time_rate, 2),
            "in_transit": in_transit,
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
        "status_distribution": {_logistics_status(k): v for k, v in status_counter.items()},
        "carrier_distribution": carrier_counter,
        "transport_mode_distribution": transport_mode_counter,
        "risk_heatmap": {
            "delayed": len([s for s in shipments if _is_delayed(s)]),
            "exception": len([s for s in shipments if s.get("status") == "exception"]),
            "high_cost": len([s for s in shipments if s.get("cost", 0) > 50000]),
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
    }


def _is_delayed(shipment: Dict[str, Any]) -> bool:
    """判断是否延期"""
    if shipment.get("status") in ("delivered", "completed", "cancelled"):
        return False
    eta = shipment.get("eta")
    if not eta:
        return False
    try:
        eta_date = datetime.fromisoformat(eta.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > eta_date
    except Exception:
        return False


def _is_on_time(shipment: Dict[str, Any]) -> bool:
    """判断是否准时交付"""
    eta = shipment.get("eta")
    delivered_at = shipment.get("delivered_at")
    if not eta or not delivered_at:
        return True  # 无数据视为准时
    try:
        eta_date = datetime.fromisoformat(eta.replace("Z", "+00:00"))
        delivered_date = datetime.fromisoformat(delivered_at.replace("Z", "+00:00"))
        # 允许24小时误差
        return abs((delivered_date - eta_date).days) <= 1
    except Exception:
        return True


@router.get("/")
async def list_shipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    carrier: Optional[str] = None,
    transport_mode: Optional[str] = None,
    order_id: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """物流列表 + 统计"""
    shipments = _logistics_source()
    filtered: List[Dict[str, Any]] = []
    
    for shipment in shipments:
        # 状态筛选
        if status and shipment.get("status") != status:
            continue
        
        # 承运商筛选
        if carrier and shipment.get("carrier") != carrier:
            continue
        
        # 运输方式筛选
        if transport_mode and shipment.get("transport_mode") != transport_mode:
            continue
        
        # 订单筛选
        if order_id and shipment.get("order_id") != order_id:
            continue
        
        # 关键词搜索
        if q:
            text = f"{shipment.get('shipment_id','')}{shipment.get('order_id','')}{shipment.get('carrier','')}{shipment.get('tracking_number','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(shipment)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个运单添加状态标签和延期标记
    for shipment in page_items:
        shipment["status_label"] = _logistics_status(shipment.get("status", "unknown"))
        shipment["is_delayed"] = _is_delayed(shipment)
        shipment["landed_cost"] = round(
            shipment.get("cost", 0) + shipment.get("insurance", 0) + shipment.get("customs_cost", 0), 2
        )

    status_counter = Counter(shipment.get("status", "unknown") for shipment in filtered)
    carrier_counter = Counter(shipment.get("carrier", "未知") for shipment in filtered)
    
    total_cost = sum(shipment.get("cost", 0) for shipment in filtered)
    total_shipments = len(filtered)

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "shipments": page_items,
        "status_distribution": {_logistics_status(k): v for k, v in status_counter.items()},
        "carrier_distribution": carrier_counter,
        "total_cost": round(total_cost, 2),
        "total_shipments": total_shipments,
    }


@router.post("/")
async def create_shipment(payload: LogisticsCreateRequest):
    """创建物流运单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    shipment_id = f"LG-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    data["shipment_id"] = shipment_id
    data.setdefault("status", "ready")
    data.setdefault("priority", "normal")
    data.setdefault("milestones", [])
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.logistics.append(data)
    
    return {
        "success": True,
        "shipment": data,
        "message": "物流运单创建成功"
    }


@router.get("/{shipment_id}")
async def get_shipment_detail(shipment_id: str):
    """单个运单 + 生命周期 + 8维度"""
    shipment = _find_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="运单不存在")

    # 计算到岸成本
    landed_cost = shipment.get("cost", 0) + shipment.get("insurance", 0) + shipment.get("customs_cost", 0)
    
    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("delivery", [])
    status_mapping = {
        "ready": 0,
        "packing": 0,
        "picked_up": 1,
        "in_transit": 2,
        "customs": 2,
        "in_delivery": 3,
        "delivered": len(lifecycle_steps),
        "completed": len(lifecycle_steps),
        "cancelled": 0,
        "exception": 2,
    }
    current_index = status_mapping.get(shipment.get("status"), 0)
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
    for dim, score in (shipment.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    # 里程碑进度
    milestones = shipment.get("milestones", [])
    milestone_count = len(milestones)
    
    insights = []
    if _is_delayed(shipment):
        insights.append("⚠️ 运单已延期，建议联系承运商")
    if shipment.get("status") == "exception":
        insights.append("🔴 运单异常，需要立即处理")
    if shipment.get("cost", 0) > 50000:
        insights.append("💰 物流成本较高，建议优化运输方案")
    if shipment.get("status") == "delivered":
        if _is_on_time(shipment):
            insights.append("✅ 准时交付")
        else:
            insights.append("⚠️ 延迟交付，建议分析原因")
    if shipment.get("status") == "in_transit" and shipment.get("current_location"):
        insights.append(f"📍 当前位置：{shipment['current_location']}")

    return {
        "success": True,
        "shipment": shipment,
        "landed_cost": round(landed_cost, 2),
        "status_label": _logistics_status(shipment.get("status", "unknown")),
        "is_delayed": _is_delayed(shipment),
        "is_on_time": _is_on_time(shipment) if shipment.get("status") == "delivered" else None,
        "lifecycle": lifecycle,
        "milestones": milestones,
        "milestone_progress": round((milestone_count / max(4, len(lifecycle_steps)) * 100), 2),
        "dimension_breakdown": dimensions,
        "insights": insights,
    }


@router.patch("/{shipment_id}")
async def update_shipment(shipment_id: str, payload: LogisticsUpdateRequest):
    """更新运单（状态/位置/里程碑等）"""
    shipment = _find_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="运单不存在")

    # 更新字段
    if payload.status:
        old_status = shipment.get("status")
        shipment["status"] = payload.status
        # 如果是签收状态，记录签收时间
        if payload.status == "delivered" and not shipment.get("delivered_at"):
            shipment["delivered_at"] = _now()
    if payload.carrier:
        shipment["carrier"] = payload.carrier
    if payload.transport_mode:
        shipment["transport_mode"] = payload.transport_mode
    if payload.eta:
        shipment["eta"] = payload.eta
    if payload.cost is not None:
        shipment["cost"] = payload.cost
    if payload.insurance is not None:
        shipment["insurance"] = payload.insurance
    if payload.customs_cost is not None:
        shipment["customs_cost"] = payload.customs_cost
    if payload.current_location:
        shipment["current_location"] = payload.current_location
    if payload.milestones is not None:
        shipment["milestones"] = payload.milestones
    if payload.tracking_number:
        shipment["tracking_number"] = payload.tracking_number

    # 记录变更历史
    history = shipment.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    shipment["updated_at"] = _now()
    
    return {"success": True, "shipment": shipment}


@router.post("/{shipment_id}/milestone")
async def add_milestone(shipment_id: str, milestone: str):
    """添加里程碑"""
    shipment = _find_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="运单不存在")

    milestones = shipment.setdefault("milestones", [])
    if milestone not in milestones:
        milestones.append(milestone)
        shipment["updated_at"] = _now()
        
        # 根据里程碑自动更新状态
        if "打包完成" in milestone or "装柜完成" in milestone:
            shipment["status"] = "picking_up"
        elif "已提货" in milestone:
            shipment["status"] = "in_transit"
        elif "清关" in milestone:
            shipment["status"] = "customs"
        elif "配送中" in milestone:
            shipment["status"] = "in_delivery"
        elif "已签收" in milestone:
            shipment["status"] = "delivered"
            shipment["delivered_at"] = _now()
    
    return {"success": True, "shipment": shipment, "milestones": milestones}


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("delivery")
    shipments = _logistics_source()
    avg_dimension = defaultdict(list)
    for shipment in shipments:
        for dim, score in (shipment.get("dimensions") or {}).items():
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
        "shipment_sample_size": len(shipments),
    }


@router.get("/analytics/cost")
async def analyze_logistics_cost():
    """物流成本分析"""
    shipments = _logistics_source()
    
    # 按承运商统计成本
    carrier_costs = defaultdict(lambda: {"count": 0, "total_cost": 0.0, "total_insurance": 0.0, "total_customs": 0.0})
    for shipment in shipments:
        carrier = shipment.get("carrier", "未知")
        carrier_costs[carrier]["count"] += 1
        carrier_costs[carrier]["total_cost"] += shipment.get("cost", 0)
        carrier_costs[carrier]["total_insurance"] += shipment.get("insurance", 0)
        carrier_costs[carrier]["total_customs"] += shipment.get("customs_cost", 0)
    
    carrier_analysis = []
    for carrier, stats in carrier_costs.items():
        total_landed = stats["total_cost"] + stats["total_insurance"] + stats["total_customs"]
        avg_cost = total_landed / stats["count"] if stats["count"] > 0 else 0
        carrier_analysis.append({
            "carrier": carrier,
            "shipments": stats["count"],
            "total_cost": round(stats["total_cost"], 2),
            "total_insurance": round(stats["total_insurance"], 2),
            "total_customs": round(stats["total_customs"], 2),
            "total_landed_cost": round(total_landed, 2),
            "avg_cost": round(avg_cost, 2),
        })
    
    carrier_analysis.sort(key=lambda x: x["total_landed_cost"], reverse=True)
    
    # 按运输方式统计成本
    transport_costs = defaultdict(lambda: {"count": 0, "total_cost": 0.0})
    for shipment in shipments:
        mode = shipment.get("transport_mode", "未知")
        transport_costs[mode]["count"] += 1
        transport_costs[mode]["total_cost"] += shipment.get("cost", 0) + shipment.get("insurance", 0) + shipment.get("customs_cost", 0)
    
    transport_analysis = []
    for mode, stats in transport_costs.items():
        avg_cost = stats["total_cost"] / stats["count"] if stats["count"] > 0 else 0
        transport_analysis.append({
            "transport_mode": mode,
            "shipments": stats["count"],
            "total_cost": round(stats["total_cost"], 2),
            "avg_cost": round(avg_cost, 2),
        })
    
    transport_analysis.sort(key=lambda x: x["total_cost"], reverse=True)
    
    # 总体统计
    total_cost = sum(shipment.get("cost", 0) for shipment in shipments)
    total_insurance = sum(shipment.get("insurance", 0) for shipment in shipments)
    total_customs = sum(shipment.get("customs_cost", 0) for shipment in shipments)
    total_landed = total_cost + total_insurance + total_customs
    
    return {
        "success": True,
        "total_cost": round(total_cost, 2),
        "total_insurance": round(total_insurance, 2),
        "total_customs": round(total_customs, 2),
        "total_landed_cost": round(total_landed, 2),
        "carrier_analysis": carrier_analysis,
        "transport_analysis": transport_analysis,
        "avg_shipment_cost": round(total_landed / len(shipments), 2) if shipments else 0,
    }


@router.get("/analytics/performance")
async def analyze_logistics_performance():
    """物流绩效分析（准时交付率、异常率等）"""
    shipments = _logistics_source()
    
    # 准时交付率
    delivered = [s for s in shipments if s.get("status") in ("delivered", "completed")]
    on_time = len([s for s in delivered if _is_on_time(s)])
    on_time_rate = (on_time / len(delivered) * 100) if delivered else 0
    
    # 延期率
    delayed = len([s for s in shipments if _is_delayed(s)])
    delay_rate = (delayed / len(shipments) * 100) if shipments else 0
    
    # 异常率
    exception_count = len([s for s in shipments if s.get("status") == "exception"])
    exception_rate = (exception_count / len(shipments) * 100) if shipments else 0
    
    # 在途时间分析（简化）
    in_transit_shipments = [s for s in shipments if s.get("status") == "in_transit"]
    avg_transit_days = 0
    if in_transit_shipments:
        total_days = 0
        for shipment in in_transit_shipments:
            created_at = shipment.get("created_at", _now())
            try:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                days = (datetime.now(timezone.utc) - created_date).days
                total_days += days
            except Exception:
                pass
        avg_transit_days = total_days / len(in_transit_shipments) if in_transit_shipments else 0
    
    # 按承运商统计绩效
    carrier_performance = defaultdict(lambda: {"total": 0, "delivered": 0, "on_time": 0, "delayed": 0, "exception": 0})
    for shipment in shipments:
        carrier = shipment.get("carrier", "未知")
        carrier_performance[carrier]["total"] += 1
        if shipment.get("status") in ("delivered", "completed"):
            carrier_performance[carrier]["delivered"] += 1
            if _is_on_time(shipment):
                carrier_performance[carrier]["on_time"] += 1
        if _is_delayed(shipment):
            carrier_performance[carrier]["delayed"] += 1
        if shipment.get("status") == "exception":
            carrier_performance[carrier]["exception"] += 1
    
    carrier_stats = []
    for carrier, stats in carrier_performance.items():
        on_time_rate_carrier = (stats["on_time"] / stats["delivered"] * 100) if stats["delivered"] > 0 else 0
        delay_rate_carrier = (stats["delayed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        exception_rate_carrier = (stats["exception"] / stats["total"] * 100) if stats["total"] > 0 else 0
        carrier_stats.append({
            "carrier": carrier,
            "total_shipments": stats["total"],
            "delivered": stats["delivered"],
            "on_time_rate": round(on_time_rate_carrier, 2),
            "delay_rate": round(delay_rate_carrier, 2),
            "exception_rate": round(exception_rate_carrier, 2),
            "performance_score": round((on_time_rate_carrier - delay_rate_carrier - exception_rate_carrier * 2), 2),
        })
    
    carrier_stats.sort(key=lambda x: x["performance_score"], reverse=True)
    
    return {
        "success": True,
        "overall_on_time_rate": round(on_time_rate, 2),
        "overall_delay_rate": round(delay_rate, 2),
        "overall_exception_rate": round(exception_rate, 2),
        "avg_transit_days": round(avg_transit_days, 1),
        "carrier_performance": carrier_stats,
    }

