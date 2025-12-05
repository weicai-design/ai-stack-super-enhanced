"""
通知渠道配置文件
P0-018: 可观测体系增强 - 多渠道通知配置
"""

from typing import Dict, Any
from enum import Enum


class NotificationChannel(Enum):
    """通知渠道枚举"""
    EMAIL = "email"
    DINGTALK = "dingtalk"
    WECHAT_WORK = "wechat_work"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


# 默认通知配置模板
DEFAULT_NOTIFICATION_CONFIGS: Dict[NotificationChannel, Dict[str, Any]] = {
    NotificationChannel.EMAIL: {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_email": "noreply@yourcompany.com",
        "to_emails": ["devops@yourcompany.com", "alerts@yourcompany.com"],
        "subject_template": "[{severity}] {rule_name} - {timestamp}",
        "body_template": """
告警通知
========

**告警规则:** {rule_name}
**严重程度:** {severity}
**当前值:** {current_value}
**阈值:** {threshold}
**时间:** {timestamp}

**描述:**
{description}

**建议操作:**
{suggested_actions}

**详细信息:**
- 告警ID: {alert_id}
- 规则ID: {rule_id}
- 预测影响: {predicted_impact}
- 置信度: {confidence}

请及时处理此告警。
        """
    },
    
    NotificationChannel.DINGTALK: {
        "enabled": False,
        "webhook_url": "",
        "secret": "",
        "message_template": {
            "msgtype": "markdown",
            "markdown": {
                "title": "{severity}告警: {rule_name}",
                "text": """### {severity}告警: {rule_name}
                
**告警详情:**
- 规则: {rule_name}
- 严重程度: {severity}
- 当前值: {current_value}
- 阈值: {threshold}
- 时间: {timestamp}

**描述:**
{description}

**建议操作:**
{suggested_actions}

**详细信息:**
- 告警ID: {alert_id}
- 规则ID: {rule_id}
- 预测影响: {predicted_impact}
- 置信度: {confidence}
                """
            }
        }
    },
    
    NotificationChannel.WECHAT_WORK: {
        "enabled": False,
        "corp_id": "",
        "agent_id": "",
        "secret": "",
        "message_template": {
            "touser": "@all",
            "msgtype": "text",
            "text": {
                "content": "[{severity}] {rule_name}\n当前值: {current_value}\n阈值: {threshold}\n时间: {timestamp}"
            }
        }
    },
    
    NotificationChannel.SLACK: {
        "enabled": False,
        "webhook_url": "",
        "channel": "#alerts",
        "username": "Alert Bot",
        "icon_emoji": ":warning:",
        "message_template": {
            "text": "*{severity} Alert: {rule_name}*",
            "attachments": [
                {
                    "color": "{color}",
                    "fields": [
                        {"title": "Current Value", "value": "{current_value}", "short": True},
                        {"title": "Threshold", "value": "{threshold}", "short": True},
                        {"title": "Time", "value": "{timestamp}", "short": False},
                        {"title": "Description", "value": "{description}", "short": False}
                    ]
                }
            ]
        }
    },
    
    NotificationChannel.WEBHOOK: {
        "enabled": False,
        "url": "",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}"
        },
        "payload_template": {
            "alert_id": "{alert_id}",
            "rule_name": "{rule_name}",
            "severity": "{severity}",
            "current_value": {current_value},
            "threshold": {threshold},
            "timestamp": "{timestamp}",
            "description": "{description}",
            "suggested_actions": {suggested_actions}
        }
    },
    
    NotificationChannel.SMS: {
        "enabled": False,
        "provider": "twilio",  # twilio, aliyun, tencent
        "account_sid": "",
        "auth_token": "",
        "from_number": "",
        "to_numbers": [""],
        "message_template": "[{severity}] {rule_name}: {current_value} > {threshold} at {timestamp}"
    }
}


# 严重程度到颜色的映射
SEVERITY_COLORS = {
    "info": "#36a64f",      # 绿色
    "warning": "#ffcc00",   # 黄色
    "error": "#ff9900",     # 橙色
    "critical": "#ff0000"   # 红色
}


# 告警模板变量
ALERT_TEMPLATE_VARIABLES = {
    "alert_id": "告警唯一标识",
    "rule_id": "规则ID",
    "rule_name": "规则名称",
    "severity": "严重程度",
    "current_value": "当前值",
    "threshold": "阈值",
    "timestamp": "时间戳",
    "description": "描述",
    "suggested_actions": "建议操作",
    "predicted_impact": "预测影响",
    "confidence": "置信度",
    "color": "颜色代码"
}


class NotificationConfigManager:
    """通知配置管理器"""
    
    def __init__(self, config_file: str = "notification_config.json"):
        self.config_file = config_file
        self.configs = DEFAULT_NOTIFICATION_CONFIGS.copy()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        import json
        import os
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_configs = json.load(f)
                    
                # 合并配置
                for channel_str, config in saved_configs.items():
                    channel = NotificationChannel(channel_str)
                    if channel in self.configs:
                        self.configs[channel].update(config)
                        
            except Exception as e:
                print(f"加载通知配置文件失败: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        import json
        
        try:
            # 转换为可序列化的格式
            config_to_save = {}
            for channel, config in self.configs.items():
                config_to_save[channel.value] = config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"保存通知配置文件失败: {e}")
    
    def enable_channel(self, channel: NotificationChannel, config: Dict[str, Any] = None):
        """启用通知渠道"""
        if channel not in self.configs:
            self.configs[channel] = DEFAULT_NOTIFICATION_CONFIGS.get(channel, {}).copy()
        
        if config:
            self.configs[channel].update(config)
        
        self.configs[channel]["enabled"] = True
        self.save_config()
    
    def disable_channel(self, channel: NotificationChannel):
        """禁用通知渠道"""
        if channel in self.configs:
            self.configs[channel]["enabled"] = False
            self.save_config()
    
    def get_channel_config(self, channel: NotificationChannel) -> Dict[str, Any]:
        """获取渠道配置"""
        return self.configs.get(channel, {}).copy()
    
    def get_enabled_channels(self) -> list:
        """获取已启用的渠道"""
        return [
            channel for channel, config in self.configs.items()
            if config.get("enabled", False)
        ]
    
    def format_message(self, channel: NotificationChannel, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化消息"""
        config = self.configs.get(channel, {})
        template = config.get("message_template", {})
        
        # 添加颜色信息
        alert_data["color"] = SEVERITY_COLORS.get(alert_data.get("severity", "info"), "#36a64f")
        
        # 格式化消息（简单的字符串替换）
        import json
        
        def format_dict(obj):
            if isinstance(obj, dict):
                return {k: format_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [format_dict(item) for item in obj]
            elif isinstance(obj, str):
                # 替换模板变量
                for key, value in alert_data.items():
                    placeholder = "{" + key + "}"
                    if placeholder in obj:
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value, ensure_ascii=False)
                        obj = obj.replace(placeholder, str(value))
                return obj
            else:
                return obj
        
        return format_dict(template)


# 全局配置管理器实例
_notification_config_manager: NotificationConfigManager = None


def get_notification_config_manager() -> NotificationConfigManager:
    """获取通知配置管理器实例"""
    global _notification_config_manager
    if _notification_config_manager is None:
        _notification_config_manager = NotificationConfigManager()
    return _notification_config_manager