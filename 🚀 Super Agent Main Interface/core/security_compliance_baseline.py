"""
安全与合规基线系统
P0-017: 安全与合规（爬虫/内容/数据权限/命令白名单/隐私与审计）基线
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import hashlib
import json

from .database_persistence import DatabasePersistence, get_persistence
from .security.audit_pipeline import SecurityAuditPipeline, get_audit_pipeline
from .security.risk_engine import SecurityRiskEngine, get_risk_engine

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceCategory(Enum):
    """合规类别"""
    CRAWLER = "crawler"  # 爬虫
    CONTENT = "content"  # 内容
    DATA = "data"  # 数据
    COMMAND = "command"  # 命令
    PRIVACY = "privacy"  # 隐私


class ViolationType(Enum):
    """违规类型"""
    CRAWLER_RATE_LIMIT = "crawler_rate_limit"  # 爬虫频率限制
    CRAWLER_FORBIDDEN_DOMAIN = "crawler_forbidden_domain"  # 禁止域名
    CONTENT_SENSITIVE = "content_sensitive"  # 敏感内容
    CONTENT_COPYRIGHT = "content_copyright"  # 版权问题
    DATA_UNAUTHORIZED_ACCESS = "data_unauthorized_access"  # 未授权数据访问
    DATA_PII_EXPOSURE = "data_pii_exposure"  # 个人隐私信息暴露
    COMMAND_BLOCKED = "command_blocked"  # 命令被阻止
    COMMAND_DANGEROUS = "command_dangerous"  # 危险命令
    PRIVACY_DATA_LEAK = "privacy_data_leak"  # 隐私数据泄露
    PRIVACY_UNAUTHORIZED_SHARING = "privacy_unauthorized_sharing"  # 未授权分享


@dataclass
class SecurityViolation:
    """安全违规记录"""
    violation_id: str
    violation_type: ViolationType
    category: ComplianceCategory
    severity: SecurityLevel
    description: str
    detected_at: datetime
    source: str  # 来源（用户ID、IP、模块等）
    resource: Optional[str] = None  # 资源路径/URL/命令等
    action_taken: Optional[str] = None  # 采取的行动
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompliancePolicy:
    """合规策略"""
    policy_id: str
    category: ComplianceCategory
    name: str
    description: str
    rules: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SecurityComplianceBaseline:
    """
    安全与合规基线系统
    
    功能：
    1. 爬虫安全控制
    2. 内容安全检测
    3. 数据权限管理
    4. 命令白名单
    5. 隐私与审计
    """
    
    def __init__(self):
        # 违规记录
        self.violations: List[SecurityViolation] = []
        
        # 合规策略
        self.policies: Dict[str, CompliancePolicy] = {}
        
        # 审计日志
        self.audit_log: List[Dict[str, Any]] = []

        # 外部依赖
        self.persistence: Optional[DatabasePersistence] = None
        self.audit_pipeline: Optional[SecurityAuditPipeline] = None
        self.risk_engine: Optional[SecurityRiskEngine] = None

        try:
            self.persistence = get_persistence()
            self.audit_pipeline = get_audit_pipeline()
            self.risk_engine = get_risk_engine()
        except Exception as exc:  # pragma: no cover
            logger.warning("安全合规基线外部依赖初始化失败: %s", exc)
        
        # 初始化默认策略
        self._initialize_default_policies()
        
        logger.info("安全与合规基线系统初始化完成")
    
    def _initialize_default_policies(self):
        """初始化默认合规策略"""
        # 爬虫安全策略
        self.policies["crawler_rate_limit"] = CompliancePolicy(
            policy_id="crawler_rate_limit",
            category=ComplianceCategory.CRAWLER,
            name="爬虫频率限制",
            description="限制爬虫请求频率，防止过度请求",
            rules={
                "max_requests_per_minute": 10,
                "max_requests_per_hour": 100,
                "delay_between_requests": (1, 3),  # 秒
                "forbidden_domains": [
                    "example-forbidden.com",
                    "blocked-site.com"
                ]
            }
        )
        
        # 内容安全策略
        self.policies["content_sensitive"] = CompliancePolicy(
            policy_id="content_sensitive",
            category=ComplianceCategory.CONTENT,
            name="敏感内容检测",
            description="检测和过滤敏感内容",
            rules={
                "sensitive_keywords": [
                    "涉政", "暴力", "极端", "黄赌毒", "敏感词",
                    "政治", "色情", "赌博", "毒品", "恐怖"
                ],
                "copyright_check": True,
                "similarity_threshold": 0.8
            }
        )
        
        # 数据权限策略
        self.policies["data_permission"] = CompliancePolicy(
            policy_id="data_permission",
            category=ComplianceCategory.DATA,
            name="数据权限控制",
            description="控制数据访问权限",
            rules={
                "require_authorization": True,
                "pii_detection": True,
                "encryption_required": True,
                "access_logging": True
            }
        )
        
        # 命令白名单策略
        self.policies["command_whitelist"] = CompliancePolicy(
            policy_id="command_whitelist",
            category=ComplianceCategory.COMMAND,
            name="命令白名单",
            description="控制可执行的命令",
            rules={
                "whitelist_enabled": True,
                "allowed_commands": [
                    "ls", "cat", "grep", "find", "head", "tail",
                    "python", "node", "npm", "pip", "git",
                    "echo", "pwd", "cd", "mkdir", "touch"
                ],
                "forbidden_commands": [
                    "rm -rf", "format", "del /f", "shutdown", "reboot",
                    "mkfs", "dd if=", "sudo rm", "chmod 777"
                ],
                "forbidden_tokens": ["&&", "||", ";", "|", ">", "<", "$(", "`"]
            }
        )
        
        # 隐私保护策略
        self.policies["privacy_protection"] = CompliancePolicy(
            policy_id="privacy_protection",
            category=ComplianceCategory.PRIVACY,
            name="隐私保护",
            description="保护个人隐私信息",
            rules={
                "pii_detection": True,
                "pii_types": ["email", "phone", "id_card", "bank_card", "address"],
                "data_encryption": True,
                "access_control": True,
                "retention_policy": 90  # 数据保留天数
            }
        )
    
    # ============ 爬虫安全 ============
    
    async def check_crawler_request(
        self,
        url: str,
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        检查爬虫请求
        
        Args:
            url: 请求URL
            source: 请求来源
            
        Returns:
            检查结果
        """
        policy = self.policies.get("crawler_rate_limit")
        if not policy or not policy.enabled:
            return {"allowed": True, "reason": "策略未启用"}
        
        rules = policy.rules
        
        # 检查禁止域名
        forbidden_domains = rules.get("forbidden_domains", [])
        for domain in forbidden_domains:
            if domain in url:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.CRAWLER_FORBIDDEN_DOMAIN,
                    category=ComplianceCategory.CRAWLER,
                    severity=SecurityLevel.HIGH,
                    description=f"尝试访问禁止的域名: {domain}",
                    detected_at=datetime.now(),
                    source=source,
                    resource=url
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": f"禁止访问域名: {domain}",
                    "violation_id": violation.violation_id
                }
        
        # 检查频率限制（简化实现）
        # 实际应该使用更精确的频率控制
        
        return {"allowed": True, "reason": "通过检查"}
    
    # ============ 内容安全 ============
    
    async def check_content_security(
        self,
        content: str,
        content_type: str = "text",
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        检查内容安全
        
        Args:
            content: 内容
            content_type: 内容类型
            source: 来源
            
        Returns:
            检查结果
        """
        policy = self.policies.get("content_sensitive")
        if not policy or not policy.enabled:
            return {"safe": True, "score": 100.0}
        
        rules = policy.rules
        sensitive_keywords = rules.get("sensitive_keywords", [])
        
        # 检测敏感词
        detected_keywords = []
        for keyword in sensitive_keywords:
            if keyword in content:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            violation = SecurityViolation(
                violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                violation_type=ViolationType.CONTENT_SENSITIVE,
                category=ComplianceCategory.CONTENT,
                severity=SecurityLevel.MEDIUM,
                description=f"检测到敏感词: {', '.join(detected_keywords)}",
                detected_at=datetime.now(),
                source=source,
                resource=content[:100]  # 只记录前100字符
            )
            self._record_violation(violation)
            
            return {
                "safe": False,
                "score": max(0, 100 - len(detected_keywords) * 20),
                "detected_keywords": detected_keywords,
                "violation_id": violation.violation_id
            }
        
        return {"safe": True, "score": 100.0}
    
    # ============ 数据权限 ============
    
    async def check_data_permission(
        self,
        resource_path: str,
        action: str,  # read, write, delete
        user_id: str,
        user_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        检查数据权限
        
        Args:
            resource_path: 资源路径
            action: 操作类型
            user_id: 用户ID
            user_permissions: 用户权限列表
            
        Returns:
            权限检查结果
        """
        policy = self.policies.get("data_permission")
        if not policy or not policy.enabled:
            return {"allowed": True, "reason": "策略未启用"}
        
        rules = policy.rules
        
        # 检查是否需要授权
        if rules.get("require_authorization", True):
            if not user_permissions:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.DATA_UNAUTHORIZED_ACCESS,
                    category=ComplianceCategory.DATA,
                    severity=SecurityLevel.HIGH,
                    description=f"未授权访问: {action} {resource_path}",
                    detected_at=datetime.now(),
                    source=user_id,
                    resource=resource_path
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": "需要授权",
                    "violation_id": violation.violation_id
                }
        
        # 检查PII检测
        if rules.get("pii_detection", True):
            pii_detected = await self._detect_pii(resource_path)
            if pii_detected:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.DATA_PII_EXPOSURE,
                    category=ComplianceCategory.DATA,
                    severity=SecurityLevel.CRITICAL,
                    description=f"检测到个人隐私信息: {resource_path}",
                    detected_at=datetime.now(),
                    source=user_id,
                    resource=resource_path
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": "包含个人隐私信息",
                    "violation_id": violation.violation_id
                }
        
        return {"allowed": True, "reason": "通过检查"}
    
    async def _detect_pii(self, content: str) -> bool:
        """检测个人隐私信息"""
        # 简化的PII检测
        pii_patterns = [
            r'\b\d{18}\b',  # 身份证号
            r'\b\d{16,19}\b',  # 银行卡号
            r'\b1[3-9]\d{9}\b',  # 手机号
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # 邮箱
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    # ============ 命令白名单 ============
    
    async def check_command_security(
        self,
        command: str,
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        检查命令安全性
        
        Args:
            command: 命令
            source: 来源
            
        Returns:
            检查结果
        """
        policy = self.policies.get("command_whitelist")
        if not policy or not policy.enabled:
            return {"allowed": True, "reason": "策略未启用"}
        
        rules = policy.rules
        
        # 检查禁止的命令
        forbidden_commands = rules.get("forbidden_commands", [])
        for forbidden in forbidden_commands:
            if forbidden in command:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.COMMAND_DANGEROUS,
                    category=ComplianceCategory.COMMAND,
                    severity=SecurityLevel.CRITICAL,
                    description=f"检测到危险命令: {forbidden}",
                    detected_at=datetime.now(),
                    source=source,
                    resource=command
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": f"危险命令: {forbidden}",
                    "violation_id": violation.violation_id
                }
        
        # 检查禁止的token
        forbidden_tokens = rules.get("forbidden_tokens", [])
        for token in forbidden_tokens:
            if token in command:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.COMMAND_BLOCKED,
                    category=ComplianceCategory.COMMAND,
                    severity=SecurityLevel.HIGH,
                    description=f"检测到禁止的token: {token}",
                    detected_at=datetime.now(),
                    source=source,
                    resource=command
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": f"禁止的token: {token}",
                    "violation_id": violation.violation_id
                }
        
        # 检查白名单（如果启用）
        if rules.get("whitelist_enabled", True):
            allowed_commands = rules.get("allowed_commands", [])
            command_base = command.split()[0] if command.split() else command
            
            if command_base not in allowed_commands:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.COMMAND_BLOCKED,
                    category=ComplianceCategory.COMMAND,
                    severity=SecurityLevel.MEDIUM,
                    description=f"命令不在白名单中: {command_base}",
                    detected_at=datetime.now(),
                    source=source,
                    resource=command
                )
                self._record_violation(violation)
                
                return {
                    "allowed": False,
                    "reason": f"命令不在白名单中: {command_base}",
                    "violation_id": violation.violation_id
                }
        
        return {"allowed": True, "reason": "通过检查"}
    
    # ============ 隐私保护 ============
    
    async def check_privacy_compliance(
        self,
        data: Any,
        data_type: str = "text",
        source: str = "system"
    ) -> Dict[str, Any]:
        """
        检查隐私合规性
        
        Args:
            data: 数据
            data_type: 数据类型
            source: 来源
            
        Returns:
            检查结果
        """
        policy = self.policies.get("privacy_protection")
        if not policy or not policy.enabled:
            return {"compliant": True, "score": 100.0}
        
        rules = policy.rules
        
        # 检测PII
        if rules.get("pii_detection", True):
            data_str = str(data)
            pii_detected = await self._detect_pii(data_str)
            
            if pii_detected:
                violation = SecurityViolation(
                    violation_id=f"violation_{int(datetime.now().timestamp() * 1000)}",
                    violation_type=ViolationType.PRIVACY_DATA_LEAK,
                    category=ComplianceCategory.PRIVACY,
                    severity=SecurityLevel.CRITICAL,
                    description="检测到个人隐私信息",
                    detected_at=datetime.now(),
                    source=source,
                    resource=data_str[:100]
                )
                self._record_violation(violation)
                
                return {
                    "compliant": False,
                    "score": 0.0,
                    "reason": "包含个人隐私信息",
                    "violation_id": violation.violation_id
                }
        
        return {"compliant": True, "score": 100.0}
    
    # ============ 审计日志 ============
    
    def _record_violation(self, violation: SecurityViolation):
        """记录违规"""
        self.violations.append(violation)
        
        # 保留最近10000条
        if len(self.violations) > 10000:
            self.violations = self.violations[-10000:]
        
        # 记录审计日志
        self._log_audit_event(
            event_type="security_violation",
            severity=violation.severity.value,
            violation_type=violation.violation_type.value,
            category=violation.category.value,
            source=violation.source,
            resource=violation.resource,
            description=violation.description
        )
        
        payload = {
            "violation_id": violation.violation_id,
            "violation_type": violation.violation_type.value,
            "category": violation.category.value,
            "severity": violation.severity.value,
            "description": violation.description,
            "detected_at": violation.detected_at.isoformat(),
            "source": violation.source,
            "resource": violation.resource,
            "metadata": violation.metadata,
        }

        if self.persistence:
            try:
                self.persistence.save(
                    table_name="security_violations",
                    record_id=violation.violation_id,
                    data=payload,
                    metadata={"severity": violation.severity.value},
                )
            except Exception as exc:  # pragma: no cover
                logger.error("保存违规记录失败: %s", exc)

        if self.audit_pipeline:
            self.audit_pipeline.log_security_event(
                event_type=f"violation.{violation.violation_type.value}",
                source="security_compliance",
                severity=violation.severity.value,
                status="failed",
                metadata=payload,
            )

        if self.risk_engine:
            self.risk_engine.record_violation(payload)

        logger.warning(f"安全违规: {violation.violation_type.value} - {violation.description}")
    
    def _log_audit_event(
        self,
        event_type: str,
        severity: str,
        **kwargs
    ):
        """记录审计事件"""
        log_entry = {
            "event_type": event_type,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.audit_log.append(log_entry)
        
        # 保留最近50000条
        if len(self.audit_log) > 50000:
            self.audit_log = self.audit_log[-50000:]
    
    def get_violations(
        self,
        category: Optional[ComplianceCategory] = None,
        severity: Optional[SecurityLevel] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取违规记录"""
        if self.persistence:
            filters = {}
            if category:
                filters["category"] = category.value
            if severity:
                filters["severity"] = severity.value
            records = self.persistence.query(
                table_name="security_violations",
                filters=filters or None,
                limit=limit,
                order_by="_created_at",
                order_desc=True,
            )
            return [
                {
                    "violation_id": r.get("violation_id"),
                    "violation_type": r.get("violation_type"),
                    "category": r.get("category"),
                    "severity": r.get("severity"),
                    "description": r.get("description"),
                    "detected_at": r.get("detected_at"),
                    "source": r.get("source"),
                    "resource": r.get("resource"),
                    "action_taken": r.get("action_taken"),
                }
                for r in records
            ]

        violations = self.violations
        
        if category:
            violations = [v for v in violations if v.category == category]
        
        if severity:
            violations = [v for v in violations if v.severity == severity]
        
        return [
            {
                "violation_id": v.violation_id,
                "violation_type": v.violation_type.value,
                "category": v.category.value,
                "severity": v.severity.value,
                "description": v.description,
                "detected_at": v.detected_at.isoformat(),
                "source": v.source,
                "resource": v.resource,
                "action_taken": v.action_taken
            }
            for v in violations[-limit:]
        ]
    
    def get_audit_log(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        if self.persistence:
            filters = {}
            if event_type:
                filters["event_type"] = event_type
            if severity:
                filters["severity"] = severity
            logs = self.persistence.query(
                table_name="security_audit",
                filters=filters or None,
                limit=limit,
                order_by="_created_at",
                order_desc=True,
            )
            return [{k: v for k, v in log.items() if not k.startswith("_")} for log in logs]

        logs = self.audit_log
        
        if event_type:
            logs = [l for l in logs if l.get("event_type") == event_type]
        
        if severity:
            logs = [l for l in logs if l.get("severity") == severity]
        
        return logs[-limit:]
    
    def update_policy(
        self,
        policy_id: str,
        rules: Optional[Dict[str, Any]] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新合规策略
        
        Args:
            policy_id: 策略ID
            rules: 新规则（可选）
            enabled: 是否启用（可选）
            
        Returns:
            更新结果
        """
        if policy_id not in self.policies:
            raise ValueError(f"策略不存在: {policy_id}")
        
        policy = self.policies[policy_id]
        
        if rules is not None:
            policy.rules.update(rules)
        
        if enabled is not None:
            policy.enabled = enabled
        
        policy.updated_at = datetime.now()
        
        self._log_audit_event(
            event_type="policy_updated",
            severity="info",
            policy_id=policy_id,
            changes={"rules": rules, "enabled": enabled}
        )
        
        logger.info(f"策略已更新: {policy_id}")
        
        return {
            "success": True,
            "policy_id": policy_id,
            "updated_at": policy.updated_at.isoformat()
        }
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略"""
        policy = self.policies.get(policy_id)
        if not policy:
            return None
        
        return {
            "policy_id": policy.policy_id,
            "category": policy.category.value,
            "name": policy.name,
            "description": policy.description,
            "rules": policy.rules,
            "enabled": policy.enabled,
            "created_at": policy.created_at.isoformat(),
            "updated_at": policy.updated_at.isoformat()
        }
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """列出所有策略"""
        return [self.get_policy(pid) for pid in self.policies.keys()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.persistence:
            recent = self.persistence.query(
                table_name="security_violations",
                limit=500,
                order_by="_created_at",
                order_desc=True,
            )
            category_counts: Dict[str, int] = {}
            severity_counts: Dict[str, int] = {}
            type_counts: Dict[str, int] = {}
            for item in recent:
                category = item.get("category", "unknown")
                severity = item.get("severity", "unknown")
                vtype = item.get("violation_type", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                type_counts[vtype] = type_counts.get(vtype, 0) + 1
            return {
                "total_violations": self.persistence.count("security_violations"),
                "recent_violations": len(recent),
                "category_distribution": category_counts,
                "severity_distribution": severity_counts,
                "type_distribution": type_counts,
                "total_audit_logs": self.persistence.count("security_audit"),
                "policies_count": len(self.policies),
                "enabled_policies": len([p for p in self.policies.values() if p.enabled])
            }

        recent_violations = self.violations[-1000:] if self.violations else []
        
        category_counts = {}
        severity_counts = {}
        type_counts = {}
        
        for violation in recent_violations:
            category = violation.category.value
            severity = violation.severity.value
            vtype = violation.violation_type.value
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[vtype] = type_counts.get(vtype, 0) + 1
        
        return {
            "total_violations": len(self.violations),
            "recent_violations": len(recent_violations),
            "category_distribution": category_counts,
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "total_audit_logs": len(self.audit_log),
            "policies_count": len(self.policies),
            "enabled_policies": len([p for p in self.policies.values() if p.enabled])
        }



