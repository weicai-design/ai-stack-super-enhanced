#!/usr/bin/env python3
"""
到料管理系统
Receiving Management System

功能：
- 到料通知管理
- 收货检验
- 到料登记
- 质量检验
- 入库管理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ReceivingStatus(Enum):
    """收货状态"""
    SCHEDULED = "scheduled"  # 已排期
    IN_TRANSIT = "in_transit"  # 在途
    ARRIVED = "arrived"  # 已到达
    INSPECTING = "inspecting"  # 检验中
    ACCEPTED = "accepted"  # 合格入库
    REJECTED = "rejected"  # 拒收
    PARTIAL_ACCEPTED = "partial_accepted"  # 部分合格


class QualityStatus(Enum):
    """质量状态"""
    PENDING = "pending"  # 待检
    PASS = "pass"  # 合格
    FAIL = "fail"  # 不合格
    CONDITIONAL_PASS = "conditional_pass"  # 让步接收


class ReceivingManager:
    """到料管理器"""
    
    def __init__(self):
        """初始化到料管理器"""
        self.receiving_notices: Dict[str, Dict[str, Any]] = {}
        self.receiving_records: Dict[str, Dict[str, Any]] = {}
        self.inspection_records: Dict[str, Dict[str, Any]] = {}
        
    # ==================== 到料通知管理 ====================
    
    def create_receiving_notice(
        self,
        notice_id: str,
        purchase_order_id: str,
        supplier_id: str,
        material_id: str,
        material_name: str,
        quantity: float,
        unit: str,
        scheduled_date: str,
        delivery_method: str = "truck",
        contact_person: str = "",
        contact_phone: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建到料通知
        
        Args:
            notice_id: 通知单号
            purchase_order_id: 采购订单号
            supplier_id: 供应商ID
            material_id: 物料编号
            material_name: 物料名称
            quantity: 数量
            unit: 单位
            scheduled_date: 预计到货日期
            delivery_method: 送货方式
            contact_person: 联系人
            contact_phone: 联系电话
            notes: 备注
        
        Returns:
            到料通知信息
        """
        notice = {
            "notice_id": notice_id,
            "purchase_order_id": purchase_order_id,
            "supplier_id": supplier_id,
            "material_id": material_id,
            "material_name": material_name,
            "quantity": quantity,
            "unit": unit,
            "scheduled_date": scheduled_date,
            "delivery_method": delivery_method,
            "contact_person": contact_person,
            "contact_phone": contact_phone,
            "notes": notes,
            "status": ReceivingStatus.SCHEDULED.value,
            "created_at": datetime.now().isoformat(),
            "actual_arrival_date": None,
            "actual_quantity": 0,
            "receiving_record_id": None
        }
        
        self.receiving_notices[notice_id] = notice
        return notice
    
    def update_receiving_status(
        self,
        notice_id: str,
        status: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        更新到料状态
        
        Args:
            notice_id: 通知单号
            status: 新状态
            notes: 备注
        
        Returns:
            更新后的通知信息
        """
        if notice_id not in self.receiving_notices:
            raise ValueError(f"到料通知 {notice_id} 不存在")
        
        notice = self.receiving_notices[notice_id]
        notice["status"] = status
        notice["updated_at"] = datetime.now().isoformat()
        
        if notes:
            if "status_history" not in notice:
                notice["status_history"] = []
            notice["status_history"].append({
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "notes": notes
            })
        
        return notice
    
    # ==================== 收货登记 ====================
    
    def register_receiving(
        self,
        record_id: str,
        notice_id: str,
        actual_quantity: float,
        actual_arrival_date: Optional[str] = None,
        delivery_note_no: str = "",
        receiver: str = "system",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        登记收货
        
        Args:
            record_id: 收货记录ID
            notice_id: 到料通知单号
            actual_quantity: 实际到货数量
            actual_arrival_date: 实际到货日期
            delivery_note_no: 送货单号
            receiver: 收货人
            notes: 备注
        
        Returns:
            收货记录
        """
        if notice_id not in self.receiving_notices:
            raise ValueError(f"到料通知 {notice_id} 不存在")
        
        notice = self.receiving_notices[notice_id]
        
        if actual_arrival_date is None:
            actual_arrival_date = datetime.now().isoformat()
        
        record = {
            "record_id": record_id,
            "notice_id": notice_id,
            "purchase_order_id": notice["purchase_order_id"],
            "supplier_id": notice["supplier_id"],
            "material_id": notice["material_id"],
            "material_name": notice["material_name"],
            "planned_quantity": notice["quantity"],
            "actual_quantity": actual_quantity,
            "unit": notice["unit"],
            "scheduled_date": notice["scheduled_date"],
            "actual_arrival_date": actual_arrival_date,
            "delivery_note_no": delivery_note_no,
            "receiver": receiver,
            "notes": notes,
            "status": ReceivingStatus.ARRIVED.value,
            "quality_status": QualityStatus.PENDING.value,
            "accepted_quantity": 0,
            "rejected_quantity": 0,
            "created_at": datetime.now().isoformat()
        }
        
        self.receiving_records[record_id] = record
        
        # 更新通知状态
        notice["status"] = ReceivingStatus.ARRIVED.value
        notice["actual_arrival_date"] = actual_arrival_date
        notice["actual_quantity"] = actual_quantity
        notice["receiving_record_id"] = record_id
        
        # 计算到货及时率
        scheduled_dt = datetime.fromisoformat(notice["scheduled_date"])
        actual_dt = datetime.fromisoformat(actual_arrival_date)
        
        if actual_dt <= scheduled_dt:
            record["on_time"] = True
            record["delay_days"] = 0
        else:
            record["on_time"] = False
            record["delay_days"] = (actual_dt - scheduled_dt).days
        
        return record
    
    # ==================== 质量检验 ====================
    
    def create_inspection(
        self,
        inspection_id: str,
        receiving_record_id: str,
        inspector: str,
        inspection_items: List[Dict[str, Any]],
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        创建质量检验
        
        Args:
            inspection_id: 检验单号
            receiving_record_id: 收货记录ID
            inspector: 检验员
            inspection_items: 检验项目列表
            notes: 备注
        
        Returns:
            检验记录
        """
        if receiving_record_id not in self.receiving_records:
            raise ValueError(f"收货记录 {receiving_record_id} 不存在")
        
        record = self.receiving_records[receiving_record_id]
        
        inspection = {
            "inspection_id": inspection_id,
            "receiving_record_id": receiving_record_id,
            "material_id": record["material_id"],
            "material_name": record["material_name"],
            "quantity": record["actual_quantity"],
            "inspector": inspector,
            "inspection_items": inspection_items,
            "notes": notes,
            "status": "in_progress",
            "overall_result": QualityStatus.PENDING.value,
            "started_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.inspection_records[inspection_id] = inspection
        
        # 更新收货记录状态
        record["status"] = ReceivingStatus.INSPECTING.value
        record["inspection_id"] = inspection_id
        
        return inspection
    
    def complete_inspection(
        self,
        inspection_id: str,
        inspection_results: List[Dict[str, Any]],
        overall_result: str,
        accepted_quantity: float,
        rejected_quantity: float,
        defect_description: str = "",
        photos: List[str] = None
    ) -> Dict[str, Any]:
        """
        完成质量检验
        
        Args:
            inspection_id: 检验单号
            inspection_results: 检验结果列表
            overall_result: 总体结论（pass/fail/conditional_pass）
            accepted_quantity: 合格数量
            rejected_quantity: 不合格数量
            defect_description: 缺陷描述
            photos: 照片URL列表
        
        Returns:
            更新后的检验记录
        """
        if inspection_id not in self.inspection_records:
            raise ValueError(f"检验记录 {inspection_id} 不存在")
        
        inspection = self.inspection_records[inspection_id]
        
        inspection["inspection_results"] = inspection_results
        inspection["overall_result"] = overall_result
        inspection["accepted_quantity"] = accepted_quantity
        inspection["rejected_quantity"] = rejected_quantity
        inspection["defect_description"] = defect_description
        inspection["photos"] = photos or []
        inspection["status"] = "completed"
        inspection["completed_at"] = datetime.now().isoformat()
        
        # 更新收货记录
        record_id = inspection["receiving_record_id"]
        record = self.receiving_records[record_id]
        
        record["quality_status"] = overall_result
        record["accepted_quantity"] = accepted_quantity
        record["rejected_quantity"] = rejected_quantity
        
        if overall_result == QualityStatus.PASS.value:
            record["status"] = ReceivingStatus.ACCEPTED.value
        elif overall_result == QualityStatus.FAIL.value:
            record["status"] = ReceivingStatus.REJECTED.value
        elif overall_result == QualityStatus.CONDITIONAL_PASS.value:
            record["status"] = ReceivingStatus.PARTIAL_ACCEPTED.value
        
        return inspection
    
    # ==================== 入库管理 ====================
    
    def process_warehousing(
        self,
        receiving_record_id: str,
        warehouse_location: str,
        batch_no: str = "",
        operator: str = "system"
    ) -> Dict[str, Any]:
        """
        处理入库
        
        Args:
            receiving_record_id: 收货记录ID
            warehouse_location: 仓库位置
            batch_no: 批次号
            operator: 操作员
        
        Returns:
            入库结果
        """
        if receiving_record_id not in self.receiving_records:
            raise ValueError(f"收货记录 {receiving_record_id} 不存在")
        
        record = self.receiving_records[receiving_record_id]
        
        if record["quality_status"] not in [
            QualityStatus.PASS.value,
            QualityStatus.CONDITIONAL_PASS.value
        ]:
            raise ValueError("只有质量合格的物料才能入库")
        
        warehousing = {
            "warehousing_id": f"WH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "receiving_record_id": receiving_record_id,
            "material_id": record["material_id"],
            "material_name": record["material_name"],
            "quantity": record["accepted_quantity"],
            "unit": record["unit"],
            "warehouse_location": warehouse_location,
            "batch_no": batch_no,
            "operator": operator,
            "warehoused_at": datetime.now().isoformat()
        }
        
        # 更新收货记录
        if "warehousing_records" not in record:
            record["warehousing_records"] = []
        record["warehousing_records"].append(warehousing)
        
        return warehousing
    
    # ==================== 查询和分析 ====================
    
    def get_receiving_notices(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取到料通知列表
        
        Args:
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            到料通知列表
        """
        notices = list(self.receiving_notices.values())
        
        if status:
            notices = [n for n in notices if n["status"] == status]
        
        if start_date:
            notices = [n for n in notices if n["scheduled_date"] >= start_date]
        
        if end_date:
            notices = [n for n in notices if n["scheduled_date"] <= end_date]
        
        # 按预计到货日期排序
        notices.sort(key=lambda x: x["scheduled_date"])
        
        return notices
    
    def get_receiving_records(
        self,
        material_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取收货记录列表
        
        Args:
            material_id: 物料编号
            supplier_id: 供应商ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            收货记录列表
        """
        records = list(self.receiving_records.values())
        
        if material_id:
            records = [r for r in records if r["material_id"] == material_id]
        
        if supplier_id:
            records = [r for r in records if r["supplier_id"] == supplier_id]
        
        if start_date:
            records = [r for r in records if r["actual_arrival_date"] >= start_date]
        
        if end_date:
            records = [r for r in records if r["actual_arrival_date"] <= end_date]
        
        # 按到货日期倒序
        records.sort(key=lambda x: x["actual_arrival_date"], reverse=True)
        
        return records
    
    def analyze_receiving_performance(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        到料绩效分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            绩效分析结果
        """
        # 筛选期间内的收货记录
        records = self.get_receiving_records(start_date=start_date, end_date=end_date)
        
        if not records:
            return {
                "period": {"start": start_date, "end": end_date},
                "total_records": 0,
                "message": "该期间内没有收货记录"
            }
        
        # 统计
        total_records = len(records)
        on_time_count = sum(1 for r in records if r.get("on_time", False))
        
        # 质量统计
        quality_stats = {
            "pass": 0,
            "fail": 0,
            "conditional_pass": 0,
            "pending": 0
        }
        
        for record in records:
            status = record.get("quality_status", QualityStatus.PENDING.value)
            if status == QualityStatus.PASS.value:
                quality_stats["pass"] += 1
            elif status == QualityStatus.FAIL.value:
                quality_stats["fail"] += 1
            elif status == QualityStatus.CONDITIONAL_PASS.value:
                quality_stats["conditional_pass"] += 1
            else:
                quality_stats["pending"] += 1
        
        # 按供应商统计
        supplier_stats = {}
        for record in records:
            supplier_id = record["supplier_id"]
            if supplier_id not in supplier_stats:
                supplier_stats[supplier_id] = {
                    "total": 0,
                    "on_time": 0,
                    "quality_pass": 0,
                    "total_quantity": 0,
                    "accepted_quantity": 0
                }
            
            supplier_stats[supplier_id]["total"] += 1
            supplier_stats[supplier_id]["total_quantity"] += record["actual_quantity"]
            supplier_stats[supplier_id]["accepted_quantity"] += record.get("accepted_quantity", 0)
            
            if record.get("on_time", False):
                supplier_stats[supplier_id]["on_time"] += 1
            
            if record.get("quality_status") == QualityStatus.PASS.value:
                supplier_stats[supplier_id]["quality_pass"] += 1
        
        # 计算供应商绩效
        for supplier_id, stats in supplier_stats.items():
            stats["on_time_rate"] = (stats["on_time"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            stats["quality_pass_rate"] = (stats["quality_pass"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_records": total_records,
                "on_time_count": on_time_count,
                "on_time_rate": (on_time_count / total_records) * 100 if total_records > 0 else 0,
                "quality_stats": quality_stats,
                "quality_pass_rate": (quality_stats["pass"] / total_records) * 100 if total_records > 0 else 0
            },
            "by_supplier": supplier_stats
        }


# 创建全局实例
default_receiving_manager = ReceivingManager()

