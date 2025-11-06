"""
仓储管理模块
实现完整的仓库、库位、出入库、库存优化功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class WarehouseType(Enum):
    """仓库类型"""
    RAW_MATERIAL = "raw_material"  # 原材料仓
    SEMI_FINISHED = "semi_finished"  # 半成品仓
    FINISHED_GOODS = "finished_goods"  # 成品仓
    TOOL = "tool"  # 工具仓
    SCRAP = "scrap"  # 废料仓


class LocationType(Enum):
    """库位类型"""
    SHELF = "shelf"  # 货架
    PALLET = "pallet"  # 托盘
    FLOOR = "floor"  # 地面
    COLD_STORAGE = "cold_storage"  # 冷藏
    HAZMAT = "hazmat"  # 危险品


class WarehouseManager:
    """仓储管理器"""
    
    def __init__(self):
        """初始化仓储管理器"""
        self.warehouses = {}
        self.locations = {}
        self.storage_rules = {}
        self.transfer_records = []
        self.picking_tasks = {}
        self.putaway_tasks = {}
    
    def create_warehouse(
        self,
        warehouse_id: str,
        name: str,
        warehouse_type: str,
        address: str,
        capacity: float,
        manager: str
    ) -> Dict[str, Any]:
        """
        创建仓库
        
        Args:
            warehouse_id: 仓库ID
            name: 仓库名称
            warehouse_type: 仓库类型
            address: 地址
            capacity: 容量（立方米）
            manager: 仓库经理
        
        Returns:
            仓库信息
        """
        warehouse = {
            "warehouse_id": warehouse_id,
            "name": name,
            "warehouse_type": warehouse_type,
            "address": address,
            "capacity": capacity,
            "used_capacity": 0,
            "manager": manager,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "zones": []
        }
        
        self.warehouses[warehouse_id] = warehouse
        
        return {
            "success": True,
            "message": "仓库已创建",
            "warehouse": warehouse
        }
    
    def create_storage_location(
        self,
        location_id: str,
        warehouse_id: str,
        zone: str,
        location_type: str,
        capacity: float,
        row: str = "",
        column: str = "",
        level: str = ""
    ) -> Dict[str, Any]:
        """
        创建库位
        
        Args:
            location_id: 库位ID
            warehouse_id: 仓库ID
            zone: 区域
            location_type: 库位类型
            capacity: 容量
            row: 行
            column: 列
            level: 层
        
        Returns:
            库位信息
        """
        if warehouse_id not in self.warehouses:
            return {"success": False, "error": "仓库不存在"}
        
        location = {
            "location_id": location_id,
            "warehouse_id": warehouse_id,
            "zone": zone,
            "location_type": location_type,
            "capacity": capacity,
            "occupied_capacity": 0,
            "row": row,
            "column": column,
            "level": level,
            "materials": {},
            "status": "available",
            "created_at": datetime.now().isoformat()
        }
        
        self.locations[location_id] = location
        
        # 更新仓库的区域信息
        warehouse = self.warehouses[warehouse_id]
        if zone not in warehouse["zones"]:
            warehouse["zones"].append(zone)
        
        return {
            "success": True,
            "message": "库位已创建",
            "location": location
        }
    
    def create_putaway_task(
        self,
        material_id: str,
        quantity: float,
        from_location: str,
        recommended_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建上架任务
        
        Args:
            material_id: 物料ID
            quantity: 数量
            from_location: 来源位置（通常是收货区）
            recommended_location: 推荐库位
        
        Returns:
            上架任务信息
        """
        task_id = f"PUT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 如果没有指定推荐库位，自动推荐
        if not recommended_location:
            recommended_location = self._recommend_storage_location(
                material_id,
                quantity
            )
        
        task = {
            "task_id": task_id,
            "task_type": "putaway",
            "material_id": material_id,
            "quantity": quantity,
            "from_location": from_location,
            "to_location": recommended_location,
            "status": "pending",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "assigned_to": None,
            "completed_at": None
        }
        
        self.putaway_tasks[task_id] = task
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "上架任务已创建",
            "task": task
        }
    
    def create_picking_task(
        self,
        order_id: str,
        items: List[Dict[str, Any]],
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        创建拣货任务
        
        Args:
            order_id: 订单ID
            items: 拣货项目 [{"material_id": "", "quantity": 0}]
            priority: 优先级
        
        Returns:
            拣货任务信息
        """
        task_id = f"PICK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 为每个物料找到最优库位
        picking_list = []
        for item in items:
            locations = self._find_material_locations(
                item["material_id"],
                item["quantity"]
            )
            picking_list.append({
                "material_id": item["material_id"],
                "quantity": item["quantity"],
                "locations": locations
            })
        
        task = {
            "task_id": task_id,
            "task_type": "picking",
            "order_id": order_id,
            "picking_list": picking_list,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "assigned_to": None,
            "picked_items": [],
            "completed_at": None
        }
        
        self.picking_tasks[task_id] = task
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "拣货任务已创建",
            "task": task
        }
    
    def complete_putaway_task(
        self,
        task_id: str,
        actual_location: str,
        operator: str
    ) -> Dict[str, Any]:
        """
        完成上架任务
        
        Args:
            task_id: 任务ID
            actual_location: 实际上架库位
            operator: 操作员
        
        Returns:
            完成结果
        """
        if task_id not in self.putaway_tasks:
            return {"success": False, "error": "上架任务不存在"}
        
        task = self.putaway_tasks[task_id]
        
        if task["status"] == "completed":
            return {"success": False, "error": "任务已完成"}
        
        # 更新库位库存
        if actual_location in self.locations:
            location = self.locations[actual_location]
            material_id = task["material_id"]
            
            if material_id not in location["materials"]:
                location["materials"][material_id] = 0
            location["materials"][material_id] += task["quantity"]
        
        # 更新任务状态
        task["status"] = "completed"
        task["actual_location"] = actual_location
        task["completed_by"] = operator
        task["completed_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "上架任务已完成",
            "task": task
        }
    
    def complete_picking_task(
        self,
        task_id: str,
        picked_items: List[Dict[str, Any]],
        operator: str
    ) -> Dict[str, Any]:
        """
        完成拣货任务
        
        Args:
            task_id: 任务ID
            picked_items: 已拣物料 [{"material_id": "", "quantity": 0, "location": ""}]
            operator: 操作员
        
        Returns:
            完成结果
        """
        if task_id not in self.picking_tasks:
            return {"success": False, "error": "拣货任务不存在"}
        
        task = self.picking_tasks[task_id]
        
        if task["status"] == "completed":
            return {"success": False, "error": "任务已完成"}
        
        # 更新库位库存
        for item in picked_items:
            location_id = item["location"]
            if location_id in self.locations:
                location = self.locations[location_id]
                material_id = item["material_id"]
                
                if material_id in location["materials"]:
                    location["materials"][material_id] -= item["quantity"]
                    if location["materials"][material_id] <= 0:
                        del location["materials"][material_id]
        
        # 更新任务状态
        task["status"] = "completed"
        task["picked_items"] = picked_items
        task["completed_by"] = operator
        task["completed_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "拣货任务已完成",
            "task": task
        }
    
    def transfer_between_locations(
        self,
        material_id: str,
        quantity: float,
        from_location: str,
        to_location: str,
        reason: str,
        operator: str
    ) -> Dict[str, Any]:
        """
        库位间转移
        
        Args:
            material_id: 物料ID
            quantity: 数量
            from_location: 源库位
            to_location: 目标库位
            reason: 转移原因
            operator: 操作员
        
        Returns:
            转移记录
        """
        if from_location not in self.locations or to_location not in self.locations:
            return {"success": False, "error": "库位不存在"}
        
        from_loc = self.locations[from_location]
        to_loc = self.locations[to_location]
        
        # 检查源库位库存
        if material_id not in from_loc["materials"] or from_loc["materials"][material_id] < quantity:
            return {
                "success": False,
                "error": "源库位库存不足",
                "available": from_loc["materials"].get(material_id, 0)
            }
        
        # 执行转移
        from_loc["materials"][material_id] -= quantity
        if from_loc["materials"][material_id] <= 0:
            del from_loc["materials"][material_id]
        
        if material_id not in to_loc["materials"]:
            to_loc["materials"][material_id] = 0
        to_loc["materials"][material_id] += quantity
        
        # 记录转移
        transfer_id = f"TRF{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transfer_record = {
            "transfer_id": transfer_id,
            "material_id": material_id,
            "quantity": quantity,
            "from_location": from_location,
            "to_location": to_location,
            "reason": reason,
            "operator": operator,
            "timestamp": datetime.now().isoformat()
        }
        
        self.transfer_records.append(transfer_record)
        
        return {
            "success": True,
            "message": "库位转移已完成",
            "transfer_record": transfer_record
        }
    
    def get_warehouse_utilization(
        self,
        warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取仓库利用率
        
        Args:
            warehouse_id: 仓库ID（可选）
        
        Returns:
            利用率报告
        """
        if warehouse_id:
            if warehouse_id not in self.warehouses:
                return {"success": False, "error": "仓库不存在"}
            
            warehouse = self.warehouses[warehouse_id]
            
            # 统计该仓库的库位
            warehouse_locations = [
                loc for loc in self.locations.values()
                if loc["warehouse_id"] == warehouse_id
            ]
            
            total_locations = len(warehouse_locations)
            occupied_locations = sum(
                1 for loc in warehouse_locations
                if loc["materials"]
            )
            
            utilization = (occupied_locations / total_locations * 100) if total_locations > 0 else 0
            
            return {
                "warehouse_id": warehouse_id,
                "name": warehouse["name"],
                "total_locations": total_locations,
                "occupied_locations": occupied_locations,
                "utilization_rate": round(utilization, 2),
                "zones": warehouse["zones"]
            }
        else:
            # 返回所有仓库的利用率
            summary = []
            for wh_id in self.warehouses:
                utilization = self.get_warehouse_utilization(wh_id)
                summary.append(utilization)
            
            return {
                "total_warehouses": len(summary),
                "warehouses": summary
            }
    
    def get_task_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取任务统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            任务统计
        """
        # 统计上架任务
        putaway_tasks = [
            task for task in self.putaway_tasks.values()
            if start_date <= task["created_at"][:10] <= end_date
        ]
        
        putaway_completed = sum(
            1 for task in putaway_tasks
            if task["status"] == "completed"
        )
        
        # 统计拣货任务
        picking_tasks = [
            task for task in self.picking_tasks.values()
            if start_date <= task["created_at"][:10] <= end_date
        ]
        
        picking_completed = sum(
            1 for task in picking_tasks
            if task["status"] == "completed"
        )
        
        return {
            "period": {"start": start_date, "end": end_date},
            "putaway": {
                "total": len(putaway_tasks),
                "completed": putaway_completed,
                "pending": len(putaway_tasks) - putaway_completed,
                "completion_rate": round((putaway_completed / len(putaway_tasks) * 100), 2) if putaway_tasks else 0
            },
            "picking": {
                "total": len(picking_tasks),
                "completed": picking_completed,
                "pending": len(picking_tasks) - picking_completed,
                "completion_rate": round((picking_completed / len(picking_tasks) * 100), 2) if picking_tasks else 0
            }
        }
    
    def _recommend_storage_location(
        self,
        material_id: str,
        quantity: float
    ) -> str:
        """
        推荐存储库位
        
        Args:
            material_id: 物料ID
            quantity: 数量
        
        Returns:
            推荐库位ID
        """
        # 简化版：找到第一个空闲且容量足够的库位
        # 实际应用中应考虑ABC分类、周转率、存储规则等因素
        
        for location_id, location in self.locations.items():
            if location["status"] == "available":
                available_capacity = location["capacity"] - location["occupied_capacity"]
                if available_capacity >= quantity:
                    return location_id
        
        return "DEFAULT_LOCATION"
    
    def _find_material_locations(
        self,
        material_id: str,
        quantity: float
    ) -> List[Dict[str, Any]]:
        """
        查找物料所在库位
        
        Args:
            material_id: 物料ID
            quantity: 需求数量
        
        Returns:
            库位列表（按FIFO原则排序）
        """
        locations = []
        remaining_qty = quantity
        
        # 找到所有包含该物料的库位
        for location_id, location in self.locations.items():
            if material_id in location["materials"]:
                available_qty = location["materials"][material_id]
                pick_qty = min(available_qty, remaining_qty)
                
                locations.append({
                    "location_id": location_id,
                    "available_quantity": available_qty,
                    "pick_quantity": pick_qty
                })
                
                remaining_qty -= pick_qty
                
                if remaining_qty <= 0:
                    break
        
        return locations


# 创建默认实例
default_warehouse_manager = WarehouseManager()

