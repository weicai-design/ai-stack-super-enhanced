"""订单管理模块"""
import logging
from typing import Dict, List, Optional
from datetime import date
from ..models import Order

logger = logging.getLogger(__name__)

class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        self.orders: Dict[str, List[Order]] = {}
    
    def create_order(self, tenant_id: str, order: Order) -> Order:
        """创建订单"""
        if tenant_id not in self.orders:
            self.orders[tenant_id] = []
        order.tenant_id = tenant_id
        order.total_amount = order.quantity * order.unit_price
        self.orders[tenant_id].append(order)
        logger.info(f"订单已创建: {order.order_no}")
        return order
    
    def get_orders(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Order]:
        """获取订单列表"""
        orders = self.orders.get(tenant_id, [])
        if filters:
            if "status" in filters:
                orders = [o for o in orders if o.status == filters["status"]]
            if "customer_id" in filters:
                orders = [o for o in orders if o.customer_id == filters["customer_id"]]
        return orders
    
    def update_order_status(self, tenant_id: str, order_id: str, status: str) -> Optional[Order]:
        """更新订单状态"""
        for order in self.orders.get(tenant_id, []):
            if order.id == order_id:
                order.status = status
                logger.info(f"订单状态已更新: {order.order_no} -> {status}")
                return order
        return None
    
    def get_order_statistics(self, tenant_id: str) -> Dict:
        """获取订单统计"""
        orders = self.orders.get(tenant_id, [])
        total = len(orders)
        total_amount = sum(o.total_amount for o in orders)
        avg_amount = total_amount / total if total > 0 else 0
        
        by_status = {}
        for order in orders:
            by_status[order.status] = by_status.get(order.status, 0) + 1
        
        return {
            "total_orders": total,
            "total_amount": total_amount,
            "avg_order_amount": avg_amount,
            "orders_by_status": by_status
        }

order_manager = OrderManager()

















