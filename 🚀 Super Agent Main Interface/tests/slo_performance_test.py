#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证测试脚本（T003）

验证所有API端点的响应时间是否满足2秒SLO要求
"""

import asyncio
import time
import httpx
import statistics
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PerformanceResult:
    """性能测试结果"""
    endpoint: str
    response_time: float
    status_code: int
    success: bool
    error: str = ""


class SLOPerformanceTester:
    """2秒SLO性能验证器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url
        self.slo_threshold = 2.0  # 2秒SLO阈值
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # 定义要测试的API端点
        self.endpoints = [
            "/docs",  # API文档
            "/api/experts/",  # 专家列表
            "/api/experts/count",  # 专家统计
            "/api/metrics/health",  # 健康检查
            "/api/metrics/performance",  # 性能指标
            "/api/metrics/analysis/summary",  # 分析摘要
            "/api/metrics/experts/ranking",  # 专家排名
            "/api/metrics/comparison?experts=rag_knowledge_expert,erp_quality_expert",  # 专家对比
        ]
    
    async def test_endpoint(self, endpoint: str) -> PerformanceResult:
        """测试单个端点性能"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = await self.client.get(url)
            response_time = time.time() - start_time
            
            return PerformanceResult(
                endpoint=endpoint,
                response_time=response_time,
                status_code=response.status_code,
                success=response.status_code == 200 and response_time <= self.slo_threshold
            )
        except Exception as e:
            response_time = time.time() - start_time
            return PerformanceResult(
                endpoint=endpoint,
                response_time=response_time,
                status_code=0,
                success=False,
                error=str(e)
            )
    
    async def run_concurrent_tests(self, concurrent_requests: int = 10) -> List[PerformanceResult]:
        """运行并发性能测试"""
        print(f"🚀 开始并发性能测试 ({concurrent_requests}个并发请求)...")
        
        # 为每个端点创建并发请求
        tasks = []
        for endpoint in self.endpoints:
            for i in range(concurrent_requests):
                tasks.append(self.test_endpoint(endpoint))
        
        # 并发执行所有测试
        results = await asyncio.gather(*tasks)
        
        print(f"✅ 并发测试完成，共测试 {len(results)} 个请求")
        return results
    
    async def run_sequential_tests(self) -> List[PerformanceResult]:
        """运行顺序性能测试"""
        print("🚀 开始顺序性能测试...")
        
        results = []
        for endpoint in self.endpoints:
            result = await self.test_endpoint(endpoint)
            results.append(result)
            
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} {endpoint}: {result.response_time:.3f}s (状态码: {result.status_code})")
        
        print("✅ 顺序测试完成")
        return results
    
    def analyze_results(self, results: List[PerformanceResult]) -> Dict[str, any]:
        """分析性能测试结果"""
        # 按端点分组结果
        endpoint_results: Dict[str, List[float]] = {}
        for result in results:
            if result.endpoint not in endpoint_results:
                endpoint_results[result.endpoint] = []
            endpoint_results[result.endpoint].append(result.response_time)
        
        # 计算统计指标
        analysis = {
            "total_requests": len(results),
            "successful_requests": sum(1 for r in results if r.success),
            "failed_requests": sum(1 for r in results if not r.success),
            "slo_compliance_rate": 0.0,
            "average_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
            "endpoint_analysis": {},
            "slo_violations": []
        }
        
        # 计算总体指标
        if results:
            response_times = [r.response_time for r in results]
            analysis["average_response_time"] = statistics.mean(response_times)
            analysis["slo_compliance_rate"] = sum(1 for r in results if r.success) / len(results)
            
            # 计算百分位数
            sorted_times = sorted(response_times)
            analysis["p95_response_time"] = sorted_times[int(len(sorted_times) * 0.95)]
            analysis["p99_response_time"] = sorted_times[int(len(sorted_times) * 0.99)]
        
        # 分析每个端点
        for endpoint, times in endpoint_results.items():
            if times:
                avg_time = statistics.mean(times)
                p95_time = sorted(times)[int(len(times) * 0.95)]
                success_rate = sum(1 for r in results if r.endpoint == endpoint and r.success) / len(times)
                
                analysis["endpoint_analysis"][endpoint] = {
                    "average_time": avg_time,
                    "p95_time": p95_time,
                    "success_rate": success_rate,
                    "request_count": len(times),
                    "slo_compliant": avg_time <= self.slo_threshold
                }
                
                if avg_time > self.slo_threshold:
                    analysis["slo_violations"].append({
                        "endpoint": endpoint,
                        "average_time": avg_time,
                        "threshold": self.slo_threshold
                    })
        
        return analysis
    
    def print_report(self, analysis: Dict[str, any]):
        """打印性能测试报告"""
        print("\n" + "="*80)
        print("📊 2秒SLO性能验证报告")
        print("="*80)
        
        print(f"\n📈 总体性能指标:")
        print(f"   • 总请求数: {analysis['total_requests']}")
        print(f"   • 成功请求数: {analysis['successful_requests']}")
        print(f"   • SLO合规率: {analysis['slo_compliance_rate']:.1%}")
        print(f"   • 平均响应时间: {analysis['average_response_time']:.3f}s")
        print(f"   • P95响应时间: {analysis['p95_response_time']:.3f}s")
        print(f"   • P99响应时间: {analysis['p99_response_time']:.3f}s")
        
        print(f"\n🔍 端点性能分析:")
        for endpoint, metrics in analysis["endpoint_analysis"].items():
            status_icon = "✅" if metrics["slo_compliant"] else "❌"
            print(f"   {status_icon} {endpoint}")
            print(f"     平均时间: {metrics['average_time']:.3f}s, P95: {metrics['p95_time']:.3f}s")
            print(f"     成功率: {metrics['success_rate']:.1%}, 请求数: {metrics['request_count']}")
        
        if analysis["slo_violations"]:
            print(f"\n⚠️  SLO违规端点:")
            for violation in analysis["slo_violations"]:
                print(f"   ❌ {violation['endpoint']}: {violation['average_time']:.3f}s > {violation['threshold']}s")
        
        # 总体评估
        print(f"\n🎯 SLO合规评估:")
        if analysis["slo_compliance_rate"] >= 0.95:
            print("   ✅ 优秀 - 系统满足2秒SLO要求 (合规率 ≥ 95%)")
        elif analysis["slo_compliance_rate"] >= 0.90:
            print("   ⚠️  良好 - 系统基本满足SLO要求 (合规率 ≥ 90%)")
        else:
            print("   ❌ 需要改进 - 系统未满足SLO要求 (合规率 < 90%)")
        
        print("="*80)
    
    async def run_comprehensive_test(self):
        """运行全面的性能测试"""
        print("🚀 开始2秒SLO性能验证测试...")
        print(f"📊 测试目标: 验证所有API端点是否满足2秒响应时间要求")
        print(f"🔗 测试地址: {self.base_url}")
        
        try:
            # 1. 运行顺序测试
            sequential_results = await self.run_sequential_tests()
            
            # 2. 运行并发测试
            concurrent_results = await self.run_concurrent_tests(concurrent_requests=5)
            
            # 3. 合并结果并分析
            all_results = sequential_results + concurrent_results
            analysis = self.analyze_results(all_results)
            
            # 4. 生成报告
            self.print_report(analysis)
            
            # 5. 返回测试结果
            return {
                "success": analysis["slo_compliance_rate"] >= 0.90,
                "analysis": analysis,
                "slo_compliant": analysis["slo_compliance_rate"] >= 0.90
            }
            
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "slo_compliant": False
            }
        finally:
            await self.client.aclose()


async def main():
    """主函数"""
    tester = SLOPerformanceTester()
    
    # 等待服务器启动
    print("⏳ 等待API服务器启动...")
    await asyncio.sleep(5)
    
    # 运行性能测试
    result = await tester.run_comprehensive_test()
    
    # 返回退出码
    exit_code = 0 if result["slo_compliant"] else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)