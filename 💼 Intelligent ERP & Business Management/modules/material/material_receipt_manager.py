"""
到料管理模块
实现完整的到料接收、检验、入库流程
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ReceiptStatus(Enum):
    """到料状态"""
    PENDING = "pending"  # 待收货
    RECEIVED = "received"  # 已收货
    INSPECTING = "inspecting"  # 检验中
    PASSED = "passed"  # 检验通过
    REJECTED = "rejected"  # 检验不合格
    RETURNED = "returned"  # 已退货
    STORED = "stored"  # 已入库


class InspectionResult(Enum):
    """检验结果"""
    PASS = "pass"  # 合格
    FAIL = "fail"  # 不合格
    CONDITIONAL_PASS = "conditional_pass"  # 让步接收
    PENDING = "pending"  # 待检验


class MaterialReceiptManager:
    """到料管理器"""
    
    def __init__(self):
        """初始化到料管理器"""
        self.receipts = {}
        self.inspections = {}
        self.return_records = {}
        self.receipt_counter = 1000
    
    def create_receipt_notice(
        self,
        po_number: str,
        supplier_id: str,
        expected_date: str,
        items: List[Dict[str, Any]],
        delivery_note: str = ""
    ) -> Dict[str, Any]:
        """
        创建到货通知
        
        Args:
            po_number: 采购订单号
            supplier_id: 供应商ID
            expected_date: 预计到货日期
            items: 物料清单 [{"material_id": "", "quantity": 0, "unit": ""}]
            delivery_note: 送货单号
        
        Returns:
            到货通知信息
        """
        receipt_id = f"RN{datetime.now().strftime('%Y%m%d')}{self.receipt_counter:04d}"
        self.receipt_counter += 1
        
        receipt = {
            "receipt_id": receipt_id,
            "po_number": po_number,
            "supplier_id": supplier_id,
            "expected_date": expected_date,
            "items": items,
            "delivery_note": delivery_note,
            "status": ReceiptStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "actual_arrival_date": None,
            "received_by": None,
            "inspection_results": []
        }
        
        self.receipts[receipt_id] = receipt
        
        return {
            "success": True,
            "receipt_id": receipt_id,
            "message": "到货通知已创建",
            "receipt": receipt
        }
    
    def record_material_arrival(
        self,
        receipt_id: str,
        actual_items: List[Dict[str, Any]],
        received_by: str,
        arrival_date: str,
        truck_number: str = "",
        photos: List[str] = None
    ) -> Dict[str, Any]:
        """
        记录物料到达
        
        Args:
            receipt_id: 到货通知ID
            actual_items: 实际到货物料 [{"material_id": "", "quantity": 0, "package_condition": ""}]
            received_by: 收货人
            arrival_date: 实际到达日期
            truck_number: 车牌号
            photos: 照片列表
        
        Returns:
            到货记录
        """
        if receipt_id not in self.receipts:
            return {"success": False, "error": "到货通知不存在"}
        
        receipt = self.receipts[receipt_id]
        
        # 更新到货信息
        receipt["actual_arrival_date"] = arrival_date
        receipt["received_by"] = received_by
        receipt["actual_items"] = actual_items
        receipt["truck_number"] = truck_number
        receipt["photos"] = photos or []
        receipt["status"] = ReceiptStatus.RECEIVED.value
        receipt["received_at"] = datetime.now().isoformat()
        
        # 对比预期和实际数量
        discrepancies = self._check_quantity_discrepancy(
            receipt["items"],
            actual_items
        )
        
        receipt["discrepancies"] = discrepancies
        
        # 如果有差异，需要处理
        if discrepancies:
            receipt["requires_attention"] = True
        
        return {
            "success": True,
            "message": "物料到达已记录",
            "receipt": receipt,
            "discrepancies": discrepancies
        }
    
    def create_inspection_task(
        self,
        receipt_id: str,
        inspector: str,
        inspection_type: str = "standard",
        sampling_plan: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建检验任务
        
        Args:
            receipt_id: 到货ID
            inspector: 检验员
            inspection_type: 检验类型 (standard/full/sampling)
            sampling_plan: 抽样计划
        
        Returns:
            检验任务信息
        """
        if receipt_id not in self.receipts:
            return {"success": False, "error": "到货记录不存在"}
        
        receipt = self.receipts[receipt_id]
        
        inspection_id = f"INS{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        inspection = {
            "inspection_id": inspection_id,
            "receipt_id": receipt_id,
            "inspector": inspector,
            "inspection_type": inspection_type,
            "sampling_plan": sampling_plan or {},
            "status": InspectionResult.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "inspection_items": [],
            "overall_result": None,
            "remarks": ""
        }
        
        self.inspections[inspection_id] = inspection
        receipt["status"] = ReceiptStatus.INSPECTING.value
        
        return {
            "success": True,
            "inspection_id": inspection_id,
            "message": "检验任务已创建",
            "inspection": inspection
        }
    
    def record_inspection_result(
        self,
        inspection_id: str,
        inspection_items: List[Dict[str, Any]],
        overall_result: str,
        defect_description: str = "",
        photos: List[str] = None
    ) -> Dict[str, Any]:
        """
        记录检验结果
        
        Args:
            inspection_id: 检验任务ID
            inspection_items: 检验项目 [{"item": "", "standard": "", "actual": "", "result": "pass/fail"}]
            overall_result: 总体结果 (pass/fail/conditional_pass)
            defect_description: 缺陷描述
            photos: 检验照片
        
        Returns:
            检验结果
        """
        if inspection_id not in self.inspections:
            return {"success": False, "error": "检验任务不存在"}
        
        inspection = self.inspections[inspection_id]
        receipt = self.receipts[inspection["receipt_id"]]
        
        # 更新检验记录
        inspection["inspection_items"] = inspection_items
        inspection["overall_result"] = overall_result
        inspection["defect_description"] = defect_description
        inspection["photos"] = photos or []
        inspection["completed_at"] = datetime.now().isoformat()
        inspection["status"] = overall_result
        
        # 更新到货状态
        if overall_result == InspectionResult.PASS.value:
            receipt["status"] = ReceiptStatus.PASSED.value
        elif overall_result == InspectionResult.FAIL.value:
            receipt["status"] = ReceiptStatus.REJECTED.value
        elif overall_result == InspectionResult.CONDITIONAL_PASS.value:
            receipt["status"] = ReceiptStatus.PASSED.value
            receipt["conditional_acceptance"] = True
        
        receipt["inspection_results"].append(inspection)
        
        return {
            "success": True,
            "message": "检验结果已记录",
            "inspection": inspection,
            "receipt_status": receipt["status"]
        }
    
    def process_rejected_material(
        self,
        receipt_id: str,
        action: str,
        handler: str,
        reason: str,
        replacement_expected: bool = False
    ) -> Dict[str, Any]:
        """
        处理不合格物料
        
        Args:
            receipt_id: 到货ID
            action: 处理措施 (return/scrap/rework)
            handler: 处理人
            reason: 处理原因
            replacement_expected: 是否期待替换
        
        Returns:
            处理记录
        """
        if receipt_id not in self.receipts:
            return {"success": False, "error": "到货记录不存在"}
        
        receipt = self.receipts[receipt_id]
        
        if receipt["status"] != ReceiptStatus.REJECTED.value:
            return {"success": False, "error": "物料未被标记为不合格"}
        
        return_id = f"RET{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return_record = {
            "return_id": return_id,
            "receipt_id": receipt_id,
            "po_number": receipt["po_number"],
            "supplier_id": receipt["supplier_id"],
            "action": action,
            "handler": handler,
            "reason": reason,
            "replacement_expected": replacement_expected,
            "created_at": datetime.now().isoformat(),
            "completed": False
        }
        
        self.return_records[return_id] = return_record
        receipt["status"] = ReceiptStatus.RETURNED.value
        receipt["return_record"] = return_id
        
        return {
            "success": True,
            "message": f"不合格物料处理已记录: {action}",
            "return_record": return_record
        }
    
    def move_to_storage(
        self,
        receipt_id: str,
        storage_locations: List[Dict[str, Any]],
        moved_by: str
    ) -> Dict[str, Any]:
        """
        移至仓库
        
        Args:
            receipt_id: 到货ID
            storage_locations: 存储位置 [{"material_id": "", "location": "", "quantity": 0}]
            moved_by: 移库人
        
        Returns:
            入库记录
        """
        if receipt_id not in self.receipts:
            return {"success": False, "error": "到货记录不存在"}
        
        receipt = self.receipts[receipt_id]
        
        if receipt["status"] != ReceiptStatus.PASSED.value:
            return {"success": False, "error": "物料未通过检验，无法入库"}
        
        # 更新状态
        receipt["status"] = ReceiptStatus.STORED.value
        receipt["storage_locations"] = storage_locations
        receipt["moved_by"] = moved_by
        receipt["stored_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "物料已入库",
            "receipt": receipt,
            "storage_locations": storage_locations
        }
    
    def get_receipt_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取到料统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计报告
        """
        # 筛选时间范围内的到货
        receipts_in_range = [
            receipt for receipt in self.receipts.values()
            if start_date <= receipt["created_at"][:10] <= end_date
        ]
        
        total_receipts = len(receipts_in_range)
        
        # 按状态统计
        by_status = {}
        for receipt in receipts_in_range:
            status = receipt["status"]
            by_status[status] = by_status.get(status, 0) + 1
        
        # 检验合格率
        inspected = sum(
            1 for receipt in receipts_in_range
            if receipt["status"] in [ReceiptStatus.PASSED.value, ReceiptStatus.REJECTED.value]
        )
        
        passed = sum(
            1 for receipt in receipts_in_range
            if receipt["status"] == ReceiptStatus.PASSED.value
        )
        
        pass_rate = (passed / inspected * 100) if inspected > 0 else 0
        
        # 准时到货率
        on_time = sum(
            1 for receipt in receipts_in_range
            if receipt.get("actual_arrival_date")
            and receipt["actual_arrival_date"] <= receipt["expected_date"]
        )
        
        with_arrival = sum(
            1 for receipt in receipts_in_range
            if receipt.get("actual_arrival_date")
        )
        
        on_time_rate = (on_time / with_arrival * 100) if with_arrival > 0 else 0
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_receipts": total_receipts,
                "inspected": inspected,
                "passed": passed,
                "rejected": by_status.get(ReceiptStatus.REJECTED.value, 0)
            },
            "by_status": by_status,
            "performance": {
                "inspection_pass_rate": round(pass_rate, 2),
                "on_time_arrival_rate": round(on_time_rate, 2)
            }
        }
    
    def _check_quantity_discrepancy(
        self,
        expected_items: List[Dict[str, Any]],
        actual_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        检查数量差异
        
        Args:
            expected_items: 预期物料
            actual_items: 实际物料
        
        Returns:
            差异列表
        """
        discrepancies = []
        
        # 创建实际数量字典
        actual_dict = {
            item["material_id"]: item["quantity"]
            for item in actual_items
        }
        
        for expected in expected_items:
            material_id = expected["material_id"]
            expected_qty = expected["quantity"]
            actual_qty = actual_dict.get(material_id, 0)
            
            if actual_qty != expected_qty:
                discrepancies.append({
                    "material_id": material_id,
                    "expected_quantity": expected_qty,
                    "actual_quantity": actual_qty,
                    "difference": actual_qty - expected_qty,
                    "variance_percentage": ((actual_qty - expected_qty) / expected_qty * 100) if expected_qty > 0 else 0
                })
        
        return discrepancies


# 创建默认实例
default_receipt_manager = MaterialReceiptManager()

