#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T012 · 订单管理API

能力要求：
- 订单全生命周期（接收→校验→承诺→执行→回款）
- 25项能力清单（与ERP蓝图保持一致）
- 8维度分析（质量/成本/交付/安全/利润/效率/管理/技术）
"""
from __future__ import annotations

import html
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

# 使用绝对导入路径避免模块冲突
import sys
import os

# 获取Super Agent Main Interface的core模块绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
super_agent_dir = os.path.dirname(current_dir)
core_dir = os.path.join(super_agent_dir, "core")

# 确保core目录在sys.path中
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

# 直接导入erp_process_service模块
from erp_process_service import BASE_STAGE_LIFECYCLES, ERPProcessService

# 延迟导入erp_process_service以避免相对导入问题
def get_erp_process_service():
    """获取ERP流程服务实例"""
    try:
        from api.super_agent_api import erp_process_service
        return erp_process_service
    except ImportError:
        # 如果导入失败，创建新的实例
        return ERPProcessService()

erp_process_service = get_erp_process_service()

router = APIRouter(prefix="/api/orders", tags=["ERP Order Management"])


# ============ 安全防护函数 ============

def _sanitize_sql_input(input_str: str) -> str:
    """
    清理SQL注入风险字符
    """
    if not input_str:
        return ""
    
    # 移除常见的SQL注入关键词
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'OR', 'AND', 'WHERE']
    sanitized = input_str
    for keyword in sql_keywords:
        sanitized = re.sub(re.escape(keyword), '', sanitized, flags=re.IGNORECASE)
    
    # 移除特殊字符
    sanitized = re.sub(r'[;\'\"\\]', '', sanitized)
    
    return sanitized.strip()


def _sanitize_html_input(input_str: str) -> str:
    """
    清理XSS风险字符，HTML转义
    """
    if not input_str:
        return ""
    
    return html.escape(input_str)


def _validate_numeric_input(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    验证数值输入
    """
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def _validate_string_length(input_str: str, max_length: int = 500) -> bool:
    """
    验证字符串长度
    """
    return input_str is not None and len(input_str) <= max_length


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
        "legal": "legal",
        "合同": "legal",
        "供应": "supply",
        "材料": "supply",
        "资金": "finance",
        "成本": "finance",
        "交付": "delivery",
        "进度": "delivery",
    }
    for key, bucket in keywords.items():
        if key in value:
            return bucket
    return "general"


def _orders_source() -> List[Dict[str, Any]]:
    return erp_process_service.orders


def _find_order(order_id: str) -> Optional[Dict[str, Any]]:
    for order in _orders_source():
        if str(order.get("order_id")) == str(order_id):
            return order
    return None


def _refresh_stage_metrics() -> None:
    refresh = getattr(erp_process_service, "_refresh_stage_from_orders", None)
    if callable(refresh):
        refresh()


