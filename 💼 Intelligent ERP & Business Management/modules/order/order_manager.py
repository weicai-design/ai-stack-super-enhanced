"""
订单管理模块
- 订单信息CRUD
- 订单状态管理
- 订单分析统计
- 订单与客户关联
- 自动事件发布（集成ERP数据监听）
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
    
    def __init__(self, db_session: Session, data_listener=None):
        """
        初始化订单管理器
        
        Args:
            db_session: 数据库会话
            data_listener: ERP数据监听器（可选，用于自动发布事件）
        """
        self.db = db_session
        self.data_listener = data_listener
    
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
            
            # 自动发布订单创建事件
            if self.data_listener:
                try:
                    order_dict = self._order_to_dict(order)
                    # 使用asyncio在同步方法中调用异步方法
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果事件循环正在运行，创建任务
                            asyncio.create_task(self.data_listener.on_order_created(order_dict))
                        else:
                            loop.run_until_complete(self.data_listener.on_order_created(order_dict))
                    except RuntimeError:
                        # 如果没有事件循环，创建新的
                        asyncio.run(self.data_listener.on_order_created(order_dict))
                except Exception as e:
                    # 事件发布失败不影响订单创建
                    import logging
                    logging.getLogger(__name__).warning(f"订单创建事件发布失败: {e}")
            
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
            
            # 自动发布订单状态变化事件
            if self.data_listener:
                try:
                    import asyncio
                    old_data = {"status": old_status}
                    new_data = self._order_to_dict(order)
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.data_listener.on_order_updated(
                                    str(order_id), old_data, new_data
                                )
                            )
                        else:
                            loop.run_until_complete(
                                self.data_listener.on_order_updated(
                                    str(order_id), old_data, new_data
                                )
                            )
                    except RuntimeError:
                        asyncio.run(
                            self.data_listener.on_order_updated(
                                str(order_id), old_data, new_data
                            )
                        )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"订单状态变化事件发布失败: {e}")
            
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
            
            # 保存旧数据用于事件发布
            old_data = self._order_to_dict(order)
            
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            # 自动发布订单更新事件
            if self.data_listener:
                try:
                    import asyncio
                    new_data = self._order_to_dict(order)
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.data_listener.on_order_updated(
                                    str(order_id), old_data, new_data
                                )
                            )
                        else:
                            loop.run_until_complete(
                                self.data_listener.on_order_updated(
                                    str(order_id), old_data, new_data
                                )
                            )
                    except RuntimeError:
                        asyncio.run(
                            self.data_listener.on_order_updated(
                                str(order_id), old_data, new_data
                            )
                        )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"订单更新事件发布失败: {e}")
            
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
            
            # 保存订单数据用于事件发布
            order_data = self._order_to_dict(order)
            
            self.db.delete(order)
            self.db.commit()
            
            # 自动发布订单删除事件
            if self.data_listener:
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.data_listener.on_order_deleted(str(order_id), order_data)
                            )
                        else:
                            loop.run_until_complete(
                                self.data_listener.on_order_deleted(str(order_id), order_data)
                            )
                    except RuntimeError:
                        asyncio.run(
                            self.data_listener.on_order_deleted(str(order_id), order_data)
                        )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"订单删除事件发布失败: {e}")
            
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
    
    # ============ 高级功能（新增）============
    
    def order_priority_analysis(self, order_id: int) -> Dict[str, Any]:
        """
        订单优先级智能分析（新功能）
        
        基于多个因素自动判断订单优先级：
        - 客户价值
        - 订单金额
        - 交付紧急度
        - 订单类型
        """
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            priority_score = 0
            factors = []
            
            # 1. 客户价值因素（0-30分）
            customer = order.customer
            if customer:
                if customer.category == 'VIP':
                    priority_score += 30
                    factors.append("VIP客户（+30分）")
                elif customer.category == '重要':
                    priority_score += 20
                    factors.append("重要客户（+20分）")
                elif customer.category == '普通':
                    priority_score += 10
                    factors.append("普通客户（+10分）")
            
            # 2. 订单金额因素（0-30分）
            amount = float(order.order_amount) if order.order_amount else 0
            if amount >= 1000000:
                priority_score += 30
                factors.append("大额订单≥100万（+30分）")
            elif amount >= 500000:
                priority_score += 20
                factors.append("中额订单≥50万（+20分）")
            elif amount >= 100000:
                priority_score += 10
                factors.append("小额订单≥10万（+10分）")
            
            # 3. 交付紧急度（0-25分）
            if order.delivery_date:
                days_to_delivery = (order.delivery_date - datetime.now()).days
                if days_to_delivery < 7:
                    priority_score += 25
                    factors.append(f"紧急交付（{days_to_delivery}天内，+25分）")
                elif days_to_delivery < 15:
                    priority_score += 15
                    factors.append(f"较紧急（{days_to_delivery}天内，+15分）")
                elif days_to_delivery < 30:
                    priority_score += 8
                    factors.append(f"正常（{days_to_delivery}天内，+8分）")
            
            # 4. 订单类型因素（0-15分）
            order_type = order.extra_metadata.get('order_type', '短期') if order.extra_metadata else '短期'
            if order_type == '长期':
                priority_score += 15
                factors.append("长期订单（+15分）")
            elif order_type == '战略':
                priority_score += 12
                factors.append("战略订单（+12分）")
            else:
                priority_score += 5
                factors.append("短期订单（+5分）")
            
            # 优先级等级
            if priority_score >= 80:
                priority_level = "P0-最高优先级"
                priority_color = "red"
                recommendation = "立即安排，优先生产，确保按时交付"
            elif priority_score >= 60:
                priority_level = "P1-高优先级"
                priority_color = "orange"
                recommendation = "优先处理，密切跟踪进度"
            elif priority_score >= 40:
                priority_level = "P2-中优先级"
                priority_color = "yellow"
                recommendation = "正常排期，按计划执行"
            else:
                priority_level = "P3-低优先级"
                priority_color = "green"
                recommendation = "灵活安排，优化资源利用"
            
            return {
                "success": True,
                "order_id": order_id,
                "order_number": order.order_number,
                "priority_level": priority_level,
                "priority_score": priority_score,
                "priority_color": priority_color,
                "contributing_factors": factors,
                "recommendation": recommendation,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def order_abnormal_detection(self) -> Dict[str, Any]:
        """
        订单异常检测（新功能）
        
        自动检测各类订单异常情况：
        - 延期订单
        - 金额异常
        - 长期未处理
        - 状态异常
        """
        try:
            all_orders = self.db.query(Order).all()
            
            abnormal_orders = {
                "delayed_delivery": [],
                "amount_abnormal": [],
                "long_pending": [],
                "status_abnormal": []
            }
            
            for order in all_orders:
                # 1. 检测延期
                if order.delivery_date and order.status != '已完成':
                    days_overdue = (datetime.now() - order.delivery_date).days
                    if days_overdue > 0:
                        abnormal_orders["delayed_delivery"].append({
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "customer_name": order.customer.name if order.customer else None,
                            "days_overdue": days_overdue,
                            "delivery_date": order.delivery_date.isoformat(),
                            "status": order.status,
                            "severity": "高" if days_overdue > 7 else "中" if days_overdue > 3 else "低"
                        })
                
                # 2. 检测金额异常（超出正常范围）
                amount = float(order.order_amount) if order.order_amount else 0
                if amount > 5000000:  # 超大额
                    abnormal_orders["amount_abnormal"].append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "amount": amount,
                        "reason": "超大额订单（>500万）",
                        "requires_review": True
                    })
                elif amount < 1000:  # 超小额
                    abnormal_orders["amount_abnormal"].append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "amount": amount,
                        "reason": "超小额订单（<1千）",
                        "requires_review": False
                    })
                
                # 3. 检测长期未处理
                if order.status == '待确认':
                    days_pending = (datetime.now() - order.created_at).days if order.created_at else 0
                    if days_pending > 3:
                        abnormal_orders["long_pending"].append({
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "days_pending": days_pending,
                            "created_at": order.created_at.isoformat() if order.created_at else None,
                            "action_required": "尽快确认订单"
                        })
                
                # 4. 检测状态异常
                # 例如：已确认但过了交付日期还未开始生产
                if order.status == '已确认' and order.delivery_date:
                    days_to_delivery = (order.delivery_date - datetime.now()).days
                    if days_to_delivery < 7:
                        abnormal_orders["status_abnormal"].append({
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "issue": "即将交付但未开始生产",
                            "days_to_delivery": days_to_delivery,
                            "current_status": order.status,
                            "recommended_action": "立即转入生产"
                        })
            
            # 统计
            total_abnormal = (
                len(abnormal_orders["delayed_delivery"]) +
                len(abnormal_orders["amount_abnormal"]) +
                len(abnormal_orders["long_pending"]) +
                len(abnormal_orders["status_abnormal"])
            )
            
            return {
                "success": True,
                "total_abnormal_count": total_abnormal,
                "abnormal_orders": abnormal_orders,
                "statistics": {
                    "delayed_delivery_count": len(abnormal_orders["delayed_delivery"]),
                    "amount_abnormal_count": len(abnormal_orders["amount_abnormal"]),
                    "long_pending_count": len(abnormal_orders["long_pending"]),
                    "status_abnormal_count": len(abnormal_orders["status_abnormal"])
                },
                "requires_immediate_attention": len(abnormal_orders["delayed_delivery"]) + len(abnormal_orders["status_abnormal"]),
                "detection_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def order_fulfillment_analysis(self) -> Dict[str, Any]:
        """
        订单履约率分析（新功能）
        
        分析订单的履约情况：
        - 按时交付率
        - 延期交付率
        - 平均延期天数
        - 履约改善趋势
        """
        try:
            # 获取已完成的订单
            completed_orders = self.db.query(Order).filter(
                Order.status == '已完成'
            ).all()
            
            if not completed_orders:
                return {
                    "success": True,
                    "message": "暂无已完成订单",
                    "on_time_rate": 0,
                    "total_orders": 0
                }
            
            on_time_count = 0
            delayed_count = 0
            total_delay_days = 0
            delay_details = []
            
            for order in completed_orders:
                if not order.delivery_date or not order.updated_at:
                    continue
                
                # 计算实际交付日期（使用updated_at作为完成日期）
                actual_delivery = order.updated_at.date()
                planned_delivery = order.delivery_date
                
                # 比较
                if actual_delivery <= planned_delivery:
                    on_time_count += 1
                else:
                    delayed_count += 1
                    delay_days = (actual_delivery - planned_delivery).days
                    total_delay_days += delay_days
                    
                    delay_details.append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "planned_delivery": planned_delivery.isoformat(),
                        "actual_delivery": actual_delivery.isoformat(),
                        "delay_days": delay_days,
                        "customer_name": order.customer.name if order.customer else None
                    })
            
            total_analyzed = on_time_count + delayed_count
            
            # 计算履约率
            on_time_rate = (on_time_count / total_analyzed * 100) if total_analyzed > 0 else 0
            delayed_rate = (delayed_count / total_analyzed * 100) if total_analyzed > 0 else 0
            avg_delay_days = (total_delay_days / delayed_count) if delayed_count > 0 else 0
            
            # 履约评级
            if on_time_rate >= 95:
                rating = "优秀"
                grade = "A+"
            elif on_time_rate >= 90:
                rating = "良好"
                grade = "A"
            elif on_time_rate >= 80:
                rating = "一般"
                grade = "B"
            elif on_time_rate >= 70:
                rating = "偏低"
                grade = "C"
            else:
                rating = "较差"
                grade = "D"
            
            # 改进建议
            recommendations = []
            if on_time_rate < 90:
                recommendations.append("履约率偏低，建议：1) 优化生产计划 2) 提前预警 3) 加强跟踪")
            if avg_delay_days > 5:
                recommendations.append(f"平均延期{avg_delay_days:.1f}天较长，需要改进生产效率")
            if delayed_count > 10:
                recommendations.append("延期订单数量较多，建议分析根本原因")
            
            return {
                "success": True,
                "fulfillment_metrics": {
                    "total_orders_analyzed": total_analyzed,
                    "on_time_count": on_time_count,
                    "delayed_count": delayed_count,
                    "on_time_rate": round(on_time_rate, 2),
                    "delayed_rate": round(delayed_rate, 2),
                    "average_delay_days": round(avg_delay_days, 2)
                },
                "rating": rating,
                "grade": grade,
                "delayed_orders": delay_details[:10],  # 只返回前10个延期订单
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def intelligent_order_allocation(self) -> Dict[str, Any]:
        """
        订单智能分配（新功能）
        
        基于订单优先级和资源情况自动分配生产计划
        """
        try:
            # 获取待处理订单
            pending_orders = self.db.query(Order).filter(
                Order.status.in_(['待确认', '已确认'])
            ).all()
            
            if not pending_orders:
                return {
                    "success": True,
                    "message": "暂无待分配订单",
                    "allocation_plan": []
                }
            
            # 为每个订单计算优先级
            order_priorities = []
            for order in pending_orders:
                priority_result = self.order_priority_analysis(order.id)
                if priority_result["success"]:
                    order_priorities.append({
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "priority_score": priority_result["priority_score"],
                        "priority_level": priority_result["priority_level"],
                        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                        "amount": float(order.order_amount) if order.order_amount else 0
                    })
            
            # 按优先级排序
            order_priorities.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # 生成分配计划
            allocation_plan = []
            current_date = datetime.now()
            
            for i, order_info in enumerate(order_priorities, 1):
                # 简化的分配逻辑
                allocation_plan.append({
                    "sequence": i,
                    "order_id": order_info["order_id"],
                    "order_number": order_info["order_number"],
                    "priority_level": order_info["priority_level"],
                    "priority_score": order_info["priority_score"],
                    "suggested_start_date": (current_date + timedelta(days=i-1)).isoformat(),
                    "delivery_date": order_info["delivery_date"],
                    "allocation_reason": f"优先级{order_info['priority_level']}，排序第{i}位"
                })
            
            return {
                "success": True,
                "total_orders": len(pending_orders),
                "allocation_plan": allocation_plan,
                "plan_generated_at": datetime.now().isoformat(),
                "recommendations": [
                    "按照分配计划顺序执行生产",
                    "关注P0和P1优先级订单",
                    "定期复核优先级，动态调整"
                ]
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# 工具函数
def get_order_manager(db_session: Session) -> OrderManager:
    """获取订单管理器实例"""
    return OrderManager(db_session)

