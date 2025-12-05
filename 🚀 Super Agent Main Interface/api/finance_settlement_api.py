#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T020 · 财务结算API

能力要求：
- 财务结算全生命周期（开票→对账→收款→核销→结案）
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

router = APIRouter(prefix="/api/finance-settlement", tags=["ERP Finance Settlement Management"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_status(score: float) -> str:
    if score >= 0.85:
        return "excellent"
    if score >= 0.7:
        return "watch"
    return "risk"


def _finance_status(status: str) -> str:
    """判断财务结算状态"""
    status_mapping = {
        "awaiting_invoice": "待开票",
        "invoiced": "已开票",
        "awaiting_reconciliation": "待对账",
        "reconciled": "已对账",
        "in_collection": "收款中",
        "partially_collected": "部分收款",
        "collected": "已收款",
        "written_off": "已核销",
        "closed": "已结案",
        "cancelled": "已取消",
    }
    return status_mapping.get(status, status)


def _finance_source() -> List[Dict[str, Any]]:
    return erp_process_service.finance


def _find_settlement(settlement_id: str) -> Optional[Dict[str, Any]]:
    for settlement in _finance_source():
        if str(settlement.get("settlement_id")) == str(settlement_id):
            return settlement
    return None


class FinanceSettlementCreateRequest(BaseModel):
    order_id: str = Field(..., description="订单号")
    amount: float = Field(..., gt=0, description="结算金额")
    currency: str = Field("CNY", description="币种")
    due_date: Optional[str] = Field(None, description="到期日期（ISO8601）")
    invoice_type: Optional[str] = Field(None, description="发票类型（增值税/普通发票等）")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="税率（0-1）")
    payment_terms: Optional[str] = Field(None, description="付款条件（如：30天）")
    customer: Optional[str] = Field(None, description="客户名称")


class FinanceSettlementUpdateRequest(BaseModel):
    status: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    due_date: Optional[str] = None
    received: Optional[float] = Field(None, ge=0, le=1, description="收款比例（0-1）")
    received_amount: Optional[float] = Field(None, ge=0, description="已收款金额")
    invoice_number: Optional[str] = Field(None, description="发票号")
    invoice_date: Optional[str] = Field(None, description="开票日期（ISO8601）")
    reconciliation_date: Optional[str] = Field(None, description="对账日期（ISO8601）")
    collection_date: Optional[str] = Field(None, description="收款日期（ISO8601）")
    note: Optional[str] = None


class PaymentRecord(BaseModel):
    payment_date: str = Field(..., description="收款日期（ISO8601）")
    payment_amount: float = Field(..., gt=0, description="收款金额")
    payment_method: Optional[str] = Field(None, description="收款方式（银行转账/现金/支票等）")
    reference_number: Optional[str] = Field(None, description="参考号（如银行流水号）")
    note: Optional[str] = None


@router.get("/overview")
async def get_finance_settlement_overview():
    """整体概览 + 8维度 + 15项能力"""
    view = erp_process_service.get_finance_view()
    dimension_analysis = erp_process_service.get_dimension_analysis("finance_settlement")
    blueprint = erp_process_service.get_stage_blueprint("finance_settlement")
    lifecycle = BASE_STAGE_LIFECYCLES.get("finance_settlement", [])
    settlements = _finance_source()

    # 统计结算状态
    status_counter = Counter(settlement.get("status", "unknown") for settlement in settlements)
    
    # 统计币种
    currency_counter = Counter(settlement.get("currency", "CNY") for settlement in settlements)
    
    # 计算总金额和已收款金额
    total_amount = sum(settlement.get("amount", 0) for settlement in settlements)
    total_received = sum(settlement.get("amount", 0) * settlement.get("received", 0) for settlement in settlements)
    collection_rate = (total_received / total_amount * 100) if total_amount > 0 else 0
    
    # 计算逾期金额
    overdue_amount = sum(
        settlement.get("amount", 0) * (1 - settlement.get("received", 0))
        for settlement in settlements
        if _is_overdue(settlement)
    )
    
    # 计算账龄分布
    age_distribution = _calculate_age_distribution(settlements)
    
    # 蓝图已自动扩展能力清单到15项（通过_build_stage_capabilities）
    capabilities = blueprint.get("blueprint", {}).get("capabilities", [])

    return {
        "success": True,
        "updated_at": _now(),
        "summary": {
            **view.get("summary", {}),
            "total_received": round(total_received, 2),
            "collection_rate": round(collection_rate, 2),
            "overdue_amount": round(overdue_amount, 2),
            "overdue_count": len([s for s in settlements if _is_overdue(s)]),
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
        "status_distribution": {_finance_status(k): v for k, v in status_counter.items()},
        "currency_distribution": currency_counter,
        "age_distribution": age_distribution,
        "risk_heatmap": {
            "overdue": len([s for s in settlements if _is_overdue(s)]),
            "high_amount": len([s for s in settlements if s.get("amount", 0) > 1000000]),
            "low_collection": len([s for s in settlements if s.get("received", 0) < 0.5 and s.get("status") not in ("closed", "cancelled")]),
        },
        "capabilities": capabilities,
        "dimension_summary": dimension_analysis.get("dimensions", []),
    }


def _is_overdue(settlement: Dict[str, Any]) -> bool:
    """判断是否逾期"""
    if settlement.get("status") in ("closed", "collected", "cancelled"):
        return False
    due_date = settlement.get("due_date")
    if not due_date:
        return False
    try:
        due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > due
    except Exception:
        return False


def _calculate_age_distribution(settlements: List[Dict[str, Any]]) -> Dict[str, int]:
    """计算账龄分布"""
    age_groups = {
        "0-30天": 0,
        "31-60天": 0,
        "61-90天": 0,
        "91-180天": 0,
        "180天以上": 0,
    }
    
    for settlement in settlements:
        if settlement.get("status") in ("closed", "collected", "cancelled"):
            continue
        due_date = settlement.get("due_date")
        if not due_date:
            continue
        try:
            due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - due).days
            if days <= 0:
                age_groups["0-30天"] += 1
            elif days <= 30:
                age_groups["0-30天"] += 1
            elif days <= 60:
                age_groups["31-60天"] += 1
            elif days <= 90:
                age_groups["61-90天"] += 1
            elif days <= 180:
                age_groups["91-180天"] += 1
            else:
                age_groups["180天以上"] += 1
        except Exception:
            pass
    
    return age_groups


@router.get("/")
async def list_settlements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    currency: Optional[str] = None,
    order_id: Optional[str] = None,
    overdue_only: bool = Query(False, description="仅显示逾期"),
    q: Optional[str] = Query(None, alias="search"),
):
    """财务结算列表 + 统计"""
    settlements = _finance_source()
    filtered: List[Dict[str, Any]] = []
    
    for settlement in settlements:
        # 状态筛选
        if status and settlement.get("status") != status:
            continue
        
        # 币种筛选
        if currency and settlement.get("currency") != currency:
            continue
        
        # 订单筛选
        if order_id and settlement.get("order_id") != order_id:
            continue
        
        # 逾期筛选
        if overdue_only and not _is_overdue(settlement):
            continue
        
        # 关键词搜索
        if q:
            text = f"{settlement.get('settlement_id','')}{settlement.get('order_id','')}{settlement.get('customer','')}{settlement.get('invoice_number','')}"
            if q.lower() not in text.lower():
                continue
        
        filtered.append(settlement)

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]

    # 为每个结算单添加状态标签和计算字段
    for settlement in page_items:
        settlement["status_label"] = _finance_status(settlement.get("status", "unknown"))
        settlement["is_overdue"] = _is_overdue(settlement)
        amount = settlement.get("amount", 0)
        received_ratio = settlement.get("received", 0)
        settlement["received_amount"] = round(amount * received_ratio, 2)
        settlement["outstanding_amount"] = round(amount * (1 - received_ratio), 2)
        settlement["collection_rate"] = round(received_ratio * 100, 2)

    status_counter = Counter(settlement.get("status", "unknown") for settlement in filtered)
    currency_counter = Counter(settlement.get("currency", "CNY") for settlement in filtered)
    
    total_amount = sum(settlement.get("amount", 0) for settlement in filtered)
    total_received = sum(settlement.get("received_amount", 0) for settlement in page_items)

    return {
        "success": True,
        "page": page,
        "page_size": page_size,
        "total": total,
        "settlements": page_items,
        "status_distribution": {_finance_status(k): v for k, v in status_counter.items()},
        "currency_distribution": currency_counter,
        "total_amount": round(total_amount, 2),
        "total_received": round(total_received, 2),
    }


