#!/usr/bin/env python3
"""
物料管理系统
Material Management System

功能：
- 物料主数据管理
- 库存管理
- 物料需求计划(MRP)
- 安全库存管理
- 物料追溯
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class MaterialType(Enum):
    """物料类型"""
    RAW_MATERIAL = "raw_material"  # 原材料
    SEMI_FINISHED = "semi_finished"  # 半成品
    FINISHED_GOOD = "finished_good"  # 成品
    CONSUMABLE = "consumable"  # 耗材
    SPARE_PART = "spare_part"  # 备件


class MaterialStatus(Enum):
    """物料状态"""
    ACTIVE = "active"  # 激活
    INACTIVE = "inactive"  # 停用
    OBSOLETE = "obsolete"  # 废弃


class MaterialManager:
    """物料管理器"""
    
    def __init__(self):
        """初始化物料管理器"""
        self.materials: Dict[str, Dict[str, Any]] = {}
        self.inventory: Dict[str, Dict[str, Any]] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.mrp_records: List[Dict[str, Any]] = []
        
    # ==================== 物料主数据管理 ====================
    
    def create_material(
        self,
        material_id: str,
        name: str,
        specification: str,
        material_type: str,
        unit: str,
        unit_price: float = 0.0,
        lead_time_days: int = 7,
        min_order_qty: float = 1.0,
        safety_stock: float = 0.0,
        reorder_point: float = 0.0,
        supplier_ids: List[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建物料主数据
        
        Args:
            material_id: 物料编号
            name: 物料名称
            specification: 规格型号
            material_type: 物料类型
            unit: 计量单位
            unit_price: 单价
            lead_time_days: 采购/生产提前期（天）
            min_order_qty: 最小订购量
            safety_stock: 安全库存
            reorder_point: 再订购点
            supplier_ids: 供应商列表
            notes: 备注
        
        Returns:
            物料信息
        """
        material = {
            "material_id": material_id,
            "name": name,
            "specification": specification,
            "material_type": material_type,
            "unit": unit,
            "unit_price": unit_price,
            "lead_time_days": lead_time_days,
            "min_order_qty": min_order_qty,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "supplier_ids": supplier_ids or [],
            "notes": notes,
            "status": MaterialStatus.ACTIVE.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.materials[material_id] = material
        
        # 初始化库存记录
        if material_id not in self.inventory:
            self.inventory[material_id] = {
                "material_id": material_id,
                "on_hand": 0.0,  # 现有库存
                "allocated": 0.0,  # 已分配
                "available": 0.0,  # 可用库存
                "on_order": 0.0,  # 在途库存
                "reserved": 0.0,  # 预留库存
                "last_updated": datetime.now().isoformat()
            }
        
        return material
    
    def update_material(
        self,
        material_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        更新物料信息
        
        Args:
            material_id: 物料编号
            **kwargs: 要更新的字段
        
        Returns:
            更新后的物料信息
        """
        if material_id not in self.materials:
            raise ValueError(f"物料 {material_id} 不存在")
        
        material = self.materials[material_id]
        
        for key, value in kwargs.items():
            if key in material and key not in ["material_id", "created_at"]:
                material[key] = value
        
        material["updated_at"] = datetime.now().isoformat()
        
        return material
    
    def get_material(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物料信息
        
        Args:
            material_id: 物料编号
        
        Returns:
            物料信息
        """
        return self.materials.get(material_id)
    
    def list_materials(
        self,
        material_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取物料列表
        
        Args:
            material_type: 物料类型筛选
            status: 状态筛选
            search: 搜索关键词（名称/编号）
        
        Returns:
            物料列表
        """
        materials = list(self.materials.values())
        
        if material_type:
            materials = [m for m in materials if m["material_type"] == material_type]
        
        if status:
            materials = [m for m in materials if m["status"] == status]
        
        if search:
            search_lower = search.lower()
            materials = [
                m for m in materials
                if search_lower in m["material_id"].lower()
                or search_lower in m["name"].lower()
            ]
        
        return materials
    
    # ==================== 库存管理 ====================
    
    def record_transaction(
        self,
        material_id: str,
        transaction_type: str,
        quantity: float,
        reference_id: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        记录库存事务
        
        Args:
            material_id: 物料编号
            transaction_type: 事务类型（inbound/outbound/adjustment/transfer）
            quantity: 数量（正数为入库，负数为出库）
            reference_id: 关联单据号
            notes: 备注
        
        Returns:
            事务记录
        """
        if material_id not in self.materials:
            raise ValueError(f"物料 {material_id} 不存在")
        
        transaction = {
            "transaction_id": f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "material_id": material_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "reference_id": reference_id,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "created_by": "system"
        }
        
        self.transactions.append(transaction)
        
        # 更新库存
        self._update_inventory(material_id, quantity, transaction_type)
        
        return transaction
    
    def _update_inventory(
        self,
        material_id: str,
        quantity: float,
        transaction_type: str
    ):
        """
        更新库存数量
        
        Args:
            material_id: 物料编号
            quantity: 数量变化
            transaction_type: 事务类型
        """
        if material_id not in self.inventory:
            self.inventory[material_id] = {
                "material_id": material_id,
                "on_hand": 0.0,
                "allocated": 0.0,
                "available": 0.0,
                "on_order": 0.0,
                "reserved": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        
        inv = self.inventory[material_id]
        
        if transaction_type in ["inbound", "receive"]:
            inv["on_hand"] += quantity
            inv["on_order"] = max(0, inv["on_order"] - quantity)
        elif transaction_type in ["outbound", "issue"]:
            inv["on_hand"] -= quantity
            inv["allocated"] = max(0, inv["allocated"] - quantity)
        elif transaction_type == "adjustment":
            inv["on_hand"] += quantity
        elif transaction_type == "allocate":
            inv["allocated"] += quantity
        elif transaction_type == "order":
            inv["on_order"] += quantity
        
        # 更新可用库存
        inv["available"] = inv["on_hand"] - inv["allocated"] - inv["reserved"]
        inv["last_updated"] = datetime.now().isoformat()
    
    def get_inventory_status(
        self,
        material_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取库存状态
        
        Args:
            material_id: 物料编号（可选，不提供则返回全部）
        
        Returns:
            库存状态
        """
        if material_id:
            if material_id not in self.inventory:
                raise ValueError(f"物料 {material_id} 库存记录不存在")
            
            inv = self.inventory[material_id].copy()
            material = self.materials.get(material_id, {})
            
            # 添加物料基本信息
            inv["material_name"] = material.get("name", "")
            inv["unit"] = material.get("unit", "")
            inv["safety_stock"] = material.get("safety_stock", 0)
            inv["reorder_point"] = material.get("reorder_point", 0)
            
            # 判断是否需要补货
            inv["need_reorder"] = inv["available"] <= material.get("reorder_point", 0)
            
            return inv
        else:
            # 返回所有库存
            result = []
            for mat_id in self.inventory:
                result.append(self.get_inventory_status(mat_id))
            return {"inventory_list": result}
    
    def check_low_stock(self) -> List[Dict[str, Any]]:
        """
        检查低库存物料
        
        Returns:
            低库存物料列表
        """
        low_stock_items = []
        
        for material_id, inv in self.inventory.items():
            material = self.materials.get(material_id, {})
            reorder_point = material.get("reorder_point", 0)
            
            if inv["available"] <= reorder_point:
                low_stock_items.append({
                    "material_id": material_id,
                    "material_name": material.get("name", ""),
                    "available": inv["available"],
                    "reorder_point": reorder_point,
                    "shortage": reorder_point - inv["available"],
                    "unit": material.get("unit", ""),
                    "lead_time_days": material.get("lead_time_days", 0)
                })
        
        # 按短缺数量排序
        low_stock_items.sort(key=lambda x: x["shortage"], reverse=True)
        
        return low_stock_items
    
    # ==================== 物料需求计划(MRP) ====================
    
    def calculate_mrp(
        self,
        material_id: str,
        demand_quantity: float,
        demand_date: str,
        order_id: str = ""
    ) -> Dict[str, Any]:
        """
        计算物料需求计划
        
        Args:
            material_id: 物料编号
            demand_quantity: 需求数量
            demand_date: 需求日期
            order_id: 关联订单号
        
        Returns:
            MRP计划
        """
        if material_id not in self.materials:
            raise ValueError(f"物料 {material_id} 不存在")
        
        material = self.materials[material_id]
        inv = self.inventory.get(material_id, {})
        
        # 计算净需求
        available_qty = inv.get("available", 0)
        on_order_qty = inv.get("on_order", 0)
        
        net_requirement = max(0, demand_quantity - available_qty - on_order_qty)
        
        # 计算订购数量（考虑最小订购量）
        min_order_qty = material.get("min_order_qty", 1)
        if net_requirement > 0:
            order_quantity = max(net_requirement, min_order_qty)
            # 向上取整到最小订购量的倍数
            if order_quantity % min_order_qty != 0:
                order_quantity = ((order_quantity // min_order_qty) + 1) * min_order_qty
        else:
            order_quantity = 0
        
        # 计算订购日期（需求日期 - 提前期）
        lead_time = material.get("lead_time_days", 7)
        demand_dt = datetime.fromisoformat(demand_date)
        order_date = (demand_dt - timedelta(days=lead_time)).date().isoformat()
        
        mrp_record = {
            "mrp_id": f"MRP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "material_id": material_id,
            "material_name": material["name"],
            "demand_quantity": demand_quantity,
            "demand_date": demand_date,
            "available_quantity": available_qty,
            "on_order_quantity": on_order_qty,
            "net_requirement": net_requirement,
            "order_quantity": order_quantity,
            "order_date": order_date,
            "lead_time_days": lead_time,
            "order_id": order_id,
            "created_at": datetime.now().isoformat()
        }
        
        self.mrp_records.append(mrp_record)
        
        return mrp_record
    
    def get_mrp_plan(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        material_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取MRP计划
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            material_id: 物料编号
        
        Returns:
            MRP计划列表
        """
        records = self.mrp_records.copy()
        
        if material_id:
            records = [r for r in records if r["material_id"] == material_id]
        
        if start_date:
            records = [r for r in records if r["demand_date"] >= start_date]
        
        if end_date:
            records = [r for r in records if r["demand_date"] <= end_date]
        
        # 按订购日期排序
        records.sort(key=lambda x: x["order_date"])
        
        return records
    
    # ==================== 分析报表 ====================
    
    def analyze_inventory_turnover(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        库存周转率分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            周转率分析
        """
        # 筛选期间内的事务
        period_transactions = [
            t for t in self.transactions
            if start_date <= t["timestamp"][:10] <= end_date
        ]
        
        # 按物料统计
        material_stats = {}
        
        for trans in period_transactions:
            mat_id = trans["material_id"]
            
            if mat_id not in material_stats:
                material = self.materials.get(mat_id, {})
                material_stats[mat_id] = {
                    "material_id": mat_id,
                    "material_name": material.get("name", ""),
                    "outbound_qty": 0,
                    "inbound_qty": 0,
                    "avg_inventory": 0,
                    "turnover_rate": 0
                }
            
            qty = trans["quantity"]
            if trans["transaction_type"] in ["outbound", "issue"]:
                material_stats[mat_id]["outbound_qty"] += abs(qty)
            elif trans["transaction_type"] in ["inbound", "receive"]:
                material_stats[mat_id]["inbound_qty"] += qty
        
        # 计算周转率
        for mat_id, stats in material_stats.items():
            inv = self.inventory.get(mat_id, {})
            avg_inv = inv.get("on_hand", 0)
            
            if avg_inv > 0:
                stats["avg_inventory"] = avg_inv
                stats["turnover_rate"] = stats["outbound_qty"] / avg_inv
            else:
                stats["turnover_rate"] = 0
        
        # 按周转率排序
        sorted_stats = sorted(
            material_stats.values(),
            key=lambda x: x["turnover_rate"],
            reverse=True
        )
        
        return {
            "period": {"start": start_date, "end": end_date},
            "total_materials": len(material_stats),
            "materials": sorted_stats,
            "fast_movers": [s for s in sorted_stats if s["turnover_rate"] > 5],
            "slow_movers": [s for s in sorted_stats if 0 < s["turnover_rate"] < 1],
            "no_movement": [s for s in sorted_stats if s["turnover_rate"] == 0]
        }
    
    def get_material_transactions(
        self,
        material_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取物料事务历史
        
        Args:
            material_id: 物料编号
            limit: 返回记录数
        
        Returns:
            事务记录列表
        """
        transactions = [
            t for t in self.transactions
            if t["material_id"] == material_id
        ]
        
        # 按时间倒序
        transactions.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return transactions[:limit]


# 创建全局实例
default_material_manager = MaterialManager()

