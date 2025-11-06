"""
设备管理模块
实现完整的设备台账、维护、保养、故障管理功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class EquipmentStatus(Enum):
    """设备状态"""
    IDLE = "idle"  # 空闲
    RUNNING = "running"  # 运行中
    MAINTENANCE = "maintenance"  # 维护中
    BREAKDOWN = "breakdown"  # 故障
    RETIRED = "retired"  # 报废


class MaintenanceType(Enum):
    """维护类型"""
    DAILY = "daily"  # 日常保养
    WEEKLY = "weekly"  # 周保养
    MONTHLY = "monthly"  # 月保养
    QUARTERLY = "quarterly"  # 季度保养
    ANNUAL = "annual"  # 年度保养
    PREVENTIVE = "preventive"  # 预防性维护
    CORRECTIVE = "corrective"  # 纠正性维护


class EquipmentManager:
    """设备管理器"""
    
    def __init__(self):
        """初始化设备管理器"""
        self.equipments = {}
        self.maintenance_records = []
        self.maintenance_plans = {}
        self.breakdown_records = []
        self.spare_parts = {}
        self.oee_records = []
    
    def register_equipment(
        self,
        equipment_id: str,
        name: str,
        equipment_type: str,
        model: str,
        manufacturer: str,
        purchase_date: str,
        location: str,
        specifications: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        注册设备
        
        Args:
            equipment_id: 设备编号
            name: 设备名称
            equipment_type: 设备类型
            model: 型号
            manufacturer: 制造商
            purchase_date: 购买日期
            location: 安装位置
            specifications: 技术规格
        
        Returns:
            设备信息
        """
        equipment = {
            "equipment_id": equipment_id,
            "name": name,
            "equipment_type": equipment_type,
            "model": model,
            "manufacturer": manufacturer,
            "purchase_date": purchase_date,
            "location": location,
            "specifications": specifications or {},
            "status": EquipmentStatus.IDLE.value,
            "total_running_hours": 0,
            "mtbf": 0,  # 平均故障间隔时间
            "mttr": 0,  # 平均修复时间
            "created_at": datetime.now().isoformat(),
            "last_maintenance": None,
            "next_maintenance_due": None
        }
        
        self.equipments[equipment_id] = equipment
        
        return {
            "success": True,
            "message": "设备已注册",
            "equipment": equipment
        }
    
    def create_maintenance_plan(
        self,
        equipment_id: str,
        maintenance_type: str,
        interval_days: int,
        tasks: List[Dict[str, Any]],
        responsible_person: str = ""
    ) -> Dict[str, Any]:
        """
        创建维护计划
        
        Args:
            equipment_id: 设备ID
            maintenance_type: 维护类型
            interval_days: 维护间隔（天）
            tasks: 维护任务列表 [{"task": "", "standard": "", "duration_minutes": 0}]
            responsible_person: 责任人
        
        Returns:
            维护计划信息
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        plan_id = f"MP{equipment_id}{len(self.maintenance_plans) + 1:04d}"
        
        plan = {
            "plan_id": plan_id,
            "equipment_id": equipment_id,
            "maintenance_type": maintenance_type,
            "interval_days": interval_days,
            "tasks": tasks,
            "responsible_person": responsible_person,
            "active": True,
            "created_at": datetime.now().isoformat(),
            "last_execution": None,
            "next_due_date": None
        }
        
        # 计算首次到期日
        plan["next_due_date"] = (datetime.now() + timedelta(days=interval_days)).isoformat()[:10]
        
        self.maintenance_plans[plan_id] = plan
        
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "维护计划已创建",
            "plan": plan
        }
    
    def execute_maintenance(
        self,
        equipment_id: str,
        maintenance_type: str,
        executor: str,
        completed_tasks: List[Dict[str, Any]],
        duration_minutes: int,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        执行维护
        
        Args:
            equipment_id: 设备ID
            maintenance_type: 维护类型
            executor: 执行人
            completed_tasks: 完成的任务 [{"task": "", "result": "pass/fail", "note": ""}]
            duration_minutes: 耗时（分钟）
            notes: 备注
        
        Returns:
            维护记录
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        
        record_id = f"MR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        record = {
            "record_id": record_id,
            "equipment_id": equipment_id,
            "maintenance_type": maintenance_type,
            "executor": executor,
            "completed_tasks": completed_tasks,
            "duration_minutes": duration_minutes,
            "notes": notes,
            "executed_at": datetime.now().isoformat(),
            "result": "completed"
        }
        
        self.maintenance_records.append(record)
        
        # 更新设备维护信息
        equipment["last_maintenance"] = datetime.now().isoformat()
        equipment["status"] = EquipmentStatus.IDLE.value
        
        # 更新相关维护计划
        for plan in self.maintenance_plans.values():
            if (plan["equipment_id"] == equipment_id and 
                plan["maintenance_type"] == maintenance_type):
                plan["last_execution"] = datetime.now().isoformat()
                plan["next_due_date"] = (datetime.now() + timedelta(days=plan["interval_days"])).isoformat()[:10]
        
        return {
            "success": True,
            "record_id": record_id,
            "message": "维护已完成",
            "record": record
        }
    
    def report_breakdown(
        self,
        equipment_id: str,
        fault_description: str,
        reporter: str,
        severity: str = "medium",
        impact: str = ""
    ) -> Dict[str, Any]:
        """
        报告故障
        
        Args:
            equipment_id: 设备ID
            fault_description: 故障描述
            reporter: 报告人
            severity: 严重程度 (low/medium/high/critical)
            impact: 影响描述
        
        Returns:
            故障记录
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        
        breakdown_id = f"BD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        breakdown = {
            "breakdown_id": breakdown_id,
            "equipment_id": equipment_id,
            "fault_description": fault_description,
            "reporter": reporter,
            "severity": severity,
            "impact": impact,
            "reported_at": datetime.now().isoformat(),
            "status": "reported",
            "assigned_to": None,
            "repair_started": None,
            "repair_completed": None,
            "downtime_minutes": 0,
            "root_cause": None,
            "solution": None
        }
        
        self.breakdown_records.append(breakdown)
        
        # 更新设备状态
        equipment["status"] = EquipmentStatus.BREAKDOWN.value
        
        return {
            "success": True,
            "breakdown_id": breakdown_id,
            "message": "故障已报告",
            "breakdown": breakdown
        }
    
    def repair_breakdown(
        self,
        breakdown_id: str,
        repairer: str,
        root_cause: str,
        solution: str,
        spare_parts_used: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        修复故障
        
        Args:
            breakdown_id: 故障ID
            repairer: 维修人
            root_cause: 根本原因
            solution: 解决方案
            spare_parts_used: 使用的备件 [{"part_id": "", "quantity": 0}]
        
        Returns:
            修复结果
        """
        breakdown = next((b for b in self.breakdown_records if b["breakdown_id"] == breakdown_id), None)
        
        if not breakdown:
            return {"success": False, "error": "故障记录不存在"}
        
        # 更新故障记录
        breakdown["status"] = "repaired"
        breakdown["assigned_to"] = repairer
        breakdown["root_cause"] = root_cause
        breakdown["solution"] = solution
        breakdown["spare_parts_used"] = spare_parts_used or []
        breakdown["repair_completed"] = datetime.now().isoformat()
        
        # 计算停机时间
        if breakdown.get("repair_started"):
            started = datetime.fromisoformat(breakdown["repair_started"])
        else:
            started = datetime.fromisoformat(breakdown["reported_at"])
        
        completed = datetime.now()
        breakdown["downtime_minutes"] = int((completed - started).total_seconds() / 60)
        
        # 更新设备状态
        equipment = self.equipments[breakdown["equipment_id"]]
        equipment["status"] = EquipmentStatus.IDLE.value
        
        # 更新MTTR（平均修复时间）
        repaired_breakdowns = [b for b in self.breakdown_records 
                               if b["equipment_id"] == breakdown["equipment_id"] 
                               and b["status"] == "repaired"]
        
        total_downtime = sum(b["downtime_minutes"] for b in repaired_breakdowns)
        equipment["mttr"] = total_downtime / len(repaired_breakdowns) if repaired_breakdowns else 0
        
        return {
            "success": True,
            "message": "故障已修复",
            "breakdown": breakdown,
            "downtime_minutes": breakdown["downtime_minutes"]
        }
    
    def record_oee(
        self,
        equipment_id: str,
        date: str,
        planned_production_time: int,
        actual_production_time: int,
        ideal_cycle_time: float,
        total_pieces: int,
        good_pieces: int
    ) -> Dict[str, Any]:
        """
        记录设备综合效率(OEE)
        
        Args:
            equipment_id: 设备ID
            date: 日期
            planned_production_time: 计划生产时间（分钟）
            actual_production_time: 实际生产时间（分钟）
            ideal_cycle_time: 理想节拍时间（分钟/件）
            total_pieces: 总产量
            good_pieces: 良品数量
        
        Returns:
            OEE记录
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        # 计算OEE三要素
        # 可用率 = 实际生产时间 / 计划生产时间
        availability = (actual_production_time / planned_production_time * 100) if planned_production_time > 0 else 0
        
        # 表现性 = (理想节拍时间 × 总产量) / 实际生产时间
        performance = (ideal_cycle_time * total_pieces / actual_production_time * 100) if actual_production_time > 0 else 0
        
        # 质量率 = 良品数量 / 总产量
        quality = (good_pieces / total_pieces * 100) if total_pieces > 0 else 0
        
        # OEE = 可用率 × 表现性 × 质量率
        oee = availability * performance * quality / 10000
        
        oee_record = {
            "equipment_id": equipment_id,
            "date": date,
            "planned_production_time": planned_production_time,
            "actual_production_time": actual_production_time,
            "ideal_cycle_time": ideal_cycle_time,
            "total_pieces": total_pieces,
            "good_pieces": good_pieces,
            "availability": round(availability, 2),
            "performance": round(performance, 2),
            "quality": round(quality, 2),
            "oee": round(oee, 2),
            "recorded_at": datetime.now().isoformat()
        }
        
        self.oee_records.append(oee_record)
        
        return {
            "success": True,
            "message": "OEE已记录",
            "oee_record": oee_record
        }
    
    def get_maintenance_due_list(
        self,
        days_ahead: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取到期维护列表
        
        Args:
            days_ahead: 提前天数
        
        Returns:
            到期维护列表
        """
        due_date = (datetime.now() + timedelta(days=days_ahead)).date()
        due_plans = []
        
        for plan in self.maintenance_plans.values():
            if not plan["active"]:
                continue
            
            if plan.get("next_due_date"):
                next_due = datetime.fromisoformat(plan["next_due_date"]).date()
                if next_due <= due_date:
                    equipment = self.equipments.get(plan["equipment_id"], {})
                    due_plans.append({
                        "plan": plan,
                        "equipment": equipment,
                        "days_until_due": (next_due - datetime.now().date()).days
                    })
        
        # 按到期日排序
        due_plans.sort(key=lambda x: x["days_until_due"])
        
        return due_plans
    
    def get_equipment_performance(
        self,
        equipment_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取设备绩效
        
        Args:
            equipment_id: 设备ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            绩效报告
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        
        # 筛选时间范围内的OEE记录
        oee_records = [
            r for r in self.oee_records
            if r["equipment_id"] == equipment_id
            and start_date <= r["date"] <= end_date
        ]
        
        # 计算平均OEE
        avg_oee = sum(r["oee"] for r in oee_records) / len(oee_records) if oee_records else 0
        avg_availability = sum(r["availability"] for r in oee_records) / len(oee_records) if oee_records else 0
        avg_performance = sum(r["performance"] for r in oee_records) / len(oee_records) if oee_records else 0
        avg_quality = sum(r["quality"] for r in oee_records) / len(oee_records) if oee_records else 0
        
        # 故障统计
        breakdowns = [
            b for b in self.breakdown_records
            if b["equipment_id"] == equipment_id
            and start_date <= b["reported_at"][:10] <= end_date
        ]
        
        total_breakdowns = len(breakdowns)
        total_downtime = sum(b.get("downtime_minutes", 0) for b in breakdowns if b["status"] == "repaired")
        
        # 维护统计
        maintenances = [
            m for m in self.maintenance_records
            if m["equipment_id"] == equipment_id
            and start_date <= m["executed_at"][:10] <= end_date
        ]
        
        return {
            "success": True,
            "equipment_id": equipment_id,
            "equipment_name": equipment["name"],
            "period": {"start": start_date, "end": end_date},
            "oee_metrics": {
                "average_oee": round(avg_oee, 2),
                "average_availability": round(avg_availability, 2),
                "average_performance": round(avg_performance, 2),
                "average_quality": round(avg_quality, 2),
                "days_with_data": len(oee_records)
            },
            "breakdown_metrics": {
                "total_breakdowns": total_breakdowns,
                "total_downtime_minutes": total_downtime,
                "mttr": equipment["mttr"],
                "mtbf": equipment["mtbf"]
            },
            "maintenance_metrics": {
                "total_maintenances": len(maintenances),
                "total_maintenance_time": sum(m["duration_minutes"] for m in maintenances)
            }
        }
    
    def get_spare_parts_inventory(self) -> Dict[str, Any]:
        """
        获取备件库存
        
        Returns:
            备件库存信息
        """
        return {
            "success": True,
            "spare_parts": self.spare_parts,
            "total_parts": len(self.spare_parts)
        }
    
    def add_spare_part(
        self,
        part_id: str,
        name: str,
        compatible_equipments: List[str],
        quantity: int,
        unit: str,
        min_stock: int = 0
    ) -> Dict[str, Any]:
        """
        添加备件
        
        Args:
            part_id: 备件ID
            name: 备件名称
            compatible_equipments: 适用设备列表
            quantity: 数量
            unit: 单位
            min_stock: 最小库存
        
        Returns:
            备件信息
        """
        spare_part = {
            "part_id": part_id,
            "name": name,
            "compatible_equipments": compatible_equipments,
            "quantity": quantity,
            "unit": unit,
            "min_stock": min_stock,
            "created_at": datetime.now().isoformat()
        }
        
        self.spare_parts[part_id] = spare_part
        
        return {
            "success": True,
            "message": "备件已添加",
            "spare_part": spare_part
        }


# 创建默认实例
default_equipment_manager = EquipmentManager()

