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
    AVAILABLE = "available"  # 可用
    IN_USE = "in_use"  # 使用中
    MAINTENANCE = "maintenance"  # 维护中
    REPAIR = "repair"  # 维修中
    STANDBY = "standby"  # 待机
    SCRAPPED = "scrapped"  # 报废


class MaintenanceType(Enum):
    """维护类型"""
    DAILY = "daily"  # 日常保养
    WEEKLY = "weekly"  # 周保养
    MONTHLY = "monthly"  # 月保养
    QUARTERLY = "quarterly"  # 季度保养
    ANNUAL = "annual"  # 年度保养
    OVERHAUL = "overhaul"  # 大修


class EquipmentManager:
    """设备管理器"""
    
    def __init__(self):
        """初始化设备管理器"""
        self.equipments = {}
        self.maintenance_plans = {}
        self.maintenance_records = []
        self.repair_records = []
        self.spare_parts = {}
        self.equipment_counter = 1000
    
    def register_equipment(
        self,
        equipment_id: str,
        name: str,
        category: str,
        model: str,
        manufacturer: str,
        purchase_date: str,
        location: str,
        specifications: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        登记设备
        
        Args:
            equipment_id: 设备编号
            name: 设备名称
            category: 设备类别
            model: 型号
            manufacturer: 制造商
            purchase_date: 购置日期
            location: 安装位置
            specifications: 技术规格
        
        Returns:
            设备信息
        """
        equipment = {
            "equipment_id": equipment_id,
            "name": name,
            "category": category,
            "model": model,
            "manufacturer": manufacturer,
            "purchase_date": purchase_date,
            "location": location,
            "specifications": specifications or {},
            "status": EquipmentStatus.AVAILABLE.value,
            "usage_hours": 0,
            "maintenance_count": 0,
            "repair_count": 0,
            "last_maintenance_date": None,
            "next_maintenance_date": None,
            "registered_at": datetime.now().isoformat(),
            "active": True
        }
        
        self.equipments[equipment_id] = equipment
        
        return {
            "success": True,
            "message": "设备已登记",
            "equipment": equipment
        }
    
    def create_maintenance_plan(
        self,
        equipment_id: str,
        maintenance_type: str,
        interval_days: int,
        maintenance_items: List[Dict[str, Any]],
        responsible_person: str = ""
    ) -> Dict[str, Any]:
        """
        创建维护计划
        
        Args:
            equipment_id: 设备ID
            maintenance_type: 维护类型
            interval_days: 间隔天数
            maintenance_items: 维护项目 [{"item": "", "standard": "", "method": ""}]
            responsible_person: 责任人
        
        Returns:
            维护计划信息
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        plan_id = f"MP{datetime.now().strftime('%Y%m%d')}{len(self.maintenance_plans) + 1:04d}"
        
        # 计算下次维护日期
        next_date = (datetime.now() + timedelta(days=interval_days)).strftime('%Y-%m-%d')
        
        plan = {
            "plan_id": plan_id,
            "equipment_id": equipment_id,
            "maintenance_type": maintenance_type,
            "interval_days": interval_days,
            "maintenance_items": maintenance_items,
            "responsible_person": responsible_person,
            "next_maintenance_date": next_date,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        self.maintenance_plans[plan_id] = plan
        
        # 更新设备的下次维护日期
        equipment = self.equipments[equipment_id]
        if not equipment["next_maintenance_date"] or next_date < equipment["next_maintenance_date"]:
            equipment["next_maintenance_date"] = next_date
        
        return {
            "success": True,
            "plan_id": plan_id,
            "message": "维护计划已创建",
            "plan": plan
        }
    
    def record_maintenance(
        self,
        equipment_id: str,
        maintenance_type: str,
        maintenance_items: List[Dict[str, Any]],
        maintainer: str,
        duration_hours: float,
        parts_used: List[Dict[str, Any]] = None,
        findings: str = ""
    ) -> Dict[str, Any]:
        """
        记录维护保养
        
        Args:
            equipment_id: 设备ID
            maintenance_type: 维护类型
            maintenance_items: 维护项目 [{"item": "", "result": "pass/fail", "note": ""}]
            maintainer: 维护人员
            duration_hours: 耗时（小时）
            parts_used: 使用的备件
            findings: 发现的问题
        
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
            "maintenance_items": maintenance_items,
            "maintainer": maintainer,
            "duration_hours": duration_hours,
            "parts_used": parts_used or [],
            "findings": findings,
            "maintenance_date": datetime.now().strftime('%Y-%m-%d'),
            "created_at": datetime.now().isoformat()
        }
        
        self.maintenance_records.append(record)
        
        # 更新设备信息
        equipment["last_maintenance_date"] = record["maintenance_date"]
        equipment["maintenance_count"] += 1
        
        # 更新下次维护日期（如果有对应的计划）
        for plan in self.maintenance_plans.values():
            if plan["equipment_id"] == equipment_id and plan["maintenance_type"] == maintenance_type:
                next_date = (datetime.now() + timedelta(days=plan["interval_days"])).strftime('%Y-%m-%d')
                plan["next_maintenance_date"] = next_date
                equipment["next_maintenance_date"] = next_date
                break
        
        return {
            "success": True,
            "record_id": record_id,
            "message": "维护记录已创建",
            "record": record
        }
    
    def report_failure(
        self,
        equipment_id: str,
        failure_description: str,
        severity: str,
        reported_by: str,
        impact: str = ""
    ) -> Dict[str, Any]:
        """
        报告故障
        
        Args:
            equipment_id: 设备ID
            failure_description: 故障描述
            severity: 严重程度 (low/medium/high/critical)
            reported_by: 报告人
            impact: 影响
        
        Returns:
            故障记录
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        
        repair_id = f"RP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        repair_record = {
            "repair_id": repair_id,
            "equipment_id": equipment_id,
            "failure_description": failure_description,
            "severity": severity,
            "reported_by": reported_by,
            "impact": impact,
            "status": "reported",
            "reported_at": datetime.now().isoformat(),
            "repair_started_at": None,
            "repair_completed_at": None,
            "root_cause": None,
            "repair_actions": [],
            "parts_replaced": [],
            "cost": 0
        }
        
        self.repair_records.append(repair_record)
        
        # 更新设备状态
        if severity in ["high", "critical"]:
            equipment["status"] = EquipmentStatus.REPAIR.value
        
        return {
            "success": True,
            "repair_id": repair_id,
            "message": "故障已记录",
            "repair_record": repair_record
        }
    
    def start_repair(
        self,
        repair_id: str,
        technician: str,
        estimated_duration_hours: float
    ) -> Dict[str, Any]:
        """
        开始维修
        
        Args:
            repair_id: 维修ID
            technician: 维修人员
            estimated_duration_hours: 预计耗时
        
        Returns:
            更新结果
        """
        repair_record = next((r for r in self.repair_records if r["repair_id"] == repair_id), None)
        
        if not repair_record:
            return {"success": False, "error": "维修记录不存在"}
        
        repair_record["status"] = "in_repair"
        repair_record["technician"] = technician
        repair_record["estimated_duration_hours"] = estimated_duration_hours
        repair_record["repair_started_at"] = datetime.now().isoformat()
        
        # 更新设备状态
        equipment_id = repair_record["equipment_id"]
        if equipment_id in self.equipments:
            self.equipments[equipment_id]["status"] = EquipmentStatus.REPAIR.value
        
        return {
            "success": True,
            "message": "维修已开始",
            "repair_record": repair_record
        }
    
    def complete_repair(
        self,
        repair_id: str,
        root_cause: str,
        repair_actions: List[str],
        parts_replaced: List[Dict[str, Any]],
        cost: float,
        test_result: str
    ) -> Dict[str, Any]:
        """
        完成维修
        
        Args:
            repair_id: 维修ID
            root_cause: 根本原因
            repair_actions: 维修措施
            parts_replaced: 更换的零件
            cost: 费用
            test_result: 测试结果
        
        Returns:
            完成结果
        """
        repair_record = next((r for r in self.repair_records if r["repair_id"] == repair_id), None)
        
        if not repair_record:
            return {"success": False, "error": "维修记录不存在"}
        
        repair_record["status"] = "completed"
        repair_record["root_cause"] = root_cause
        repair_record["repair_actions"] = repair_actions
        repair_record["parts_replaced"] = parts_replaced
        repair_record["cost"] = cost
        repair_record["test_result"] = test_result
        repair_record["repair_completed_at"] = datetime.now().isoformat()
        
        # 计算维修耗时
        if repair_record["repair_started_at"]:
            start_time = datetime.fromisoformat(repair_record["repair_started_at"])
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 3600
            repair_record["actual_duration_hours"] = round(duration, 2)
        
        # 更新设备状态和统计
        equipment_id = repair_record["equipment_id"]
        if equipment_id in self.equipments:
            equipment = self.equipments[equipment_id]
            equipment["status"] = EquipmentStatus.AVAILABLE.value
            equipment["repair_count"] += 1
        
        return {
            "success": True,
            "message": "维修已完成",
            "repair_record": repair_record
        }
    
    def update_equipment_usage(
        self,
        equipment_id: str,
        hours: float
    ) -> Dict[str, Any]:
        """
        更新设备使用时长
        
        Args:
            equipment_id: 设备ID
            hours: 使用小时数
        
        Returns:
            更新结果
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        equipment["usage_hours"] += hours
        
        return {
            "success": True,
            "message": "使用时长已更新",
            "total_hours": equipment["usage_hours"]
        }
    
    def get_equipment_health(
        self,
        equipment_id: str
    ) -> Dict[str, Any]:
        """
        获取设备健康度
        
        Args:
            equipment_id: 设备ID
        
        Returns:
            健康度报告
        """
        if equipment_id not in self.equipments:
            return {"success": False, "error": "设备不存在"}
        
        equipment = self.equipments[equipment_id]
        
        # 计算健康度指标
        
        # 1. 故障率
        total_time = equipment["usage_hours"]
        failure_count = equipment["repair_count"]
        mtbf = total_time / failure_count if failure_count > 0 else float('inf')  # 平均故障间隔时间
        
        # 2. 维护及时性
        maintenance_overdue = False
        if equipment["next_maintenance_date"]:
            next_date = datetime.strptime(equipment["next_maintenance_date"], '%Y-%m-%d')
            if next_date < datetime.now():
                maintenance_overdue = True
        
        # 3. 使用率
        # 简化计算：假设设备应该使用8小时/天
        days_since_purchase = (datetime.now() - datetime.strptime(equipment["purchase_date"], '%Y-%m-%d')).days
        expected_hours = days_since_purchase * 8
        utilization_rate = (total_time / expected_hours * 100) if expected_hours > 0 else 0
        
        # 4. 综合健康度评分 (0-100)
        health_score = 100
        
        # 故障次数扣分
        health_score -= min(failure_count * 5, 30)
        
        # 维护超期扣分
        if maintenance_overdue:
            health_score -= 15
        
        # 使用率影响（过低或过高都扣分）
        if utilization_rate < 50 or utilization_rate > 120:
            health_score -= 10
        
        health_score = max(0, health_score)
        
        # 健康等级
        if health_score >= 90:
            health_level = "优秀"
        elif health_score >= 75:
            health_level = "良好"
        elif health_score >= 60:
            health_level = "一般"
        else:
            health_level = "需关注"
        
        return {
            "success": True,
            "equipment_id": equipment_id,
            "name": equipment["name"],
            "health_score": round(health_score, 2),
            "health_level": health_level,
            "metrics": {
                "usage_hours": total_time,
                "failure_count": failure_count,
                "mtbf_hours": round(mtbf, 2) if mtbf != float('inf') else "无故障",
                "utilization_rate": round(utilization_rate, 2),
                "maintenance_overdue": maintenance_overdue,
                "maintenance_count": equipment["maintenance_count"]
            }
        }
    
    def get_maintenance_due_list(
        self,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        获取待维护设备列表
        
        Args:
            days_ahead: 提前天数
        
        Returns:
            待维护列表
        """
        due_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        due_list = []
        for equipment in self.equipments.values():
            if equipment["next_maintenance_date"] and equipment["next_maintenance_date"] <= due_date:
                due_list.append({
                    "equipment_id": equipment["equipment_id"],
                    "name": equipment["name"],
                    "next_maintenance_date": equipment["next_maintenance_date"],
                    "last_maintenance_date": equipment["last_maintenance_date"],
                    "status": equipment["status"]
                })
        
        # 按日期排序
        due_list.sort(key=lambda x: x["next_maintenance_date"])
        
        return {
            "success": True,
            "due_within_days": days_ahead,
            "total_count": len(due_list),
            "equipments": due_list
        }
    
    def get_equipment_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取设备统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计报告
        """
        # 按状态统计
        status_stats = {}
        for equipment in self.equipments.values():
            status = equipment["status"]
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 维护统计
        maintenance_in_range = [
            m for m in self.maintenance_records
            if start_date <= m["maintenance_date"] <= end_date
        ]
        
        total_maintenance = len(maintenance_in_range)
        total_maintenance_hours = sum(m["duration_hours"] for m in maintenance_in_range)
        
        # 维修统计
        repairs_in_range = [
            r for r in self.repair_records
            if r["reported_at"] and start_date <= r["reported_at"][:10] <= end_date
        ]
        
        total_repairs = len(repairs_in_range)
        total_repair_cost = sum(r.get("cost", 0) for r in repairs_in_range)
        
        # 平均维修时间
        completed_repairs = [r for r in repairs_in_range if r["status"] == "completed"]
        avg_repair_time = (sum(r.get("actual_duration_hours", 0) for r in completed_repairs) / len(completed_repairs)) if completed_repairs else 0
        
        # 设备可用率
        total_equipments = len(self.equipments)
        available_equipments = status_stats.get(EquipmentStatus.AVAILABLE.value, 0) + status_stats.get(EquipmentStatus.IN_USE.value, 0)
        availability_rate = (available_equipments / total_equipments * 100) if total_equipments > 0 else 0
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_equipments": total_equipments,
                "availability_rate": round(availability_rate, 2)
            },
            "by_status": status_stats,
            "maintenance": {
                "total_count": total_maintenance,
                "total_hours": round(total_maintenance_hours, 2),
                "average_per_equipment": round(total_maintenance / total_equipments, 2) if total_equipments > 0 else 0
            },
            "repair": {
                "total_count": total_repairs,
                "total_cost": round(total_repair_cost, 2),
                "average_repair_time_hours": round(avg_repair_time, 2),
                "completion_rate": round((len(completed_repairs) / total_repairs * 100), 2) if total_repairs > 0 else 0
            }
        }


# 创建默认实例
default_equipment_manager = EquipmentManager()
