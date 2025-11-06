#!/usr/bin/env python3
"""
AI Stack 性能基准测试
测试各个模块的性能指标
"""
import asyncio
import time
import httpx
from typing import Dict, Any, List
from datetime import datetime
import statistics


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self, base_url: str = "http://localhost"):
        """
        初始化基准测试
        
        Args:
            base_url: 基础URL
        """
        self.base_url = base_url
        self.results = []
    
    async def benchmark_api(
        self,
        name: str,
        url: str,
        method: str = "GET",
        data: Dict[str, Any] = None,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """
        对单个API进行基准测试
        
        Args:
            name: 测试名称
            url: API URL
            method: HTTP方法
            data: 请求数据
            iterations: 迭代次数
        
        Returns:
            测试结果
        """
        print(f"\n🔄 测试 {name} ({iterations}次请求)...")
        
        response_times = []
        success_count = 0
        error_count = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                try:
                    start_time = time.time()
                    
                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        response = await client.post(url, json=data)
                    else:
                        raise ValueError(f"不支持的方法: {method}")
                    
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # 转换为毫秒
                    
                    if response.status_code == 200:
                        success_count += 1
                        response_times.append(response_time)
                    else:
                        error_count += 1
                
                except Exception as e:
                    error_count += 1
                    print(f"  ⚠️  请求 {i+1} 失败: {str(e)}")
                
                # 显示进度
                if (i + 1) % 10 == 0:
                    print(f"  进度: {i+1}/{iterations}")
        
        # 计算统计数据
        if response_times:
            result = {
                "name": name,
                "iterations": iterations,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": (success_count / iterations) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)],
                "throughput": success_count / (sum(response_times) / 1000)  # 请求/秒
            }
        else:
            result = {
                "name": name,
                "iterations": iterations,
                "success_count": 0,
                "error_count": error_count,
                "success_rate": 0,
                "error": "所有请求都失败了"
            }
        
        self.results.append(result)
        return result
    
    async def run_all_benchmarks(self):
        """运行所有基准测试"""
        print("=" * 60)
        print("🚀 AI Stack 性能基准测试")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"基础URL: {self.base_url}")
        print()
        
        # 定义测试用例
        test_cases = [
            {
                "name": "AI交互中心 - 健康检查",
                "url": f"{self.base_url}:8020/health",
                "method": "GET",
                "iterations": 100
            },
            {
                "name": "AI交互中心 - 聊天API",
                "url": f"{self.base_url}:8020/api/chat",
                "method": "POST",
                "data": {"message": "测试消息", "user_id": "benchmark"},
                "iterations": 50
            },
            {
                "name": "RAG系统 - 健康检查",
                "url": f"{self.base_url}:8011/health",
                "method": "GET",
                "iterations": 100
            },
            {
                "name": "RAG系统 - 知识检索",
                "url": f"{self.base_url}:8011/api/search",
                "method": "POST",
                "data": {"query": "测试查询", "top_k": 5},
                "iterations": 50
            }
        ]
        
        # 运行测试
        for test_case in test_cases:
            await self.benchmark_api(**test_case)
            await asyncio.sleep(1)  # 避免过载
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 性能基准测试报告")
        print("=" * 60)
        
        for result in self.results:
            print(f"\n【{result['name']}】")
            print("-" * 60)
            
            if "error" in result:
                print(f"❌ 错误: {result['error']}")
                continue
            
            print(f"总请求数: {result['iterations']}")
            print(f"成功: {result['success_count']} | 失败: {result['error_count']}")
            print(f"成功率: {result['success_rate']:.2f}%")
            print()
            print(f"响应时间统计 (ms):")
            print(f"  • 平均: {result['avg_response_time']:.2f}")
            print(f"  • 最小: {result['min_response_time']:.2f}")
            print(f"  • 最大: {result['max_response_time']:.2f}")
            print(f"  • 中位数: {result['median_response_time']:.2f}")
            print(f"  • P95: {result['p95_response_time']:.2f}")
            print(f"  • P99: {result['p99_response_time']:.2f}")
            print()
            print(f"吞吐量: {result['throughput']:.2f} 请求/秒")
        
        # 总体评估
        print("\n" + "=" * 60)
        print("🎯 总体评估")
        print("=" * 60)
        
        avg_success_rate = statistics.mean([r['success_rate'] for r in self.results if 'success_rate' in r])
        avg_response_time = statistics.mean([r['avg_response_time'] for r in self.results if 'avg_response_time' in r])
        
        print(f"平均成功率: {avg_success_rate:.2f}%")
        print(f"平均响应时间: {avg_response_time:.2f}ms")
        
        # 性能评级
        if avg_response_time < 50:
            grade = "优秀 🌟🌟🌟🌟🌟"
        elif avg_response_time < 100:
            grade = "良好 🌟🌟🌟🌟"
        elif avg_response_time < 200:
            grade = "中等 🌟🌟🌟"
        elif avg_response_time < 500:
            grade = "一般 🌟🌟"
        else:
            grade = "需要优化 🌟"
        
        print(f"性能评级: {grade}")
        
        print("\n" + "=" * 60)
        print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())

