"""
设备管理API
Equipment Management API
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


class MaintenanceRecord(BaseModel):
    """维护记录"""
    equipment_id: int
    maintenance_type: str  # preventive/corrective/emergency
    description: str
    cost: float


@router.get("/equipment")
async def get_equipment_list(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """获取设备列表"""
    equipment = [
        {
            "id": 1,
            "code": "EQ001",
            "name": "自动焊接机A1",
            "category": "焊接设备",
            "model": "WD-3000",
            "manufacturer": "日本焊接株式会社",
            "location": "生产车间1-A区",
            "status": "running",
            "utilization_rate": 0.85,
            "efficiency": 0.92,
            "purchase_date": "2023-05-15",
            "warranty_until": "2026-05-15",
            "last_maintenance": "2025-10-25",
            "next_maintenance": "2025-12-25",
            "total_runtime_hours": 5280,
            "downtime_hours": 45,
            "failure_count": 3
        },
        {
            "id": 2,
            "code": "EQ002",
            "name": "SMT贴片机B2",
            "category": "贴片设备",
            "model": "SMT-5000",
            "manufacturer": "韩国电子设备",
            "location": "生产车间1-B区",
            "status": "running",
            "utilization_rate": 0.78,
            "efficiency": 0.88,
            "purchase_date": "2024-02-20",
            "warranty_until": "2027-02-20",
            "last_maintenance": "2025-11-01",
            "next_maintenance": "2026-01-01",
            "total_runtime_hours": 3200,
            "downtime_hours": 28,
            "failure_count": 2
        },
        {
            "id": 3,
            "code": "EQ003",
            "name": "AOI检测机C1",
            "category": "检测设备",
            "model": "AOI-2000",
            "manufacturer": "深圳检测设备",
            "location": "质检区",
            "status": "maintenance",
            "utilization_rate": 0.72,
            "efficiency": 0.95,
            "purchase_date": "2023-08-10",
            "warranty_until": "2026-08-10",
            "last_maintenance": "2025-11-03",
            "next_maintenance": "2026-02-03",
            "total_runtime_hours": 4560,
            "downtime_hours": 72,
            "failure_count": 5
        },
        {
            "id": 4,
            "code": "EQ004",
            "name": "注塑机D1",
            "category": "成型设备",
            "model": "INJ-800",
            "manufacturer": "广州塑料机械",
            "location": "生产车间2",
            "status": "idle",
            "utilization_rate": 0.55,
            "efficiency": 0.82,
            "purchase_date": "2022-11-05",
            "warranty_until": "2025-11-05",
            "last_maintenance": "2025-09-15",
            "next_maintenance": "2025-12-15",
            "total_runtime_hours": 8200,
            "downtime_hours": 156,
            "failure_count": 12
        }
    ]
    
    # 筛选
    if category:
        equipment = [e for e in equipment if e["category"] == category]
    if status:
        equipment = [e for e in equipment if e["status"] == status]
    
    return {
        "success": True,
        "total": len(equipment),
        "equipment": equipment[:limit],
        "summary": {
            "running": len([e for e in equipment if e["status"] == "running"]),
            "idle": len([e for e in equipment if e["status"] == "idle"]),
            "maintenance": len([e for e in equipment if e["status"] == "maintenance"]),
            "breakdown": len([e for e in equipment if e["status"] == "breakdown"])
        }
    }


@router.get("/equipment/{equipment_code}")
async def get_equipment_detail(equipment_code: str):
    """获取设备详情"""
    return {
        "success": True,
        "equipment": {
            "code": equipment_code,
            "name": "自动焊接机A1",
            "category": "焊接设备",
            "model": "WD-3000",
            "manufacturer": "日本焊接株式会社",
            "serial_number": "WD3000-2023-05-001",
            "purchase_date": "2023-05-15",
            "purchase_cost": 580000,
            "location": "生产车间1-A区",
            "responsible_person": "李维护",
            "status": "running",
            "specifications": {
                "power": "15KW",
                "voltage": "380V",
                "max_speed": "1200点/小时",
                "accuracy": "±0.05mm"
            },
            "performance": {
                "utilization_rate": 0.85,
                "efficiency": 0.92,
                "availability": 0.95,
                "oee": 0.83
            },
            "runtime": {
                "total_hours": 5280,
                "this_month": 245,
                "today": 8.5,
                "cycles_completed": 125000
            },
            "maintenance": {
                "last_maintenance": "2025-10-25",
                "next_maintenance": "2025-12-25",
                "maintenance_interval_days": 60,
                "total_maintenances": 18,
                "total_maintenance_cost": 45000
            },
            "failures": {
                "total_count": 3,
                "total_downtime_hours": 12,
                "mtbf": 1760,  # Mean Time Between Failures
                "mttr": 4  # Mean Time To Repair
            }
        }
    }


@router.get("/maintenance/records")
async def get_maintenance_records(
    equipment_id: Optional[int] = None,
    maintenance_type: Optional[str] = None
):
    """获取维护记录"""
    records = [
        {
            "id": 1,
            "equipment_code": "EQ001",
            "equipment_name": "自动焊接机A1",
            "maintenance_type": "preventive",
            "maintenance_date": "2025-10-25",
            "duration_hours": 4,
            "cost": 2500,
            "performed_by": "李维护",
            "description": "定期保养：清洁、润滑、检查",
            "parts_replaced": ["过滤网", "润滑油"],
            "next_maintenance": "2025-12-25",
            "status": "completed"
        },
        {
            "id": 2,
            "equipment_code": "EQ003",
            "equipment_name": "AOI检测机C1",
            "maintenance_type": "corrective",
            "maintenance_date": "2025-11-03",
            "duration_hours": 6,
            "cost": 8500,
            "performed_by": "张工程师",
            "description": "更换故障镜头模组",
            "parts_replaced": ["镜头模组", "控制板"],
            "next_maintenance": "2026-02-03",
            "status": "completed"
        },
        {
            "id": 3,
            "equipment_code": "EQ002",
            "equipment_name": "SMT贴片机B2",
            "maintenance_type": "preventive",
            "maintenance_date": "2025-11-01",
            "duration_hours": 3,
            "cost": 1800,
            "performed_by": "王技师",
            "description": "月度保养检查",
            "parts_replaced": [],
            "next_maintenance": "2026-01-01",
            "status": "completed"
        }
    ]
    
    if equipment_id:
        records = [r for r in records if r.get("equipment_id") == equipment_id]
    if maintenance_type:
        records = [r for r in records if r["maintenance_type"] == maintenance_type]
    
    return {
        "success": True,
        "total": len(records),
        "records": records
    }


@router.post("/maintenance/records")
async def create_maintenance_record(record: MaintenanceRecord):
    """创建维护记录"""
    return {
        "success": True,
        "message": "维护记录创建成功",
        "record_id": 1
    }


@router.get("/maintenance/plan")
async def get_maintenance_plan(month: Optional[str] = None):
    """获取维护计划"""
    plan = [
        {
            "date": "2025-11-15",
            "equipment_code": "EQ004",
            "equipment_name": "注塑机D1",
            "maintenance_type": "preventive",
            "estimated_duration": 4,
            "estimated_cost": 3000,
            "responsible": "李维护",
            "status": "scheduled"
        },
        {
            "date": "2025-11-20",
            "equipment_code": "EQ001",
            "equipment_name": "自动焊接机A1",
            "maintenance_type": "inspection",
            "estimated_duration": 2,
            "estimated_cost": 500,
            "responsible": "王技师",
            "status": "scheduled"
        },
        {
            "date": "2025-12-25",
            "equipment_code": "EQ001",
            "equipment_name": "自动焊接机A1",
            "maintenance_type": "preventive",
            "estimated_duration": 4,
            "estimated_cost": 2500,
            "responsible": "李维护",
            "status": "scheduled"
        }
    ]
    
    return {
        "success": True,
        "total": len(plan),
        "plan": plan,
        "summary": {
            "total_maintenances": 3,
            "total_estimated_hours": 10,
            "total_estimated_cost": 6000
        }
    }


@router.get("/failures")
async def get_failure_records(
    equipment_id: Optional[int] = None,
    severity: Optional[str] = None
):
    """获取故障记录"""
    failures = [
        {
            "id": 1,
            "equipment_code": "EQ001",
            "equipment_name": "自动焊接机A1",
            "failure_date": "2025-10-15 14:30:00",
            "failure_type": "mechanical",
            "severity": "medium",
            "description": "传动带打滑",
            "downtime_hours": 2.5,
            "repair_cost": 1200,
            "root_cause": "传动带老化磨损",
            "corrective_action": "更换新传动带",
            "repaired_by": "李维护",
            "status": "resolved"
        },
        {
            "id": 2,
            "equipment_code": "EQ003",
            "equipment_name": "AOI检测机C1",
            "failure_date": "2025-11-02 09:15:00",
            "failure_type": "electrical",
            "severity": "high",
            "description": "视觉系统无法启动",
            "downtime_hours": 6,
            "repair_cost": 8500,
            "root_cause": "镜头模组控制板故障",
            "corrective_action": "更换镜头模组和控制板",
            "repaired_by": "张工程师",
            "status": "resolved"
        },
        {
            "id": 3,
            "equipment_code": "EQ004",
            "equipment_name": "注塑机D1",
            "failure_date": "2025-09-20 11:00:00",
            "failure_type": "hydraulic",
            "severity": "medium",
            "description": "液压压力不稳定",
            "downtime_hours": 4,
            "repair_cost": 3500,
            "root_cause": "液压泵密封件老化",
            "corrective_action": "更换液压泵密封件",
            "repaired_by": "王技师",
            "status": "resolved"
        }
    ]
    
    return {
        "success": True,
        "total": len(failures),
        "failures": failures,
        "summary": {
            "total_downtime": 12.5,
            "total_repair_cost": 13200,
            "by_severity": {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 0
            }
        }
    }


@router.get("/statistics/summary")
async def get_equipment_summary():
    """获取设备统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_equipment": 45,
            "running": 32,
            "idle": 8,
            "maintenance": 3,
            "breakdown": 2,
            "avg_utilization_rate": 0.75,
            "avg_efficiency": 0.88,
            "avg_oee": 0.79,
            "total_maintenance_cost_this_month": 25000,
            "total_downtime_hours_this_month": 45,
            "scheduled_maintenances_this_month": 8
        }
    }


