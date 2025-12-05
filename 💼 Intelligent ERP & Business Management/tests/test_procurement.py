"""
采购管理模块测试套件
包含单元测试、集成测试、性能测试
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加模块路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.procurement.procurement_manager import ProcurementManager, RateLimiter, CircuitBreaker
from modules.procurement.procurement_models import Supplier, PurchaseOrder, PurchaseOrderItem


class TestRateLimiter:
    """限流器测试"""
    
    def test_rate_limiter_acquire(self):
        """测试令牌获取"""
        limiter = RateLimiter(capacity=10, rate=1)
        
        # 前10次应该成功
        for i in range(10):
            assert limiter.acquire() == True
        
        # 第11次应该失败
        assert limiter.acquire() == False
    
    def test_rate_limiter_refill(self):
        """测试令牌补充"""
        limiter = RateLimiter(capacity=5, rate=2)  # 5容量，2个/秒
        
        # 消耗所有令牌
        for i in range(5):
            assert limiter.acquire() == True
        
        # 等待0.6秒，应该补充1.2个令牌
        import time
        time.sleep(0.6)
        
        # 应该能获取1个令牌
        assert limiter.acquire() == True
        
        # 再获取应该失败
        assert limiter.acquire() == False


class TestCircuitBreaker:
    """熔断器测试"""
    
    def test_circuit_breaker_states(self):
        """测试熔断器状态转换"""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1)
        
        # 初始状态应该是CLOSED
        assert breaker.state == "CLOSED"
        assert breaker.can_execute() == True
        
        # 记录3次失败，应该触发熔断
        for i in range(3):
            breaker.record_failure()
        
        assert breaker.state == "OPEN"
        assert breaker.can_execute() == False
        
        # 等待超时，应该进入HALF_OPEN
        import time
        time.sleep(1.1)
        assert breaker.can_execute() == True
        assert breaker.state == "HALF_OPEN"
        
        # 记录成功，应该恢复为CLOSED
        breaker.record_success()
        assert breaker.state == "CLOSED"
        assert breaker.can_execute() == True


class TestProcurementManager:
    """采购管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建采购管理器实例"""
        return ProcurementManager()
    
    def test_create_purchase_request(self, manager):
        """测试创建采购申请"""
        request = manager.create_purchase_request(
            requester="张三",
            items=[{"name": "原材料A", "quantity": 100, "unit_price": 10.5}],
            reason="生产需求",
            required_date="2025-12-01",
            priority="high"
        )
        
        assert request["success"] == True
        assert "request_id" in request
        assert request["request"]["requester"] == "张三"
        assert request["request"]["status"] == "pending"
    
    def test_approve_purchase_request(self, manager):
        """测试审批采购申请"""
        # 先创建申请
        request_result = manager.create_purchase_request(
            requester="李四",
            items=[{"name": "原材料B", "quantity": 50, "unit_price": 8.0}],
            reason="测试审批",
            required_date="2025-12-02",
            priority="medium"
        )
        
        request_id = request_result["request_id"]
        
        # 审批申请
        approval_result = manager.approve_purchase_request(
            request_id=request_id,
            approver="王经理",
            approval_notes="同意采购"
        )
        
        assert approval_result["success"] == True
        assert approval_result["request"]["status"] == "approved"
        assert approval_result["request"]["approved_by"] == "王经理"
    
    def test_create_procurement_order(self, manager):
        """测试创建采购订单"""
        # 先创建并审批申请
        request_result = manager.create_purchase_request(
            requester="赵工",
            items=[{"name": "电子元件", "quantity": 200, "unit_price": 5.0}],
            reason="项目需求",
            required_date="2025-12-03",
            priority="high"
        )
        
        request_id = request_result["request_id"]
        
        manager.approve_purchase_request(
            request_id=request_id,
            approver="张总监",
            approval_notes="紧急采购"
        )
        
        # 创建采购订单
        order_result = manager.create_procurement_order(
            request_id=request_id,
            supplier_id=1,
            expected_delivery_date="2025-12-10"
        )
        
        assert order_result["success"] == True
        assert "order_id" in order_result
        assert order_result["order"]["status"] == "confirmed"
    
    def test_add_supplier(self, manager):
        """测试添加供应商"""
        supplier_result = manager.add_supplier(
            name="优质供应商有限公司",
            category="电子元器件",
            contact_person="陈经理",
            phone="13800138000",
            email="chen@supplier.com",
            address="深圳市南山区科技园"
        )
        
        assert supplier_result["success"] == True
        assert "supplier_id" in supplier_result
        assert supplier_result["supplier"]["name"] == "优质供应商有限公司"
    
    def test_get_supplier_performance(self, manager):
        """测试获取供应商绩效"""
        # 先添加供应商
        supplier_result = manager.add_supplier(
            name="测试供应商",
            category="测试",
            contact_person="测试",
            phone="1234567890"
        )
        
        supplier_id = supplier_result["supplier_id"]
        
        # 获取绩效
        performance = manager.get_supplier_performance(supplier_id)
        
        assert performance["success"] == True
        assert "performance" in performance
        assert "on_time_delivery_rate" in performance["performance"]
    
    def test_procurement_analysis(self, manager):
        """测试采购分析"""
        analysis = manager.get_procurement_analysis()
        
        assert analysis["success"] == True
        assert "analysis" in analysis
        assert "total_orders" in analysis["analysis"]
        assert "total_amount" in analysis["analysis"]


class TestProcurementIntegration:
    """采购管理集成测试"""
    
    def test_end_to_end_procurement_flow(self):
        """测试端到端采购流程"""
        manager = ProcurementManager()
        
        # 1. 创建采购申请
        request_result = manager.create_purchase_request(
            requester="集成测试",
            items=[{"name": "集成测试物料", "quantity": 100, "unit_price": 15.0}],
            reason="集成测试",
            required_date="2025-12-05",
            priority="high"
        )
        
        assert request_result["success"] == True
        request_id = request_result["request_id"]
        
        # 2. 审批采购申请
        approval_result = manager.approve_purchase_request(
            request_id=request_id,
            approver="集成测试审批人",
            approval_notes="集成测试审批"
        )
        
        assert approval_result["success"] == True
        
        # 3. 添加供应商
        supplier_result = manager.add_supplier(
            name="集成测试供应商",
            category="集成测试",
            contact_person="集成测试联系人",
            phone="13800138000"
        )
        
        assert supplier_result["success"] == True
        supplier_id = supplier_result["supplier_id"]
        
        # 4. 创建采购订单
        order_result = manager.create_procurement_order(
            request_id=request_id,
            supplier_id=supplier_id,
            expected_delivery_date="2025-12-15"
        )
        
        assert order_result["success"] == True
        order_id = order_result["order_id"]
        
        # 5. 发送订单给供应商
        send_result = manager.send_order_to_supplier(order_id)
        
        assert send_result["success"] == True
        
        # 6. 记录收货
        receipt_result = manager.record_goods_receipt(
            order_id=order_id,
            received_quantity=100,
            quality_status="合格",
            received_by="仓库管理员"
        )
        
        assert receipt_result["success"] == True
        
        # 7. 检查最终状态
        orders = manager.get_procurement_orders()
        assert orders["success"] == True
        
        # 查找刚创建的订单
        target_order = None
        for order in orders["orders"]:
            if order["order_id"] == order_id:
                target_order = order
                break
        
        assert target_order is not None
        assert target_order["status"] == "completed"


class TestProcurementPerformance:
    """采购管理性能测试"""
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import threading
        import time
        
        manager = ProcurementManager()
        results = []
        
        def create_request(thread_id):
            """创建采购申请的线程函数"""
            try:
                result = manager.create_purchase_request(
                    requester=f"线程{thread_id}",
                    items=[{"name": f"物料{thread_id}", "quantity": 10, "unit_price": 5.0}],
                    reason=f"性能测试{thread_id}",
                    required_date="2025-12-01",
                    priority="medium"
                )
                results.append((thread_id, result["success"]))
            except Exception as e:
                results.append((thread_id, False))
        
        # 创建10个并发线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_request, args=(i,))
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 统计成功数量
        success_count = sum(1 for _, success in results if success)
        
        print(f"并发测试结果: {success_count}/10 成功，耗时: {execution_time:.2f}秒")
        
        # 验证限流熔断是否正常工作
        assert execution_time < 5.0  # 应该在5秒内完成
        assert success_count >= 8    # 至少80%成功（考虑限流）


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])