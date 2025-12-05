"""
订单管理性能测试

测试范围：
1. 高并发订单创建性能
2. 大数据量订单查询性能
3. 批量操作性能
4. 内存使用和响应时间
"""
import pytest
import sys
import os
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database_models import Base, Customer, Order
from modules.order.order_manager import OrderManager


class TestOrderPerformance:
    """订单管理性能测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_performance_test(self):
        """设置性能测试环境"""
        # 创建内存数据库
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        
        SessionLocal = sessionmaker(autocreate=False, autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()
        
        # 创建测试客户
        self.test_customer = Customer(
            name="性能测试客户",
            code="PERF-TEST-001",
            category="VIP",
            contact_person="性能测试员",
            contact_phone="13900139000",
            contact_email="performance@test.com",
            address="性能测试地址"
        )
        self.db_session.add(self.test_customer)
        self.db_session.commit()
        
        self.order_manager = OrderManager(self.db_session)
        
        yield
        
        # 清理
        self.db_session.close()
        Base.metadata.drop_all(self.engine)
    
    def generate_bulk_order_data(self, count):
        """生成批量订单数据"""
        orders = []
        for i in range(count):
            order_data = {
                "customer_id": self.test_customer.id,
                "order_number": f"PERF-ORDER-{i:06d}",
                "order_date": datetime.now() - timedelta(days=i % 30),
                "delivery_date": datetime.now() + timedelta(days=30 - i % 30),
                "order_amount": 10000.0 + (i % 100) * 100,
                "order_type": "短期" if i % 3 == 0 else "长期",
                "status": ["待确认", "已确认", "生产中", "已完成", "已取消"][i % 5],
                "items": [
                    {
                        "name": f"性能测试产品{i:03d}",
                        "quantity": 10 + i % 20,
                        "unit_price": 1000.0 + (i % 50) * 10,
                        "code": f"PERF-PROD-{i:03d}"
                    }
                ]
            }
            orders.append(order_data)
        return orders
    
    def test_concurrent_order_creation(self):
        """测试并发订单创建性能"""
        num_threads = 10
        orders_per_thread = 20
        total_orders = num_threads * orders_per_thread
        
        def create_orders_thread(thread_id):
            """单个线程创建订单"""
            success_count = 0
            for i in range(orders_per_thread):
                order_data = {
                    "customer_id": self.test_customer.id,
                    "order_number": f"CONCURRENT-{thread_id:02d}-{i:03d}",
                    "order_date": datetime.now(),
                    "delivery_date": datetime.now() + timedelta(days=30),
                    "order_amount": 10000.0 + thread_id * 1000 + i * 10,
                    "order_type": "短期",
                    "status": "待确认",
                    "items": []
                }
                
                try:
                    result = self.order_manager.create_order(order_data)
                    if result["success"]:
                        success_count += 1
                except Exception as e:
                    print(f"线程 {thread_id} 创建订单失败: {e}")
            
            return success_count
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_orders_thread, i) for i in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        execution_time = end_time - start_time
        total_success = sum(results)
        
        print(f"并发订单创建测试结果:")
        print(f"线程数: {num_threads}")
        print(f"每线程订单数: {orders_per_thread}")
        print(f"总订单数: {total_orders}")
        print(f"成功订单数: {total_success}")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"吞吐量: {total_success/execution_time:.2f} 订单/秒")
        
        # 性能断言
        assert execution_time < 30.0, f"并发订单创建时间过长: {execution_time:.2f}秒"
        assert total_success >= total_orders * 0.9, f"成功率过低: {total_success}/{total_orders}"
        assert total_success/execution_time > 5.0, f"吞吐量过低: {total_success/execution_time:.2f} 订单/秒"
    
    def test_bulk_order_creation_performance(self):
        """测试批量订单创建性能"""
        order_counts = [100, 500, 1000]
        
        for count in order_counts:
            orders = self.generate_bulk_order_data(count)
            
            start_time = time.time()
            success_count = 0
            
            for order_data in orders:
                try:
                    result = self.order_manager.create_order(order_data)
                    if result["success"]:
                        success_count += 1
                except Exception as e:
                    print(f"创建订单失败: {e}")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"批量订单创建测试 (数量: {count}):")
            print(f"成功订单数: {success_count}")
            print(f"执行时间: {execution_time:.2f} 秒")
            print(f"平均时间: {execution_time/count:.4f} 秒/订单")
            
            # 性能断言
            assert success_count >= count * 0.95, f"批量创建成功率过低: {success_count}/{count}"
            assert execution_time/count < 0.1, f"单订单处理时间过长: {execution_time/count:.4f}秒"
    
    def test_large_dataset_query_performance(self):
        """测试大数据集查询性能"""
        # 先创建大量测试数据
        bulk_orders = self.generate_bulk_order_data(1000)
        for order_data in bulk_orders:
            self.order_manager.create_order(order_data)
        
        # 测试不同查询条件的性能
        query_tests = [
            ("无筛选条件", {}),
            ("按状态筛选", {"status": "待确认"}),
            ("按客户筛选", {"customer_id": self.test_customer.id}),
            ("分页查询", {"page": 1, "page_size": 50}),
            ("复杂查询", {"status": "待确认", "customer_id": self.test_customer.id, "page": 1, "page_size": 20})
        ]
        
        for test_name, query_params in query_tests:
            start_time = time.time()
            
            result = self.order_manager.list_orders(**query_params)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"查询性能测试 - {test_name}:")
            print(f"执行时间: {execution_time:.4f} 秒")
            print(f"返回订单数: {len(result.get('orders', []))}")
            
            # 性能断言
            assert execution_time < 1.0, f"查询时间过长: {execution_time:.4f}秒"
            assert result["success"] == True, f"查询失败: {result.get('error', '')}"
    
    def test_order_status_update_performance(self):
        """测试订单状态更新性能"""
        # 创建测试订单
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "PERF-UPDATE-TEST",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        create_result = self.order_manager.create_order(order_data)
        order_id = create_result["order_id"]
        
        # 测试批量状态更新性能
        status_updates = 100
        start_time = time.time()
        
        for i in range(status_updates):
            new_status = ["待确认", "已确认", "生产中", "已完成"][i % 4]
            result = self.order_manager.update_order_status(
                order_id=order_id,
                new_status=new_status,
                note=f"性能测试更新 {i}"
            )
            assert result["success"] == True, f"状态更新失败: {result.get('error', '')}"
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"订单状态更新性能测试:")
        print(f"更新次数: {status_updates}")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"平均时间: {execution_time/status_updates:.4f} 秒/次")
        
        # 性能断言
        assert execution_time/status_updates < 0.05, f"单次状态更新时间过长: {execution_time/status_updates:.4f}秒"
    
    def test_memory_usage_under_load(self):
        """测试负载下的内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行批量操作
        orders = self.generate_bulk_order_data(500)
        
        for order_data in orders:
            self.order_manager.create_order(order_data)
        
        # 执行复杂查询
        for _ in range(100):
            self.order_manager.list_orders(status="待确认", customer_id=self.test_customer.id)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"内存使用测试:")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 内存使用断言
        assert memory_increase < 100.0, f"内存增长过多: {memory_increase:.2f} MB"
    
    def test_error_handling_performance(self):
        """测试错误处理性能"""
        # 测试大量无效输入的处理性能
        invalid_inputs = [
            {"customer_id": -999},  # 无效客户ID
            {"order_number": "A" * 100},  # 超长订单号
            {"order_amount": "not_a_number"},  # 非数字金额
            {"status": "invalid_status"},  # 无效状态
        ]
        
        start_time = time.time()
        
        for invalid_input in invalid_inputs * 25:  # 重复100次
            try:
                # 使用有效的基础数据，只修改无效字段
                base_data = {
                    "customer_id": self.test_customer.id,
                    "order_number": "PERF-ERROR-TEST",
                    "order_date": datetime.now(),
                    "delivery_date": datetime.now() + timedelta(days=30),
                    "order_amount": 10000.0,
                    "order_type": "短期",
                    "status": "待确认",
                    "items": []
                }
                base_data.update(invalid_input)
                
                result = self.order_manager.create_order(base_data)
                # 预期会失败，但应该快速返回错误
                assert result["success"] == False
            except Exception:
                # 允许异常，但应该快速失败
                pass
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"错误处理性能测试:")
        print(f"无效输入次数: 100")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"平均时间: {execution_time/100:.4f} 秒/次")
        
        # 性能断言
        assert execution_time/100 < 0.01, f"错误处理时间过长: {execution_time/100:.4f}秒"


class TestOrderScalability:
    """订单管理可扩展性测试类"""
    
    def test_database_connection_scaling(self):
        """测试数据库连接扩展性"""
        # 模拟多个并发数据库连接
        num_connections = 20
        
        def simulate_database_operation(conn_id):
            """模拟数据库操作"""
            engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            Base.metadata.create_all(engine)
            
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            
            # 执行一些数据库操作
            customer = Customer(
                name=f"Scalability Test Customer {conn_id}",
                code=f"SCALE-{conn_id:03d}",
                category="Test"
            )
            session.add(customer)
            session.commit()
            
            session.close()
            return True
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [executor.submit(simulate_database_operation, i) for i in range(num_connections)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"数据库连接扩展性测试:")
        print(f"并发连接数: {num_connections}")
        print(f"执行时间: {execution_time:.2f} 秒")
        
        assert all(results), "部分数据库操作失败"
        assert execution_time < 10.0, f"数据库连接扩展性差: {execution_time:.2f}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])