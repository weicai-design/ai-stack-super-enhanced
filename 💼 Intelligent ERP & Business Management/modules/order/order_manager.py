"""
订单管理模块
- 订单信息CRUD
- 订单状态管理
- 订单分析统计
- 订单与客户关联
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal
import sys
sys.path.append('../..')
from core.database_models import Order, Customer, OrderItem


class OrderManager:
    """订单管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============ CRUD操作 ============
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新订单
        
        Args:
            order_data: {
                "customer_id": 客户ID,
                "order_number": "订单编号",
                "order_date": "订单日期",
                "delivery_date": "交付日期",
                "order_amount": 订单金额,
                "order_type": "长期/短期",
                "status": "待确认/已确认/生产中/已完成",
                "items": [订单明细]
            }
        
        Returns:
            创建的订单信息
        """
        try:
            # 验证客户是否存在
            customer = self.db.query(Customer).filter(
                Customer.id == order_data['customer_id']
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "error": "客户不存在"
                }
            
            # 检查订单编号是否已存在
            existing = self.db.query(Order).filter(
                Order.order_number == order_data['order_number']
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"订单编号 {order_data['order_number']} 已存在"
                }
            
            # 创建订单
            order = Order(
                customer_id=order_data['customer_id'],
                order_number=order_data['order_number'],
                order_date=datetime.fromisoformat(order_data['order_date']) 
                           if isinstance(order_data.get('order_date'), str) 
                           else order_data.get('order_date', datetime.utcnow()),
                delivery_date=datetime.fromisoformat(order_data['delivery_date'])
                             if order_data.get('delivery_date') and isinstance(order_data['delivery_date'], str)
                             else order_data.get('delivery_date'),
                order_amount=Decimal(str(order_data.get('order_amount', 0))),
                status=order_data.get('status', '待确认'),
                extra_metadata={
                    "order_type": order_data.get('order_type', '短期'),
                    "items": order_data.get('items', [])
                }
            )
            
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            return {
                "success": True,
                "order": self._order_to_dict(order),
                "message": "订单创建成功"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_orders(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取订单列表"""
        try:
            query = self.db.query(Order)
            
            # 客户筛选
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            
            # 状态筛选
            if status:
                query = query.filter(Order.status == status)
            
            # 日期范围筛选
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            if end_date:
                query = query.filter(Order.order_date <= end_date)
            
            # 总数
            total = query.count()
            
            # 分页
            offset = (page - 1) * page_size
            orders = query.order_by(Order.order_date.desc()).offset(offset).limit(page_size).all()
            
            # 统计
            stats = self._get_order_statistics(customer_id, status)
            
            return {
                "success": True,
                "orders": [self._order_to_dict(o) for o in orders],
                "total": total,
                "page": page,
                "page_size": page_size,
                "statistics": stats
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_order_status(
        self,
        order_id: int,
        new_status: str,
        note: str = ""
    ) -> Dict[str, Any]:
        """更新订单状态"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            old_status = order.status
            order.status = new_status
            
            # 记录状态变更历史
            if not order.extra_metadata:
                order.extra_metadata = {}
            
            if 'status_history' not in order.extra_metadata:
                order.extra_metadata['status_history'] = []
            
            order.extra_metadata['status_history'].append({
                "from": old_status,
                "to": new_status,
                "note": note,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            return {
                "success": True,
                "order": self._order_to_dict(order),
                "message": f"订单状态已从 {old_status} 变更为 {new_status}"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 订单分析 ============
    
    def analyze_order_trends(
        self,
        period: str = "month",
        months: int = 12
    ) -> Dict[str, Any]:
        """
        订单趋势分析
        
        Args:
            period: 周期（day/week/month/quarter/year）
            months: 分析月数
        
        Returns:
            趋势数据
        """
        try:
            # 获取指定时间范围的订单
            start_date = datetime.utcnow() - timedelta(days=months*30)
            
            orders = self.db.query(Order).filter(
                Order.order_date >= start_date
            ).all()
            
            # 按周期分组
            from modules.customer.customer_manager import CustomerManager
            cm = CustomerManager(self.db)
            trend_data = cm._group_orders_by_period(orders, period)
            
            return {
                "success": True,
                "period": period,
                "months": months,
                "trend_data": trend_data
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_order_by_category(self) -> Dict[str, Any]:
        """按客户类别分析订单"""
        try:
            # 联表查询
            result = self.db.query(
                Customer.category,
                func.count(Order.id).label('order_count'),
                func.sum(Order.order_amount).label('total_amount')
            ).join(Order, Customer.id == Order.customer_id)\
             .group_by(Customer.category).all()
            
            analysis = [
                {
                    "category": r.category,
                    "order_count": r.order_count,
                    "total_amount": float(r.total_amount) if r.total_amount else 0
                }
                for r in result
            ]
            
            return {
                "success": True,
                "analysis": analysis
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_order(self, order_id: int) -> Dict[str, Any]:
        """获取订单详情"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            return {
                "success": True,
                "order": self._order_to_dict(order)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_order(
        self,
        order_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新订单"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(order, key) and value is not None:
                    setattr(order, key, value)
            
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            return {
                "success": True,
                "order": self._order_to_dict(order),
                "message": "订单已更新"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def delete_order(self, order_id: int) -> Dict[str, Any]:
        """删除订单"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            # 检查订单状态
            if order.status in ['生产中', '已完成']:
                return {
                    "success": False,
                    "error": f"订单状态为 {order.status}，无法删除"
                }
            
            self.db.delete(order)
            self.db.commit()
            
            return {
                "success": True,
                "message": "订单已删除"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    # ============ 内部辅助方法 ============
    
    def _order_to_dict(self, order: Order) -> Dict[str, Any]:
        """订单对象转字典"""
        customer = order.customer if order.customer else None
        
        return {
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": customer.name if customer else None,
            "order_number": order.order_number,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
            "order_amount": float(order.order_amount) if order.order_amount else 0,
            "status": order.status,
            "extra_metadata": order.extra_metadata,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        }
    
    def _get_order_statistics(
        self,
        customer_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取订单统计"""
        query = self.db.query(Order)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if status:
            query = query.filter(Order.status == status)
        
        total = query.count()
        total_amount = self.db.query(func.sum(Order.order_amount)).filter(
            Order.id.in_([o.id for o in query.all()])
        ).scalar() or 0
        
        return {
            "total_orders": total,
            "total_amount": float(total_amount)
        }


# ============ 订单管理器（临时实现） ============
class OrderManager:
    """订单管理器"""
    def __init__(self, db_session: Session):
        self.db = db_session


# ============ 项目管理器（临时实现） ============
class ProjectManager:
    """项目管理器"""
    def __init__(self, db_session: Session):
        self.db = db_session

