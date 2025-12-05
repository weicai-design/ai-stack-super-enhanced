"""
压力性能测试
测试系统在高并发、大数据量、长时间运行等极端条件下的表现
"""

import unittest
import asyncio
import time
import threading
import concurrent.futures
import random
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import psutil
import os

from ..core.enhanced_circuit_breaker_manager import enhanced_integration_manager
from ..core.performance_optimizer import performance_optimizer
from ..core.data_persistence_backup import create_data_manager
from ..config.enhanced_circuit_breaker_config import ServiceCategory


class TestConcurrentLoadStress(unittest.TestCase):
    """并发负载压力测试"""
    
    def setUp(self):
        """测试准备"""
        # 注册压力测试服务
        enhanced_integration_manager.register_service(
            "stress_test_service", ServiceCategory.API_SERVICE
        )
    
    def test_high_concurrent_requests(self):
        """测试高并发请求处理"""
        results = []
        errors = []
        execution_times = []
        lock = threading.Lock()
        
        def stress_operation(request_id):
            """单个压力操作"""
            start_time = time.time()
            
            @enhanced_integration_manager.enhanced_service_protection("stress_test_service")
            @performance_optimizer.performance_monitor
            def perform_operation():
                # 模拟业务操作，包含随机延迟
                processing_time = random.uniform(0.001, 0.05)
                time.sleep(processing_time)
                
                # 模拟偶尔失败
                if random.random() < 0.05:  # 5%失败率
                    raise Exception("Random operation failure")
                
                return {
                    "request_id": request_id,
                    "processed": True,
                    "processing_time": processing_time
                }
            
            try:
                result = perform_operation()
                end_time = time.time()
                
                with lock:
                    results.append(result)
                    execution_times.append(end_time - start_time)
                
                return result
            except Exception as e:
                with lock:
                    errors.append({"request_id": request_id, "error": str(e)})
                return None
        
        # 执行高并发测试
        num_requests = 1000
        max_workers = 50
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(num_requests)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 性能指标计算
        successful_requests = len(results)
        failed_requests = len(errors)
        throughput = num_requests / total_time
        avg_response_time = statistics.mean(execution_times) if execution_times else 0
        p95_response_time = statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else 0
        
        # 输出性能报告
        print(f"\n=== 高并发压力测试结果 ===")
        print(f"总请求数: {num_requests}")
        print(f"成功请求: {successful_requests}")
        print(f"失败请求: {failed_requests}")
        print(f"成功率: {(successful_requests/num_requests)*100:.2f}%")
        print(f"总执行时间: {total_time:.2f}秒")
        print(f"吞吐量: {throughput:.2f} 请求/秒")
        print(f"平均响应时间: {avg_response_time*1000:.2f}毫秒")
        print(f"P95响应时间: {p95_response_time*1000:.2f}毫秒")
        
        # 性能断言
        self.assertGreater(successful_requests, num_requests * 0.9)  # 成功率大于90%
        self.assertLess(avg_response_time, 0.1)  # 平均响应时间小于100ms
        self.assertGreater(throughput, 100)  # 吞吐量大于100请求/秒
    
    def test_memory_usage_under_load(self):
        """测试负载下的内存使用"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_operation():
            """内存密集型操作"""
            # 创建大对象
            large_data = [{"id": i, "data": "x" * 1000} for i in range(1000)]
            
            @enhanced_integration_manager.enhanced_service_protection("stress_test_service")
            def process_large_data():
                # 模拟数据处理
                processed = []
                for item in large_data:
                    processed_item = {
                        "processed_id": item["id"],
                        "data_length": len(item["data"]),
                        "timestamp": time.time()
                    }
                    processed.append(processed_item)
                return processed
            
            return process_large_data()
        
        # 执行多次内存密集型操作
        results = []
        for i in range(100):
            result = memory_intensive_operation()
            results.append(result)
            
            # 强制垃圾回收
            if i % 20 == 0:
                import gc
                gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n=== 内存使用测试结果 ===")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 内存使用断言
        self.assertLess(memory_increase, 50)  # 内存增长小于50MB
    
    def test_cpu_usage_under_load(self):
        """测试负载下的CPU使用"""
        def cpu_intensive_operation():
            """CPU密集型操作"""
            @enhanced_integration_manager.enhanced_service_protection("stress_test_service")
            def perform_calculation():
                # 模拟复杂计算
                result = 0
                for i in range(10000):
                    result += i * i
                return result
            
            return perform_calculation()
        
        # 监控CPU使用率
        cpu_percentages = []
        
        def monitor_cpu():
            while monitoring:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_percentages.append(cpu_percent)
                time.sleep(0.1)
        
        # 启动CPU监控
        monitoring = True
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # 执行CPU密集型操作
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(cpu_intensive_operation) for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # 停止监控
        monitoring = False
        monitor_thread.join()
        
        # 分析CPU使用
        avg_cpu = statistics.mean(cpu_percentages) if cpu_percentages else 0
        max_cpu = max(cpu_percentages) if cpu_percentages else 0
        
        print(f"\n=== CPU使用测试结果 ===")
        print(f"平均CPU使用率: {avg_cpu:.2f}%")
        print(f"最大CPU使用率: {max_cpu:.2f}%")
        print(f"执行时间: {end_time - start_time:.2f}秒")
        
        # CPU使用断言
        self.assertLess(avg_cpu, 80)  # 平均CPU使用率小于80%


class TestDataVolumeStress(unittest.TestCase):
    """数据量压力测试"""
    
    def setUp(self):
        """测试准备"""
        self.data_manager = create_data_manager("stress_test_data")
        enhanced_integration_manager.register_service(
            "data_volume_service", ServiceCategory.DATABASE_SERVICE
        )
    
    def tearDown(self):
        """测试清理"""
        import shutil
        import os
        if os.path.exists("stress_test_data"):
            shutil.rmtree("stress_test_data")
    
    def test_large_data_processing(self):
        """测试大数据量处理"""
        # 生成大量测试数据
        large_dataset = [
            {
                "id": i,
                "name": f"Item_{i}",
                "value": random.randint(1, 1000),
                "timestamp": datetime.now().isoformat(),
                "metadata": {"category": random.choice(["A", "B", "C"])}
            }
            for i in range(10000)  # 1万条记录
        ]
        
        @enhanced_integration_manager.enhanced_service_protection("data_volume_service")
        @performance_optimizer.performance_monitor
        def process_large_dataset(data):
            """处理大数据集"""
            # 模拟数据处理逻辑
            processed = []
            
            for item in data:
                processed_item = {
                    "processed_id": item["id"],
                    "processed_name": item["name"].upper(),
                    "value_squared": item["value"] ** 2,
                    "processing_time": time.time()
                }
                processed.append(processed_item)
            
            return processed
        
        # 执行大数据处理
        start_time = time.time()
        processed_data = process_large_dataset(large_dataset)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n=== 大数据处理测试结果 ===")
        print(f"数据集大小: {len(large_dataset)} 条记录")
        print(f"处理时间: {processing_time:.2f}秒")
        print(f"处理速度: {len(large_dataset)/processing_time:.2f} 记录/秒")
        
        # 验证处理结果
        self.assertEqual(len(processed_data), len(large_dataset))
        self.assertLess(processing_time, 10)  # 处理时间小于10秒
    
    def test_high_frequency_data_operations(self):
        """测试高频数据操作"""
        operation_count = 0
        lock = threading.Lock()
        
        def high_frequency_operation():
            """高频数据操作"""
            nonlocal operation_count
            
            @enhanced_integration_manager.enhanced_service_protection("data_volume_service")
            def perform_data_operation():
                # 模拟数据操作
                data = {
                    "operation_id": f"op_{int(time.time() * 1000)}",
                    "timestamp": datetime.now().isoformat(),
                    "data": "x" * 100  # 100字节数据
                }
                
                # 保存数据
                filename = f"operation_{data['operation_id']}.json"
                success = self.data_manager.save_data(
                    data, filename, ServiceCategory.USER_DATA
                )
                
                return success
            
            result = perform_data_operation()
            with lock:
                operation_count += 1
            
            return result
        
        # 执行高频操作
        start_time = time.time()
        duration = 10  # 测试10秒
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # 持续执行操作直到时间结束
            futures = []
            while time.time() - start_time < duration:
                future = executor.submit(high_frequency_operation)
                futures.append(future)
                time.sleep(0.001)  # 控制提交频率
            
            # 等待所有操作完成
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        operations_per_second = operation_count / actual_duration
        
        print(f"\n=== 高频数据操作测试结果 ===")
        print(f"操作总数: {operation_count}")
        print(f"测试时长: {actual_duration:.2f}秒")
        print(f"操作频率: {operations_per_second:.2f} 操作/秒")
        
        # 性能断言
        self.assertGreater(operation_count, 1000)  # 至少1000次操作
        self.assertGreater(operations_per_second, 50)  # 至少50操作/秒


class TestLongRunningStress(unittest.TestCase):
    """长时间运行压力测试"""
    
    def test_extended_duration_operations(self):
        """测试长时间运行操作"""
        enhanced_integration_manager.register_service(
            "long_running_service", ServiceCategory.API_SERVICE
        )
        
        operation_count = 0
        error_count = 0
        start_time = time.time()
        test_duration = 30  # 测试30秒
        
        def long_running_operation():
            """长时间运行操作"""
            nonlocal operation_count, error_count
            
            @enhanced_integration_manager.enhanced_service_protection("long_running_service")
            def perform_operation():
                # 模拟长时间运行操作
                operation_time = random.uniform(0.1, 1.0)
                time.sleep(operation_time)
                
                # 模拟偶尔失败
                if random.random() < 0.02:  # 2%失败率
                    raise Exception("Long running operation failed")
                
                return {
                    "operation_time": operation_time,
                    "completed_at": time.time()
                }
            
            try:
                result = perform_operation()
                operation_count += 1
                return result
            except Exception:
                error_count += 1
                return None
        
        # 持续执行操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() - start_time < test_duration:
                future = executor.submit(long_running_operation)
                futures.append(future)
                
                # 控制提交频率
                time.sleep(0.05)
            
            # 等待所有操作完成
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # 计算稳定性指标
        success_rate = operation_count / (operation_count + error_count) if (operation_count + error_count) > 0 else 0
        
        print(f"\n=== 长时间运行测试结果 ===")
        print(f"测试时长: {actual_duration:.2f}秒")
        print(f"成功操作: {operation_count}")
        print(f"失败操作: {error_count}")
        print(f"成功率: {success_rate*100:.2f}%")
        print(f"平均操作频率: {operation_count/actual_duration:.2f} 操作/秒")
        
        # 稳定性断言
        self.assertGreater(operation_count, 50)  # 至少50次成功操作
        self.assertGreater(success_rate, 0.95)  # 成功率大于95%
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 长时间运行的内存操作
        def memory_operation(iteration):
            """可能引起内存泄漏的操作"""
            # 创建对象但不释放
            data_objects = [{"iteration": iteration, "data": "x" * 1000} for _ in range(100)]
            
            # 模拟业务处理
            @enhanced_integration_manager.enhanced_service_protection("long_running_service")
            def process_objects():
                return len(data_objects)
            
            return process_objects()
        
        # 执行多次操作
        for i in range(1000):
            result = memory_operation(i)
            
            # 定期强制垃圾回收
            if i % 100 == 0:
                import gc
                gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"\n=== 内存泄漏检测结果 ===")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 内存泄漏检测
        self.assertLess(memory_increase, 10)  # 内存增长小于10MB


class TestCircuitBreakerStress(unittest.TestCase):
    """熔断器压力测试"""
    
    def test_circuit_breaker_under_high_failure_rate(self):
        """测试高失败率下的熔断器行为"""
        enhanced_integration_manager.register_service(
            "high_failure_service", ServiceCategory.API_SERVICE
        )
        
        failure_count = 0
        success_count = 0
        
        def unreliable_operation():
            """不可靠的操作"""
            nonlocal failure_count, success_count
            
            @enhanced_integration_manager.enhanced_service_protection("high_failure_service")
            def perform_unreliable_operation():
                # 高失败率操作
                if random.random() < 0.7:  # 70%失败率
                    raise Exception("High failure rate operation")
                
                return {"status": "success"}
            
            try:
                result = perform_unreliable_operation()
                success_count += 1
                return result
            except Exception:
                failure_count += 1
                return None
        
        # 执行大量操作
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(unreliable_operation) for _ in range(200)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 分析熔断器效果
        total_operations = success_count + failure_count
        actual_failure_rate = failure_count / total_operations if total_operations > 0 else 0
        
        print(f"\n=== 熔断器压力测试结果 ===")
        print(f"总操作数: {total_operations}")
        print(f"成功操作: {success_count}")
        print(f"失败操作: {failure_count}")
        print(f"实际失败率: {actual_failure_rate*100:.2f}%")
        
        # 验证熔断器保护效果
        # 由于熔断器保护，实际失败率应该低于原始失败率
        self.assertLess(actual_failure_rate, 0.7)
        self.assertGreater(success_count, 0)  # 应该有成功操作
    
    def test_rate_limiter_under_high_load(self):
        """测试高负载下的限流器行为"""
        enhanced_integration_manager.register_service(
            "rate_limited_service", ServiceCategory.API_SERVICE
        )
        
        successful_requests = 0
        rate_limited_requests = 0
        
        def rate_limited_operation():
            """受限流保护的操作"""
            nonlocal successful_requests, rate_limited_requests
            
            @enhanced_integration_manager.enhanced_service_protection("rate_limited_service")
            def perform_operation():
                return {"request_id": int(time.time() * 1000)}
            
            try:
                result = perform_operation()
                successful_requests += 1
                return result
            except Exception as e:
                if "rate limit" in str(e).lower():
                    rate_limited_requests += 1
                return None
        
        # 短时间内发送大量请求
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(rate_limited_operation) for _ in range(500)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        
        total_requests = successful_requests + rate_limited_requests
        request_rate = total_requests / (end_time - start_time)
        
        print(f"\n=== 限流器压力测试结果 ===")
        print(f"总请求数: {total_requests}")
        print(f"成功请求: {successful_requests}")
        print(f"被限流请求: {rate_limited_requests}")
        print(f"请求频率: {request_rate:.2f} 请求/秒")
        
        # 验证限流器效果
        self.assertGreater(rate_limited_requests, 0)  # 应该有被限流的请求
        self.assertLess(request_rate, 100)  # 请求频率应受限制


class TestSystemResourceStress(unittest.TestCase):
    """系统资源压力测试"""
    
    def test_file_io_stress(self):
        """测试文件I/O压力"""
        data_manager = create_data_manager("io_stress_test")
        
        file_count = 0
        total_data_size = 0
        
        def intensive_file_operation(file_id):
            """密集型文件操作"""
            nonlocal file_count, total_data_size
            
            # 创建大量数据
            large_data = {
                "file_id": file_id,
                "content": "x" * 1024,  # 1KB数据
                "timestamp": datetime.now().isoformat(),
                "metadata": {"size": 1024}
            }
            
            # 保存文件
            filename = f"stress_file_{file_id}.json"
            success = data_manager.save_data(
                large_data, filename, ServiceCategory.USER_DATA
            )
            
            if success:
                file_count += 1
                total_data_size += 1024
            
            return success
        
        # 执行大量文件操作
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(intensive_file_operation, i) for i in range(1000)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        io_throughput = file_count / (end_time - start_time)
        data_throughput = total_data_size / (end_time - start_time) / 1024  # KB/s
        
        print(f"\n=== 文件I/O压力测试结果 ===")
        print(f"文件数量: {file_count}")
        print(f"总数据量: {total_data_size/1024:.2f} KB")
        print(f"文件操作吞吐量: {io_throughput:.2f} 文件/秒")
        print(f"数据吞吐量: {data_throughput:.2f} KB/秒")
        
        # 清理测试文件
        import shutil
        shutil.rmtree("io_stress_test")
        
        # I/O性能断言
        self.assertEqual(file_count, 1000)  # 所有文件都应成功创建
        self.assertGreater(io_throughput, 10)  # 至少10文件/秒
    
    def test_network_simulation_stress(self):
        """测试网络模拟压力"""
        enhanced_integration_manager.register_service(
            "network_service", ServiceCategory.API_SERVICE
        )
        
        def network_operation():
            """模拟网络操作"""
            @enhanced_integration_manager.enhanced_service_protection("network_service")
            def simulate_network_call():
                # 模拟网络延迟
                network_delay = random.uniform(0.01, 0.5)
                time.sleep(network_delay)
                
                # 模拟网络错误
                if random.random() < 0.1:  # 10%网络错误率
                    raise Exception("Network error")
                
                return {
                    "response_time": network_delay,
                    "data": "network_response"
                }
            
            return simulate_network_call()
        
        # 执行网络压力测试
        start_time = time.time()
        successful_calls = 0
        failed_calls = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(network_operation) for _ in range(200)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    successful_calls += 1
                except Exception:
                    failed_calls += 1
        
        end_time = time.time()
        
        total_calls = successful_calls + failed_calls
        call_rate = total_calls / (end_time - start_time)
        success_rate = successful_calls / total_calls if total_calls > 0 else 0
        
        print(f"\n=== 网络压力测试结果 ===")
        print(f"总调用数: {total_calls}")
        print(f"成功调用: {successful_calls}")
        print(f"失败调用: {failed_calls}")
        print(f"调用频率: {call_rate:.2f} 调用/秒")
        print(f"成功率: {success_rate*100:.2f}%")
        
        # 网络性能断言
        self.assertGreater(success_rate, 0.8)  # 成功率大于80%
        self.assertGreater(call_rate, 10)  # 至少10调用/秒


if __name__ == "__main__":
    # 运行压力测试
    unittest.main(verbosity=2)