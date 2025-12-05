#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证器（T003）

功能：
1. 验证系统各模块响应时间是否满足2秒SLO要求
2. 提供实时性能监控和告警机制
3. 生成性能报告和优化建议
4. 支持历史性能数据分析和趋势预测

验收标准：
- 所有关键API接口响应时间≤2秒
- 性能监控覆盖率达到100%
- 实时告警机制正常工作
- 性能报告包含详细分析和优化建议
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import statistics
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceStatus(Enum):
    """性能状态枚举"""
    WITHIN_SLO = "within_slo"  # 满足SLO要求
    WARNING = "warning"  # 接近SLO限制
    VIOLATION = "violation"  # 违反SLO要求
    UNKNOWN = "unknown"  # 未知状态


class ModuleType(Enum):
    """模块类型枚举"""
    WORKFLOW = "workflow"
    RAG = "rag"
    ERP = "erp"
    CONTENT_CREATION = "content_creation"
    TREND_ANALYSIS = "trend_analysis"
    STOCK_QUANT = "stock_quant"
    FINANCE = "finance"
    AI_PROGRAMMING = "ai_programming"
    TASK_SYSTEM = "task_system"
    LEARNING_SYSTEM = "learning_system"
    RESOURCE_MANAGEMENT = "resource_management"


@dataclass
class PerformanceMetric:
    """性能指标"""
    module: ModuleType
    operation: str
    response_time: float  # 响应时间（秒）
    status: PerformanceStatus
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "module": self.module.value,
            "operation": self.operation,
            "response_time": self.response_time,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class SLOValidationResult:
    """SLO验证结果"""
    module: ModuleType
    operation: str
    response_time: float
    slo_threshold: float = 2.0  # 2秒SLO
    status: PerformanceStatus = PerformanceStatus.UNKNOWN
    is_within_slo: bool = False
    violation_severity: float = 0.0  # 违反严重程度（0-1）
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "module": self.module.value,
            "operation": self.operation,
            "response_time": self.response_time,
            "slo_threshold": self.slo_threshold,
            "status": self.status.value,
            "is_within_slo": self.is_within_slo,
            "violation_severity": self.violation_severity,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


@dataclass
class PerformanceReport:
    """性能报告"""
    period_start: str
    period_end: str
    total_operations: int
    operations_within_slo: int
    operations_violated_slo: int
    overall_slo_compliance: float  # SLO合规率（0-1）
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    module_performance: Dict[str, Dict[str, Any]]
    critical_violations: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_operations": self.total_operations,
            "operations_within_slo": self.operations_within_slo,
            "operations_violated_slo": self.operations_violated_slo,
            "overall_slo_compliance": self.overall_slo_compliance,
            "average_response_time": self.average_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "module_performance": self.module_performance,
            "critical_violations": self.critical_violations,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }


