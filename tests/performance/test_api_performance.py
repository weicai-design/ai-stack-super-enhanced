"""
性能测试 - API性能
"""

import pytest
import time
import asyncio
import concurrent.futures
from tests.test_utils import test_helper, PerformanceTestHelper


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.mark.parametrize("endpoint,max_time", [
        ("/health", 0.1),
        ("/api/customers", 0.5),
        ("/rag/search?query=test", 0.5),
    ])
    def test_response_time(self, client, endpoint, max_time, timer):
        """测试：API响应时间"""
        timer.start()
        response = client.get(endpoint)
        timer.stop()
        
        assert response.status_code in [200, 404]
        assert timer.elapsed < max_time, \
            f"{endpoint} 响应时间 {timer.elapsed}s 超过 {max_time}s"
    
    def test_concurrent_requests(self):
        """测试：并发请求性能"""
        import httpx
        
        url = "http://localhost:8011/health"
        concurrent_users = 100
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                return response.status_code == 200
        
        async def run_concurrent_test():
            tasks = [make_request() for _ in range(concurrent_users)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            return success_count, len(results)
        
        # 运行测试
        start_time = time.time()
        success, total = asyncio.run(run_concurrent_test())
        duration = time.time() - start_time
        
        print(f"\n并发测试: {success}/{total} 成功, 耗时: {duration:.2f}s")
        
        # 至少90%的请求应该成功
        success_rate = success / total
        assert success_rate >= 0.9, f"成功率 {success_rate:.2%} 低于90%"
        
        # 平均响应时间应该合理
        avg_time = duration / concurrent_users
        assert avg_time < 0.5, f"平均响应时间 {avg_time:.2f}s 过长"
    
    def test_sustained_load(self):
        """测试：持续负载"""
        import httpx
        
        url = "http://localhost:8011/health"
        duration_seconds = 10
        requests_per_second = 10
        
        async def sustained_load_test():
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                request_count = 0
                error_count = 0
                
                while time.time() - start_time < duration_seconds:
                    try:
                        response = await client.get(url, timeout=5.0)
                        if response.status_code == 200:
                            request_count += 1
                        else:
                            error_count += 1
                    except:
                        error_count += 1
                    
                    # 控制请求速率
                    await asyncio.sleep(1.0 / requests_per_second)
                
                return request_count, error_count
        
        success, errors = asyncio.run(sustained_load_test())
        
        print(f"\n持续负载测试: {success} 成功, {errors} 失败")
        
        # 错误率应该低于5%
        total = success + errors
        error_rate = errors / total if total > 0 else 0
        assert error_rate < 0.05, f"错误率 {error_rate:.2%} 超过5%"
    
    @pytest.mark.parametrize("payload_size", [100, 1000, 10000])
    def test_large_payload_performance(self, client, payload_size):
        """测试：大负载性能"""
        # 创建大负载
        large_text = "测试" * payload_size
        payload = {"text": large_text}
        
        start_time = time.time()
        response = client.post("/rag/ingest/text", json=payload, timeout=30)
        duration = time.time() - start_time
        
        print(f"\n负载大小: {payload_size * 2} 字符, 耗时: {duration:.2f}s")
        
        # 应该在合理时间内完成
        assert duration < 10, f"处理时间 {duration}s 过长"

