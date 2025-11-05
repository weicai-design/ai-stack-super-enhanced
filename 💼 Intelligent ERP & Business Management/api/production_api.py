"""
生产管理API
Production Management API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/production", tags=["production"])


class ProductionOrderCreate(BaseModel):
    """创建生产订单"""
    product_code: str
    quantity: float
    due_date: str
    priority: str = "normal"  # low/normal/high/urgent


@router.get("/orders")
async def get_production_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50
):
    """获取生产订单列表"""
    orders = [
        {
            "id": 1,
            "order_no": "PRD20251101001",
            "product_code": "PROD-001",
            "product_name": "智能控制器A型",
            "quantity": 1000,
            "completed_quantity": 850,
            "completion_rate": 0.85,
            "start_date": "2025-11-01",
            "due_date": "2025-11-10",
            "actual_finish_date": None,
            "status": "in_progress",
            "priority": "high",
            "workshop": "生产车间1",
            "responsible_person": "李经理"
        },
        {
            "id": 2,
            "order_no": "PRD20251102001",
            "product_code": "PROD-002",
            "product_name": "传感器B型",
            "quantity": 2000,
            "completed_quantity": 2000,
            "completion_rate": 1.0,
            "start_date": "2025-10-25",
            "due_date": "2025-11-02",
            "actual_finish_date": "2025-11-02",
            "status": "completed",
            "priority": "normal",
            "workshop": "生产车间2",
            "responsible_person": "张主管"
        },
        {
            "id": 3,
            "order_no": "PRD20251103001",
            "product_code": "PROD-003",
            "product_name": "电源模块C型",
            "quantity": 500,
            "completed_quantity": 0,
            "completion_rate": 0.0,
            "start_date": "2025-11-05",
            "due_date": "2025-11-15",
            "actual_finish_date": None,
            "status": "planned",
            "priority": "normal",
            "workshop": "生产车间1",
            "responsible_person": "王工程师"
        }
    ]
    
    # 状态筛选
    if status:
        orders = [o for o in orders if o["status"] == status]
    
    # 优先级筛选
    if priority:
        orders = [o for o in orders if o["priority"] == priority]
    
    return {
        "success": True,
        "total": len(orders),
        "orders": orders[:limit],
        "summary": {
            "planned": len([o for o in orders if o["status"] == "planned"]),
            "in_progress": len([o for o in orders if o["status"] == "in_progress"]),
            "completed": len([o for o in orders if o["status"] == "completed"]),
            "delayed": len([o for o in orders if o["status"] == "delayed"])
        }
    }


@router.get("/orders/{order_no}")
async def get_production_order_detail(order_no: str):
    """获取生产订单详情"""
    return {
        "success": True,
        "order": {
            "order_no": order_no,
            "product_code": "PROD-001",
            "product_name": "智能控制器A型",
            "specification": "标准版 V2.0",
            "quantity": 1000,
            "completed_quantity": 850,
            "qualified_quantity": 840,
            "reject_quantity": 10,
            "status": "in_progress",
            "priority": "high",
            "workshop": "生产车间1",
            "production_line": "产线A",
            "start_date": "2025-11-01 08:00:00",
            "due_date": "2025-11-10 18:00:00",
            "estimated_finish": "2025-11-09 16:00:00",
            "processes": [
                {
                    "seq": 1,
                    "process_name": "物料准备",
                    "status": "completed",
                    "planned_time": 2,
                    "actual_time": 1.5,
                    "responsible": "仓库组"
                },
                {
                    "seq": 2,
                    "process_name": "PCB组装",
                    "status": "completed",
                    "planned_time": 20,
                    "actual_time": 18,
                    "responsible": "组装组"
                },
                {
                    "seq": 3,
                    "process_name": "焊接",
                    "status": "in_progress",
                    "planned_time": 15,
                    "actual_time": 12,
                    "completion_rate": 0.85,
                    "responsible": "焊接组"
                },
                {
                    "seq": 4,
                    "process_name": "功能测试",
                    "status": "pending",
                    "planned_time": 8,
                    "actual_time": 0,
                    "responsible": "测试组"
                },
                {
                    "seq": 5,
                    "process_name": "包装入库",
                    "status": "pending",
                    "planned_time": 3,
                    "actual_time": 0,
                    "responsible": "包装组"
                }
            ],
            "material_usage": [
                {"material": "PCB板", "planned": 1000, "actual": 850, "shortage": 0},
                {"material": "电阻", "planned": 10000, "actual": 8500, "shortage": 0},
                {"material": "外壳", "planned": 1000, "actual": 850, "shortage": 0}
            ],
            "quality_records": [
                {"date": "2025-11-01", "inspected": 100, "passed": 98, "failed": 2},
                {"date": "2025-11-02", "inspected": 200, "passed": 198, "failed": 2}
            ]
        }
    }


@router.post("/orders")
async def create_production_order(order: ProductionOrderCreate):
    """创建生产订单"""
    return {
        "success": True,
        "message": "生产订单创建成功",
        "order_no": f"PRD{datetime.now().strftime('%Y%m%d')}001"
    }


@router.get("/schedule")
async def get_production_schedule(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取生产排程"""
    schedule = {
        "period": "2025-11-01 至 2025-11-15",
        "workshops": [
            {
                "workshop": "生产车间1",
                "capacity": 100,
                "utilization": 0.85,
                "schedule": [
                    {
                        "date": "2025-11-05",
                        "orders": [
                            {"order_no": "PRD20251101001", "product": "智能控制器A型", "quantity": 150},
                            {"order_no": "PRD20251103001", "product": "电源模块C型", "quantity": 100}
                        ],
                        "capacity_used": 85
                    },
                    {
                        "date": "2025-11-06",
                        "orders": [
                            {"order_no": "PRD20251101001", "product": "智能控制器A型", "quantity": 150}
                        ],
                        "capacity_used": 50
                    }
                ]
            },
            {
                "workshop": "生产车间2",
                "capacity": 150,
                "utilization": 0.72,
                "schedule": [
                    {
                        "date": "2025-11-05",
                        "orders": [
                            {"order_no": "PRD20251104001", "product": "传感器B型", "quantity": 300}
                        ],
                        "capacity_used": 108
                    }
                ]
            }
        ]
    }
    
    return {
        "success": True,
        "schedule": schedule
    }


