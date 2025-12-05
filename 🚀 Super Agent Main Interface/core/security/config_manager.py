"""
安全配置管理器

功能：
- 统一管理安全相关配置
- 支持环境变量配置和默认值
- 配置验证和健康检查
- 配置热重载支持
- 配置变更通知机制

架构设计说明：
- 采用单例模式确保配置一致性
- 支持多环境配置（开发/测试/生产）
- 配置项分组管理，便于维护
- 内置配置验证和错误恢复机制

技术选型：
- Python标准库实现，无外部依赖
- 支持JSON格式配置解析
- 环境变量优先级高于默认配置

部署配置：
- 通过环境变量覆盖默认配置
- 支持配置文件路径配置
- 配置热重载间隔可配置
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import uuid4

logger = logging.getLogger(__name__)


class SecurityConfigManager:
    """安全配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config = {}
        self.last_reload = datetime.now()
        self.reload_interval = int(os.getenv("SECURITY_CONFIG_RELOAD_INTERVAL", "300"))  # 默认5分钟
        
        # 初始化配置
        self._load_config()
        
        logger.info("安全配置管理器初始化完成")
    
    def _load_config(self) -> None:
        """加载配置"""
        # RBAC权限配置
        self.config["rbac"] = self._load_rbac_config()
        
        # 审计配置
        self.config["audit"] = self._load_audit_config()
        
        # 合规检查配置
        self.config["compliance"] = self._load_compliance_config()
        
        # 安全策略配置
        self.config["security_policy"] = self._load_security_policy_config()
        
        # 监控告警配置
        self.config["monitoring"] = self._load_monitoring_config()
        
        self.last_reload = datetime.now()
    
    def _load_rbac_config(self) -> Dict[str, Any]:
        """加载RBAC配置"""
        return {
            "default_roles": os.getenv("RBAC_DEFAULT_ROLES", "viewer").split(","),
            "extra_permissions": self._parse_json_config("RBAC_EXTRA_PERMISSIONS", {}),
            "permission_separator": os.getenv("RBAC_PERMISSION_SEPARATOR", ":"),
            "wildcard_permission": os.getenv("RBAC_WILDCARD_PERMISSION", "*"),
        }
    
    def _load_audit_config(self) -> Dict[str, Any]:
        """加载审计配置"""
        return {
            "failure_rate_threshold": int(os.getenv("AUDIT_FAILURE_RATE_THRESHOLD", "5")),
            "critical_event_count_threshold": int(os.getenv("CRITICAL_EVENT_COUNT_THRESHOLD", "10")),
            "slow_request_threshold": int(os.getenv("SLOW_REQUEST_THRESHOLD", "5000")),
            "critical_events": os.getenv("CRITICAL_SECURITY_EVENTS", "unauthorized_access,data_breach,privilege_escalation").split(","),
            "retention_days": int(os.getenv("AUDIT_RETENTION_DAYS", "30")),
        }
    
    def _load_compliance_config(self) -> Dict[str, Any]:
        """加载合规检查配置"""
        return {
            "cache_ttl": int(os.getenv("COMPLIANCE_CACHE_TTL", "300")),
            "max_check_time": int(os.getenv("MAX_COMPLIANCE_CHECK_TIME", "10000")),
            "retry_count": int(os.getenv("COMPLIANCE_RETRY_COUNT", "3")),
            "check_interval": int(os.getenv("COMPLIANCE_CHECK_INTERVAL", "3600")),
        }
    
    def _load_security_policy_config(self) -> Dict[str, Any]:
        """加载安全策略配置"""
        return {
            "password_min_length": int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            "session_timeout": int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
            "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            "lockout_duration": int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
        }
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """加载监控配置"""
        return {
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            "alert_channels": os.getenv("ALERT_CHANNELS", "log,event").split(","),
            "metrics_export_interval": int(os.getenv("METRICS_EXPORT_INTERVAL", "300")),
        }
    
    def _parse_json_config(self, env_var: str, default: Any) -> Any:
        """解析JSON格式的配置"""
        value = os.getenv(env_var)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.warning("解析JSON配置失败 %s: %s", env_var, e)
        return default
    
    def get_config(self, section: str, key: str = None, default: Any = None) -> Any:
        """获取配置"""
        # 检查是否需要重新加载配置
        if (datetime.now() - self.last_reload).total_seconds() > self.reload_interval:
            self._load_config()
        
        if section not in self.config:
            logger.warning("配置节不存在: %s", section)
            return default
        
        if key is None:
            return self.config[section]
        
        return self.config[section].get(key, default)
    
    def set_config(self, section: str, key: str, value: Any) -> bool:
        """设置配置（仅内存中生效）"""
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        logger.info("配置已更新: %s.%s", section, key)
        return True
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性"""
        validation_result = {
            "status": "valid",
            "timestamp": datetime.now().isoformat(),
            "issues": [],
        }
        
        # 验证RBAC配置
        rbac_config = self.config.get("rbac", {})
        if not rbac_config.get("default_roles"):
            validation_result["issues"].append("RBAC默认角色配置为空")
        
        # 验证审计配置
        audit_config = self.config.get("audit", {})
        if audit_config.get("failure_rate_threshold", 0) < 0:
            validation_result["issues"].append("审计失败率阈值不能为负数")
        
        # 验证合规检查配置
        compliance_config = self.config.get("compliance", {})
        if compliance_config.get("max_check_time", 0) <= 0:
            validation_result["issues"].append("合规检查最大时间必须大于0")
        
        # 验证安全策略配置
        security_config = self.config.get("security_policy", {})
        if security_config.get("password_min_length", 0) < 6:
            validation_result["issues"].append("密码最小长度不能小于6")
        
        if validation_result["issues"]:
            validation_result["status"] = "invalid"
        
        return validation_result
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config_sections": list(self.config.keys()),
            "last_reload": self.last_reload.isoformat(),
            "reload_interval": self.reload_interval,
        }
        
        # 检查配置验证
        validation = self.validate_config()
        if validation["status"] == "invalid":
            health_status["status"] = "warning"
            health_status["validation_issues"] = validation["issues"]
        
        # 检查配置加载时间
        if (datetime.now() - self.last_reload).total_seconds() > self.reload_interval * 2:
            health_status["status"] = "warning"
            health_status["reload_warning"] = "配置长时间未重新加载"
        
        return health_status
    
    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置"""
        try:
            old_config = self.config.copy()
            self._load_config()
            
            # 检查配置变更
            changes = self._detect_config_changes(old_config, self.config)
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "message": "配置重新加载成功"
            }
            
            # 发布配置变更事件
            if changes:
                self._publish_config_change_event(changes)
            
            return result
            
        except Exception as e:
            logger.error("配置重新加载失败: %s", e)
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "message": "配置重新加载失败"
            }
    
    def _detect_config_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测配置变更"""
        changes = []
        
        # 检查新增的配置节
        for section in set(new_config.keys()) - set(old_config.keys()):
            changes.append({
                "type": "section_added",
                "section": section,
                "old_value": None,
                "new_value": new_config[section],
            })
        
        # 检查删除的配置节
        for section in set(old_config.keys()) - set(new_config.keys()):
            changes.append({
                "type": "section_removed",
                "section": section,
                "old_value": old_config[section],
                "new_value": None,
            })
        
        # 检查配置项变更
        for section in set(old_config.keys()) & set(new_config.keys()):
            old_section = old_config[section]
            new_section = new_config[section]
            
            # 检查配置项变更
            for key in set(old_section.keys()) | set(new_section.keys()):
                old_value = old_section.get(key)
                new_value = new_section.get(key)
                
                if old_value != new_value:
                    changes.append({
                        "type": "value_changed",
                        "section": section,
                        "key": key,
                        "old_value": old_value,
                        "new_value": new_value,
                    })
        
        return changes
    
    def _publish_config_change_event(self, changes: List[Dict[str, Any]]) -> None:
        """发布配置变更事件"""
        try:
            from core.event_bus import EventBus, EventCategory, EventSeverity
            
            event_bus = EventBus()
            coroutine = event_bus.publish(
                category=EventCategory.SECURITY,
                event_type="config.changed",
                source="SecurityConfigManager",
                severity=EventSeverity.INFO,
                payload={
                    "changes": changes,
                    "timestamp": datetime.now().isoformat(),
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
            logger.warning("配置变更事件发布失败: %s", e)


def get_security_config_manager() -> SecurityConfigManager:
    """获取安全配置管理器实例"""
    return SecurityConfigManager()