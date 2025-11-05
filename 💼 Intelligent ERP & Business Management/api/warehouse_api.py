"""
仓储管理API
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/warehouse", tags=["warehouse"])


@router.get("/inventory")
async def get_inventory(category: Optional[str] = None):
    """获取库存列表"""
    inventory = [
        {
            "id": 1,
            "material_code": "MAT001",
            "material_name": "电子元件A",
            "category": "电子元器件",
            "quantity": 5000,
            "unit": "个",
            "warehouse": "仓库A",
            "location": "A-01-01",
            "safety_stock": 1000,
            "status": "normal"
        },
        {
            "id": 2,
            "material_code": "MAT002",
            "material_name": "原材料B",
            "category": "原材料",
            "quantity": 2500,
            "unit": "kg",
            "warehouse": "仓库B",
            "location": "B-02-05",
            "safety_stock": 500,
            "status": "low_stock"  # 低库存警告
        }
    ]
    
    return {
        "success": True,
        "total": len(inventory),
        "inventory": inventory,
        "low_stock_count": 1
    }


@router.get("/warehouses")
async def get_warehouses():
    """获取仓库列表"""
    warehouses = [
        {
            "id": 1,
            "code": "WH001",
            "name": "主仓库A",
            "type": "成品仓",
            "capacity": 10000,
            "utilization": 0.75,
            "location": "深圳市南山区"
        },
        {
            "id": 2,
            "code": "WH002",
            "name": "原料仓B",
            "type": "原料仓",
            "capacity": 5000,
            "utilization": 0.60,
            "location": "深圳市宝安区"
        }
    ]
    
    return {
        "success": True,
        "total": len(warehouses),
        "warehouses": warehouses
    }


@router.get("/statistics/summary")
async def get_warehouse_summary():
    """获取仓储统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_warehouses": 3,
            "total_inventory_items": 156,
            "total_inventory_value": 8500000,
            "low_stock_items": 12,
            "overstock_items": 5,
            "avg_utilization": 0.68,
            "inventory_turnover_days": 45
        }
    }


