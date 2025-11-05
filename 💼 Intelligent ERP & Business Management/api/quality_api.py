"""
质量管理API
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.get("/inspections")
async def get_inspections(status: Optional[str] = None):
    """获取质检记录"""
    inspections = [
        {
            "id": 1,
            "inspection_no": "QC20251101001",
            "type": "incoming",  # 来料检验
            "material_name": "电子元件A",
            "batch_no": "BATCH001",
            "quantity": 1000,
            "sample_size": 50,
            "passed": 48,
            "failed": 2,
            "pass_rate": 0.96,
            "inspector": "质检员A",
            "inspection_date": "2025-11-01",
            "result": "qualified",
            "notes": ""
        },
        {
            "id": 2,
            "inspection_no": "QC20251102001",
            "type": "process",  # 过程检验
            "product_name": "产品X",
            "process_step": "装配",
            "quantity": 500,
            "sample_size": 25,
            "passed": 25,
            "failed": 0,
            "pass_rate": 1.0,
            "inspector": "质检员B",
            "inspection_date": "2025-11-02",
            "result": "qualified"
        }
    ]
    
    return {
        "success": True,
        "total": len(inspections),
        "inspections": inspections
    }


@router.get("/statistics/summary")
async def get_quality_summary():
    """获取质量统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_inspections_this_month": 156,
            "avg_pass_rate": 0.97,
            "incoming_pass_rate": 0.96,
            "process_pass_rate": 0.98,
            "final_pass_rate": 0.99,
            "total_defects": 45,
            "critical_defects": 3,
            "major_defects": 15,
            "minor_defects": 27,
            "customer_complaint_rate": 0.02
        }
    }


@router.get("/defects")
async def get_defects(severity: Optional[str] = None):
    """获取质量问题列表"""
    defects = [
        {
            "id": 1,
            "defect_no": "DEF001",
            "type": "外观缺陷",
            "severity": "minor",
            "product": "产品X",
            "description": "表面划痕",
            "found_by": "质检员A",
            "found_date": "2025-11-01",
            "status": "closed",
            "corrective_action": "加强包装保护"
        },
        {
            "id": 2,
            "defect_no": "DEF002",
            "type": "尺寸偏差",
            "severity": "major",
            "product": "产品Y",
            "description": "长度超出公差",
            "found_by": "质检员B",
            "found_date": "2025-11-02",
            "status": "investigating",
            "corrective_action": ""
        }
    ]
    
    return {
        "success": True,
        "total": len(defects),
        "defects": defects
    }


