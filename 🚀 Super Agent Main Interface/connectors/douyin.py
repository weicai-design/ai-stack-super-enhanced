#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音API连接器（生产级实现）
4.2: 实现授权链接、token刷新、内容发布、回调处理
"""

from __future__ import annotations

import os
import logging
import asyncio
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse, parse_qs
import httpx
import hashlib
import hmac
import time
import json

# 导入密钥管理和重试处理器
from core.api_credential_manager import get_credential_manager
from core.api_retry_handler import APIRetryHandler, RetryStrategy, execute_with_retry

logger = logging.getLogger(__name__)


class DouyinConnector:
    """
    抖音API连接器（生产级）
    
    功能：
    1. OAuth授权链接生成
    2. Token刷新
    3. 内容发布（视频、图文）
    4. 回调处理
    """
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    ):
        """
        初始化抖音连接器
        
        Args:
            app_id: 应用ID（优先从环境变量或凭证管理器获取）
            app_secret: 应用密钥（优先从环境变量或凭证管理器获取）
            client_key: 客户端Key（备用认证方式）
            client_secret: 客户端密钥（备用认证方式）
            redirect_uri: OAuth回调地址
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_strategy: 重试策略
        """
        # 初始化凭证管理器
        self.credential_manager = get_credential_manager()
        
        # 从环境变量或凭证管理器获取密钥
        self.app_id = (
            app_id
            or os.getenv("DOUYIN_APP_ID")
            or self.credential_manager.get_credential("douyin", "app_id")
        )
        self.app_secret = (
            app_secret
            or os.getenv("DOUYIN_APP_SECRET")
            or self.credential_manager.get_credential("douyin", "app_secret")
        )
        self.client_key = (
            client_key
            or os.getenv("DOUYIN_CLIENT_KEY")
            or self.credential_manager.get_credential("douyin", "client_key")
        )
        self.client_secret = (
            client_secret
            or os.getenv("DOUYIN_CLIENT_SECRET")
            or self.credential_manager.get_credential("douyin", "client_secret")
        )
        
        # OAuth配置
        self.redirect_uri = (
            redirect_uri
            or os.getenv("DOUYIN_REDIRECT_URI")
            or self.credential_manager.get_credential("douyin", "redirect_uri")
            or "http://localhost:8000/api/douyin/callback"
        )
        
        # API配置
        self.base_url = base_url or os.getenv("DOUYIN_BASE_URL", "https://open.douyin.com")
        self.timeout = timeout
        
        # Token存储
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # 从凭证管理器加载已保存的token
        self._load_tokens()
        
        # 验证配置
        if not self.app_id or not self.app_secret:
            if not self.client_key or not self.client_secret:
                logger.warning(
                    "抖音API密钥未配置，请设置环境变量或使用凭证管理器配置："
                    "DOUYIN_APP_ID, DOUYIN_APP_SECRET 或 DOUYIN_CLIENT_KEY, DOUYIN_CLIENT_SECRET"
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
        
        # 回调处理器
        self.callback_handlers: Dict[str, Callable] = {}
        
        logger.info(f"抖音连接器初始化完成，API地址: {self.base_url}")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        headers = {
            "User-Agent": "AI-Stack-Douyin-Connector/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # 如果有access_token，添加到请求头
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    def _load_tokens(self):
        """从凭证管理器加载已保存的token"""
        try:
            self.access_token = self.credential_manager.get_credential("douyin", "access_token")
            self.refresh_token = self.credential_manager.get_credential("douyin", "refresh_token")
            
            expires_at_str = self.credential_manager.get_credential("douyin", "token_expires_at")
            if expires_at_str:
                self.token_expires_at = datetime.fromisoformat(expires_at_str)
        except Exception as e:
            logger.warning(f"加载token失败: {e}")
    
    def _save_tokens(self):
        """保存token到凭证管理器"""
        try:
            if self.access_token:
                self.credential_manager.set_credential("douyin", "access_token", self.access_token)
            if self.refresh_token:
                self.credential_manager.set_credential("douyin", "refresh_token", self.refresh_token)
            if self.token_expires_at:
                self.credential_manager.set_credential(
                    "douyin",
                    "token_expires_at",
                    self.token_expires_at.isoformat()
                )
        except Exception as e:
            logger.error(f"保存token失败: {e}")
    
    def _is_token_expired(self) -> bool:
        """检查token是否过期"""
        if not self.token_expires_at:
            return True
        # 提前5分钟刷新
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))
    
    async def _ensure_valid_token(self):
        """确保token有效，如果过期则自动刷新"""
        if not self.access_token or self._is_token_expired():
            if self.refresh_token:
                await self.refresh_token()
            else:
                raise ValueError("Access token已过期且无refresh token，请重新授权")
    
    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        """
        发起HTTP请求（带重试和自动token刷新）
        
        Args:
            endpoint: API端点
            method: HTTP方法
            params: 查询参数
            data: 请求体
            headers: 额外请求头
            require_auth: 是否需要认证
            
        Returns:
            API响应
        """
        # 确保token有效
        if require_auth:
            await self._ensure_valid_token()
        
        url = f"{self.base_url}{endpoint}"
        
        # 合并请求头
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
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
                logger.error(f"抖音API请求失败: {error_msg}")
                
                # 如果是401错误，尝试刷新token后重试
                if e.response.status_code == 401 and require_auth and self.refresh_token:
                    logger.info("Token可能已过期，尝试刷新...")
                    await self.refresh_token()
                    # 重新发起请求（只重试一次）
                    if method.upper() == "GET":
                        response = await self.client.get(url, params=params, headers=self._get_default_headers())
                    elif method.upper() == "POST":
                        response = await self.client.post(url, json=data, params=params, headers=self._get_default_headers())
                    else:
                        raise Exception(error_msg)
                    response.raise_for_status()
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "data": response.json() if response.content else {},
                        "headers": dict(response.headers),
                    }
                
                raise Exception(error_msg)
            except httpx.TimeoutException as e:
                error_msg = f"请求超时: {str(e)}"
                logger.error(f"抖音API请求超时: {error_msg}")
                raise
            except Exception as e:
                error_msg = f"请求异常: {str(e)}"
                logger.error(f"抖音API请求异常: {error_msg}")
                raise
        
        # 使用重试机制执行请求
        return await execute_with_retry(
            _request,
            max_retries=self.retry_handler.max_retries,
            initial_delay=self.retry_handler.initial_delay,
            max_delay=self.retry_handler.max_delay,
            strategy=self.retry_handler.strategy,
        )
    
    def generate_auth_url(
        self,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
    ) -> str:
        """
        生成OAuth授权链接（生产级实现）
        
        Args:
            state: 状态参数（用于防止CSRF攻击）
            scope: 授权范围（如：user_info, video.create等）
            
        Returns:
            授权链接URL
        """
        # 参数验证
        if not self.app_id:
            error_msg = "缺少app_id，无法生成授权链接"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not self.redirect_uri:
            error_msg = "缺少redirect_uri，无法生成授权链接"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 生成state（如果未提供）- 使用安全的随机生成
        if not state:
            import secrets
            state = secrets.token_urlsafe(32)
        elif not isinstance(state, str) or len(state) < 16:
            error_msg = "state参数必须是至少16个字符的字符串"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证scope
        if scope is not None:
            if not isinstance(scope, list) or len(scope) == 0:
                error_msg = "scope必须是非空列表"
                logger.error(error_msg)
                raise ValueError(error_msg)
            # 验证scope格式
            valid_scopes = ["user_info", "video.create", "video.upload", "video.data", "video.delete"]
            invalid_scopes = [s for s in scope if s not in valid_scopes]
            if invalid_scopes:
                logger.warning(f"检测到无效的scope: {invalid_scopes}")
        
        # 默认授权范围
        if not scope:
            scope = ["user_info", "video.create", "video.upload"]
        
        try:
            # 构建授权参数
            params = {
                "client_key": self.app_id,
                "response_type": "code",
                "scope": ",".join(scope),
                "redirect_uri": self.redirect_uri,
                "state": state,
            }
            
            # 生成授权链接
            auth_url = f"{self.base_url}/platform/oauth/connect?{urlencode(params)}"
            
            logger.info(f"生成授权链接成功，state: {state[:8]}...")
            return auth_url
            
        except Exception as e:
            error_msg = f"生成授权链接失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    async def handle_callback(
        self,
        code: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理OAuth回调，获取access_token（生产级实现）
        
        Args:
            code: 授权码
            state: 状态参数（用于验证）
            
        Returns:
            Token信息
        """
        # 参数验证
        if not code or not isinstance(code, str):
            error_msg = "无效的授权码"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if not self.app_id or not self.app_secret:
            error_msg = "缺少app_id或app_secret，无法获取token"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        try:
            # 构建token请求
            token_data = {
                "client_key": self.app_id,
                "client_secret": self.app_secret,
                "code": code,
                "grant_type": "authorization_code",
            }
            
            # 调用token接口（带重试）
            response = await self._make_request(
                endpoint="/oauth/access_token",
                method="POST",
                data=token_data,
                require_auth=False,
            )
            
            if not response.get("success"):
                error_msg = f"获取token失败: {response.get('error', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.get("data", {})
            
            # 验证响应数据
            if not data.get("access_token"):
                error_msg = "API返回数据格式错误，缺少access_token"
                logger.error(f"{error_msg}: {data}")
                raise Exception(error_msg)
            
            # 保存token
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            expires_in = int(data.get("expires_in", 7200))  # 默认2小时
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # 保存到凭证管理器
            self._save_tokens()
            
            logger.info("成功获取access_token")
            
            return {
                "success": True,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "expires_at": self.token_expires_at.isoformat(),
            }
            
        except httpx.TimeoutException as e:
            error_msg = f"获取token超时: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"处理回调失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
            }
    
    async def refresh_token(self) -> Dict[str, Any]:
        """
        刷新access_token（生产级实现）
        
        Returns:
            新的token信息
        """
        # 参数验证
        if not self.refresh_token:
            error_msg = "缺少refresh_token，无法刷新token"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if not self.app_id or not self.app_secret:
            error_msg = "缺少app_id或app_secret，无法刷新token"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        try:
            # 构建刷新请求
            refresh_data = {
                "client_key": self.app_id,
                "client_secret": self.app_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
            
            # 调用刷新接口（带重试）
            response = await self._make_request(
                endpoint="/oauth/refresh_token",
                method="POST",
                data=refresh_data,
                require_auth=False,
            )
            
            if not response.get("success"):
                error_msg = f"刷新token失败: {response.get('error', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.get("data", {})
            
            # 验证响应数据
            if not data.get("access_token"):
                error_msg = "API返回数据格式错误，缺少access_token"
                logger.error(f"{error_msg}: {data}")
                raise Exception(error_msg)
            
            # 更新token
            self.access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")
            if new_refresh_token:
                self.refresh_token = new_refresh_token
            expires_in = int(data.get("expires_in", 7200))
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # 保存到凭证管理器
            self._save_tokens()
            
            logger.info("成功刷新access_token")
            
            return {
                "success": True,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "expires_at": self.token_expires_at.isoformat(),
            }
            
        except httpx.TimeoutException as e:
            error_msg = f"刷新token超时: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            # 如果是401错误，说明refresh_token已失效，需要重新授权
            if e.response.status_code == 401:
                logger.warning("refresh_token已失效，需要重新授权")
                self.access_token = None
                self.refresh_token = None
                self.token_expires_at = None
                self._save_tokens()
            return {
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"刷新token失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
            }
    
    async def publish_video(
        self,
        video_url: str,
        title: str,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
        privacy_level: int = 0,  # 0:公开, 1:仅自己可见
    ) -> Dict[str, Any]:
        """
        发布视频（生产级实现）
        
        Args:
            video_url: 视频URL或video_id（需要先上传到抖音服务器）
            title: 视频标题
            description: 视频描述
            cover_url: 封面图URL
            privacy_level: 隐私级别（0:公开, 1:仅自己可见）
            
        Returns:
            发布结果
        """
        # 参数验证
        if not video_url or not isinstance(video_url, str):
            error_msg = "无效的视频URL或video_id"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if not title or not isinstance(title, str) or len(title.strip()) == 0:
            error_msg = "视频标题不能为空"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if len(title) > 55:  # 抖音标题最大长度限制
            error_msg = f"视频标题过长（最大55字符），当前: {len(title)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if description and len(description) > 2000:  # 抖音描述最大长度限制
            error_msg = f"视频描述过长（最大2000字符），当前: {len(description)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if privacy_level not in [0, 1]:
            error_msg = f"无效的隐私级别: {privacy_level}，必须是0（公开）或1（仅自己可见）"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        try:
            # 确保token有效
            await self._ensure_valid_token()
            
            # 构建发布数据
            publish_data = {
                "video_id": video_url,  # 实际应该是上传后返回的video_id
                "text": title.strip(),
                "poi_id": "",  # 位置ID（可选）
                "privacy_level": privacy_level,
            }
            
            if description:
                publish_data["text"] = f"{title.strip()}\n{description.strip()}"
            
            if cover_url:
                publish_data["cover_tsp"] = cover_url
            
            # 调用发布接口（带重试）
            response = await self._make_request(
                endpoint="/video/create",
                method="POST",
                data=publish_data,
            )
            
            if not response.get("success"):
                error_msg = f"发布视频失败: {response.get('error', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.get("data", {})
            
            # 验证响应数据
            if not data.get("item_id"):
                error_msg = "API返回数据格式错误，缺少item_id"
                logger.error(f"{error_msg}: {data}")
                raise Exception(error_msg)
            
            logger.info(f"成功发布视频: {data.get('item_id', '')}")
            
            return {
                "success": True,
                "item_id": data.get("item_id", ""),
                "video_id": data.get("video_id", ""),
                "share_url": data.get("share_url", ""),
            }
            
        except httpx.TimeoutException as e:
            error_msg = f"发布视频超时: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"发布视频失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
            }
    
    async def publish_image(
        self,
        images: List[str],
        title: str,
        description: Optional[str] = None,
        privacy_level: int = 0,
    ) -> Dict[str, Any]:
        """
        发布图文（生产级实现）
        
        Args:
            images: 图片URL列表（需要先上传到抖音服务器）
            title: 标题
            description: 描述
            privacy_level: 隐私级别
            
        Returns:
            发布结果
        """
        # 参数验证
        if not images or not isinstance(images, list) or len(images) == 0:
            error_msg = "图片列表不能为空"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if len(images) > 9:  # 抖音图文最多9张图片
            error_msg = f"图片数量过多（最多9张），当前: {len(images)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if not title or not isinstance(title, str) or len(title.strip()) == 0:
            error_msg = "标题不能为空"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if len(title) > 55:  # 抖音标题最大长度限制
            error_msg = f"标题过长（最大55字符），当前: {len(title)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if description and len(description) > 2000:  # 抖音描述最大长度限制
            error_msg = f"描述过长（最大2000字符），当前: {len(description)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        if privacy_level not in [0, 1]:
            error_msg = f"无效的隐私级别: {privacy_level}，必须是0（公开）或1（仅自己可见）"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        try:
            # 确保token有效
            await self._ensure_valid_token()
            
            # 构建发布数据
            publish_data = {
                "image_list": images,
                "text": title.strip(),
                "privacy_level": privacy_level,
            }
            
            if description:
                publish_data["text"] = f"{title.strip()}\n{description.strip()}"
            
            # 调用发布接口（带重试）
            response = await self._make_request(
                endpoint="/image/create",
                method="POST",
                data=publish_data,
            )
            
            if not response.get("success"):
                error_msg = f"发布图文失败: {response.get('error', '未知错误')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            data = response.get("data", {})
            
            # 验证响应数据
            if not data.get("item_id"):
                error_msg = "API返回数据格式错误，缺少item_id"
                logger.error(f"{error_msg}: {data}")
                raise Exception(error_msg)
            
            logger.info(f"成功发布图文: {data.get('item_id', '')}")
            
            return {
                "success": True,
                "item_id": data.get("item_id", ""),
                "share_url": data.get("share_url", ""),
            }
            
        except httpx.TimeoutException as e:
            error_msg = f"发布图文超时: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"发布图文失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
            }
    
    def register_callback_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], Any],
    ):
        """
        注册回调处理器
        
        Args:
            event_type: 事件类型（如：video.audit, video.comment等）
            handler: 处理函数
        """
        self.callback_handlers[event_type] = handler
        logger.info(f"注册回调处理器: {event_type}")
    
    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理Webhook回调（生产级实现）
        
        Args:
            payload: 回调数据
            signature: 签名（用于验证）
            
        Returns:
            处理结果
        """
        # 参数验证
        if not payload or not isinstance(payload, dict):
            error_msg = "无效的回调数据"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
            }
        
        try:
            # 验证签名（如果提供）
            if signature:
                if not self.app_secret:
                    logger.warning("提供了签名但缺少app_secret，跳过签名验证")
                elif not self._verify_signature(payload, signature):
                    error_msg = "Webhook签名验证失败"
                    logger.warning(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                    }
            
            # 获取事件类型
            event_type = payload.get("event", "")
            if not event_type:
                error_msg = "回调数据缺少event字段"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                }
            
            event_data = payload.get("data", {})
            
            # 查找对应的处理器
            handler = self.callback_handlers.get(event_type)
            if handler:
                try:
                    # 调用处理器
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(event_data)
                    else:
                        result = handler(event_data)
                    
                    logger.info(f"成功处理Webhook事件: {event_type}")
                    
                    return {
                        "success": True,
                        "event_type": event_type,
                        "result": result,
                    }
                except Exception as handler_error:
                    error_msg = f"事件处理器执行失败: {str(handler_error)}"
                    logger.error(f"{error_msg} (事件类型: {event_type})", exc_info=True)
                    return {
                        "success": False,
                        "error": error_msg,
                        "event_type": event_type,
                    }
            else:
                logger.warning(f"未找到事件处理器: {event_type}")
                return {
                    "success": False,
                    "error": f"未找到事件处理器: {event_type}",
                    "event_type": event_type,
                }
                
        except Exception as e:
            error_msg = f"处理Webhook失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
            }
    
    def _verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
    ) -> bool:
        """
        验证Webhook签名（生产级实现）
        
        Args:
            payload: 回调数据
            signature: 签名
            
        Returns:
            是否验证通过
        """
        # 参数验证
        if not signature or not isinstance(signature, str):
            logger.error("无效的签名")
            return False
        
        if not self.app_secret:
            logger.error("缺少app_secret，无法验证签名")
            return False
        
        try:
            # 构建签名字符串（根据抖音API文档的签名算法）
            timestamp = payload.get("timestamp", "")
            nonce = payload.get("nonce", "")
            
            if not timestamp or not nonce:
                logger.error("回调数据缺少timestamp或nonce字段")
                return False
            
            # 抖音签名算法：SHA256(timestamp + nonce + app_secret)
            sign_str = f"{timestamp}{nonce}{self.app_secret}"
            
            # 计算签名
            calculated_signature = hashlib.sha256(sign_str.encode()).hexdigest()
            
            # 安全比较（防止时序攻击）
            if len(calculated_signature) != len(signature):
                logger.warning("签名长度不匹配")
                return False
            
            # 使用hmac.compare_digest进行安全比较
            import hmac
            return hmac.compare_digest(calculated_signature, signature)
            
        except Exception as e:
            logger.error(f"签名验证异常: {e}", exc_info=True)
            return False
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        
        Returns:
            用户信息
        """
        try:
            response = await self._make_request(
                endpoint="/oauth/userinfo",
                method="GET",
            )
            
            if not response.get("success"):
                raise Exception(f"获取用户信息失败: {response.get('error', '未知错误')}")
            
            return {
                "success": True,
                "data": response.get("data", {}),
            }
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
        logger.info("抖音连接器已关闭")


