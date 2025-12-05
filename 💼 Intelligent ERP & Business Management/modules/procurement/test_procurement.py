"""
采购管理模块测试套件
包含单元测试、集成测试和性能测试
"""

import unittest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from procurement_manager import ProcurementManager, RateLimiter, CircuitBreaker


class TestRateLimiter(unittest.TestCase):
    """限流器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.rate_limiter = RateLimiter(rate=10, capacity=20)
    
    def test_acquire_success(self):
        """测试成功获取令牌"""
        result = self.rate_limiter.acquire()
        self.assertTrue(result)
    
    def test_acquire_rate_limit(self):
        """测试限流"""
        # 快速请求超过限制
        for _ in range(25):
            self.rate_limiter.acquire()
        
        # 应该被限流
        result = self.rate_limiter.acquire()
        self.assertFalse(result)
    
    def test_refill_tokens(self):
        """测试令牌补充"""
        # 消耗所有令牌
        for _ in range(20):
            self.rate_limiter.acquire()
        
        # 等待补充
        time.sleep(0.2)
        
        # 应该可以获取新令牌
        result = self.rate_limiter.acquire()
        self.assertTrue(result)


class TestCircuitBreaker(unittest.TestCase):
    """熔断器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1,
            half_open_max_requests=2
        )
    
    def test_circuit_closed_state(self):
        """测试熔断器关闭状态"""
        self.assertEqual(self.circuit_breaker.state, "CLOSED")
        self.assertTrue(self.circuit_breaker.allow_request())
    
    def test_circuit_open_state(self):
        """测试熔断器打开状态"""
        # 模拟多次失败
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        self.assertEqual(self.circuit_breaker.state, "OPEN")
        self.assertFalse(self.circuit_breaker.allow_request())
    
    def test_circuit_half_open_state(self):
        """测试熔断器半开状态"""
        # 先打开熔断器
        for _ in range(3):
            self.circuit_breaker.record_failure()
        
        # 等待恢复超时
        time.sleep(1.1)
        
        # 调用allow_request来触发状态转换
        can_request = self.circuit_breaker.allow_request()
        
        # 应该进入半开状态
        self.assertEqual(self.circuit_breaker.state, "HALF_OPEN")
        self.assertTrue(can_request)


class TestProcurementManager(unittest.TestCase):
    """采购管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = ProcurementManager()
    
    def test_create_purchase_request_success(self):
        """测试创建采购请求成功"""
        request_data = {
            "item_name": "测试商品",
            "quantity": 10,
            "unit_price": 100.0,
            "supplier": "测试供应商",
            "requested_by": "测试用户"
        }
        
        result = self.manager.create_purchase_request(request_data)
        
        self.assertIn("request_id", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "采购请求创建成功")
    
    def test_create_purchase_request_validation(self):
        """测试采购请求验证"""
        # 测试缺少必要字段
        invalid_data = {
            "item_name": "测试商品"
            # 缺少其他必要字段
        }
        
        result = self.manager.create_purchase_request(invalid_data)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("验证失败", result["message"])
    
    def test_rate_limiting(self):
        """测试限流功能"""
        # 创建新的管理器，使用更严格的限流配置
        strict_manager = ProcurementManager()
        strict_manager.rate_limiter = RateLimiter(capacity=5, rate=1)  # 5容量，1个/秒
        
        request_data = {
            "item_name": "测试商品",
            "quantity": 1,
            "unit_price": 10.0,
            "supplier": "测试供应商",
            "requested_by": "测试用户"
        }
        
        # 前5个请求应该成功
        for i in range(5):
            result = strict_manager.create_purchase_request(request_data)
            self.assertEqual(result["status"], "success")
        
        # 第6个请求应该被限流
        result = strict_manager.create_purchase_request(request_data)
        self.assertEqual(result["status"], "error")
        self.assertIn("请求频率过高", result["message"])


class TestIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = ProcurementManager()
    
    def test_end_to_end_procurement_flow(self):
        """测试端到端采购流程"""
        # 1. 创建采购请求
        request_data = {
            "item_name": "办公用品",
            "quantity": 50,
            "unit_price": 15.0,
            "supplier": "办公用品供应商",
            "requested_by": "采购部门"
        }
        
        create_result = self.manager.create_purchase_request(request_data)
        self.assertEqual(create_result["status"], "success")
        request_id = create_result["request_id"]
        
        # 2. 验证请求信息
        self.assertIsNotNone(request_id)
        self.assertGreater(len(request_id), 0)
        
        # 3. 测试缓存功能
        # 再次创建相同请求应该使用缓存
        cached_result = self.manager.create_purchase_request(request_data)
        self.assertEqual(cached_result["status"], "success")
        
        # 4. 验证审计日志
        # 这里可以添加审计日志验证逻辑


class TestPerformance(unittest.TestCase):
    """性能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = ProcurementManager()
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        request_data = {
            "item_name": "性能测试商品",
            "quantity": 1,
            "unit_price": 1.0,
            "supplier": "测试供应商",
            "requested_by": "性能测试"
        }
        
        results = []
        
        def create_request():
            result = self.manager.create_purchase_request(request_data)
            results.append(result)
        
        # 创建多个线程并发请求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        self.assertEqual(len(results), 5)
        success_count = sum(1 for r in results if r["status"] == "success")
        self.assertGreaterEqual(success_count, 3)  # 至少3个成功
    
    def test_response_time(self):
        """测试响应时间"""
        request_data = {
            "item_name": "响应时间测试",
            "quantity": 1,
            "unit_price": 1.0,
            "supplier": "测试供应商",
            "requested_by": "响应测试"
        }
        
        start_time = time.time()
        result = self.manager.create_purchase_request(request_data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # 响应时间应该小于1秒
        self.assertLess(response_time, 1.0)
        self.assertEqual(result["status"], "success")


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)