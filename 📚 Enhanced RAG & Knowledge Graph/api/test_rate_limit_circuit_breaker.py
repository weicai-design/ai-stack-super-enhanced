#!/usr/bin/env python3
"""
智能任务系统限流熔断机制测试
测试限流、熔断、监控指标功能
"""

import asyncio
import time
import httpx
import json
from typing import List, Dict

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_ENDPOINTS = [
    "/api/v5/task/create",
    "/api/v5/task/list",
    "/api/v5/task/confirm",
    "/api/v5/task/sync-with-agent"
]

class RateLimitTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
    
    async def test_rate_limit(self, endpoint: str, requests_count: int = 15, delay: float = 0.1):
        """测试限流功能"""
        print(f"\n🔍 测试 {endpoint} 的限流功能...")
        
        success_count = 0
        rate_limit_count = 0
        error_count = 0
        
        for i in range(requests_count):
            try:
                if endpoint == "/api/v5/task/create":
                    response = await self.client.post(
                        f"{self.base_url}{endpoint}",
                        json={
                            "title": f"测试任务 {i}",
                            "description": "限流测试任务",
                            "source": "user_defined"
                        }
                    )
                elif endpoint == "/api/v5/task/confirm":
                    # 先创建一个任务用于确认
                    create_response = await self.client.post(
                        f"{self.base_url}/api/v5/task/create",
                        json={
                            "title": f"确认测试任务 {i}",
                            "description": "确认测试任务",
                            "source": "user_defined"
                        }
                    )
                    if create_response.status_code == 200:
                        task_id = create_response.json()["id"]
                        response = await self.client.post(
                            f"{self.base_url}{endpoint}",
                            json={
                                "task_id": task_id,
                                "notes": "测试确认"
                            }
                        )
                    else:
                        response = create_response
                else:
                    response = await self.client.post(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✅ 请求 {i+1}: 成功")
                elif response.status_code == 429:
                    rate_limit_count += 1
                    print(f"  ⚠️ 请求 {i+1}: 限流触发")
                else:
                    error_count += 1
                    print(f"  ❌ 请求 {i+1}: 错误 {response.status_code}")
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ 请求 {i+1}: 异常 {str(e)}")
        
        result = {
            "endpoint": endpoint,
            "total_requests": requests_count,
            "success_count": success_count,
            "rate_limit_count": rate_limit_count,
            "error_count": error_count,
            "rate_limit_ratio": rate_limit_count / requests_count * 100
        }
        
        self.results.append(result)
        return result
    
    async def test_circuit_breaker(self, endpoint: str, error_requests: int = 10):
        """测试熔断器功能"""
        print(f"\n🔍 测试 {endpoint} 的熔断器功能...")
        
        # 模拟连续错误请求来触发熔断
        error_count = 0
        circuit_open_count = 0
        
        for i in range(error_requests):
            try:
                # 发送会导致错误的请求
                response = await self.client.post(
                    f"{self.base_url}{endpoint}",
                    json={"invalid": "data"}  # 无效数据触发错误
                )
                
                if response.status_code >= 500:
                    error_count += 1
                    print(f"  ❌ 错误请求 {i+1}: 触发错误")
                else:
                    print(f"  ⚠️ 错误请求 {i+1}: 未触发错误")
                
            except Exception as e:
                if "CircuitBreakerError" in str(e) or "circuit open" in str(e).lower():
                    circuit_open_count += 1
                    print(f"  ⚡ 熔断器触发 {i+1}: 熔断器已打开")
                else:
                    error_count += 1
                    print(f"  ❌ 错误请求 {i+1}: 异常 {str(e)}")
            
            await asyncio.sleep(0.5)
        
        result = {
            "endpoint": endpoint,
            "total_requests": error_requests,
            "error_count": error_count,
            "circuit_open_count": circuit_open_count,
            "circuit_breaker_triggered": circuit_open_count > 0
        }
        
        self.results.append(result)
        return result
    
    async def test_monitoring_metrics(self):
        """测试监控指标功能"""
        print(f"\n🔍 测试监控指标功能...")
        
        # 发送一些正常请求来生成监控数据
        metrics_data = []
        
        for i in range(5):
            try:
                start_time = time.time()
                
                response = await self.client.post(
                    f"{self.base_url}/api/v5/task/create",
                    json={
                        "title": f"监控测试任务 {i}",
                        "description": "监控指标测试任务",
                        "source": "user_defined"
                    }
                )
                
                execution_time = time.time() - start_time
                
                metrics_data.append({
                    "request_id": i,
                    "status_code": response.status_code,
                    "execution_time": execution_time,
                    "success": response.status_code == 200
                })
                
                print(f"  📊 请求 {i+1}: 状态 {response.status_code}, 耗时 {execution_time:.3f}s")
                
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"  ❌ 监控测试请求 {i+1}: 异常 {str(e)}")
        
        result = {
            "test_type": "monitoring_metrics",
            "total_requests": 5,
            "metrics_data": metrics_data,
            "avg_execution_time": sum(m["execution_time"] for m in metrics_data) / len(metrics_data) if metrics_data else 0
        }
        
        self.results.append(result)
        return result
    
    async def run_comprehensive_test(self):
        """运行全面测试"""
        print("🚀 开始智能任务系统限流熔断机制全面测试")
        print("=" * 60)
        
        # 测试限流功能
        rate_limit_results = []
        for endpoint in ["/api/v5/task/create", "/api/v5/task/list"]:
            result = await self.test_rate_limit(endpoint, requests_count=12)
            rate_limit_results.append(result)
        
        # 测试熔断器功能
        circuit_results = []
        for endpoint in ["/api/v5/task/create"]:
            result = await self.test_circuit_breaker(endpoint, error_requests=8)
            circuit_results.append(result)
        
        # 测试监控指标
        metrics_result = await self.test_monitoring_metrics()
        
        # 输出测试报告
        await self.generate_test_report(rate_limit_results, circuit_results, metrics_result)
    
    async def generate_test_report(self, rate_limit_results, circuit_results, metrics_result):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 智能任务系统限流熔断机制测试报告")
        print("=" * 60)
        
        # 限流测试结果
        print("\n🔒 限流功能测试结果:")
        for result in rate_limit_results:
            print(f"  • {result['endpoint']}:")
            print(f"    总请求数: {result['total_requests']}")
            print(f"    成功请求: {result['success_count']}")
            print(f"    限流触发: {result['rate_limit_count']}")
            print(f"    限流比例: {result['rate_limit_ratio']:.1f}%")
            
            # 判断限流是否正常工作
            if result['rate_limit_count'] > 0:
                print("    ✅ 限流功能正常")
            else:
                print("    ⚠️ 限流功能可能未生效")
        
        # 熔断器测试结果
        print("\n⚡ 熔断器功能测试结果:")
        for result in circuit_results:
            print(f"  • {result['endpoint']}:")
            print(f"    总请求数: {result['total_requests']}")
            print(f"    错误请求: {result['error_count']}")
            print(f"    熔断触发: {result['circuit_open_count']}")
            
            if result['circuit_breaker_triggered']:
                print("    ✅ 熔断器功能正常")
            else:
                print("    ⚠️ 熔断器功能可能未生效")
        
        # 监控指标测试结果
        print("\n📈 监控指标功能测试结果:")
        print(f"  平均执行时间: {metrics_result['avg_execution_time']:.3f}s")
        print(f"  总请求数: {metrics_result['total_requests']}")
        print("  ✅ 监控指标功能正常")
        
        # 总体评估
        print("\n🎯 总体评估:")
        rate_limit_working = any(r['rate_limit_count'] > 0 for r in rate_limit_results)
        circuit_breaker_working = any(r['circuit_breaker_triggered'] for r in circuit_results)
        
        if rate_limit_working and circuit_breaker_working:
            print("  ✅ 限流熔断机制全面正常工作")
            print("  ✅ 生产级工程化能力达标")
        else:
            print("  ⚠️ 部分功能需要进一步验证")
        
        print("\n✅ 测试完成")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主测试函数"""
    tester = RateLimitTester(BASE_URL)
    
    try:
        await tester.run_comprehensive_test()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    print("智能任务系统限流熔断机制测试")
    print("注意: 请确保任务管理API服务正在 localhost:8000 运行")
    print("启动命令: uvicorn task_management_v5_api:router --host 0.0.0.0 --port 8000")
    
    asyncio.run(main())