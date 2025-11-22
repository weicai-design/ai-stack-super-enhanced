#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
故障演练脚本
P3-403: 模拟Sidecar宕机、数据库降级、API超时等故障
"""

from __future__ import annotations

import asyncio
import subprocess
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import httpx
import docker

logger = logging.getLogger(__name__)


class ChaosScenario(str, Enum):
    """故障场景"""
    SIDECAR_DOWN = "sidecar_down"  # Sidecar宕机
    DATABASE_DEGRADED = "database_degraded"  # 数据库降级
    API_TIMEOUT = "api_timeout"  # API超时
    NETWORK_PARTITION = "network_partition"  # 网络分区
    HIGH_LATENCY = "high_latency"  # 高延迟
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽


@dataclass
class ChaosTestResult:
    """故障测试结果"""
    scenario: ChaosScenario
    start_time: str
    end_time: str
    duration: float
    success: bool
    error_message: Optional[str] = None
    recovery_time: Optional[float] = None
    impact_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["scenario"] = self.scenario.value
        return data


class ChaosTestRunner:
    """
    故障演练运行器
    
    功能：
    1. 模拟各种故障场景
    2. 监控系统响应
    3. 验证恢复机制
    4. 生成故障报告
    """
    
    def __init__(self):
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except:
            logger.warning("Docker客户端初始化失败，将使用命令行方式")
        
        self.test_results: List[ChaosTestResult] = []
        
        logger.info("故障演练运行器初始化完成")
    
    # ============ Sidecar宕机 ============
    
    async def test_sidecar_down(
        self,
        sidecar_name: str = "rag-sidecar",
        duration: int = 60,
    ) -> ChaosTestResult:
        """
        测试Sidecar宕机场景
        
        Args:
            sidecar_name: Sidecar服务名称
            duration: 故障持续时间（秒）
            
        Returns:
            测试结果
        """
        logger.info(f"开始故障演练: Sidecar宕机 - {sidecar_name}")
        
        start_time = datetime.utcnow()
        result = ChaosTestResult(
            scenario=ChaosScenario.SIDECAR_DOWN,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            success=False,
        )
        
        try:
            # 1. 记录故障前状态
            before_metrics = await self._get_system_metrics()
            
            # 2. 停止Sidecar
            logger.info(f"停止Sidecar: {sidecar_name}")
            stop_success = await self._stop_service(sidecar_name)
            
            if not stop_success:
                result.error_message = "无法停止Sidecar服务"
                return result
            
            # 3. 等待故障生效
            await asyncio.sleep(5)
            
            # 4. 测试系统响应
            impact_metrics = await self._test_system_resilience()
            
            # 5. 等待指定时长
            await asyncio.sleep(duration)
            
            # 6. 恢复服务
            logger.info(f"恢复Sidecar: {sidecar_name}")
            recovery_start = time.time()
            recovery_success = await self._start_service(sidecar_name)
            recovery_time = time.time() - recovery_start
            
            if not recovery_success:
                result.error_message = "无法恢复Sidecar服务"
                return result
            
            # 7. 验证恢复
            await asyncio.sleep(10)
            after_metrics = await self._get_system_metrics()
            
            # 8. 记录结果
            end_time = datetime.utcnow()
            result.end_time = end_time.isoformat()
            result.duration = (end_time - start_time).total_seconds()
            result.success = True
            result.recovery_time = recovery_time
            result.impact_metrics = {
                "before": before_metrics,
                "during": impact_metrics,
                "after": after_metrics,
            }
            
            logger.info(f"Sidecar宕机测试完成: 恢复时间 {recovery_time:.2f}秒")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Sidecar宕机测试失败: {e}", exc_info=True)
        
        finally:
            # 确保服务恢复
            await self._start_service(sidecar_name)
        
        self.test_results.append(result)
        return result
    
    # ============ 数据库降级 ============
    
    async def test_database_degraded(
        self,
        database_name: str = "postgres",
        degradation_type: str = "slow_queries",
        duration: int = 60,
    ) -> ChaosTestResult:
        """
        测试数据库降级场景
        
        Args:
            database_name: 数据库服务名称
            degradation_type: 降级类型 (slow_queries/connection_limit/disk_full)
            duration: 故障持续时间（秒）
            
        Returns:
            测试结果
        """
        logger.info(f"开始故障演练: 数据库降级 - {degradation_type}")
        
        start_time = datetime.utcnow()
        result = ChaosTestResult(
            scenario=ChaosScenario.DATABASE_DEGRADED,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            success=False,
            metadata={"degradation_type": degradation_type},
        )
        
        try:
            # 1. 记录故障前状态
            before_metrics = await self._get_system_metrics()
            
            # 2. 注入故障
            if degradation_type == "slow_queries":
                # 模拟慢查询（通过添加延迟）
                await self._inject_database_delay(database_name, delay_ms=5000)
            elif degradation_type == "connection_limit":
                # 模拟连接数限制
                await self._limit_database_connections(database_name, max_connections=5)
            elif degradation_type == "disk_full":
                # 模拟磁盘满（通过限制写入）
                await self._simulate_disk_full(database_name)
            
            # 3. 测试系统响应
            impact_metrics = await self._test_system_resilience()
            
            # 4. 等待指定时长
            await asyncio.sleep(duration)
            
            # 5. 恢复
            recovery_start = time.time()
            await self._restore_database(database_name, degradation_type)
            recovery_time = time.time() - recovery_start
            
            # 6. 验证恢复
            await asyncio.sleep(10)
            after_metrics = await self._get_system_metrics()
            
            # 7. 记录结果
            end_time = datetime.utcnow()
            result.end_time = end_time.isoformat()
            result.duration = (end_time - start_time).total_seconds()
            result.success = True
            result.recovery_time = recovery_time
            result.impact_metrics = {
                "before": before_metrics,
                "during": impact_metrics,
                "after": after_metrics,
            }
            
            logger.info(f"数据库降级测试完成: 恢复时间 {recovery_time:.2f}秒")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"数据库降级测试失败: {e}", exc_info=True)
        
        finally:
            # 确保恢复
            await self._restore_database(database_name, degradation_type)
        
        self.test_results.append(result)
        return result
    
    # ============ API超时 ============
    
    async def test_api_timeout(
        self,
        endpoint: str = "/gateway/rag/search",
        timeout_duration: int = 30,
        test_duration: int = 60,
    ) -> ChaosTestResult:
        """
        测试API超时场景
        
        Args:
            endpoint: API端点
            timeout_duration: 超时时间（秒）
            test_duration: 测试持续时间（秒）
            
        Returns:
            测试结果
        """
        logger.info(f"开始故障演练: API超时 - {endpoint}")
        
        start_time = datetime.utcnow()
        result = ChaosTestResult(
            scenario=ChaosScenario.API_TIMEOUT,
            start_time=start_time.isoformat(),
            end_time="",
            duration=0.0,
            success=False,
            metadata={"endpoint": endpoint, "timeout": timeout_duration},
        )
        
        try:
            # 1. 记录故障前状态
            before_metrics = await self._get_system_metrics()
            
            # 2. 模拟API超时（通过增加处理时间）
            # 这里可以通过修改服务配置或使用代理来实现
            logger.info(f"模拟API超时: {endpoint}")
            
            # 3. 测试系统响应
            impact_metrics = await self._test_api_resilience(endpoint, timeout_duration)
            
            # 4. 等待指定时长
            await asyncio.sleep(test_duration)
            
            # 5. 恢复
            recovery_start = time.time()
            await self._restore_api_timeout(endpoint)
            recovery_time = time.time() - recovery_start
            
            # 6. 验证恢复
            await asyncio.sleep(10)
            after_metrics = await self._get_system_metrics()
            
            # 7. 记录结果
            end_time = datetime.utcnow()
            result.end_time = end_time.isoformat()
            result.duration = (end_time - start_time).total_seconds()
            result.success = True
            result.recovery_time = recovery_time
            result.impact_metrics = {
                "before": before_metrics,
                "during": impact_metrics,
                "after": after_metrics,
            }
            
            logger.info(f"API超时测试完成: 恢复时间 {recovery_time:.2f}秒")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"API超时测试失败: {e}", exc_info=True)
        
        finally:
            # 确保恢复
            await self._restore_api_timeout(endpoint)
        
        self.test_results.append(result)
        return result
    
    # ============ 辅助方法 ============
    
    async def _stop_service(self, service_name: str) -> bool:
        """停止服务"""
        try:
            if self.docker_client:
                container = self.docker_client.containers.get(service_name)
                container.stop()
            else:
                # 使用docker-compose
                subprocess.run(
                    ["docker-compose", "-f", "deployments/docker-compose.sidecar.yml", "stop", service_name],
                    check=True,
                )
            return True
        except Exception as e:
            logger.error(f"停止服务失败: {service_name} - {e}")
            return False
    
    async def _start_service(self, service_name: str) -> bool:
        """启动服务"""
        try:
            if self.docker_client:
                container = self.docker_client.containers.get(service_name)
                container.start()
            else:
                subprocess.run(
                    ["docker-compose", "-f", "deployments/docker-compose.sidecar.yml", "start", service_name],
                    check=True,
                )
            return True
        except Exception as e:
            logger.error(f"启动服务失败: {service_name} - {e}")
            return False
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            async with httpx.AsyncClient() as client:
                # 获取Gateway状态
                gateway_res = await client.get("http://localhost:9000/gateway/status", timeout=5.0)
                gateway_data = gateway_res.json() if gateway_res.status_code == 200 else {}
                
                return {
                    "gateway_status": gateway_data,
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    async def _test_system_resilience(self) -> Dict[str, Any]:
        """测试系统弹性"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 测试关键端点
                test_endpoints = [
                    "/health",
                    "/gateway/health",
                ]
                
                results = {}
                for endpoint in test_endpoints:
                    try:
                        start = time.time()
                        response = await client.get(f"http://localhost:9000{endpoint}")
                        elapsed = (time.time() - start) * 1000
                        
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "response_time_ms": elapsed,
                            "available": response.status_code < 400,
                        }
                    except Exception as e:
                        results[endpoint] = {
                            "status_code": 0,
                            "response_time_ms": 10000,
                            "available": False,
                            "error": str(e)[:100],
                        }
                
                return results
        except Exception as e:
            logger.error(f"测试系统弹性失败: {e}")
            return {}
    
    async def _test_api_resilience(
        self,
        endpoint: str,
        timeout: int,
    ) -> Dict[str, Any]:
        """测试API弹性"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                results = []
                
                for _ in range(10):
                    try:
                        start = time.time()
                        response = await client.get(f"http://localhost:9000{endpoint}?query=test")
                        elapsed = (time.time() - start) * 1000
                        
                        results.append({
                            "status_code": response.status_code,
                            "response_time_ms": elapsed,
                            "success": response.status_code < 400,
                        })
                    except httpx.TimeoutException:
                        results.append({
                            "status_code": 0,
                            "response_time_ms": timeout * 1000,
                            "success": False,
                            "error": "timeout",
                        })
                    except Exception as e:
                        results.append({
                            "status_code": 0,
                            "response_time_ms": 0,
                            "success": False,
                            "error": str(e)[:100],
                        })
                
                return {
                    "total_requests": len(results),
                    "successful": sum(1 for r in results if r["success"]),
                    "failed": sum(1 for r in results if not r["success"]),
                    "avg_response_time": sum(r["response_time_ms"] for r in results) / len(results) if results else 0,
                    "results": results,
                }
        except Exception as e:
            logger.error(f"测试API弹性失败: {e}")
            return {}
    
    async def _inject_database_delay(self, database_name: str, delay_ms: int):
        """注入数据库延迟"""
        # 这里可以通过修改数据库配置或使用代理实现
        logger.info(f"注入数据库延迟: {database_name} - {delay_ms}ms")
        # 实际实现需要根据具体数据库类型
    
    async def _limit_database_connections(self, database_name: str, max_connections: int):
        """限制数据库连接数"""
        logger.info(f"限制数据库连接数: {database_name} - {max_connections}")
        # 实际实现需要根据具体数据库类型
    
    async def _simulate_disk_full(self, database_name: str):
        """模拟磁盘满"""
        logger.info(f"模拟磁盘满: {database_name}")
        # 实际实现需要根据具体数据库类型
    
    async def _restore_database(self, database_name: str, degradation_type: str):
        """恢复数据库"""
        logger.info(f"恢复数据库: {database_name} - {degradation_type}")
        # 实际实现需要根据具体数据库类型
    
    async def _restore_api_timeout(self, endpoint: str):
        """恢复API超时"""
        logger.info(f"恢复API超时: {endpoint}")
        # 实际实现需要根据具体API类型
    
    def generate_chaos_report(self) -> Dict[str, Any]:
        """生成故障演练报告"""
        return {
            "report_id": f"chaos_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "total_tests": len(self.test_results),
            "results": [r.to_dict() for r in self.test_results],
            "summary": self._generate_summary(),
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成汇总统计"""
        if not self.test_results:
            return {}
        
        successful = sum(1 for r in self.test_results if r.success)
        failed = len(self.test_results) - successful
        
        recovery_times = [r.recovery_time for r in self.test_results if r.recovery_time]
        
        return {
            "successful_tests": successful,
            "failed_tests": failed,
            "success_rate": (successful / len(self.test_results) * 100) if self.test_results else 0,
            "avg_recovery_time": sum(recovery_times) / len(recovery_times) if recovery_times else 0,
            "max_recovery_time": max(recovery_times) if recovery_times else 0,
        }

