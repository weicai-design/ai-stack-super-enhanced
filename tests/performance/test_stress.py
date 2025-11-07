"""
压力测试 - 极限测试
"""

import pytest
import asyncio
import time
import httpx


@pytest.mark.stress
@pytest.mark.slow
class TestStressTests:
    """压力测试"""
    
    @pytest.mark.asyncio
    async def test_max_concurrent_connections(self):
        """测试：最大并发连接数"""
        url = "http://localhost:8011/health"
        max_connections = 1000
        
        async def make_request(client):
            try:
                response = await client.get(url)
                return response.status_code == 200
            except:
                return False
        
        # 创建大量并发请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [make_request(client) for _ in range(max_connections)]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start_time
            
            success_count = sum(1 for r in results if r is True)
            success_rate = success_count / max_connections
            
            print(f"\n最大并发测试: {success_count}/{max_connections} 成功")
            print(f"成功率: {success_rate:.2%}")
            print(f"总耗时: {duration:.2f}s")
            print(f"平均响应: {duration/max_connections:.4f}s")
            
            # 至少70%应该成功
            assert success_rate >= 0.7, f"成功率 {success_rate:.2%} 低于70%"
    
    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self):
        """测试：快速连续请求"""
        url = "http://localhost:8011/health"
        request_count = 100
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # 快速连续发送请求（无延迟）
            tasks = [client.get(url, timeout=10.0) for _ in range(request_count)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            print(f"\n快速请求测试: {success_count}/{request_count} 成功")
            print(f"总耗时: {duration:.2f}s")
            print(f"QPS: {request_count/duration:.2f}")
            
            # 至少80%应该成功
            success_rate = success_count / request_count
            assert success_rate >= 0.8
    
    @pytest.mark.skip(reason="长时间测试，默认跳过")
    @pytest.mark.asyncio
    async def test_endurance_test(self):
        """测试：耐久测试（24小时）"""
        url = "http://localhost:8011/health"
        test_duration = 24 * 3600  # 24小时
        request_interval = 10  # 10秒一次
        
        start_time = time.time()
        error_count = 0
        success_count = 0
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < test_duration:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                except:
                    error_count += 1
                
                await asyncio.sleep(request_interval)
        
        total = success_count + error_count
        success_rate = success_count / total if total > 0 else 0
        
        print(f"\n耐久测试完成")
        print(f"测试时长: {test_duration/3600}小时")
        print(f"成功: {success_count}, 失败: {error_count}")
        print(f"成功率: {success_rate:.2%}")
        
        # 24小时测试，成功率应该>99%
        assert success_rate >= 0.99

