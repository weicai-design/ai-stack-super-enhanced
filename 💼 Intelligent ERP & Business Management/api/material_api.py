"""
物料管理API
Material Management API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/material", tags=["material"])


class MaterialCreate(BaseModel):
    """创建物料"""
    code: str
    name: str
    category: str
    unit: str
    specification: Optional[str] = None
    safety_stock: float = 0


class MRPCalculation(BaseModel):
    """物料需求计划计算"""
    material_code: str
    period_type: str  # daily/weekly/monthly
    start_date: str
    end_date: str


@router.get("/materials")
async def get_materials(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """获取物料列表"""
    materials = [
        {
            "id": 1,
            "code": "MAT001",
            "name": "电阻10KΩ",
            "category": "电子元器件",
            "specification": "1/4W 5%",
            "unit": "个",
            "standard_cost": 0.05,
            "current_stock": 15000,
            "safety_stock": 5000,
            "on_order": 10000,
            "available": 20000,
            "status": "normal",
            "supplier": "深圳电子科技"
        },
        {
            "id": 2,
            "code": "MAT002",
            "name": "电容100μF",
            "category": "电子元器件",
            "specification": "25V 铝电解",
            "unit": "个",
            "standard_cost": 0.15,
            "current_stock": 8000,
            "safety_stock": 3000,
            "on_order": 0,
            "available": 8000,
            "status": "low_stock",
            "supplier": "上海元器件"
        },
        {
            "id": 3,
            "code": "MAT003",
            "name": "PCB板-基础版",
            "category": "印刷电路板",
            "specification": "10x15cm 双层",
            "unit": "片",
            "standard_cost": 8.50,
            "current_stock": 500,
            "safety_stock": 200,
            "on_order": 500,
            "available": 800,
            "status": "normal",
            "supplier": "深圳PCB厂"
        },
        {
            "id": 4,
            "code": "MAT004",
            "name": "塑料外壳-A型",
            "category": "外壳材料",
            "specification": "ABS材质 黑色",
            "unit": "个",
            "standard_cost": 2.30,
            "current_stock": 2000,
            "safety_stock": 1000,
            "on_order": 3000,
            "available": 4000,
            "status": "normal",
            "supplier": "广州塑料厂"
        },
        {
            "id": 5,
            "code": "MAT005",
            "name": "螺丝M3x10",
            "category": "紧固件",
            "specification": "304不锈钢",
            "unit": "个",
            "standard_cost": 0.02,
            "current_stock": 50000,
            "safety_stock": 10000,
            "on_order": 0,
            "available": 50000,
            "status": "overstock",
            "supplier": "标准件公司"
        }
    ]
    
    # 按类别筛选
    if category:
        materials = [m for m in materials if m["category"] == category]
    
    # 按状态筛选
    if status:
        materials = [m for m in materials if m["status"] == status]
    
    return {
        "success": True,
        "total": len(materials),
        "materials": materials[:limit],
        "summary": {
            "normal": len([m for m in materials if m["status"] == "normal"]),
            "low_stock": len([m for m in materials if m["status"] == "low_stock"]),
            "overstock": len([m for m in materials if m["status"] == "overstock"]),
            "out_of_stock": len([m for m in materials if m["status"] == "out_of_stock"])
        }
    }


@router.get("/materials/{material_code}")
async def get_material_detail(material_code: str):
    """获取物料详情"""
    return {
        "success": True,
        "material": {
            "code": material_code,
            "name": "电阻10KΩ",
            "category": "电子元器件",
            "specification": "1/4W 5%",
            "unit": "个",
            "standard_cost": 0.05,
            "current_stock": 15000,
            "safety_stock": 5000,
            "reorder_point": 7000,
            "economic_order_qty": 20000,
            "lead_time_days": 7,
            "supplier_list": [
                {"name": "深圳电子科技", "price": 0.05, "lead_time": 7, "quality_rate": 0.98},
                {"name": "广州元器件", "price": 0.048, "lead_time": 10, "quality_rate": 0.96}
            ],
            "inventory_locations": [
                {"warehouse": "主仓库A", "location": "A-01-05", "quantity": 10000},
                {"warehouse": "分仓库B", "location": "B-03-12", "quantity": 5000}
            ],
            "usage_history": [
                {"date": "2025-10", "usage": 25000, "avg_daily": 833},
                {"date": "2025-09", "usage": 28000, "avg_daily": 933},
                {"date": "2025-08", "usage": 22000, "avg_daily": 733}
            ]
        }
    }


@router.post("/materials")
async def create_material(material: MaterialCreate):
    """创建物料"""
    return {
        "success": True,
        "message": "物料创建成功",
        "material_code": material.code
    }


@router.get("/categories")
async def get_material_categories():
    """获取物料分类"""
    categories = [
        {
            "id": 1,
            "code": "CAT001",
            "name": "电子元器件",
            "parent": None,
            "material_count": 125,
            "subcategories": ["电阻", "电容", "二极管", "三极管", "集成电路"]
        },
        {
            "id": 2,
            "code": "CAT002",
            "name": "印刷电路板",
            "parent": None,
            "material_count": 15,
            "subcategories": ["单层板", "双层板", "多层板", "柔性板"]
        },
        {
            "id": 3,
            "code": "CAT003",
            "name": "外壳材料",
            "parent": None,
            "material_count": 25,
            "subcategories": ["塑料外壳", "金属外壳", "复合材料"]
        },
        {
            "id": 4,
            "code": "CAT004",
            "name": "紧固件",
            "parent": None,
            "material_count": 80,
            "subcategories": ["螺丝", "螺母", "垫片", "铆钉"]
        }
    ]
    
    return {
        "success": True,
        "total": len(categories),
        "categories": categories
    }


@router.post("/mrp/calculate")
async def calculate_mrp(calculation: MRPCalculation):
    """
    计算物料需求计划（Material Requirement Planning）
    基于生产计划、当前库存、在途订单计算物料需求
    """
    # 模拟MRP计算结果
    mrp_result = {
        "material_code": calculation.material_code,
        "material_name": "电阻10KΩ",
        "period": f"{calculation.start_date} 至 {calculation.end_date}",
        "calculation_time": datetime.now().isoformat(),
        "requirements": [
            {
                "date": "2025-11-10",
                "gross_requirement": 5000,  # 毛需求（生产需求）
                "scheduled_receipt": 10000,  # 预计到货
                "on_hand": 15000,  # 期初库存
                "net_requirement": 0,  # 净需求
                "planned_order": 0  # 计划订单
            },
            {
                "date": "2025-11-15",
                "gross_requirement": 8000,
                "scheduled_receipt": 0,
                "on_hand": 17000,
                "net_requirement": 0,
                "planned_order": 0
            },
            {
                "date": "2025-11-20",
                "gross_requirement": 12000,
                "scheduled_receipt": 0,
                "on_hand": 5000,
                "net_requirement": 2000,  # 低于安全库存，产生净需求
                "planned_order": 20000  # 按经济订货量下单
            },
            {
                "date": "2025-11-25",
                "gross_requirement": 6000,
                "scheduled_receipt": 20000,
                "on_hand": 19000,
                "net_requirement": 0,
                "planned_order": 0
            }
        ],
        "summary": {
            "total_gross_requirement": 31000,
            "total_planned_orders": 20000,
            "min_inventory": 5000,
            "max_inventory": 25000,
            "suggested_actions": [
                {
                    "action": "place_order",
                    "material": "电阻10KΩ",
                    "quantity": 20000,
                    "due_date": "2025-11-13",
                    "reason": "预计11-20库存将低于安全库存"
                }
            ]
        }
    }
    
    return {
        "success": True,
        "mrp": mrp_result
    }


@router.get("/statistics/summary")
async def get_material_summary():
    """获取物料管理统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_materials": 245,
            "active_materials": 230,
            "total_categories": 15,
            "total_inventory_value": 3250000,
            "low_stock_materials": 12,
            "overstock_materials": 5,
            "out_of_stock_materials": 3,
            "pending_mrp_actions": 8,
            "avg_inventory_turnover": 6.5,
            "inventory_accuracy": 0.985
        }
    }


