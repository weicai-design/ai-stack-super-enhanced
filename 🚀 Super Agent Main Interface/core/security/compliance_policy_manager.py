#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规策略管理器
P1-204: 针对爬虫、外部API、终端命令编写合规策略与审计流程，支持审批与回溯
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import json
import re

from ..database_persistence import DatabasePersistence, get_persistence
from .audit_pipeline import SecurityAuditPipeline, get_audit_pipeline
from .approval_workflow import SensitiveOperationApprovalManager, get_approval_manager, ApprovalStatus

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """操作类型"""
    CRAWLER = "crawler"  # 爬虫操作
    EXTERNAL_API = "external_api"  # 外部API调用
    TERMINAL_COMMAND = "terminal_command"  # 终端命令
    DATA_ACCESS = "data_access"  # 数据访问
    SYSTEM_CONFIG = "system_config"  # 系统配置


class RiskLevel(str, Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """合规规则"""
    rule_id: str
    operation_type: OperationType
    name: str
    description: str
    pattern: Optional[str] = None  # 正则表达式模式
    whitelist: List[str] = field(default_factory=list)  # 白名单
    blacklist: List[str] = field(default_factory=list)  # 黑名单
    rate_limit: Optional[Dict[str, int]] = None  # 速率限制
    requires_approval: bool = False  # 是否需要审批
    risk_level: RiskLevel = RiskLevel.MEDIUM
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["operation_type"] = self.operation_type.value
        data["risk_level"] = self.risk_level.value
        return data


@dataclass
class ComplianceCheckResult:
    """合规检查结果"""
    allowed: bool
    rule_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    approval_id: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


class CompliancePolicyManager:
    """
    合规策略管理器
    
    功能：
    1. 管理合规策略规则
    2. 执行合规检查
    3. 触发审批流程
    4. 记录审计日志
    5. 支持回溯查询
    """
    
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        audit_pipeline: Optional[SecurityAuditPipeline] = None,
        approval_manager: Optional[SensitiveOperationApprovalManager] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.audit_pipeline = audit_pipeline or get_audit_pipeline()
        self.approval_manager = approval_manager or get_approval_manager()
        
        self.table_name = "compliance_policies"
        self.audit_table = "compliance_audit"
        
        # 内存中的规则缓存
        self.rules: Dict[str, ComplianceRule] = {}
        self.rate_limit_trackers: Dict[str, List[float]] = {}  # {key: [timestamps]}
        
        # 初始化默认策略
        self._initialize_default_policies()
        
        logger.info("合规策略管理器初始化完成")
    
    def _initialize_default_policies(self):
        """初始化默认合规策略"""
        # 爬虫合规策略
        self._add_default_crawler_policies()
        
        # 外部API合规策略
        self._add_default_external_api_policies()
        
        # 终端命令合规策略
        self._add_default_terminal_command_policies()
    
    def _add_default_crawler_policies(self):
        """添加默认爬虫合规策略"""
        # 策略1: 爬虫频率限制
        rule = ComplianceRule(
            rule_id="crawler_rate_limit",
            operation_type=OperationType.CRAWLER,
            name="爬虫频率限制",
            description="限制爬虫请求频率，防止过度请求",
            rate_limit={
                "per_minute": 10,
                "per_hour": 100,
                "per_day": 1000,
            },
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略2: 禁止域名
        rule = ComplianceRule(
            rule_id="crawler_forbidden_domains",
            operation_type=OperationType.CRAWLER,
            name="禁止爬取域名",
            description="禁止爬取特定域名",
            blacklist=[
                "example-forbidden.com",
                "blocked-site.com",
                "private-network.local",
            ],
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略3: 爬虫User-Agent检查
        rule = ComplianceRule(
            rule_id="crawler_user_agent",
            operation_type=OperationType.CRAWLER,
            name="爬虫User-Agent检查",
            description="检查爬虫User-Agent，识别恶意爬虫",
            blacklist=[
                "sqlmap",
                "nikto",
                "dirbuster",
                "scanner",
            ],
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略4: 爬虫路径限制
        rule = ComplianceRule(
            rule_id="crawler_path_restriction",
            operation_type=OperationType.CRAWLER,
            name="爬虫路径限制",
            description="限制爬虫访问的路径",
            whitelist=[
                "/public",
                "/docs",
                "/api/public",
            ],
            blacklist=[
                "/admin",
                "/internal",
                "/private",
            ],
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
        )
        self.rules[rule.rule_id] = rule
    
    def _add_default_external_api_policies(self):
        """添加默认外部API合规策略"""
        # 策略1: API调用频率限制
        rule = ComplianceRule(
            rule_id="external_api_rate_limit",
            operation_type=OperationType.EXTERNAL_API,
            name="外部API频率限制",
            description="限制外部API调用频率，防止超限",
            rate_limit={
                "per_minute": 60,
                "per_hour": 1000,
                "per_day": 10000,
            },
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略2: API密钥管理
        rule = ComplianceRule(
            rule_id="external_api_key_management",
            operation_type=OperationType.EXTERNAL_API,
            name="API密钥管理",
            description="检查API密钥的有效性和权限",
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略3: 敏感API调用审批
        rule = ComplianceRule(
            rule_id="external_api_sensitive_operations",
            operation_type=OperationType.EXTERNAL_API,
            name="敏感API调用审批",
            description="敏感API调用需要审批",
            blacklist=[
                "delete",
                "remove",
                "destroy",
                "transfer",
            ],
            requires_approval=True,
            risk_level=RiskLevel.CRITICAL,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略4: API端点白名单
        rule = ComplianceRule(
            rule_id="external_api_endpoint_whitelist",
            operation_type=OperationType.EXTERNAL_API,
            name="API端点白名单",
            description="只允许调用白名单中的API端点",
            whitelist=[
                "https://api.douyin.com/v1/",
                "https://api.tushare.pro/",
                "https://api.ths123.com/",
            ],
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
    
    def _add_default_terminal_command_policies(self):
        """添加默认终端命令合规策略"""
        # 策略1: 危险命令黑名单
        rule = ComplianceRule(
            rule_id="terminal_dangerous_commands",
            operation_type=OperationType.TERMINAL_COMMAND,
            name="危险命令黑名单",
            description="禁止执行危险命令",
            blacklist=[
                "rm -rf /",
                "dd if=",
                "mkfs",
                "fdisk",
                "format",
                "del /f",
                "format c:",
            ],
            requires_approval=False,
            risk_level=RiskLevel.CRITICAL,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略2: 命令白名单
        rule = ComplianceRule(
            rule_id="terminal_command_whitelist",
            operation_type=OperationType.TERMINAL_COMMAND,
            name="命令白名单",
            description="只允许执行白名单中的命令",
            whitelist=[
                "ls", "cat", "grep", "find",
                "python", "node", "npm",
                "git", "docker", "kubectl",
            ],
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略3: 系统命令审批
        rule = ComplianceRule(
            rule_id="terminal_system_commands",
            operation_type=OperationType.TERMINAL_COMMAND,
            name="系统命令审批",
            description="系统级命令需要审批",
            pattern=r"^(sudo|su|systemctl|service|chmod|chown)",
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
        )
        self.rules[rule.rule_id] = rule
        
        # 策略4: 网络命令审批
        rule = ComplianceRule(
            rule_id="terminal_network_commands",
            operation_type=OperationType.TERMINAL_COMMAND,
            name="网络命令审批",
            description="网络相关命令需要审批",
            pattern=r"^(curl|wget|scp|rsync|ssh)",
            requires_approval=True,
            risk_level=RiskLevel.MEDIUM,
        )
        self.rules[rule.rule_id] = rule
    
    def check_compliance(
        self,
        operation_type: OperationType,
        operation: str,
        actor: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComplianceCheckResult:
        """
        检查操作合规性
        
        Args:
            operation_type: 操作类型
            operation: 操作内容（URL、命令、API端点等）
            actor: 执行者
            metadata: 元数据（IP、User-Agent等）
            
        Returns:
            合规检查结果
        """
        metadata = metadata or {}
        result = ComplianceCheckResult(
            allowed=True,
            reasons=[],
            suggestions=[],
            metadata=metadata,
        )
        
        # 获取相关规则
        relevant_rules = [
            rule for rule in self.rules.values()
            if rule.operation_type == operation_type and rule.enabled
        ]
        
        if not relevant_rules:
            # 没有规则，默认允许
            return result
        
        # 检查每个规则
        for rule in relevant_rules:
            rule_result = self._check_rule(rule, operation, actor, metadata)
            
            if not rule_result["allowed"]:
                result.allowed = False
                result.rule_id = rule.rule_id
                result.risk_level = rule.risk_level
                result.requires_approval = rule.requires_approval
                result.reasons.extend(rule_result["reasons"])
                result.suggestions.extend(rule_result.get("suggestions", []))
                
                # 如果风险级别更高，更新
                if self._compare_risk_level(rule.risk_level, result.risk_level) > 0:
                    result.risk_level = rule.risk_level
            
            # 如果需要审批
            if rule.requires_approval and rule_result.get("requires_approval", False):
                result.requires_approval = True
        
        # 如果需要审批，创建审批请求
        if result.requires_approval and result.allowed:
            approval_id = self._create_approval_request(
                operation_type=operation_type,
                operation=operation,
                actor=actor,
                rule_id=result.rule_id,
                metadata=metadata,
            )
            result.approval_id = approval_id
            result.allowed = False  # 等待审批
        
        # 记录审计日志
        self._log_compliance_check(operation_type, operation, actor, result, metadata)
        
        return result
    
    def _check_rule(
        self,
        rule: ComplianceRule,
        operation: str,
        actor: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """检查单个规则"""
        result = {
            "allowed": True,
            "reasons": [],
            "suggestions": [],
            "requires_approval": False,
        }
        
        # 检查黑名单
        if rule.blacklist:
            for item in rule.blacklist:
                if item.lower() in operation.lower():
                    result["allowed"] = False
                    result["reasons"].append(f"匹配黑名单: {item}")
                    break
        
        # 检查白名单
        if rule.whitelist and result["allowed"]:
            matched = False
            for item in rule.whitelist:
                if item.lower() in operation.lower():
                    matched = True
                    break
            if not matched:
                result["allowed"] = False
                result["reasons"].append("不在白名单中")
        
        # 检查正则表达式
        if rule.pattern and result["allowed"]:
            if not re.search(rule.pattern, operation, re.IGNORECASE):
                # 模式不匹配，可能需要审批
                result["requires_approval"] = rule.requires_approval
            else:
                # 模式匹配，检查是否需要审批
                if rule.requires_approval:
                    result["requires_approval"] = True
        
        # 检查速率限制
        if rule.rate_limit and result["allowed"]:
            rate_key = f"{rule.rule_id}:{actor}"
            if not self._check_rate_limit(rate_key, rule.rate_limit):
                result["allowed"] = False
                result["reasons"].append("超过速率限制")
                result["suggestions"].append("请稍后重试")
        
        return result
    
    def _check_rate_limit(self, key: str, limits: Dict[str, int]) -> bool:
        """检查速率限制"""
        now = datetime.utcnow().timestamp()
        
        if key not in self.rate_limit_trackers:
            self.rate_limit_trackers[key] = []
        
        timestamps = self.rate_limit_trackers[key]
        
        # 清理过期记录
        if "per_minute" in limits:
            timestamps = [t for t in timestamps if t > now - 60]
        if "per_hour" in limits:
            timestamps = [t for t in timestamps if t > now - 3600]
        if "per_day" in limits:
            timestamps = [t for t in timestamps if t > now - 86400]
        
        self.rate_limit_trackers[key] = timestamps
        
        # 检查限制
        if "per_minute" in limits and len([t for t in timestamps if t > now - 60]) >= limits["per_minute"]:
            return False
        if "per_hour" in limits and len([t for t in timestamps if t > now - 3600]) >= limits["per_hour"]:
            return False
        if "per_day" in limits and len([t for t in timestamps if t > now - 86400]) >= limits["per_day"]:
            return False
        
        # 记录本次请求
        timestamps.append(now)
        self.rate_limit_trackers[key] = timestamps[-1000:]  # 保留最近1000条
        
        return True
    
    def _create_approval_request(
        self,
        operation_type: OperationType,
        operation: str,
        actor: str,
        rule_id: Optional[str],
        metadata: Dict[str, Any],
    ) -> str:
        """创建审批请求"""
        justification = f"执行{operation_type.value}操作: {operation[:100]}"
        
        approval = self.approval_manager.submit_request(
            applicant=actor,
            operation=f"{operation_type.value}:{operation[:200]}",
            justification=justification,
            metadata={
                "operation_type": operation_type.value,
                "operation": operation,
                "rule_id": rule_id,
                **metadata,
            },
        )
        
        return approval.approval_id
    
    def _log_compliance_check(
        self,
        operation_type: OperationType,
        operation: str,
        actor: str,
        result: ComplianceCheckResult,
        metadata: Dict[str, Any],
    ):
        """记录合规检查审计日志"""
        audit_data = {
            "operation_type": operation_type.value,
            "operation": operation,
            "actor": actor,
            "allowed": result.allowed,
            "risk_level": result.risk_level.value,
            "requires_approval": result.requires_approval,
            "approval_id": result.approval_id,
            "reasons": result.reasons,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {**metadata, **result.metadata},
        }
        
        # 持久化
        try:
            self.persistence.save(
                table_name=self.audit_table,
                data=audit_data,
                record_id=f"compliance_{uuid4()}",
                metadata={"operation_type": operation_type.value, "risk_level": result.risk_level.value},
            )
        except Exception as e:
            logger.error(f"合规审计日志持久化失败: {e}")
        
        # 审计管道
        if self.audit_pipeline:
            self.audit_pipeline.log_security_event(
                event_type=f"compliance_check.{operation_type.value}",
                source="compliance_policy_manager",
                severity="warning" if not result.allowed else "info",
                status="blocked" if not result.allowed else "allowed",
                actor=actor,
                metadata=audit_data,
            )
    
    def _compare_risk_level(self, level1: RiskLevel, level2: RiskLevel) -> int:
        """比较风险级别"""
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        idx1 = levels.index(level1)
        idx2 = levels.index(level2)
        return idx1 - idx2
    
    # ============ 策略管理 ============
    
    def add_rule(self, rule: ComplianceRule) -> str:
        """添加合规规则"""
        rule.updated_at = datetime.utcnow().isoformat() + "Z"
        self.rules[rule.rule_id] = rule
        
        # 持久化
        try:
            self.persistence.save(
                table_name=self.table_name,
                data=rule.to_dict(),
                record_id=rule.rule_id,
                metadata={"operation_type": rule.operation_type.value},
            )
        except Exception as e:
            logger.error(f"规则持久化失败: {e}")
        
        return rule.rule_id
    
    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """获取规则"""
        return self.rules.get(rule_id)
    
    def list_rules(
        self,
        operation_type: Optional[OperationType] = None,
        enabled_only: bool = False,
    ) -> List[ComplianceRule]:
        """列出规则"""
        rules = list(self.rules.values())
        
        if operation_type:
            rules = [r for r in rules if r.operation_type == operation_type]
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return rules
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新规则"""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        
        # 更新字段
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 持久化
        try:
            self.persistence.save(
                table_name=self.table_name,
                data=rule.to_dict(),
                record_id=rule_id,
                metadata={"operation_type": rule.operation_type.value},
            )
        except Exception as e:
            logger.error(f"规则更新失败: {e}")
        
        return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """删除规则"""
        if rule_id not in self.rules:
            return False
        
        del self.rules[rule_id]
        
        # 从持久化中删除
        try:
            self.persistence.delete(self.table_name, rule_id)
        except Exception as e:
            logger.error(f"规则删除失败: {e}")
        
        return True
    
    # ============ 回溯查询 ============
    
    def query_audit_log(
        self,
        operation_type: Optional[OperationType] = None,
        actor: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        risk_level: Optional[RiskLevel] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志（回溯）
        
        Args:
            operation_type: 操作类型
            actor: 执行者
            start_time: 开始时间
            end_time: 结束时间
            risk_level: 风险级别
            limit: 返回数量限制
            
        Returns:
            审计日志列表
        """
        filters: Dict[str, Any] = {}
        
        if operation_type:
            filters["operation_type"] = operation_type.value
        if actor:
            filters["actor"] = actor
        if risk_level:
            filters["risk_level"] = risk_level.value
        
        # 时间过滤
        if start_time or end_time:
            # 这里需要在查询时处理时间范围
            pass
        
        try:
            records = self.persistence.query(
                table_name=self.audit_table,
                filters=filters or None,
                limit=limit,
                order_by="_created_at",
                order_desc=True,
            )
            
            # 转换为标准格式
            result = []
            for record in records:
                data = {k: v for k, v in record.items() if not k.startswith("_")}
                
                # 时间过滤
                if start_time or end_time:
                    timestamp_str = data.get("timestamp", "")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            if start_time and timestamp < start_time:
                                continue
                            if end_time and timestamp > end_time:
                                continue
                        except Exception:
                            pass
                
                result.append(data)
            
            return result
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []
    
    def get_statistics(
        self,
        operation_type: Optional[OperationType] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """获取统计信息"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        records = self.query_audit_log(
            operation_type=operation_type,
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )
        
        stats = {
            "total_checks": len(records),
            "allowed": 0,
            "blocked": 0,
            "requires_approval": 0,
            "by_risk_level": {},
            "by_operation_type": {},
            "top_actors": {},
        }
        
        for record in records:
            if record.get("allowed"):
                stats["allowed"] += 1
            else:
                stats["blocked"] += 1
            
            if record.get("requires_approval"):
                stats["requires_approval"] += 1
            
            risk_level = record.get("risk_level", "low")
            stats["by_risk_level"][risk_level] = stats["by_risk_level"].get(risk_level, 0) + 1
            
            op_type = record.get("operation_type", "unknown")
            stats["by_operation_type"][op_type] = stats["by_operation_type"].get(op_type, 0) + 1
            
            actor = record.get("actor", "unknown")
            stats["top_actors"][actor] = stats["top_actors"].get(actor, 0) + 1
        
        return stats


_compliance_manager: Optional[CompliancePolicyManager] = None


def get_compliance_manager() -> CompliancePolicyManager:
    """获取合规策略管理器实例"""
    global _compliance_manager
    if _compliance_manager is None:
        _compliance_manager = CompliancePolicyManager()
    return _compliance_manager

