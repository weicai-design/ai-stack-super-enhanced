"""
交付管理模块
实现完整的交付计划、执行、跟踪功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class DeliveryStatus(Enum):
    """交付状态"""
    PLANNED = "planned"  # 已计划
    CONFIRMED = "confirmed"  # 已确认
    PREPARING = "preparing"  # 准备中
    READY = "ready"  # 就绪
    IN_DELIVERY = "in_delivery"  # 配送中
    DELIVERED = "delivered"  # 已交付
    ACCEPTED = "accepted"  # 已验收
    REJECTED = "rejected"  # 已拒收
    CANCELLED = "cancelled"  # 已取消


class DeliveryType(Enum):
    """交付类型"""
    NORMAL = "normal"  # 正常交付
    URGENT = "urgent"  # 紧急交付
    PARTIAL = "partial"  # 部分交付
    DIRECT = "direct"  # 直送
    THIRD_PARTY = "third_party"  # 第三方物流


class DeliveryManager:
    """交付管理器"""
    
    def __init__(self):
        """初始化交付管理器"""
        self.delivery_plans = {}
        self.delivery_orders = {}
        self.packing_lists = {}
        self.delivery_notes = {}
        self.acceptance_records = {}
        self.order_counter = 1000
    
    def create_delivery_plan(
        self,
        sales_order_id: str,
        customer_id: str,
        delivery_date: str,
        items: List[Dict[str, Any]],
        delivery_address: Dict[str, Any],
        delivery_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        创建交付计划
        
        Args:
            sales_order_id: 销售订单ID
            customer_id: 客户ID
            delivery_date: 计划交付日期
            items: 交付物料 [{"material_id": "", "quantity": 0, "unit": ""}]
            delivery_address: 交付地址
            delivery_type: 交付类型
        
        Returns:
            交付计划信息
        """
        plan_id = f"DP{datetime.now().strftime('%Y%m%d')}{self.order_counter:04d}"
        self.order_counter += 1
        
        plan = {
            "plan_id": plan_id,
            "sales_order_id": sales_order_id,
            "customer_id": customer_id,
            "delivery_date": delivery_date,
            "items": items,
            "delivery_address": delivery_address,
            "delivery_type": delivery_type,
            "status": DeliveryStatus.PLANNED.value,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "confirmed_at": None,
            "actual_delivery_date": None
        }
        
        self.delivery_plans[plan_id] = plan
        
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "交付计划已创建",
            "plan": plan
        }
    
    def confirm_delivery_plan(
        self,
        plan_id: str,
        confirmer: str,
        confirmed_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        确认交付计划
        
        Args:
            plan_id: 计划ID
            confirmer: 确认人
            confirmed_date: 确认的交付日期
        
        Returns:
            确认结果
        """
        if plan_id not in self.delivery_plans:
            return {"success": False, "error": "交付计划不存在"}
        
        plan = self.delivery_plans[plan_id]
        
        if confirmed_date:
            plan["delivery_date"] = confirmed_date
        
        plan["status"] = DeliveryStatus.CONFIRMED.value
        plan["confirmed_at"] = datetime.now().isoformat()
        plan["confirmed_by"] = confirmer
        
        # 自动创建交付订单
        do_result = self.create_delivery_order(plan_id)
        
        return {
            "success": True,
            "message": "交付计划已确认",
            "plan": plan,
            "delivery_order": do_result.get("order")
        }
    
    def create_delivery_order(
        self,
        plan_id: str
    ) -> Dict[str, Any]:
        """
        创建交付订单
        
        Args:
            plan_id: 交付计划ID
        
        Returns:
            交付订单信息
        """
        if plan_id not in self.delivery_plans:
            return {"success": False, "error": "交付计划不存在"}
        
        plan = self.delivery_plans[plan_id]
        
        if plan["status"] != DeliveryStatus.CONFIRMED.value:
            return {"success": False, "error": "交付计划未确认"}
        
        order_id = f"DO{datetime.now().strftime('%Y%m%d')}{len(self.delivery_orders) + 1:04d}"
        
        order = {
            "order_id": order_id,
            "plan_id": plan_id,
            "sales_order_id": plan["sales_order_id"],
            "customer_id": plan["customer_id"],
            "items": plan["items"],
            "delivery_date": plan["delivery_date"],
            "delivery_address": plan["delivery_address"],
            "delivery_type": plan["delivery_type"],
            "status": DeliveryStatus.PREPARING.value,
            "created_at": datetime.now().isoformat(),
            "packing_list_id": None,
            "delivery_note_id": None,
            "tracking_number": None
        }
        
        self.delivery_orders[order_id] = order
        plan["delivery_order_id"] = order_id
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "交付订单已创建",
            "order": order
        }
    
    def create_packing_list(
        self,
        order_id: str,
        packed_items: List[Dict[str, Any]],
        packer: str,
        package_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建装箱单
        
        Args:
            order_id: 交付订单ID
            packed_items: 装箱物料 [{"material_id": "", "quantity": 0, "box_number": ""}]
            packer: 打包人
            package_info: 包装信息 {"boxes": 0, "weight": 0, "volume": 0}
        
        Returns:
            装箱单信息
        """
        if order_id not in self.delivery_orders:
            return {"success": False, "error": "交付订单不存在"}
        
        order = self.delivery_orders[order_id]
        
        packing_list_id = f"PL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        packing_list = {
            "packing_list_id": packing_list_id,
            "order_id": order_id,
            "packed_items": packed_items,
            "package_info": package_info,
            "packer": packer,
            "packed_at": datetime.now().isoformat(),
            "verified": False,
            "verified_by": None
        }
        
        self.packing_lists[packing_list_id] = packing_list
        order["packing_list_id"] = packing_list_id
        order["status"] = DeliveryStatus.READY.value
        
        return {
            "success": True,
            "packing_list_id": packing_list_id,
            "message": "装箱单已创建",
            "packing_list": packing_list
        }
    
    def create_delivery_note(
        self,
        order_id: str,
        driver: str,
        vehicle_number: str,
        carrier: str = "",
        estimated_delivery_time: str = ""
    ) -> Dict[str, Any]:
        """
        创建发货单
        
        Args:
            order_id: 交付订单ID
            driver: 司机
            vehicle_number: 车牌号
            carrier: 承运商
            estimated_delivery_time: 预计送达时间
        
        Returns:
            发货单信息
        """
        if order_id not in self.delivery_orders:
            return {"success": False, "error": "交付订单不存在"}
        
        order = self.delivery_orders[order_id]
        
        if order["status"] != DeliveryStatus.READY.value:
            return {"success": False, "error": "交付订单未就绪"}
        
        delivery_note_id = f"DN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        tracking_number = f"TRK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        delivery_note = {
            "delivery_note_id": delivery_note_id,
            "order_id": order_id,
            "tracking_number": tracking_number,
            "driver": driver,
            "vehicle_number": vehicle_number,
            "carrier": carrier,
            "estimated_delivery_time": estimated_delivery_time,
            "shipped_at": datetime.now().isoformat(),
            "delivery_status_updates": []
        }
        
        self.delivery_notes[delivery_note_id] = delivery_note
        order["delivery_note_id"] = delivery_note_id
        order["tracking_number"] = tracking_number
        order["status"] = DeliveryStatus.IN_DELIVERY.value
        
        return {
            "success": True,
            "delivery_note_id": delivery_note_id,
            "tracking_number": tracking_number,
            "message": "发货单已创建，货物已发出",
            "delivery_note": delivery_note
        }
    
    def update_delivery_status(
        self,
        tracking_number: str,
        status_update: str,
        location: str = "",
        remarks: str = ""
    ) -> Dict[str, Any]:
        """
        更新配送状态
        
        Args:
            tracking_number: 追踪号
            status_update: 状态更新
            location: 当前位置
            remarks: 备注
        
        Returns:
            更新结果
        """
        # 查找发货单
        delivery_note = None
        for dn in self.delivery_notes.values():
            if dn["tracking_number"] == tracking_number:
                delivery_note = dn
                break
        
        if not delivery_note:
            return {"success": False, "error": "追踪号不存在"}
        
        status_record = {
            "status": status_update,
            "location": location,
            "remarks": remarks,
            "timestamp": datetime.now().isoformat()
        }
        
        delivery_note["delivery_status_updates"].append(status_record)
        
        return {
            "success": True,
            "message": "配送状态已更新",
            "status_record": status_record
        }
    
    def record_delivery_completion(
        self,
        order_id: str,
        delivered_at: str,
        receiver: str,
        signature: str = ""
    ) -> Dict[str, Any]:
        """
        记录交付完成
        
        Args:
            order_id: 交付订单ID
            delivered_at: 送达时间
            receiver: 收货人
            signature: 签名
        
        Returns:
            交付记录
        """
        if order_id not in self.delivery_orders:
            return {"success": False, "error": "交付订单不存在"}
        
        order = self.delivery_orders[order_id]
        
        order["status"] = DeliveryStatus.DELIVERED.value
        order["delivered_at"] = delivered_at
        order["receiver"] = receiver
        order["signature"] = signature
        
        # 更新计划的实际交付日期
        if order["plan_id"] in self.delivery_plans:
            plan = self.delivery_plans[order["plan_id"]]
            plan["actual_delivery_date"] = delivered_at[:10]
        
        return {
            "success": True,
            "message": "交付已完成",
            "order": order
        }
    
    def create_acceptance_record(
        self,
        order_id: str,
        accepted_items: List[Dict[str, Any]],
        inspector: str,
        acceptance_result: str,
        issues: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建验收记录
        
        Args:
            order_id: 交付订单ID
            accepted_items: 验收物料 [{"material_id": "", "quantity": 0, "quality": "pass/fail"}]
            inspector: 验收人
            acceptance_result: 验收结果 (accepted/rejected/conditional)
            issues: 问题列表
        
        Returns:
            验收记录
        """
        if order_id not in self.delivery_orders:
            return {"success": False, "error": "交付订单不存在"}
        
        order = self.delivery_orders[order_id]
        
        if order["status"] != DeliveryStatus.DELIVERED.value:
            return {"success": False, "error": "货物尚未送达"}
        
        acceptance_id = f"AC{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        acceptance_record = {
            "acceptance_id": acceptance_id,
            "order_id": order_id,
            "accepted_items": accepted_items,
            "inspector": inspector,
            "acceptance_result": acceptance_result,
            "issues": issues or [],
            "accepted_at": datetime.now().isoformat()
        }
        
        self.acceptance_records[acceptance_id] = acceptance_record
        
        # 更新订单状态
        if acceptance_result == "accepted":
            order["status"] = DeliveryStatus.ACCEPTED.value
        elif acceptance_result == "rejected":
            order["status"] = DeliveryStatus.REJECTED.value
        
        order["acceptance_id"] = acceptance_id
        
        return {
            "success": True,
            "acceptance_id": acceptance_id,
            "message": f"验收已完成: {acceptance_result}",
            "acceptance_record": acceptance_record
        }
    
    def get_delivery_performance(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取交付绩效
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            绩效报告
        """
        # 筛选时间范围内的计划
        plans_in_range = [
            plan for plan in self.delivery_plans.values()
            if start_date <= plan["created_at"][:10] <= end_date
        ]
        
        total_plans = len(plans_in_range)
        
        # 准时交付率
        on_time_deliveries = 0
        total_deliveries = 0
        
        for plan in plans_in_range:
            if plan.get("actual_delivery_date"):
                total_deliveries += 1
                if plan["actual_delivery_date"] <= plan["delivery_date"]:
                    on_time_deliveries += 1
        
        on_time_rate = (on_time_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        # 验收通过率
        accepted = 0
        rejected = 0
        
        for acceptance in self.acceptance_records.values():
            order = self.delivery_orders.get(acceptance["order_id"], {})
            plan_id = order.get("plan_id")
            
            if plan_id and plan_id in [p["plan_id"] for p in plans_in_range]:
                if acceptance["acceptance_result"] == "accepted":
                    accepted += 1
                elif acceptance["acceptance_result"] == "rejected":
                    rejected += 1
        
        total_acceptance = accepted + rejected
        acceptance_rate = (accepted / total_acceptance * 100) if total_acceptance > 0 else 0
        
        # 按交付类型统计
        by_type = {}
        for plan in plans_in_range:
            dtype = plan["delivery_type"]
            by_type[dtype] = by_type.get(dtype, 0) + 1
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_plans": total_plans,
                "total_deliveries": total_deliveries,
                "on_time_deliveries": on_time_deliveries,
                "on_time_rate": round(on_time_rate, 2)
            },
            "acceptance": {
                "total": total_acceptance,
                "accepted": accepted,
                "rejected": rejected,
                "acceptance_rate": round(acceptance_rate, 2)
            },
            "by_type": by_type
        }
    
    def get_tracking_info(
        self,
        tracking_number: str
    ) -> Dict[str, Any]:
        """
        获取追踪信息
        
        Args:
            tracking_number: 追踪号
        
        Returns:
            追踪信息
        """
        # 查找发货单
        delivery_note = None
        for dn in self.delivery_notes.values():
            if dn["tracking_number"] == tracking_number:
                delivery_note = dn
                break
        
        if not delivery_note:
            return {"success": False, "error": "追踪号不存在"}
        
        order = self.delivery_orders.get(delivery_note["order_id"], {})
        
        return {
            "success": True,
            "tracking_number": tracking_number,
            "order_id": delivery_note["order_id"],
            "current_status": order.get("status"),
            "shipped_at": delivery_note["shipped_at"],
            "estimated_delivery": delivery_note.get("estimated_delivery_time"),
            "status_updates": delivery_note["delivery_status_updates"],
            "carrier": delivery_note.get("carrier"),
            "driver": delivery_note.get("driver"),
            "vehicle": delivery_note.get("vehicle_number")
        }


# 创建默认实例
default_delivery_manager = DeliveryManager()

