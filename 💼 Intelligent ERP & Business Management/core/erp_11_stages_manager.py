#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 11环节管理器
实现11个核心业务环节的独立管理、试算和监控
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ERPStage(Enum):
    """ERP 11环节定义"""
    MARKET_RESEARCH = "market_research"              # 1. 市场调研
    CUSTOMER_DEVELOPMENT = "customer_development"     # 2. 客户开发
    PROJECT_DEVELOPMENT = "project_development"       # 3. 项目开发
    PRODUCTION_PLANNING = "production_planning"       # 4. 投产管理
    ORDER_MANAGEMENT = "order_management"             # 5. 订单管理
    PROCUREMENT_RECEIPT = "procurement_receipt"      # 6. 采购与到料
    PRODUCTION = "production"                         # 7. 生产
    QUALITY_CHECK = "quality_check"                   # 8. 检验
    WAREHOUSING = "warehousing"                       # 9. 入库
    DELIVERY_SHIPPING = "delivery_shipping"          # 10. 交付与发运
    PAYMENT = "payment"                               # 11. 账款回收


class ERP11StagesManager:
    """
    ERP 11环节管理器
    每个环节独立管理，支持试算、监控、导出
    """
    
    def __init__(self):
        """初始化11环节管理器"""
        self.stages = {}
        self.stage_instances = {}
        self.calculators = {}
        self.listeners = []
        self._initialize_stages()
        self._initialize_calculators()
    
    def _initialize_stages(self):
        """初始化11个环节"""
        stage_configs = {
            ERPStage.MARKET_RESEARCH.value: {
                "name": "市场调研",
                "order": 1,
                "metrics": ["market_size", "target_segments", "feasibility", "opportunities"],
                "kpi_formula": "market_size * feasibility_score * opportunities_count",
                "default_duration_days": 7,
            },
            ERPStage.CUSTOMER_DEVELOPMENT.value: {
                "name": "客户开发",
                "order": 2,
                "metrics": ["leads_contacted", "qualified_leads", "conversion_rate"],
                "kpi_formula": "qualified_leads / leads_contacted * 100",
                "default_duration_days": 10,
            },
            ERPStage.PROJECT_DEVELOPMENT.value: {
                "name": "项目开发",
                "order": 3,
                "metrics": ["bom_ready", "custom_features", "engineering_hours"],
                "kpi_formula": "custom_features * 10 + engineering_hours / 10",
                "default_duration_days": 12,
            },
            ERPStage.PRODUCTION_PLANNING.value: {
                "name": "投产管理",
                "order": 4,
                "metrics": ["lines_reserved", "capacity_utilization", "planned_batches"],
                "kpi_formula": "capacity_utilization * planned_batches",
                "default_duration_days": 5,
            },
            ERPStage.ORDER_MANAGEMENT.value: {
                "name": "订单管理",
                "order": 5,
                "metrics": ["orders_confirmed", "orders_pending", "value_confirmed"],
                "kpi_formula": "orders_confirmed / (orders_confirmed + orders_pending) * 100",
                "default_duration_days": 9,
            },
            ERPStage.PROCUREMENT_RECEIPT.value: {
                "name": "采购与到料",
                "order": 6,
                "metrics": ["procurement_orders", "materials_received", "on_time_rate"],
                "kpi_formula": "materials_received / procurement_orders * on_time_rate * 100",
                "default_duration_days": 7,
            },
            ERPStage.PRODUCTION.value: {
                "name": "生产",
                "order": 7,
                "metrics": ["units_produced", "production_efficiency", "defect_rate"],
                "kpi_formula": "units_produced * production_efficiency * (1 - defect_rate)",
                "default_duration_days": 10,
            },
            ERPStage.QUALITY_CHECK.value: {
                "name": "检验",
                "order": 8,
                "metrics": ["units_inspected", "pass_rate", "defects_found"],
                "kpi_formula": "units_inspected * pass_rate / 100",
                "default_duration_days": 2,
            },
            ERPStage.WAREHOUSING.value: {
                "name": "入库",
                "order": 9,
                "metrics": ["units_warehoused", "warehouse_utilization", "inventory_turnover"],
                "kpi_formula": "units_warehoused * inventory_turnover",
                "default_duration_days": 1,
            },
            ERPStage.DELIVERY_SHIPPING.value: {
                "name": "交付与发运",
                "order": 10,
                "metrics": ["orders_delivered", "on_time_delivery_rate", "shipping_cost"],
                "kpi_formula": "orders_delivered * on_time_delivery_rate / 100",
                "default_duration_days": 3,
            },
            ERPStage.PAYMENT.value: {
                "name": "账款回收",
                "order": 11,
                "metrics": ["amount_received", "collection_rate", "days_outstanding"],
                "kpi_formula": "amount_received * collection_rate / 100",
                "default_duration_days": 30,
            },
        }
        
        self.stages = stage_configs
    
    def _initialize_calculators(self):
        """初始化试算器"""
        for stage_id, config in self.stages.items():
            self.calculators[stage_id] = StageCalculator(
                stage_id=stage_id,
                formula=config["kpi_formula"],
                metrics=config["metrics"]
            )
    
    def create_stage_instance(
        self,
        stage_id: str,
        process_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建环节实例
        
        Args:
            stage_id: 环节ID
            process_id: 流程ID
            initial_data: 初始数据
            
        Returns:
            环节实例信息
        """
        if stage_id not in self.stages:
            return {"success": False, "error": f"环节 {stage_id} 不存在"}
        
        instance_id = f"{process_id}_{stage_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        instance = {
            "instance_id": instance_id,
            "process_id": process_id,
            "stage_id": stage_id,
            "stage_name": self.stages[stage_id]["name"],
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "data": initial_data or {},
            "metrics": {},
            "kpi_score": 0.0,
            "calculated_at": None,
            "created_at": datetime.now().isoformat(),
        }
        
        self.stage_instances[instance_id] = instance
        
        # 触发监听器
        self._notify_listeners("instance_created", instance)
        
        return {
            "success": True,
            "instance_id": instance_id,
            "instance": instance
        }
    
    def start_stage(
        self,
        instance_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动环节
        
        Args:
            instance_id: 实例ID
            data: 环节数据
            
        Returns:
            启动结果
        """
        if instance_id not in self.stage_instances:
            return {"success": False, "error": "实例不存在"}
        
        instance = self.stage_instances[instance_id]
        instance["status"] = "in_progress"
        instance["started_at"] = datetime.now().isoformat()
        
        if data:
            instance["data"].update(data)
        
        # 触发监听器
        self._notify_listeners("stage_started", instance)
        
        return {
            "success": True,
            "instance": instance
        }
    
    def update_stage_metrics(
        self,
        instance_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新环节指标
        
        Args:
            instance_id: 实例ID
            metrics: 指标数据
            
        Returns:
            更新结果
        """
        if instance_id not in self.stage_instances:
            return {"success": False, "error": "实例不存在"}
        
        instance = self.stage_instances[instance_id]
        instance["metrics"].update(metrics)
        instance["data"].update(metrics)
        
        # 自动试算
        calculator = self.calculators.get(instance["stage_id"])
        if calculator:
            kpi_score = calculator.calculate(instance["metrics"])
            instance["kpi_score"] = kpi_score
            instance["calculated_at"] = datetime.now().isoformat()
        
        # 触发监听器
        self._notify_listeners("metrics_updated", instance)
        
        return {
            "success": True,
            "instance": instance,
            "kpi_score": instance["kpi_score"]
        }
    
    def complete_stage(
        self,
        instance_id: str,
        final_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        完成环节
        
        Args:
            instance_id: 实例ID
            final_data: 最终数据
            
        Returns:
            完成结果
        """
        if instance_id not in self.stage_instances:
            return {"success": False, "error": "实例不存在"}
        
        instance = self.stage_instances[instance_id]
        instance["status"] = "completed"
        instance["completed_at"] = datetime.now().isoformat()
        
        if final_data:
            instance["data"].update(final_data)
        
        # 最终试算
        calculator = self.calculators.get(instance["stage_id"])
        if calculator:
            kpi_score = calculator.calculate(instance["metrics"])
            instance["kpi_score"] = kpi_score
            instance["calculated_at"] = datetime.now().isoformat()
        
        # 触发监听器
        self._notify_listeners("stage_completed", instance)
        
        return {
            "success": True,
            "instance": instance,
            "kpi_score": instance["kpi_score"]
        }
    
    def trial_calculate(
        self,
        stage_id: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        试算环节KPI
        
        Args:
            stage_id: 环节ID
            metrics: 指标数据
            
        Returns:
            试算结果
        """
        if stage_id not in self.stages:
            return {"success": False, "error": f"环节 {stage_id} 不存在"}
        
        calculator = self.calculators.get(stage_id)
        if not calculator:
            return {"success": False, "error": "试算器未初始化"}
        
        try:
            kpi_score = calculator.calculate(metrics)
            breakdown = calculator.get_breakdown(metrics)
            
            return {
                "success": True,
                "stage_id": stage_id,
                "stage_name": self.stages[stage_id]["name"],
                "kpi_score": kpi_score,
                "breakdown": breakdown,
                "formula": self.stages[stage_id]["kpi_formula"],
                "metrics_used": list(metrics.keys()),
            }
        except Exception as e:
            logger.error(f"Trial calculate failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stage_info(self, stage_id: str) -> Dict[str, Any]:
        """获取环节信息"""
        if stage_id not in self.stages:
            return {"success": False, "error": f"环节 {stage_id} 不存在"}
        
        config = self.stages[stage_id]
        instances = [
            inst for inst in self.stage_instances.values()
            if inst["stage_id"] == stage_id
        ]
        
        return {
            "success": True,
            "stage_id": stage_id,
            "config": config,
            "total_instances": len(instances),
            "active_instances": len([i for i in instances if i["status"] == "in_progress"]),
            "completed_instances": len([i for i in instances if i["status"] == "completed"]),
        }
    
    def get_all_stages(self) -> Dict[str, Any]:
        """获取所有环节信息"""
        stages_info = {}
        for stage_id, config in self.stages.items():
            stages_info[stage_id] = self.get_stage_info(stage_id)
        
        return {
            "success": True,
            "total_stages": len(self.stages),
            "stages": stages_info
        }
    
    def register_listener(self, listener: callable):
        """注册监听器"""
        self.listeners.append(listener)
    
    def _notify_listeners(self, event_type: str, data: Dict[str, Any]):
        """通知监听器"""
        for listener in self.listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Listener error: {e}")
    
    def export_stage_data(
        self,
        stage_id: Optional[str] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        导出环节数据
        
        Args:
            stage_id: 环节ID（None表示所有环节）
            format: 导出格式（json/csv/excel）
            
        Returns:
            导出数据
        """
        if stage_id:
            instances = [
                inst for inst in self.stage_instances.values()
                if inst["stage_id"] == stage_id
            ]
        else:
            instances = list(self.stage_instances.values())
        
        if format == "json":
            return {
                "success": True,
                "format": "json",
                "total": len(instances),
                "data": instances,
                "exported_at": datetime.now().isoformat(),
            }
        elif format == "csv":
            # CSV格式导出（简化版）
            csv_lines = []
            if instances:
                headers = list(instances[0].keys())
                csv_lines.append(",".join(headers))
                for inst in instances:
                    values = [str(inst.get(h, "")) for h in headers]
                    csv_lines.append(",".join(values))
            
            return {
                "success": True,
                "format": "csv",
                "total": len(instances),
                "data": "\n".join(csv_lines),
                "exported_at": datetime.now().isoformat(),
            }
        else:
            return {"success": False, "error": f"不支持的格式: {format}"}


class StageCalculator:
    """环节试算器"""
    
    def __init__(self, stage_id: str, formula: str, metrics: List[str]):
        self.stage_id = stage_id
        self.formula = formula
        self.metrics = metrics
    
    def calculate(self, metrics: Dict[str, Any]) -> float:
        """
        计算KPI分数
        
        Args:
            metrics: 指标数据
            
        Returns:
            KPI分数
        """
        try:
            # 安全执行公式
            safe_dict = {k: float(v) if isinstance(v, (int, float)) else 0.0 for k, v in metrics.items()}
            safe_dict.update({
                "True": 1.0,
                "False": 0.0,
                "true": 1.0,
                "false": 0.0,
            })
            
            # 处理布尔值
            for k, v in metrics.items():
                if isinstance(v, bool):
                    safe_dict[k] = 1.0 if v else 0.0
            
            result = eval(self.formula, {"__builtins__": {}}, safe_dict)
            return round(float(result), 2)
        except Exception as e:
            logger.error(f"Calculate error: {e}, formula: {self.formula}, metrics: {metrics}")
            return 0.0
    
    def get_breakdown(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """获取计算分解"""
        breakdown = {}
        for metric in self.metrics:
            if metric in metrics:
                breakdown[metric] = metrics[metric]
        return breakdown


# 全局实例
erp_11_stages_manager = ERP11StagesManager()

