"""
售后服务管理模块
- 售后工单管理
- 客户投诉处理
- 维修记录管理
- 退换货管理
- 售后数据分析
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import sys
sys.path.append('../..')
from core.database_models import (
    AfterSalesTicket, CustomerComplaint, RepairRecord, ReturnRecord,
    Customer, Order
)


class AfterSalesManager:
    """售后服务管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============ 售后工单管理 ============
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建售后工单
        
        Args:
            ticket_data: {
                "order_id": 订单ID,
                "customer_id": 客户ID,
                "ticket_type": "complaint/repair/return/exchange/consultation",
                "priority": "low/medium/high/urgent",
                "title": "工单标题",
                "description": "问题描述",
                "assigned_to": "负责人",
                "reported_by": "报告人"
            }
        
        Returns:
            创建的工单信息
        """
        try:
            # 生成工单编号
            ticket_number = self._generate_ticket_number()
            
            # 创建工单
            ticket = AfterSalesTicket(
                ticket_number=ticket_number,
                order_id=ticket_data['order_id'],
                customer_id=ticket_data['customer_id'],
                ticket_type=ticket_data['ticket_type'],
                priority=ticket_data.get('priority', 'medium'),
                status='open',
                title=ticket_data['title'],
                description=ticket_data['description'],
                assigned_to=ticket_data.get('assigned_to'),
                reported_by=ticket_data.get('reported_by'),
                reported_at=datetime.utcnow()
            )
            
            self.db.add(ticket)
            self.db.commit()
            self.db.refresh(ticket)
            
            return {
                "success": True,
                "ticket": self._ticket_to_dict(ticket)
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """获取工单详情"""
        ticket = self.db.query(AfterSalesTicket).filter(
            AfterSalesTicket.id == ticket_id
        ).first()
        
        if not ticket:
            return {"success": False, "error": "工单不存在"}
        
        return {
            "success": True,
            "ticket": self._ticket_to_dict(ticket)
        }
    
    def list_tickets(
        self,
        status: Optional[str] = None,
        ticket_type: Optional[str] = None,
        priority: Optional[str] = None,
        customer_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取工单列表"""
        query = self.db.query(AfterSalesTicket)
        
        # 过滤条件
        if status:
            query = query.filter(AfterSalesTicket.status == status)
        if ticket_type:
            query = query.filter(AfterSalesTicket.ticket_type == ticket_type)
        if priority:
            query = query.filter(AfterSalesTicket.priority == priority)
        if customer_id:
            query = query.filter(AfterSalesTicket.customer_id == customer_id)
        
        # 总数
        total = query.count()
        
        # 分页
        tickets = query.order_by(desc(AfterSalesTicket.reported_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "success": True,
            "tickets": [self._ticket_to_dict(t) for t in tickets],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def update_ticket(
        self,
        ticket_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新工单"""
        ticket = self.db.query(AfterSalesTicket).filter(
            AfterSalesTicket.id == ticket_id
        ).first()
        
        if not ticket:
            return {"success": False, "error": "工单不存在"}
        
        try:
            # 更新字段
            if 'status' in update_data:
                ticket.status = update_data['status']
                if update_data['status'] == 'resolved':
                    ticket.resolved_at = datetime.utcnow()
            
            if 'priority' in update_data:
                ticket.priority = update_data['priority']
            if 'assigned_to' in update_data:
                ticket.assigned_to = update_data['assigned_to']
            if 'resolution' in update_data:
                ticket.resolution = update_data['resolution']
            if 'customer_satisfaction' in update_data:
                ticket.customer_satisfaction = update_data['customer_satisfaction']
            
            ticket.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(ticket)
            
            return {
                "success": True,
                "ticket": self._ticket_to_dict(ticket)
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 客户投诉管理 ============
    
    def create_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建客户投诉"""
        try:
            complaint_number = self._generate_complaint_number()
            
            complaint = CustomerComplaint(
                complaint_number=complaint_number,
                ticket_id=complaint_data.get('ticket_id'),
                customer_id=complaint_data['customer_id'],
                order_id=complaint_data.get('order_id'),
                complaint_type=complaint_data['complaint_type'],
                severity=complaint_data.get('severity', 'medium'),
                description=complaint_data['description'],
                expected_resolution=complaint_data.get('expected_resolution'),
                status='pending',
                reported_at=datetime.utcnow()
            )
            
            self.db.add(complaint)
            self.db.commit()
            self.db.refresh(complaint)
            
            return {
                "success": True,
                "complaint": self._complaint_to_dict(complaint)
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_complaints(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        complaint_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取投诉列表"""
        query = self.db.query(CustomerComplaint)
        
        if status:
            query = query.filter(CustomerComplaint.status == status)
        if severity:
            query = query.filter(CustomerComplaint.severity == severity)
        if complaint_type:
            query = query.filter(CustomerComplaint.complaint_type == complaint_type)
        
        total = query.count()
        complaints = query.order_by(desc(CustomerComplaint.reported_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "success": True,
            "complaints": [self._complaint_to_dict(c) for c in complaints],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    # ============ 维修记录管理 ============
    
    def create_repair_record(self, repair_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建维修记录"""
        try:
            repair_number = self._generate_repair_number()
            
            repair = RepairRecord(
                repair_number=repair_number,
                ticket_id=repair_data['ticket_id'],
                order_id=repair_data.get('order_id'),
                product_name=repair_data['product_name'],
                product_code=repair_data.get('product_code'),
                serial_number=repair_data.get('serial_number'),
                issue_description=repair_data['issue_description'],
                repair_type=repair_data.get('repair_type', 'warranty'),
                repair_status='pending',
                technician=repair_data.get('technician'),
                repair_start_date=repair_data.get('repair_start_date'),
                repair_cost=repair_data.get('repair_cost', 0),
                parts_cost=repair_data.get('parts_cost', 0),
                labor_cost=repair_data.get('labor_cost', 0),
                warranty_status=repair_data.get('warranty_status', 'in_warranty')
            )
            
            self.db.add(repair)
            self.db.commit()
            self.db.refresh(repair)
            
            return {
                "success": True,
                "repair": self._repair_to_dict(repair)
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_repair_records(
        self,
        repair_status: Optional[str] = None,
        repair_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取维修记录列表"""
        query = self.db.query(RepairRecord)
        
        if repair_status:
            query = query.filter(RepairRecord.repair_status == repair_status)
        if repair_type:
            query = query.filter(RepairRecord.repair_type == repair_type)
        
        total = query.count()
        repairs = query.order_by(desc(RepairRecord.repair_start_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "success": True,
            "repairs": [self._repair_to_dict(r) for r in repairs],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    # ============ 退换货管理 ============
    
    def create_return_record(self, return_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建退换货记录"""
        try:
            return_number = self._generate_return_number()
            
            return_record = ReturnRecord(
                return_number=return_number,
                ticket_id=return_data['ticket_id'],
                order_id=return_data['order_id'],
                return_type=return_data['return_type'],
                reason=return_data['reason'],
                product_name=return_data['product_name'],
                product_code=return_data.get('product_code'),
                quantity=return_data['quantity'],
                return_amount=return_data['return_amount'],
                return_status='pending',
                requested_date=return_data.get('requested_date', date.today()),
                return_address=return_data.get('return_address')
            )
            
            self.db.add(return_record)
            self.db.commit()
            self.db.refresh(return_record)
            
            return {
                "success": True,
                "return_record": self._return_to_dict(return_record)
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_return_records(
        self,
        return_status: Optional[str] = None,
        return_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取退换货记录列表"""
        query = self.db.query(ReturnRecord)
        
        if return_status:
            query = query.filter(ReturnRecord.return_status == return_status)
        if return_type:
            query = query.filter(ReturnRecord.return_type == return_type)
        
        total = query.count()
        returns = query.order_by(desc(ReturnRecord.requested_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "success": True,
            "returns": [self._return_to_dict(r) for r in returns],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    # ============ 售后数据分析 ============
    
    def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取售后统计数据"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
        
        # 工单统计
        tickets_query = self.db.query(AfterSalesTicket).filter(
            func.date(AfterSalesTicket.reported_at) >= start_date,
            func.date(AfterSalesTicket.reported_at) <= end_date
        )
        
        total_tickets = tickets_query.count()
        open_tickets = tickets_query.filter(
            AfterSalesTicket.status == 'open'
        ).count()
        resolved_tickets = tickets_query.filter(
            AfterSalesTicket.status == 'resolved'
        ).count()
        
        # 按类型统计
        tickets_by_type = self.db.query(
            AfterSalesTicket.ticket_type,
            func.count(AfterSalesTicket.id)
        ).filter(
            func.date(AfterSalesTicket.reported_at) >= start_date,
            func.date(AfterSalesTicket.reported_at) <= end_date
        ).group_by(AfterSalesTicket.ticket_type).all()
        
        # 投诉统计
        complaints_query = self.db.query(CustomerComplaint).filter(
            func.date(CustomerComplaint.reported_at) >= start_date,
            func.date(CustomerComplaint.reported_at) <= end_date
        )
        total_complaints = complaints_query.count()
        
        # 维修统计
        repairs_query = self.db.query(RepairRecord).filter(
            RepairRecord.repair_start_date >= start_date,
            RepairRecord.repair_start_date <= end_date
        )
        total_repairs = repairs_query.count()
        completed_repairs = repairs_query.filter(
            RepairRecord.repair_status == 'completed'
        ).count()
        
        # 退换货统计
        returns_query = self.db.query(ReturnRecord).filter(
            ReturnRecord.requested_date >= start_date,
            ReturnRecord.requested_date <= end_date
        )
        total_returns = returns_query.count()
        total_return_amount = self.db.query(
            func.sum(ReturnRecord.return_amount)
        ).filter(
            ReturnRecord.requested_date >= start_date,
            ReturnRecord.requested_date <= end_date
        ).scalar() or 0
        
        # 平均满意度
        avg_satisfaction = self.db.query(
            func.avg(AfterSalesTicket.customer_satisfaction)
        ).filter(
            AfterSalesTicket.customer_satisfaction.isnot(None),
            func.date(AfterSalesTicket.resolved_at) >= start_date,
            func.date(AfterSalesTicket.resolved_at) <= end_date
        ).scalar() or 0
        
        return {
            "success": True,
            "statistics": {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "tickets": {
                    "total": total_tickets,
                    "open": open_tickets,
                    "resolved": resolved_tickets,
                    "by_type": {t[0]: t[1] for t in tickets_by_type}
                },
                "complaints": {
                    "total": total_complaints
                },
                "repairs": {
                    "total": total_repairs,
                    "completed": completed_repairs,
                    "completion_rate": (completed_repairs / total_repairs * 100) if total_repairs > 0 else 0
                },
                "returns": {
                    "total": total_returns,
                    "total_amount": float(total_return_amount)
                },
                "customer_satisfaction": {
                    "average": float(avg_satisfaction) if avg_satisfaction else 0
                }
            }
        }
    
    # ============ 辅助方法 ============
    
    def _generate_ticket_number(self) -> str:
        """生成工单编号"""
        count = self.db.query(func.count(AfterSalesTicket.id)).scalar()
        return f"AST{datetime.now().strftime('%Y%m%d')}{count + 1:06d}"
    
    def _generate_complaint_number(self) -> str:
        """生成投诉编号"""
        count = self.db.query(func.count(CustomerComplaint.id)).scalar()
        return f"COM{datetime.now().strftime('%Y%m%d')}{count + 1:06d}"
    
    def _generate_repair_number(self) -> str:
        """生成维修编号"""
        count = self.db.query(func.count(RepairRecord.id)).scalar()
        return f"REP{datetime.now().strftime('%Y%m%d')}{count + 1:06d}"
    
    def _generate_return_number(self) -> str:
        """生成退换货编号"""
        count = self.db.query(func.count(ReturnRecord.id)).scalar()
        return f"RET{datetime.now().strftime('%Y%m%d')}{count + 1:06d}"
    
    def _ticket_to_dict(self, ticket: AfterSalesTicket) -> Dict[str, Any]:
        """工单转字典"""
        return {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "order_id": ticket.order_id,
            "customer_id": ticket.customer_id,
            "ticket_type": ticket.ticket_type,
            "priority": ticket.priority,
            "status": ticket.status,
            "title": ticket.title,
            "description": ticket.description,
            "assigned_to": ticket.assigned_to,
            "reported_by": ticket.reported_by,
            "reported_at": ticket.reported_at.isoformat() if ticket.reported_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "resolution": ticket.resolution,
            "customer_satisfaction": ticket.customer_satisfaction,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None
        }
    
    def _complaint_to_dict(self, complaint: CustomerComplaint) -> Dict[str, Any]:
        """投诉转字典"""
        return {
            "id": complaint.id,
            "complaint_number": complaint.complaint_number,
            "ticket_id": complaint.ticket_id,
            "customer_id": complaint.customer_id,
            "order_id": complaint.order_id,
            "complaint_type": complaint.complaint_type,
            "severity": complaint.severity,
            "description": complaint.description,
            "expected_resolution": complaint.expected_resolution,
            "status": complaint.status,
            "reported_at": complaint.reported_at.isoformat() if complaint.reported_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "resolution": complaint.resolution,
            "resolved_by": complaint.resolved_by,
            "customer_feedback": complaint.customer_feedback
        }
    
    def _repair_to_dict(self, repair: RepairRecord) -> Dict[str, Any]:
        """维修记录转字典"""
        return {
            "id": repair.id,
            "repair_number": repair.repair_number,
            "ticket_id": repair.ticket_id,
            "order_id": repair.order_id,
            "product_name": repair.product_name,
            "product_code": repair.product_code,
            "serial_number": repair.serial_number,
            "issue_description": repair.issue_description,
            "repair_type": repair.repair_type,
            "repair_status": repair.repair_status,
            "technician": repair.technician,
            "repair_start_date": repair.repair_start_date.isoformat() if repair.repair_start_date else None,
            "repair_end_date": repair.repair_end_date.isoformat() if repair.repair_end_date else None,
            "repair_cost": float(repair.repair_cost) if repair.repair_cost else 0,
            "parts_cost": float(repair.parts_cost) if repair.parts_cost else 0,
            "labor_cost": float(repair.labor_cost) if repair.labor_cost else 0,
            "warranty_status": repair.warranty_status
        }
    
    def _return_to_dict(self, return_record: ReturnRecord) -> Dict[str, Any]:
        """退换货记录转字典"""
        return {
            "id": return_record.id,
            "return_number": return_record.return_number,
            "ticket_id": return_record.ticket_id,
            "order_id": return_record.order_id,
            "return_type": return_record.return_type,
            "reason": return_record.reason,
            "product_name": return_record.product_name,
            "product_code": return_record.product_code,
            "quantity": float(return_record.quantity),
            "return_amount": float(return_record.return_amount),
            "return_status": return_record.return_status,
            "requested_date": return_record.requested_date.isoformat() if return_record.requested_date else None,
            "approved_date": return_record.approved_date.isoformat() if return_record.approved_date else None,
            "completed_date": return_record.completed_date.isoformat() if return_record.completed_date else None,
            "refund_status": return_record.refund_status,
            "refund_amount": float(return_record.refund_amount) if return_record.refund_amount else 0
        }


def get_after_sales_manager(db: Session) -> AfterSalesManager:
    """获取售后服务管理器实例"""
    return AfterSalesManager(db)


