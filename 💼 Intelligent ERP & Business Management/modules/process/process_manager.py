"""
工艺管理模块
实现完整的工艺路线、工序、参数、文件管理功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ProcessStatus(Enum):
    """工艺状态"""
    DRAFT = "draft"  # 草稿
    REVIEW = "review"  # 审核中
    APPROVED = "approved"  # 已批准
    IN_USE = "in_use"  # 使用中
    OBSOLETE = "obsolete"  # 已废弃


class ProcessManager:
    """工艺管理器"""
    
    def __init__(self):
        """初始化工艺管理器"""
        self.process_routes = {}
        self.process_steps = {}
        self.process_parameters = {}
        self.process_documents = {}
        self.process_versions = {}
        self.route_counter = 1000
    
    def create_process_route(
        self,
        product_id: str,
        route_name: str,
        description: str,
        created_by: str
    ) -> Dict[str, Any]:
        """
        创建工艺路线
        
        Args:
            product_id: 产品ID
            route_name: 路线名称
            description: 描述
            created_by: 创建人
        
        Returns:
            工艺路线信息
        """
        route_id = f"PR{datetime.now().strftime('%Y%m%d')}{self.route_counter:04d}"
        self.route_counter += 1
        
        route = {
            "route_id": route_id,
            "product_id": product_id,
            "route_name": route_name,
            "description": description,
            "version": "1.0",
            "status": ProcessStatus.DRAFT.value,
            "steps": [],
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "approved_by": None,
            "approved_at": None
        }
        
        self.process_routes[route_id] = route
        
        return {
            "success": True,
            "route_id": route_id,
            "message": "工艺路线已创建",
            "route": route
        }
    
    def add_process_step(
        self,
        route_id: str,
        step_number: int,
        step_name: str,
        operation_type: str,
        workstation: str,
        standard_time_minutes: float,
        equipment_required: List[str] = None,
        skills_required: List[str] = None
    ) -> Dict[str, Any]:
        """
        添加工艺步骤
        
        Args:
            route_id: 工艺路线ID
            step_number: 步骤序号
            step_name: 步骤名称
            operation_type: 操作类型
            workstation: 工作站
            standard_time_minutes: 标准时间（分钟）
            equipment_required: 所需设备
            skills_required: 所需技能
        
        Returns:
            工艺步骤信息
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        if route["status"] not in [ProcessStatus.DRAFT.value, ProcessStatus.REVIEW.value]:
            return {"success": False, "error": "工艺路线已批准，无法修改"}
        
        step_id = f"PS{datetime.now().strftime('%Y%m%d%H%M%S')}{step_number:03d}"
        
        step = {
            "step_id": step_id,
            "route_id": route_id,
            "step_number": step_number,
            "step_name": step_name,
            "operation_type": operation_type,
            "workstation": workstation,
            "standard_time_minutes": standard_time_minutes,
            "equipment_required": equipment_required or [],
            "skills_required": skills_required or [],
            "quality_checkpoints": [],
            "parameters": [],
            "documents": [],
            "created_at": datetime.now().isoformat()
        }
        
        self.process_steps[step_id] = step
        route["steps"].append(step_id)
        
        # 按步骤序号排序
        route["steps"].sort(key=lambda sid: self.process_steps[sid]["step_number"])
        
        return {
            "success": True,
            "step_id": step_id,
            "message": "工艺步骤已添加",
            "step": step
        }
    
    def add_process_parameter(
        self,
        step_id: str,
        parameter_name: str,
        parameter_type: str,
        target_value: Any,
        tolerance_upper: Optional[float] = None,
        tolerance_lower: Optional[float] = None,
        unit: str = ""
    ) -> Dict[str, Any]:
        """
        添加工艺参数
        
        Args:
            step_id: 步骤ID
            parameter_name: 参数名称
            parameter_type: 参数类型 (numeric/text/boolean)
            target_value: 目标值
            tolerance_upper: 上限公差
            tolerance_lower: 下限公差
            unit: 单位
        
        Returns:
            工艺参数信息
        """
        if step_id not in self.process_steps:
            return {"success": False, "error": "工艺步骤不存在"}
        
        step = self.process_steps[step_id]
        
        param_id = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        parameter = {
            "param_id": param_id,
            "step_id": step_id,
            "parameter_name": parameter_name,
            "parameter_type": parameter_type,
            "target_value": target_value,
            "tolerance_upper": tolerance_upper,
            "tolerance_lower": tolerance_lower,
            "unit": unit,
            "created_at": datetime.now().isoformat()
        }
        
        self.process_parameters[param_id] = parameter
        step["parameters"].append(param_id)
        
        return {
            "success": True,
            "param_id": param_id,
            "message": "工艺参数已添加",
            "parameter": parameter
        }
    
    def attach_process_document(
        self,
        step_id: str,
        document_name: str,
        document_type: str,
        file_path: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        附加工艺文件
        
        Args:
            step_id: 步骤ID
            document_name: 文件名称
            document_type: 文件类型 (drawing/photo/video/instruction)
            file_path: 文件路径
            description: 描述
        
        Returns:
            文件信息
        """
        if step_id not in self.process_steps:
            return {"success": False, "error": "工艺步骤不存在"}
        
        step = self.process_steps[step_id]
        
        doc_id = f"PD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        document = {
            "doc_id": doc_id,
            "step_id": step_id,
            "document_name": document_name,
            "document_type": document_type,
            "file_path": file_path,
            "description": description,
            "uploaded_at": datetime.now().isoformat()
        }
        
        self.process_documents[doc_id] = document
        step["documents"].append(doc_id)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "工艺文件已附加",
            "document": document
        }
    
    def submit_for_approval(
        self,
        route_id: str,
        submitter: str
    ) -> Dict[str, Any]:
        """
        提交审批
        
        Args:
            route_id: 工艺路线ID
            submitter: 提交人
        
        Returns:
            提交结果
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        if route["status"] != ProcessStatus.DRAFT.value:
            return {"success": False, "error": "工艺路线状态不正确"}
        
        if not route["steps"]:
            return {"success": False, "error": "工艺路线没有步骤"}
        
        route["status"] = ProcessStatus.REVIEW.value
        route["submitted_by"] = submitter
        route["submitted_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "已提交审批",
            "route": route
        }
    
    def approve_process_route(
        self,
        route_id: str,
        approver: str,
        approved: bool,
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        审批工艺路线
        
        Args:
            route_id: 工艺路线ID
            approver: 审批人
            approved: 是否批准
            comments: 审批意见
        
        Returns:
            审批结果
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        if route["status"] != ProcessStatus.REVIEW.value:
            return {"success": False, "error": "工艺路线未提交审批"}
        
        if approved:
            route["status"] = ProcessStatus.APPROVED.value
            route["approved_by"] = approver
            route["approved_at"] = datetime.now().isoformat()
            route["approval_comments"] = comments
            
            message = "工艺路线已批准"
        else:
            route["status"] = ProcessStatus.DRAFT.value
            route["rejected_by"] = approver
            route["rejected_at"] = datetime.now().isoformat()
            route["rejection_comments"] = comments
            
            message = "工艺路线已退回"
        
        return {
            "success": True,
            "message": message,
            "route": route
        }
    
    def activate_process_route(
        self,
        route_id: str
    ) -> Dict[str, Any]:
        """
        激活工艺路线
        
        Args:
            route_id: 工艺路线ID
        
        Returns:
            激活结果
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        if route["status"] != ProcessStatus.APPROVED.value:
            return {"success": False, "error": "工艺路线未批准"}
        
        # 保存版本历史
        version_id = f"{route_id}_V{route['version']}"
        self.process_versions[version_id] = route.copy()
        
        # 激活
        route["status"] = ProcessStatus.IN_USE.value
        route["activated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "message": "工艺路线已激活",
            "route": route
        }
    
    def create_new_version(
        self,
        route_id: str,
        created_by: str,
        change_description: str
    ) -> Dict[str, Any]:
        """
        创建新版本
        
        Args:
            route_id: 工艺路线ID
            created_by: 创建人
            change_description: 变更说明
        
        Returns:
            新版本信息
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        old_route = self.process_routes[route_id]
        
        # 保存旧版本
        version_id = f"{route_id}_V{old_route['version']}"
        self.process_versions[version_id] = old_route.copy()
        
        # 计算新版本号
        major, minor = map(int, old_route["version"].split('.'))
        new_version = f"{major}.{minor + 1}"
        
        # 创建新版本（复制旧版本的内容）
        new_route_id = f"PR{datetime.now().strftime('%Y%m%d')}{self.route_counter:04d}"
        self.route_counter += 1
        
        new_route = old_route.copy()
        new_route["route_id"] = new_route_id
        new_route["version"] = new_version
        new_route["status"] = ProcessStatus.DRAFT.value
        new_route["previous_version"] = route_id
        new_route["change_description"] = change_description
        new_route["created_by"] = created_by
        new_route["created_at"] = datetime.now().isoformat()
        new_route["approved_by"] = None
        new_route["approved_at"] = None
        
        self.process_routes[new_route_id] = new_route
        
        # 旧版本标记为废弃
        old_route["status"] = ProcessStatus.OBSOLETE.value
        old_route["obsolete_at"] = datetime.now().isoformat()
        old_route["replaced_by"] = new_route_id
        
        return {
            "success": True,
            "message": f"新版本 {new_version} 已创建",
            "new_route_id": new_route_id,
            "new_route": new_route
        }
    
    def get_process_route_details(
        self,
        route_id: str
    ) -> Dict[str, Any]:
        """
        获取工艺路线详情
        
        Args:
            route_id: 工艺路线ID
        
        Returns:
            详细信息
        """
        if route_id not in self.process_routes:
            return {"success": False, "error": "工艺路线不存在"}
        
        route = self.process_routes[route_id]
        
        # 获取所有步骤的详细信息
        steps_details = []
        for step_id in route["steps"]:
            if step_id in self.process_steps:
                step = self.process_steps[step_id].copy()
                
                # 获取参数详情
                parameters = [
                    self.process_parameters[pid]
                    for pid in step["parameters"]
                    if pid in self.process_parameters
                ]
                
                # 获取文档详情
                documents = [
                    self.process_documents[did]
                    for did in step["documents"]
                    if did in self.process_documents
                ]
                
                step["parameter_details"] = parameters
                step["document_details"] = documents
                
                steps_details.append(step)
        
        # 计算总标准时间
        total_time = sum(s["standard_time_minutes"] for s in steps_details)
        
        return {
            "success": True,
            "route": route,
            "steps": steps_details,
            "summary": {
                "total_steps": len(steps_details),
                "total_standard_time_minutes": total_time,
                "total_parameters": sum(len(s["parameters"]) for s in steps_details),
                "total_documents": sum(len(s["documents"]) for s in steps_details)
            }
        }
    
    def get_process_statistics(
        self
    ) -> Dict[str, Any]:
        """
        获取工艺统计
        
        Returns:
            统计报告
        """
        total_routes = len(self.process_routes)
        
        # 按状态统计
        status_stats = {}
        for route in self.process_routes.values():
            status = route["status"]
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 按产品统计
        product_stats = {}
        for route in self.process_routes.values():
            product_id = route["product_id"]
            product_stats[product_id] = product_stats.get(product_id, 0) + 1
        
        # 复杂度分析
        complexity_levels = {"简单": 0, "中等": 0, "复杂": 0}
        for route in self.process_routes.values():
            step_count = len(route["steps"])
            if step_count <= 3:
                complexity_levels["简单"] += 1
            elif step_count <= 8:
                complexity_levels["中等"] += 1
            else:
                complexity_levels["复杂"] += 1
        
        return {
            "success": True,
            "summary": {
                "total_routes": total_routes,
                "total_steps": len(self.process_steps),
                "total_parameters": len(self.process_parameters),
                "total_documents": len(self.process_documents)
            },
            "by_status": status_stats,
            "by_product": product_stats,
            "complexity_distribution": complexity_levels,
            "in_use_routes": status_stats.get(ProcessStatus.IN_USE.value, 0)
        }


# 创建默认实例
default_process_manager = ProcessManager()
