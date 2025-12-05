"""
模块API适配器
为ERP、内容、趋势模块提供统一的API适配器
"""

from __future__ import annotations

import logging
import httpx
from typing import Any, Dict, Optional
from datetime import datetime

from .configurable_api_connector import BaseAPIConnector

logger = logging.getLogger(__name__)


class ERPAPIConnector(BaseAPIConnector):
    """ERP模块API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", config.get("erp_api_url", "http://localhost:8013"))
        super().__init__(config)
        self.api_key = config.get("api_key") or config.get("ERP_API_KEY")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取ERP认证头"""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers


class ContentAPIConnector(BaseAPIConnector):
    """内容模块API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", config.get("content_api_url", "http://localhost:8016"))
        super().__init__(config)
        self.api_key = config.get("api_key") or config.get("CONTENT_API_KEY")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取内容模块认证头"""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers


class TrendAPIConnector(BaseAPIConnector):
    """趋势模块API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", config.get("trend_api_url", "http://localhost:8015"))
        super().__init__(config)
        self.api_key = config.get("api_key") or config.get("TREND_API_KEY")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取趋势模块认证头"""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

