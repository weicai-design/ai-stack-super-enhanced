"""
发运管理模块
实现完整的发运计划、调度、跟踪功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class ShipmentStatus(Enum):
    """发运状态"""
    PLANNED = "planned"  # 已计划
    SCHEDULED = "scheduled"  # 已排程
    LOADING = "loading"  # 装货中
    IN_TRANSIT = "in_transit"  # 运输中
    ARRIVED = "arrived"  # 已到达
    UNLOADING = "unloading"  # 卸货中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class TransportMode(Enum):
    """运输方式"""
    TRUCK = "truck"  # 卡车
    RAIL = "rail"  # 铁路
    AIR = "air"  # 航空
    SEA = "sea"  # 海运
    MULTIMODAL = "multimodal"  # 多式联运


class ShippingManager:
    """发运管理器"""
    
    def __init__(self):
        """初始化发运管理器"""
        self.shipment_plans = {}
        self.shipments = {}
        self.vehicles = {}
        self.routes = {}
        self.loading_records = {}
        self.transport_records = []
    
    def create_shipment_plan(
        self,
        delivery_orders: List[str],
        destination: str,
        transport_mode: str,
        planned_date: str,
        estimated_arrival: str
    ) -> Dict[str, Any]:
        """
        创建发运计划
        
        Args:
            delivery_orders: 交付订单列表
            destination: 目的地
            transport_mode: 运输方式
            planned_date: 计划发运日期
            estimated_arrival: 预计到达时间
        
        Returns:
            发运计划信息
        """
        plan_id = f"SP{datetime.now().strftime('%Y%m%d')}{len(self.shipment_plans) + 1:04d}"
        
        plan = {
            "plan_id": plan_id,
            "delivery_orders": delivery_orders,
            "destination": destination,
            "transport_mode": transport_mode,
            "planned_date": planned_date,
            "estimated_arrival": estimated_arrival,
            "status": ShipmentStatus.PLANNED.value,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "assigned_vehicle": None,
            "assigned_route": None
        }
        
        self.shipment_plans[plan_id] = plan
        
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "发运计划已创建",
            "plan": plan
        }
    
    def schedule_shipment(
        self,
        plan_id: str,
        vehicle_id: str,
        route_id: str,
        driver: str,
        departure_time: str
    ) -> Dict[str, Any]:
        """
        排程发运
        
        Args:
            plan_id: 发运计划ID
            vehicle_id: 车辆ID
            route_id: 路线ID
            driver: 司机
            departure_time: 出发时间
        
        Returns:
            排程结果
        """
        if plan_id not in self.shipment_plans:
            return {"success": False, "error": "发运计划不存在"}
        
        plan = self.shipment_plans[plan_id]
        
        # 检查车辆可用性
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            if vehicle.get("status") != "available":
                return {"success": False, "error": "车辆不可用"}
        
        shipment_id = f"SH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        shipment = {
            "shipment_id": shipment_id,
            "plan_id": plan_id,
            "vehicle_id": vehicle_id,
            "route_id": route_id,
            "driver": driver,
            "departure_time": departure_time,
            "status": ShipmentStatus.SCHEDULED.value,
            "created_at": datetime.now().isoformat(),
            "actual_departure": None,
            "actual_arrival": None,
            "checkpoints": []
        }
        
        self.shipments[shipment_id] = shipment
        plan["shipment_id"] = shipment_id
        plan["status"] = ShipmentStatus.SCHEDULED.value
        plan["assigned_vehicle"] = vehicle_id
        plan["assigned_route"] = route_id
        
        # 更新车辆状态
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]["status"] = "scheduled"
            self.vehicles[vehicle_id]["current_shipment"] = shipment_id
        
        return {
            "success": True,
            "shipment_id": shipment_id,
            "message": "发运已排程",
            "shipment": shipment
        }
    
    def start_loading(
        self,
        shipment_id: str,
        loader: str
    ) -> Dict[str, Any]:
        """
        开始装货
        
        Args:
            shipment_id: 发运ID
            loader: 装货员
        
        Returns:
            装货记录
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "发运不存在"}
        
        shipment = self.shipments[shipment_id]
        
        loading_id = f"LD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        loading_record = {
            "loading_id": loading_id,
            "shipment_id": shipment_id,
            "loader": loader,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "loaded_items": [],
            "photos": []
        }
        
        self.loading_records[loading_id] = loading_record
        shipment["status"] = ShipmentStatus.LOADING.value
        shipment["loading_id"] = loading_id
        
        return {
            "success": True,
            "loading_id": loading_id,
            "message": "装货已开始",
            "loading_record": loading_record
        }
    
    def complete_loading(
        self,
        loading_id: str,
        loaded_items: List[Dict[str, Any]],
        seal_number: str = ""
    ) -> Dict[str, Any]:
        """
        完成装货
        
        Args:
            loading_id: 装货ID
            loaded_items: 已装货物 [{"order_id": "", "boxes": 0, "weight": 0}]
            seal_number: 铅封号
        
        Returns:
            完成结果
        """
        if loading_id not in self.loading_records:
            return {"success": False, "error": "装货记录不存在"}
        
        loading_record = self.loading_records[loading_id]
        shipment = self.shipments[loading_record["shipment_id"]]
        
        loading_record["completed_at"] = datetime.now().isoformat()
        loading_record["loaded_items"] = loaded_items
        loading_record["seal_number"] = seal_number
        
        # 更新发运状态为运输中
        shipment["status"] = ShipmentStatus.IN_TRANSIT.value
        shipment["actual_departure"] = datetime.now().isoformat()
        
        # 更新车辆状态
        vehicle_id = shipment.get("vehicle_id")
        if vehicle_id and vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]["status"] = "in_transit"
        
        return {
            "success": True,
            "message": "装货已完成，车辆已出发",
            "loading_record": loading_record
        }
    
    def add_checkpoint(
        self,
        shipment_id: str,
        location: str,
        checkpoint_type: str,
        remarks: str = ""
    ) -> Dict[str, Any]:
        """
        添加检查点
        
        Args:
            shipment_id: 发运ID
            location: 位置
            checkpoint_type: 检查点类型 (departure/waypoint/arrival)
            remarks: 备注
        
        Returns:
            检查点记录
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "发运不存在"}
        
        shipment = self.shipments[shipment_id]
        
        checkpoint = {
            "location": location,
            "checkpoint_type": checkpoint_type,
            "timestamp": datetime.now().isoformat(),
            "remarks": remarks
        }
        
        shipment["checkpoints"].append(checkpoint)
        
        # 如果是到达检查点，更新状态
        if checkpoint_type == "arrival":
            shipment["status"] = ShipmentStatus.ARRIVED.value
            shipment["actual_arrival"] = datetime.now().isoformat()
            
            # 更新车辆状态
            vehicle_id = shipment.get("vehicle_id")
            if vehicle_id and vehicle_id in self.vehicles:
                self.vehicles[vehicle_id]["status"] = "arrived"
        
        return {
            "success": True,
            "message": f"检查点已记录: {checkpoint_type}",
            "checkpoint": checkpoint
        }
    
    def record_unloading(
        self,
        shipment_id: str,
        unloaded_items: List[Dict[str, Any]],
        unloader: str,
        received_by: str
    ) -> Dict[str, Any]:
        """
        记录卸货
        
        Args:
            shipment_id: 发运ID
            unloaded_items: 卸货物品
            unloader: 卸货员
            received_by: 接收人
        
        Returns:
            卸货记录
        """
        if shipment_id not in self.shipments:
            return {"success": False, "error": "发运不存在"}
        
        shipment = self.shipments[shipment_id]
        
        if shipment["status"] != ShipmentStatus.ARRIVED.value:
            return {"success": False, "error": "货物尚未到达"}
        
        shipment["status"] = ShipmentStatus.UNLOADING.value
        
        unloading_record = {
            "shipment_id": shipment_id,
            "unloaded_items": unloaded_items,
            "unloader": unloader,
            "received_by": received_by,
            "unloaded_at": datetime.now().isoformat()
        }
        
        shipment["unloading_record"] = unloading_record
        shipment["status"] = ShipmentStatus.COMPLETED.value
        
        # 释放车辆
        vehicle_id = shipment.get("vehicle_id")
        if vehicle_id and vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]["status"] = "available"
            self.vehicles[vehicle_id]["current_shipment"] = None
        
        return {
            "success": True,
            "message": "卸货已完成，发运完成",
            "unloading_record": unloading_record
        }
    
    def add_vehicle(
        self,
        vehicle_id: str,
        vehicle_type: str,
        license_plate: str,
        capacity: Dict[str, Any],
        driver_default: str = ""
    ) -> Dict[str, Any]:
        """
        添加车辆
        
        Args:
            vehicle_id: 车辆ID
            vehicle_type: 车型
            license_plate: 车牌号
            capacity: 容量 {"weight": 0, "volume": 0}
            driver_default: 默认司机
        
        Returns:
            车辆信息
        """
        vehicle = {
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "license_plate": license_plate,
            "capacity": capacity,
            "driver_default": driver_default,
            "status": "available",
            "current_shipment": None,
            "created_at": datetime.now().isoformat()
        }
        
        self.vehicles[vehicle_id] = vehicle
        
        return {
            "success": True,
            "message": "车辆已添加",
            "vehicle": vehicle
        }
    
    def add_route(
        self,
        route_id: str,
        from_location: str,
        to_location: str,
        distance_km: float,
        estimated_duration_hours: float,
        waypoints: List[str] = None
    ) -> Dict[str, Any]:
        """
        添加路线
        
        Args:
            route_id: 路线ID
            from_location: 起点
            to_location: 终点
            distance_km: 距离（公里）
            estimated_duration_hours: 预计时长（小时）
            waypoints: 途经点
        
        Returns:
            路线信息
        """
        route = {
            "route_id": route_id,
            "from_location": from_location,
            "to_location": to_location,
            "distance_km": distance_km,
            "estimated_duration_hours": estimated_duration_hours,
            "waypoints": waypoints or [],
            "created_at": datetime.now().isoformat()
        }
        
        self.routes[route_id] = route
        
        return {
            "success": True,
            "message": "路线已添加",
            "route": route
        }
    
    def get_shipment_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取发运统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计报告
        """
        # 筛选时间范围内的发运
        shipments_in_range = [
            shipment for shipment in self.shipments.values()
            if start_date <= shipment["created_at"][:10] <= end_date
        ]
        
        total_shipments = len(shipments_in_range)
        
        # 按状态统计
        by_status = {}
        for shipment in shipments_in_range:
            status = shipment["status"]
            by_status[status] = by_status.get(status, 0) + 1
        
        # 准时到达率
        on_time_arrivals = 0
        total_arrivals = 0
        
        for shipment in shipments_in_range:
            if shipment.get("actual_arrival"):
                total_arrivals += 1
                
                # 获取计划
                plan = self.shipment_plans.get(shipment["plan_id"], {})
                estimated_arrival = plan.get("estimated_arrival")
                
                if estimated_arrival and shipment["actual_arrival"] <= estimated_arrival:
                    on_time_arrivals += 1
        
        on_time_rate = (on_time_arrivals / total_arrivals * 100) if total_arrivals > 0 else 0
        
        # 按运输方式统计
        by_transport = {}
        for shipment in shipments_in_range:
            plan = self.shipment_plans.get(shipment["plan_id"], {})
            tmode = plan.get("transport_mode", "unknown")
            by_transport[tmode] = by_transport.get(tmode, 0) + 1
        
        # 车辆利用率
        total_vehicles = len(self.vehicles)
        in_use_vehicles = sum(
            1 for v in self.vehicles.values()
            if v["status"] in ["scheduled", "in_transit"]
        )
        
        vehicle_utilization = (in_use_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_shipments": total_shipments,
                "completed": by_status.get(ShipmentStatus.COMPLETED.value, 0),
                "in_transit": by_status.get(ShipmentStatus.IN_TRANSIT.value, 0)
            },
            "by_status": by_status,
            "by_transport_mode": by_transport,
            "performance": {
                "on_time_arrival_rate": round(on_time_rate, 2),
                "total_arrivals": total_arrivals,
                "on_time_arrivals": on_time_arrivals
            },
            "resources": {
                "total_vehicles": total_vehicles,
                "in_use_vehicles": in_use_vehicles,
                "vehicle_utilization": round(vehicle_utilization, 2)
            }
        }
    
    def get_vehicle_status(
        self,
        vehicle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取车辆状态
        
        Args:
            vehicle_id: 车辆ID（可选）
        
        Returns:
            车辆状态
        """
        if vehicle_id:
            if vehicle_id not in self.vehicles:
                return {"success": False, "error": "车辆不存在"}
            
            return {
                "success": True,
                "vehicle": self.vehicles[vehicle_id]
            }
        else:
            # 返回所有车辆状态
            return {
                "success": True,
                "total_vehicles": len(self.vehicles),
                "vehicles": list(self.vehicles.values())
            }


# 创建默认实例
default_shipping_manager = ShippingManager()

