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
    
    # ============ 高级功能（新增）============
    
    def customer_lifecycle_analysis(self, customer_id: int) -> Dict[str, Any]:
        """
        客户生命周期分析
        - 新客户阶段
        - 成长阶段
        - 成熟阶段
        - 流失风险阶段
        """
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {"success": False, "error": "客户不存在"}
            
            # 获取客户订单
            orders = self.db.query(Order).filter(
                Order.customer_id == customer_id
            ).order_by(Order.order_date).all()
            
            if not orders:
                return {
                    "success": True,
                    "lifecycle_stage": "新客户",
                    "days_since_first_order": 0,
                    "total_orders": 0,
                    "recommendation": "尚未产生订单，建议主动跟进"
                }
            
            # 计算关键指标
            first_order_date = orders[0].order_date
            last_order_date = orders[-1].order_date
            days_since_first = (datetime.now().date() - first_order_date).days
            days_since_last = (datetime.now().date() - last_order_date).days
            total_orders = len(orders)
            total_amount = sum(o.order_amount or 0 for o in orders)
            
            # 判断生命周期阶段
            if days_since_first < 90:
                stage = "新客户"
                recommendation = "积极培养，建立良好关系"
            elif days_since_first < 365 and total_orders >= 3:
                stage = "成长阶段"
                recommendation = "持续跟进，提供优质服务"
            elif total_orders >= 10:
                stage = "成熟阶段"
                recommendation = "维护忠诚度，提供增值服务"
            elif days_since_last > 180:
                stage = "流失风险"
                recommendation = "紧急关注，主动联系挽回"
            else:
                stage = "稳定阶段"
                recommendation = "定期回访，维护关系"
            
            return {
                "success": True,
                "customer_name": customer.name,
                "lifecycle_stage": stage,
                "days_since_first_order": days_since_first,
                "days_since_last_order": days_since_last,
                "total_orders": total_orders,
                "total_amount": float(total_amount),
                "average_days_between_orders": days_since_first / max(total_orders - 1, 1),
                "recommendation": recommendation
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def customer_churn_risk_analysis(self) -> Dict[str, Any]:
        """
        客户流失风险分析
        识别有流失风险的客户
        """
        try:
            # 获取所有客户
            customers = self.db.query(Customer).all()
            
            high_risk = []
            medium_risk = []
            low_risk = []
            
            for customer in customers:
                # 获取最近订单
                last_order = self.db.query(Order).filter(
                    Order.customer_id == customer.id
                ).order_by(Order.order_date.desc()).first()
                
                if not last_order:
                    high_risk.append({
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "risk_level": "高",
                        "reason": "从未下单",
                        "days_inactive": None
                    })
                    continue
                
                # 计算不活跃天数
                days_inactive = (datetime.now().date() - last_order.order_date).days
                
                # 风险等级判断
                if days_inactive > 180:
                    high_risk.append({
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "risk_level": "高",
                        "reason": f"{days_inactive}天未下单",
                        "days_inactive": days_inactive,
                        "last_order_date": last_order.order_date.isoformat()
                    })
                elif days_inactive > 90:
                    medium_risk.append({
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "risk_level": "中",
                        "reason": f"{days_inactive}天未下单",
                        "days_inactive": days_inactive,
                        "last_order_date": last_order.order_date.isoformat()
                    })
                else:
                    low_risk.append({
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "risk_level": "低",
                        "days_inactive": days_inactive
                    })
            
            return {
                "success": True,
                "high_risk_customers": high_risk,
                "medium_risk_customers": medium_risk,
                "low_risk_customers": low_risk,
                "statistics": {
                    "total_customers": len(customers),
                    "high_risk_count": len(high_risk),
                    "medium_risk_count": len(medium_risk),
                    "low_risk_count": len(low_risk),
                    "high_risk_percentage": (len(high_risk) / len(customers) * 100) if customers else 0
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def customer_segmentation(self) -> Dict[str, Any]:
        """
        客户细分分析（RFM模型）
        R: Recency（最近一次购买）
        F: Frequency（购买频率）
        M: Monetary（购买金额）
        """
        try:
            customers = self.db.query(Customer).all()
            
            customer_segments = []
            
            for customer in customers:
                orders = self.db.query(Order).filter(
                    Order.customer_id == customer.id
                ).order_by(Order.order_date.desc()).all()
                
                if not orders:
                    continue
                
                # R: 最近一次购买距今天数
                recency = (datetime.now().date() - orders[0].order_date).days
                
                # F: 购买频率
                frequency = len(orders)
                
                # M: 购买总金额
                monetary = sum(o.order_amount or 0 for o in orders)
                
                # RFM评分（简化版：1-5分）
                r_score = 5 if recency < 30 else 4 if recency < 90 else 3 if recency < 180 else 2 if recency < 365 else 1
                f_score = 5 if frequency >= 20 else 4 if frequency >= 10 else 3 if frequency >= 5 else 2 if frequency >= 2 else 1
                m_score = 5 if monetary >= 1000000 else 4 if monetary >= 500000 else 3 if monetary >= 100000 else 2 if monetary >= 50000 else 1
                
                # 综合得分
                total_score = r_score + f_score + m_score
                
                # 客户分群
                if total_score >= 13:
                    segment = "VIP客户"
                elif total_score >= 10:
                    segment = "重要客户"
                elif total_score >= 7:
                    segment = "一般客户"
                else:
                    segment = "低价值客户"
                
                customer_segments.append({
                    "customer_id": customer.id,
                    "customer_name": customer.name,
                    "recency_days": recency,
                    "frequency": frequency,
                    "monetary": float(monetary),
                    "r_score": r_score,
                    "f_score": f_score,
                    "m_score": m_score,
                    "total_score": total_score,
                    "segment": segment
                })
            
            # 按分群统计
            from collections import Counter
            segment_counts = Counter(c["segment"] for c in customer_segments)
            
            return {
                "success": True,
                "customer_segments": customer_segments,
                "segment_distribution": dict(segment_counts),
                "total_analyzed": len(customer_segments)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def customer_credit_rating(self, customer_id: int) -> Dict[str, Any]:
        """
        客户信用评级
        基于历史订单、付款记录等
        """
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {"success": False, "error": "客户不存在"}
            
            orders = self.db.query(Order).filter(
                Order.customer_id == customer_id
            ).all()
            
            if not orders:
                return {
                    "success": True,
                    "credit_rating": "未评级",
                    "credit_score": 0,
                    "reason": "暂无订单记录"
                }
            
            # 评分因素
            total_orders = len(orders)
            total_amount = sum(o.order_amount or 0 for o in orders)
            avg_amount = total_amount / total_orders
            
            # 客户历史长度
            first_order_date = min(o.order_date for o in orders)
            customer_age_days = (datetime.now().date() - first_order_date).days
            
            # 计算信用分数（满分100）
            score = 0
            
            # 1. 订单数量（30分）
            if total_orders >= 50:
                score += 30
            elif total_orders >= 20:
                score += 25
            elif total_orders >= 10:
                score += 20
            elif total_orders >= 5:
                score += 15
            else:
                score += total_orders * 3
            
            # 2. 订单总额（30分）
            if total_amount >= 5000000:
                score += 30
            elif total_amount >= 2000000:
                score += 25
            elif total_amount >= 1000000:
                score += 20
            elif total_amount >= 500000:
                score += 15
            else:
                score += min(total_amount / 50000 * 3, 15)
            
            # 3. 客户历史（20分）
            if customer_age_days >= 730:  # 2年
                score += 20
            elif customer_age_days >= 365:  # 1年
                score += 15
            elif customer_age_days >= 180:  # 半年
                score += 10
            else:
                score += customer_age_days / 18
            
            # 4. 活跃度（20分）
            last_order = max(o.order_date for o in orders)
            days_since_last = (datetime.now().date() - last_order).days
            if days_since_last < 30:
                score += 20
            elif days_since_last < 90:
                score += 15
            elif days_since_last < 180:
                score += 10
            else:
                score += max(20 - days_since_last / 36, 0)
            
            # 信用等级
            if score >= 90:
                rating = "AAA级"
                description = "优质客户，信用极好"
            elif score >= 80:
                rating = "AA级"
                description = "优秀客户，信用良好"
            elif score >= 70:
                rating = "A级"
                description = "良好客户，信用可靠"
            elif score >= 60:
                rating = "BBB级"
                description = "一般客户，信用尚可"
            elif score >= 50:
                rating = "BB级"
                description = "普通客户，需关注"
            else:
                rating = "B级"
                description = "新客户或低活跃客户"
            
            return {
                "success": True,
                "customer_name": customer.name,
                "credit_rating": rating,
                "credit_score": round(score, 2),
                "description": description,
                "factors": {
                    "total_orders": total_orders,
                    "total_amount": float(total_amount),
                    "customer_age_days": customer_age_days,
                    "days_since_last_order": days_since_last
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# 工具函数
def get_customer_manager(db_session: Session) -> CustomerManager:
    """获取客户管理器实例"""
    return CustomerManager(db_session)











