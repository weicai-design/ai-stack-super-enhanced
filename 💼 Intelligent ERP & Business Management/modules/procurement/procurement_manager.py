#!/usr/bin/env python3
"""
采购管理系统
Procurement Management System

功能：
- 采购计划管理
- 供应商管理
- 采购订单管理
- 采购执行跟踪
- 采购成本分析
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class ProcurementStatus(Enum):
    """采购状态"""
    PLANNED = "planned"  # 已计划
    APPROVED = "approved"  # 已批准
    ORDERED = "ordered"  # 已下单
    PARTIAL_RECEIVED = "partial_received"  # 部分到货
    RECEIVED = "received"  # 已到货
    CANCELLED = "cancelled"  # 已取消


class SupplierLevel(Enum):
    """供应商等级"""
    A = "A级供应商"  # 优秀
    B = "B级供应商"  # 良好
    C = "C级供应商"  # 一般
    D = "D级供应商"  # 待改进


class ProcurementManager:
    """采购管理器"""
    
    def __init__(self):
        """初始化采购管理器"""
        self.procurement_plans: Dict[str, Dict[str, Any]] = {}
        self.purchase_orders: Dict[str, Dict[str, Any]] = {}
        self.suppliers: Dict[str, Dict[str, Any]] = {}
        self.material_requirements: Dict[str, Dict[str, Any]] = {}
        
    # ==================== 采购计划管理 ====================
    
    def create_procurement_plan(
        self,
        plan_id: str,
        material_id: str,
        material_name: str,
        quantity: float,
        unit: str,
        required_date: str,
        budget: float,
        priority: str = "normal",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建采购计划
        
        Args:
            plan_id: 计划ID
            material_id: 物料ID
            material_name: 物料名称
            quantity: 采购数量
            unit: 单位
            required_date: 需求日期
            budget: 预算
            priority: 优先级（urgent/high/normal/low）
            notes: 备注
        
        Returns:
            采购计划信息
        """
        plan = {
            "plan_id": plan_id,
            "material_id": material_id,
            "material_name": material_name,
            "quantity": quantity,
            "unit": unit,
            "required_date": required_date,
            "budget": budget,
            "priority": priority,
            "status": ProcurementStatus.PLANNED.value,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "approved_at": None,
            "approved_by": None
        }
        
        self.procurement_plans[plan_id] = plan
        return plan
    
    def approve_procurement_plan(
        self,
        plan_id: str,
        approved_by: str,
        approved_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        批准采购计划
        
        Args:
            plan_id: 计划ID
            approved_by: 批准人
            approved_budget: 批准预算（可选）
        
        Returns:
            更新后的计划信息
        """
        if plan_id not in self.procurement_plans:
            raise ValueError(f"采购计划 {plan_id} 不存在")
        
        plan = self.procurement_plans[plan_id]
        plan["status"] = ProcurementStatus.APPROVED.value
        plan["approved_at"] = datetime.now().isoformat()
        plan["approved_by"] = approved_by
        
        if approved_budget is not None:
            plan["approved_budget"] = approved_budget
        else:
            plan["approved_budget"] = plan["budget"]
        
        return plan
    
    def get_procurement_plans(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取采购计划列表
        
        Args:
            status: 状态筛选
            priority: 优先级筛选
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            采购计划列表
        """
        plans = list(self.procurement_plans.values())
        
        # 状态筛选
        if status:
            plans = [p for p in plans if p["status"] == status]
        
        # 优先级筛选
        if priority:
            plans = [p for p in plans if p["priority"] == priority]
        
        # 日期筛选
        if start_date:
            plans = [p for p in plans if p["required_date"] >= start_date]
        if end_date:
            plans = [p for p in plans if p["required_date"] <= end_date]
        
        # 按需求日期排序
        plans.sort(key=lambda x: x["required_date"])
        
        return plans
    
    # ==================== 采购订单管理 ====================
    
    def create_purchase_order(
        self,
        order_id: str,
        plan_id: str,
        supplier_id: str,
        material_id: str,
        material_name: str,
        quantity: float,
        unit: str,
        unit_price: float,
        total_amount: float,
        delivery_date: str,
        payment_terms: str = "Net 30",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建采购订单
        
        Args:
            order_id: 订单ID
            plan_id: 关联的采购计划ID
            supplier_id: 供应商ID
            material_id: 物料ID
            material_name: 物料名称
            quantity: 采购数量
            unit: 单位
            unit_price: 单价
            total_amount: 总金额
            delivery_date: 交货日期
            payment_terms: 付款条款
            notes: 备注
        
        Returns:
            采购订单信息
        """
        order = {
            "order_id": order_id,
            "plan_id": plan_id,
            "supplier_id": supplier_id,
            "material_id": material_id,
            "material_name": material_name,
            "quantity": quantity,
            "unit": unit,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "delivery_date": delivery_date,
            "payment_terms": payment_terms,
            "status": ProcurementStatus.ORDERED.value,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "received_quantity": 0,
            "received_dates": [],
            "cancelled": False
        }
        
        self.purchase_orders[order_id] = order
        
        # 更新采购计划状态
        if plan_id in self.procurement_plans:
            self.procurement_plans[plan_id]["status"] = ProcurementStatus.ORDERED.value
            self.procurement_plans[plan_id]["order_id"] = order_id
        
        return order
    
    def receive_material(
        self,
        order_id: str,
        received_quantity: float,
        received_date: Optional[str] = None,
        quality_status: str = "passed",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        物料到货登记
        
        Args:
            order_id: 订单ID
            received_quantity: 到货数量
            received_date: 到货日期
            quality_status: 质量状态（passed/failed/pending）
            notes: 备注
        
        Returns:
            更新后的订单信息
        """
        if order_id not in self.purchase_orders:
            raise ValueError(f"采购订单 {order_id} 不存在")
        
        order = self.purchase_orders[order_id]
        
        if received_date is None:
            received_date = datetime.now().isoformat()
        
        # 记录到货信息
        receive_record = {
            "quantity": received_quantity,
            "date": received_date,
            "quality_status": quality_status,
            "notes": notes
        }
        order["received_dates"].append(receive_record)
        
        # 更新已到货数量
        if quality_status == "passed":
            order["received_quantity"] += received_quantity
        
        # 更新订单状态
        if order["received_quantity"] >= order["quantity"]:
            order["status"] = ProcurementStatus.RECEIVED.value
        elif order["received_quantity"] > 0:
            order["status"] = ProcurementStatus.PARTIAL_RECEIVED.value
        
        return order
    
    def cancel_purchase_order(
        self,
        order_id: str,
        reason: str,
        cancelled_by: str
    ) -> Dict[str, Any]:
        """
        取消采购订单
        
        Args:
            order_id: 订单ID
            reason: 取消原因
            cancelled_by: 取消人
        
        Returns:
            更新后的订单信息
        """
        if order_id not in self.purchase_orders:
            raise ValueError(f"采购订单 {order_id} 不存在")
        
        order = self.purchase_orders[order_id]
        order["status"] = ProcurementStatus.CANCELLED.value
        order["cancelled"] = True
        order["cancel_reason"] = reason
        order["cancelled_by"] = cancelled_by
        order["cancelled_at"] = datetime.now().isoformat()
        
        return order
    
    # ==================== 供应商管理 ====================
    
    def add_supplier(
        self,
        supplier_id: str,
        name: str,
        contact_person: str,
        phone: str,
        email: str,
        address: str,
        materials: List[str],
        level: str = "C",
        payment_terms: str = "Net 30",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        添加供应商
        
        Args:
            supplier_id: 供应商ID
            name: 供应商名称
            contact_person: 联系人
            phone: 电话
            email: 邮箱
            address: 地址
            materials: 可供应物料列表
            level: 供应商等级（A/B/C/D）
            payment_terms: 付款条款
            notes: 备注
        
        Returns:
            供应商信息
        """
        supplier = {
            "supplier_id": supplier_id,
            "name": name,
            "contact_person": contact_person,
            "phone": phone,
            "email": email,
            "address": address,
            "materials": materials,
            "level": level,
            "payment_terms": payment_terms,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "total_orders": 0,
            "total_amount": 0.0,
            "on_time_delivery_rate": 100.0,
            "quality_pass_rate": 100.0,
            "last_order_date": None
        }
        
        self.suppliers[supplier_id] = supplier
        return supplier
    
    def update_supplier_performance(
        self,
        supplier_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        更新供应商绩效
        
        Args:
            supplier_id: 供应商ID
            order_id: 订单ID
        
        Returns:
            更新后的供应商信息
        """
        if supplier_id not in self.suppliers:
            raise ValueError(f"供应商 {supplier_id} 不存在")
        
        if order_id not in self.purchase_orders:
            raise ValueError(f"采购订单 {order_id} 不存在")
        
        supplier = self.suppliers[supplier_id]
        order = self.purchase_orders[order_id]
        
        # 更新订单统计
        supplier["total_orders"] += 1
        supplier["total_amount"] += order["total_amount"]
        supplier["last_order_date"] = order["created_at"]
        
        # 计算准时交货率
        if order["status"] == ProcurementStatus.RECEIVED.value:
            delivery_date = datetime.fromisoformat(order["delivery_date"])
            last_received = datetime.fromisoformat(order["received_dates"][-1]["date"])
            
            if last_received <= delivery_date:
                # 准时交货
                pass
            else:
                # 延迟交货，降低准时率
                supplier["on_time_delivery_rate"] = (
                    supplier["on_time_delivery_rate"] * 0.95
                )
        
        # 计算质量合格率
        passed_quantity = sum(
            r["quantity"] for r in order["received_dates"]
            if r["quality_status"] == "passed"
        )
        total_received = order["received_quantity"]
        
        if total_received > 0:
            order_quality_rate = (passed_quantity / total_received) * 100
            # 加权平均
            supplier["quality_pass_rate"] = (
                supplier["quality_pass_rate"] * 0.8 + order_quality_rate * 0.2
            )
        
        # 根据绩效更新供应商等级
        self._update_supplier_level(supplier_id)
        
        return supplier
    
    def _update_supplier_level(self, supplier_id: str):
        """
        根据绩效更新供应商等级
        
        Args:
            supplier_id: 供应商ID
        """
        supplier = self.suppliers[supplier_id]
        
        on_time_rate = supplier["on_time_delivery_rate"]
        quality_rate = supplier["quality_pass_rate"]
        
        # 综合评分
        score = on_time_rate * 0.5 + quality_rate * 0.5
        
        if score >= 95:
            supplier["level"] = "A"
        elif score >= 85:
            supplier["level"] = "B"
        elif score >= 75:
            supplier["level"] = "C"
        else:
            supplier["level"] = "D"
    
    def get_supplier_list(
        self,
        level: Optional[str] = None,
        material: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取供应商列表
        
        Args:
            level: 等级筛选
            material: 物料筛选
        
        Returns:
            供应商列表
        """
        suppliers = list(self.suppliers.values())
        
        if level:
            suppliers = [s for s in suppliers if s["level"] == level]
        
        if material:
            suppliers = [s for s in suppliers if material in s["materials"]]
        
        # 按等级和总金额排序
        level_order = {"A": 0, "B": 1, "C": 2, "D": 3}
        suppliers.sort(
            key=lambda x: (level_order.get(x["level"], 99), -x["total_amount"])
        )
        
        return suppliers
    
    # ==================== 采购分析 ====================
    
    def analyze_procurement_cost(
        self,
        start_date: str,
        end_date: str,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """
        采购成本分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组方式（day/week/month/quarter/year）
        
        Returns:
            成本分析结果
        """
        # 筛选日期范围内的订单
        orders = [
            o for o in self.purchase_orders.values()
            if start_date <= o["created_at"][:10] <= end_date
        ]
        
        # 统计
        total_orders = len(orders)
        total_amount = sum(o["total_amount"] for o in orders)
        avg_amount = total_amount / total_orders if total_orders > 0 else 0
        
        # 按物料分组
        material_costs = {}
        for order in orders:
            material_id = order["material_id"]
            if material_id not in material_costs:
                material_costs[material_id] = {
                    "material_name": order["material_name"],
                    "quantity": 0,
                    "amount": 0,
                    "orders": 0
                }
            
            material_costs[material_id]["quantity"] += order["quantity"]
            material_costs[material_id]["amount"] += order["total_amount"]
            material_costs[material_id]["orders"] += 1
        
        # 按供应商分组
        supplier_costs = {}
        for order in orders:
            supplier_id = order["supplier_id"]
            if supplier_id not in supplier_costs:
                supplier_costs[supplier_id] = {
                    "supplier_name": self.suppliers.get(supplier_id, {}).get("name", "未知"),
                    "amount": 0,
                    "orders": 0
                }
            
            supplier_costs[supplier_id]["amount"] += order["total_amount"]
            supplier_costs[supplier_id]["orders"] += 1
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_orders": total_orders,
                "total_amount": total_amount,
                "avg_amount": avg_amount
            },
            "by_material": material_costs,
            "by_supplier": supplier_costs,
            "top_materials": sorted(
                material_costs.items(),
                key=lambda x: x[1]["amount"],
                reverse=True
            )[:10],
            "top_suppliers": sorted(
                supplier_costs.items(),
                key=lambda x: x[1]["amount"],
                reverse=True
            )[:10]
        }
    
    def get_procurement_status_report(self) -> Dict[str, Any]:
        """
        获取采购状态报告
        
        Returns:
            采购状态报告
        """
        # 统计采购计划状态
        plan_status = {}
        for plan in self.procurement_plans.values():
            status = plan["status"]
            plan_status[status] = plan_status.get(status, 0) + 1
        
        # 统计采购订单状态
        order_status = {}
        for order in self.purchase_orders.values():
            status = order["status"]
            order_status[status] = order_status.get(status, 0) + 1
        
        # 统计供应商等级
        supplier_level = {}
        for supplier in self.suppliers.values():
            level = supplier["level"]
            supplier_level[level] = supplier_level.get(level, 0) + 1
        
        # 紧急采购
        urgent_plans = [
            p for p in self.procurement_plans.values()
            if p["priority"] == "urgent" and p["status"] != ProcurementStatus.RECEIVED.value
        ]
        
        # 延迟交货
        today = datetime.now().date()
        delayed_orders = []
        for order in self.purchase_orders.values():
            if order["status"] in [
                ProcurementStatus.ORDERED.value,
                ProcurementStatus.PARTIAL_RECEIVED.value
            ]:
                delivery_date = datetime.fromisoformat(order["delivery_date"]).date()
                if delivery_date < today:
                    delayed_orders.append(order)
        
        return {
            "plan_status": plan_status,
            "order_status": order_status,
            "supplier_level": supplier_level,
            "urgent_plans": len(urgent_plans),
            "urgent_plan_details": urgent_plans,
            "delayed_orders": len(delayed_orders),
            "delayed_order_details": delayed_orders,
            "total_plans": len(self.procurement_plans),
            "total_orders": len(self.purchase_orders),
            "total_suppliers": len(self.suppliers)
        }


# 创建全局实例
default_procurement_manager = ProcurementManager()

