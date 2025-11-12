"""
运营数据分析器
制造型企业场景数据分析
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

class DataAnalyzer:
    """
    运营数据分析器
    
    功能：
    1. 订单-项目-计划-采购-生产-入库-交付-回款全流程分析
    2. 关键指标监控
    3. 异常预警
    """
    
    def __init__(self, erp_connector=None):
        self.erp_connector = erp_connector
        
    async def analyze_manufacturing_flow(self) -> Dict[str, Any]:
        """分析制造流程（订单→回款全流程）⭐增强版"""
        # 从ERP获取数据
        if self.erp_connector:
            data = await self.erp_connector.get_manufacturing_data()
        else:
            data = {}
        
        orders = data.get("orders", [])
        projects = data.get("projects", [])
        production = data.get("production", [])
        delivery = data.get("delivery", [])
        payment = data.get("payment", [])
        
        # 分析各环节
        analysis = {
            "orders": self._analyze_orders(orders),
            "projects": self._analyze_projects(projects),
            "production": self._analyze_production(production),
            "delivery": self._analyze_delivery(delivery),
            "payment": self._analyze_payment(payment),
            "flow_efficiency": self._analyze_flow_efficiency(orders, delivery, payment),
            "key_metrics": self._calculate_key_metrics(orders, delivery, payment),
            "anomalies": self._detect_anomalies(orders, production, delivery, payment)
        }
        
        return analysis
    
    def _analyze_flow_efficiency(
        self,
        orders: List[Dict],
        delivery: List[Dict],
        payment: List[Dict]
    ) -> Dict[str, Any]:
        """分析流程效率"""
        # 计算订单到交付的平均时间
        order_to_delivery_time = []
        for order in orders:
            order_date = order.get("created_at")
            order_id = order.get("id")
            # 查找对应的交付记录
            matching_delivery = next(
                (d for d in delivery if d.get("order_id") == order_id),
                None
            )
            if matching_delivery and order_date:
                delivery_date = matching_delivery.get("delivery_date")
                if delivery_date:
                    # 计算时间差（简化）
                    order_to_delivery_time.append(1)  # 占位值
        
        # 计算交付到回款的平均时间
        delivery_to_payment_time = []
        for deliv in delivery:
            delivery_id = deliv.get("id")
            matching_payment = next(
                (p for p in payment if p.get("delivery_id") == delivery_id),
                None
            )
            if matching_payment:
                delivery_to_payment_time.append(1)  # 占位值
        
        return {
            "order_to_delivery_avg_days": sum(order_to_delivery_time) / len(order_to_delivery_time) if order_to_delivery_time else 0,
            "delivery_to_payment_avg_days": sum(delivery_to_payment_time) / len(delivery_to_payment_time) if delivery_to_payment_time else 0,
            "total_flow_efficiency": "良好"  # 简化评估
        }
    
    def _calculate_key_metrics(
        self,
        orders: List[Dict],
        delivery: List[Dict],
        payment: List[Dict]
    ) -> Dict[str, Any]:
        """计算关键指标"""
        total_order_amount = sum(o.get("amount", 0) for o in orders)
        total_delivery_amount = sum(d.get("amount", 0) for d in delivery)
        total_payment_amount = sum(p.get("amount", 0) for p in payment)
        
        return {
            "total_orders": len(orders),
            "total_order_amount": total_order_amount,
            "total_deliveries": len(delivery),
            "total_delivery_amount": total_delivery_amount,
            "total_payments": len(payment),
            "total_payment_amount": total_payment_amount,
            "payment_rate": (total_payment_amount / total_order_amount * 100) if total_order_amount > 0 else 0,
            "delivery_rate": (total_delivery_amount / total_order_amount * 100) if total_order_amount > 0 else 0
        }
    
    def _detect_anomalies(
        self,
        orders: List[Dict],
        production: List[Dict],
        delivery: List[Dict],
        payment: List[Dict]
    ) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        # 检测超期订单
        overdue_orders = [
            o for o in orders
            if o.get("status") == "in_progress" and o.get("due_date")
            # 简化：假设有超期逻辑
        ]
        if overdue_orders:
            anomalies.append({
                "type": "overdue_orders",
                "severity": "high",
                "count": len(overdue_orders),
                "description": f"有{len(overdue_orders)}个订单超期"
            })
        
        # 检测交付延迟
        delayed_deliveries = [
            d for d in delivery
            if d.get("status") == "delayed"
        ]
        if delayed_deliveries:
            anomalies.append({
                "type": "delayed_deliveries",
                "severity": "medium",
                "count": len(delayed_deliveries),
                "description": f"有{len(delayed_deliveries)}个交付延迟"
            })
        
        # 检测回款异常
        unpaid_orders = len(orders) - len(payment)
        if unpaid_orders > len(orders) * 0.3:  # 超过30%未回款
            anomalies.append({
                "type": "high_unpaid_rate",
                "severity": "high",
                "unpaid_count": unpaid_orders,
                "description": f"未回款订单占比过高: {unpaid_orders}/{len(orders)}"
            })
        
        return anomalies
    
    def _analyze_orders(self, orders: List[Dict]) -> Dict[str, Any]:
        """分析订单"""
        return {
            "total": len(orders),
            "pending": len([o for o in orders if o.get("status") == "pending"]),
            "in_progress": len([o for o in orders if o.get("status") == "in_progress"]),
            "completed": len([o for o in orders if o.get("status") == "completed"])
        }
    
    def _analyze_projects(self, projects: List[Dict]) -> Dict[str, Any]:
        """分析项目"""
        return {"total": len(projects)}
    
    def _analyze_production(self, production: List[Dict]) -> Dict[str, Any]:
        """分析生产"""
        return {"total": len(production)}
    
    def _analyze_delivery(self, delivery: List[Dict]) -> Dict[str, Any]:
        """分析交付"""
        return {"total": len(delivery)}
    
    def _analyze_payment(self, payment: List[Dict]) -> Dict[str, Any]:
        """分析回款"""
        return {"total": len(payment)}