@router.post("/")
async def create_settlement(payload: FinanceSettlementCreateRequest):
    """创建财务结算单（本地回写ERP11环节）"""
    data = payload.dict(exclude_none=True)
    settlement_id = f"FIN-{datetime.now(timezone.utc).strftime('%y%m%d%H%M%S')}"
    data["settlement_id"] = settlement_id
    data.setdefault("status", "awaiting_invoice")
    data.setdefault("received", 0.0)
    data.setdefault("currency", "CNY")
    
    # 设置默认维度评分
    if not data.get("dimensions"):
        data["dimensions"] = {dim: 0.75 for dim in DIMENSIONS}
    
    data.setdefault("created_at", _now())
    erp_process_service.finance.append(data)
    
    return {
        "success": True,
        "settlement": data,
        "message": "财务结算单创建成功"
    }


@router.get("/{settlement_id}")
async def get_settlement_detail(settlement_id: str):
    """单个结算单 + 生命周期 + 8维度"""
    settlement = _find_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="财务结算单不存在")

    # 计算收款信息
    amount = settlement.get("amount", 0)
    received_ratio = settlement.get("received", 0)
    received_amount = amount * received_ratio
    outstanding_amount = amount * (1 - received_ratio)
    
    lifecycle_steps = BASE_STAGE_LIFECYCLES.get("finance_settlement", [])
    status_mapping = {
        "awaiting_invoice": 0,
        "invoiced": 1,
        "awaiting_reconciliation": 2,
        "reconciled": 2,
        "in_collection": 3,
        "partially_collected": 3,
        "collected": 4,
        "written_off": 4,
        "closed": len(lifecycle_steps),
        "cancelled": 0,
    }
    current_index = status_mapping.get(settlement.get("status"), 0)
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
    for dim, score in (settlement.get("dimensions") or {}).items():
        dimensions.append(
            {
                "dimension": dim,
                "score": round(score, 3),
                "status": _dimension_status(score),
            }
        )

    # 账龄计算
    age_days = None
    if settlement.get("due_date"):
        try:
            due = datetime.fromisoformat(settlement.get("due_date").replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - due).days
        except Exception:
            pass
    
    insights = []
    if _is_overdue(settlement):
        insights.append("⚠️ 结算单已逾期，建议催收")
    if received_ratio >= 1.0 and settlement.get("status") != "closed":
        insights.append("✅ 已全额收款，可结案")
    if received_ratio == 0 and settlement.get("status") in ("invoiced", "reconciled"):
        insights.append("💰 已开票/对账，等待收款")
    if outstanding_amount > 0 and age_days and age_days > 90:
        insights.append("🔴 账龄超过90天，风险较高")
    if settlement.get("amount", 0) > 1000000:
        insights.append("💎 大额结算单，建议重点关注")

    return {
        "success": True,
        "settlement": settlement,
        "status_label": _finance_status(settlement.get("status", "unknown")),
        "is_overdue": _is_overdue(settlement),
        "lifecycle": lifecycle,
        "dimension_breakdown": dimensions,
        "financial_summary": {
            "total_amount": round(amount, 2),
            "received_amount": round(received_amount, 2),
            "outstanding_amount": round(outstanding_amount, 2),
            "collection_rate": round(received_ratio * 100, 2),
            "age_days": age_days,
        },
        "insights": insights,
    }


