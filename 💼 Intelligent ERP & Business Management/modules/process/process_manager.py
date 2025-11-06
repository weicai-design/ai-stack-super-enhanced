"""
工艺管理模块
实现完整的工艺路线、工艺参数、工艺变更管理功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ProcessStatus(Enum):
    """工艺状态"""
    DRAFT = "draft"  # 草稿
    REVIEW = "review"  # 评审中
    APPROVED = "approved"  # 已批准
    ACTIVE = "active"  # 生效中
    OBSOLETE = "obsolete"  # 已废弃


class ChangeType(Enum):
    """变更类型"""
    PARAMETER = "parameter"  # 参数变更
    OPERATION = "operation"  # 工序变更
    EQUIPMENT = "equipment"  # 设备变更
    MATERIAL = "material"  # 材料变更
    QUALITY = "quality"  # 质量标准变更


class ProcessManager:
    """工艺管理器"""
    
    def __init__(self):
        """初始化工艺管理器"""
        self.process_routes = {}
        self.operations = {}
        self.process_parameters = {}
        self.change_requests = []
        self.work_instructions = {}
        self.bom_structures = {}
    
    def create_process_route(
        self,
        route_id: str,
        product_id: str,
        version: str,
        operations: List[Dict[str, Any]],
        created_by: str
    ) -> Dict[str, Any]:
        """
        创建工艺路线
        
        Args:
            route_id: 路线ID
            product_id: 产品ID
            version: 版本号
            operations: 工序列表 [{"op_id": "", "sequence": 0, "description": ""}]
            created_by: 创建人
        
        Returns:
            工艺路线信息
        """
        route = {
            "route_id": route_id,
            "product_id": product_id,
            "version": version,
            "operations": operations,
            "status": ProcessStatus.DRAFT.value,
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "approved_by": None,
            "approved_at": None,
            "effective_date": None
        }
        
        self.process_routes[route_id] = route
        
        return {
            "success": True,
            "route_id": route_id,
            "message": "工艺路线已创建",
            "route": route
        }
    
    def create_operation(
        self,
        operation_id: str,
        name: str,
        description: str,
        equipment_required: str,
        standard_time_minutes: float,
        quality_standards: List[Dict[str, Any]],
        safety_requirements: List[str] = None
    ) -> Dict[str, Any]:
        """
        创建工序
        
        Args:
            operation_id: 工序ID
            name: 工序名称
            description: 工序描述
            equipment_required: 所需设备
            standard_time_minutes: 标准工时（分钟）
            quality_standards: 质量标准 [{"item": "", "specification": "", "tolerance": ""}]
            safety_requirements: 安全要求
        
        Returns:
            工序信息
        """
        operation = {
            "operation_id": operation_id,
            "name": name,
            "description": description,
            "equipment_required": equipment_required,
            "standard_time_minutes": standard_time_minutes,
            "quality_standards": quality_standards,
            "safety_requirements": safety_requirements or [],
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        self.operations[operation_id] = operation
        
        return {
            "success": True,
            "operation_id": operation_id,
            "message": "工序已创建",
            "operation": operation
        }
    
    def define_process_parameters(
        self,
        route_id: str,
        operation_id: str,
        parameters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        定义工艺参数
        
        Args:
            route_id: 路线ID
            operation_id: 工序ID
            parameters: 参数列表 [{"name": "", "value": 0, "unit": "", "tolerance": ""}]
        
        Returns:
            参数定义信息
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        param_id = f"PP{route_id}{operation_id}"
        
        param_def = {
            "param_id": param_id,
            "route_id": route_id,
            "operation_id": operation_id,
            "parameters": parameters,
            "defined_at": datetime.now().isoformat(),
            "version": 1
        }
        
        self.process_parameters[param_id] = param_def
        
        return {
            "success": True,
            "param_id": param_id,
            "message": "工艺参数已定义",
            "parameters": param_def
        }
    
    def approve_process_route(
        self,
        route_id: str,
        approver: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """
        批准工艺路线
        
        Args:
            route_id: 路线ID
            approver: 批准人
            effective_date: 生效日期
        
        Returns:
            批准结果
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        route["status"] = ProcessStatus.APPROVED.value
        route["approved_by"] = approver
        route["approved_at"] = datetime.now().isoformat()
        route["effective_date"] = effective_date
        
        # 如果生效日期是今天或之前，立即激活
        if effective_date <= datetime.now().isoformat()[:10]:
            route["status"] = ProcessStatus.ACTIVE.value
        
        return {
            "success": True,
            "message": "工艺路线已批准",
            "route": route
        }
    
    def create_change_request(
        self,
        route_id: str,
        change_type: str,
        change_description: str,
        reason: str,
        requestor: str,
        proposed_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建变更请求
        
        Args:
            route_id: 路线ID
            change_type: 变更类型
            change_description: 变更描述
            reason: 变更原因
            requestor: 申请人
            proposed_changes: 拟议变更内容
        
        Returns:
            变更请求信息
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        change_id = f"CR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        change_request = {
            "change_id": change_id,
            "route_id": route_id,
            "change_type": change_type,
            "change_description": change_description,
            "reason": reason,
            "requestor": requestor,
            "proposed_changes": proposed_changes,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "reviewed_by": None,
            "review_decision": None,
            "implemented_at": None
        }
        
        self.change_requests.append(change_request)
        
        return {
            "success": True,
            "change_id": change_id,
            "message": "变更请求已创建",
            "change_request": change_request
        }
    
    def review_change_request(
        self,
        change_id: str,
        reviewer: str,
        decision: str,
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        评审变更请求
        
        Args:
            change_id: 变更ID
            reviewer: 评审人
            decision: 决定 (approved/rejected)
            comments: 评审意见
        
        Returns:
            评审结果
        """
        change_request = next((cr for cr in self.change_requests if cr["change_id"] == change_id), None)
        
        if not change_request:
            return {"success": False, "error": "变更请求不存在"}
        
        change_request["reviewed_by"] = reviewer
        change_request["review_decision"] = decision
        change_request["review_comments"] = comments
        change_request["reviewed_at"] = datetime.now().isoformat()
        
        if decision == "approved":
            change_request["status"] = "approved"
            # 实施变更
            self._implement_change(change_request)
        else:
            change_request["status"] = "rejected"
        
        return {
            "success": True,
            "message": f"变更请求已{decision}",
            "change_request": change_request
        }
    
    def _implement_change(self, change_request: Dict[str, Any]):
        """实施变更"""
        route_id = change_request["route_id"]
        route = self.process_routes.get(route_id)
        
        if not route:
            return
        
        # 根据变更类型实施变更
        change_type = change_request["change_type"]
        proposed_changes = change_request["proposed_changes"]
        
        if change_type == ChangeType.PARAMETER.value:
            # 更新参数
            for param_id, param_def in self.process_parameters.items():
                if param_def["route_id"] == route_id:
                    param_def["parameters"] = proposed_changes.get("parameters", param_def["parameters"])
                    param_def["version"] += 1
        
        elif change_type == ChangeType.OPERATION.value:
            # 更新工序
            route["operations"] = proposed_changes.get("operations", route["operations"])
        
        # 更新路线版本
        current_version = route["version"]
        route["version"] = f"{current_version}.1"
        
        change_request["implemented_at"] = datetime.now().isoformat()
        change_request["status"] = "implemented"
    
    def create_work_instruction(
        self,
        instruction_id: str,
        operation_id: str,
        title: str,
        steps: List[Dict[str, Any]],
        photos: List[str] = None,
        videos: List[str] = None
    ) -> Dict[str, Any]:
        """
        创建作业指导书
        
        Args:
            instruction_id: 指导书ID
            operation_id: 工序ID
            title: 标题
            steps: 步骤列表 [{"step": 1, "description": "", "key_points": []}]
            photos: 图片列表
            videos: 视频列表
        
        Returns:
            作业指导书信息
        """
        if operation_id not in self.operations:
            return {"success": False, "error": "工序不存在"}
        
        instruction = {
            "instruction_id": instruction_id,
            "operation_id": operation_id,
            "title": title,
            "steps": steps,
            "photos": photos or [],
            "videos": videos or [],
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.work_instructions[instruction_id] = instruction
        
        return {
            "success": True,
            "instruction_id": instruction_id,
            "message": "作业指导书已创建",
            "instruction": instruction
        }
    
    def create_bom(
        self,
        bom_id: str,
        product_id: str,
        materials: List[Dict[str, Any]],
        version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        创建物料清单(BOM)
        
        Args:
            bom_id: BOM ID
            product_id: 产品ID
            materials: 物料列表 [{"material_id": "", "quantity": 0, "unit": "", "level": 0}]
            version: 版本
        
        Returns:
            BOM信息
        """
        bom = {
            "bom_id": bom_id,
            "product_id": product_id,
            "materials": materials,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.bom_structures[bom_id] = bom
        
        return {
            "success": True,
            "bom_id": bom_id,
            "message": "BOM已创建",
            "bom": bom
        }
    
    def calculate_material_requirements(
        self,
        product_id: str,
        required_quantity: int
    ) -> Dict[str, Any]:
        """
        计算物料需求
        
        Args:
            product_id: 产品ID
            required_quantity: 需求数量
        
        Returns:
            物料需求清单
        """
        # 查找产品的BOM
        bom = next((b for b in self.bom_structures.values() 
                   if b["product_id"] == product_id and b["status"] == "active"), None)
        
        if not bom:
            return {"success": False, "error": "未找到产品的有效BOM"}
        
        # 计算物料需求
        requirements = []
        for material in bom["materials"]:
            required_qty = material["quantity"] * required_quantity
            requirements.append({
                "material_id": material["material_id"],
                "unit_quantity": material["quantity"],
                "total_required": required_qty,
                "unit": material["unit"],
                "level": material["level"]
            })
        
        return {
            "success": True,
            "product_id": product_id,
            "required_quantity": required_quantity,
            "bom_version": bom["version"],
            "material_requirements": requirements
        }
    
    def get_process_statistics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取工艺统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            统计报告
        """
        # 工艺路线统计
        total_routes = len(self.process_routes)
        active_routes = len([r for r in self.process_routes.values() 
                            if r["status"] == ProcessStatus.ACTIVE.value])
        
        # 变更请求统计
        changes_in_range = [
            cr for cr in self.change_requests
            if start_date <= cr["created_at"][:10] <= end_date
        ]
        
        total_changes = len(changes_in_range)
        approved_changes = len([cr for cr in changes_in_range if cr["status"] in ["approved", "implemented"]])
        
        # 按变更类型统计
        by_type = {}
        for cr in changes_in_range:
            ctype = cr["change_type"]
            by_type[ctype] = by_type.get(ctype, 0) + 1
        
        return {
            "period": {"start": start_date, "end": end_date},
            "routes": {
                "total": total_routes,
                "active": active_routes,
                "draft": len([r for r in self.process_routes.values() 
                             if r["status"] == ProcessStatus.DRAFT.value])
            },
            "changes": {
                "total": total_changes,
                "approved": approved_changes,
                "rejected": len([cr for cr in changes_in_range if cr["status"] == "rejected"]),
                "pending": len([cr for cr in changes_in_range if cr["status"] == "pending"]),
                "by_type": by_type
            },
            "operations": {
                "total": len(self.operations),
                "active": len([o for o in self.operations.values() if o["active"]])
            },
            "boms": {
                "total": len(self.bom_structures),
                "active": len([b for b in self.bom_structures.values() if b["status"] == "active"])
            }
        }


# 创建默认实例
default_process_manager = ProcessManager()
