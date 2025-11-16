"""
外部服务联调状态检查
用于确认抖音内容发布、同花顺行情等必要凭证是否就绪
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IntegrationStatus:
    name: str
    required_env: List[str]
    optional_env: List[str] = field(default_factory=list)

    def collect(self) -> Dict[str, str]:
        details: Dict[str, str] = {}
        for key in self.required_env:
            details[key] = "✅ 已配置" if os.environ.get(key) else "⚠️ 缺失"
        for key in self.optional_env:
            details[key] = "✅" if os.environ.get(key) else "⬜ 可选"
        ready = all(os.environ.get(key) for key in self.required_env)
        return {"ready": ready, "details": details}


class ExternalIntegrationStatus:
    def __init__(self):
        self.integrations = {
            "douyin_content": IntegrationStatus(
                name="抖音内容发布",
                required_env=["DOUYIN_CLIENT_KEY", "DOUYIN_CLIENT_SECRET", "DOUYIN_SERVICE_ID"],
                optional_env=["DOUYIN_REFRESH_TOKEN"],
            ),
            "stock_gateway": IntegrationStatus(
                name="同花顺行情/模拟盘",
                required_env=["THS_APP_KEY", "THS_APP_SECRET"],
                optional_env=["THS_SIM_ACCOUNT", "THS_SIM_PASSWORD"],
            ),
        }

    def get_status(self) -> Dict[str, Dict[str, str]]:
        return {key: integration.collect() for key, integration in self.integrations.items()}