@router.get("/statistics/utilization")
async def get_utilization_analysis():
    """获取设备利用率分析"""
    return {
        "success": True,
        "utilization": {
            "overall_utilization": 0.75,
            "target_utilization": 0.85,
            "by_category": [
                {"category": "焊接设备", "utilization": 0.82, "equipment_count": 5},
                {"category": "贴片设备", "utilization": 0.78, "equipment_count": 3},
                {"category": "检测设备", "utilization": 0.85, "equipment_count": 4},
                {"category": "成型设备", "utilization": 0.65, "equipment_count": 6}
            ],
            "underutilized_equipment": [
                {"code": "EQ004", "name": "注塑机D1", "utilization": 0.55},
                {"code": "EQ015", "name": "钻孔机E3", "utilization": 0.48}
            ],
            "recommendations": [
                "注塑机D1利用率偏低，建议调整生产计划增加排产",
                "钻孔机E3产能闲置，可考虑外协加工订单"
            ]
        }
    }


@router.get("/statistics/reliability")
async def get_reliability_analysis():
    """获取设备可靠性分析"""
    return {
        "success": True,
        "reliability": {
            "overall_mtbf": 1580,  # 平均无故障时间（小时）
            "overall_mttr": 4.2,  # 平均修复时间（小时）
            "availability": 0.95,  # 可用度
            "by_equipment": [
                {
                    "code": "EQ001",
                    "name": "自动焊接机A1",
                    "mtbf": 1760,
                    "mttr": 4,
                    "failure_rate": 0.000568,
                    "availability": 0.978
                },
                {
                    "code": "EQ003",
                    "name": "AOI检测机C1",
                    "mtbf": 912,
                    "mttr": 7.2,
                    "failure_rate": 0.001096,
                    "availability": 0.921
                }
            ],
            "failure_trend": [
                {"month": "2025-08", "failures": 5, "downtime": 28},
                {"month": "2025-09", "failures": 4, "downtime": 22},
                {"month": "2025-10", "failures": 6, "downtime": 35},
                {"month": "2025-11", "failures": 3, "downtime": 18}
            ]
        }
    }

