#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检查机制
P0-001: 实现自动检查器，对执行结果进行验证、质量评估、合规检查
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import uuid4

from .unified_event_bus import UnifiedEventBus, EventCategory, EventSeverity, get_unified_event_bus

logger = logging.getLogger(__name__)


class CheckType(str, Enum):
    """检查类型"""
    VALIDATION = "validation"  # 数据验证
    QUALITY = "quality"  # 质量检查
    COMPLIANCE = "compliance"  # 合规检查
    PERFORMANCE = "performance"  # 性能检查
    SECURITY = "security"  # 安全检查
    FUNCTIONALITY = "functionality"  # 功能检查


class CheckResult(str, Enum):
    """检查结果"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class CheckRule:
    """检查规则"""
    rule_id: str
    check_type: CheckType
    name: str
    description: str
    checker: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]] | Dict[str, Any]]
    enabled: bool = True
    severity: EventSeverity = EventSeverity.WARNING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckReport:
    """检查报告"""
    check_id: str
    execution_id: str
    check_type: CheckType
    rule_id: str
    rule_name: str
    result: CheckResult
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_ms: float = 0.0


class ExecutionChecker:
    """
    自动检查器
    
    功能：
    - 数据验证
    - 质量评估
    - 合规检查
    - 性能检查
    - 安全检查
    - 功能检查
    """
    
    def __init__(self, event_bus: Optional[UnifiedEventBus] = None):
        self.event_bus = event_bus or get_unified_event_bus()
        self.rules: Dict[str, CheckRule] = {}
        self.reports: List[CheckReport] = []
        self._lock = asyncio.Lock()
        
        # 注册默认检查规则
        self._register_default_rules()
    
    def _register_default_rules(self):
        """注册默认检查规则"""
        # 数据验证规则
        self.register_rule(CheckRule(
            rule_id="data_validation_required_fields",
            check_type=CheckType.VALIDATION,
            name="必需字段验证",
            description="检查执行结果是否包含必需字段",
            checker=self._check_required_fields,
        ))
        
        # 质量检查规则
        self.register_rule(CheckRule(
            rule_id="quality_result_format",
            check_type=CheckType.QUALITY,
            name="结果格式检查",
            description="检查执行结果格式是否正确",
            checker=self._check_result_format,
        ))
        
        # 性能检查规则
        self.register_rule(CheckRule(
            rule_id="performance_response_time",
            check_type=CheckType.PERFORMANCE,
            name="响应时间检查",
            description="检查执行响应时间是否在合理范围内",
            checker=self._check_response_time,
        ))
        
        # 安全检查规则
        self.register_rule(CheckRule(
            rule_id="security_sensitive_data",
            check_type=CheckType.SECURITY,
            name="敏感数据检查",
            description="检查执行结果是否包含敏感数据",
            checker=self._check_sensitive_data,
        ))
    
    def register_rule(self, rule: CheckRule):
        """注册检查规则"""
        self.rules[rule.rule_id] = rule
        logger.debug(f"检查规则已注册: {rule.rule_id} ({rule.name})")
    
    def unregister_rule(self, rule_id: str) -> bool:
        """取消注册检查规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.debug(f"检查规则已取消: {rule_id}")
            return True
        return False
    
    async def check_execution(
        self,
        execution_id: str,
        execution_result: Dict[str, Any],
        check_types: Optional[List[CheckType]] = None,
    ) -> List[CheckReport]:
        """
        检查执行结果
        
        Args:
            execution_id: 执行ID
            execution_result: 执行结果
            check_types: 要执行的检查类型（None表示全部）
            
        Returns:
            检查报告列表
        """
        reports = []
        
        # 筛选要执行的规则
        rules_to_execute = [
            rule for rule in self.rules.values()
            if rule.enabled and (check_types is None or rule.check_type in check_types)
        ]
        
        for rule in rules_to_execute:
            try:
                start_time = datetime.utcnow()
                
                # 执行检查
                if asyncio.iscoroutinefunction(rule.checker):
                    check_result = await rule.checker(execution_result)
                else:
                    check_result = rule.checker(execution_result)
                
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # 创建检查报告
                report = CheckReport(
                    check_id=f"check_{uuid4()}",
                    execution_id=execution_id,
                    check_type=rule.check_type,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    result=CheckResult(check_result.get("result", "skip")),
                    message=check_result.get("message", ""),
                    details=check_result.get("details", {}),
                    duration_ms=duration_ms,
                )
                
                reports.append(report)
                
                # 发布检查事件
                await self.event_bus.publish(
                    category=EventCategory.CHECK,
                    event_type=f"check_{rule.check_type.value}",
                    source="execution_checker",
                    severity=rule.severity if report.result == CheckResult.FAIL else EventSeverity.INFO,
                    payload={
                        "execution_id": execution_id,
                        "check_id": report.check_id,
                        "rule_id": rule.rule_id,
                        "result": report.result.value,
                        "message": report.message,
                    },
                    correlation_id=execution_id,
                )
                
            except Exception as e:
                logger.error(f"检查规则执行失败: {rule.rule_id}, {e}", exc_info=True)
                # 创建失败报告
                report = CheckReport(
                    check_id=f"check_{uuid4()}",
                    execution_id=execution_id,
                    check_type=rule.check_type,
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    result=CheckResult.FAIL,
                    message=f"检查执行异常: {str(e)}",
                    details={"error": str(e)},
                )
                reports.append(report)
        
        # 保存报告
        async with self._lock:
            self.reports.extend(reports)
            # 保留最近10000个报告
            if len(self.reports) > 10000:
                self.reports = self.reports[-10000:]
        
        return reports
    
    async def _check_required_fields(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查必需字段"""
        required_fields = ["success", "result"]
        missing_fields = [field for field in required_fields if field not in execution_result]
        
        if missing_fields:
            return {
                "result": "fail",
                "message": f"缺少必需字段: {', '.join(missing_fields)}",
                "details": {"missing_fields": missing_fields},
            }
        
        return {
            "result": "pass",
            "message": "必需字段检查通过",
            "details": {},
        }
    
    async def _check_result_format(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查结果格式"""
        if not isinstance(execution_result, dict):
            return {
                "result": "fail",
                "message": "执行结果必须是字典类型",
                "details": {"type": type(execution_result).__name__},
            }
        
        if "success" in execution_result and not isinstance(execution_result["success"], bool):
            return {
                "result": "fail",
                "message": "success字段必须是布尔类型",
                "details": {},
            }
        
        return {
            "result": "pass",
            "message": "结果格式检查通过",
            "details": {},
        }
    
    async def _check_response_time(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查响应时间"""
        duration = execution_result.get("duration", 0)
        max_duration = execution_result.get("max_duration", 2.0)  # 默认2秒
        
        if duration > max_duration:
            return {
                "result": "warning",
                "message": f"响应时间 {duration:.2f}s 超过阈值 {max_duration}s",
                "details": {
                    "duration": duration,
                    "max_duration": max_duration,
                },
            }
        
        return {
            "result": "pass",
            "message": f"响应时间 {duration:.2f}s 在合理范围内",
            "details": {"duration": duration},
        }
    
    async def _check_sensitive_data(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """检查敏感数据"""
        sensitive_keywords = ["password", "token", "secret", "key", "api_key"]
        result_str = str(execution_result).lower()
        
        found_keywords = [kw for kw in sensitive_keywords if kw in result_str]
        
        if found_keywords:
            return {
                "result": "warning",
                "message": f"检测到可能的敏感数据关键词: {', '.join(found_keywords)}",
                "details": {"found_keywords": found_keywords},
            }
        
        return {
            "result": "pass",
            "message": "未检测到敏感数据",
            "details": {},
        }
    
    def get_reports(
        self,
        execution_id: Optional[str] = None,
        check_type: Optional[CheckType] = None,
        result: Optional[CheckResult] = None,
        limit: int = 100,
    ) -> List[CheckReport]:
        """获取检查报告"""
        reports = self.reports
        
        if execution_id:
            reports = [r for r in reports if r.execution_id == execution_id]
        if check_type:
            reports = [r for r in reports if r.check_type == check_type]
        if result:
            reports = [r for r in reports if r.result == result]
        
        return list(reversed(reports[-limit:]))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.reports)
        by_result = {}
        by_type = {}
        
        for report in self.reports:
            by_result[report.result.value] = by_result.get(report.result.value, 0) + 1
            by_type[report.check_type.value] = by_type.get(report.check_type.value, 0) + 1
        
        return {
            "total_checks": total,
            "by_result": by_result,
            "by_type": by_type,
            "rules_count": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
        }