class OrderItemInput(BaseModel):
    name: str
    quantity: float = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    code: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('产品名称不能为空')
        if len(v) > 200:
            raise ValueError('产品名称长度不能超过200字符')
        # 清理HTML和SQL注入风险
        v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('code')
    def validate_code(cls, v):
        if v and len(v) > 50:
            raise ValueError('产品编码长度不能超过50字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v


class OrderCreateRequest(BaseModel):
    order_id: Optional[str] = Field(None, description="自定义订单号（可选）")
    customer: str
    industry: Optional[str] = None
    value: float = Field(..., ge=0)
    currency: str = "CNY"
    priority: str = "normal"
    status: str = "confirming"
    stage: Optional[str] = None
    delivery_date: Optional[str] = Field(
        None, description="交付日期（ISO8601，如 2025-11-30）"
    )
    risk: Optional[str] = None
    dimensions: Optional[Dict[str, float]] = None
    tags: List[str] = Field(default_factory=list)
    items: List[OrderItemInput] = Field(default_factory=list)
    
    @validator('customer')
    def validate_customer(cls, v):
        if not v or not v.strip():
            raise ValueError('客户名称不能为空')
        if len(v) > 200:
            raise ValueError('客户名称长度不能超过200字符')
        v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('industry')
    def validate_industry(cls, v):
        if v and len(v) > 100:
            raise ValueError('行业名称长度不能超过100字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('order_id')
    def validate_order_id(cls, v):
        if v and len(v) > 50:
            raise ValueError('订单ID长度不能超过50字符')
        if v:
            # 订单ID只能包含字母、数字、下划线和短横线
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('订单ID只能包含字母、数字、下划线和短横线')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if v not in valid_priorities:
            raise ValueError(f'优先级必须是以下之一: {valid_priorities}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['confirming', 'approved', 'executing', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'订单状态必须是以下之一: {valid_statuses}')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['CNY', 'USD', 'EUR', 'JPY', 'GBP']
        if v not in valid_currencies:
            raise ValueError(f'货币必须是以下之一: {valid_currencies}')
        return v
    
    @validator('delivery_date')
    def validate_delivery_date(cls, v):
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('交付日期格式不正确，请使用ISO8601格式')
        return v
    
    @validator('risk')
    def validate_risk(cls, v):
        if v and len(v) > 500:
            raise ValueError('风险描述长度不能超过500字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('标签数量不能超过20个')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('单个标签长度不能超过50字符')
            if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5_-]+$', tag):
                raise ValueError('标签只能包含中文、字母、数字、下划线和短横线')
        return v
    
    @validator('dimensions')
    def validate_dimensions(cls, v):
        if v:
            valid_dimensions = ['quality', 'cost', 'delivery', 'safety', 'profit', 'efficiency', 'management', 'technology']
            for key in v.keys():
                if key not in valid_dimensions:
                    raise ValueError(f'维度必须是以下之一: {valid_dimensions}')
                if not isinstance(v[key], (int, float)) or v[key] < 0 or v[key] > 1:
                    raise ValueError('维度评分必须是0到1之间的数值')
        return v


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="新的订单状态")
    stage: Optional[str] = Field(
        None, description="订单所处阶段（接收/评估/承诺/执行/回款等）"
    )
    risk: Optional[str] = None
    note: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['confirming', 'approved', 'executing', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f'订单状态必须是以下之一: {valid_statuses}')
        return v
    
    @validator('stage')
    def validate_stage(cls, v):
        if v and len(v) > 100:
            raise ValueError('阶段名称长度不能超过100字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('risk')
    def validate_risk(cls, v):
        if v and len(v) > 500:
            raise ValueError('风险描述长度不能超过500字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v
    
    @validator('note')
    def validate_note(cls, v):
        if v and len(v) > 1000:
            raise ValueError('备注长度不能超过1000字符')
        if v:
            v = _sanitize_html_input(_sanitize_sql_input(v))
        return v


@router.get("/overview")
async def get_order_overview():
    """整体概览 + 8维度 + 25项能力"""
    view = erp_process_service.get_orders_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("order_management")
    blueprint = erp_process_service.get_stage_blueprint("order_management")
    lifecycle = BASE_STAGE_LIFECYCLES.get("order_management", [])
    orders = _orders_source()

    status_counter = Counter(order.get("status", "unknown") for order in orders)
    stage_counter = Counter(order.get("stage", "未定义") for order in orders)
    risk_counter = Counter(_risk_bucket(order.get("risk")) for order in orders)

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
        "capabilities": blueprint.get("blueprint", {}).get("capabilities", []),
        "dimension_summary": view.get("dimension_summary", []),
    }


@router.get("/")
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    stage: Optional[str] = None,
    q: Optional[str] = Query(None, alias="search"),
):
    """订单列表 + 统计"""
    # 安全验证：清理输入参数
    if status:
        status = _sanitize_html_input(_sanitize_sql_input(status))
        valid_statuses = ['confirming', 'approved', 'executing', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"无效的状态参数，必须是以下之一: {valid_statuses}")
    
    if priority:
        priority = _sanitize_html_input(_sanitize_sql_input(priority))
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"无效的优先级参数，必须是以下之一: {valid_priorities}")
    
    if stage:
        stage = _sanitize_html_input(_sanitize_sql_input(stage))
        if len(stage) > 100:
            raise HTTPException(status_code=400, detail="阶段名称长度不能超过100字符")
    
    if q:
        q = _sanitize_html_input(_sanitize_sql_input(q))
        if len(q) > 200:
            raise HTTPException(status_code=400, detail="搜索关键词长度不能超过200字符")
    
    orders = _orders_source()
    filtered: List[Dict[str, Any]] = []
    for order in orders:
        if status and order.get("status") != status:
            continue
        if priority and order.get("priority") != priority:
            continue
        if stage and order.get("stage") != stage:
            continue
        if q:
            text = f"{order.get('order_id','')}{order.get('customer','')}{order.get('industry','')}{order.get('risk','')}"
            if q.lower() not in text.lower():
                continue
        filtered.append(order)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    status_counter = Counter(order.get("status", "unknown") for order in filtered)
    stage_counter = Counter(order.get("stage", "未定义") for order in filtered)
    priority_counter = Counter(order.get("priority", "normal") for order in filtered)

    value_by_priority = defaultdict(float)
    for order in filtered:
        value_by_priority[order.get("priority", "normal")] += float(order.get("value", 0))

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "orders": page_items,
        "status_distribution": status_counter,
        "stage_distribution": stage_counter,
        "priority_distribution": priority_counter,
        "value_by_priority": value_by_priority,
    }


