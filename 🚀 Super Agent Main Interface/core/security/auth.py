from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import get_security_settings


def require_api_token(x_api_key: str | None = Header(default=None), x_api_token: str | None = Header(default=None)) -> None:
    """
    全局 API Key 依赖。若未配置 API_TOKEN，则不强制校验。
    支持 X-API-KEY / X-API-TOKEN 两种 header，便于兼容历史调用。
    """
    settings = get_security_settings()
    expected = settings.api_token
    if not expected:
        return
    candidate = x_api_key or x_api_token
    if not candidate or candidate != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或无效的 API Token",
        )


