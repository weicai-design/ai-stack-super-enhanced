"""
物料管理模块
实现完整的物料库存、分类、追踪功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class MaterialType(Enum):
    """物料类型"""
    RAW_MATERIAL = "raw_material"  # 原材料
    SEMI_FINISHED = "semi_finished"  # 半成品
    FINISHED_GOODS = "finished_goods"  # 成品
    COMPONENT = "component"  # 零部件
    PACKAGING = "packaging"  # 包装材料
    CONSUMABLE = "consumable"  # 耗材
    TOOL = "tool"  # 工具


class StockMovementType(Enum):
    """库存变动类型"""
    IN_PURCHASE = "in_purchase"  # 采购入库
    IN_PRODUCTION = "in_production"  # 生产入库
    IN_RETURN = "in_return"  # 退货入库
    IN_ADJUSTMENT = "in_adjustment"  # 调整入库
    OUT_PRODUCTION = "out_production"  # 生产出库
    OUT_SALE = "out_sale"  # 销售出库
    OUT_SCRAP = "out_scrap"  # 报废出库
    OUT_ADJUSTMENT = "out_adjustment"  # 调整出库
    TRANSFER = "transfer"  # 调拨


class MaterialInventoryManager:
    """物料库存管理器"""
    
    def __init__(self):
        """初始化物料管理器"""
        self.materials = {}
        self.inventory = {}
        self.stock_movements = []
        self.locations = {}
        self.batches = {}
    
    def create_material(
        self,
        material_id: str,
        name: str,
        material_type: str,
        unit: str,
        spec: str = "",
        safety_stock: float = 0,
        reorder_point: float = 0,
        lead_time_days: int = 0,
        shelf_life_days: int = 0
    ) -> Dict[str, Any]:
        """
        创建物料主数据
        
        Args:
            material_id: 物料编号
            name: 物料名称
            material_type: 物料类型
            unit: 单位
            spec: 规格
            safety_stock: 安全库存
            reorder_point: 再订货点
            lead_time_days: 采购提前期（天）
            shelf_life_days: 保质期（天）
        
        Returns:
            物料信息
        """
        material = {
            "material_id": material_id,
            "name": name,
            "material_type": material_type,
            "unit": unit,
            "spec": spec,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "lead_time_days": lead_time_days,
            "shelf_life_days": shelf_life_days,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "cost": 0,
            "avg_cost": 0
        }
        
        self.materials[material_id] = material
        
        # 初始化库存记录
        self.inventory[material_id] = {
            "material_id": material_id,
            "total_quantity": 0,
            "available_quantity": 0,
            "reserved_quantity": 0,
            "in_transit_quantity": 0,
            "locations": {},
            "batches": [],
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "message": "物料已创建",
            "material": material
        }
    
    def record_stock_movement(
        self,
        material_id: str,
        movement_type: str,
        quantity: float,
        location: str,
        reference: str = "",
        batch_number: str = "",
        cost: float = 0
    ) -> Dict[str, Any]:
        """
        记录库存变动
        
        Args:
            material_id: 物料ID
            movement_type: 变动类型
            quantity: 数量（入库为正，出库为负）
            location: 库位
            reference: 参考单号
            batch_number: 批次号
            cost: 成本
        
        Returns:
            变动记录
        """
        if material_id not in self.inventory:
            return {"success": False, "error": "物料不存在"}
        
        movement_id = f"MOV{datetime.now().strftime('%Y%m%d%H%M%S')}{len(self.stock_movements):04d}"
        
        movement = {
            "movement_id": movement_id,
            "material_id": material_id,
            "movement_type": movement_type,
            "quantity": quantity,
            "location": location,
            "reference": reference,
            "batch_number": batch_number,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
            "operator": "system"
        }
        
        self.stock_movements.append(movement)
        
        # 更新库存
        inv = self.inventory[material_id]
        inv["total_quantity"] += quantity
        
        # 更新库位库存
        if location not in inv["locations"]:
            inv["locations"][location] = 0
        inv["locations"][location] += quantity
        
        # 如果是入库，创建或更新批次
        if quantity > 0 and batch_number:
            self._update_batch(material_id, batch_number, quantity, cost, location)
        
        # 更新平均成本
        if quantity > 0 and cost > 0:
            material = self.materials[material_id]
            total_cost = material.get("avg_cost", 0) * (inv["total_quantity"] - quantity) + cost * quantity
            material["avg_cost"] = total_cost / inv["total_quantity"] if inv["total_quantity"] > 0 else 0
        
        inv["last_updated"] = datetime.now().isoformat()
        
        # 检查库存预警
        alerts = self._check_stock_alerts(material_id)
        
        return {
            "success": True,
            "message": "库存变动已记录",
            "movement": movement,
            "current_stock": inv["total_quantity"],
            "alerts": alerts
        }
    
    def reserve_stock(
        self,
        material_id: str,
        quantity: float,
        reference: str
    ) -> Dict[str, Any]:
        """
        预留库存
        
        Args:
            material_id: 物料ID
            quantity: 预留数量
            reference: 参考单号
        
        Returns:
            预留记录
        """
        if material_id not in self.inventory:
            return {"success": False, "error": "物料不存在"}
        
        inv = self.inventory[material_id]
        
        # 检查可用库存
        if inv["available_quantity"] < quantity:
            return {
                "success": False,
                "error": "可用库存不足",
                "available": inv["available_quantity"],
                "requested": quantity
            }
        
        # 预留库存
        inv["reserved_quantity"] += quantity
        inv["available_quantity"] -= quantity
        
        reservation_id = f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if "reservations" not in inv:
            inv["reservations"] = {}
        
        inv["reservations"][reservation_id] = {
            "reservation_id": reservation_id,
            "quantity": quantity,
            "reference": reference,
            "created_at": datetime.now().isoformat(),
            "released": False
        }
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "message": "库存已预留",
            "reserved_quantity": quantity
        }
    
    def release_reservation(
        self,
        material_id: str,
        reservation_id: str
    ) -> Dict[str, Any]:
        """
        释放预留
        
        Args:
            material_id: 物料ID
            reservation_id: 预留ID
        
        Returns:
            释放结果
        """
        if material_id not in self.inventory:
            return {"success": False, "error": "物料不存在"}
        
        inv = self.inventory[material_id]
        
        if "reservations" not in inv or reservation_id not in inv["reservations"]:
            return {"success": False, "error": "预留记录不存在"}
        
        reservation = inv["reservations"][reservation_id]
        
        if reservation["released"]:
            return {"success": False, "error": "预留已释放"}
        
        # 释放库存
        inv["reserved_quantity"] -= reservation["quantity"]
        inv["available_quantity"] += reservation["quantity"]
        reservation["released"] = True
        reservation["released_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "预留已释放",
            "quantity": reservation["quantity"]
        }
    
    def get_inventory_status(
        self,
        material_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取库存状态
        
        Args:
            material_id: 物料ID（可选，不指定则返回所有）
        
        Returns:
            库存状态
        """
        if material_id:
            if material_id not in self.inventory:
                return {"success": False, "error": "物料不存在"}
            
            inv = self.inventory[material_id]
            material = self.materials[material_id]
            
            # 计算库存天数
            # 简化版：假设日均消耗为0.1倍的总库存
            daily_consumption = inv["total_quantity"] * 0.1
            days_of_stock = inv["total_quantity"] / daily_consumption if daily_consumption > 0 else 999
            
            return {
                "material_id": material_id,
                "name": material["name"],
                "total_quantity": inv["total_quantity"],
                "available_quantity": inv["available_quantity"],
                "reserved_quantity": inv["reserved_quantity"],
                "in_transit_quantity": inv["in_transit_quantity"],
                "safety_stock": material["safety_stock"],
                "reorder_point": material["reorder_point"],
                "days_of_stock": round(days_of_stock, 1),
                "locations": inv["locations"],
                "batches": inv.get("batches", []),
                "last_updated": inv["last_updated"]
            }
        else:
            # 返回所有物料的库存汇总
            summary = []
            for mat_id in self.inventory:
                status = self.get_inventory_status(mat_id)
                summary.append(status)
            
            return {
                "total_materials": len(summary),
                "materials": summary
            }
    
    def get_stock_movement_history(
        self,
        material_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        movement_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取库存变动历史
        
        Args:
            material_id: 物料ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            movement_type: 变动类型（可选）
        
        Returns:
            变动历史列表
        """
        movements = self.stock_movements
        
        # 筛选
        if material_id:
            movements = [m for m in movements if m["material_id"] == material_id]
        
        if start_date:
            movements = [m for m in movements if m["timestamp"][:10] >= start_date]
        
        if end_date:
            movements = [m for m in movements if m["timestamp"][:10] <= end_date]
        
        if movement_type:
            movements = [m for m in movements if m["movement_type"] == movement_type]
        
        return movements
    
    def perform_stock_count(
        self,
        material_id: str,
        location: str,
        counted_quantity: float,
        counter: str
    ) -> Dict[str, Any]:
        """
        执行盘点
        
        Args:
            material_id: 物料ID
            location: 库位
            counted_quantity: 盘点数量
            counter: 盘点人
        
        Returns:
            盘点结果
        """
        if material_id not in self.inventory:
            return {"success": False, "error": "物料不存在"}
        
        inv = self.inventory[material_id]
        
        # 获取账面数量
        book_quantity = inv["locations"].get(location, 0)
        
        # 计算差异
        difference = counted_quantity - book_quantity
        
        count_record = {
            "count_id": f"CNT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "material_id": material_id,
            "location": location,
            "book_quantity": book_quantity,
            "counted_quantity": counted_quantity,
            "difference": difference,
            "counter": counter,
            "timestamp": datetime.now().isoformat(),
            "adjusted": False
        }
        
        # 如果有差异，建议调整
        if abs(difference) > 0.01:  # 容差0.01
            count_record["requires_adjustment"] = True
            count_record["adjustment_suggestion"] = {
                "movement_type": StockMovementType.IN_ADJUSTMENT.value if difference > 0 else StockMovementType.OUT_ADJUSTMENT.value,
                "quantity": abs(difference),
                "reference": count_record["count_id"]
            }
        
        return {
            "success": True,
            "message": "盘点已完成",
            "count_record": count_record
        }
    
    def _update_batch(
        self,
        material_id: str,
        batch_number: str,
        quantity: float,
        cost: float,
        location: str
    ):
        """
        更新批次信息
        
        Args:
            material_id: 物料ID
            batch_number: 批次号
            quantity: 数量
            cost: 成本
            location: 库位
        """
        if batch_number not in self.batches:
            material = self.materials[material_id]
            expiry_date = None
            if material["shelf_life_days"] > 0:
                expiry_date = (datetime.now() + timedelta(days=material["shelf_life_days"])).isoformat()[:10]
            
            self.batches[batch_number] = {
                "batch_number": batch_number,
                "material_id": material_id,
                "quantity": quantity,
                "cost": cost,
                "location": location,
                "production_date": datetime.now().isoformat()[:10],
                "expiry_date": expiry_date,
                "created_at": datetime.now().isoformat()
            }
        else:
            batch = self.batches[batch_number]
            batch["quantity"] += quantity
        
        # 更新库存的批次列表
        inv = self.inventory[material_id]
        if batch_number not in [b["batch_number"] for b in inv.get("batches", [])]:
            if "batches" not in inv:
                inv["batches"] = []
            inv["batches"].append(self.batches[batch_number])
    
    def _check_stock_alerts(
        self,
        material_id: str
    ) -> List[Dict[str, Any]]:
        """
        检查库存预警
        
        Args:
            material_id: 物料ID
        
        Returns:
            预警列表
        """
        alerts = []
        
        material = self.materials[material_id]
        inv = self.inventory[material_id]
        
        # 低于安全库存
        if inv["total_quantity"] < material["safety_stock"]:
            alerts.append({
                "type": "below_safety_stock",
                "severity": "high",
                "message": f"库存低于安全库存: 当前{inv['total_quantity']} < 安全库存{material['safety_stock']}"
            })
        
        # 低于再订货点
        if inv["total_quantity"] < material["reorder_point"]:
            alerts.append({
                "type": "below_reorder_point",
                "severity": "medium",
                "message": f"库存低于再订货点: 当前{inv['total_quantity']} < 再订货点{material['reorder_point']}",
                "action": "建议创建采购申请"
            })
        
        # 检查即将过期的批次
        if material["shelf_life_days"] > 0:
            today = datetime.now().date()
            for batch in inv.get("batches", []):
                if batch.get("expiry_date"):
                    expiry = datetime.fromisoformat(batch["expiry_date"]).date()
                    days_to_expiry = (expiry - today).days
                    
                    if days_to_expiry < 30 and days_to_expiry > 0:
                        alerts.append({
                            "type": "expiring_soon",
                            "severity": "medium",
                            "message": f"批次{batch['batch_number']}将在{days_to_expiry}天后过期",
                            "batch_number": batch["batch_number"],
                            "quantity": batch["quantity"]
                        })
                    elif days_to_expiry <= 0:
                        alerts.append({
                            "type": "expired",
                            "severity": "high",
                            "message": f"批次{batch['batch_number']}已过期",
                            "batch_number": batch["batch_number"],
                            "quantity": batch["quantity"],
                            "action": "需要报废处理"
                        })
        
        return alerts


# 创建默认实例
default_inventory_manager = MaterialInventoryManager()