@router.post("/")
async def create_order(payload: OrderCreateRequest):
    """创建订单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    data.setdefault("created_at", _now())
    result = erp_process_service.add_order(data)
    _refresh_stage_metrics()
    return result


@router.get("/{order_id}")
async def get_order_detail(order_id: str):
    """单个订单 + 生命周期 + 8维度"""
    # 安全验证：清理订单ID
    order_id = _sanitize_html_input(_sanitize_sql_input(order_id))
    
    # 验证订单ID格式
    if not order_id or len(order_id) > 50:
        raise HTTPException(status_code=400, detail="订单ID格式不正确")
    
    # 订单ID只能包含字母、数字、下划线和短横线
    if not re.match(r'^[a-zA-Z0-9_-]+$', order_id):
        raise HTTPException(status_code=400, detail="订单ID格式不正确，只能包含字母、数字、下划线和短横线")
    
    order = _find_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("order_management", [])
    status_mapping = {
        "confirming": 1,
        "approved": 2,
        "executing": 4,
        "completed": len(lifecycle_steps),
    }
    current_index = status_mapping.get(order.get("status"), 1)
    lifecycle = []
    for idx, step in enumerate(lifecycle_steps, start=1):
        lifecycle.append(
            {
                "stage": step,
                "sequence": idx,
                "status": "completed"
                if idx < current_index
                else "current"
                if idx == current_index
                else "pending",
            }
        )

    dimensions = []
    for dim, score in (order.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    insights = []
    if order.get("risk") and order["risk"] not in ("无", "none"):
        insights.append(f"⚠️ 风险提示：{order['risk']}")
    if order.get("priority") in ("urgent", "high"):
        insights.append("⏱️ 高优订单，请优先排程")
    if order.get("status") == "completed":
        insights.append("✅ 已完成，可进入回款核对")

    return {
        "success": True,
        "order": order,
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "insights": insights,
    }


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, payload: OrderStatusUpdateRequest):
    """更新订单状态/阶段/风险"""
    # 安全验证：清理订单ID
    order_id = _sanitize_html_input(_sanitize_sql_input(order_id))
    
    # 验证订单ID格式
    if not order_id or len(order_id) > 50:
        raise HTTPException(status_code=400, detail="订单ID格式不正确")
    
    # 订单ID只能包含字母、数字、下划线和短横线
    if not re.match(r'^[a-zA-Z0-9_-]+$', order_id):
        raise HTTPException(status_code=400, detail="订单ID格式不正确，只能包含字母、数字、下划线和短横线")
    
    order = _find_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order["status"] = payload.status
    if payload.stage:
        order["stage"] = payload.stage
    if payload.risk is not None:
        order["risk"] = payload.risk

    history = order.setdefault("status_history", [])
    history.append(
        {
            "to": payload.status,
            "stage": payload.stage or order.get("stage"),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    _refresh_stage_metrics()
    return {"success": True, "order": order}


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("order_management")
    orders = _orders_source()
    avg_dimension = defaultdict(list)
    for order in orders:
        for dim, score in (order.get("dimensions") or {}).items():
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
        "order_sample_size": len(orders),
    }


@router.get("/analytics/risk")
async def analyze_order_risk():
    """风险雷达"""
    orders = _orders_source()
    heatmap = Counter(_risk_bucket(order.get("risk")) for order in orders)
    high_risk = [
        {
            "order_id": order.get("order_id"),
            "customer": order.get("customer"),
            "risk": order.get("risk"),
            "priority": order.get("priority"),
            "stage": order.get("stage"),
        }
        for order in orders
        if order.get("risk") and order["risk"] not in ("无", "none")
    ][:10]

    return {"success": True, "heatmap": heatmap, "high_risk_orders": high_risk}