@router.patch("/{settlement_id}")
async def update_settlement(settlement_id: str, payload: FinanceSettlementUpdateRequest):
    """更新结算单（状态/金额/收款等）"""
    settlement = _find_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="财务结算单不存在")

    # 更新字段
    if payload.status:
        settlement["status"] = payload.status
    if payload.amount is not None:
        settlement["amount"] = payload.amount
    if payload.currency:
        settlement["currency"] = payload.currency
    if payload.due_date:
        settlement["due_date"] = payload.due_date
    if payload.received is not None:
        settlement["received"] = payload.received
        # 如果收款比例达到1.0，自动更新状态
        if payload.received >= 1.0 and settlement.get("status") not in ("closed", "collected"):
            settlement["status"] = "collected"
    if payload.received_amount is not None:
        amount = settlement.get("amount", 0)
        if amount > 0:
            settlement["received"] = min(1.0, payload.received_amount / amount)
    if payload.invoice_number:
        settlement["invoice_number"] = payload.invoice_number
    if payload.invoice_date:
        settlement["invoice_date"] = payload.invoice_date
        if settlement.get("status") == "awaiting_invoice":
            settlement["status"] = "invoiced"
    if payload.reconciliation_date:
        settlement["reconciliation_date"] = payload.reconciliation_date
        if settlement.get("status") == "invoiced":
            settlement["status"] = "reconciled"
    if payload.collection_date:
        settlement["collection_date"] = payload.collection_date

    # 记录变更历史
    history = settlement.setdefault("change_history", [])
    history.append(
        {
            "type": "update",
            "fields": payload.dict(exclude_none=True, exclude={"note"}),
            "note": payload.note,
            "timestamp": _now(),
        }
    )
    settlement["updated_at"] = _now()
    
    return {"success": True, "settlement": settlement}


