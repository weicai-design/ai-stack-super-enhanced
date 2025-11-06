"""
ERP集成API
整合所有ERP子模块的统一API接口
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入所有子模块管理器
from modules.customer.customer_manager import default_customer_manager
from modules.order.order_manager import default_order_manager
from modules.production.production_manager import default_production_manager
from modules.quality.quality_manager import default_quality_manager
from modules.project.project_manager import default_project_manager
from modules.procurement.procurement_manager import default_procurement_manager
from modules.material.material_receipt_manager import default_receipt_manager
from modules.material.material_inventory_manager import default_inventory_manager
from modules.warehouse.warehouse_manager import default_warehouse_manager
from modules.delivery.delivery_manager import default_delivery_manager
from modules.shipping.shipping_manager import default_shipping_manager
from modules.equipment.equipment_manager import default_equipment_manager
from modules.process.process_manager import default_process_manager
from monitoring.closed_loop_monitor import closed_loop_monitor


router = APIRouter(prefix="/api/erp", tags=["ERP集成"])


# ==================== 采购管理API ====================

@router.post("/procurement/request/create")
async def create_purchase_request(data: Dict[str, Any]):
    """创建采购申请"""
    try:
        return default_procurement_manager.create_purchase_request(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/procurement/request/approve")
async def approve_purchase_request(data: Dict[str, Any]):
    """审批采购申请"""
    try:
        return default_procurement_manager.approve_purchase_request(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/procurement/order/create")
async def create_procurement_order(data: Dict[str, Any]):
    """创建采购订单"""
    try:
        return default_procurement_manager.create_procurement_order(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/procurement/analysis")
async def get_procurement_analysis(start_date: str, end_date: str):
    """获取采购分析"""
    try:
        return default_procurement_manager.get_procurement_analysis(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 到料管理API ====================

@router.post("/receipt/notice/create")
async def create_receipt_notice(data: Dict[str, Any]):
    """创建到货通知"""
    try:
        return default_receipt_manager.create_receipt_notice(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt/arrival/record")
async def record_material_arrival(data: Dict[str, Any]):
    """记录物料到达"""
    try:
        return default_receipt_manager.record_material_arrival(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt/inspection/create")
async def create_inspection_task(data: Dict[str, Any]):
    """创建检验任务"""
    try:
        return default_receipt_manager.create_inspection_task(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt/inspection/result")
async def record_inspection_result(data: Dict[str, Any]):
    """记录检验结果"""
    try:
        return default_receipt_manager.record_inspection_result(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 物料管理API ====================

@router.post("/material/create")
async def create_material(data: Dict[str, Any]):
    """创建物料"""
    try:
        return default_inventory_manager.create_material(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material/movement")
async def record_stock_movement(data: Dict[str, Any]):
    """记录库存变动"""
    try:
        return default_inventory_manager.record_stock_movement(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/material/inventory/status")
async def get_inventory_status(material_id: Optional[str] = None):
    """获取库存状态"""
    try:
        return default_inventory_manager.get_inventory_status(material_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material/reserve")
async def reserve_stock(data: Dict[str, Any]):
    """预留库存"""
    try:
        return default_inventory_manager.reserve_stock(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 仓储管理API ====================

@router.post("/warehouse/create")
async def create_warehouse(data: Dict[str, Any]):
    """创建仓库"""
    try:
        return default_warehouse_manager.create_warehouse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warehouse/location/create")
async def create_storage_location(data: Dict[str, Any]):
    """创建库位"""
    try:
        return default_warehouse_manager.create_storage_location(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warehouse/putaway/create")
async def create_putaway_task(data: Dict[str, Any]):
    """创建上架任务"""
    try:
        return default_warehouse_manager.create_putaway_task(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warehouse/picking/create")
async def create_picking_task(data: Dict[str, Any]):
    """创建拣货任务"""
    try:
        return default_warehouse_manager.create_picking_task(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 交付管理API ====================

@router.post("/delivery/plan/create")
async def create_delivery_plan(data: Dict[str, Any]):
    """创建交付计划"""
    try:
        return default_delivery_manager.create_delivery_plan(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delivery/plan/confirm")
async def confirm_delivery_plan(data: Dict[str, Any]):
    """确认交付计划"""
    try:
        return default_delivery_manager.confirm_delivery_plan(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delivery/performance")
async def get_delivery_performance(start_date: str, end_date: str):
    """获取交付绩效"""
    try:
        return default_delivery_manager.get_delivery_performance(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 发运管理API ====================

@router.post("/shipping/plan/create")
async def create_shipment_plan(data: Dict[str, Any]):
    """创建发运计划"""
    try:
        return default_shipping_manager.create_shipment_plan(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shipping/schedule")
async def schedule_shipment(data: Dict[str, Any]):
    """排程发运"""
    try:
        return default_shipping_manager.schedule_shipment(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shipping/statistics")
async def get_shipment_statistics(start_date: str, end_date: str):
    """获取发运统计"""
    try:
        return default_shipping_manager.get_shipment_statistics(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 设备管理API ====================

@router.post("/equipment/register")
async def register_equipment(data: Dict[str, Any]):
    """登记设备"""
    try:
        return default_equipment_manager.register_equipment(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/equipment/maintenance/plan")
async def create_maintenance_plan(data: Dict[str, Any]):
    """创建维护计划"""
    try:
        return default_equipment_manager.create_maintenance_plan(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment/health/{equipment_id}")
async def get_equipment_health(equipment_id: str):
    """获取设备健康度"""
    try:
        return default_equipment_manager.get_equipment_health(equipment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment/maintenance/due")
async def get_maintenance_due_list(days_ahead: int = 7):
    """获取待维护设备"""
    try:
        return default_equipment_manager.get_maintenance_due_list(days_ahead)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工艺管理API ====================

@router.post("/process/route/create")
async def create_process_route(data: Dict[str, Any]):
    """创建工艺路线"""
    try:
        return default_process_manager.create_process_route(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/step/add")
async def add_process_step(data: Dict[str, Any]):
    """添加工艺步骤"""
    try:
        return default_process_manager.add_process_step(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/process/route/{route_id}")
async def get_process_route_details(route_id: str):
    """获取工艺路线详情"""
    try:
        return default_process_manager.get_process_route_details(route_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 闭环监控API ====================

@router.post("/monitoring/issue/detect")
async def detect_issue(data: Dict[str, Any]):
    """检测问题"""
    try:
        return closed_loop_monitor.detect_issue(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/improvement/create")
async def create_improvement(data: Dict[str, Any]):
    """创建改进措施"""
    try:
        return closed_loop_monitor.create_improvement(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/improvement/progress")
async def update_improvement_progress(data: Dict[str, Any]):
    """更新改进进度"""
    try:
        return closed_loop_monitor.update_improvement_progress(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """获取监控看板"""
    try:
        return closed_loop_monitor.get_monitoring_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/verify")
async def verify_improvement(data: Dict[str, Any]):
    """验证改进效果"""
    try:
        return closed_loop_monitor.verify_improvement(
            data.get("issue_id"),
            data.get("verification_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/report")
async def generate_closed_loop_report(start_date: str, end_date: str):
    """生成闭环监控报告"""
    try:
        return closed_loop_monitor.generate_closed_loop_report(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合查询API ====================

@router.get("/dashboard/overview")
async def get_erp_overview():
    """获取ERP总览"""
    try:
        # 获取各模块关键指标
        overview = {
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "customer": {
                    "total_customers": len(default_customer_manager.customers),
                    "active_customers": sum(1 for c in default_customer_manager.customers.values() if c.get("active", True))
                },
                "order": {
                    "total_orders": len(default_order_manager.orders),
                    "pending_orders": sum(1 for o in default_order_manager.orders.values() if o.get("status") == "pending")
                },
                "procurement": {
                    "total_orders": len(default_procurement_manager.procurement_orders),
                    "pending_approval": sum(1 for r in default_procurement_manager.purchase_requests.values() if r.get("status") == "pending")
                },
                "inventory": {
                    "total_materials": len(default_inventory_manager.materials),
                    "low_stock_alerts": 0  # 需要计算
                },
                "warehouse": {
                    "total_warehouses": len(default_warehouse_manager.warehouses),
                    "total_locations": len(default_warehouse_manager.locations)
                },
                "equipment": {
                    "total_equipments": len(default_equipment_manager.equipments),
                    "maintenance_due": 0  # 需要计算
                },
                "monitoring": {
                    "total_issues": len(closed_loop_monitor.issues),
                    "active_issues": sum(1 for i in closed_loop_monitor.issues if i.get("status") != "已闭环")
                }
            }
        }
        
        return {"success": True, "overview": overview}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/kpi")
async def get_erp_kpi():
    """获取ERP关键指标"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        kpi = {
            "delivery_performance": default_delivery_manager.get_delivery_performance(
                last_month, today
            ),
            "procurement_performance": default_procurement_manager.get_procurement_analysis(
                last_month, today
            ),
            "equipment_statistics": default_equipment_manager.get_equipment_statistics(
                last_month, today
            ),
            "monitoring_health": closed_loop_monitor.get_monitoring_dashboard()
        }
        
        return {"success": True, "kpi": kpi}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

