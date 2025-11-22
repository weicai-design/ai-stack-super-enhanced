#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可配置API连接器
P2-304: 实现抖音、同花顺、ERP、内容平台等真实API的可配置接入
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional
import httpx
from datetime import datetime

from .api_credential_manager import get_credential_manager
from .api_retry_handler import APIRetryHandler, RetryStrategy, execute_with_retry

logger = logging.getLogger(__name__)


class ConfigurableAPIConnector:
    """
    可配置API连接器
    
    功能：
    1. 统一管理多个平台的API接入
    2. 自动从凭证管理器获取凭证
    3. 自动重试机制
    4. 可配置的API端点
    """
    
    def __init__(self):
        self.credential_manager = get_credential_manager()
        self.retry_handler = APIRetryHandler(
            max_retries=3,
            initial_delay=1.0,
            strategy=RetryStrategy.EXPONENTIAL,
        )
        self.connectors: Dict[str, Any] = {}
        
        logger.info("可配置API连接器初始化完成")
    
    def register_connector(
        self,
        platform: str,
        connector_class: type,
        config: Optional[Dict[str, Any]] = None,
    ):
        """注册平台连接器"""
        try:
            # 从凭证管理器获取凭证
            credentials = self.credential_manager.get_all_credentials(platform)
            
            # 合并配置
            final_config = (config or {}).copy()
            final_config.update(credentials)
            
            # 创建连接器实例
            connector = connector_class(final_config)
            connector.retry_handler = self.retry_handler
            connector.credential_manager = self.credential_manager
            
            self.connectors[platform] = connector
            
            logger.info(f"已注册平台连接器: {platform}")
            
        except Exception as e:
            logger.error(f"注册连接器失败: {platform} - {e}", exc_info=True)
    
    def get_connector(self, platform: str) -> Optional[Any]:
        """获取平台连接器"""
        return self.connectors.get(platform)
    
    async def call_api(
        self,
        platform: str,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        调用API
        
        Args:
            platform: 平台名称
            endpoint: API端点
            method: HTTP方法
            params: 查询参数
            data: 请求体
            headers: 请求头
            
        Returns:
            API响应
        """
        connector = self.get_connector(platform)
        if not connector:
            raise ValueError(f"平台 {platform} 未注册")
        
        # 使用重试机制执行
        async def _make_request():
            return await connector.make_request(
                endpoint=endpoint,
                method=method,
                params=params,
                data=data,
                headers=headers,
            )
        
        return await execute_with_retry(
            _make_request,
            max_retries=self.retry_handler.max_retries,
            initial_delay=self.retry_handler.initial_delay,
        )


class BaseAPIConnector:
    """基础API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30.0)
        self.retry_handler: Optional[APIRetryHandler] = None
        self.credential_manager = None
        
        # HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_default_headers(),
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            "User-Agent": "AI-Stack/1.0",
            "Content-Type": "application/json",
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头（子类实现）"""
        return {}
    
    async def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """发起HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        # 合并请求头
        request_headers = self._get_default_headers()
        request_headers.update(self._get_auth_headers())
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=params, headers=request_headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=params, headers=request_headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, params=params, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params, headers=request_headers)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers),
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API请求失败: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"API请求异常: {e}")
            raise
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


class DouyinAPIConnector(BaseAPIConnector):
    """抖音API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", "https://open.douyin.com")
        super().__init__(config)
        
        self.app_id = config.get("app_id") or config.get("DOUYIN_APP_ID")
        self.app_secret = config.get("app_secret") or config.get("DOUYIN_APP_SECRET")
        self.access_token = config.get("access_token") or config.get("DOUYIN_ACCESS_TOKEN")
        self.client_key = config.get("client_key") or config.get("DOUYIN_CLIENT_KEY")
        self.client_secret = config.get("client_secret") or config.get("DOUYIN_CLIENT_SECRET")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取抖音认证头"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.client_key and self.client_secret:
            # 使用Client Key/Secret认证
            headers["X-Client-Key"] = self.client_key
            headers["X-Client-Secret"] = self.client_secret
        return headers
    
    async def publish_video(
        self,
        video_url: str,
        title: str,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发布视频"""
        data = {
            "video_url": video_url,
            "title": title,
            "description": description or "",
            "cover_url": cover_url,
        }
        return await self.make_request("/video/publish", method="POST", data=data)
    
    async def get_video_stats(self, video_id: str) -> Dict[str, Any]:
        """获取视频统计"""
        return await self.make_request(f"/video/{video_id}/stats", method="GET")
    
    async def refresh_token(self) -> Dict[str, Any]:
        """刷新访问令牌"""
        if not self.app_id or not self.app_secret:
            raise ValueError("缺少app_id或app_secret")
        
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "grant_type": "client_credential",
        }
        result = await self.make_request("/oauth/token", method="POST", data=data)
        
        if result.get("success") and "access_token" in result.get("data", {}):
            self.access_token = result["data"]["access_token"]
            # 保存到凭证管理器
            if self.credential_manager:
                self.credential_manager.set_credential(
                    "douyin",
                    "access_token",
                    self.access_token,
                )
        
        return result


