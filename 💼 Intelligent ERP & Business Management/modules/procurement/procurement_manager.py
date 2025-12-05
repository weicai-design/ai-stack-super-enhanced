"""
采购管理模块
实现完整的采购流程管理功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import time
import threading
from collections import deque

# 导入监控模块
import sys
import os
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 注释掉不存在的导入，使用本地实现
# from monitoring.project_procurement_monitor import (
#     monitor_project_creation, monitor_procurement_order,
#     MetricType, monitor
# )
# from core.circuit_breaker import circuit_breaker, rate_limit, circuit_manager
# from core.error_handler import ErrorHandlingStrategies
# from core.audit_manager import audit_decorators


class RateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, capacity: int, rate: float):
        self.capacity = capacity  # 桶容量
        self.tokens = capacity    # 当前令牌数
        self.rate = rate          # 令牌生成速率（个/秒）
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """获取令牌"""
        with self.lock:
            now = time.time()
            # 补充令牌
            time_passed = now - self.last_refill
            new_tokens = time_passed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            # 检查是否足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, half_open_max_requests: int = 2):
        self.failure_threshold = failure_threshold  # 失败阈值
        self.recovery_timeout = recovery_timeout   # 恢复超时（秒）
        self.half_open_max_requests = half_open_max_requests  # 半开状态最大请求数
        self.failures = 0                           # 当前失败次数
        self.last_failure_time = None               # 最后失败时间
        self.state = "CLOSED"                       # 状态：CLOSED, OPEN, HALF_OPEN
        self.half_open_requests = 0                  # 半开状态请求计数
        self.lock = threading.Lock()
    
    def record_failure(self):
        """记录失败"""
        with self.lock:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"熔断器状态变为OPEN，失败次数: {self.failures}")
    
    def record_success(self):
        """记录成功"""
        with self.lock:
            self.failures = 0
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                logger.info("熔断器状态恢复为CLOSED")
    
    def allow_request(self) -> bool:
        """检查是否允许请求"""
        with self.lock:
            if self.state == "CLOSED":
                return True
            
            if self.state == "OPEN":
                # 检查是否超时，进入半开状态
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_requests = 0
                    logger.info("熔断器进入HALF_OPEN状态")
                    return True
                return False
            
            # HALF_OPEN状态检查请求数量
            if self.half_open_requests < self.half_open_max_requests:
                self.half_open_requests += 1
                return True
            return False


class ProcurementStatus(Enum):
    """采购状态"""
    DRAFT = "draft"  # 草稿
    PENDING_APPROVAL = "pending_approval"  # 待审批
    APPROVED = "approved"  # 已审批
    ORDERED = "ordered"  # 已下单
    PARTIAL_RECEIVED = "partial_received"  # 部分到货
    RECEIVED = "received"  # 已到货
    CANCELLED = "cancelled"  # 已取消
    CLOSED = "closed"  # 已关闭


class ProcurementType(Enum):
    """采购类型"""
    RAW_MATERIAL = "raw_material"  # 原材料
    COMPONENT = "component"  # 零部件
    FINISHED_GOODS = "finished_goods"  # 成品
    PACKAGING = "packaging"  # 包装材料
    CONSUMABLE = "consumable"  # 耗材
    EQUIPMENT = "equipment"  # 设备
    SERVICE = "service"  # 服务


class ProcurementManager:
    """采购管理器"""
    
    def __init__(self, data_listener=None):
        """
        初始化采购管理器
        
        Args:
            data_listener: ERP数据监听器（可选，用于自动发布事件）
        """
        self.procurement_orders = {}
        self.suppliers = {}
        self.purchase_requests = {}
        self.price_history = {}
        self.order_counter = 1000
        self.data_listener = data_listener
        
        # 限流熔断配置
        self.rate_limiter = RateLimiter(capacity=100, rate=10)  # 100容量，10个/秒
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        # 缓存配置
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, float] = {}
        self.cache_lock = threading.Lock()
    
    def _check_rate_limit(self) -> bool:
        """检查限流"""
        if not self.rate_limiter.acquire():
            logger.warning("请求被限流")
            return False
        return True
    
    def _check_circuit_breaker(self) -> bool:
        """检查熔断器"""
        if not self.circuit_breaker.allow_request():
            logger.warning("请求被熔断")
            return False
        return True
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self.cache_lock:
            if key in self.cache and time.time() < self.cache_ttl.get(key, 0):
                return self.cache[key]
            return None
    
    def _cache_set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        with self.cache_lock:
            self.cache[key] = value
            self.cache_ttl[key] = time.time() + ttl
    
    def _cache_invalidate(self, key: str):
        """清除缓存"""
        with self.cache_lock:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_ttl:
                del self.cache_ttl[key]
    
    def create_purchase_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建采购申请
        
        Args:
            request_data: 采购请求数据，包含以下字段：
                - item_name: 商品名称
                - quantity: 数量
                - unit_price: 单价
                - supplier: 供应商
                - requested_by: 申请人
        
        Returns:
            采购申请信息
        """
        # 检查限流和熔断
        if not self._check_rate_limit():
            return {"status": "error", "message": "请求频率过高，请稍后再试"}
        
        if not self._check_circuit_breaker():
            return {"status": "error", "message": "系统暂时不可用，请稍后再试"}
        
        try:
            # 验证必要字段
            required_fields = ["item_name", "quantity", "unit_price", "supplier", "requested_by"]
            for field in required_fields:
                if field not in request_data:
                    return {"status": "error", "message": f"验证失败：缺少必要字段 {field}"}
            
            # 生成请求ID
            request_id = f"PR{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 创建采购请求记录
            request = {
                "request_id": request_id,
                "item_name": request_data["item_name"],
                "quantity": request_data["quantity"],
                "unit_price": request_data["unit_price"],
                "supplier": request_data["supplier"],
                "requested_by": request_data["requested_by"],
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "total_amount": request_data["quantity"] * request_data["unit_price"]
            }
            
            # 存储到内存中
            self.purchase_requests[request_id] = request
            
            # 记录成功
            self.circuit_breaker.record_success()
            
            return {
                "status": "success",
                "request_id": request_id,
                "message": "采购请求创建成功",
                "data": request
            }
            
        except Exception as e:
            # 记录失败
            self.circuit_breaker.record_failure()
            logger.error(f"创建采购请求失败: {e}")
            return {"status": "error", "message": f"创建采购请求失败: {str(e)}"}
    
    def approve_purchase_request(
        self,
        request_id: str,
        approver: str,
        approved: bool,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        审批采购申请
        
        Args:
            request_id: 申请ID
            approver: 审批人
            approved: 是否批准
            comment: 审批意见
        
        Returns:
            审批结果
        """
        if request_id not in self.purchase_requests:
            return {"success": False, "error": "采购申请不存在"}
        
        request = self.purchase_requests[request_id]
        
        if approved:
            request["status"] = "approved"
            request["approved_at"] = datetime.now().isoformat()
            request["approved_by"] = approver
            request["approval_comment"] = comment
            
            # 自动转换为采购订单
            po_result = self.create_procurement_order_from_request(request_id)
            
            return {
                "success": True,
                "message": "采购申请已批准",
                "request": request,
                "procurement_order": po_result.get("order")
            }
        else:
            request["status"] = "rejected"
            request["rejected_at"] = datetime.now().isoformat()
            request["rejected_by"] = approver
            request["rejection_reason"] = comment
            
            return {
                "success": True,
                "message": "采购申请已拒绝",
                "request": request
            }
    
    def create_procurement_order_from_request(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """
        从采购申请创建采购订单
        
        Args:
            request_id: 采购申请ID
        
        Returns:
            采购订单信息
        """
        if request_id not in self.purchase_requests:
            return {"success": False, "error": "采购申请不存在"}
        
        request = self.purchase_requests[request_id]
        
        if request["status"] != "approved":
            return {"success": False, "error": "采购申请未批准"}
        
        # 根据物料选择供应商
        supplier_id = self._select_best_supplier(request["items"])
        
        return self.create_procurement_order(
            supplier_id=supplier_id,
            items=request["items"],
            delivery_date=request["required_date"],
            reference=f"基于采购申请 {request_id}"
        )
    
    def create_procurement_order(
        self,
        supplier_id: str,
        items: List[Dict[str, Any]],
        delivery_date: str,
        payment_terms: str = "Net 30",
        reference: str = ""
    ) -> Dict[str, Any]:
        """
        创建采购订单
        
        Args:
            supplier_id: 供应商ID
            items: 采购项目 [{"material_id": "", "quantity": 0, "unit_price": 0}]
            delivery_date: 交货日期
            payment_terms: 付款条款
            reference: 参考信息
        
        Returns:
            采购订单信息
        """
        start_time = time.time()
        
        try:
            order_id = f"PO{datetime.now().strftime('%Y%m%d')}{self.order_counter:04d}"
            self.order_counter += 1
            
            # 记录供应商绩效（模拟）
            supplier_performance = 0.95  # 模拟供应商绩效
            logger.info(f"供应商绩效记录: {supplier_performance}, 供应商ID: {supplier_id}")
            
            # 记录响应时间
            response_time = time.time() - start_time
            logger.info(f"API响应时间: {response_time}, 方法: create_procurement_order")
            
            return {
                "success": True,
                "order_id": order_id,
                "message": "采购订单创建成功"
            }
            
        except Exception as e:
            # 记录错误指标
            logger.error(f"创建采购订单失败: {str(e)}, 方法: create_procurement_order")
            raise
        
        # 计算总金额
        total_amount = sum(item["quantity"] * item.get("unit_price", 0) for item in items)
        
        order = {
            "order_id": order_id,
            "supplier_id": supplier_id,
            "items": items,
            "total_amount": total_amount,
            "currency": "CNY",
            "delivery_date": delivery_date,
            "payment_terms": payment_terms,
            "reference": reference,
            "status": ProcurementStatus.APPROVED.value,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "ordered_at": None,
            "received_items": [],
            "invoice_amount": 0,
            "paid_amount": 0
        }
        
        self.procurement_orders[order_id] = order
        
        # 自动发布采购订单创建事件
        if self.data_listener:
            try:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            self.data_listener.on_procurement_order_created(order_id, order)
                        )
                    else:
                        loop.run_until_complete(
                            self.data_listener.on_procurement_order_created(order_id, order)
                        )
                except RuntimeError:
                    asyncio.run(
                        self.data_listener.on_procurement_order_created(order_id, order)
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"采购订单创建事件发布失败: {e}")
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "采购订单已创建",
            "order": order
        }
    
    def send_order_to_supplier(
        self,
        order_id: str,
        send_method: str = "email"
    ) -> Dict[str, Any]:
        """
        发送订单给供应商
        
        Args:
            order_id: 订单ID
            send_method: 发送方式 (email/fax/portal)
        
        Returns:
            发送结果
        """
        if order_id not in self.procurement_orders:
            return {"success": False, "error": "采购订单不存在"}
        
        order = self.procurement_orders[order_id]
        order["status"] = ProcurementStatus.ORDERED.value
        order["ordered_at"] = datetime.now().isoformat()
        order["send_method"] = send_method
        
        # 实际应用中，这里会调用邮件服务或其他发送方式
        
        return {
            "success": True,
            "message": f"采购订单已通过{send_method}发送给供应商",
            "order": order
        }
    
    def record_goods_receipt(
        self,
        order_id: str,
        received_items: List[Dict[str, Any]],
        receipt_date: str,
        quality_check: bool = True
    ) -> Dict[str, Any]:
        """
        记录收货
        
        Args:
            order_id: 订单ID
            received_items: 收货项目 [{"material_id": "", "quantity": 0, "quality": "pass"}]
            receipt_date: 收货日期
            quality_check: 是否通过质检
        
        Returns:
            收货记录
        """
        if order_id not in self.procurement_orders:
            return {"success": False, "error": "采购订单不存在"}
        
        order = self.procurement_orders[order_id]
        
        # 添加收货记录
        receipt_record = {
            "receipt_id": f"GR{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "order_id": order_id,
            "received_items": received_items,
            "receipt_date": receipt_date,
            "quality_check": quality_check,
            "created_at": datetime.now().isoformat()
        }
        
        order["received_items"].append(receipt_record)
        
        # 检查是否全部收货
        total_ordered = {item["material_id"]: item["quantity"] for item in order["items"]}
        total_received = {}
        
        for receipt in order["received_items"]:
            for item in receipt["received_items"]:
                mat_id = item["material_id"]
                total_received[mat_id] = total_received.get(mat_id, 0) + item["quantity"]
        
        # 更新订单状态
        all_received = all(
            total_received.get(mat_id, 0) >= qty
            for mat_id, qty in total_ordered.items()
        )
        
        if all_received:
            order["status"] = ProcurementStatus.RECEIVED.value
        else:
            order["status"] = ProcurementStatus.PARTIAL_RECEIVED.value
        
        return {
            "success": True,
            "message": "收货记录已创建",
            "receipt": receipt_record,
            "order_status": order["status"]
        }
    
    def get_procurement_analysis(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        采购分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            采购分析报告
        """
        # 筛选时间范围内的订单
        orders_in_range = [
            order for order in self.procurement_orders.values()
            if start_date <= order["created_at"][:10] <= end_date
        ]
        
        # 统计分析
        total_orders = len(orders_in_range)
        total_amount = sum(order["total_amount"] for order in orders_in_range)
        
        # 按供应商统计
        by_supplier = {}
        for order in orders_in_range:
            supplier = order["supplier_id"]
            if supplier not in by_supplier:
                by_supplier[supplier] = {
                    "order_count": 0,
                    "total_amount": 0
                }
            by_supplier[supplier]["order_count"] += 1
            by_supplier[supplier]["total_amount"] += order["total_amount"]
        
        # 按状态统计
        by_status = {}
        for order in orders_in_range:
            status = order["status"]
            by_status[status] = by_status.get(status, 0) + 1
        
        # 及时交货率
        on_time_deliveries = 0
        total_deliveries = 0
        
        for order in orders_in_range:
            if order["status"] in [ProcurementStatus.RECEIVED.value, ProcurementStatus.CLOSED.value]:
                total_deliveries += 1
                if order.get("received_items"):
                    last_receipt = order["received_items"][-1]
                    if last_receipt["receipt_date"] <= order["delivery_date"]:
                        on_time_deliveries += 1
        
        on_time_rate = (on_time_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_orders": total_orders,
                "total_amount": total_amount,
                "average_order_value": total_amount / total_orders if total_orders > 0 else 0
            },
            "by_supplier": by_supplier,
            "by_status": by_status,
            "performance": {
                "on_time_delivery_rate": round(on_time_rate, 2),
                "total_deliveries": total_deliveries,
                "on_time_deliveries": on_time_deliveries
            }
        }
    
    def _select_best_supplier(self, items: List[Dict[str, Any]]) -> str:
        """
        选择最佳供应商
        
        Args:
            items: 物料清单
        
        Returns:
            供应商ID
        """
        # 简化版本，实际应根据价格、质量、交货期等综合评估
        # 这里返回默认供应商
        return "SUP001"
    
    def add_supplier(
        self,
        supplier_id: str,
        name: str,
        contact: Dict[str, Any],
        materials: List[str],
        payment_terms: str = "Net 30",
        rating: float = 0.0
    ) -> Dict[str, Any]:
        """
        添加供应商
        
        Args:
            supplier_id: 供应商ID
            name: 供应商名称
            contact: 联系信息
            materials: 可供应物料列表
            payment_terms: 付款条款
            rating: 供应商评级
        
        Returns:
            供应商信息
        """
        supplier = {
            "supplier_id": supplier_id,
            "name": name,
            "contact": contact,
            "materials": materials,
            "payment_terms": payment_terms,
            "rating": rating,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        self.suppliers[supplier_id] = supplier
        
        return {
            "success": True,
            "message": "供应商已添加",
            "supplier": supplier
        }
    
    def get_supplier_performance(
        self,
        supplier_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取供应商绩效
        
        Args:
            supplier_id: 供应商ID
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            供应商绩效报告
        """
        # 筛选该供应商的订单
        supplier_orders = [
            order for order in self.procurement_orders.values()
            if order["supplier_id"] == supplier_id
            and start_date <= order["created_at"][:10] <= end_date
        ]
        
        if not supplier_orders:
            return {
                "supplier_id": supplier_id,
                "period": {"start": start_date, "end": end_date},
                "message": "该时期内无订单数据"
            }
        
        # 统计指标
        total_orders = len(supplier_orders)
        total_amount = sum(order["total_amount"] for order in supplier_orders)
        
        # 质量指标
        quality_issues = 0
        for order in supplier_orders:
            for receipt in order.get("received_items", []):
                for item in receipt["received_items"]:
                    if item.get("quality") != "pass":
                        quality_issues += 1
        
        # 交货准时率
        on_time = sum(
            1 for order in supplier_orders
            if order["status"] == ProcurementStatus.RECEIVED.value
            and order.get("received_items")
            and order["received_items"][-1]["receipt_date"] <= order["delivery_date"]
        )
        
        delivered_orders = sum(
            1 for order in supplier_orders
            if order["status"] in [ProcurementStatus.RECEIVED.value, ProcurementStatus.CLOSED.value]
        )
        
        on_time_rate = (on_time / delivered_orders * 100) if delivered_orders > 0 else 0
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": self.suppliers.get(supplier_id, {}).get("name", "Unknown"),
            "period": {"start": start_date, "end": end_date},
            "metrics": {
                "total_orders": total_orders,
                "total_amount": total_amount,
                "average_order_value": total_amount / total_orders,
                "on_time_delivery_rate": round(on_time_rate, 2),
                "quality_issues": quality_issues,
                "quality_pass_rate": round((1 - quality_issues / total_orders) * 100, 2) if total_orders > 0 else 100
            }
        }


# 创建默认实例
default_procurement_manager = ProcurementManager()
