"""
API限流系统
Rate Limiter System

使用slowapi实现API请求限流，防止滥用

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 尝试导入slowapi
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    HAS_SLOWAPI = True
except ImportError:
    logger.warning("slowapi未安装，限流功能将使用stub模式")
    HAS_SLOWAPI = False
    Limiter = None
    RateLimitExceeded = None


# ==================== 限流配置 ====================

# 全局限流规则
GLOBAL_RATE_LIMITS = {
    "default": "100/minute",      # 默认：每分钟100次
    "strict": "10/minute",        # 严格：每分钟10次
    "moderate": "30/minute",      # 中等：每分钟30次
    "relaxed": "200/minute",      # 宽松：每分钟200次
}

# 端点特定限流规则
ENDPOINT_RATE_LIMITS = {
    # Smart QA API（AI生成，成本较高）
    "/smart-qa/chat": "10/minute",              # 智能聊天：10次/分钟
    "/smart-qa/conversations": "30/minute",     # 对话列表：30次/分钟
    
    # KG可视化API（数据密集）
    "/kg/viz/graph": "20/minute",               # 完整图谱：20次/分钟
    "/kg/viz/export/*": "10/minute",            # 导出：10次/分钟
    "/kg/viz/stats": "60/minute",               # 统计：60次/分钟
    
    # RAG检索API（AI密集）
    "/rag/search": "30/minute",                 # 搜索：30次/分钟
    "/rag/ingest": "10/minute",                 # 导入：10次/分钟
    
    # 知识图谱API（数据库密集）
    "/kg/query": "30/minute",                   # 查询：30次/分钟
    "/kg/batch/query": "5/minute",              # 批量查询：5次/分钟
    
    # 系统API（开放）
    "/health": "200/minute",                    # 健康检查：200次/分钟
    "/docs": "100/minute",                      # 文档：100次/分钟
}

# 用户配额（基于API key或IP）
USER_QUOTAS = {
    "free": {
        "daily_limit": 1000,     # 每天1000次请求
        "rate": "20/minute"      # 每分钟20次
    },
    "basic": {
        "daily_limit": 10000,    # 每天10000次请求
        "rate": "50/minute"      # 每分钟50次
    },
    "pro": {
        "daily_limit": 100000,   # 每天100000次请求
        "rate": "200/minute"     # 每分钟200次
    },
    "unlimited": {
        "daily_limit": -1,       # 无限制
        "rate": "1000/minute"    # 每分钟1000次
    }
}


# ==================== 限流器初始化 ====================

def create_limiter() -> Limiter | None:
    """
    创建限流器实例
    
    Returns:
        Limiter实例或None（如果slowapi未安装）
    """
    if not HAS_SLOWAPI:
        logger.warning("slowapi未安装，创建stub限流器")
        return None
    
    try:
        limiter = Limiter(
            key_func=get_remote_address,  # 使用IP地址作为key
            default_limits=[GLOBAL_RATE_LIMITS["default"]],  # 默认限流
            storage_uri="memory://",  # 使用内存存储（生产环境建议使用Redis）
            strategy="fixed-window",  # 固定窗口策略
            headers_enabled=True,  # 启用响应头
        )
        logger.info("✅ API限流器已创建（内存存储模式）")
        return limiter
    
    except Exception as e:
        logger.error(f"创建限流器失败: {e}")
        return None


# ==================== 自定义错误处理 ====================

async def custom_rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    自定义限流错误处理
    
    返回友好的错误消息和重试信息
    """
    # 获取限流信息
    retry_after = getattr(exc, "retry_after", 60)
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "API请求频率超限，请稍后再试",
            "details": {
                "retry_after": retry_after,
                "limit": getattr(exc, "limit", "未知"),
                "window": getattr(exc, "window", "未知")
            },
            "suggestions": [
                "请等待一段时间后重试",
                "考虑升级到更高配额的方案",
                "联系管理员申请配额提升"
            ]
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(getattr(exc, "limit", "未知")),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after)
        }
    )


# ==================== 限流装饰器 ====================

def rate_limit(limit: str = None):
    """
    限流装饰器
    
    Args:
        limit: 限流规则，例如 "10/minute", "100/hour"
    
    Usage:
        @app.get("/api/endpoint")
        @rate_limit("10/minute")
        async def endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        if not HAS_SLOWAPI:
            # stub模式：不做限流
            return func
        
        # 如果没有指定limit，使用默认值
        actual_limit = limit or GLOBAL_RATE_LIMITS["default"]
        
        # 应用slowapi的limit装饰器
        return limiter.limit(actual_limit)(func)
    
    return decorator


# ==================== 限流监控 ====================

class RateLimitMonitor:
    """限流监控器"""
    
    def __init__(self):
        self.total_requests = 0
        self.limited_requests = 0
        self.requests_by_ip = {}
        self.requests_by_endpoint = {}
    
    def record_request(self, ip: str, endpoint: str, limited: bool = False):
        """记录请求"""
        self.total_requests += 1
        
        if limited:
            self.limited_requests += 1
        
        # 按IP统计
        if ip not in self.requests_by_ip:
            self.requests_by_ip[ip] = {"total": 0, "limited": 0}
        self.requests_by_ip[ip]["total"] += 1
        if limited:
            self.requests_by_ip[ip]["limited"] += 1
        
        # 按端点统计
        if endpoint not in self.requests_by_endpoint:
            self.requests_by_endpoint[endpoint] = {"total": 0, "limited": 0}
        self.requests_by_endpoint[endpoint]["total"] += 1
        if limited:
            self.requests_by_endpoint[endpoint]["limited"] += 1
    
    def get_statistics(self):
        """获取统计数据"""
        return {
            "total_requests": self.total_requests,
            "limited_requests": self.limited_requests,
            "limit_rate": f"{self.limited_requests / max(self.total_requests, 1) * 100:.2f}%",
            "top_ips": sorted(
                self.requests_by_ip.items(),
                key=lambda x: x[1]["total"],
                reverse=True
            )[:10],
            "top_endpoints": sorted(
                self.requests_by_endpoint.items(),
                key=lambda x: x[1]["total"],
                reverse=True
            )[:10]
        }


# ==================== 全局实例 ====================

# 创建限流器实例
limiter = create_limiter()

# 创建监控器实例
monitor = RateLimitMonitor()


# ==================== 辅助函数 ====================

def get_rate_limit_info(request: Request) -> dict:
    """
    获取当前请求的限流信息
    
    Args:
        request: FastAPI请求对象
    
    Returns:
        限流信息字典
    """
    if not HAS_SLOWAPI or not limiter:
        return {
            "enabled": False,
            "message": "限流功能未启用"
        }
    
    # 从请求头获取限流信息
    headers = request.headers
    
    return {
        "enabled": True,
        "limit": headers.get("X-RateLimit-Limit", "未知"),
        "remaining": headers.get("X-RateLimit-Remaining", "未知"),
        "reset": headers.get("X-RateLimit-Reset", "未知")
    }


def is_whitelisted(ip: str) -> bool:
    """
    检查IP是否在白名单中
    
    Args:
        ip: IP地址
    
    Returns:
        是否在白名单中
    """
    # 白名单IP（可从配置文件读取）
    whitelist = [
        "127.0.0.1",
        "::1",
        "localhost"
    ]
    
    return ip in whitelist


# ==================== 导出 ====================

__all__ = [
    "limiter",
    "monitor",
    "rate_limit",
    "custom_rate_limit_handler",
    "get_rate_limit_info",
    "is_whitelisted",
    "HAS_SLOWAPI",
    "ENDPOINT_RATE_LIMITS",
    "USER_QUOTAS"
]

































