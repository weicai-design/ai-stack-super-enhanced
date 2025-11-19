"""
流程管理器
Process Manager

提供全流程业务管理：市场调研→回款

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum

from .models import BusinessProcess, ProcessStatus, Issue

logger = logging.getLogger(__name__)


class BusinessStage(str, Enum):
    """业务阶段"""
    MARKET_RESEARCH = "market_research"      # 市场调研
    CUSTOMER_DEV = "customer_development"    # 客户开发
    PROJECT_DEV = "project_development"      # 项目开发
    PRODUCTION_MGMT = "production_management"  # 投产管理
    ORDER_MGMT = "order_management"          # 订单管理
    PRODUCTION_PLAN = "production_planning"  # 生产计划
    MATERIAL_PLAN = "material_planning"      # 物料需求计划
    PURCHASE_PLAN = "purchase_planning"      # 采购计划
    MATERIAL_ARRIVAL = "material_arrival"    # 到料
    PRODUCTION_EXEC = "production_execution" # 生产执行
    QUALITY_CHECK = "quality_inspection"     # 检验
    WAREHOUSE_IN = "warehouse_in"            # 入库
    STORAGE = "storage"                      # 储存
    DELIVERY = "delivery"                    # 交付
    SHIPPING = "shipping"                    # 发运
    PAYMENT = "payment_collection"           # 客户账款回款


class ProcessManager:
    """流程管理器"""
    
    def __init__(self):
        """初始化流程管理器"""
        logger.info("✅ 流程管理器已初始化")
    
    def create_full_business_process(
        self,
        tenant_id: str,
        customer_name: str,
        project_name: str,
        order_amount: float
    ) -> BusinessProcess:
        """
        创建完整业务流程
        
        从市场调研到回款的全流程
        
        Args:
            tenant_id: 租户ID
            customer_name: 客户名称
            project_name: 项目名称
            order_amount: 订单金额
        
        Returns:
            业务流程实例
        """
        process = BusinessProcess(
            tenant_id=tenant_id,
            workflow_id="full_business_flow",
            name=f"{customer_name} - {project_name}",
            current_step=0,
            status=ProcessStatus.PENDING,
            data={
                "customer_name": customer_name,
                "project_name": project_name,
                "order_amount": order_amount,
                "stages": [],
                "created_date": date.today().isoformat()
            }
        )
        
        # 初始化所有业务阶段
        for stage in BusinessStage:
            process.data["stages"].append({
                "stage": stage.value,
                "status": "pending",
                "data": {}
            })
        
        logger.info(f"创建全流程业务: {process.name}")
        
        return process
    
    def update_stage(
        self,
        process: BusinessProcess,
        stage: BusinessStage,
        data: Dict[str, Any]
    ) -> BusinessProcess:
        """
        更新业务阶段数据
        
        Args:
            process: 业务流程
            stage: 业务阶段
            data: 阶段数据
        
        Returns:
            更新后的流程
        """
        # 查找对应阶段
        for stage_info in process.data.get("stages", []):
            if stage_info["stage"] == stage.value:
                stage_info["data"].update(data)
                stage_info["updated_at"] = datetime.now().isoformat()
                
                # 如果有完成标记，更新状态
                if data.get("completed"):
                    stage_info["status"] = "completed"
                    stage_info["completed_at"] = datetime.now().isoformat()
                else:
                    stage_info["status"] = "in_progress"
                
                logger.info(f"更新业务阶段 {stage.value}: {data}")
                break
        
        process.updated_at = datetime.now()
        return process
    
    def get_stage_data(
        self,
        process: BusinessProcess,
        stage: BusinessStage
    ) -> Optional[Dict[str, Any]]:
        """
        获取业务阶段数据
        
        Args:
            process: 业务流程
            stage: 业务阶段
        
        Returns:
            阶段数据
        """
        for stage_info in process.data.get("stages", []):
            if stage_info["stage"] == stage.value:
                return stage_info
        
        return None
    
    def calculate_progress(
        self,
        process: BusinessProcess
    ) -> Dict[str, Any]:
        """
        计算流程进度
        
        Args:
            process: 业务流程
        
        Returns:
            进度信息
        """
        stages = process.data.get("stages", [])
        total_stages = len(stages)
        completed_stages = sum(1 for s in stages if s.get("status") == "completed")
        in_progress_stages = sum(1 for s in stages if s.get("status") == "in_progress")
        
        progress_percent = (completed_stages / total_stages * 100) if total_stages > 0 else 0
        
        return {
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "in_progress_stages": in_progress_stages,
            "pending_stages": total_stages - completed_stages - in_progress_stages,
            "progress_percent": progress_percent,
            "status": process.status
        }
    
    def get_kpi_metrics(
        self,
        tenant_id: str,
        processes: List[BusinessProcess]
    ) -> Dict[str, Any]:
        """
        计算KPI指标
        
        Args:
            tenant_id: 租户ID
            processes: 业务流程列表
        
        Returns:
            KPI指标
        """
        if not processes:
            return {}
        
        # 统计各状态流程数
        status_counts = {}
        for process in processes:
            status = process.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 计算完成率
        completed = status_counts.get("completed", 0)
        total = len(processes)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # 计算平均周期
        completed_processes = [p for p in processes if p.status == ProcessStatus.COMPLETED]
        avg_cycle_days = 0
        if completed_processes:
            cycle_times = []
            for p in completed_processes:
                if p.started_at and p.completed_at:
                    cycle_time = (p.completed_at - p.started_at).days
                    cycle_times.append(cycle_time)
            
            if cycle_times:
                avg_cycle_days = sum(cycle_times) / len(cycle_times)
        
        # 阻塞流程
        blocked_count = status_counts.get("blocked", 0)
        blocked_rate = (blocked_count / total * 100) if total > 0 else 0
        
        return {
            "total_processes": total,
            "completed_processes": completed,
            "in_progress_processes": status_counts.get("in_progress", 0),
            "blocked_processes": blocked_count,
            "cancelled_processes": status_counts.get("cancelled", 0),
            "completion_rate": completion_rate,
            "blocked_rate": blocked_rate,
            "avg_cycle_days": avg_cycle_days
        }


# ==================== 导出 ====================

__all__ = [
    "WorkflowEngine",
    "BusinessStage"
]



























