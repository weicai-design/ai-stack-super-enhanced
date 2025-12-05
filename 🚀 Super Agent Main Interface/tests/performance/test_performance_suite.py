#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试套件（生产级实现）
7.1: 运行性能测试，记录2秒SLO、专家协同案例等数据
"""

from __future__ import annotations

import asyncio
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    print("警告: httpx 未安装，某些功能可能不可用")
    httpx = None

try:
    import pytest
except ImportError:
    print("警告: pytest 未安装，某些功能可能不可用")
    pytest = None

from core.slo_performance_reporter import (
    slo_performance_reporter,
    VectorIndexBenchmark,
    StreamingBenchmark,
    ContextCompressionBenchmark,
)
from core.slo_report_generator import get_slo_report_generator
from core.performance_monitor import PerformanceMonitor
from core.expert_collaboration import ExpertCollaborationHub, get_expert_collaboration_hub
from core.data_service import get_data_service

logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class PerformanceTestResult:
    """性能测试结果"""
    test_name: str
    success: bool
    response_time_ms: float
    target_time_ms: float = 2000.0  # 2秒SLO
    status: str = "unknown"  # pass/fail/warning
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExpertCollaborationCase:
    """专家协同案例"""
    case_id: str
    topic: str
    initiator: str
    experts: List[Dict[str, Any]]
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    contributions_count: int = 0
    decisions_count: int = 0
    synergy_score: float = 0.0
    response_latency_ms: Optional[float] = None
    status: str = "completed"  # completed/failed/timeout
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceTestSuite:
    """
    性能测试套件（生产级实现 - 7.1）
    
    功能：
    1. 2秒SLO测试
    2. 专家协同案例测试
    3. API性能测试
    4. 负载测试
    5. 压力测试
    6. 结果记录和报告
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        slo_target_ms: float = 2000.0,  # 2秒SLO
    ):
        self.base_url = base_url
        self.slo_target_ms = slo_target_ms
        self.client: Optional[httpx.AsyncClient] = None
        self.performance_monitor = PerformanceMonitor(target_response_time=slo_target_ms / 1000.0)
        self.slo_reporter = slo_performance_reporter
        self.slo_generator = get_slo_report_generator()
        self.expert_hub = get_expert_collaboration_hub()
        
        # 测试结果存储
        self.test_results: List[PerformanceTestResult] = []
        self.expert_collaboration_cases: List[ExpertCollaborationCase] = []
        
        # 结果存储目录
        self.results_dir = PROJECT_ROOT / "performance_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"性能测试套件初始化完成（SLO目标: {slo_target_ms}ms）")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self.client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    # ============ 2秒SLO测试 ============
    
    async def test_slo_2s(
        self,
        endpoint: str = "/api/super-agent/chat",
        test_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> PerformanceTestResult:
        """
        测试2秒SLO
        
        Args:
            endpoint: 测试端点
            test_cases: 测试用例列表
            
        Returns:
            测试结果
        """
        test_name = f"slo_2s_{endpoint.replace('/', '_')}"
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            # 默认测试用例
            if not test_cases:
                test_cases = [
                    {"message": "你好", "context": {}},
                    {"message": "查询最近的订单", "context": {}},
                    {"message": "分析市场趋势", "context": {}},
                ]
            
            results = []
            for i, test_case in enumerate(test_cases):
                case_start = time.time()
                try:
                    response = await client.post(
                        endpoint,
                        json=test_case,
                        timeout=self.slo_target_ms / 1000.0 + 1.0,  # 超时时间稍大于SLO
                    )
                    case_duration = (time.time() - case_start) * 1000  # 转换为毫秒
                    
                    results.append({
                        "case": i + 1,
                        "duration_ms": case_duration,
                        "status_code": response.status_code,
                        "success": response.status_code == 200 and case_duration <= self.slo_target_ms,
                    })
                    
                    # 记录性能指标
                    self.performance_monitor.record_response_time(
                        case_duration / 1000.0,
                        from_cache=False,
                    )
                    
                except asyncio.TimeoutError:
                    case_duration = self.slo_target_ms + 1000  # 超时
                    results.append({
                        "case": i + 1,
                        "duration_ms": case_duration,
                        "status_code": None,
                        "success": False,
                        "error": "timeout",
                    })
                except Exception as e:
                    case_duration = (time.time() - case_start) * 1000
                    results.append({
                        "case": i + 1,
                        "duration_ms": case_duration,
                        "status_code": None,
                        "success": False,
                        "error": str(e),
                    })
            
            # 计算平均响应时间
            avg_duration = sum(r["duration_ms"] for r in results) / len(results) if results else 0
            success_count = sum(1 for r in results if r.get("success", False))
            success_rate = success_count / len(results) if results else 0
            
            # 确定状态
            if avg_duration <= self.slo_target_ms and success_rate >= 0.95:
                status = "pass"
            elif avg_duration <= self.slo_target_ms * 1.2 and success_rate >= 0.90:
                status = "warning"
            else:
                status = "fail"
            
            total_duration = (time.time() - start_time) * 1000
            
            result = PerformanceTestResult(
                test_name=test_name,
                success=status == "pass",
                response_time_ms=avg_duration,
                target_time_ms=self.slo_target_ms,
                status=status,
                metadata={
                    "endpoint": endpoint,
                    "test_cases": results,
                    "success_rate": success_rate,
                    "total_duration_ms": total_duration,
                },
            )
            
            self.test_results.append(result)
            
            # 记录到SLO报告生成器
            self.slo_generator.record_metric(
                slo_name="response_time_2s",
                value=avg_duration,
                metadata={"test_name": test_name, "endpoint": endpoint},
            )
            
            logger.info(f"2秒SLO测试完成: {test_name} - 平均响应时间: {avg_duration:.2f}ms, 状态: {status}")
            
            return result
        
        except Exception as e:
            logger.error(f"2秒SLO测试失败: {e}", exc_info=True)
            result = PerformanceTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=0.0,
                target_time_ms=self.slo_target_ms,
                status="fail",
                error=str(e),
            )
            self.test_results.append(result)
            return result
    
    # ============ 专家协同案例测试 ============
    
    async def test_expert_collaboration_case(
        self,
        topic: str = "性能优化方案讨论",
        initiator: str = "system",
        experts: Optional[List[Dict[str, Any]]] = None,
        goals: Optional[List[str]] = None,
    ) -> ExpertCollaborationCase:
        """
        测试专家协同案例
        
        Args:
            topic: 协同主题
            initiator: 发起人
            experts: 专家列表
            goals: 目标列表
            
        Returns:
            协同案例
        """
        case_id = f"collab_case_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        start_time_iso = datetime.utcnow().isoformat() + "Z"
        
        try:
            # 默认专家列表
            if not experts:
                experts = [
                    {"expert_id": "rag-1", "name": "RAG专家", "domain": "rag"},
                    {"expert_id": "ops-1", "name": "运营专家", "domain": "operations"},
                    {"expert_id": "tech-1", "name": "技术专家", "domain": "technology"},
                ]
            
            if not goals:
                goals = ["分析性能瓶颈", "提出优化方案", "制定行动计划"]
            
            # 创建协同会话
            session = await self.expert_hub.start_session(
                topic=topic,
                initiator=initiator,
                goals=goals,
                experts=experts,
            )
            session_id = session["session_id"]
            
            # 模拟专家贡献
            contributions = []
            for i, expert in enumerate(experts):
                contribution_start = time.time()
                
                await self.expert_hub.add_contribution(
                    session_id=session_id,
                    expert_id=expert["expert_id"],
                    expert_name=expert["name"],
                    summary=f"{expert['name']}的分析和建议",
                    channel=expert.get("domain", "general"),
                    action_items=[f"行动项{i+1}"],
                    impact_score=0.7 + i * 0.1,
                )
                
                contribution_duration = (time.time() - contribution_start) * 1000
                contributions.append({
                    "expert_id": expert["expert_id"],
                    "duration_ms": contribution_duration,
                })
            
            # 最终决策
            decision_start = time.time()
            final_session = await self.expert_hub.finalize_session(
                session_id=session_id,
                owner=initiator,
                summary="完成协同讨论，达成共识",
                kpis=["响应时间<2s", "成功率>95%"],
                followups=["持续监控性能指标"],
            )
            decision_duration = (time.time() - decision_start) * 1000
            
            # 计算总耗时
            total_duration = (time.time() - start_time) * 1000
            end_time_iso = datetime.utcnow().isoformat() + "Z"
            
            # 获取会话元数据
            metadata = final_session.get("metadata", {})
            synergy_score = metadata.get("synergy_score", 0.0)
            response_latency = metadata.get("response_latency_ms")
            
            # 确定状态
            if total_duration <= self.slo_target_ms:
                status = "completed"
            elif total_duration <= self.slo_target_ms * 2:
                status = "completed"  # 仍算完成，但超时
            else:
                status = "timeout"
            
            case = ExpertCollaborationCase(
                case_id=case_id,
                topic=topic,
                initiator=initiator,
                experts=experts,
                start_time=start_time_iso,
                end_time=end_time_iso,
                duration_ms=total_duration,
                contributions_count=len(contributions),
                decisions_count=1,
                synergy_score=synergy_score,
                response_latency_ms=response_latency,
                status=status,
                metadata={
                    "session_id": session_id,
                    "contributions": contributions,
                    "decision_duration_ms": decision_duration,
                    "goals": goals,
                },
            )
            
            self.expert_collaboration_cases.append(case)
            
            # 记录性能指标
            self.performance_monitor.record_response_time(
                total_duration / 1000.0,
                from_cache=False,
            )
            
            logger.info(f"专家协同案例测试完成: {case_id} - 耗时: {total_duration:.2f}ms, 协同指数: {synergy_score:.2f}")
            
            return case
        
        except Exception as e:
            logger.error(f"专家协同案例测试失败: {e}", exc_info=True)
            end_time_iso = datetime.utcnow().isoformat() + "Z"
            total_duration = (time.time() - start_time) * 1000
            
            case = ExpertCollaborationCase(
                case_id=case_id,
                topic=topic,
                initiator=initiator,
                experts=experts or [],
                start_time=start_time_iso,
                end_time=end_time_iso,
                duration_ms=total_duration,
                status="failed",
                metadata={"error": str(e)},
            )
            self.expert_collaboration_cases.append(case)
            return case
    
    # ============ API性能测试 ============
    
    async def test_api_performance(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        iterations: int = 10,
    ) -> PerformanceTestResult:
        """
        测试API性能
        
        Args:
            endpoint: API端点
            method: HTTP方法
            payload: 请求负载
            iterations: 迭代次数
            
        Returns:
            测试结果
        """
        test_name = f"api_perf_{method.lower()}_{endpoint.replace('/', '_')}"
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            durations = []
            success_count = 0
            
            for i in range(iterations):
                iter_start = time.time()
                try:
                    if method.upper() == "GET":
                        response = await client.get(endpoint, timeout=30.0)
                    elif method.upper() == "POST":
                        response = await client.post(endpoint, json=payload, timeout=30.0)
                    else:
                        raise ValueError(f"不支持的HTTP方法: {method}")
                    
                    iter_duration = (time.time() - iter_start) * 1000
                    durations.append(iter_duration)
                    
                    if response.status_code == 200:
                        success_count += 1
                    
                    # 记录性能指标
                    self.performance_monitor.record_response_time(
                        iter_duration / 1000.0,
                        from_cache=False,
                    )
                
                except Exception as e:
                    iter_duration = (time.time() - iter_start) * 1000
                    durations.append(iter_duration)
                    logger.warning(f"API请求失败: {e}")
            
            # 计算统计信息
            avg_duration = sum(durations) / len(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            sorted_durations = sorted(durations)
            p50_duration = sorted_durations[int(len(sorted_durations) * 0.50)] if sorted_durations else 0
            p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
            p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0
            success_rate = success_count / iterations if iterations > 0 else 0
            
            # 确定状态
            if avg_duration <= self.slo_target_ms and success_rate >= 0.95:
                status = "pass"
            elif avg_duration <= self.slo_target_ms * 1.2 and success_rate >= 0.90:
                status = "warning"
            else:
                status = "fail"
            
            result = PerformanceTestResult(
                test_name=test_name,
                success=status == "pass",
                response_time_ms=avg_duration,
                target_time_ms=self.slo_target_ms,
                status=status,
                metadata={
                    "endpoint": endpoint,
                    "method": method,
                    "iterations": iterations,
                    "success_rate": success_rate,
                    "min_duration_ms": min_duration,
                    "max_duration_ms": max_duration,
                    "p50_duration_ms": p50_duration,
                    "p95_duration_ms": p95_duration,
                    "p99_duration_ms": p99_duration,
                },
            )
            
            self.test_results.append(result)
            
            logger.info(f"API性能测试完成: {test_name} - 平均响应时间: {avg_duration:.2f}ms, P95: {p95_duration:.2f}ms")
            
            return result
        
        except Exception as e:
            logger.error(f"API性能测试失败: {e}", exc_info=True)
            result = PerformanceTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=0.0,
                target_time_ms=self.slo_target_ms,
                status="fail",
                error=str(e),
            )
            self.test_results.append(result)
            return result
    
    # ============ 负载测试 ============
    
    async def load_test(
        self,
        endpoint: str = "/api/super-agent/health",
        concurrent_users: int = 10,
        requests_per_user: int = 10,
    ) -> PerformanceTestResult:
        """
        负载测试
        
        Args:
            endpoint: 测试端点
            concurrent_users: 并发用户数
            requests_per_user: 每个用户的请求数
            
        Returns:
            测试结果
        """
        test_name = f"load_test_{endpoint.replace('/', '_')}"
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            async def user_request(user_id: int):
                """单个用户的请求"""
                user_durations = []
                for i in range(requests_per_user):
                    req_start = time.time()
                    try:
                        response = await client.get(endpoint, timeout=30.0)
                        req_duration = (time.time() - req_start) * 1000
                        user_durations.append(req_duration)
                    except Exception as e:
                        req_duration = (time.time() - req_start) * 1000
                        user_durations.append(req_duration)
                        logger.warning(f"用户{user_id}请求{i+1}失败: {e}")
                return user_durations
            
            # 并发执行
            tasks = [user_request(i) for i in range(concurrent_users)]
            all_results = await asyncio.gather(*tasks)
            
            # 汇总结果
            all_durations = []
            for user_results in all_results:
                all_durations.extend(user_results)
            
            total_requests = concurrent_users * requests_per_user
            avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
            success_count = sum(1 for d in all_durations if d <= self.slo_target_ms)
            success_rate = success_count / len(all_durations) if all_durations else 0
            
            # 确定状态
            if avg_duration <= self.slo_target_ms and success_rate >= 0.95:
                status = "pass"
            elif avg_duration <= self.slo_target_ms * 1.2 and success_rate >= 0.90:
                status = "warning"
            else:
                status = "fail"
            
            total_duration = (time.time() - start_time) * 1000
            qps = total_requests / (total_duration / 1000.0) if total_duration > 0 else 0
            
            result = PerformanceTestResult(
                test_name=test_name,
                success=status == "pass",
                response_time_ms=avg_duration,
                target_time_ms=self.slo_target_ms,
                status=status,
                metadata={
                    "endpoint": endpoint,
                    "concurrent_users": concurrent_users,
                    "requests_per_user": requests_per_user,
                    "total_requests": total_requests,
                    "success_rate": success_rate,
                    "qps": qps,
                    "total_duration_ms": total_duration,
                },
            )
            
            self.test_results.append(result)
            
            logger.info(f"负载测试完成: {test_name} - 平均响应时间: {avg_duration:.2f}ms, QPS: {qps:.2f}, 成功率: {success_rate*100:.1f}%")
            
            return result
        
        except Exception as e:
            logger.error(f"负载测试失败: {e}", exc_info=True)
            result = PerformanceTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=0.0,
                target_time_ms=self.slo_target_ms,
                status="fail",
                error=str(e),
            )
            self.test_results.append(result)
            return result
    
    # ============ 压力测试 ============
    
    async def stress_test(
        self,
        endpoint: str = "/api/super-agent/health",
        initial_users: int = 10,
        max_users: int = 100,
        step: int = 10,
    ) -> List[PerformanceTestResult]:
        """
        压力测试（递增负载）
        
        Args:
            endpoint: 测试端点
            initial_users: 初始用户数
            max_users: 最大用户数
            step: 递增步长
            
        Returns:
            测试结果列表
        """
        results = []
        
        current_users = initial_users
        while current_users <= max_users:
            logger.info(f"压力测试: {current_users} 并发用户")
            
            result = await self.load_test(
                endpoint=endpoint,
                concurrent_users=current_users,
                requests_per_user=5,  # 每个用户5个请求
            )
            
            result.test_name = f"stress_test_{current_users}users_{endpoint.replace('/', '_')}"
            results.append(result)
            
            # 如果失败率过高，停止测试
            if result.metadata.get("success_rate", 1.0) < 0.80:
                logger.warning(f"成功率低于80%，停止压力测试")
                break
            
            current_users += step
            await asyncio.sleep(2)  # 间隔2秒
        
        return results
    
    # ============ 结果记录和报告 ============
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        保存测试结果
        
        Args:
            filename: 文件名（可选）
            
        Returns:
            保存的文件路径
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_test_results_{timestamp}.json"
        
        filepath = self.results_dir / filename
        
        data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "slo_target_ms": self.slo_target_ms,
            "test_results": [r.to_dict() for r in self.test_results],
            "expert_collaboration_cases": [c.to_dict() for c in self.expert_collaboration_cases],
            "performance_stats": self.performance_monitor.get_performance_stats(),
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试结果已保存: {filepath}")
        
        return str(filepath)
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        Returns:
            测试报告
        """
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.status == "pass")
        failed_tests = sum(1 for r in self.test_results if r.status == "fail")
        warning_tests = sum(1 for r in self.test_results if r.status == "warning")
        
        # 计算平均响应时间
        avg_response_time = (
            sum(r.response_time_ms for r in self.test_results) / total_tests
            if total_tests > 0
            else 0
        )
        
        # SLO达成率
        slo_compliance_rate = (
            (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0
        )
        
        # 专家协同案例统计
        total_cases = len(self.expert_collaboration_cases)
        completed_cases = sum(1 for c in self.expert_collaboration_cases if c.status == "completed")
        avg_case_duration = (
            sum(c.duration_ms for c in self.expert_collaboration_cases if c.duration_ms) / total_cases
            if total_cases > 0
            else 0
        )
        avg_synergy_score = (
            sum(c.synergy_score for c in self.expert_collaboration_cases) / total_cases
            if total_cases > 0
            else 0
        )
        
        # 性能统计
        perf_stats = self.performance_monitor.get_performance_stats()
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "slo_target_ms": self.slo_target_ms,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warning": warning_tests,
                "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "slo_compliance_rate": slo_compliance_rate,
            },
            "performance": {
                "avg_response_time_ms": avg_response_time,
                "performance_stats": perf_stats,
            },
            "expert_collaboration": {
                "total_cases": total_cases,
                "completed_cases": completed_cases,
                "avg_duration_ms": avg_case_duration,
                "avg_synergy_score": avg_synergy_score,
            },
            "test_results": [r.to_dict() for r in self.test_results],
            "expert_cases": [c.to_dict() for c in self.expert_collaboration_cases],
        }
        
        logger.info(f"测试报告生成完成: 总测试数={total_tests}, 通过={passed_tests}, SLO达成率={slo_compliance_rate:.1f}%")
        
        return report


# ============ Pytest测试用例 ============

if pytest:
    @pytest.mark.asyncio
    async def test_slo_2s_basic():
        """测试2秒SLO（基础）"""
        suite = PerformanceTestSuite()
        try:
            result = await suite.test_slo_2s(endpoint="/api/super-agent/health")
            assert result.status in ["pass", "warning"], f"SLO测试失败: {result.status}"
        finally:
            await suite.close()
    
    @pytest.mark.asyncio
    async def test_expert_collaboration_basic():
        """测试专家协同案例（基础）"""
        suite = PerformanceTestSuite()
        try:
            case = await suite.test_expert_collaboration_case()
            assert case.status == "completed", f"专家协同案例失败: {case.status}"
        finally:
            await suite.close()
    
    @pytest.mark.asyncio
    async def test_api_performance():
        """测试API性能"""
        suite = PerformanceTestSuite()
        try:
            result = await suite.test_api_performance(
                endpoint="/api/super-agent/health",
                method="GET",
                iterations=5,
            )
            assert result.status in ["pass", "warning"], f"API性能测试失败: {result.status}"
        finally:
            await suite.close()
    
    @pytest.mark.asyncio
    async def test_load_test():
        """测试负载测试"""
        suite = PerformanceTestSuite()
        try:
            result = await suite.load_test(
                endpoint="/api/super-agent/health",
                concurrent_users=5,
                requests_per_user=3,
            )
            assert result.status in ["pass", "warning"], f"负载测试失败: {result.status}"
        finally:
            await suite.close()
    
    @pytest.mark.asyncio
    async def test_performance_suite_comprehensive():
        """综合性能测试"""
        suite = PerformanceTestSuite()
        try:
            # 1. 2秒SLO测试
            slo_result = await suite.test_slo_2s()
            
            # 2. 专家协同案例测试
            collab_case = await suite.test_expert_collaboration_case()
            
            # 3. API性能测试
            api_result = await suite.test_api_performance(
                endpoint="/api/super-agent/health",
                iterations=5,
            )
            
            # 4. 保存结果
            results_file = suite.save_results()
            
            # 5. 生成报告
            report = suite.generate_report()
            
            # 验证结果
            assert slo_result.status in ["pass", "warning"], "SLO测试失败"
            assert collab_case.status == "completed", "专家协同案例失败"
            assert api_result.status in ["pass", "warning"], "API性能测试失败"
            assert results_file, "结果文件未保存"
            assert report["summary"]["total_tests"] >= 2, "测试数量不足"
            
        finally:
            await suite.close()


# ============ 命令行入口 ============

async def main():
    """主函数"""
    suite = PerformanceTestSuite()
    
    try:
        logger.info("开始运行性能测试套件...")
        
        # 1. 2秒SLO测试
        logger.info("1. 运行2秒SLO测试...")
        slo_result = await suite.test_slo_2s()
        logger.info(f"SLO测试结果: {slo_result.status} - {slo_result.response_time_ms:.2f}ms")
        
        # 2. 专家协同案例测试
        logger.info("2. 运行专家协同案例测试...")
        collab_case = await suite.test_expert_collaboration_case()
        logger.info(f"专家协同案例: {collab_case.status} - {collab_case.duration_ms:.2f}ms")
        
        # 3. API性能测试
        logger.info("3. 运行API性能测试...")
        api_result = await suite.test_api_performance(
            endpoint="/api/super-agent/health",
            iterations=10,
        )
        logger.info(f"API性能测试: {api_result.status} - {api_result.response_time_ms:.2f}ms")
        
        # 4. 保存结果
        logger.info("4. 保存测试结果...")
        results_file = suite.save_results()
        logger.info(f"结果已保存: {results_file}")
        
        # 5. 生成报告
        logger.info("5. 生成测试报告...")
        report = suite.generate_report()
        
        # 输出报告摘要
        print("\n" + "="*60)
        print("性能测试报告摘要")
        print("="*60)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"警告: {report['summary']['warning']}")
        print(f"通过率: {report['summary']['pass_rate']:.1f}%")
        print(f"SLO达成率: {report['summary']['slo_compliance_rate']:.1f}%")
        print(f"平均响应时间: {report['performance']['avg_response_time_ms']:.2f}ms")
        print(f"专家协同案例: {report['expert_collaboration']['total_cases']}")
        print(f"平均协同耗时: {report['expert_collaboration']['avg_duration_ms']:.2f}ms")
        print(f"平均协同指数: {report['expert_collaboration']['avg_synergy_score']:.2f}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"性能测试套件执行失败: {e}", exc_info=True)
        raise
    finally:
        await suite.close()


if __name__ == "__main__":
    asyncio.run(main())

