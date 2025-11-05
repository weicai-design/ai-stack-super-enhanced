"""
统一健康检查模块
提供详细的服务健康状态检查
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealthStatus:
    """健康状态常量"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.start_time = datetime.now()
        self.checks = {}
        
        # 注册默认检查
        self.register_check("basic", self._basic_check, required=True)
    
    def register_check(
        self,
        name: str,
        check_func: Callable,
        required: bool = False,
        timeout: float = 5.0
    ):
        """
        注册健康检查项
        
        Args:
            name: 检查项名称
            check_func: 检查函数（返回Dict[str, Any]）
            required: 是否必需（失败时影响整体状态）
            timeout: 超时时间（秒）
        """
        self.checks[name] = {
            "func": check_func,
            "required": required,
            "timeout": timeout
        }
        logger.debug(f"注册健康检查: {name}")
    
    async def _basic_check(self) -> Dict[str, Any]:
        """基础检查"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": HealthStatus.HEALTHY,
            "uptime_seconds": uptime,
            "message": "服务运行正常"
        }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        执行所有健康检查
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        results = {
            "service": self.service_name,
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "status": HealthStatus.HEALTHY,
            "checks": {},
            "duration_ms": 0
        }
        
        # 执行所有检查
        for check_name, check_config in self.checks.items():
            check_func = check_config["func"]
            timeout = check_config["timeout"]
            required = check_config["required"]
            
            try:
                # 执行检查（带超时）
                check_result = await asyncio.wait_for(
                    check_func(),
                    timeout=timeout
                )
                
                results["checks"][check_name] = check_result
                
                # 如果是必需检查且失败，更新整体状态
                if required and check_result.get("status") != HealthStatus.HEALTHY:
                    if check_result.get("status") == HealthStatus.UNHEALTHY:
                        results["status"] = HealthStatus.UNHEALTHY
                    elif results["status"] == HealthStatus.HEALTHY:
                        results["status"] = HealthStatus.DEGRADED
                
            except asyncio.TimeoutError:
                error_result = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"检查超时（>{timeout}秒）"
                }
                results["checks"][check_name] = error_result
                
                if required:
                    results["status"] = HealthStatus.UNHEALTHY
            
            except Exception as e:
                error_result = {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"检查失败: {str(e)}"
                }
                results["checks"][check_name] = error_result
                
                logger.error(f"健康检查 {check_name} 失败: {e}")
                
                if required:
                    results["status"] = HealthStatus.UNHEALTHY
        
        # 计算总耗时
        results["duration_ms"] = (time.time() - start_time) * 1000
        
        return results
    
    async def check_database(self, db_session) -> Dict[str, Any]:
        """数据库健康检查"""
        try:
            # 执行简单查询
            await db_session.execute("SELECT 1")
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "数据库连接正常"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"数据库连接失败: {str(e)}"
            }
    
    async def check_cache(self, cache_client) -> Dict[str, Any]:
        """缓存健康检查"""
        try:
            # 测试读写
            test_key = f"health_check_{int(time.time())}"
            await cache_client.set(test_key, "test", expire=10)
            value = await cache_client.get(test_key)
            await cache_client.delete(test_key)
            
            if value == "test":
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "缓存服务正常"
                }
            else:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "缓存读写异常"
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"缓存服务失败: {str(e)}"
            }
    
    async def check_external_api(
        self,
        api_name: str,
        api_url: str
    ) -> Dict[str, Any]:
        """外部API健康检查"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                start = time.time()
                async with session.get(api_url, timeout=5) as response:
                    duration_ms = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        return {
                            "status": HealthStatus.HEALTHY,
                            "message": f"{api_name} 可用",
                            "response_time_ms": duration_ms
                        }
                    else:
                        return {
                            "status": HealthStatus.DEGRADED,
                            "message": f"{api_name} 返回 {response.status}",
                            "response_time_ms": duration_ms
                        }
        except asyncio.TimeoutError:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"{api_name} 超时"
            }
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"{api_name} 不可用: {str(e)}"
            }
    
    async def check_disk_space(self, path: str = "/", min_free_gb: float = 5.0) -> Dict[str, Any]:
        """磁盘空间检查"""
        try:
            import psutil
            
            disk = psutil.disk_usage(path)
            free_gb = disk.free / (1024 ** 3)
            percent = disk.percent
            
            if free_gb < min_free_gb:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"磁盘空间不足: {free_gb:.2f}GB",
                    "free_gb": free_gb,
                    "percent": percent
                }
            elif percent > 90:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"磁盘空间偏低: {percent}%",
                    "free_gb": free_gb,
                    "percent": percent
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "磁盘空间充足",
                    "free_gb": free_gb,
                    "percent": percent
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"无法检查磁盘空间: {str(e)}"
            }
    
    async def check_memory(self, max_percent: float = 90.0) -> Dict[str, Any]:
        """内存使用检查"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            percent = memory.percent
            available_gb = memory.available / (1024 ** 3)
            
            if percent > max_percent:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": f"内存使用率过高: {percent}%",
                    "percent": percent,
                    "available_gb": available_gb
                }
            elif percent > 80:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"内存使用率偏高: {percent}%",
                    "percent": percent,
                    "available_gb": available_gb
                }
            else:
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "内存使用正常",
                    "percent": percent,
                    "available_gb": available_gb
                }
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"无法检查内存: {str(e)}"
            }


# ==================== FastAPI集成 ====================

def create_health_endpoint(health_checker: HealthChecker):
    """
    创建健康检查端点
    
    返回一个可以直接用于FastAPI的路由函数
    """
    async def health_check():
        return await health_checker.check_health()
    
    return health_check


def create_readyz_endpoint(health_checker: HealthChecker):
    """创建就绪检查端点（Kubernetes风格）"""
    async def readyz():
        health_result = await health_checker.check_health()
        
        if health_result["status"] == HealthStatus.HEALTHY:
            return {
                "status": "ready",
                "message": f"{health_checker.service_name} 已就绪"
            }
        else:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail=f"服务未就绪: {health_result['status']}"
            )
    
    return readyz


def create_livez_endpoint(health_checker: HealthChecker):
    """创建存活检查端点（Kubernetes风格）"""
    async def livez():
        # 简单的存活检查，只要进程在运行就返回成功
        return {
            "status": "alive",
            "uptime_seconds": (datetime.now() - health_checker.start_time).total_seconds()
        }
    
    return livez


