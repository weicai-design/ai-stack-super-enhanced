"""
全流程管理器
实现从市场调研到账款回收的完整企业运营流程
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class ProcessStage(Enum):
    """流程阶段"""
    MARKET_RESEARCH = "market_research"  # 市场调研
    CUSTOMER_DEVELOPMENT = "customer_development"  # 客户开发
    PROJECT_DEVELOPMENT = "project_development"  # 项目开发
    PRODUCTION_PLANNING = "production_planning"  # 投产管理
    ORDER_MANAGEMENT = "order_management"  # 订单管理
    PROCUREMENT = "procurement"  # 采购
    MATERIAL_RECEIPT = "material_receipt"  # 到料
    PRODUCTION = "production"  # 生产
    QUALITY_CHECK = "quality_check"  # 检验
    WAREHOUSING = "warehousing"  # 入库
    DELIVERY = "delivery"  # 交付
    SHIPPING = "shipping"  # 发运
    PAYMENT = "payment"  # 账款回收


class FullProcessManager:
    """全流程管理器"""
    
    def __init__(self):
        """初始化全流程管理器"""
        self.processes = {}
        self.process_counter = 1000
    
    def initiate_full_process(
        self,
        business_opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        启动完整业务流程
        
        Args:
            business_opportunity: 商机信息 {
                "source": "来源",
                "customer_info": {},
                "product_interest": [],
                "estimated_value": 0
            }
        
        Returns:
            流程信息
        """
        process_id = f"BP{datetime.now().strftime('%Y%m%d')}{self.process_counter:04d}"
        self.process_counter += 1
        
        process = {
            "process_id": process_id,
            "business_opportunity": business_opportunity,
            "current_stage": ProcessStage.MARKET_RESEARCH.value,
            "stages": {},
            "timeline": [],
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "total_value": 0,
            "documents": []
        }
        
        # 初始化市场调研阶段
        process["stages"][ProcessStage.MARKET_RESEARCH.value] = {
            "stage": ProcessStage.MARKET_RESEARCH.value,
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "data": {},
            "next_stage": ProcessStage.CUSTOMER_DEVELOPMENT.value
        }
        
        self.processes[process_id] = process
        
        return {
            "success": True,
            "process_id": process_id,
            "message": "全流程已启动",
            "process": process
        }
    
    def complete_market_research(
        self,
        process_id: str,
        research_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        完成市场调研
        
        Args:
            process_id: 流程ID
            research_data: 调研数据 {
                "market_size": 0,
                "competitors": [],
                "customer_needs": [],
                "feasibility": ""
            }
        
        Returns:
            完成结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        stage = process["stages"][ProcessStage.MARKET_RESEARCH.value]
        
        stage["status"] = "completed"
        stage["completed_at"] = datetime.now().isoformat()
        stage["data"] = research_data
        
        # 推进到下一阶段
        self._advance_to_next_stage(process, ProcessStage.CUSTOMER_DEVELOPMENT.value)
        
        return {
            "success": True,
            "message": "市场调研已完成，进入客户开发阶段",
            "next_stage": ProcessStage.CUSTOMER_DEVELOPMENT.value
        }
    
    def complete_customer_development(
        self,
        process_id: str,
        customer_id: str,
        contact_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        完成客户开发
        
        Args:
            process_id: 流程ID
            customer_id: 客户ID
            contact_history: 接触历史
        
        Returns:
            完成结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        # 完成客户开发阶段
        stage_data = {
            "stage": ProcessStage.CUSTOMER_DEVELOPMENT.value,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "data": {
                "customer_id": customer_id,
                "contact_history": contact_history
            }
        }
        
        process["stages"][ProcessStage.CUSTOMER_DEVELOPMENT.value] = stage_data
        
        # 推进到项目开发
        self._advance_to_next_stage(process, ProcessStage.PROJECT_DEVELOPMENT.value)
        
        return {
            "success": True,
            "message": "客户开发已完成，进入项目开发阶段",
            "customer_id": customer_id
        }
    
    def complete_project_development(
        self,
        process_id: str,
        project_id: str,
        specifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        完成项目开发
        
        Args:
            process_id: 流程ID
            project_id: 项目ID
            specifications: 规格要求
        
        Returns:
            完成结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        stage_data = {
            "stage": ProcessStage.PROJECT_DEVELOPMENT.value,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "data": {
                "project_id": project_id,
                "specifications": specifications
            }
        }
        
        process["stages"][ProcessStage.PROJECT_DEVELOPMENT.value] = stage_data
        
        # 推进到投产管理
        self._advance_to_next_stage(process, ProcessStage.PRODUCTION_PLANNING.value)
        
        return {
            "success": True,
            "message": "项目开发已完成，进入投产管理阶段",
            "project_id": project_id
        }
    
    def link_order(
        self,
        process_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        关联订单
        
        Args:
            process_id: 流程ID
            order_id: 订单ID
        
        Returns:
            关联结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        stage_data = {
            "stage": ProcessStage.ORDER_MANAGEMENT.value,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "data": {"order_id": order_id}
        }
        
        process["stages"][ProcessStage.ORDER_MANAGEMENT.value] = stage_data
        
        # 推进到采购阶段
        self._advance_to_next_stage(process, ProcessStage.PROCUREMENT.value)
        
        return {
            "success": True,
            "message": "订单已关联，进入采购阶段",
            "order_id": order_id
        }
    
    def track_procurement(
        self,
        process_id: str,
        procurement_order_id: str
    ) -> Dict[str, Any]:
        """
        跟踪采购
        
        Args:
            process_id: 流程ID
            procurement_order_id: 采购订单ID
        
        Returns:
            跟踪结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        if ProcessStage.PROCUREMENT.value not in process["stages"]:
            process["stages"][ProcessStage.PROCUREMENT.value] = {
                "stage": ProcessStage.PROCUREMENT.value,
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "procurement_orders": []
            }
        
        process["stages"][ProcessStage.PROCUREMENT.value]["procurement_orders"].append(procurement_order_id)
        
        return {
            "success": True,
            "message": "采购订单已关联",
            "procurement_order_id": procurement_order_id
        }
    
    def record_payment_received(
        self,
        process_id: str,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        记录账款回收
        
        Args:
            process_id: 流程ID
            payment_data: 付款数据 {
                "amount": 0,
                "payment_method": "",
                "transaction_id": ""
            }
        
        Returns:
            记录结果
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        # 记录付款
        stage_data = {
            "stage": ProcessStage.PAYMENT.value,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "data": payment_data
        }
        
        process["stages"][ProcessStage.PAYMENT.value] = stage_data
        
        # 计算总价值
        process["total_value"] = payment_data.get("amount", 0)
        
        # 标记流程完成
        process["status"] = "completed"
        process["completed_at"] = datetime.now().isoformat()
        
        # 计算流程周期
        start_time = datetime.fromisoformat(process["created_at"])
        end_time = datetime.now()
        cycle_days = (end_time - start_time).days
        process["cycle_days"] = cycle_days
        
        return {
            "success": True,
            "message": "账款已回收，流程完成",
            "total_value": process["total_value"],
            "cycle_days": cycle_days
        }
    
    def get_process_status(
        self,
        process_id: str
    ) -> Dict[str, Any]:
        """
        获取流程状态
        
        Args:
            process_id: 流程ID
        
        Returns:
            流程状态
        """
        if process_id not in self.processes:
            return {"success": False, "error": "流程不存在"}
        
        process = self.processes[process_id]
        
        # 统计各阶段状态
        stage_summary = {}
        for stage_name, stage_data in process["stages"].items():
            stage_summary[stage_name] = stage_data["status"]
        
        # 计算进度
        total_stages = len(ProcessStage)
        completed_stages = sum(1 for s in process["stages"].values() if s["status"] == "completed")
        progress = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        
        return {
            "success": True,
            "process_id": process_id,
            "current_stage": process["current_stage"],
            "overall_status": process["status"],
            "progress_percent": round(progress, 2),
            "stages_completed": completed_stages,
            "total_stages": total_stages,
            "stage_summary": stage_summary,
            "created_at": process["created_at"],
            "total_value": process.get("total_value", 0)
        }
    
    def get_all_active_processes(self) -> Dict[str, Any]:
        """
        获取所有活跃流程
        
        Returns:
            活跃流程列表
        """
        active_processes = [
            {
                "process_id": pid,
                "current_stage": p["current_stage"],
                "created_at": p["created_at"],
                "estimated_value": p["business_opportunity"].get("estimated_value", 0)
            }
            for pid, p in self.processes.items()
            if p["status"] == "active"
        ]
        
        return {
            "success": True,
            "total_active": len(active_processes),
            "processes": active_processes
        }
    
    def get_cycle_time_analysis(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取周期时间分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            周期分析
        """
        # 筛选已完成的流程
        completed = [
            p for p in self.processes.values()
            if p["status"] == "completed"
            and start_date <= p["created_at"][:10] <= end_date
        ]
        
        if not completed:
            return {
                "success": True,
                "message": "该时期内无已完成流程"
            }
        
        # 计算平均周期
        avg_cycle = sum(p.get("cycle_days", 0) for p in completed) / len(completed)
        
        # 最快和最慢
        fastest = min(completed, key=lambda x: x.get("cycle_days", 999))
        slowest = max(completed, key=lambda x: x.get("cycle_days", 0))
        
        return {
            "success": True,
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_completed": len(completed),
                "average_cycle_days": round(avg_cycle, 2),
                "fastest_cycle_days": fastest.get("cycle_days", 0),
                "slowest_cycle_days": slowest.get("cycle_days", 0)
            },
            "total_value": sum(p.get("total_value", 0) for p in completed)
        }
    
    def _advance_to_next_stage(
        self,
        process: Dict[str, Any],
        next_stage: str
    ):
        """
        推进到下一阶段
        
        Args:
            process: 流程数据
            next_stage: 下一阶段
        """
        process["current_stage"] = next_stage
        
        if next_stage not in process["stages"]:
            process["stages"][next_stage] = {
                "stage": next_stage,
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "data": {}
            }
        
        # 记录时间线
        process["timeline"].append({
            "stage": next_stage,
            "timestamp": datetime.now().isoformat(),
            "action": "stage_started"
        })


# 创建默认实例
full_process_manager = FullProcessManager()