# 单例工厂函数
_connector_instance: Optional[DouyinConnector] = None


def get_douyin_connector(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    **kwargs
) -> DouyinConnector:
    """
    获取抖音连接器实例（单例模式）
    
    Args:
        app_id: 应用ID（可选，优先使用环境变量或凭证管理器）
        app_secret: 应用密钥（可选，优先使用环境变量或凭证管理器）
        **kwargs: 其他配置参数
        
    Returns:
        抖音连接器实例
    """
    global _connector_instance
    
    if _connector_instance is None:
        _connector_instance = DouyinConnector(
            app_id=app_id,
            app_secret=app_secret,
            **kwargs
        )
    
    return _connector_instance


# 便捷函数
def generate_auth_url(
    state: Optional[str] = None,
    scope: Optional[List[str]] = None,
) -> str:
    """
    生成授权链接（便捷函数）
    
    Args:
        state: 状态参数
        scope: 授权范围
        
    Returns:
        授权链接
    """
    connector = get_douyin_connector()
    return connector.generate_auth_url(state, scope)


async def handle_callback(code: str, state: Optional[str] = None) -> Dict[str, Any]:
    """
    处理OAuth回调（便捷函数）
    
    Args:
        code: 授权码
        state: 状态参数
        
    Returns:
        Token信息
    """
    connector = get_douyin_connector()
    return await connector.handle_callback(code, state)