@router.get("/capacity")
async def get_production_capacity():
    """获取产能分析"""
    return {
        "success": True,
        "capacity": {
            "total_capacity": 250,  # 每日产能（标准工时）
            "used_capacity": 195,
            "available_capacity": 55,
            "utilization_rate": 0.78,
            "by_workshop": [
                {
                    "workshop": "生产车间1",
                    "capacity": 100,
                    "used": 85,
                    "utilization": 0.85
                },
                {
                    "workshop": "生产车间2",
                    "capacity": 150,
                    "used": 110,
                    "utilization": 0.73
                }
            ],
            "by_product_line": [
                {
                    "line": "产线A",
                    "capacity": 50,
                    "used": 45,
                    "efficiency": 0.92,
                    "products": ["智能控制器", "电源模块"]
                },
                {
                    "line": "产线B",
                    "capacity": 50,
                    "used": 40,
                    "efficiency": 0.88,
                    "products": ["传感器", "开关"]
                }
            ],
            "bottleneck_processes": [
                {"process": "焊接", "capacity": 30, "load": 28, "is_bottleneck": True},
                {"process": "测试", "capacity": 40, "load": 35, "is_bottleneck": False}
            ]
        }
    }


@router.get("/efficiency")
async def get_production_efficiency():
    """获取生产效率分析"""
    return {
        "success": True,
        "efficiency": {
            "overall_efficiency": 0.87,
            "target_efficiency": 0.90,
            "metrics": {
                "oee": 0.85,  # Overall Equipment Effectiveness 设备综合效率
                "availability": 0.95,  # 可用率
                "performance": 0.92,  # 表现指数
                "quality": 0.97  # 质量指数
            },
            "by_workshop": [
                {
                    "workshop": "生产车间1",
                    "efficiency": 0.88,
                    "output_per_hour": 42,
                    "target_output": 50,
                    "first_pass_yield": 0.96
                },
                {
                    "workshop": "生产车间2",
                    "efficiency": 0.86,
                    "output_per_hour": 65,
                    "target_output": 75,
                    "first_pass_yield": 0.98
                }
            ],
            "improvement_suggestions": [
                "焊接工序效率偏低，建议增加设备或优化流程",
                "产线A的设备故障率较高，建议加强预防性维护",
                "建议对操作人员进行标准化作业培训"
            ]
        }
    }


@router.get("/statistics/summary")
async def get_production_summary():
    """获取生产统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_orders_this_month": 45,
            "completed_orders": 32,
            "in_progress_orders": 10,
            "planned_orders": 3,
            "on_time_completion_rate": 0.91,
            "total_output": 25000,
            "total_output_value": 1850000,
            "avg_cycle_time_days": 5.2,
            "overall_efficiency": 0.87,
            "quality_pass_rate": 0.97
        }
    }


@router.get("/kpi")
async def get_production_kpi():
    """获取生产KPI指标"""
    return {
        "success": True,
        "kpi": {
            "period": "2025-11",
            "indicators": [
                {
                    "name": "产量达成率",
                    "target": 100,
                    "actual": 95,
                    "unit": "%",
                    "status": "warning"
                },
                {
                    "name": "准时交付率",
                    "target": 95,
                    "actual": 91,
                    "unit": "%",
                    "status": "warning"
                },
                {
                    "name": "一次合格率",
                    "target": 98,
                    "actual": 97,
                    "unit": "%",
                    "status": "good"
                },
                {
                    "name": "设备利用率",
                    "target": 85,
                    "actual": 78,
                    "unit": "%",
                    "status": "warning"
                },
                {
                    "name": "人均产值",
                    "target": 50000,
                    "actual": 48500,
                    "unit": "元",
                    "status": "good"
                }
            ],
            "trend": [
                {"month": "2025-08", "efficiency": 0.85, "quality": 0.96},
                {"month": "2025-09", "efficiency": 0.86, "quality": 0.96},
                {"month": "2025-10", "efficiency": 0.87, "quality": 0.97},
                {"month": "2025-11", "efficiency": 0.87, "quality": 0.97}
            ]
        }
    }

