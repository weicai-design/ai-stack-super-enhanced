"""
客户管理模块
- 客户信息CRUD
- 客户分类管理
- 客户订单关联
- 客户分析统计
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import sys
sys.path.append('../..')
from core.database_models import Customer, Order


class CustomerManager:
    """客户管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============ CRUD操作 ============
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新客户
        
        Args:
            customer_data: {
                "name": "客户名称",
                "code": "客户编码",
                "category": "VIP/普通/新客户",
                "contact_person": "联系人",
                "contact_phone": "电话",
                "contact_email": "邮箱",
                "address": "地址"
            }
        
        Returns:
            创建的客户信息
        """
        try:
            # 检查客户编码是否已存在
            existing = self.db.query(Customer).filter(
                Customer.code == customer_data['code']
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "error": f"客户编码 {customer_data['code']} 已存在"
                }
            
            # 创建客户
            customer = Customer(
                name=customer_data['name'],
                code=customer_data['code'],
                category=customer_data.get('category', '普通'),
                contact_person=customer_data.get('contact_person'),
                contact_phone=customer_data.get('contact_phone'),
                contact_email=customer_data.get('contact_email'),
                address=customer_data.get('address'),
                extra_metadata=customer_data.get('extra_metadata', {})
            )
            
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            
            return {
                "success": True,
                "customer": self._customer_to_dict(customer),
                "message": "客户创建成功"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """获取客户详情"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "error": "客户不存在"
                }
            
            # 获取客户订单统计
            order_stats = self._get_customer_order_stats(customer_id)
            
            return {
                "success": True,
                "customer": self._customer_to_dict(customer),
                "order_stats": order_stats
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_customers(
        self, 
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取客户列表
        
        Args:
            category: 客户类别筛选
            keyword: 关键词搜索
            page: 页码
            page_size: 每页数量
        
        Returns:
            客户列表和统计
        """
        try:
            query = self.db.query(Customer)
            
            # 类别筛选
            if category:
                query = query.filter(Customer.category == category)
            
            # 关键词搜索
            if keyword:
                query = query.filter(
                    or_(
                        Customer.name.like(f"%{keyword}%"),
                        Customer.code.like(f"%{keyword}%"),
                        Customer.contact_person.like(f"%{keyword}%")
                    )
                )
            
            # 总数
            total = query.count()
            
            # 分页
            offset = (page - 1) * page_size
            customers = query.offset(offset).limit(page_size).all()
            
            # 统计信息
            stats = self._get_customer_statistics()
            
            return {
                "success": True,
                "customers": [self._customer_to_dict(c) for c in customers],
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
    
    def update_customer(
        self, 
        customer_id: int, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新客户信息"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "error": "客户不存在"
                }
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(customer, key) and value is not None:
                    setattr(customer, key, value)
            
            customer.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(customer)
            
            return {
                "success": True,
                "customer": self._customer_to_dict(customer),
                "message": "客户信息已更新"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_customer(self, customer_id: int) -> Dict[str, Any]:
        """删除客户"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    "success": False,
                    "error": "客户不存在"
                }
            
            # 检查是否有关联订单
            order_count = self.db.query(Order).filter(
                Order.customer_id == customer_id
            ).count()
            
            if order_count > 0:
                return {
                    "success": False,
                    "error": f"该客户有 {order_count} 个关联订单，无法删除"
                }
            
            self.db.delete(customer)
            self.db.commit()
            
            return {
                "success": True,
                "message": "客户已删除"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 客户分析 ============
    
    def analyze_customer_value(self, customer_id: int) -> Dict[str, Any]:
        """
        客户价值分析
        - 订单总额
        - 订单数量
        - 平均订单金额
        - 长期/短期订单占比
        """
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {"success": False, "error": "客户不存在"}
            
            # 订单统计
            orders = self.db.query(Order).filter(
                Order.customer_id == customer_id
            ).all()
            
            total_orders = len(orders)
            total_amount = sum(o.order_amount for o in orders if o.order_amount)
            avg_amount = total_amount / total_orders if total_orders > 0 else 0
            
            # 长期/短期订单分析（示例：根据订单周期）
            long_term = sum(1 for o in orders if o.extra_metadata and 
                           o.extra_metadata.get('order_type') == '长期')
            short_term = total_orders - long_term
            
            return {
                "success": True,
                "customer_name": customer.name,
                "customer_code": customer.code,
                "analysis": {
                    "total_orders": total_orders,
                    "total_amount": float(total_amount),
                    "average_amount": float(avg_amount),
                    "long_term_orders": long_term,
                    "short_term_orders": short_term,
                    "long_term_ratio": (long_term / total_orders * 100) if total_orders > 0 else 0
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_customer_order_trend(
        self, 
        customer_id: int,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        客户订单趋势分析
        
        Args:
            customer_id: 客户ID
            period: 周期（day/week/month/quarter/year）
        
        Returns:
            订单趋势数据
        """
        try:
            # 获取客户所有订单
            orders = self.db.query(Order).filter(
                Order.customer_id == customer_id
            ).order_by(Order.order_date).all()
            
            # 按周期分组统计
            trend_data = self._group_orders_by_period(orders, period)
            
            return {
                "success": True,
                "customer_id": customer_id,
                "period": period,
                "trend_data": trend_data
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 客户分类管理 ============
    
    def upgrade_customer_category(
        self, 
        customer_id: int,
        new_category: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        升级/变更客户类别
        
        Args:
            customer_id: 客户ID
            new_category: 新类别
            reason: 变更原因
        
        Returns:
            更新结果
        """
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {"success": False, "error": "客户不存在"}
            
            old_category = customer.category
            customer.category = new_category
            
            # 记录变更历史
            if not customer.extra_metadata:
                customer.extra_metadata = {}
            
            if 'category_history' not in customer.extra_metadata:
                customer.extra_metadata['category_history'] = []
            
            customer.extra_metadata['category_history'].append({
                "from": old_category,
                "to": new_category,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            customer.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(customer)
            
            return {
                "success": True,
                "customer": self._customer_to_dict(customer),
                "message": f"客户类别已从 {old_category} 变更为 {new_category}"
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 内部辅助方法 ============
    
    def _customer_to_dict(self, customer: Customer) -> Dict[str, Any]:
        """将客户对象转为字典"""
        return {
            "id": customer.id,
            "name": customer.name,
            "code": customer.code,
            "category": customer.category,
            "contact_person": customer.contact_person,
            "contact_phone": customer.contact_phone,
            "contact_email": customer.contact_email,
            "address": customer.address,
            "extra_metadata": customer.extra_metadata,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "updated_at": customer.updated_at.isoformat() if customer.updated_at else None
        }
    
    def _get_customer_order_stats(self, customer_id: int) -> Dict[str, Any]:
        """获取客户订单统计"""
        orders = self.db.query(Order).filter(
            Order.customer_id == customer_id
        ).all()
        
        total_amount = sum(o.order_amount for o in orders if o.order_amount)
        
        return {
            "total_orders": len(orders),
            "total_amount": float(total_amount),
            "average_amount": float(total_amount / len(orders)) if len(orders) > 0 else 0
        }
    
    def _get_customer_statistics(self) -> Dict[str, Any]:
        """获取客户总体统计"""
        total = self.db.query(Customer).count()
        vip = self.db.query(Customer).filter(Customer.category == 'VIP').count()
        normal = self.db.query(Customer).filter(Customer.category == '普通').count()
        new = self.db.query(Customer).filter(Customer.category == '新客户').count()
        
        return {
            "total": total,
            "vip": vip,
            "normal": normal,
            "new": new
        }
    
    def _group_orders_by_period(
        self, 
        orders: List[Order], 
        period: str
    ) -> List[Dict[str, Any]]:
        """按周期分组订单"""
        from collections import defaultdict
        
        grouped = defaultdict(lambda: {"count": 0, "amount": 0})
        
        for order in orders:
            if not order.order_date:
                continue
            
            # 根据周期生成key
            if period == "day":
                key = order.order_date.strftime("%Y-%m-%d")
            elif period == "week":
                key = order.order_date.strftime("%Y-W%W")
            elif period == "month":
                key = order.order_date.strftime("%Y-%m")
            elif period == "quarter":
                quarter = (order.order_date.month - 1) // 3 + 1
                key = f"{order.order_date.year}-Q{quarter}"
            elif period == "year":
                key = str(order.order_date.year)
            else:
                key = order.order_date.strftime("%Y-%m")
            
            grouped[key]["count"] += 1
            grouped[key]["amount"] += order.order_amount if order.order_amount else 0
        
        # 转换为列表
        result = [
            {
                "period": k,
                "order_count": v["count"],
                "total_amount": float(v["amount"])
            }
            for k, v in sorted(grouped.items())
        ]
        
        return result


# 工具函数
def get_customer_manager(db_session: Session) -> CustomerManager:
    """获取客户管理器实例"""
    return CustomerManager(db_session)











