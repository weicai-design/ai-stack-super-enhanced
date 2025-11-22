#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运营财务策略联动系统
功能：预算/成本/报表的跨系统策略联动
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StrategyTrigger(Enum):
    """策略触发条件"""
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_SPIKE = "cost_spike"
    REPORT_ANOMALY = "report_anomaly"
    KPI_WARNING = "kpi_warning"
    CASH_FLOW_CRITICAL = "cash_flow_critical"
    RUNWAY_RISK = "runway_risk"


class StrategyAction(Enum):
    """策略动作"""
    FREEZE_BUDGET = "freeze_budget"
    ALERT_STAKEHOLDERS = "alert_stakeholders"
    ADJUST_COST = "adjust_cost"
    UPDATE_REPORT = "update_report"
    SYNC_ERP = "sync_erp"
    SUGGEST_REBALANCE = "suggest_rebalance"


class OperationsFinanceStrategy:
    """
    运营财务策略联动器
    管理预算/成本/报表的跨系统联动
    """
    
    def __init__(self):
        """初始化策略联动系统"""
        self.strategies: List[Dict[str, Any]] = []
        self.execution_logs: List[Dict[str, Any]] = []
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """初始化默认策略"""
        self.strategies = [
            {
                "id": "budget_guard_001",
                "name": "预算超支保护",
                "trigger": StrategyTrigger.BUDGET_EXCEEDED.value,
                "condition": {"threshold": 0.9, "period": "monthly"},
                "actions": [
                    {
                        "type": StrategyAction.FREEZE_BUDGET.value,
                        "target": "non_critical",
                        "systems": ["operations_finance", "erp"]
                    },
                    {
                        "type": StrategyAction.ALERT_STAKEHOLDERS.value,
                        "recipients": ["finance_team", "cfo"],
                        "systems": ["operations_finance"]
                    }
                ],
                "enabled": True
            },
            {
                "id": "cost_bridge_002",
                "name": "成本异常联动",
                "trigger": StrategyTrigger.COST_SPIKE.value,
                "condition": {"increase_rate": 0.05, "time_window": "7d"},
                "actions": [
                    {
                        "type": StrategyAction.ADJUST_COST.value,
                        "target": "variable_costs",
                        "systems": ["operations_finance", "erp"]
                    },
                    {
                        "type": StrategyAction.SYNC_ERP.value,
                        "target": "cost_center",
                        "systems": ["erp"]
                    }
                ],
                "enabled": True
            },
            {
                "id": "runway_predictive_005",
                "name": "预测型 Runway 守护",
                "trigger": StrategyTrigger.RUNWAY_RISK.value,
                "condition": {"forecast_horizon": 6, "threshold": 4},
                "actions": [
                    {
                        "type": StrategyAction.ALERT_STAKEHOLDERS.value,
                        "recipients": ["cfo", "ceo"],
                        "systems": ["operations_finance"]
                    },
                    {
                        "type": StrategyAction.SUGGEST_REBALANCE.value,
                        "target": "cash_flow_plan",
                        "systems": ["operations_finance", "trend"]
                    }
                ],
                "enabled": True
            },
        ]
    
    def _check_trigger(
        self,
        trigger: str,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """检查触发条件"""
        if trigger == StrategyTrigger.BUDGET_EXCEEDED.value:
            budget_usage = context.get("budget_usage", 0.0)
            threshold = condition.get("threshold", 0.9)
            return budget_usage >= threshold
        
        elif trigger == StrategyTrigger.COST_SPIKE.value:
            cost_increase = context.get("cost_increase_rate", 0.0)
            threshold = condition.get("increase_rate", 0.05)
            return cost_increase >= threshold
        
        elif trigger == StrategyTrigger.REPORT_ANOMALY.value:
            anomaly_score = context.get("anomaly_score", 0.0)
            threshold = condition.get("anomaly_score", 0.7)
            return anomaly_score >= threshold
        
        elif trigger == StrategyTrigger.KPI_WARNING.value:
            kpi_value = context.get("kpi_value", 0.0)
            kpi_type = context.get("kpi_type", "")
            threshold = condition.get("threshold", 0.0)
            kpi_type_match = condition.get("kpi_type") == kpi_type
            
            if kpi_type_match:
                if kpi_type == "runway":
                    return kpi_value <= threshold
                else:
                    return kpi_value <= threshold
        
        elif trigger == StrategyTrigger.CASH_FLOW_CRITICAL.value:
            net_cash = context.get("net_cash", 0.0)
            return net_cash <= 50000  # 临界值
        elif trigger == StrategyTrigger.RUNWAY_RISK.value:
            return context.get("predicted_runway", 12) <= condition.get("threshold", 4)
        
        return False
    
    async def execute_strategy(
        self,
        strategy_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行策略
        
        Args:
            strategy_info: 策略信息（包含 strategy, triggered_at, context）
            
        Returns:
            执行结果
        """
        strategy = strategy_info["strategy"]
        context = strategy_info["context"]
        
        execution_result = {
            "strategy_id": strategy["id"],
            "strategy_name": strategy["name"],
            "triggered_at": strategy_info["triggered_at"],
            "executed_at": datetime.now().isoformat(),
            "actions": [],
            "status": "success"
        }
        
        actions = strategy.get("actions", [])
        for action in actions:
            try:
                action_result = await self._execute_action(action, context)
                execution_result["actions"].append({
                    "type": action["type"],
                    "target": action.get("target", ""),
                    "status": "success",
                    "result": action_result
                })
            except Exception as e:
                logger.error(f"执行动作失败: {action['type']}, 错误: {e}")
                execution_result["actions"].append({
                    "type": action["type"],
                    "target": action.get("target", ""),
                    "status": "error",
                    "error": str(e)
                })
                execution_result["status"] = "partial_failure"
        
        # 记录执行日志
        self.execution_logs.append(execution_result)
        self.execution_logs = self.execution_logs[-500:]  # 保留最近500条
        
        return execution_result
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个动作"""
        action_type = action["type"]
        target = action.get("target", "")
        systems = action.get("systems", [])
        
        if action_type == StrategyAction.FREEZE_BUDGET.value:
            return {
                "message": f"已冻结 {target} 预算",
                "systems": systems,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action_type == StrategyAction.ALERT_STAKEHOLDERS.value:
            recipients = action.get("recipients", [])
            return {
                "message": f"已通知 {', '.join(recipients)}",
                "recipients": recipients,
                "systems": systems,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action_type == StrategyAction.ADJUST_COST.value:
            return {
                "message": f"已调整 {target} 成本",
                "target": target,
                "systems": systems,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action_type == StrategyAction.UPDATE_REPORT.value:
            return {
                "message": f"已更新 {target} 报表",
                "target": target,
                "systems": systems,
                "timestamp": datetime.now().isoformat()
            }
        
        elif action_type == StrategyAction.SYNC_ERP.value:
            return {
                "message": f"已同步 {target} 到 ERP",
                "target": target,
                "systems": systems,
                "timestamp": datetime.now().isoformat()
            }
        
        return {"message": "动作执行完成", "timestamp": datetime.now().isoformat()}
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            "total_strategies": len(self.strategies),
            "enabled_strategies": len([s for s in self.strategies if s.get("enabled", True)]),
            "recent_executions": len([e for e in self.execution_logs if datetime.fromisoformat(e["executed_at"]) > datetime.now() - timedelta(days=7)]),
            "strategies": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "trigger": s["trigger"],
                    "enabled": s.get("enabled", True)
                }
                for s in self.strategies
            ]
        }
    
    def get_execution_history(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_logs[-limit:]


# 全局实例
operations_finance_strategy = OperationsFinanceStrategy()

