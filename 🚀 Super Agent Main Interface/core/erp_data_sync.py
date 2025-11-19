#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 数据同步机制
功能：运营财务系统与ERP系统的数据同步
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """同步方向"""
    TO_ERP = "to_erp"  # 运营财务 -> ERP
    FROM_ERP = "from_erp"  # ERP -> 运营财务
    BIDIRECTIONAL = "bidirectional"  # 双向同步


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ERPDataSync:
    """
    ERP 数据同步器
    管理运营财务系统与ERP系统的数据同步
    """
    
    def __init__(self):
        """初始化同步器"""
        self.sync_configs: Dict[str, Dict[str, Any]] = {
            "budget": {
                "direction": SyncDirection.BIDIRECTIONAL.value,
                "frequency": "daily",
                "fields": ["budget_amount", "budget_category", "budget_period", "budget_status"],
                "mapping": {
                    "operations_finance": "budget_amount",
                    "erp": "budget_plan_amount"
                }
            },
            "cost": {
                "direction": SyncDirection.TO_ERP.value,
                "frequency": "realtime",
                "fields": ["cost_amount", "cost_category", "cost_date", "cost_center"],
                "mapping": {
                    "operations_finance": "cost_amount",
                    "erp": "actual_cost"
                }
            },
            "financial_report": {
                "direction": SyncDirection.BIDIRECTIONAL.value,
                "frequency": "weekly",
                "fields": ["report_type", "report_period", "report_data", "report_status"],
                "mapping": {
                    "operations_finance": "report_data",
                    "erp": "financial_report_data"
                }
            },
            "kpi": {
                "direction": SyncDirection.TO_ERP.value,
                "frequency": "daily",
                "fields": ["kpi_name", "kpi_value", "kpi_period", "kpi_status"],
                "mapping": {
                    "operations_finance": "kpi_value",
                    "erp": "performance_indicator_value"
                }
            },
        }
        
        self.sync_logs: List[Dict[str, Any]] = []
        self.last_sync_times: Dict[str, str] = {}
    
    async def sync_data(
        self,
        data_type: str,
        data: Dict[str, Any],
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        同步数据
        
        Args:
            data_type: 数据类型（budget/cost/financial_report/kpi）
            data: 数据内容
            direction: 同步方向（可选，默认使用配置）
            
        Returns:
            同步结果
        """
        if data_type not in self.sync_configs:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        config = self.sync_configs[data_type]
        sync_direction = direction or config["direction"]
        
        sync_log = {
            "data_type": data_type,
            "direction": sync_direction,
            "status": SyncStatus.IN_PROGRESS.value,
            "started_at": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            if sync_direction == SyncDirection.TO_ERP.value:
                result = await self._sync_to_erp(data_type, data, config)
            elif sync_direction == SyncDirection.FROM_ERP.value:
                result = await self._sync_from_erp(data_type, data, config)
            elif sync_direction == SyncDirection.BIDIRECTIONAL.value:
                # 双向同步：先同步到ERP，再从ERP同步回来
                result_to = await self._sync_to_erp(data_type, data, config)
                result_from = await self._sync_from_erp(data_type, data, config)
                result = {
                    "to_erp": result_to,
                    "from_erp": result_from
                }
            else:
                raise ValueError(f"不支持的同步方向: {sync_direction}")
            
            sync_log["status"] = SyncStatus.SUCCESS.value
            sync_log["result"] = result
            sync_log["completed_at"] = datetime.now().isoformat()
            
            # 更新最后同步时间
            self.last_sync_times[data_type] = sync_log["completed_at"]
            
        except Exception as e:
            logger.error(f"数据同步失败: {data_type}, 错误: {e}")
            sync_log["status"] = SyncStatus.FAILED.value
            sync_log["error"] = str(e)
            sync_log["completed_at"] = datetime.now().isoformat()
        
        # 记录同步日志
        self.sync_logs.append(sync_log)
        self.sync_logs = self.sync_logs[-1000:]  # 保留最近1000条
        
        return sync_log
    
    async def _sync_to_erp(
        self,
        data_type: str,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """同步数据到ERP"""
        mapping = config.get("mapping", {})
        fields = config.get("fields", [])
        
        # 数据转换
        erp_data = {}
        for field in fields:
            if field in data:
                # 使用映射规则转换字段名
                erp_field = mapping.get("erp", field)
                erp_data[erp_field] = data[field]
        
        # TODO: 真实实现应调用ERP API
        # import httpx
        # response = await httpx.post(f"https://erp-api.example.com/sync/{data_type}", json=erp_data)
        # return response.json()
        
        # 模拟实现
        return {
            "success": True,
            "message": f"数据已同步到ERP: {data_type}",
            "erp_data": erp_data,
            "timestamp": datetime.now().isoformat(),
            "note": "真实实现需要调用ERP API"
        }
    
    async def _sync_from_erp(
        self,
        data_type: str,
        data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从ERP同步数据"""
        mapping = config.get("mapping", {})
        fields = config.get("fields", [])
        
        # TODO: 真实实现应从ERP API获取数据
        # import httpx
        # response = await httpx.get(f"https://erp-api.example.com/sync/{data_type}")
        # erp_data = response.json()
        
        # 模拟实现
        erp_data = {
            "erp_field": "erp_value"
        }
        
        # 数据转换
        operations_data = {}
        for field in fields:
            erp_field = mapping.get("erp", field)
            if erp_field in erp_data:
                operations_data[field] = erp_data[erp_field]
        
        return {
            "success": True,
            "message": f"数据已从ERP同步: {data_type}",
            "operations_data": operations_data,
            "timestamp": datetime.now().isoformat(),
            "note": "真实实现需要调用ERP API"
        }
    
    def get_sync_status(
        self,
        data_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取同步状态
        
        Args:
            data_type: 数据类型（None表示全部）
            
        Returns:
            同步状态
        """
        if data_type:
            config = self.sync_configs.get(data_type, {})
            last_sync = self.last_sync_times.get(data_type)
            
            # 统计最近同步记录
            recent_logs = [
                log for log in self.sync_logs[-100:]
                if log["data_type"] == data_type
            ]
            
            success_count = len([log for log in recent_logs if log["status"] == SyncStatus.SUCCESS.value])
            failed_count = len([log for log in recent_logs if log["status"] == SyncStatus.FAILED.value])
            
            return {
                "data_type": data_type,
                "direction": config.get("direction"),
                "frequency": config.get("frequency"),
                "last_sync": last_sync,
                "recent_success": success_count,
                "recent_failed": failed_count,
                "success_rate": round(success_count / len(recent_logs) * 100, 2) if recent_logs else 0.0
            }
        
        # 全部数据类型状态
        status_summary = {}
        for dt in self.sync_configs.keys():
            status_summary[dt] = self.get_sync_status(dt)
        
        return {
            "total_types": len(self.sync_configs),
            "status_by_type": status_summary
        }
    
    def get_sync_history(
        self,
        data_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取同步历史
        
        Args:
            data_type: 数据类型（None表示全部）
            limit: 返回数量限制
            
        Returns:
            同步历史记录
        """
        logs = self.sync_logs[-limit:]
        
        if data_type:
            logs = [log for log in logs if log["data_type"] == data_type]
        
        return logs
    
    def update_sync_config(
        self,
        data_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新同步配置
        
        Args:
            data_type: 数据类型
            config: 新配置
            
        Returns:
            更新后的配置
        """
        if data_type not in self.sync_configs:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        # 合并配置
        self.sync_configs[data_type].update(config)
        
        return self.sync_configs[data_type]


# 全局实例
erp_data_sync = ERPDataSync()