@router.post("/{settlement_id}/payment")
async def record_payment(settlement_id: str, payment: PaymentRecord):
    """记录收款"""
    settlement = _find_settlement(settlement_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="财务结算单不存在")

    # 记录收款
    payment_record = payment.dict(exclude_none=True)
    payment_record["recorded_at"] = _now()
    payments = settlement.setdefault("payment_records", [])
    payments.append(payment_record)
    
    # 更新收款金额和比例
    total_received = sum(p.get("payment_amount", 0) for p in payments)
    amount = settlement.get("amount", 0)
    if amount > 0:
        settlement["received"] = min(1.0, total_received / amount)
        if settlement["received"] >= 1.0:
            settlement["status"] = "collected"
            settlement["collection_date"] = payment.payment_date
        elif settlement["received"] > 0:
            settlement["status"] = "partially_collected"
    
    settlement["updated_at"] = _now()
    
    return {
        "success": True,
        "settlement": settlement,
        "payment_record": payment_record,
        "message": "收款记录成功"
    }


@router.get("/analytics/dimensions")
async def analyze_dimensions():
    """8维度宏观对比"""
    dimension_analysis = erp_process_service.get_dimension_analysis("finance_settlement")
    settlements = _finance_source()
    avg_dimension = defaultdict(list)
    for settlement in settlements:
        for dim, score in (settlement.get("dimensions") or {}).items():
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
        "settlement_sample_size": len(settlements),
    }


