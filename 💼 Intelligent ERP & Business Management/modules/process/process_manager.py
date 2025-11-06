#!/usr/bin/env python3
"""
工艺管理系统
Process Management System

功能：
- 工艺路线管理
- 工艺参数管理
- 工序管理
- 工艺文件管理
- 工艺变更管理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ProcessStatus(Enum):
    """工艺状态"""
    DRAFT = "draft"  # 草稿
    APPROVED = "approved"  # 已批准
    ACTIVE = "active"  # 生效中
    OBSOLETE = "obsolete"  # 已废弃


class ProcessManager:
    """工艺管理器"""
    
    def __init__(self):
        """初始化工艺管理器"""
        self.process_routes: Dict[str, Dict[str, Any]] = {}
        self.operations: Dict[str, Dict[str, Any]] = {}
        self.process_documents: Dict[str, Dict[str, Any]] = {}
        self.process_changes: List[Dict[str, Any]] = []
        
    # ==================== 工艺路线管理 ====================
    
    def create_process_route(
        self,
        route_id: str,
        product_id: str,
        product_name: str,
        version: str = "1.0",
        description: str = "",
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        创建工艺路线
        
        Args:
            route_id: 工艺路线ID
            product_id: 产品ID
            product_name: 产品名称
            version: 版本号
            description: 描述
            created_by: 创建人
        
        Returns:
            工艺路线信息
        """
        route = {
            "route_id": route_id,
            "product_id": product_id,
            "product_name": product_name,
            "version": version,
            "description": description,
            "status": ProcessStatus.DRAFT.value,
            "operations": [],  # 工序列表
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
            "approved_by": None,
            "approved_at": None,
            "effective_date": None
        }
        
        self.process_routes[route_id] = route
        return route
    
    def add_operation_to_route(
        self,
        route_id: str,
        operation_id: str,
        operation_name: str,
        sequence: int,
        work_center: str,
        standard_time: float,  # 标准工时（分钟）
        setup_time: float = 0,  # 准备时间（分钟）
        description: str = "",
        parameters: Dict[str, Any] = None,
        quality_requirements: List[Dict[str, Any]] = None,
        tools_required: List[str] = None
    ) -> Dict[str, Any]:
        """
        添加工序到工艺路线
        
        Args:
            route_id: 工艺路线ID
            operation_id: 工序ID
            operation_name: 工序名称
            sequence: 工序顺序号
            work_center: 工作中心
            standard_time: 标准工时（分钟）
            setup_time: 准备时间（分钟）
            description: 工序描述
            parameters: 工艺参数
            quality_requirements: 质量要求
            tools_required: 所需工具
        
        Returns:
            工序信息
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        operation = {
            "operation_id": operation_id,
            "route_id": route_id,
            "operation_name": operation_name,
            "sequence": sequence,
            "work_center": work_center,
            "standard_time": standard_time,
            "setup_time": setup_time,
            "description": description,
            "parameters": parameters or {},
            "quality_requirements": quality_requirements or [],
            "tools_required": tools_required or [],
            "created_at": datetime.now().isoformat()
        }
        
        self.operations[operation_id] = operation
        
        # 添加到路线
        route = self.process_routes[route_id]
        route["operations"].append(operation)
        
        # 按序号排序
        route["operations"].sort(key=lambda x: x["sequence"])
        
        return operation
    
    def approve_process_route(
        self,
        route_id: str,
        approved_by: str,
        effective_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批准工艺路线
        
        Args:
            route_id: 工艺路线ID
            approved_by: 批准人
            effective_date: 生效日期
        
        Returns:
            更新后的工艺路线
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        route = self.process_routes[route_id]
        
        if effective_date is None:
            effective_date = datetime.now().date().isoformat()
        
        route["status"] = ProcessStatus.APPROVED.value
        route["approved_by"] = approved_by
        route["approved_at"] = datetime.now().isoformat()
        route["effective_date"] = effective_date
        
        # 记录变更
        self._record_process_change(
            route_id=route_id,
            change_type="approval",
            description=f"工艺路线由 {approved_by} 批准，生效日期：{effective_date}",
            changed_by=approved_by
        )
        
        return route
    
    def activate_process_route(
        self,
        route_id: str,
        activated_by: str
    ) -> Dict[str, Any]:
        """
        激活工艺路线
        
        Args:
            route_id: 工艺路线ID
            activated_by: 激活人
        
        Returns:
            更新后的工艺路线
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        route = self.process_routes[route_id]
        
        if route["status"] != ProcessStatus.APPROVED.value:
            raise ValueError("只有已批准的工艺路线才能激活")
        
        route["status"] = ProcessStatus.ACTIVE.value
        route["activated_by"] = activated_by
        route["activated_at"] = datetime.now().isoformat()
        
        # 记录变更
        self._record_process_change(
            route_id=route_id,
            change_type="activation",
            description=f"工艺路线由 {activated_by} 激活",
            changed_by=activated_by
        )
        
        return route
    
    # ==================== 工艺参数管理 ====================
    
    def update_operation_parameters(
        self,
        operation_id: str,
        parameters: Dict[str, Any],
        updated_by: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        更新工序参数
        
        Args:
            operation_id: 工序ID
            parameters: 新参数
            updated_by: 更新人
            reason: 更新原因
        
        Returns:
            更新后的工序信息
        """
        if operation_id not in self.operations:
            raise ValueError(f"工序 {operation_id} 不存在")
        
        operation = self.operations[operation_id]
        old_parameters = operation["parameters"].copy()
        
        operation["parameters"].update(parameters)
        operation["updated_at"] = datetime.now().isoformat()
        operation["updated_by"] = updated_by
        
        # 记录变更
        route_id = operation["route_id"]
        self._record_process_change(
            route_id=route_id,
            change_type="parameter_update",
            description=f"工序 {operation['operation_name']} 参数更新: {reason}",
            changed_by=updated_by,
            old_value=old_parameters,
            new_value=operation["parameters"]
        )
        
        return operation
    
    def get_operation_parameters(
        self,
        operation_id: str
    ) -> Dict[str, Any]:
        """
        获取工序参数
        
        Args:
            operation_id: 工序ID
        
        Returns:
            工序参数
        """
        if operation_id not in self.operations:
            raise ValueError(f"工序 {operation_id} 不存在")
        
        return self.operations[operation_id]["parameters"]
    
    # ==================== 工艺文件管理 ====================
    
    def add_process_document(
        self,
        doc_id: str,
        route_id: str,
        doc_type: str,  # sop/drawing/spec/instruction
        title: str,
        file_path: str,
        version: str = "1.0",
        uploaded_by: str = "system",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        添加工艺文件
        
        Args:
            doc_id: 文档ID
            route_id: 工艺路线ID
            doc_type: 文档类型
            title: 文档标题
            file_path: 文件路径
            version: 版本号
            uploaded_by: 上传人
            notes: 备注
        
        Returns:
            文档信息
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        document = {
            "doc_id": doc_id,
            "route_id": route_id,
            "doc_type": doc_type,
            "title": title,
            "file_path": file_path,
            "version": version,
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.now().isoformat(),
            "notes": notes,
            "status": "active"
        }
        
        self.process_documents[doc_id] = document
        
        # 添加到工艺路线
        route = self.process_routes[route_id]
        if "documents" not in route:
            route["documents"] = []
        route["documents"].append(doc_id)
        
        return document
    
    def get_route_documents(
        self,
        route_id: str,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取工艺路线的文档列表
        
        Args:
            route_id: 工艺路线ID
            doc_type: 文档类型筛选
        
        Returns:
            文档列表
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        documents = [
            self.process_documents[doc_id]
            for doc_id in self.process_routes[route_id].get("documents", [])
            if doc_id in self.process_documents
        ]
        
        if doc_type:
            documents = [d for d in documents if d["doc_type"] == doc_type]
        
        return documents
    
    # ==================== 工艺变更管理 ====================
    
    def _record_process_change(
        self,
        route_id: str,
        change_type: str,
        description: str,
        changed_by: str,
        old_value: Any = None,
        new_value: Any = None
    ):
        """
        记录工艺变更
        
        Args:
            route_id: 工艺路线ID
            change_type: 变更类型
            description: 变更描述
            changed_by: 变更人
            old_value: 旧值
            new_value: 新值
        """
        change = {
            "change_id": f"CHG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "route_id": route_id,
            "change_type": change_type,
            "description": description,
            "changed_by": changed_by,
            "changed_at": datetime.now().isoformat(),
            "old_value": old_value,
            "new_value": new_value
        }
        
        self.process_changes.append(change)
    
    def get_process_change_history(
        self,
        route_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取工艺变更历史
        
        Args:
            route_id: 工艺路线ID
            limit: 返回记录数
        
        Returns:
            变更历史列表
        """
        changes = [
            c for c in self.process_changes
            if c["route_id"] == route_id
        ]
        
        # 按时间倒序
        changes.sort(key=lambda x: x["changed_at"], reverse=True)
        
        return changes[:limit]
    
    # ==================== 查询和分析 ====================
    
    def get_process_route(
        self,
        route_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取工艺路线详情
        
        Args:
            route_id: 工艺路线ID
        
        Returns:
            工艺路线信息
        """
        return self.process_routes.get(route_id)
    
    def list_process_routes(
        self,
        product_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取工艺路线列表
        
        Args:
            product_id: 产品ID筛选
            status: 状态筛选
        
        Returns:
            工艺路线列表
        """
        routes = list(self.process_routes.values())
        
        if product_id:
            routes = [r for r in routes if r["product_id"] == product_id]
        
        if status:
            routes = [r for r in routes if r["status"] == status]
        
        return routes
    
    def calculate_total_time(
        self,
        route_id: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        计算工艺总工时
        
        Args:
            route_id: 工艺路线ID
            quantity: 生产数量
        
        Returns:
            工时统计
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        route = self.process_routes[route_id]
        operations = route["operations"]
        
        total_setup_time = sum(op["setup_time"] for op in operations)
        total_standard_time = sum(op["standard_time"] for op in operations)
        total_time_per_unit = total_standard_time
        total_time_for_quantity = total_setup_time + (total_standard_time * quantity)
        
        return {
            "route_id": route_id,
            "product_name": route["product_name"],
            "quantity": quantity,
            "total_setup_time": total_setup_time,
            "total_standard_time_per_unit": total_standard_time,
            "total_time_for_quantity": total_time_for_quantity,
            "operations_count": len(operations),
            "operations_breakdown": [
                {
                    "sequence": op["sequence"],
                    "operation_name": op["operation_name"],
                    "setup_time": op["setup_time"],
                    "standard_time": op["standard_time"],
                    "total_time": op["setup_time"] + (op["standard_time"] * quantity)
                }
                for op in operations
            ]
        }
    
    def analyze_bottleneck(
        self,
        route_id: str
    ) -> Dict[str, Any]:
        """
        瓶颈工序分析
        
        Args:
            route_id: 工艺路线ID
        
        Returns:
            瓶颈分析结果
        """
        if route_id not in self.process_routes:
            raise ValueError(f"工艺路线 {route_id} 不存在")
        
        route = self.process_routes[route_id]
        operations = route["operations"]
        
        if not operations:
            return {"message": "该工艺路线没有工序"}
        
        # 找出耗时最长的工序
        bottleneck = max(operations, key=lambda x: x["standard_time"])
        
        total_time = sum(op["standard_time"] for op in operations)
        bottleneck_percentage = (bottleneck["standard_time"] / total_time) * 100 if total_time > 0 else 0
        
        return {
            "route_id": route_id,
            "product_name": route["product_name"],
            "bottleneck_operation": {
                "sequence": bottleneck["sequence"],
                "operation_name": bottleneck["operation_name"],
                "standard_time": bottleneck["standard_time"],
                "work_center": bottleneck["work_center"],
                "percentage_of_total": bottleneck_percentage
            },
            "total_operations": len(operations),
            "total_time": total_time
        }


# 创建全局实例
default_process_manager = ProcessManager()