class SLOPerformanceValidator:
    """
    2秒SLO性能验证器
    
    实现完整的性能监控和SLO验证机制
    """
    
    def __init__(self, slo_threshold: float = 2.0, history_size: int = 1000):
        """
        初始化验证器
        
        Args:
            slo_threshold: SLO阈值（秒）
            history_size: 历史数据大小
        """
        self.slo_threshold = slo_threshold
        self.performance_history: deque[PerformanceMetric] = deque(maxlen=history_size)
        self.alerts: List[Dict[str, Any]] = []
        
        # 性能配置
        self.performance_config = {
            ModuleType.WORKFLOW: {
                "critical_operations": ["execute", "validate", "monitor"],
                "warning_threshold": 1.5,  # 警告阈值
            },
            ModuleType.RAG: {
                "critical_operations": ["retrieve", "retrieve_for_integration"],
                "warning_threshold": 1.5,
            },
            ModuleType.ERP: {
                "critical_operations": ["analyze", "process", "report"],
                "warning_threshold": 1.8,
            },
            # 其他模块配置...
        }
        
        # 默认配置
        self.default_config = {
            "warning_threshold": 1.7,
            "critical_operations": [],
        }
    
    async def validate_operation_performance(
        self,
        module: ModuleType,
        operation: str,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> SLOValidationResult:
        """
        验证操作性能
        
        Args:
            module: 模块类型
            operation: 操作名称
            operation_func: 操作函数
            *args, **kwargs: 操作函数参数
            
        Returns:
            SLO验证结果
        """
        start_time = time.time()
        
        try:
            # 执行操作
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)
            
            response_time = time.time() - start_time
            
            # 验证SLO合规性
            validation_result = self._validate_slo_compliance(
                module, operation, response_time
            )
            
            # 记录性能指标
            metric = PerformanceMetric(
                module=module,
                operation=operation,
                response_time=response_time,
                status=validation_result.status,
                metadata={
                    "result_type": type(result).__name__,
                    "success": True,
                }
            )
            self.performance_history.append(metric)
            
            # 检查是否需要告警
            await self._check_alerts(metric)
            
            return validation_result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # 记录错误性能指标
            metric = PerformanceMetric(
                module=module,
                operation=operation,
                response_time=response_time,
                status=PerformanceStatus.VIOLATION,
                metadata={
                    "error": str(e),
                    "success": False,
                }
            )
            self.performance_history.append(metric)
            
            # 生成错误验证结果
            return SLOValidationResult(
                module=module,
                operation=operation,
                response_time=response_time,
                status=PerformanceStatus.VIOLATION,
                is_within_slo=False,
                violation_severity=1.0,
                recommendations=[f"操作执行失败: {str(e)}"],
            )
    
    def _validate_slo_compliance(
        self, module: ModuleType, operation: str, response_time: float
    ) -> SLOValidationResult:
        """验证SLO合规性"""
        # 获取模块配置
        config = self.performance_config.get(module, self.default_config)
        warning_threshold = config.get("warning_threshold", self.default_config["warning_threshold"])
        
        # 确定性能状态
        if response_time <= self.slo_threshold:
            status = PerformanceStatus.WITHIN_SLO
            is_within_slo = True
            violation_severity = 0.0
        elif response_time <= warning_threshold:
            status = PerformanceStatus.WARNING
            is_within_slo = False
            violation_severity = (response_time - self.slo_threshold) / (warning_threshold - self.slo_threshold)
        else:
            status = PerformanceStatus.VIOLATION
            is_within_slo = False
            violation_severity = min(1.0, (response_time - self.slo_threshold) / self.slo_threshold)
        
        # 生成优化建议
        recommendations = self._generate_recommendations(
            module, operation, response_time, status
        )
        
        return SLOValidationResult(
            module=module,
            operation=operation,
            response_time=response_time,
            status=status,
            is_within_slo=is_within_slo,
            violation_severity=violation_severity,
            recommendations=recommendations,
        )
    
    def _generate_recommendations(
        self, module: ModuleType, operation: str, response_time: float, status: PerformanceStatus
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if status == PerformanceStatus.WITHIN_SLO:
            if response_time > self.slo_threshold * 0.8:
                recommendations.append("响应时间接近SLO限制，建议进行性能优化")
        elif status == PerformanceStatus.WARNING:
            recommendations.append("响应时间超过SLO限制，需要立即优化")
            
            # 模块特定建议
            if module == ModuleType.RAG:
                recommendations.extend([
                    "优化RAG检索算法",
                    "增加缓存机制",
                    "考虑使用更快的向量数据库"
                ])
            elif module == ModuleType.WORKFLOW:
                recommendations.extend([
                    "优化工作流执行逻辑",
                    "减少不必要的验证步骤",
                    "并行化处理任务"
                ])
        elif status == PerformanceStatus.VIOLATION:
            recommendations.append("严重违反SLO要求，需要紧急优化")
            
            # 根据违反程度提供建议
            if response_time > self.slo_threshold * 2:
                recommendations.append("考虑重构该模块或使用更高效的技术方案")
        
        return recommendations
    
    async def _check_alerts(self, metric: PerformanceMetric):
        """检查是否需要告警"""
        if metric.status == PerformanceStatus.VIOLATION:
            alert = {
                "type": "slo_violation",
                "module": metric.module.value,
                "operation": metric.operation,
                "response_time": metric.response_time,
                "severity": "critical",
                "timestamp": metric.timestamp,
                "message": f"{metric.module.value}.{metric.operation} 违反2秒SLO要求: {metric.response_time:.2f}秒"
            }
            self.alerts.append(alert)
            logger.warning(alert["message"])
        
        elif metric.status == PerformanceStatus.WARNING:
            alert = {
                "type": "slo_warning",
                "module": metric.module.value,
                "operation": metric.operation,
                "response_time": metric.response_time,
                "severity": "warning",
                "timestamp": metric.timestamp,
                "message": f"{metric.module.value}.{metric.operation} 接近SLO限制: {metric.response_time:.2f}秒"
            }
            self.alerts.append(alert)
            logger.warning(alert["message"])
    
    async def generate_performance_report(
        self, hours: int = 24
    ) -> PerformanceReport:
        """
        生成性能报告
        
        Args:
            hours: 报告时间范围（小时）
            
        Returns:
            性能报告
        """
        # 计算时间范围
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # 过滤指定时间范围内的性能指标
        recent_metrics = [
            metric for metric in self.performance_history
            if start_time <= datetime.fromisoformat(metric.timestamp.replace('Z', '+00:00')) <= end_time
        ]
        
        if not recent_metrics:
            return self._generate_empty_report(start_time, end_time)
        
        # 计算总体统计信息
        response_times = [metric.response_time for metric in recent_metrics]
        within_slo_count = sum(1 for metric in recent_metrics 
                              if metric.status == PerformanceStatus.WITHIN_SLO)
        violated_slo_count = sum(1 for metric in recent_metrics 
                                if metric.status == PerformanceStatus.VIOLATION)
        
        # 计算百分位数
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)
        
        # 按模块分析性能
        module_performance = {}
        for module in ModuleType:
            module_metrics = [m for m in recent_metrics if m.module == module]
            if module_metrics:
                module_times = [m.response_time for m in module_metrics]
                module_within_slo = sum(1 for m in module_metrics 
                                      if m.status == PerformanceStatus.WITHIN_SLO)
                
                module_performance[module.value] = {
                    "total_operations": len(module_metrics),
                    "within_slo_count": module_within_slo,
                    "slo_compliance_rate": module_within_slo / len(module_metrics),
                    "avg_response_time": statistics.mean(module_times),
                    "max_response_time": max(module_times),
                    "min_response_time": min(module_times),
                }
        
        # 识别关键违反
        critical_violations = [
            metric.to_dict() for metric in recent_metrics
            if metric.status == PerformanceStatus.VIOLATION 
            and metric.response_time > self.slo_threshold * 1.5
        ]
        
        # 生成优化建议
        recommendations = self._generate_report_recommendations(recent_metrics)
        
        return PerformanceReport(
            period_start=start_time.isoformat() + "Z",
            period_end=end_time.isoformat() + "Z",
            total_operations=len(recent_metrics),
            operations_within_slo=within_slo_count,
            operations_violated_slo=violated_slo_count,
            overall_slo_compliance=within_slo_count / len(recent_metrics),
            average_response_time=statistics.mean(response_times),
            p95_response_time=sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1],
            p99_response_time=sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1],
            module_performance=module_performance,
            critical_violations=critical_violations,
            recommendations=recommendations,
        )
    
    def _generate_empty_report(self, start_time: datetime, end_time: datetime) -> PerformanceReport:
        """生成空报告"""
        return PerformanceReport(
            period_start=start_time.isoformat() + "Z",
            period_end=end_time.isoformat() + "Z",
            total_operations=0,
            operations_within_slo=0,
            operations_violated_slo=0,
            overall_slo_compliance=1.0,
            average_response_time=0.0,
            p95_response_time=0.0,
            p99_response_time=0.0,
            module_performance={},
            critical_violations=[],
            recommendations=["无性能数据可用"],
        )
    
    def _generate_report_recommendations(self, metrics: List[PerformanceMetric]) -> List[str]:
        """生成报告优化建议"""
        recommendations = []
        
        # 计算总体SLO合规率
        within_slo_count = sum(1 for m in metrics if m.status == PerformanceStatus.WITHIN_SLO)
        compliance_rate = within_slo_count / len(metrics) if metrics else 1.0
        
        if compliance_rate < 0.9:
            recommendations.append("整体SLO合规率低于90%，需要系统级性能优化")
        
        # 识别性能瓶颈模块
        module_violations = {}
        for metric in metrics:
            if metric.status == PerformanceStatus.VIOLATION:
                module_violations[metric.module.value] = module_violations.get(metric.module.value, 0) + 1
        
        if module_violations:
            worst_module = max(module_violations.items(), key=lambda x: x[1])
            recommendations.append(f"{worst_module[0]}模块违反SLO次数最多({worst_module[1]}次)，建议优先优化")
        
        # 检查响应时间趋势
        recent_times = [m.response_time for m in metrics[-10:]] if len(metrics) >= 10 else []
        if len(recent_times) >= 5:
            avg_recent = statistics.mean(recent_times)
            avg_older = statistics.mean([m.response_time for m in metrics[:-10]]) if len(metrics) > 10 else avg_recent
            
            if avg_recent > avg_older * 1.2:
                recommendations.append("近期响应时间有上升趋势，建议关注性能退化问题")
        
        return recommendations
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        if not self.performance_history:
            return {"total_operations": 0}
        
        recent_metrics = list(self.performance_history)[-100:]  # 最近100个操作
        response_times = [metric.response_time for metric in recent_metrics]
        
        within_slo = sum(1 for m in recent_metrics 
                        if m.status == PerformanceStatus.WITHIN_SLO)
        violations = sum(1 for m in recent_metrics 
                        if m.status == PerformanceStatus.VIOLATION)
        
        return {
            "total_operations": len(self.performance_history),
            "recent_operations": len(recent_metrics),
            "recent_slo_compliance": within_slo / len(recent_metrics) if recent_metrics else 1.0,
            "recent_violation_rate": violations / len(recent_metrics) if recent_metrics else 0.0,
            "avg_response_time": statistics.mean(response_times) if response_times else 0.0,
            "max_response_time": max(response_times) if response_times else 0.0,
            "active_alerts": len(self.alerts),
            "last_alert_time": self.alerts[-1]["timestamp"] if self.alerts else None,
        }


# 全局验证器实例
_slo_validator: Optional[SLOPerformanceValidator] = None


def get_slo_validator(slo_threshold: float = 2.0) -> SLOPerformanceValidator:
    """获取SLO验证器实例（单例模式）"""
    global _slo_validator
    
    if _slo_validator is None:
        _slo_validator = SLOPerformanceValidator(slo_threshold)
    
    return _slo_validator