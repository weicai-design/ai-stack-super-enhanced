"""
认证模块
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()


def require_api_token(token: str = Depends(security)):
    """验证API令牌"""
    # 简化实现，实际项目中需要验证token
    if not token.credentials:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return {"user_id": "demo_user", "permissions": ["read", "write"]}