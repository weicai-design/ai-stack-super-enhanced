#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零信任安全策略管理器
基于零信任原则实现持续验证和最小权限访问控制
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccessDecision(str, Enum):
    """访问决策"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_MFA = "require_mfa"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class RiskContext:
    """风险上下文"""
    user_id: str
    tenant_id: str
    device_fingerprint: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_duration: float = 0.0
    access_patterns: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class AccessRequest:
    """访问请求"""
    request_id: str
    user_id: str
    tenant_id: str
    resource: str
    action: str
    context: RiskContext
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AccessPolicy:
    """访问策略"""
    policy_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    decision: AccessDecision
    priority: int = 100
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ZeroTrustPolicyManager:
    """
    零信任安全策略管理器
    
    基于零信任原则实现：
    1. 永不信任，始终验证
    2. 最小权限原则
    3. 持续风险评估
    4. 动态访问控制
    """
    
    def __init__(self):
        self.policies: Dict[str, AccessPolicy] = {}
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 0.9,
        }
        
        # 初始化默认策略
        self._initialize_default_policies()
        
        logger.info("零信任安全策略管理器初始化完成")
    
    def _initialize_default_policies(self) -> None:
        """初始化默认策略"""
        # 高风险操作需要MFA
        self.add_policy(AccessPolicy(
            policy_id="mfa_required_high_risk",
            name="高风险操作MFA要求",
            description="当风险评估为高风险时，要求多因素认证",
            conditions={"risk_level": RiskLevel.HIGH},
            decision=AccessDecision.REQUIRE_MFA,
            priority=90,
        ))
        
        # 异常位置访问需要审批
        self.add_policy(AccessPolicy(
            policy_id="approval_required_abnormal_location",
            name="异常位置访问审批要求",
            description="当访问位置与历史模式不符时，需要审批",
            conditions={"location_anomaly": True},
            decision=AccessDecision.REQUIRE_APPROVAL,
            priority=80,
        ))
        
        # 关键资源访问限制
        self.add_policy(AccessPolicy(
            policy_id="critical_resource_access",
            name="关键资源访问控制",
            description="关键系统资源的严格访问控制",
            conditions={"resource_criticality": "high"},
            decision=AccessDecision.REQUIRE_MFA,
            priority=70,
        ))
    
    def add_policy(self, policy: AccessPolicy) -> None:
        """添加访问策略"""
        self.policies[policy.policy_id] = policy
        logger.info(f"添加访问策略: {policy.name}")
    
    def evaluate_access_request(self, request: AccessRequest) -> Tuple[AccessDecision, Dict[str, Any]]:
        """
        评估访问请求
        
        Args:
            request: 访问请求
            
        Returns:
            (决策, 评估详情)
        """
        # 1. 计算风险评分
        risk_score = self._calculate_risk_score(request.context)
        
        # 2. 确定风险等级
        risk_level = self._determine_risk_level(risk_score)
        
        # 3. 应用策略评估
        evaluation_details = {
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "applied_policies": [],
            "risk_factors": request.context.risk_factors,
        }
        
        # 4. 按优先级应用策略
        sorted_policies = sorted(self.policies.values(), key=lambda p: p.priority, reverse=True)
        
        for policy in sorted_policies:
            if not policy.enabled:
                continue
                
            if self._policy_conditions_met(policy, request, risk_level):
                evaluation_details["applied_policies"].append({
                    "policy_id": policy.policy_id,
                    "name": policy.name,
                    "decision": policy.decision.value,
                })
                
                # 返回第一个匹配的策略决策
                return policy.decision, evaluation_details
        
        # 默认决策：允许访问
        evaluation_details["applied_policies"].append({
            "policy_id": "default",
            "name": "默认策略",
            "decision": AccessDecision.ALLOW.value,
        })
        
        return AccessDecision.ALLOW, evaluation_details
    
    def _calculate_risk_score(self, context: RiskContext) -> float:
        """计算风险评分"""
        risk_score = 0.0
        risk_factors = []
        
        # 设备指纹异常
        if context.device_fingerprint and "unknown" in context.device_fingerprint:
            risk_score += 0.2
            risk_factors.append("设备指纹异常")
        
        # 位置异常
        if context.location and "unusual" in context.location:
            risk_score += 0.3
            risk_factors.append("位置异常")
        
        # IP地址异常
        if context.ip_address and self._is_suspicious_ip(context.ip_address):
            risk_score += 0.4
            risk_factors.append("IP地址异常")
        
        # 会话时长过长
        if context.session_duration > 3600:  # 超过1小时
            risk_score += 0.1
            risk_factors.append("会话时长过长")
        
        # 访问模式异常
        if len(context.access_patterns) > 10:  # 频繁访问
            risk_score += 0.2
            risk_factors.append("访问模式异常")
        
        context.risk_score = min(risk_score, 1.0)
        context.risk_factors = risk_factors
        
        return context.risk_score
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """确定风险等级"""
        if risk_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _policy_conditions_met(self, policy: AccessPolicy, request: AccessRequest, risk_level: RiskLevel) -> bool:
        """检查策略条件是否满足"""
        conditions = policy.conditions
        
        # 风险等级条件
        if "risk_level" in conditions:
            if risk_level.value != conditions["risk_level"]:
                return False
        
        # 资源关键性条件
        if "resource_criticality" in conditions:
            if request.resource not in ["admin", "config", "sensitive"]:
                return False
        
        # 位置异常条件
        if "location_anomaly" in conditions:
            if not self._has_location_anomaly(request.context):
                return False
        
        return True
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """检查IP地址是否可疑"""
        # 简单的IP检查逻辑
        suspicious_patterns = ["192.168", "10.", "172.16", "127.0.0.1"]
        return any(pattern in ip_address for pattern in suspicious_patterns)
    
    def _has_location_anomaly(self, context: RiskContext) -> bool:
        """检查位置异常"""
        # 简化的位置异常检查
        return context.location and "unusual" in context.location
    
    def get_policy_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        enabled_policies = [p for p in self.policies.values() if p.enabled]
        
        return {
            "total_policies": len(self.policies),
            "enabled_policies": len(enabled_policies),
            "policy_distribution": {
                "allow": len([p for p in enabled_policies if p.decision == AccessDecision.ALLOW]),
                "deny": len([p for p in enabled_policies if p.decision == AccessDecision.DENY]),
                "require_mfa": len([p for p in enabled_policies if p.decision == AccessDecision.REQUIRE_MFA]),
                "require_approval": len([p for p in enabled_policies if p.decision == AccessDecision.REQUIRE_APPROVAL]),
            }
        }


# 全局实例
_zero_trust_policy_manager: Optional[ZeroTrustPolicyManager] = None


def get_zero_trust_policy_manager() -> ZeroTrustPolicyManager:
    """获取零信任策略管理器实例"""
    global _zero_trust_policy_manager
    if _zero_trust_policy_manager is None:
        _zero_trust_policy_manager = ZeroTrustPolicyManager()
    return _zero_trust_policy_manager