@router.get("/statistics/abc-analysis")
async def get_abc_analysis():
    """
    ABC分析：按价值对物料分类
    A类：占总价值70%的物料（重点管理）
    B类：占总价值20%的物料（正常管理）
    C类：占总价值10%的物料（简单管理）
    """
    return {
        "success": True,
        "abc_analysis": {
            "A_class": {
                "material_count": 25,
                "percentage": 10.2,
                "value": 2275000,
                "value_percentage": 70.0,
                "examples": ["PCB板", "集成电路", "高精度传感器"]
            },
            "B_class": {
                "material_count": 60,
                "percentage": 24.5,
                "value": 650000,
                "value_percentage": 20.0,
                "examples": ["电容", "电阻", "塑料外壳"]
            },
            "C_class": {
                "material_count": 160,
                "percentage": 65.3,
                "value": 325000,
                "value_percentage": 10.0,
                "examples": ["螺丝", "标签", "包装材料"]
            }
        },
        "recommendations": [
            "A类物料应实施严格的库存控制和定期盘点",
            "B类物料采用经济订货批量策略",
            "C类物料可采用定期订货系统，简化管理流程"
        ]
    }


@router.get("/alerts")
async def get_material_alerts():
    """获取物料预警信息"""
    alerts = [
        {
            "id": 1,
            "type": "low_stock",
            "severity": "high",
            "material_code": "MAT002",
            "material_name": "电容100μF",
            "current_stock": 2500,
            "safety_stock": 3000,
            "message": "库存已低于安全库存",
            "suggested_action": "建议立即下单采购10000个",
            "created_at": "2025-11-03 10:30:00"
        },
        {
            "id": 2,
            "type": "out_of_stock",
            "severity": "critical",
            "material_code": "MAT015",
            "material_name": "LED灯珠",
            "current_stock": 0,
            "safety_stock": 5000,
            "message": "物料已缺货",
            "suggested_action": "紧急采购，影响生产订单PRD20251103001",
            "created_at": "2025-11-03 09:15:00"
        },
        {
            "id": 3,
            "type": "overstock",
            "severity": "medium",
            "material_code": "MAT005",
            "material_name": "螺丝M3x10",
            "current_stock": 50000,
            "safety_stock": 10000,
            "message": "库存积压，超出安全库存400%",
            "suggested_action": "建议暂停采购，优先使用",
            "created_at": "2025-11-03 08:00:00"
        },
        {
            "id": 4,
            "type": "slow_moving",
            "severity": "low",
            "material_code": "MAT025",
            "material_name": "旧款外壳",
            "current_stock": 1200,
            "avg_usage_monthly": 50,
            "months_supply": 24,
            "message": "呆滞物料，建议处理",
            "suggested_action": "考虑促销或报废处理",
            "created_at": "2025-11-02 16:00:00"
        }
    ]
    
    return {
        "success": True,
        "total": len(alerts),
        "alerts": alerts,
        "summary": {
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 1
        }
    }

