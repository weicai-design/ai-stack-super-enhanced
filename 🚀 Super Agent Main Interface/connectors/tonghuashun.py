#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺API连接器（生产级实现）
4.1: 实现行情查询、交易下单，集成密钥管理和重试策略
"""

from __future__ import annotations

import os
import logging
import asyncio
from typing import Any, Dict, Optional, List
from datetime import datetime
import httpx
import hashlib
import hmac
import time

# 导入密钥管理和重试处理器
from core.api_credential_manager import get_credential_manager
from core.api_retry_handler import APIRetryHandler, RetryStrategy, execute_with_retry

logger = logging.getLogger(__name__)


class TonghuashunConnector:
    """
    同花顺API连接器（生产级）
    
    功能：
    1. 行情查询（fetch_quote）
    2. 交易下单（place_order）
    3. 密钥管理（集成APICredentialManager）
    4. 重试策略（集成APIRetryHandler）
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    ):
        """
        初始化同花顺连接器
        
        Args:
            api_key: API密钥（优先从环境变量或凭证管理器获取）
            api_secret: API密钥（优先从环境变量或凭证管理器获取）
            app_key: 应用Key（备用认证方式）
            app_secret: 应用密钥（备用认证方式）
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_strategy: 重试策略
        """
        # 初始化凭证管理器
        self.credential_manager = get_credential_manager()
        
        # 从环境变量或凭证管理器获取密钥
        self.api_key = (
            api_key 
            or os.getenv("TONGHUASHUN_API_KEY")
            or self.credential_manager.get_credential("tonghuashun", "api_key")
        )
        self.api_secret = (
            api_secret
            or os.getenv("TONGHUASHUN_API_SECRET")
            or self.credential_manager.get_credential("tonghuashun", "api_secret")
        )
        self.app_key = (
            app_key
            or os.getenv("THS_APP_KEY")
            or self.credential_manager.get_credential("tonghuashun", "app_key")
        )
        self.app_secret = (
            app_secret
            or os.getenv("THS_APP_SECRET")
            or self.credential_manager.get_credential("tonghuashun", "app_secret")
        )
        
        # API配置
        self.base_url = base_url or os.getenv("THS_BASE_URL", "https://api.10jqka.com.cn")
        self.timeout = timeout
        
        # 验证密钥
        if not self.api_key or not self.api_secret:
            if not self.app_key or not self.app_secret:
                logger.warning(
                    "同花顺API密钥未配置，请设置环境变量或使用凭证管理器配置："
                    "TONGHUASHUN_API_KEY, TONGHUASHUN_API_SECRET 或 THS_APP_KEY, THS_APP_SECRET"
                )
        
        # 初始化重试处理器
        self.retry_handler = APIRetryHandler(
            max_retries=max_retries,
            initial_delay=1.0,
            max_delay=30.0,
            strategy=retry_strategy,
            retryable_status_codes=[429, 500, 502, 503, 504],
            retryable_exceptions=[
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.ConnectError,
                ConnectionError,
                TimeoutError,
            ],
        )
        
        # HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_default_headers(),
        )
        
        logger.info(f"同花顺连接器初始化完成，API地址: {self.base_url}")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            "User-Agent": "AI-Stack-THS-Connector/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        headers = {}
        
        # 优先使用API Key/Secret
        if self.api_key and self.api_secret:
            headers["X-API-Key"] = self.api_key
            headers["X-API-Secret"] = self.api_secret
        # 备用：使用App Key/Secret
        elif self.app_key and self.app_secret:
            headers["X-App-Key"] = self.app_key
            headers["X-App-Secret"] = self.app_secret
        
        return headers
    
    def _generate_signature(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
    ) -> str:
        """
        生成API签名（如果需要）
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: 请求体
            timestamp: 时间戳
            
        Returns:
            签名字符串
        """
        if not self.api_secret:
            return ""
        
        timestamp = timestamp or int(time.time())
        
        # 构建签名字符串
        sign_str = f"{method}{endpoint}{timestamp}"
        
        if params:
            sorted_params = sorted(params.items())
            sign_str += "&".join([f"{k}={v}" for k, v in sorted_params])
        
        if data:
            import json
            sign_str += json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.api_secret.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发起HTTP请求（带重试）
        
        Args:
            endpoint: API端点
            method: HTTP方法
            params: 查询参数
            data: 请求体
            headers: 额外请求头
            
        Returns:
            API响应
        """
        url = f"{self.base_url}{endpoint}"
        
        # 合并请求头
        request_headers = self._get_default_headers()
        request_headers.update(self._get_auth_headers())
        if headers:
            request_headers.update(headers)
        
        # 生成签名（如果需要）
        if self.api_secret and method.upper() in ["POST", "PUT", "DELETE"]:
            timestamp = int(time.time())
            signature = self._generate_signature(method, endpoint, params, data, timestamp)
            if signature:
                request_headers["X-Timestamp"] = str(timestamp)
                request_headers["X-Signature"] = signature
        
        async def _request():
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
                
                result = {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {},
                    "headers": dict(response.headers),
                }
                
                return result
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
                logger.error(f"同花顺API请求失败: {error_msg}")
                raise Exception(error_msg)
            except httpx.TimeoutException as e:
                error_msg = f"请求超时: {str(e)}"
                logger.error(f"同花顺API请求超时: {error_msg}")
                raise
            except Exception as e:
                error_msg = f"请求异常: {str(e)}"
                logger.error(f"同花顺API请求异常: {error_msg}")
                raise
        
        # 使用重试机制执行请求
        return await execute_with_retry(
            _request,
            max_retries=self.retry_handler.max_retries,
            initial_delay=self.retry_handler.initial_delay,
            max_delay=self.retry_handler.max_delay,
            strategy=self.retry_handler.strategy,
        )
    
    async def fetch_quote(
        self,
        symbol: str,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取股票行情
        
        Args:
            symbol: 股票代码（如：000001, 600519）
            market: 市场代码（如：SZ, SH），如果symbol包含市场代码则自动识别
            
        Returns:
            行情数据
            示例：
            {
                "success": True,
                "symbol": "000001.SZ",
                "name": "平安银行",
                "price": 12.50,
                "change": 0.25,
                "change_percent": 2.04,
                "volume": 1000000,
                "turnover": 12500000,
                "open": 12.30,
                "high": 12.60,
                "low": 12.20,
                "previous_close": 12.25,
                "timestamp": "2024-01-01T10:00:00"
            }
        """
        try:
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol, market)
            
            # 调用API
            response = await self._make_request(
                endpoint=f"/api/quote/{normalized_symbol}",
                method="GET",
                params={"symbol": normalized_symbol},
            )
            
            if not response.get("success"):
                raise Exception(f"获取行情失败: {response.get('error', '未知错误')}")
            
            data = response.get("data", {})
            
            # 标准化返回格式
            quote_data = {
                "success": True,
                "symbol": data.get("symbol", normalized_symbol),
                "name": data.get("name", ""),
                "price": float(data.get("price", 0)),
                "change": float(data.get("change", 0)),
                "change_percent": float(data.get("change_percent", 0)),
                "volume": int(data.get("volume", 0)),
                "turnover": float(data.get("turnover", 0)),
                "open": float(data.get("open", 0)),
                "high": float(data.get("high", 0)),
                "low": float(data.get("low", 0)),
                "previous_close": float(data.get("previous_close", 0)),
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
            }
            
            logger.info(f"成功获取行情: {normalized_symbol} = {quote_data['price']}")
            return quote_data
            
        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
            }
    
    async def place_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: str = "limit",
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        下单交易
        
        Args:
            symbol: 股票代码（如：000001, 600519）
            action: 交易方向（buy: 买入, sell: 卖出）
            quantity: 数量（股数，必须是100的整数倍）
            price: 价格（限价单必填，市价单可为None）
            order_type: 订单类型（limit: 限价, market: 市价）
            market: 市场代码（如：SZ, SH），如果symbol包含市场代码则自动识别
            
        Returns:
            订单结果
            示例：
            {
                "success": True,
                "order_id": "THS20240101100001",
                "symbol": "000001.SZ",
                "action": "buy",
                "quantity": 100,
                "price": 12.50,
                "order_type": "limit",
                "status": "pending",
                "created_at": "2024-01-01T10:00:00"
            }
        """
        try:
            # 验证参数
            if action not in ["buy", "sell"]:
                raise ValueError(f"无效的交易方向: {action}，必须是 'buy' 或 'sell'")
            
            if order_type not in ["limit", "market"]:
                raise ValueError(f"无效的订单类型: {order_type}，必须是 'limit' 或 'market'")
            
            if order_type == "limit" and price is None:
                raise ValueError("限价单必须指定价格")
            
            if quantity <= 0 or quantity % 100 != 0:
                raise ValueError(f"数量必须是100的整数倍，当前: {quantity}")
            
            # 标准化股票代码
            normalized_symbol = self._normalize_symbol(symbol, market)
            
            # 构建订单数据
            order_data = {
                "symbol": normalized_symbol,
                "action": action,
                "quantity": quantity,
                "order_type": order_type,
            }
            
            if price is not None:
                order_data["price"] = price
            
            # 调用API
            response = await self._make_request(
                endpoint="/api/order/place",
                method="POST",
                data=order_data,
            )
            
            if not response.get("success"):
                raise Exception(f"下单失败: {response.get('error', '未知错误')}")
            
            data = response.get("data", {})
            
            # 标准化返回格式
            order_result = {
                "success": True,
                "order_id": data.get("order_id", ""),
                "symbol": data.get("symbol", normalized_symbol),
                "action": action,
                "quantity": quantity,
                "price": price,
                "order_type": order_type,
                "status": data.get("status", "pending"),
                "filled_quantity": data.get("filled_quantity", 0),
                "average_price": data.get("average_price", 0),
                "commission": data.get("commission", 0),
                "created_at": data.get("created_at", datetime.now().isoformat()),
            }
            
            logger.info(
                f"成功下单: {normalized_symbol} {action} {quantity}股 @ {price or '市价'}"
            )
            return order_result
            
        except Exception as e:
            logger.error(f"下单失败 {symbol}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
            }
    
    def _normalize_symbol(self, symbol: str, market: Optional[str] = None) -> str:
        """
        标准化股票代码
        
        Args:
            symbol: 股票代码
            market: 市场代码
            
        Returns:
            标准化后的股票代码（如：000001.SZ）
        """
        # 移除空格和点
        symbol = symbol.strip().replace(".", "")
        
        # 如果已经包含市场代码（如：000001.SZ），直接返回
        if "." in symbol or len(symbol) == 8:
            return symbol
        
        # 如果没有指定市场，根据代码判断
        if not market:
            if symbol.startswith("0") or symbol.startswith("3"):
                market = "SZ"  # 深圳
            elif symbol.startswith("6") or symbol.startswith("9"):
                market = "SH"  # 上海
            else:
                market = "SZ"  # 默认深圳
        
        return f"{symbol}.{market}"
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        try:
            response = await self._make_request(
                endpoint="/api/account/info",
                method="GET",
            )
            
            if not response.get("success"):
                raise Exception(f"获取账户信息失败: {response.get('error', '未知错误')}")
            
            return {
                "success": True,
                "data": response.get("data", {}),
            }
            
        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态
        """
        try:
            response = await self._make_request(
                endpoint=f"/api/order/{order_id}",
                method="GET",
            )
            
            if not response.get("success"):
                raise Exception(f"查询订单状态失败: {response.get('error', '未知错误')}")
            
            return {
                "success": True,
                "data": response.get("data", {}),
            }
            
        except Exception as e:
            logger.error(f"查询订单状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        撤单
        
        Args:
            order_id: 订单ID
            
        Returns:
            撤单结果
        """
        try:
            response = await self._make_request(
                endpoint=f"/api/order/{order_id}/cancel",
                method="POST",
            )
            
            if not response.get("success"):
                raise Exception(f"撤单失败: {response.get('error', '未知错误')}")
            
            return {
                "success": True,
                "data": response.get("data", {}),
            }
            
        except Exception as e:
            logger.error(f"撤单失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
        logger.info("同花顺连接器已关闭")


# 单例工厂函数
_connector_instance: Optional[TonghuashunConnector] = None


def get_tonghuashun_connector(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    **kwargs
) -> TonghuashunConnector:
    """
    获取同花顺连接器实例（单例模式）
    
    Args:
        api_key: API密钥（可选，优先使用环境变量或凭证管理器）
        api_secret: API密钥（可选，优先使用环境变量或凭证管理器）
        **kwargs: 其他配置参数
        
    Returns:
        同花顺连接器实例
    """
    global _connector_instance
    
    if _connector_instance is None:
        _connector_instance = TonghuashunConnector(
            api_key=api_key,
            api_secret=api_secret,
            **kwargs
        )
    
    return _connector_instance


# 便捷函数
async def fetch_quote(symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
    """
    获取股票行情（便捷函数）
    
    Args:
        symbol: 股票代码
        market: 市场代码
        
    Returns:
        行情数据
    """
    connector = get_tonghuashun_connector()
    return await connector.fetch_quote(symbol, market)


async def place_order(
    symbol: str,
    action: str,
    quantity: int,
    price: Optional[float] = None,
    order_type: str = "limit",
    market: Optional[str] = None,
) -> Dict[str, Any]:
    """
    下单交易（便捷函数）
    
    Args:
        symbol: 股票代码
        action: 交易方向
        quantity: 数量
        price: 价格
        order_type: 订单类型
        market: 市场代码
        
    Returns:
        订单结果
    """
    connector = get_tonghuashun_connector()
    return await connector.place_order(symbol, action, quantity, price, order_type, market)