@router.get("/analytics/collection")
async def analyze_collection_performance():
    """收款绩效分析"""
    settlements = _finance_source()
    
    # 总体收款率
    total_amount = sum(s.get("amount", 0) for s in settlements)
    total_received = sum(s.get("amount", 0) * s.get("received", 0) for s in settlements)
    collection_rate = (total_received / total_amount * 100) if total_amount > 0 else 0
    
    # 按订单统计收款
    order_collection = defaultdict(lambda: {"amount": 0.0, "received": 0.0, "count": 0})
    for settlement in settlements:
        order_id = settlement.get("order_id", "未知")
        amount = settlement.get("amount", 0)
        received = amount * settlement.get("received", 0)
        order_collection[order_id]["amount"] += amount
        order_collection[order_id]["received"] += received
        order_collection[order_id]["count"] += 1
    
    order_stats = []
    for order_id, stats in order_collection.items():
        rate = (stats["received"] / stats["amount"] * 100) if stats["amount"] > 0 else 0
        order_stats.append({
            "order_id": order_id,
            "settlement_count": stats["count"],
            "total_amount": round(stats["amount"], 2),
            "total_received": round(stats["received"], 2),
            "collection_rate": round(rate, 2),
        })
    
    order_stats.sort(key=lambda x: x["collection_rate"], reverse=True)
    
    # 按币种统计
    currency_collection = defaultdict(lambda: {"amount": 0.0, "received": 0.0})
    for settlement in settlements:
        currency = settlement.get("currency", "CNY")
        amount = settlement.get("amount", 0)
        received = amount * settlement.get("received", 0)
        currency_collection[currency]["amount"] += amount
        currency_collection[currency]["received"] += received
    
    currency_stats = []
    for currency, stats in currency_collection.items():
        rate = (stats["received"] / stats["amount"] * 100) if stats["amount"] > 0 else 0
        currency_stats.append({
            "currency": currency,
            "total_amount": round(stats["amount"], 2),
            "total_received": round(stats["received"], 2),
            "collection_rate": round(rate, 2),
        })
    
    currency_stats.sort(key=lambda x: x["collection_rate"], reverse=True)
    
    return {
        "success": True,
        "overall_collection_rate": round(collection_rate, 2),
        "total_amount": round(total_amount, 2),
        "total_received": round(total_received, 2),
        "order_collection": order_stats[:20],  # 返回前20个订单
        "currency_collection": currency_stats,
    }


@router.get("/analytics/aging")
async def analyze_aging():
    """账龄分析"""
    settlements = _finance_source()
    
    # 账龄分布
    age_distribution = _calculate_age_distribution(settlements)
    
    # 按账龄统计金额
    age_amounts = {
        "0-30天": 0.0,
        "31-60天": 0.0,
        "61-90天": 0.0,
        "91-180天": 0.0,
        "180天以上": 0.0,
    }
    
    for settlement in settlements:
        if settlement.get("status") in ("closed", "collected", "cancelled"):
            continue
        due_date = settlement.get("due_date")
        if not due_date:
            continue
        try:
            due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - due).days
            amount = settlement.get("amount", 0) * (1 - settlement.get("received", 0))
            if days <= 0:
                age_amounts["0-30天"] += amount
            elif days <= 30:
                age_amounts["0-30天"] += amount
            elif days <= 60:
                age_amounts["31-60天"] += amount
            elif days <= 90:
                age_amounts["61-90天"] += amount
            elif days <= 180:
                age_amounts["91-180天"] += amount
            else:
                age_amounts["180天以上"] += amount
        except Exception:
            pass
    
    # 高风险账龄（90天以上）
    high_risk_settlements = []
    for settlement in settlements:
        if settlement.get("status") in ("closed", "collected", "cancelled"):
            continue
        due_date = settlement.get("due_date")
        if not due_date:
            continue
        try:
            due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - due).days
            if days > 90:
                outstanding = settlement.get("amount", 0) * (1 - settlement.get("received", 0))
                high_risk_settlements.append({
                    "settlement_id": settlement.get("settlement_id"),
                    "order_id": settlement.get("order_id"),
                    "customer": settlement.get("customer"),
                    "outstanding_amount": round(outstanding, 2),
                    "age_days": days,
                    "due_date": due_date,
                })
        except Exception:
            pass
    
    high_risk_settlements.sort(key=lambda x: x["age_days"], reverse=True)
    
    return {
        "success": True,
        "age_distribution": age_distribution,
        "age_amounts": {k: round(v, 2) for k, v in age_amounts.items()},
        "total_outstanding": round(sum(age_amounts.values()), 2),
        "high_risk_settlements": high_risk_settlements[:20],  # 返回前20个高风险
    }

