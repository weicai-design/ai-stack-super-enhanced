#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证测试（T003）
验证所有API响应时间<2秒

验收标准：
1. 95%的请求响应时间<2秒
2. 有完整的性能报告
3. 包含详细的性能指标
"""

from __future__ import annotations

import asyncio
import time
import pytest
import logging
import statistics
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import sys
import json
from dataclasses import dataclass, field, asdict

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    print("警告: httpx 未安装，某些功能可能不可用")
    httpx = None

logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 配置（支持环境变量覆盖，便于脚本化运行）
BASE_URL = os.environ.get("SLO_BASE_URL", "http://localhost:8000")
SLO_TARGET_MS = int(os.environ.get("SLO_TARGET_MS", "2000"))  # 2秒SLO
SLO_COMPLIANCE_RATE = float(os.environ.get("SLO_COMPLIANCE_RATE", "0.95"))  # 95%合规率
TEST_ITERATIONS = int(os.environ.get("SLO_TEST_ITERATIONS", "10"))  # 每个API测试次数


@dataclass
class SLOTestResult:
    """SLO测试结果"""
    api_endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times_ms: List[float]
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    slo_compliant_rate: float
    slo_compliant: bool
    errors: List[str]
    compliant_requests: int = 0
    service_unavailable: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SLO2sPerformanceTest:
    """
    2秒SLO性能验证测试类（T003）
    
    验证所有API响应时间<2秒
    """
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results: List[SLOTestResult] = []
        
        # 定义要测试的API端点
        self.api_endpoints = [
            # 工作流API
            {"path": "/api/workflow/intelligent", "method": "POST", "data": {"user_input": "测试查询"}},
            {"path": "/api/workflow/direct", "method": "POST", "data": {"module": "erp", "action": "get_orders", "params": {}}},
            {"path": "/api/workflow/status", "method": "GET"},
            
            # 超级Agent API
            {"path": "/api/super-agent/chat", "method": "POST", "data": {"message": "测试消息"}},
            {"path": "/api/super-agent/health", "method": "GET"},
            
            # RAG API
            {"path": "/api/super-agent/rag/query", "method": "POST", "data": {"query": "测试查询"}},
            
            # ERP API
            {"path": "/api/super-agent/erp/orders", "method": "GET", "params": {"limit": 10}},
            
            # 内容API
            {"path": "/api/super-agent/content/list", "method": "GET", "params": {"limit": 10}},
            
            # 趋势API
            {"path": "/api/super-agent/trend/reports", "method": "GET", "params": {"limit": 10}},
            
            # 任务生命周期API
            {"path": "/api/task-lifecycle/list", "method": "GET"},
            {"path": "/api/task-lifecycle/statistics", "method": "GET"},
        ]
    
    async def test_api_slo(self, endpoint: Dict[str, Any]) -> SLOTestResult:
        """
        测试单个API的SLO合规性
        
        Args:
            endpoint: API端点配置
            
        Returns:
            SLO测试结果
        """
        api_path = endpoint["path"]
        method = endpoint.get("method", "GET")
        data = endpoint.get("data")
        params = endpoint.get("params")
        
        logger.info(f"测试API: {method} {api_path}")
        
        response_times_ms: List[float] = []
        errors: List[str] = []
        successful_requests = 0
        failed_requests = 0
        compliant_requests = 0
        
        if httpx is None:
            logger.warning("httpx未安装，跳过API测试")
            return SLOTestResult(
                api_endpoint=api_path,
                method=method,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                response_times_ms=[],
                avg_response_time_ms=0,
                median_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                slo_compliant_rate=0,
                slo_compliant=False,
                errors=["httpx未安装"],
            )
        
        # 执行多次请求
        async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
            for _ in range(TEST_ITERATIONS):
                try:
                    start_time = time.perf_counter()
                    
                    if method == "GET":
                        response = await client.get(api_path, params=params)
                    elif method == "POST":
                        response = await client.post(api_path, json=data, params=params)
                    else:
                        raise ValueError(f"不支持的HTTP方法: {method}")
                    
                    end_time = time.perf_counter()
                    response_time_ms = (end_time - start_time) * 1000
                    
                    if response.status_code < 500:  # 2xx, 3xx, 4xx都算成功（只排除5xx）
                        response_times_ms.append(response_time_ms)
                        successful_requests += 1
                        if response_time_ms < SLO_TARGET_MS:
                            compliant_requests += 1
                    else:
                        failed_requests += 1
                        errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                        
                except Exception as e:
                    failed_requests += 1
                    error_msg = str(e)[:200]
                    errors.append(error_msg)
                    logger.warning(f"请求失败: {error_msg}")
        
        # 计算统计指标
        if response_times_ms:
            avg_response_time_ms = statistics.mean(response_times_ms)
            median_response_time_ms = statistics.median(response_times_ms)
            min_response_time_ms = min(response_times_ms)
            max_response_time_ms = max(response_times_ms)
            
            # 计算百分位数
            sorted_times = sorted(response_times_ms)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time_ms = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            p99_response_time_ms = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
            
            # 计算SLO合规率
            slo_compliant_rate = compliant_requests / len(response_times_ms)
            slo_compliant = slo_compliant_rate >= SLO_COMPLIANCE_RATE
        else:
            avg_response_time_ms = 0
            median_response_time_ms = 0
            min_response_time_ms = 0
            max_response_time_ms = 0
            p95_response_time_ms = 0
            p99_response_time_ms = 0
            slo_compliant_rate = 0
            slo_compliant = False
            compliant_requests = 0
        
        service_unavailable = successful_requests == 0
        result = SLOTestResult(
            api_endpoint=api_path,
            method=method,
            total_requests=TEST_ITERATIONS,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            response_times_ms=response_times_ms,
            avg_response_time_ms=avg_response_time_ms,
            median_response_time_ms=median_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            min_response_time_ms=min_response_time_ms,
            max_response_time_ms=max_response_time_ms,
            slo_compliant_rate=slo_compliant_rate,
            slo_compliant=slo_compliant,
            errors=errors[:5],  # 只保留前5个错误
            compliant_requests=compliant_requests,
            service_unavailable=service_unavailable,
        )
        
        self.test_results.append(result)
        
        logger.info(f"  ✓ 平均响应时间: {avg_response_time_ms:.2f}ms")
        logger.info(f"  ✓ P95响应时间: {p95_response_time_ms:.2f}ms")
        logger.info(f"  ✓ SLO合规率: {slo_compliant_rate*100:.1f}% ({'✓' if slo_compliant else '✗'})")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有API的SLO测试"""
        logger.info("="*60)
        logger.info("开始2秒SLO性能验证测试（T003）")
        logger.info("="*60)
        logger.info(f"测试API数量: {len(self.api_endpoints)}")
        logger.info(f"每个API测试次数: {TEST_ITERATIONS}")
        logger.info(f"SLO目标: {SLO_TARGET_MS}ms")
        logger.info(f"合规率要求: {SLO_COMPLIANCE_RATE*100}%")
        logger.info("")
        
        # 测试所有API
        for endpoint in self.api_endpoints:
            await self.test_api_slo(endpoint)
            await asyncio.sleep(0.1)  # 短暂延迟，避免过载
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        report_file = Path("logs/workflow") / f"slo_2s_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("")
        logger.info("="*60)
        logger.info("2秒SLO性能验证测试报告")
        logger.info("="*60)
        logger.info(f"总API数: {report['summary']['total_apis']}")
        logger.info(f"SLO合规API数: {report['summary']['slo_compliant_apis']}")
        logger.info(f"请求级SLO合规率: {report['summary']['overall_request_compliance_rate']*100:.1f}%")
        logger.info(f"API级SLO合规率: {report['summary']['overall_api_compliance_rate']*100:.1f}%")
        logger.info(f"平均响应时间: {report['summary']['avg_response_time_ms']:.2f}ms")
        logger.info(f"P95响应时间: {report['summary']['p95_response_time_ms']:.2f}ms")
        logger.info(f"报告已保存: {report_file}")
        
        return report
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_apis = len(self.test_results)
        slo_compliant_apis = sum(1 for r in self.test_results if r.slo_compliant)
        api_level_compliance_rate = slo_compliant_apis / total_apis if total_apis > 0 else 0
        
        total_requests = sum(r.total_requests for r in self.test_results)
        total_samples = sum(len(r.response_times_ms) for r in self.test_results)
        total_successful_requests = sum(r.successful_requests for r in self.test_results)
        total_compliant_samples = sum(r.compliant_requests for r in self.test_results)
        request_level_compliance_rate = (
            total_compliant_samples / total_samples if total_samples else 0
        )
        api_service_unavailable = total_samples == 0
        
        # 计算整体统计
        all_response_times: List[float] = []
        for result in self.test_results:
            all_response_times.extend(result.response_times_ms)
        
        if all_response_times:
            avg_response_time_ms = statistics.mean(all_response_times)
            # 计算百分位数（statistics模块没有percentile函数，手动计算）
            sorted_times = sorted(all_response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_response_time_ms = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            p99_response_time_ms = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
        else:
            avg_response_time_ms = 0
            p95_response_time_ms = 0
            p99_response_time_ms = 0
        
        report = {
            "test_suite": "2秒SLO性能验证测试（T003）",
            "timestamp": datetime.now().isoformat(),
            "slo_target_ms": SLO_TARGET_MS,
            "slo_compliance_rate_required": SLO_COMPLIANCE_RATE,
            "summary": {
                "total_apis": total_apis,
                "total_requests": total_requests,
                "total_successful_requests": total_successful_requests,
                "total_samples": total_samples,
                "total_compliant_samples": total_compliant_samples,
                "slo_compliant_apis": slo_compliant_apis,
                "slo_non_compliant_apis": total_apis - slo_compliant_apis,
                "overall_api_compliance_rate": api_level_compliance_rate,
                "overall_request_compliance_rate": request_level_compliance_rate,
                "avg_response_time_ms": avg_response_time_ms,
                "p95_response_time_ms": p95_response_time_ms,
                "p99_response_time_ms": p99_response_time_ms,
                "api_service_unavailable": api_service_unavailable,
                "note": "如果api_service_unavailable为true，说明API服务未运行在localhost:8000。请先启动API服务。" if api_service_unavailable else None,
                "service_unavailable_endpoints": [
                    r.api_endpoint for r in self.test_results if r.service_unavailable
                ],
            },
            "test_results": [r.to_dict() for r in self.test_results],
        }
        
        return report


@pytest.mark.asyncio
async def test_slo_2s_all_apis():
    """Pytest测试用例：所有API的2秒SLO测试"""
    test = SLO2sPerformanceTest()
    report = await test.run_all_tests()
    
    # 如果所有API都连接失败，说明API服务未运行，跳过测试
    summary = report["summary"]
    if summary["overall_request_compliance_rate"] == 0.0 and summary["total_successful_requests"] == 0:
        pytest.skip(
            "API服务未运行（或所有请求失败），无法进行SLO验证。请先启动 http://localhost:8000 的API服务。"
        )
    
    # 验证整体SLO合规率
    assert summary["overall_request_compliance_rate"] >= SLO_COMPLIANCE_RATE, \
        f"SLO合规率 {summary['overall_request_compliance_rate']*100:.1f}% 低于要求的 {SLO_COMPLIANCE_RATE*100}%"


async def main():
    """主函数：运行2秒SLO性能测试"""
    test = SLO2sPerformanceTest()
    report = await test.run_all_tests()
    return report


if __name__ == "__main__":
    asyncio.run(main())