class Ths123APIConnector(BaseAPIConnector):
    """同花顺API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", "https://api.10jqka.com.cn")
        super().__init__(config)
        
        self.api_key = config.get("api_key") or config.get("TONGHUASHUN_API_KEY")
        self.api_secret = config.get("api_secret") or config.get("TONGHUASHUN_API_SECRET")
        self.app_key = config.get("app_key") or config.get("THS_APP_KEY")
        self.app_secret = config.get("app_secret") or config.get("THS_APP_SECRET")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取同花顺认证头"""
        headers = {}
        if self.api_key and self.api_secret:
            headers["X-API-Key"] = self.api_key
            headers["X-API-Secret"] = self.api_secret
        elif self.app_key and self.app_secret:
            headers["X-App-Key"] = self.app_key
            headers["X-App-Secret"] = self.app_secret
        return headers
    
    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """获取股票行情"""
        return await self.make_request(f"/stock/{symbol}/quote", method="GET")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return await self.make_request("/account/info", method="GET")
    
    async def place_order(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: int,
    ) -> Dict[str, Any]:
        """下单"""
        data = {
            "symbol": symbol,
            "action": action,
            "price": price,
            "quantity": quantity,
        }
        return await self.make_request("/order/place", method="POST", data=data)


class ERPAPIConnector(BaseAPIConnector):
    """ERP API连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        config.setdefault("base_url", config.get("ERP_API_URL", "http://localhost:8013"))
        super().__init__(config)
        
        self.api_key = config.get("api_key") or config.get("ERP_API_KEY")
        self.username = config.get("username") or config.get("ERP_USERNAME")
        self.password = config.get("password") or config.get("ERP_PASSWORD")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取ERP认证头"""
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.username and self.password:
            # 基本认证
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        return headers
    
    async def get_financial_data(self, period: str = "month") -> Dict[str, Any]:
        """获取财务数据"""
        return await self.make_request(
            "/api/finance/dashboard",
            method="GET",
            params={"period": period},
        )
    
    async def get_orders(self, status: Optional[str] = None) -> Dict[str, Any]:
        """获取订单列表"""
        params = {}
        if status:
            params["status"] = status
        return await self.make_request("/api/orders", method="GET", params=params)
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建订单"""
        return await self.make_request("/api/orders", method="POST", data=order_data)


class ContentPlatformAPIConnector(BaseAPIConnector):
    """内容平台API连接器（通用）"""
    
    def __init__(self, config: Dict[str, Any], platform_name: str = "content"):
        config.setdefault("base_url", config.get("CONTENT_API_URL", "http://localhost:8016"))
        super().__init__(config)
        
        self.platform_name = platform_name
        self.access_token = config.get("access_token") or config.get(f"{platform_name.upper()}_ACCESS_TOKEN")
        self.api_key = config.get("api_key") or config.get(f"{platform_name.upper()}_API_KEY")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取内容平台认证头"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def publish_content(
        self,
        content: str,
        title: Optional[str] = None,
        images: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """发布内容"""
        data = {
            "content": content,
            "title": title,
            "images": images or [],
            "tags": tags or [],
        }
        return await self.make_request("/api/content/publish", method="POST", data=data)
    
    async def get_content_stats(self, content_id: str) -> Dict[str, Any]:
        """获取内容统计"""
        return await self.make_request(f"/api/content/{content_id}/stats", method="GET")


# 全局连接器管理器
_connector_manager: Optional[ConfigurableAPIConnector] = None


def get_api_connector_manager() -> ConfigurableAPIConnector:
    """获取API连接器管理器实例"""
    global _connector_manager
    if _connector_manager is None:
        _connector_manager = ConfigurableAPIConnector()
        
        # 自动注册所有平台连接器
        _connector_manager.register_connector("douyin", DouyinAPIConnector)
        _connector_manager.register_connector("ths123", Ths123APIConnector)
        _connector_manager.register_connector("erp", ERPAPIConnector)
        _connector_manager.register_connector("content", ContentPlatformAPIConnector)
    
    return _connector_manager

