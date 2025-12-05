#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T015 · 库存管理API

能力要求：
- 库存全生命周期（入库→在库→出库→盘点→调拨→优化）
- 30项能力清单（与ERP蓝图保持一致）
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

router = APIRouter(prefix="/api/inventory", tags=["ERP Inventory Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _stock_status(item: Dict[str, Any]) -> str:
    """判断库存状态：充足/预警/缺货/超储"""
    on_hand = item.get("on_hand", 0)
    available = item.get("available", 0)
    safety_stock = item.get("safety_stock", 0)
    reorder_point = item.get("reorder_point", 0)
    
    if available <= 0:
        return "out_of_stock"
    elif available < safety_stock:
        return "low_stock"
    elif available >= reorder_point * 2:
        return "overstock"
    else:
        return "normal"


def _stock_status_label(status: str) -> str:
    labels = {
        "out_of_stock": "缺货",
        "low_stock": "预警",
        "normal": "充足",
        "overstock": "超储",
    }
    return labels.get(status, "未知")


def _inventory_source() -> List[Dict[str, Any]]:
    return erp_process_service.inventory


def _find_inventory(material_id: str) -> Optional[Dict[str, Any]]:
    for item in _inventory_source():
        if str(item.get("material_id")) == str(material_id):
            return item
    return None


class InventoryItemInput(BaseModel):
    material_id: str
    name: str
    on_hand: float = Field(..., ge=0, description="在手库存")
    allocated: float = Field(0, ge=0, description="已分配")
    available: Optional[float] = Field(None, ge=0, description="可用库存（自动计算）")
    safety_stock: float = Field(0, ge=0, description="安全库存")
    reorder_point: float = Field(0, ge=0, description="再订货点")
    unit: Optional[str] = "件"
    category: Optional[str] = None
    location: Optional[str] = None


class InventoryUpdateRequest(BaseModel):
    on_hand: Optional[float] = Field(None, ge=0, description="在手库存")
    allocated: Optional[float] = Field(None, ge=0, description="已分配")
    available: Optional[float] = Field(None, ge=0, description="可用库存")
    safety_stock: Optional[float] = Field(None, ge=0, description="安全库存")
    reorder_point: Optional[float] = Field(None, ge=0, description="再订货点")
    location: Optional[str] = None
    note: Optional[str] = None


class InventoryTransferRequest(BaseModel):
    from_material_id: str
    to_material_id: Optional[str] = None
    quantity: float = Field(..., gt=0, description="调拨数量")
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    reason: Optional[str] = None


@router.get("/overview")
async def get_inventory_overview():
    """整体概览 + 8维度 + 30项能力"""
    view = erp_process_service.get_inventory_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("warehousing")
    blueprint = erp_process_service.get_stage_blueprint("warehousing")
    lifecycle = BASE_STAGE_LIFECYCLES.get("warehousing", [])
    inventory = _inventory_source()

    # 统计库存状态
    status_counter = Counter(_stock_status(item) for item in inventory)
    
    # 统计类别
    category_counter = Counter(item.get("category", "未分类") for item in inventory)
    
    # 计算总价值（假设每个物料单位成本为100）
    total_value = sum(item.get("on_hand", 0) * 100 for item in inventory)
    
    # 低库存预警
    low_stock_items = len([item for item in inventory if _stock_status(item) in ("low_stock", "out_of_stock")])
    
    # 蓝图已自动扩展能力清单到30项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "total_value": round(total_value, 2),
            "low_stock_count": low_stock_items,
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
        "status_distribution": {_stock_status_label(k): v for k, v in status_counter.items()},
        "category_distribution": category_counter,
        "risk_heatmap": {
            "low_stock": len([item for item in inventory if _stock_status(item) == "low_stock"]),
            "out_of_stock": len([item for item in inventory if _stock_status(item) == "out_of_stock"]),
            "overstock": len([item for item in inventory if _stock_status(item) == "overstock"]),
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
    }


@router.get("/")
async def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """库存列表 + 统计"""
    inventory = _inventory_source()
    filtered: List[Dict[str, Any]] = []
    
    for item in inventory:
        # 状态筛选
        if status:
            item_status = _stock_status(item)
            status_mapping = {
                "缺货": "out_of_stock",
                "预警": "low_stock",
                "充足": "normal",
                "超储": "overstock",
            }
            if item_status != status_mapping.get(status, status):
                continue
        
        # 类别筛选
        if category and item.get("category") != category:
            continue
        
        # 库位筛选
        if location and item.get("location") != location:
            continue
        
        # 关键词搜索
        if q:
            text = f"{item.get('material_id','')}{item.get('name','')}{item.get('category','')}{item.get('location','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(item)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个物料添加状态和可用库存计算
    for item in page_items:
        if item.get("available") is None:
            item["available"] = item.get("on_hand", 0) - item.get("allocated", 0)
        item["stock_status"] = _stock_status(item)
        item["stock_status_label"] = _stock_status_label(item["stock_status"])

    status_counter = Counter(_stock_status(item) for item in filtered)
    category_counter = Counter(item.get("category", "未分类") for item in filtered)
    
    total_value = sum(item.get("on_hand", 0) * 100 for item in filtered)
    total_on_hand = sum(item.get("on_hand", 0) for item in filtered)

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "inventory": page_items,
        "status_distribution": {_stock_status_label(k): v for k, v in status_counter.items()},
        "category_distribution": category_counter,
        "total_value": round(total_value, 2),
        "total_on_hand": total_on_hand,
    }


@router.post("/")
async def create_inventory_item(payload: InventoryItemInput):
    """创建库存物料（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    material_id = data.get("material_id")
    
    # 检查是否已存在
    existing = _find_inventory(material_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"物料 {material_id} 已存在")
    
    # 计算可用库存
    if data.get("available") is None:
        data["available"] = data.get("on_hand", 0) - data.get("allocated", 0)
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.inventory.append(data)
    
    return {
        "success": True,
        "inventory_item": data,
        "message": "库存物料创建成功"
    }


@router.get("/{material_id}")
async def get_inventory_detail(material_id: str):
    """单个库存物料 + 生命周期 + 8维度"""
    item = _find_inventory(material_id)
    if not item:
        raise HTTPException(status_code=404, detail="库存物料不存在")

    # 计算可用库存
    if item.get("available") is None:
        item["available"] = item.get("on_hand", 0) - item.get("allocated", 0)
    
    stock_status = _stock_status(item)
    
    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("warehousing", [])
    lifecycle = []
    for idx, step in enumerate(lifecycle_steps, start=1):
        lifecycle.append(
            {
                "stage": step,
                "sequence": idx,
                "status": "completed" if idx <= 3 else "current" if idx == 4 else "pending",
            }
        )

    dimensions = []
    for dim, score in (item.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    insights = []
    if stock_status == "out_of_stock":
        insights.append("🔴 库存缺货，建议立即补货")
    elif stock_status == "low_stock":
        insights.append("🟡 库存低于安全库存，建议尽快补货")
    elif stock_status == "overstock":
        insights.append("🟢 库存超储，建议检查需求预测")
    
    available = item.get("available", 0)
    safety_stock = item.get("safety_stock", 0)
    if available < safety_stock:
        insights.append(f"⚠️ 可用库存 ({available}) 低于安全库存 ({safety_stock})")
    
    utilization = (item.get("allocated", 0) / item.get("on_hand", 1)) * 100 if item.get("on_hand", 0) > 0 else 0
    if utilization > 80:
        insights.append(f"📊 库存占用率 {utilization:.1f}%，接近满载")

    return {
        "success": True,
        "inventory_item": item,
        "stock_status": stock_status,
        "stock_status_label": _stock_status_label(stock_status),
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "insights": insights,
        "utilization_rate": round(utilization, 2),
    }


@router.patch("/{material_id}")
async def update_inventory_item(material_id: str, payload: InventoryUpdateRequest):
    """更新库存物料（库存调整、盘点等）"""
    item = _find_inventory(material_id)
    if not item:
        raise HTTPException(status_code=404, detail="库存物料不存在")

    # 更新字段
    if payload.on_hand is not None:
        item["on_hand"] = payload.on_hand
    if payload.allocated is not None:
        item["allocated"] = payload.allocated
    if payload.available is not None:
        item["available"] = payload.available
    elif payload.on_hand is not None or payload.allocated is not None:
        # 自动计算可用库存
        item["available"] = item.get("on_hand", 0) - item.get("allocated", 0)
    if payload.safety_stock is not None:
        item["safety_stock"] = payload.safety_stock
    if payload.reorder_point is not None:
        item["reorder_point"] = payload.reorder_point
    if payload.location is not None:
        item["location"] = payload.location

    # 记录变更历史
    history = item.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    item["updated_at"] = _now()
    
    return {"success": True, "inventory_item": item}


@router.post("/transfer")
async def transfer_inventory(payload: InventoryTransferRequest):
    """库存调拨"""
    from_item = _find_inventory(payload.from_material_id)
    if not from_item:
        raise HTTPException(status_code=404, detail=f"源物料 {payload.from_material_id} 不存在")
    
    # 检查可用库存
    available = from_item.get("available", from_item.get("on_hand", 0) - from_item.get("allocated", 0))
    if available < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"可用库存不足：可用 {available}，需要 {payload.quantity}"
        )
    
    # 更新源物料
    from_item["on_hand"] = from_item.get("on_hand", 0) - payload.quantity
    from_item["available"] = available - payload.quantity
    
    # 如果目标物料存在，更新目标物料
    if payload.to_material_id:
        to_item = _find_inventory(payload.to_material_id)
        if to_item:
            to_item["on_hand"] = to_item.get("on_hand", 0) + payload.quantity
            to_item["available"] = to_item.get("available", 0) + payload.quantity
            if payload.to_location:
                to_item["location"] = payload.to_location
        else:
            raise HTTPException(status_code=404, detail=f"目标物料 {payload.to_material_id} 不存在")
    
    # 记录调拨历史
    transfer_record = {
        "from_material_id": payload.from_material_id,
        "to_material_id": payload.to_material_id,
        "quantity": payload.quantity,
        "from_location": payload.from_location or from_item.get("location"),
        "to_location": payload.to_location,
        "reason": payload.reason,
        "timestamp": _now(),
    }
    
    # 在源物料中记录调拨历史
    history = from_item.setdefault("transfer_history", [])
    history.append(transfer_record)
    
    return {
        "success": True,
        "transfer": transfer_record,
        "from_item": from_item,
        "message": "库存调拨成功"
    }


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("warehousing")
    inventory = _inventory_source()
    avg_dimension = defaultdict(list)
    for item in inventory:
        for dim, score in (item.get("dimensions") or {}).items():
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
        "inventory_sample_size": len(inventory),
    }


@router.get("/analytics/stock_health")
async def analyze_stock_health():
    """库存健康度分析"""
    inventory = _inventory_source()
    
    health_stats = {
        "total_items": len(inventory),
        "normal_stock": 0,
        "low_stock": 0,
        "out_of_stock": 0,
        "overstock": 0,
    }
    
    low_stock_items = []
    overstock_items = []
    
    for item in inventory:
        status = _stock_status(item)
        if status == "normal":
            health_stats["normal_stock"] += 1
        elif status == "low_stock":
            health_stats["low_stock"] += 1
            low_stock_items.append({
                "material_id": item.get("material_id"),
                "name": item.get("name"),
                "available": item.get("available", 0),
                "safety_stock": item.get("safety_stock", 0),
            })
        elif status == "out_of_stock":
            health_stats["out_of_stock"] += 1
            low_stock_items.append({
                "material_id": item.get("material_id"),
                "name": item.get("name"),
                "available": 0,
                "safety_stock": item.get("safety_stock", 0),
            })
        elif status == "overstock":
            health_stats["overstock"] += 1
            overstock_items.append({
                "material_id": item.get("material_id"),
                "name": item.get("name"),
                "on_hand": item.get("on_hand", 0),
                "available": item.get("available", 0),
            })
    
    health_rate = (health_stats["normal_stock"] / health_stats["total_items"] * 100) if health_stats["total_items"] > 0 else 0
    
    return {
        "success": True,
        "health_stats": health_stats,
        "health_rate": round(health_rate, 2),
        "low_stock_items": sorted(low_stock_items, key=lambda x: x["available"])[:10],
        "overstock_items": sorted(overstock_items, key=lambda x: x["on_hand"], reverse=True)[:10],
    }


@router.get("/analytics/turnover")
async def analyze_turnover():
    """库存周转分析"""
    inventory = _inventory_source()
    
    # 计算平均库存周转率（简化算法）
    total_value = sum(item.get("on_hand", 0) * 100 for item in inventory)
    total_allocated = sum(item.get("allocated", 0) for item in inventory)
    
    turnover_rate = (total_allocated / total_value * 365) if total_value > 0 else 0
    
    # 按类别统计
    category_stats = defaultdict(lambda: {"count": 0, "total_on_hand": 0, "total_allocated": 0})
    for item in inventory:
        category = item.get("category", "未分类")
        category_stats[category]["count"] += 1
        category_stats[category]["total_on_hand"] += item.get("on_hand", 0)
        category_stats[category]["total_allocated"] += item.get("allocated", 0)
    
    category_turnover = []
    for category, stats in category_stats.items():
        cat_turnover = (stats["total_allocated"] / stats["total_on_hand"] * 365) if stats["total_on_hand"] > 0 else 0
        category_turnover.append({
            "category": category,
            "item_count": stats["count"],
            "turnover_days": round(cat_turnover, 2),
        })
    
    category_turnover.sort(key=lambda x: x["turnover_days"])
    
    return {
        "success": True,
        "overall_turnover_days": round(turnover_rate, 2),
        "total_value": round(total_value, 2),
        "total_items": len(inventory),
        "category_turnover": category_turnover,
    }

