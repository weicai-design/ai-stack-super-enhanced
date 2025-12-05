#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证监控器

功能：
1. 实时监控工作流执行状态
2. 验证双线闭环工作流的完整性
3. 收集性能指标和错误统计
4. 生成验证报告
5. 提供实时告警机制
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """验证状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    UNKNOWN = "unknown"


class ValidationMetric(str, Enum):
    """验证指标"""
    RESPONSE_TIME = "response_time"
    STEP_COMPLETION = "step_completion"
    RAG_CALLS = "rag_calls"
    EXPERT_ROUTING = "expert_routing"
    MODULE_EXECUTION = "module_execution"
    ERROR_RATE = "error_rate"


@dataclass
class WorkflowValidationResult:
    """工作流验证结果"""
    workflow_id: str
    workflow_type: str
    user_input: str
    status: ValidationStatus
    duration_seconds: float
    steps_count: int
    successful_steps: int
    rag_calls: int
    validation_details: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class ValidationAlert:
    """验证告警"""
    alert_id: str
    alert_type: str
    severity: str  # "critical", "warning", "info"
    message: str
    workflow_id: Optional[str] = None
    metric: Optional[str] = None
    threshold: Optional[float] = None
    actual_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


class WorkflowValidationMonitor:
    """工作流验证监控器"""
    
    def __init__(self, validation_thresholds: Optional[Dict[str, float]] = None):
        """
        初始化监控器
        
        Args:
            validation_thresholds: 验证阈值配置
        """
        self.validation_results: List[WorkflowValidationResult] = []
        self.alerts: List[ValidationAlert] = []
        self.metrics_history: Dict[str, List[float]] = {}
        
        # 默认验证阈值
        self.thresholds = validation_thresholds or {
            "response_time_max": 2.0,  # 最大响应时间（秒）
            "step_completion_min": 0.8,  # 最小步骤完成率
            "rag_calls_min": 2,  # 最小RAG调用次数
            "error_rate_max": 0.1,  # 最大错误率
        }
        
        # 告警回调函数
        self.alert_callbacks: List[Callable[[ValidationAlert], None]] = []
    
    def validate_workflow_execution(self, execution_result: Dict[str, Any]) -> WorkflowValidationResult:
        """验证工作流执行结果"""
        workflow_id = execution_result.get("workflow_id", "unknown")
        workflow_type = execution_result.get("workflow_type", "unknown")
        user_input = execution_result.get("user_input", "")
        duration = execution_result.get("duration_seconds", 0.0)
        
        # 收集验证详情
        validation_details = self._collect_validation_details(execution_result)
        
        # 执行验证
        validation_status = self._perform_validation(execution_result, validation_details)
        
        # 创建验证结果
        result = WorkflowValidationResult(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            user_input=user_input,
            status=validation_status,
            duration_seconds=duration,
            steps_count=validation_details.get("steps_count", 0),
            successful_steps=validation_details.get("successful_steps", 0),
            rag_calls=validation_details.get("rag_calls", 0),
            validation_details=validation_details,
            timestamp=datetime.now(),
            error=execution_result.get("error"),
            trace_id=execution_result.get("trace_id"),
        )
        
        # 记录验证结果
        self.validation_results.append(result)
        
        # 检查是否需要告警
        self._check_for_alerts(result)
        
        # 更新指标历史
        self._update_metrics_history(result)
        
        return result
    
    def _collect_validation_details(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """收集验证详情"""
        details = {}
        
        # 步骤统计
        steps = execution_result.get("steps", [])
        details["steps_count"] = len(steps)
        details["successful_steps"] = sum(1 for step in steps if step.get("success", False))
        
        # RAG调用统计
        rag_calls = sum(1 for step in steps 
                       if step.get("step_type", "") in ["rag_retrieval_1", "rag_retrieval_2"])
        details["rag_calls"] = rag_calls
        
        # 专家路由统计
        expert_routing_calls = sum(1 for step in steps 
                                  if step.get("step_type", "") in ["expert_routing_1", "expert_routing_2"])
        details["expert_routing_calls"] = expert_routing_calls
        
        # 模块执行统计
        module_execution_calls = sum(1 for step in steps 
                                    if step.get("step_type", "") == "module_execution")
        details["module_execution_calls"] = module_execution_calls
        
        # 响应生成统计
        response_generation_calls = sum(1 for step in steps 
                                       if step.get("step_type", "") == "response_generation")
        details["response_generation_calls"] = response_generation_calls
        
        return details
    
    def _perform_validation(self, execution_result: Dict[str, Any], 
                           validation_details: Dict[str, Any]) -> ValidationStatus:
        """执行验证"""
        failed_checks = 0
        warning_checks = 0
        
        # 检查响应时间
        duration = execution_result.get("duration_seconds", 0.0)
        if duration > self.thresholds["response_time_max"]:
            failed_checks += 1
        elif duration > self.thresholds["response_time_max"] * 0.8:
            warning_checks += 1
        
        # 检查步骤完成率
        steps_count = validation_details.get("steps_count", 0)
        successful_steps = validation_details.get("successful_steps", 0)
        if steps_count > 0:
            completion_rate = successful_steps / steps_count
            if completion_rate < self.thresholds["step_completion_min"]:
                failed_checks += 1
            elif completion_rate < self.thresholds["step_completion_min"] + 0.1:
                warning_checks += 1
        
        # 检查RAG调用次数
        rag_calls = validation_details.get("rag_calls", 0)
        if rag_calls < self.thresholds["rag_calls_min"]:
            failed_checks += 1
        
        # 检查错误率
        if execution_result.get("error"):
            failed_checks += 1
        
        # 确定验证状态
        if failed_checks > 0:
            return ValidationStatus.FAILED
        elif warning_checks > 0:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED
    
    def _check_for_alerts(self, result: WorkflowValidationResult):
        """检查是否需要告警"""
        
        # 响应时间告警
        if result.duration_seconds > self.thresholds["response_time_max"]:
            self._create_alert(
                alert_type="response_time_exceeded",
                severity="critical",
                message=f"工作流响应时间超过阈值: {result.duration_seconds:.3f}秒 > {self.thresholds['response_time_max']}秒",
                workflow_id=result.workflow_id,
                metric="response_time",
                threshold=self.thresholds["response_time_max"],
                actual_value=result.duration_seconds,
            )
        
        # 步骤完成率告警
        if result.steps_count > 0:
            completion_rate = result.successful_steps / result.steps_count
            if completion_rate < self.thresholds["step_completion_min"]:
                self._create_alert(
                    alert_type="step_completion_low",
                    severity="critical",
                    message=f"步骤完成率过低: {completion_rate:.1%} < {self.thresholds['step_completion_min']:.1%}",
                    workflow_id=result.workflow_id,
                    metric="step_completion",
                    threshold=self.thresholds["step_completion_min"],
                    actual_value=completion_rate,
                )
        
        # RAG调用次数告警
        if result.rag_calls < self.thresholds["rag_calls_min"]:
            self._create_alert(
                alert_type="rag_calls_insufficient",
                severity="warning",
                message=f"RAG调用次数不足: {result.rag_calls} < {self.thresholds['rag_calls_min']}",
                workflow_id=result.workflow_id,
                metric="rag_calls",
                threshold=self.thresholds["rag_calls_min"],
                actual_value=result.rag_calls,
            )
    
    def _create_alert(self, alert_type: str, severity: str, message: str, 
                     workflow_id: Optional[str] = None, metric: Optional[str] = None,
                     threshold: Optional[float] = None, actual_value: Optional[float] = None):
        """创建告警"""
        alert = ValidationAlert(
            alert_id=f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            workflow_id=workflow_id,
            metric=metric,
            threshold=threshold,
            actual_value=actual_value,
        )
        
        self.alerts.append(alert)
        
        # 调用告警回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调函数执行失败: {e}")
    
    def _update_metrics_history(self, result: WorkflowValidationResult):
        """更新指标历史"""
        metrics_to_update = {
            "response_time": result.duration_seconds,
            "step_completion": result.successful_steps / result.steps_count if result.steps_count > 0 else 0,
            "rag_calls": result.rag_calls,
        }
        
        for metric_name, value in metrics_to_update.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
            
            # 保持最近100个数据点
            if len(self.metrics_history[metric_name]) >= 100:
                self.metrics_history[metric_name].pop(0)
            
            self.metrics_history[metric_name].append(value)
    
    def get_validation_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """获取验证摘要"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        recent_results = [
            r for r in self.validation_results 
            if r.timestamp >= cutoff_time
        ]
        
        if not recent_results:
            return {
                "total_validations": 0,
                "pass_rate": 0.0,
                "average_response_time": 0.0,
                "alerts_count": len(self.alerts),
            }
        
        # 计算通过率
        passed_count = sum(1 for r in recent_results if r.status == ValidationStatus.PASSED)
        pass_rate = passed_count / len(recent_results)
        
        # 计算平均响应时间
        avg_response_time = statistics.mean([r.duration_seconds for r in recent_results])
        
        # 获取最近告警
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        
        return {
            "total_validations": len(recent_results),
            "pass_rate": pass_rate,
            "average_response_time": avg_response_time,
            "alerts_count": len(recent_alerts),
            "critical_alerts": len([a for a in recent_alerts if a.severity == "critical"]),
            "warning_alerts": len([a for a in recent_alerts if a.severity == "warning"]),
            "timestamp": datetime.now().isoformat(),
        }
    
    def add_alert_callback(self, callback: Callable[[ValidationAlert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def clear_alerts(self):
        """清空告警"""
        self.alerts.clear()
    
    def export_validation_report(self, file_path: Path) -> None:
        """导出验证报告"""
        report = {
            "summary": self.get_validation_summary(),
            "recent_results": [
                {
                    "workflow_id": r.workflow_id,
                    "status": r.status.value,
                    "duration_seconds": r.duration_seconds,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.validation_results[-50:]  # 最近50个结果
            ],
            "recent_alerts": [
                {
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in self.alerts[-20:]  # 最近20个告警
            ],
            "export_timestamp": datetime.now().isoformat(),
        }
        
        file_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


# 全局监控器实例
_global_monitor: Optional[WorkflowValidationMonitor] = None


def get_workflow_validation_monitor() -> WorkflowValidationMonitor:
    """获取全局工作流验证监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = WorkflowValidationMonitor()
    return _global_monitor


def validate_workflow_execution(execution_result: Dict[str, Any]) -> WorkflowValidationResult:
    """验证工作流执行结果（便捷函数）"""
    monitor = get_workflow_validation_monitor()
    return monitor.validate_workflow_execution(execution_result)