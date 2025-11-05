"""
工艺管理API
Process Engineering Management API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/engineering", tags=["engineering"])


class ProcessRouteCreate(BaseModel):
    """创建工艺路线"""
    product_code: str
    route_name: str
    version: str = "1.0"


class ProcessStepCreate(BaseModel):
    """创建工艺步骤"""
    route_id: int
    step_sequence: int
    operation_name: str
    standard_time: float
    equipment_required: Optional[str] = None


@router.get("/routes")
async def get_process_routes(
    product_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """获取工艺路线列表"""
    routes = [
        {
            "id": 1,
            "route_code": "RT001",
            "route_name": "智能控制器A型标准工艺",
            "product_code": "PROD-001",
            "product_name": "智能控制器A型",
            "version": "2.0",
            "status": "active",
            "effective_date": "2025-01-01",
            "created_by": "工艺工程师张三",
            "created_at": "2024-12-15",
            "total_steps": 8,
            "total_standard_time": 48.5,
            "yield_rate": 0.97,
            "revision_count": 3
        },
        {
            "id": 2,
            "route_code": "RT002",
            "route_name": "传感器B型快速工艺",
            "product_code": "PROD-002",
            "product_name": "传感器B型",
            "version": "1.5",
            "status": "active",
            "effective_date": "2024-10-01",
            "created_by": "工艺工程师李四",
            "created_at": "2024-09-20",
            "total_steps": 6,
            "total_standard_time": 32.0,
            "yield_rate": 0.98,
            "revision_count": 2
        },
        {
            "id": 3,
            "route_code": "RT003",
            "route_name": "电源模块C型精密工艺",
            "product_code": "PROD-003",
            "product_name": "电源模块C型",
            "version": "1.0",
            "status": "draft",
            "effective_date": None,
            "created_by": "工艺工程师王五",
            "created_at": "2025-11-01",
            "total_steps": 10,
            "total_standard_time": 62.0,
            "yield_rate": 0.95,
            "revision_count": 0
        }
    ]
    
    # 筛选
    if product_code:
        routes = [r for r in routes if r["product_code"] == product_code]
    if status:
        routes = [r for r in routes if r["status"] == status]
    
    return {
        "success": True,
        "total": len(routes),
        "routes": routes[:limit],
        "summary": {
            "active": len([r for r in routes if r["status"] == "active"]),
            "draft": len([r for r in routes if r["status"] == "draft"]),
            "obsolete": len([r for r in routes if r["status"] == "obsolete"])
        }
    }


@router.get("/routes/{route_code}")
async def get_process_route_detail(route_code: str):
    """获取工艺路线详情"""
    return {
        "success": True,
        "route": {
            "route_code": route_code,
            "route_name": "智能控制器A型标准工艺",
            "product_code": "PROD-001",
            "product_name": "智能控制器A型",
            "version": "2.0",
            "status": "active",
            "effective_date": "2025-01-01",
            "created_by": "工艺工程师张三",
            "approved_by": "技术总监赵六",
            "steps": [
                {
                    "sequence": 1,
                    "operation_code": "OP-001",
                    "operation_name": "物料准备",
                    "description": "按BOM清单准备所有物料和工具",
                    "equipment": "物料车",
                    "tooling": "静电手环、防护手套",
                    "standard_time": 2.0,
                    "setup_time": 0.5,
                    "workers_required": 1,
                    "skill_level": "初级",
                    "quality_checkpoints": ["物料完整性检查", "数量核对"],
                    "safety_notes": ["穿戴防静电装备"]
                },
                {
                    "sequence": 2,
                    "operation_code": "OP-002",
                    "operation_name": "PCB板检验",
                    "description": "对PCB板进行外观和尺寸检验",
                    "equipment": "AOI检测机",
                    "tooling": "千分尺、放大镜",
                    "standard_time": 3.0,
                    "setup_time": 1.0,
                    "workers_required": 1,
                    "skill_level": "中级",
                    "quality_checkpoints": ["外观检查", "尺寸测量", "阻抗测试"],
                    "safety_notes": ["轻拿轻放"]
                },
                {
                    "sequence": 3,
                    "operation_code": "OP-003",
                    "operation_name": "SMT贴片",
                    "description": "使用SMT设备进行元器件贴装",
                    "equipment": "SMT贴片机B2",
                    "tooling": "贴片吸嘴、钢网",
                    "standard_time": 15.0,
                    "setup_time": 5.0,
                    "workers_required": 2,
                    "skill_level": "高级",
                    "quality_checkpoints": ["贴装位置", "贴装角度", "焊膏量"],
                    "safety_notes": ["设备运行时禁止触碰", "注意高温区域"],
                    "parameters": {
                        "temperature": "230-250°C",
                        "speed": "15000 CPH",
                        "accuracy": "±0.05mm"
                    }
                },
                {
                    "sequence": 4,
                    "operation_code": "OP-004",
                    "operation_name": "回流焊接",
                    "description": "通过回流焊炉完成焊接",
                    "equipment": "回流焊炉",
                    "tooling": None,
                    "standard_time": 8.0,
                    "setup_time": 2.0,
                    "workers_required": 1,
                    "skill_level": "中级",
                    "quality_checkpoints": ["焊点质量", "无虚焊桥接"],
                    "safety_notes": ["高温作业，保持距离"],
                    "parameters": {
                        "peak_temperature": "245°C",
                        "time_above_liquidus": "60-90s",
                        "cooling_rate": "3-5°C/s"
                    }
                },
                {
                    "sequence": 5,
                    "operation_code": "OP-005",
                    "operation_name": "人工插件",
                    "description": "人工插装直插元器件",
                    "equipment": "工作台",
                    "tooling": "镊子、斜口钳",
                    "standard_time": 6.0,
                    "setup_time": 0.5,
                    "workers_required": 2,
                    "skill_level": "初级",
                    "quality_checkpoints": ["插装方向", "插装到位"],
                    "safety_notes": ["注意引脚扎手"]
                },
                {
                    "sequence": 6,
                    "operation_code": "OP-006",
                    "operation_name": "波峰焊接",
                    "description": "直插元器件波峰焊",
                    "equipment": "波峰焊机",
                    "tooling": "治具",
                    "standard_time": 5.0,
                    "setup_time": 1.5,
                    "workers_required": 1,
                    "skill_level": "中级",
                    "quality_checkpoints": ["焊点饱满", "无桥连"],
                    "safety_notes": ["高温液态焊锡，严禁触碰"],
                    "parameters": {
                        "solder_temperature": "260°C",
                        "wave_height": "6-8mm",
                        "conveyor_angle": "6°"
                    }
                },
                {
                    "sequence": 7,
                    "operation_code": "OP-007",
                    "operation_name": "功能测试",
                    "description": "全功能电气性能测试",
                    "equipment": "自动测试台",
                    "tooling": "测试夹具、万用表",
                    "standard_time": 8.0,
                    "setup_time": 1.0,
                    "workers_required": 1,
                    "skill_level": "高级",
                    "quality_checkpoints": ["电气性能", "功能完整性", "参数范围"],
                    "safety_notes": ["测试时注意用电安全"],
                    "test_items": [
                        "电源电压测试",
                        "功耗测试",
                        "信号完整性测试",
                        "温升测试",
                        "EMC测试"
                    ]
                },
                {
                    "sequence": 8,
                    "operation_code": "OP-008",
                    "operation_name": "包装入库",
                    "description": "成品包装和入库",
                    "equipment": "包装台",
                    "tooling": "包装盒、防静电袋、标签打印机",
                    "standard_time": 1.5,
                    "setup_time": 0.2,
                    "workers_required": 1,
                    "skill_level": "初级",
                    "quality_checkpoints": ["包装完整", "标签正确"],
                    "safety_notes": ["轻拿轻放"]
                }
            ],
            "materials": [
                {"code": "MAT001", "name": "电阻10KΩ", "quantity": 10, "unit": "个"},
                {"code": "MAT002", "name": "电容100μF", "quantity": 5, "unit": "个"},
                {"code": "MAT003", "name": "PCB板-基础版", "quantity": 1, "unit": "片"}
            ],
            "quality_metrics": {
                "target_yield": 0.98,
                "actual_yield": 0.97,
                "first_pass_yield": 0.95,
                "defect_rate": 0.03
            },
            "change_history": [
                {
                    "version": "2.0",
                    "date": "2025-01-01",
                    "changed_by": "张三",
                    "change_reason": "优化SMT贴片工艺参数，提高良率",
                    "approved_by": "赵六"
                },
                {
                    "version": "1.0",
                    "date": "2024-06-01",
                    "changed_by": "张三",
                    "change_reason": "初始版本发布",
                    "approved_by": "赵六"
                }
            ]
        }
    }


@router.post("/routes")
async def create_process_route(route: ProcessRouteCreate):
    """创建工艺路线"""
    return {
        "success": True,
        "message": "工艺路线创建成功",
        "route_code": f"RT{datetime.now().strftime('%Y%m%d')}001"
    }


@router.get("/parameters")
async def get_process_parameters(
    operation_code: Optional[str] = None,
    equipment: Optional[str] = None
):
    """获取工艺参数"""
    parameters = [
        {
            "id": 1,
            "parameter_code": "PARAM-SMT-001",
            "operation": "SMT贴片",
            "equipment": "SMT贴片机B2",
            "parameter_name": "贴装速度",
            "standard_value": "15000 CPH",
            "lower_limit": "14000 CPH",
            "upper_limit": "16000 CPH",
            "unit": "CPH",
            "control_type": "SPC",
            "measurement_method": "设备显示",
            "check_frequency": "每班次"
        },
        {
            "id": 2,
            "parameter_code": "PARAM-SMT-002",
            "operation": "SMT贴片",
            "equipment": "SMT贴片机B2",
            "parameter_name": "贴装精度",
            "standard_value": "±0.05mm",
            "lower_limit": "±0.08mm",
            "upper_limit": "±0.03mm",
            "unit": "mm",
            "control_type": "SPC",
            "measurement_method": "AOI检测",
            "check_frequency": "每小时抽检"
        },
        {
            "id": 3,
            "parameter_code": "PARAM-REFLOW-001",
            "operation": "回流焊接",
            "equipment": "回流焊炉",
            "parameter_name": "峰值温度",
            "standard_value": "245°C",
            "lower_limit": "240°C",
            "upper_limit": "250°C",
            "unit": "°C",
            "control_type": "实时监控",
            "measurement_method": "热电偶",
            "check_frequency": "连续监控"
        },
        {
            "id": 4,
            "parameter_code": "PARAM-REFLOW-002",
            "operation": "回流焊接",
            "equipment": "回流焊炉",
            "parameter_name": "液相时间",
            "standard_value": "75s",
            "lower_limit": "60s",
            "upper_limit": "90s",
            "unit": "s",
            "control_type": "SPC",
            "measurement_method": "温度曲线分析",
            "check_frequency": "每班次"
        }
    ]
    
    if operation_code:
        parameters = [p for p in parameters if p.get("operation_code") == operation_code]
    if equipment:
        parameters = [p for p in parameters if equipment in p.get("equipment", "")]
    
    return {
        "success": True,
        "total": len(parameters),
        "parameters": parameters
    }


@router.get("/changes")
async def get_process_changes(
    status: Optional[str] = None,
    limit: int = 20
):
    """获取工艺变更记录"""
    changes = [
        {
            "id": 1,
            "change_no": "ECN20251101001",
            "change_type": "工艺参数调整",
            "route_code": "RT001",
            "route_name": "智能控制器A型标准工艺",
            "from_version": "1.0",
            "to_version": "2.0",
            "change_description": "优化SMT贴片温度曲线，从230-240°C调整为235-245°C，提高焊接可靠性",
            "change_reason": "质量改进，降低虚焊率",
            "initiator": "质量部李工",
            "submit_date": "2024-12-20",
            "approver": "技术总监赵六",
            "approve_date": "2024-12-28",
            "effective_date": "2025-01-01",
            "status": "approved",
            "impact_analysis": "需要调整回流焊炉温度设置，预计良率提升2%",
            "verification_status": "已验证",
            "actual_effect": "良率从95%提升至97%"
        },
        {
            "id": 2,
            "change_no": "ECN20251025001",
            "change_type": "工序调整",
            "route_code": "RT002",
            "route_name": "传感器B型快速工艺",
            "from_version": "1.0",
            "to_version": "1.5",
            "change_description": "增加焊后清洗工序，提高产品可靠性",
            "change_reason": "客户要求提高清洁度",
            "initiator": "工艺工程师张三",
            "submit_date": "2024-10-10",
            "approver": "技术总监赵六",
            "approve_date": "2024-10-20",
            "effective_date": "2024-10-25",
            "status": "approved",
            "impact_analysis": "增加一个工序，单件时间增加5分钟，需增加清洗设备",
            "verification_status": "已验证",
            "actual_effect": "客户满意度提升，清洁度达标"
        },
        {
            "id": 3,
            "change_no": "ECN20251103001",
            "change_type": "新工艺开发",
            "route_code": "RT003",
            "route_name": "电源模块C型精密工艺",
            "from_version": None,
            "to_version": "1.0",
            "change_description": "新产品工艺开发",
            "change_reason": "新产品上市",
            "initiator": "工艺工程师王五",
            "submit_date": "2025-11-01",
            "approver": None,
            "approve_date": None,
            "effective_date": None,
            "status": "pending",
            "impact_analysis": "需要采购新设备，培训操作人员",
            "verification_status": "待验证",
            "actual_effect": None
        }
    ]
    
    if status:
        changes = [c for c in changes if c["status"] == status]
    
    return {
        "success": True,
        "total": len(changes),
        "changes": changes[:limit],
        "summary": {
            "pending": len([c for c in changes if c["status"] == "pending"]),
            "approved": len([c for c in changes if c["status"] == "approved"]),
            "rejected": len([c for c in changes if c["status"] == "rejected"])
        }
    }


@router.get("/statistics/summary")
async def get_engineering_summary():
    """获取工艺管理统计摘要"""
    return {
        "success": True,
        "summary": {
            "total_routes": 25,
            "active_routes": 18,
            "draft_routes": 5,
            "obsolete_routes": 2,
            "total_operations": 156,
            "total_parameters": 342,
            "pending_changes": 3,
            "approved_changes_this_month": 8,
            "avg_yield_rate": 0.97,
            "avg_process_time": 45.2
        }
    }


@router.get("/statistics/yield-analysis")
async def get_yield_analysis():
    """获取良率分析"""
    return {
        "success": True,
        "yield_analysis": {
            "overall_yield": 0.97,
            "target_yield": 0.98,
            "by_route": [
                {
                    "route_code": "RT001",
                    "route_name": "智能控制器A型",
                    "target_yield": 0.98,
                    "actual_yield": 0.97,
                    "first_pass_yield": 0.95,
                    "improvement_trend": "+2%"
                },
                {
                    "route_code": "RT002",
                    "route_name": "传感器B型",
                    "target_yield": 0.98,
                    "actual_yield": 0.98,
                    "first_pass_yield": 0.96,
                    "improvement_trend": "+1%"
                }
            ],
            "by_operation": [
                {"operation": "SMT贴片", "yield": 0.99, "defect_rate": 0.01},
                {"operation": "波峰焊接", "yield": 0.98, "defect_rate": 0.02},
                {"operation": "功能测试", "yield": 0.97, "defect_rate": 0.03}
            ],
            "improvement_suggestions": [
                "SMT贴片工序建议加强首件检查",
                "功能测试不良主要来自焊接问题，建议优化焊接参数",
                "建议增加在线AOI检测，及早发现缺陷"
            ]
        }
    }

