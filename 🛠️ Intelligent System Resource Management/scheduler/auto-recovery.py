# ai-stack-super-enhanced/🛠️ Intelligent System Resource Management/scheduler/454. auto-recovery.py

"""
自动恢复模块
负责系统异常时的自动检测、诊断和恢复
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """恢复动作枚举"""

    RESTART_SERVICE = "restart_service"
    RELOAD_CONFIG = "reload_config"
    CLEAR_CACHE = "clear_cache"
    SCALE_RESOURCES = "scale_resources"
    FAILOVER = "failover"
    ALERT_ONLY = "alert_only"


class IssueSeverity(Enum):
    """问题严重性枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RecoveryPlan:
    """恢复计划数据类"""

    issue_id: str
    description: str
    severity: IssueSeverity
    detected_at: datetime
    recovery_actions: List[RecoveryAction]
    expected_duration: int  # 秒
    dependencies: List[str]
    rollback_plan: List[str]


class AutoRecovery:
    """
    自动恢复引擎
    实现系统异常的自动检测、诊断和恢复
    """

    def __init__(self, system_manager=None):
        self.system_manager = system_manager
        self.recovery_history: List[Dict[str, Any]] = []
        self.issue_patterns: Dict[str, Any] = {}
        self.recovery_strategies: Dict[str, RecoveryPlan] = {}

        # 恢复配置
        self.recovery_config = {
            "max_recovery_attempts": 3,
            "recovery_timeout": 300,  # 5分钟
            "auto_recovery_enabled": True,
            "alert_on_recovery": True,
            "backoff_strategy": "exponential",  # exponential, linear, fixed
        }

        # 问题模式库
        self._initialize_issue_patterns()
        self._initialize_recovery_strategies()

        logger.info("自动恢复引擎初始化完成")

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化自动恢复引擎"""
        if config:
            self.recovery_config.update(config)

        if core_services:
            self.system_manager = core_services.get("system_manager")

        logger.info("自动恢复引擎启动完成")

    def _initialize_issue_patterns(self):
        """初始化问题模式库"""
        self.issue_patterns = {
            "high_cpu_usage": {
                "description": "CPU使用率过高",
                "detection_rules": [
                    {
                        "metric": "cpu_usage",
                        "condition": ">",
                        "threshold": 90,
                        "duration": 60,
                    },
                    {
                        "metric": "system_load",
                        "condition": ">",
                        "threshold": "cpu_count*2",
                        "duration": 120,
                    },
                ],
                "severity": IssueSeverity.HIGH,
            },
            "memory_leak": {
                "description": "内存泄漏",
                "detection_rules": [
                    {
                        "metric": "memory_usage",
                        "condition": ">",
                        "threshold": 95,
                        "duration": 300,
                    },
                    {
                        "metric": "memory_trend",
                        "condition": "increasing",
                        "threshold": 10,
                        "duration": 600,
                    },
                ],
                "severity": IssueSeverity.CRITICAL,
            },
            "service_unresponsive": {
                "description": "服务无响应",
                "detection_rules": [
                    {
                        "metric": "response_time",
                        "condition": ">",
                        "threshold": 10,
                        "duration": 30,
                    },
                    {
                        "metric": "error_rate",
                        "condition": ">",
                        "threshold": 50,
                        "duration": 60,
                    },
                ],
                "severity": IssueSeverity.HIGH,
            },
            "disk_space_low": {
                "description": "磁盘空间不足",
                "detection_rules": [
                    {
                        "metric": "disk_usage",
                        "condition": ">",
                        "threshold": 95,
                        "duration": 0,
                    }
                ],
                "severity": IssueSeverity.CRITICAL,
            },
            "network_issues": {
                "description": "网络连接问题",
                "detection_rules": [
                    {
                        "metric": "network_timeout_rate",
                        "condition": ">",
                        "threshold": 20,
                        "duration": 120,
                    },
                    {
                        "metric": "connection_errors",
                        "condition": ">",
                        "threshold": 10,
                        "duration": 60,
                    },
                ],
                "severity": IssueSeverity.MEDIUM,
            },
        }

    def _initialize_recovery_strategies(self):
        """初始化恢复策略"""
        # CPU使用率过高恢复策略
        self.recovery_strategies["high_cpu_usage"] = RecoveryPlan(
            issue_id="high_cpu_usage",
            description="CPU使用率过高恢复",
            severity=IssueSeverity.HIGH,
            detected_at=datetime.utcnow(),
            recovery_actions=[
                RecoveryAction.CLEAR_CACHE,
                RecoveryAction.RESTART_SERVICE,
                RecoveryAction.SCALE_RESOURCES,
            ],
            expected_duration=120,
            dependencies=["resource_manager", "service_manager"],
            rollback_plan=["restore_previous_config", "revert_resource_scaling"],
        )

        # 内存泄漏恢复策略
        self.recovery_strategies["memory_leak"] = RecoveryPlan(
            issue_id="memory_leak",
            description="内存泄漏恢复",
            severity=IssueSeverity.CRITICAL,
            detected_at=datetime.utcnow(),
            recovery_actions=[
                RecoveryAction.RESTART_SERVICE,
                RecoveryAction.CLEAR_CACHE,
                RecoveryAction.FAILOVER,
            ],
            expected_duration=180,
            dependencies=["resource_manager", "service_manager", "backup_manager"],
            rollback_plan=["restore_from_backup", "activate_standby_service"],
        )

        # 服务无响应恢复策略
        self.recovery_strategies["service_unresponsive"] = RecoveryPlan(
            issue_id="service_unresponsive",
            description="服务无响应恢复",
            severity=IssueSeverity.HIGH,
            detected_at=datetime.utcnow(),
            recovery_actions=[
                RecoveryAction.RESTART_SERVICE,
                RecoveryAction.FAILOVER,
                RecoveryAction.ALERT_ONLY,
            ],
            expected_duration=90,
            dependencies=["service_manager", "health_monitor"],
            rollback_plan=["restore_previous_service", "reactivate_primary"],
        )

        # 磁盘空间不足恢复策略
        self.recovery_strategies["disk_space_low"] = RecoveryPlan(
            issue_id="disk_space_low",
            description="磁盘空间不足恢复",
            severity=IssueSeverity.CRITICAL,
            detected_at=datetime.utcnow(),
            recovery_actions=[RecoveryAction.CLEAR_CACHE, RecoveryAction.ALERT_ONLY],
            expected_duration=300,
            dependencies=["storage_manager", "log_manager"],
            rollback_plan=["stop_cleanup_immediately", "restore_critical_files"],
        )

    async def monitor_and_recover(self) -> Dict[str, Any]:
        """
        监控系统状态并执行自动恢复
        返回恢复执行报告
        """
        if not self.recovery_config["auto_recovery_enabled"]:
            return {"status": "disabled", "timestamp": datetime.utcnow().isoformat()}

        try:
            # 检测系统问题
            detected_issues = await self._detect_system_issues()

            if not detected_issues:
                return {
                    "status": "healthy",
                    "issues_detected": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # 执行恢复操作
            recovery_results = []
            for issue in detected_issues:
                recovery_result = await self._execute_recovery(issue)
                recovery_results.append(recovery_result)

            # 生成恢复报告
            report = await self._generate_recovery_report(
                detected_issues, recovery_results
            )

            # 记录恢复历史
            await self._record_recovery_history(report)

            return report

        except Exception as e:
            logger.error(f"自动恢复执行失败: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _detect_system_issues(self) -> List[Dict[str, Any]]:
        """检测系统问题"""
        detected_issues = []

        try:
            # 获取系统健康状态
            if hasattr(self.system_manager, "health_monitor"):
                health_report = (
                    await self.system_manager.health_monitor.analyze_system_health()
                )

                # 检查各项指标
                for issue_pattern_id, pattern in self.issue_patterns.items():
                    if await self._evaluate_issue_pattern(health_report, pattern):
                        issue = {
                            "id": issue_pattern_id,
                            "description": pattern["description"],
                            "severity": pattern["severity"].value,
                            "detected_at": datetime.utcnow(),
                            "pattern": pattern,
                            "health_data": health_report,
                        }
                        detected_issues.append(issue)

            # 检查服务状态
            service_issues = await self._check_service_health()
            detected_issues.extend(service_issues)

        except Exception as e:
            logger.error(f"问题检测失败: {str(e)}")

        return detected_issues

    async def _evaluate_issue_pattern(self, health_report: Dict, pattern: Dict) -> bool:
        """评估问题模式是否匹配"""
        try:
            rules = pattern.get("detection_rules", [])
            matched_rules = 0

            for rule in rules:
                metric = rule["metric"]
                condition = rule["condition"]
                threshold = rule["threshold"]
                duration = rule.get("duration", 0)

                # 获取指标值
                metric_value = await self._get_metric_value(health_report, metric)
                if metric_value is None:
                    continue

                # 评估条件
                if await self._evaluate_condition(metric_value, condition, threshold):
                    matched_rules += 1

            # 需要匹配所有规则才认为检测到问题
            return matched_rules == len(rules)

        except Exception as e:
            logger.error(
                f"评估问题模式失败: {pattern.get('description', 'unknown')} - {str(e)}"
            )
            return False

    async def _get_metric_value(
        self, health_report: Dict, metric_name: str
    ) -> Optional[float]:
        """从健康报告中获取指标值"""
        try:
            if metric_name in health_report.get("metrics", {}):
                metric_data = health_report["metrics"][metric_name]
                if hasattr(metric_data, "value"):
                    return metric_data.value
                elif isinstance(metric_data, dict) and "value" in metric_data:
                    return metric_data["value"]

            # 检查组件健康状态
            components_health = health_report.get("components_health", {})
            for component, health_data in components_health.items():
                if metric_name in health_data:
                    return health_data[metric_name]

            return None

        except Exception as e:
            logger.error(f"获取指标值失败: {metric_name} - {str(e)}")
            return None

    async def _evaluate_condition(
        self, value: float, condition: str, threshold: Any
    ) -> bool:
        """评估条件表达式"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == ">=":
                return value >= threshold
            elif condition == "<":
                return value < threshold
            elif condition == "<=":
                return value <= threshold
            elif condition == "==":
                return value == threshold
            elif condition == "increasing":
                # 简化处理，实际应该基于历史数据
                return value > threshold
            else:
                logger.warning(f"未知条件操作符: {condition}")
                return False

        except Exception as e:
            logger.error(f"评估条件失败: {value} {condition} {threshold} - {str(e)}")
            return False

    async def _check_service_health(self) -> List[Dict[str, Any]]:
        """检查服务健康状态"""
        service_issues = []

        try:
            if self.system_manager:
                modules_health = await self.system_manager.get_modules_health()

                for module_name, health_info in modules_health.items():
                    status = health_info.get("status", "unknown")
                    if status in ["unhealthy", "degraded", "critical"]:
                        issue = {
                            "id": f"service_{module_name}_unhealthy",
                            "description": f"服务 {module_name} 状态异常: {status}",
                            "severity": IssueSeverity.HIGH.value,
                            "detected_at": datetime.utcnow(),
                            "service": module_name,
                            "health_status": health_info,
                        }
                        service_issues.append(issue)

        except Exception as e:
            logger.error(f"检查服务健康失败: {str(e)}")

        return service_issues

    async def _execute_recovery(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """执行恢复操作"""
        issue_id = issue["id"]
        recovery_plan = self.recovery_strategies.get(issue_id)

        if not recovery_plan:
            logger.warning(f"未找到恢复策略: {issue_id}")
            return {
                "issue_id": issue_id,
                "status": "no_recovery_plan",
                "timestamp": datetime.utcnow().isoformat(),
            }

        try:
            logger.info(f"开始执行恢复: {issue['description']}")

            recovery_result = {
                "issue_id": issue_id,
                "recovery_plan": recovery_plan.issue_id,
                "actions_executed": [],
                "start_time": datetime.utcnow(),
                "status": "in_progress",
            }

            # 执行恢复动作
            for action in recovery_plan.recovery_actions:
                action_result = await self._execute_recovery_action(action, issue)
                recovery_result["actions_executed"].append(
                    {"action": action.value, "result": action_result}
                )

                # 如果动作失败，考虑执行回滚
                if not action_result.get("success", False):
                    logger.warning(f"恢复动作失败: {action.value}")
                    await self._execute_rollback(recovery_plan, action)

            recovery_result["end_time"] = datetime.utcnow()
            recovery_result["status"] = "completed"
            recovery_result["duration"] = (
                recovery_result["end_time"] - recovery_result["start_time"]
            ).total_seconds()

            logger.info(
                f"恢复完成: {issue['description']}, 耗时: {recovery_result['duration']}秒"
            )

            return recovery_result

        except Exception as e:
            logger.error(f"执行恢复失败: {issue_id} - {str(e)}")
            return {
                "issue_id": issue_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _execute_recovery_action(
        self, action: RecoveryAction, issue: Dict
    ) -> Dict[str, Any]:
        """执行单个恢复动作"""
        try:
            if action == RecoveryAction.RESTART_SERVICE:
                return await self._restart_service(issue)
            elif action == RecoveryAction.RELOAD_CONFIG:
                return await self._reload_config(issue)
            elif action == RecoveryAction.CLEAR_CACHE:
                return await self._clear_cache(issue)
            elif action == RecoveryAction.SCALE_RESOURCES:
                return await self._scale_resources(issue)
            elif action == RecoveryAction.FAILOVER:
                return await self._failover_service(issue)
            elif action == RecoveryAction.ALERT_ONLY:
                return await self._send_alert(issue)
            else:
                return {"success": False, "error": f"未知恢复动作: {action}"}

        except Exception as e:
            logger.error(f"执行恢复动作失败: {action.value} - {str(e)}")
            return {"success": False, "error": str(e)}

    async def _restart_service(self, issue: Dict) -> Dict[str, Any]:
        """重启服务"""
        try:
            service_name = issue.get("service", "unknown")
            logger.info(f"重启服务: {service_name}")

            # 模拟重启操作
            await asyncio.sleep(2)

            return {
                "success": True,
                "action": "restart_service",
                "service": service_name,
                "message": f"服务 {service_name} 重启完成",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _reload_config(self, issue: Dict) -> Dict[str, Any]:
        """重新加载配置"""
        try:
            logger.info("重新加载系统配置")

            # 模拟配置重载
            await asyncio.sleep(1)

            return {
                "success": True,
                "action": "reload_config",
                "message": "配置重载完成",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _clear_cache(self, issue: Dict) -> Dict[str, Any]:
        """清理缓存"""
        try:
            logger.info("清理系统缓存")

            # 模拟缓存清理
            await asyncio.sleep(3)

            return {"success": True, "action": "clear_cache", "message": "缓存清理完成"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _scale_resources(self, issue: Dict) -> Dict[str, Any]:
        """扩展资源"""
        try:
            logger.info("扩展系统资源")

            # 模拟资源扩展
            await asyncio.sleep(5)

            return {
                "success": True,
                "action": "scale_resources",
                "message": "资源扩展完成",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _failover_service(self, issue: Dict) -> Dict[str, Any]:
        """服务故障转移"""
        try:
            service_name = issue.get("service", "unknown")
            logger.info(f"执行服务故障转移: {service_name}")

            # 模拟故障转移
            await asyncio.sleep(10)

            return {
                "success": True,
                "action": "failover",
                "service": service_name,
                "message": f"服务 {service_name} 故障转移完成",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _send_alert(self, issue: Dict) -> Dict[str, Any]:
        """发送警报"""
        try:
            logger.info(f"发送问题警报: {issue['description']}")

            # 模拟发送警报
            await asyncio.sleep(1)

            return {"success": True, "action": "send_alert", "message": "警报发送完成"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_rollback(
        self, recovery_plan: RecoveryPlan, failed_action: RecoveryAction
    ):
        """执行回滚操作"""
        try:
            logger.warning(f"执行回滚操作，针对失败动作: {failed_action.value}")

            for rollback_step in recovery_plan.rollback_plan:
                await self._execute_rollback_step(rollback_step)

        except Exception as e:
            logger.error(f"回滚操作失败: {str(e)}")

    async def _execute_rollback_step(self, rollback_step: str):
        """执行单个回滚步骤"""
        try:
            logger.info(f"执行回滚步骤: {rollback_step}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"回滚步骤失败: {rollback_step} - {str(e)}")

    async def _generate_recovery_report(
        self, issues: List[Dict], recovery_results: List[Dict]
    ) -> Dict[str, Any]:
        """生成恢复报告"""
        successful_recoveries = [
            r for r in recovery_results if r.get("status") == "completed"
        ]
        failed_recoveries = [r for r in recovery_results if r.get("status") == "failed"]

        return {
            "status": "completed" if len(successful_recoveries) > 0 else "partial",
            "total_issues": len(issues),
            "issues_resolved": len(successful_recoveries),
            "issues_failed": len(failed_recoveries),
            "detected_issues": issues,
            "recovery_results": recovery_results,
            "summary": await self._generate_recovery_summary(issues, recovery_results),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _generate_recovery_summary(
        self, issues: List[Dict], recovery_results: List[Dict]
    ) -> str:
        """生成恢复摘要"""
        if not issues:
            return "系统运行正常，未检测到问题"

        resolved_count = len(
            [r for r in recovery_results if r.get("status") == "completed"]
        )

        if resolved_count == len(issues):
            return f"成功解决所有 {len(issues)} 个问题"
        elif resolved_count > 0:
            return f"部分解决，成功 {resolved_count} 个，失败 {len(issues) - resolved_count} 个"
        else:
            return f"恢复失败，所有 {len(issues)} 个问题均未解决"

    async def _record_recovery_history(self, recovery_report: Dict[str, Any]):
        """记录恢复历史"""
        try:
            history_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "report": recovery_report,
            }

            self.recovery_history.append(history_entry)

            # 保持历史记录大小
            if len(self.recovery_history) > 1000:
                self.recovery_history = self.recovery_history[-1000:]

        except Exception as e:
            logger.error(f"记录恢复历史失败: {str(e)}")

    async def get_recovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取恢复历史"""
        return self.recovery_history[-limit:] if self.recovery_history else []

    async def add_custom_recovery_plan(
        self, issue_id: str, recovery_plan: RecoveryPlan
    ):
        """添加自定义恢复计划"""
        self.recovery_strategies[issue_id] = recovery_plan
        logger.info(f"添加自定义恢复计划: {issue_id}")

    async def enable_auto_recovery(self):
        """启用自动恢复"""
        self.recovery_config["auto_recovery_enabled"] = True
        logger.info("自动恢复已启用")

    async def disable_auto_recovery(self):
        """禁用自动恢复"""
        self.recovery_config["auto_recovery_enabled"] = False
        logger.info("自动恢复已禁用")

    async def stop(self):
        """停止自动恢复引擎"""
        logger.info("自动恢复引擎停止")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态（实现BaseModule接口）"""
        return {
            "status": "healthy",
            "auto_recovery_enabled": self.recovery_config["auto_recovery_enabled"],
            "recovery_strategies_count": len(self.recovery_strategies),
            "recovery_history_count": len(self.recovery_history),
            "timestamp": datetime.utcnow().isoformat(),
        }


# 模块导出
__all__ = ["AutoRecovery", "RecoveryAction", "IssueSeverity", "RecoveryPlan"]
