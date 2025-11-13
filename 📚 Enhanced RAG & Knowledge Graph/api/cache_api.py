"""
缓存管理API
Cache Management API

提供缓存查询、清理、统计等功能

版本: 1.0.0 (v2.7.0新增)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/cache", tags=["Cache Management"])


# ==================== 数据模型 ====================

class CacheStats(BaseModel):
    """缓存统计"""
    backend: str = Field("unknown", description="缓存后端（redis/memory）")
    connected: bool = Field(False, description="是否连接")
    total_keys: int = Field(0, description="缓存key总数")
    memory_used: str = Field("N/A", description="内存使用")
    hit_rate: str = Field("N/A", description="命中率")


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = Field(True, description="是否启用")
    backend: str = Field("memory", description="后端类型")
    default_ttl: int = Field(3600, description="默认过期时间（秒）")
    max_keys: int = Field(10000, description="最大key数")


# ==================== API端点 ====================

@router.get("/stats", response_model=Dict[str, Any])
async def get_cache_statistics():
    """
    获取缓存统计信息
    
    返回缓存后端、key数量、内存使用等信息
    
    Returns:
        缓存统计数据
    """
    try:
        from api.cache_manager import get_cache_stats
        
        stats = get_cache_stats()
        return stats
    
    except ImportError:
        return {
            "backend": "disabled",
            "connected": False,
            "message": "缓存系统未启用"
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_cache_config():
    """
    获取缓存配置
    
    返回当前缓存系统的配置信息
    
    Returns:
        缓存配置
    """
    try:
        from api.cache_manager import HAS_REDIS, CACHE_CONFIG, cache_manager
        
        return {
            "enabled": True,
            "backend": "redis" if (HAS_REDIS and cache_manager.use_redis) else "memory",
            "redis_available": HAS_REDIS,
            "default_ttl": CACHE_CONFIG["default_ttl"],
            "redis_config": {
                "host": CACHE_CONFIG["redis_host"],
                "port": CACHE_CONFIG["redis_port"],
                "db": CACHE_CONFIG["redis_db"]
            } if HAS_REDIS else None
        }
    
    except ImportError:
        return {
            "enabled": False,
            "backend": "none",
            "message": "缓存系统未启用"
        }
    except Exception as e:
        logger.error(f"获取缓存配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_cache(
    pattern: str = Query("*", description="key模式（支持通配符）")
):
    """
    清空缓存
    
    根据模式清空缓存key
    
    Args:
        pattern: key模式，例如 "search:*" 清空所有搜索缓存
    
    Returns:
        删除的key数量
    """
    try:
        from api.cache_manager import invalidate_cache
        
        count = invalidate_cache(pattern)
        
        return {
            "message": f"已清空缓存",
            "pattern": pattern,
            "deleted_keys": count
        }
    
    except ImportError:
        raise HTTPException(status_code=503, detail="缓存系统未启用")
    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys")
async def list_cache_keys(
    pattern: str = Query("*", description="key模式"),
    limit: int = Query(100, ge=1, le=1000, description="最大返回数")
):
    """
    列出缓存keys
    
    Args:
        pattern: key模式
        limit: 最大返回数
    
    Returns:
        key列表
    """
    try:
        from api.cache_manager import cache_manager
        
        if cache_manager.use_redis and cache_manager.redis_client:
            keys = cache_manager.redis_client.keys(f"ai-stack:{pattern}")
            keys = [k for k in keys][:limit]
            return {
                "count": len(keys),
                "keys": keys,
                "backend": "redis"
            }
        else:
            keys = list(cache_manager.memory_cache.keys())[:limit]
            return {
                "count": len(keys),
                "keys": keys,
                "backend": "memory"
            }
    
    except ImportError:
        return {
            "count": 0,
            "keys": [],
            "message": "缓存系统未启用"
        }
    except Exception as e:
        logger.error(f"列出缓存keys失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ttl")
async def get_endpoint_ttl():
    """
    获取端点缓存TTL配置
    
    返回各端点的缓存过期时间配置
    
    Returns:
        TTL配置
    """
    try:
        from api.cache_manager import ENDPOINT_CACHE_TTL
        
        return {
            "default_ttl": 3600,
            "endpoint_ttl": ENDPOINT_CACHE_TTL,
            "note": "TTL单位为秒，0表示不缓存"
        }
    
    except ImportError:
        return {
            "default_ttl": 0,
            "endpoint_ttl": {},
            "message": "缓存系统未启用"
        }


@router.get("/health")
async def cache_health():
    """缓存模块健康检查"""
    try:
        from api.cache_manager import HAS_REDIS, cache_manager
        
        stats = cache_manager.get_stats()
        
        return {
            "status": "healthy" if stats.get("connected") else "degraded",
            "module": "cache",
            "version": "1.0.0",
            "redis_available": HAS_REDIS,
            "backend": stats.get("backend", "unknown"),
            "connected": stats.get("connected", False),
            "total_keys": stats.get("total_keys", 0),
            "features": [
                "result-caching",
                "ttl-management",
                "pattern-invalidation",
                "statistics-tracking",
                "memory-fallback"
            ]
        }
    
    except ImportError:
        return {
            "status": "disabled",
            "module": "cache",
            "version": "1.0.0",
            "redis_available": False,
            "message": "缓存系统未启用"
        }


# ==================== 测试端点 ====================

@router.post("/test")
async def test_cache():
    """
    测试缓存功能
    
    执行缓存读写测试，验证功能正常
    
    Returns:
        测试结果
    """
    try:
        from api.cache_manager import cache_manager
        import time
        
        test_key = "test:cache:verification"
        test_value = {"message": "Hello Cache!", "timestamp": time.time()}
        
        # 写入测试
        write_success = cache_manager.set(test_key, test_value, ttl=60)
        
        # 读取测试
        read_value = cache_manager.get(test_key)
        read_success = read_value == test_value
        
        # 删除测试
        delete_success = cache_manager.delete(test_key)
        
        return {
            "test_passed": write_success and read_success and delete_success,
            "write": "✅" if write_success else "❌",
            "read": "✅" if read_success else "❌",
            "delete": "✅" if delete_success else "❌",
            "backend": cache_manager.get_stats().get("backend", "unknown")
        }
    
    except ImportError:
        raise HTTPException(status_code=503, detail="缓存系统未启用")
    except Exception as e:
        logger.error(f"缓存测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

















