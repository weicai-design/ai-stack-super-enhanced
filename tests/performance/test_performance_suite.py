#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试套件
P3-403: 建立性能测试框架
"""

from __future__ import annotations

import asyncio
import time
import statistics
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import httpx
import concurrent.futures

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time: float  # 毫秒
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    qps: float  # 每秒查询数
    duration: float  # 测试时长（秒）
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceTestSuite:
    """
    性能测试套件
    
    功能：
    1. 负载测试
    2. 压力测试
    3. 稳定性测试
    4. 基准测试
    """
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        """
        初始化性能测试套件
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results: List[PerformanceMetrics] = []
        
        logger.info(f"性能测试套件初始化完成，基础URL: {base_url}")
    
    async def load_test(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
    ) -> PerformanceMetrics:
        """
        负载测试
        
        Args:
            endpoint: API端点
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
            method: HTTP方法
            payload: 请求体（POST/PUT时使用）
            
        Returns:
            性能指标
        """
        test_name = f"load_test_{endpoint.replace('/', '_')}_{concurrent_users}users"
        logger.info(f"开始负载测试: {test_name}")
        
        start_time = time.time()
        response_times: List[float] = []
        success_count = 0
        failure_count = 0
        errors: List[str] = []
        
        async def make_request():
            """单个请求"""
            try:
                req_start = time.time()
                
                if method.upper() == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                elif method.upper() == "POST":
                    response = await self.client.post(f"{self.base_url}{endpoint}", json=payload)
                elif method.upper() == "PUT":
                    response = await self.client.put(f"{self.base_url}{endpoint}", json=payload)
                else:
                    response = await self.client.request(method, f"{self.base_url}{endpoint}", json=payload)
                
                req_time = (time.time() - req_start) * 1000  # 转换为毫秒
                response_times.append(req_time)
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                
            except Exception as e:
                failure_count += 1
                errors.append(str(e)[:100])
        
        # 并发执行
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(requests_per_user):
                tasks.append(make_request())
        
        # 执行所有请求
        await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        total_requests = concurrent_users * requests_per_user
        
        # 计算统计指标
        metrics = self._calculate_metrics(
            test_name=test_name,
            response_times=response_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            duration=duration,
            errors=errors,
        )
        
        self.results.append(metrics)
        logger.info(f"负载测试完成: {test_name} - QPS: {metrics.qps:.2f}, 成功率: {metrics.success_rate:.2f}%")
        
        return metrics
    
    async def stress_test(
        self,
        endpoint: str,
        initial_users: int = 10,
        max_users: int = 100,
        step: int = 10,
        requests_per_user: int = 5,
        method: str = "GET",
    ) -> List[PerformanceMetrics]:
        """
        压力测试（递增负载）
        
        Args:
            endpoint: API端点
            initial_users: 初始并发用户数
            max_users: 最大并发用户数
            step: 每次递增的用户数
            requests_per_user: 每个用户的请求数
            method: HTTP方法
            
        Returns:
            性能指标列表
        """
        logger.info(f"开始压力测试: {endpoint} ({initial_users} -> {max_users} users)")
        
        results = []
        current_users = initial_users
        
        while current_users <= max_users:
            metrics = await self.load_test(
                endpoint=endpoint,
                concurrent_users=current_users,
                requests_per_user=requests_per_user,
                method=method,
            )
            results.append(metrics)
            
            # 等待一段时间再增加负载
            await asyncio.sleep(2)
            current_users += step
        
        return results
    
    async def stability_test(
        self,
        endpoint: str,
        duration_seconds: int = 300,
        requests_per_second: int = 10,
        method: str = "GET",
    ) -> PerformanceMetrics:
        """
        稳定性测试（长时间运行）
        
        Args:
            endpoint: API端点
            duration_seconds: 测试时长（秒）
            requests_per_second: 每秒请求数
            method: HTTP方法
            
        Returns:
            性能指标
        """
        test_name = f"stability_test_{endpoint.replace('/', '_')}_{duration_seconds}s"
        logger.info(f"开始稳定性测试: {test_name}")
        
        start_time = time.time()
        response_times: List[float] = []
        success_count = 0
        failure_count = 0
        errors: List[str] = []
        
        async def make_request():
            """单个请求"""
            try:
                req_start = time.time()
                
                if method.upper() == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                else:
                    response = await self.client.request(method, f"{self.base_url}{endpoint}")
                
                req_time = (time.time() - req_start) * 1000
                response_times.append(req_time)
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"HTTP {response.status_code}")
                
            except Exception as e:
                failure_count += 1
                errors.append(str(e)[:100])
        
        # 持续发送请求
        interval = 1.0 / requests_per_second
        end_time = start_time + duration_seconds
        
        while time.time() < end_time:
            await make_request()
            await asyncio.sleep(interval)
        
        duration = time.time() - start_time
        total_requests = success_count + failure_count
        
        # 计算统计指标
        metrics = self._calculate_metrics(
            test_name=test_name,
            response_times=response_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            duration=duration,
            errors=errors,
        )
        
        self.results.append(metrics)
        logger.info(f"稳定性测试完成: {test_name}")
        
        return metrics
    
    async def benchmark_test(
        self,
        endpoints: List[str],
        iterations: int = 100,
    ) -> Dict[str, PerformanceMetrics]:
        """
        基准测试
        
        Args:
            endpoints: API端点列表
            iterations: 每个端点的测试次数
            
        Returns:
            各端点的性能指标
        """
        logger.info(f"开始基准测试: {len(endpoints)} 个端点，每个 {iterations} 次")
        
        results = {}
        
        for endpoint in endpoints:
            response_times: List[float] = []
            success_count = 0
            failure_count = 0
            errors: List[str] = []
            
            start_time = time.time()
            
            for _ in range(iterations):
                try:
                    req_start = time.time()
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                    req_time = (time.time() - req_start) * 1000
                    
                    response_times.append(req_time)
                    
                    if response.status_code < 400:
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append(f"HTTP {response.status_code}")
                
                except Exception as e:
                    failure_count += 1
                    errors.append(str(e)[:100])
            
            duration = time.time() - start_time
            total_requests = iterations
            
            metrics = self._calculate_metrics(
                test_name=f"benchmark_{endpoint.replace('/', '_')}",
                response_times=response_times,
                total_requests=total_requests,
                successful_requests=success_count,
                failed_requests=failure_count,
                duration=duration,
                errors=errors,
            )
            
            results[endpoint] = metrics
            self.results.append(metrics)
        
        return results
    
    def _calculate_metrics(
        self,
        test_name: str,
        response_times: List[float],
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        duration: float,
        errors: List[str],
    ) -> PerformanceMetrics:
        """计算性能指标"""
        if not response_times:
            return PerformanceMetrics(
                test_name=test_name,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=0.0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p50_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                qps=0.0,
                duration=duration,
                errors=errors,
            )
        
        sorted_times = sorted(response_times)
        
        return PerformanceMetrics(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=(successful_requests / total_requests * 100) if total_requests > 0 else 0.0,
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p50_response_time=sorted_times[int(len(sorted_times) * 0.50)],
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)],
            qps=successful_requests / duration if duration > 0 else 0.0,
            duration=duration,
            errors=errors[:10],  # 只保留前10个错误
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        return {
            "test_suite": "Performance Test Suite",
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": self._generate_summary(),
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成汇总统计"""
        if not self.results:
            return {}
        
        all_qps = [r.qps for r in self.results]
        all_success_rates = [r.success_rate for r in self.results]
        all_avg_times = [r.avg_response_time for r in self.results]
        all_p95_times = [r.p95_response_time for r in self.results]
        
        return {
            "avg_qps": statistics.mean(all_qps),
            "max_qps": max(all_qps),
            "avg_success_rate": statistics.mean(all_success_rates),
            "min_success_rate": min(all_success_rates),
            "avg_response_time": statistics.mean(all_avg_times),
            "max_response_time": max(all_avg_times),
            "avg_p95_time": statistics.mean(all_p95_times),
            "max_p95_time": max(all_p95_times),
        }
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()

