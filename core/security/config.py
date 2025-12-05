"""
安全配置模块
"""

from typing import Dict, Any


def get_security_settings() -> Dict[str, Any]:
    """获取安全配置"""
    return {
        "api_key_required": True,
        "rate_limit_enabled": True,
        "audit_enabled": True,
        "cors_enabled": True,
        "max_request_size": "10MB"
    }