"""
抖音集成（占位实现）
说明：
 - 提供OAuth流程占位（保存access_token/过期时间）
 - 提供草稿发布占位API（真实调用后续接SDK/HTTP API）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


@dataclass
class DouyinAuthState:
    access_token: Optional[str]
    expires_at: Optional[datetime]
    refresh_token: Optional[str]
    scope: Optional[str]


class DouyinIntegration:
    def __init__(self):
        self._auth = DouyinAuthState(
            access_token=None,
            expires_at=None,
            refresh_token=None,
            scope=None
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "authorized": self._auth.access_token is not None and (self._auth.expires_at or datetime.min) > datetime.now(),
            "expires_at": self._auth.expires_at.isoformat() if self._auth.expires_at else None,
            "scope": self._auth.scope
        }

    def begin_auth(self) -> Dict[str, Any]:
        """
        启动OAuth占位：真实实现中应返回跳转URL或二维码等
        这里直接模拟授权结果（有效期2小时）
        """
        self._auth.access_token = "mock_douyin_access_token"
        self._auth.refresh_token = "mock_douyin_refresh_token"
        self._auth.scope = "video.write,video.read"
        self._auth.expires_at = datetime.now() + timedelta(hours=2)
        return {"success": True, "authorized": True, "expires_at": self._auth.expires_at.isoformat()}

    def revoke(self) -> Dict[str, Any]:
        self._auth = DouyinAuthState(access_token=None, expires_at=None, refresh_token=None, scope=None)
        return {"success": True}

    async def create_draft(self, title: str, content: str, tags: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        草稿发布占位：真实实现中应调用抖音内容创作API
        """
        if not self.get_status()["authorized"]:
            return {"success": False, "error": "未授权或Token已过期"}
        return {
            "success": True,
            "draft_id": f"dy_{int(datetime.now().timestamp())}",
            "title": title,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }


