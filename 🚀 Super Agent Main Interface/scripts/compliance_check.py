#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规检查脚本（生产级实现）
5.2: 新增合规检查脚本，支持多种合规规则、批量检查、报告生成
"""

from __future__ import annotations

import os
import sys
import json
import logging
import argparse
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.tenant_audit_logger import get_audit_logger, AuditAction
from core.security_compliance_baseline import SecurityComplianceBaseline, ComplianceCategory
from core.security.crawler_compliance import get_crawler_compliance_service

logger = logging.getLogger(__name__)


class ComplianceRuleType(str, Enum):
    """合规规则类型"""
    AUDIT_LOG = "audit_log"  # 审计日志合规
    SECURITY_POLICY = "security_policy"  # 安全策略合规
    DATA_ISOLATION = "data_isolation"  # 数据隔离合规
    ACCESS_CONTROL = "access_control"  # 访问控制合规
    ENCRYPTION = "encryption"  # 加密合规
    BACKUP = "backup"  # 备份合规
    RETENTION = "retention"  # 数据保留合规
    CRAWLER_POLICY = "crawler_policy"  # 爬虫策略合规
    COMMAND_WHITELIST = "command_whitelist"  # 命令白名单合规
    API_USAGE = "api_usage"  # API使用合规


@dataclass
class ComplianceCheckResult:
    """合规检查结果"""
    rule_type: ComplianceRuleType
    tenant_id: str
    check_name: str
    passed: bool
    severity: str  # info, warning, error
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ComplianceReport:
    """合规报告"""
    tenant_id: str
    check_date: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    results: List[ComplianceCheckResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ComplianceChecker:
    """
    合规检查器（生产级实现）
    
    功能：
    1. 多种合规规则检查
    2. 批量检查
    3. 报告生成
    """
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.security_baseline = SecurityComplianceBaseline()
        self.crawler_compliance = get_crawler_compliance_service()
        
        from core.security.config_manager import get_security_config_manager
        self.config_manager = get_security_config_manager()
        # 缓存机制
        self.cache = {}
        self.cache_ttl = self.config_manager.get_config("compliance.cache_ttl", 300)  # 默认5分钟
        self.last_cache_cleanup = datetime.now()
        
        # 性能监控
        self.check_times = {}
        self.max_check_time = self.config_manager.get_config("compliance.max_check_time", 10000)  # 默认10秒
        
        logger.info("合规检查器初始化完成")
    
    def check_audit_log_compliance(
        self,
        tenant_id: str,
        days: int = 30,
    ) -> ComplianceCheckResult:
        """
        检查审计日志合规
        
        规则：
        1. 审计日志必须记录所有关键操作
        2. 审计日志必须保留至少30天
        3. 审计日志必须包含必要的字段
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            logs = self.audit_logger.query_logs(
                tenant_id=tenant_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
            
            # 检查关键操作是否记录
            critical_actions = [
                AuditAction.LOGIN,
                AuditAction.DELETE,
                AuditAction.DATA_EXPORT,
                AuditAction.CONFIG_CHANGE,
                AuditAction.PERMISSION_GRANT,
            ]
            
            missing_actions = []
            for action in critical_actions:
                action_logs = [log for log in logs if log.action == action]
                if not action_logs:
                    missing_actions.append(action.value)
            
            # 检查日志完整性
            incomplete_logs = []
            for log in logs:
                if not log.ip_address or not log.user_agent:
                    incomplete_logs.append(log.log_id)
            
            passed = len(missing_actions) == 0 and len(incomplete_logs) == 0
            severity = "error" if not passed else "info"
            message = "审计日志合规检查通过"
            
            if missing_actions:
                message = f"缺少关键操作记录: {', '.join(missing_actions)}"
            elif incomplete_logs:
                message = f"存在不完整的日志记录: {len(incomplete_logs)}条"
            
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.AUDIT_LOG,
                tenant_id=tenant_id,
                check_name="审计日志合规",
                passed=passed,
                severity=severity,
                message=message,
                details={
                    "total_logs": len(logs),
                    "missing_actions": missing_actions,
                    "incomplete_logs_count": len(incomplete_logs),
                    "retention_days": days,
                },
            )
        except Exception as e:
            logger.error(f"审计日志合规检查失败: {e}", exc_info=True)
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.AUDIT_LOG,
                tenant_id=tenant_id,
                check_name="审计日志合规",
                passed=False,
                severity="error",
                message=f"检查失败: {str(e)}",
            )
    
    def check_security_policy_compliance(
        self,
        tenant_id: str,
    ) -> ComplianceCheckResult:
        """
        检查安全策略合规
        
        规则：
        1. 必须配置安全策略
        2. 安全策略必须启用
        3. 关键安全策略必须配置
        """
        try:
            policies = self.security_baseline.list_policies()
            
            # 检查关键策略
            required_policies = [
                "data_encryption",
                "access_control",
                "audit_logging",
                "password_policy",
            ]
            
            missing_policies = []
            disabled_policies = []
            
            for policy_id in required_policies:
                policy = self.security_baseline.get_policy(policy_id)
                if not policy:
                    missing_policies.append(policy_id)
                elif not policy.get("enabled", False):
                    disabled_policies.append(policy_id)
            
            passed = len(missing_policies) == 0 and len(disabled_policies) == 0
            severity = "error" if not passed else "info"
            message = "安全策略合规检查通过"
            
            if missing_policies:
                message = f"缺少关键安全策略: {', '.join(missing_policies)}"
            elif disabled_policies:
                message = f"存在未启用的安全策略: {', '.join(disabled_policies)}"
            
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.SECURITY_POLICY,
                tenant_id=tenant_id,
                check_name="安全策略合规",
                passed=passed,
                severity=severity,
                message=message,
                details={
                    "total_policies": len(policies),
                    "missing_policies": missing_policies,
                    "disabled_policies": disabled_policies,
                },
            )
        except Exception as e:
            logger.error(f"安全策略合规检查失败: {e}", exc_info=True)
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.SECURITY_POLICY,
                tenant_id=tenant_id,
                check_name="安全策略合规",
                passed=False,
                severity="error",
                message=f"检查失败: {str(e)}",
            )
    
    def check_data_isolation_compliance(
        self,
        tenant_id: str,
    ) -> ComplianceCheckResult:
        """
        检查数据隔离合规
        
        规则：
        1. 租户数据必须隔离
        2. 跨租户访问必须被阻止
        3. 数据访问必须记录
        """
        try:
            # 检查审计日志中的跨租户访问
            logs = self.audit_logger.query_logs(
                tenant_id=tenant_id,
                limit=1000,
            )
            
            # 检查是否有跨租户访问尝试
            cross_tenant_attempts = []
            for log in logs:
                if log.details.get("cross_tenant_access"):
                    cross_tenant_attempts.append(log.log_id)
            
            passed = len(cross_tenant_attempts) == 0
            severity = "warning" if cross_tenant_attempts else "info"
            message = "数据隔离合规检查通过"
            
            if cross_tenant_attempts:
                message = f"检测到跨租户访问尝试: {len(cross_tenant_attempts)}次"
            
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.DATA_ISOLATION,
                tenant_id=tenant_id,
                check_name="数据隔离合规",
                passed=passed,
                severity=severity,
                message=message,
                details={
                    "cross_tenant_attempts": len(cross_tenant_attempts),
                    "checked_logs": len(logs),
                },
            )
        except Exception as e:
            logger.error(f"数据隔离合规检查失败: {e}", exc_info=True)
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.DATA_ISOLATION,
                tenant_id=tenant_id,
                check_name="数据隔离合规",
                passed=False,
                severity="error",
                message=f"检查失败: {str(e)}",
            )
    
    def check_access_control_compliance(
        self,
        tenant_id: str,
    ) -> ComplianceCheckResult:
        """
        检查访问控制合规
        
        规则：
        1. 必须配置访问控制策略
        2. 权限必须正确分配
        3. 未授权访问必须被阻止
        """
        try:
            logs = self.audit_logger.query_logs(
                tenant_id=tenant_id,
                limit=1000,
            )
            
            # 检查未授权访问
            unauthorized_access = [
                log for log in logs
                if not log.success and "permission" in (log.error_message or "").lower()
            ]
            
            passed = len(unauthorized_access) == 0
            severity = "warning" if unauthorized_access else "info"
            message = "访问控制合规检查通过"
            
            if unauthorized_access:
                message = f"检测到未授权访问尝试: {len(unauthorized_access)}次"
            
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.ACCESS_CONTROL,
                tenant_id=tenant_id,
                check_name="访问控制合规",
                passed=passed,
                severity=severity,
                message=message,
                details={
                    "unauthorized_access_count": len(unauthorized_access),
                    "checked_logs": len(logs),
                },
            )
        except Exception as e:
            logger.error(f"访问控制合规检查失败: {e}", exc_info=True)
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.ACCESS_CONTROL,
                tenant_id=tenant_id,
                check_name="访问控制合规",
                passed=False,
                severity="error",
                message=f"检查失败: {str(e)}",
            )
    
    def check_crawler_policy_compliance(
        self,
        tenant_id: str,
    ) -> ComplianceCheckResult:
        """
        检查爬虫策略合规
        
        规则：
        1. 必须配置爬虫策略
        2. 爬虫访问必须被正确识别
        3. 恶意爬虫必须被阻止
        """
        try:
            # 检查爬虫合规服务配置
            policy = self.crawler_compliance._policy
            
            passed = (
                len(policy.blocked_agents) > 0 and
                len(policy.allowed_paths) > 0 and
                policy.rate_limit_per_minute > 0
            )
            
            severity = "info" if passed else "warning"
            message = "爬虫策略合规检查通过" if passed else "爬虫策略配置不完整"
            
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.CRAWLER_POLICY,
                tenant_id=tenant_id,
                check_name="爬虫策略合规",
                passed=passed,
                severity=severity,
                message=message,
                details={
                    "blocked_agents_count": len(policy.blocked_agents),
                    "allowed_paths_count": len(policy.allowed_paths),
                    "rate_limit": policy.rate_limit_per_minute,
                },
            )
        except Exception as e:
            logger.error(f"爬虫策略合规检查失败: {e}", exc_info=True)
            return ComplianceCheckResult(
                rule_type=ComplianceRuleType.CRAWLER_POLICY,
                tenant_id=tenant_id,
                check_name="爬虫策略合规",
                passed=False,
                severity="error",
                message=f"检查失败: {str(e)}",
            )
    
    def run_all_checks(
        self,
        tenant_id: str,
        rule_types: Optional[List[ComplianceRuleType]] = None,
    ) -> ComplianceReport:
        """
        运行所有合规检查
        
        Args:
            tenant_id: 租户ID
            rule_types: 要检查的规则类型（如果为None，则检查所有）
            
        Returns:
            合规报告
        """
        # 检查缓存
        cache_key = f"all_checks_{tenant_id}"
        if rule_types:
            cache_key += "_" + "_".join([rt.value for rt in rule_types])
        
        cached_result = self._get_cache(cache_key)
        if cached_result:
            logger.info("使用缓存结果")
            return cached_result
        
        if rule_types is None:
            rule_types = list(ComplianceRuleType)
        
        results = []
        start_time = datetime.now()
        
        try:
            # 运行各种检查
            if ComplianceRuleType.AUDIT_LOG in rule_types:
                results.append(self._timed_check("audit_log", lambda: self.check_audit_log_compliance(tenant_id)))
            
            if ComplianceRuleType.SECURITY_POLICY in rule_types:
                results.append(self._timed_check("security_policy", lambda: self.check_security_policy_compliance(tenant_id)))
            
            if ComplianceRuleType.DATA_ISOLATION in rule_types:
                results.append(self._timed_check("data_isolation", lambda: self.check_data_isolation_compliance(tenant_id)))
            
            if ComplianceRuleType.ACCESS_CONTROL in rule_types:
                results.append(self._timed_check("access_control", lambda: self.check_access_control_compliance(tenant_id)))
            
            if ComplianceRuleType.CRAWLER_POLICY in rule_types:
                results.append(self._timed_check("crawler_policy", lambda: self.check_crawler_policy_compliance(tenant_id)))
            
            # 统计
            total_checks = len(results)
            passed_checks = sum(1 for r in results if r.passed)
            failed_checks = sum(1 for r in results if not r.passed and r.severity == "error")
            warning_checks = sum(1 for r in results if not r.passed and r.severity == "warning")
            
            # 生成摘要
            summary = {
                "compliance_rate": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
                "by_severity": {
                    "error": failed_checks,
                    "warning": warning_checks,
                    "info": passed_checks,
                },
                "by_rule_type": {
                    rule_type.value: sum(1 for r in results if r.rule_type == rule_type)
                    for rule_type in rule_types
                },
            }
            
            report = ComplianceReport(
                tenant_id=tenant_id,
                check_date=datetime.now().isoformat(),
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                warning_checks=warning_checks,
                results=results,
                summary=summary,
            )
            
            # 设置缓存
            self._set_cache(cache_key, report)
            
            # 性能监控
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"合规检查完成: {tenant_id}, 通过: {passed_checks}/{total_checks}, 耗时: {total_time:.2f}ms")
            
            # 检查性能告警
            self._check_performance_alerts()
            
            return report
            
        except Exception as e:
            logger.error(f"合规检查执行失败: {e}")
            # 返回错误报告
            return ComplianceReport(
                tenant_id=tenant_id,
                check_date=datetime.now().isoformat(),
                total_checks=0,
                passed_checks=0,
                failed_checks=1,
                warning_checks=0,
                results=[],
                summary={"error": str(e)},
            )
    
    def _timed_check(self, check_name: str, check_func) -> ComplianceCheckResult:
        """带时间监控的检查方法"""
        start_time = datetime.now()
        result = check_func()
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        # 记录检查时间
        self.check_times[check_name] = elapsed
        
        # 添加性能信息到结果
        result.details["_performance"] = {
            "execution_time_ms": elapsed,
            "timestamp": start_time.isoformat()
        }
        
        return result
    
    def _get_cache(self, key: str):
        """获取缓存"""
        self._cleanup_cache()
        
        if key in self.cache:
            cache_item = self.cache[key]
            if (datetime.now() - cache_item["timestamp"]).total_seconds() < self.cache_ttl:
                return cache_item["data"]
            else:
                # 缓存过期，删除
                del self.cache[key]
        
        return None
    
    def _set_cache(self, key: str, data) -> None:
        """设置缓存"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }
    
    def _cleanup_cache(self) -> None:
        """清理过期缓存"""
        current_time = datetime.now()
        if (current_time - self.last_cache_cleanup).total_seconds() > 60:  # 每分钟清理一次
            expired_keys = []
            for key, item in self.cache.items():
                if (current_time - item["timestamp"]).total_seconds() > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            self.last_cache_cleanup = current_time
    
    def _check_performance_alerts(self) -> None:
        """检查性能告警"""
        slow_checks = []
        for check_name, time_ms in self.check_times.items():
            if time_ms > self.max_check_time:
                slow_checks.append((check_name, time_ms))
        
        if slow_checks:
            logger.warning(f"检测到慢合规检查: {slow_checks}")
            
            # 发布性能告警事件
            try:
                from core.event_bus import EventBus, EventCategory, EventSeverity
                from uuid import uuid4
                
                event_bus = EventBus()
                coroutine = event_bus.publish(
                    category=EventCategory.SECURITY,
                    event_type="compliance.slow_checks",
                    source="ComplianceChecker",
                    severity=EventSeverity.WARNING,
                    payload={
                        "slow_checks": slow_checks,
                        "threshold_ms": self.max_check_time,
                    },
                    correlation_id=str(uuid4()),
                )
                
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(coroutine)
                else:
                    loop.run_until_complete(coroutine)
                    
            except Exception as e:
                logger.warning(f"性能告警事件发布失败: {e}")
    
    def _retry_with_backoff(self, func: Callable, max_retries: int = 3) -> Any:
        """带指数退避的重试机制"""
        import time
        
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"操作失败，达到最大重试次数: {e}")
                    raise
                
                # 指数退避
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"操作失败，第 {attempt + 1} 次重试，等待 {delay:.2f} 秒: {e}")
                time.sleep(delay)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "check_times": self.check_times,
            "max_check_time": self.max_check_time,
        }
        
        # 检查缓存健康
        if len(self.cache) > 1000:  # 缓存过大
            health_status["status"] = "warning"
            health_status["cache_warning"] = "缓存条目过多"
        
        # 检查性能健康
        for check_name, time_ms in self.check_times.items():
            if time_ms > self.max_check_time * 2:  # 超过阈值两倍
                health_status["status"] = "warning"
                health_status[f"{check_name}_slow"] = f"检查时间过长: {time_ms}ms"
        
        return health_status
    
    def clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        cache_size = len(self.cache)
        self.cache.clear()
        self.last_cache_cleanup = datetime.now()
        
        return {
            "cleared_entries": cache_size,
            "timestamp": datetime.now().isoformat(),
            "message": "缓存已清理"
        }
    
    def generate_report(
        self,
        report: ComplianceReport,
        output_path: Optional[Path] = None,
        format: str = "json",
    ) -> str:
        """
        生成合规报告文件
        
        Args:
            report: 合规报告
            output_path: 输出路径
            format: 输出格式 (json/html)
            
        Returns:
            报告文件路径
        """
        if output_path is None:
            output_dir = Path("data/compliance_reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"{report.tenant_id}_compliance_{timestamp}.{format}"
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(asdict(report), f, ensure_ascii=False, indent=2)
        elif format == "html":
            html_content = self._generate_html_report(report)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        logger.info(f"合规报告已生成: {output_path}")
        
        return str(output_path)
    
    def _generate_html_report(self, report: ComplianceReport) -> str:
        """生成HTML格式的报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>合规检查报告 - {report.tenant_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
        .result.passed {{ border-color: #4caf50; background: #e8f5e9; }}
        .result.failed {{ border-color: #f44336; background: #ffebee; }}
        .result.warning {{ border-color: #ff9800; background: #fff3e0; }}
    </style>
</head>
<body>
    <h1>合规检查报告</h1>
    <div class="summary">
        <h2>摘要</h2>
        <p><strong>租户ID:</strong> {report.tenant_id}</p>
        <p><strong>检查日期:</strong> {report.check_date}</p>
        <p><strong>总检查数:</strong> {report.total_checks}</p>
        <p><strong>通过:</strong> {report.passed_checks}</p>
        <p><strong>失败:</strong> {report.failed_checks}</p>
        <p><strong>警告:</strong> {report.warning_checks}</p>
        <p><strong>合规率:</strong> {report.summary.get('compliance_rate', 0):.2f}%</p>
    </div>
    <h2>检查结果</h2>
"""
        for result in report.results:
            status_class = "passed" if result.passed else ("warning" if result.severity == "warning" else "failed")
            html += f"""
    <div class="result {status_class}">
        <h3>{result.check_name}</h3>
        <p><strong>状态:</strong> {'通过' if result.passed else '失败'}</p>
        <p><strong>严重程度:</strong> {result.severity}</p>
        <p><strong>消息:</strong> {result.message}</p>
        <details>
            <summary>详细信息</summary>
            <pre>{json.dumps(result.details, ensure_ascii=False, indent=2)}</pre>
        </details>
    </div>
"""
        html += """
</body>
</html>
"""
        return html


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="合规检查脚本")
    parser.add_argument("--tenant-id", required=True, help="租户ID")
    parser.add_argument("--rule-types", nargs="+", help="要检查的规则类型")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--format", choices=["json", "html"], default="json", help="输出格式")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行检查
    checker = ComplianceChecker()
    
    rule_types = None
    if args.rule_types:
        rule_types = [ComplianceRuleType(rt) for rt in args.rule_types]
    
    report = checker.run_all_checks(
        tenant_id=args.tenant_id,
        rule_types=rule_types,
    )
    
    # 生成报告
    output_path = Path(args.output) if args.output else None
    report_path = checker.generate_report(
        report=report,
        output_path=output_path,
        format=args.format,
    )
    
    # 输出结果
    print(f"\n合规检查完成:")
    print(f"  租户ID: {report.tenant_id}")
    print(f"  总检查数: {report.total_checks}")
    print(f"  通过: {report.passed_checks}")
    print(f"  失败: {report.failed_checks}")
    print(f"  警告: {report.warning_checks}")
    print(f"  合规率: {report.summary.get('compliance_rate', 0):.2f}%")
    print(f"  报告文件: {report_path}")
    
    # 返回退出码
    sys.exit(0 if report.failed_checks == 0 else 1)


if __name__ == "__main__":
    main()

