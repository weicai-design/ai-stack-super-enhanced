"""
ERP与运营财务数据打通
实现ERP系统与运营管理、财务管理模块的数据同步
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.database_models import (
    FinancialData,
    Order,
    ProcessInstance,
    ProductionExecution,
    MaterialReceipt,
    Delivery,
    Payment,
    Customer,
    Project
)


class DataIntegrationService:
    """
    数据集成服务
    
    功能：
    1. ERP → 运营管理数据同步
    2. ERP → 财务管理数据同步
    3. 数据一致性保证
    4. 数据同步状态监控
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ ERP → 运营管理数据同步 ============
    
    async def sync_to_operations(
        self,
        sync_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        同步ERP数据到运营管理模块
        
        Args:
            sync_type: 同步类型（orders/processes/production/inventory）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步结果
        """
        try:
            if sync_type == "orders":
                return await self._sync_orders_to_operations(start_date, end_date)
            elif sync_type == "processes":
                return await self._sync_processes_to_operations(start_date, end_date)
            elif sync_type == "production":
                return await self._sync_production_to_operations(start_date, end_date)
            elif sync_type == "inventory":
                return await self._sync_inventory_to_operations(start_date, end_date)
            else:
                return {
                    "success": False,
                    "error": f"不支持的同步类型: {sync_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_orders_to_operations(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步订单数据到运营管理"""
        query = self.db.query(Order)
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        orders = query.all()
        
        operations_data = []
        for order in orders:
            operations_data.append({
                "order_id": order.id,
                "order_no": order.order_no,
                "customer_id": order.customer_id,
                "customer_name": order.customer_name,
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                "status": order.status,
                "total_amount": float(order.total_amount) if order.total_amount else 0,
                "items_count": len(order.items) if hasattr(order, 'items') else 0,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "orders",
            "count": len(operations_data),
            "data": operations_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_processes_to_operations(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步流程数据到运营管理"""
        query = self.db.query(ProcessInstance)
        
        if start_date:
            query = query.filter(ProcessInstance.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(ProcessInstance.created_at <= datetime.combine(end_date, datetime.max.time()))
        
        processes = query.all()
        
        operations_data = []
        for process in processes:
            operations_data.append({
                "process_id": process.id,
                "process_name": process.process_name,
                "status": process.status,
                "current_stage": process.current_stage,
                "progress": process.progress_percentage if hasattr(process, 'progress_percentage') else 0,
                "created_at": process.created_at.isoformat() if process.created_at else None,
                "updated_at": process.updated_at.isoformat() if process.updated_at else None,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "processes",
            "count": len(operations_data),
            "data": operations_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_production_to_operations(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步生产数据到运营管理"""
        query = self.db.query(ProductionExecution)
        
        if start_date:
            query = query.filter(ProductionExecution.start_date >= start_date)
        if end_date:
            query = query.filter(ProductionExecution.start_date <= end_date)
        
        productions = query.all()
        
        operations_data = []
        for production in productions:
            operations_data.append({
                "production_id": production.id,
                "order_id": production.order_id if hasattr(production, 'order_id') else None,
                "product_name": production.product_name if hasattr(production, 'product_name') else None,
                "quantity": float(production.quantity) if hasattr(production, 'quantity') else 0,
                "status": production.status if hasattr(production, 'status') else None,
                "start_date": production.start_date.isoformat() if hasattr(production, 'start_date') and production.start_date else None,
                "end_date": production.end_date.isoformat() if hasattr(production, 'end_date') and production.end_date else None,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "production",
            "count": len(operations_data),
            "data": operations_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_inventory_to_operations(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步库存数据到运营管理"""
        from core.database_models import Inventory
        
        query = self.db.query(Inventory)
        
        if start_date:
            query = query.filter(Inventory.last_updated >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Inventory.last_updated <= datetime.combine(end_date, datetime.max.time()))
        
        inventories = query.all()
        
        operations_data = []
        for inventory in inventories:
            operations_data.append({
                "inventory_id": inventory.id,
                "material_name": inventory.material_name if hasattr(inventory, 'material_name') else None,
                "quantity": float(inventory.quantity) if hasattr(inventory, 'quantity') else 0,
                "warehouse_id": inventory.warehouse_id if hasattr(inventory, 'warehouse_id') else None,
                "last_updated": inventory.last_updated.isoformat() if hasattr(inventory, 'last_updated') and inventory.last_updated else None,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "inventory",
            "count": len(operations_data),
            "data": operations_data,
            "sync_time": datetime.now().isoformat()
        }
    
    # ============ ERP → 财务管理数据同步 ============
    
    async def sync_to_finance(
        self,
        sync_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        同步ERP数据到财务管理模块
        
        Args:
            sync_type: 同步类型（revenue/expense/payment/invoice）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步结果
        """
        try:
            if sync_type == "revenue":
                return await self._sync_revenue_to_finance(start_date, end_date)
            elif sync_type == "expense":
                return await self._sync_expense_to_finance(start_date, end_date)
            elif sync_type == "payment":
                return await self._sync_payment_to_finance(start_date, end_date)
            elif sync_type == "invoice":
                return await self._sync_invoice_to_finance(start_date, end_date)
            else:
                return {
                    "success": False,
                    "error": f"不支持的同步类型: {sync_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_revenue_to_finance(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步收入数据到财务管理"""
        query = self.db.query(Order)
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        orders = query.filter(Order.status.in_(["completed", "delivered"])).all()
        
        finance_data = []
        total_revenue = 0
        
        for order in orders:
            amount = float(order.total_amount) if order.total_amount else 0
            total_revenue += amount
            
            finance_data.append({
                "source": "order",
                "source_id": order.id,
                "source_no": order.order_no,
                "date": order.order_date.isoformat() if order.order_date else None,
                "amount": amount,
                "category": "revenue",
                "subcategory": "sales",
                "description": f"订单收入: {order.order_no}",
                "customer_id": order.customer_id,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "revenue",
            "count": len(finance_data),
            "total_amount": total_revenue,
            "data": finance_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_expense_to_finance(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步支出数据到财务管理"""
        from core.database_models import ProcurementPlan, MaterialReceipt
        
        # 同步采购支出
        procurement_query = self.db.query(ProcurementPlan)
        if start_date:
            procurement_query = procurement_query.filter(ProcurementPlan.plan_date >= start_date)
        if end_date:
            procurement_query = procurement_query.filter(ProcurementPlan.plan_date <= end_date)
        
        procurements = procurement_query.filter(ProcurementPlan.status == "completed").all()
        
        finance_data = []
        total_expense = 0
        
        for procurement in procurements:
            amount = float(procurement.total_amount) if hasattr(procurement, 'total_amount') and procurement.total_amount else 0
            total_expense += amount
            
            finance_data.append({
                "source": "procurement",
                "source_id": procurement.id,
                "source_no": procurement.plan_no if hasattr(procurement, 'plan_no') else None,
                "date": procurement.plan_date.isoformat() if hasattr(procurement, 'plan_date') and procurement.plan_date else None,
                "amount": amount,
                "category": "expense",
                "subcategory": "procurement",
                "description": f"采购支出: {procurement.plan_no if hasattr(procurement, 'plan_no') else procurement.id}",
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "expense",
            "count": len(finance_data),
            "total_amount": total_expense,
            "data": finance_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_payment_to_finance(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步回款数据到财务管理"""
        query = self.db.query(Payment)
        
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        
        payments = query.all()
        
        finance_data = []
        total_amount = 0
        
        for payment in payments:
            amount = float(payment.amount) if payment.amount else 0
            total_amount += amount
            
            finance_data.append({
                "source": "payment",
                "source_id": payment.id,
                "source_no": payment.payment_no if hasattr(payment, 'payment_no') else None,
                "date": payment.payment_date.isoformat() if payment.payment_date else None,
                "amount": amount,
                "category": "revenue",
                "subcategory": "payment",
                "description": f"客户回款: {payment.payment_no if hasattr(payment, 'payment_no') else payment.id}",
                "order_id": payment.order_id if hasattr(payment, 'order_id') else None,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "payment",
            "count": len(finance_data),
            "total_amount": total_amount,
            "data": finance_data,
            "sync_time": datetime.now().isoformat()
        }
    
    async def _sync_invoice_to_finance(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> Dict[str, Any]:
        """同步发票数据到财务管理"""
        # 从订单中提取发票信息
        query = self.db.query(Order)
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)
        
        orders = query.filter(Order.status.in_(["completed", "delivered"])).all()
        
        finance_data = []
        total_amount = 0
        
        for order in orders:
            # 假设订单有发票号字段
            invoice_no = getattr(order, 'invoice_no', None) or f"INV-{order.order_no}"
            amount = float(order.total_amount) if order.total_amount else 0
            total_amount += amount
            
            finance_data.append({
                "source": "invoice",
                "source_id": order.id,
                "source_no": invoice_no,
                "invoice_no": invoice_no,
                "date": order.order_date.isoformat() if order.order_date else None,
                "amount": amount,
                "category": "revenue",
                "subcategory": "invoice",
                "description": f"发票: {invoice_no}",
                "order_id": order.id,
                "customer_id": order.customer_id,
                "sync_time": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "sync_type": "invoice",
            "count": len(finance_data),
            "total_amount": total_amount,
            "data": finance_data,
            "sync_time": datetime.now().isoformat()
        }
    
    # ============ 数据一致性检查 ============
    
    async def check_data_consistency(
        self,
        check_type: str = "all"
    ) -> Dict[str, Any]:
        """
        检查数据一致性
        
        Args:
            check_type: 检查类型（all/orders/finance/processes）
            
        Returns:
            一致性检查结果
        """
        results = {
            "success": True,
            "checks": [],
            "issues": [],
            "check_time": datetime.now().isoformat()
        }
        
        if check_type in ["all", "orders"]:
            order_check = await self._check_orders_consistency()
            results["checks"].append(order_check)
            if not order_check.get("consistent", True):
                results["issues"].extend(order_check.get("issues", []))
        
        if check_type in ["all", "finance"]:
            finance_check = await self._check_finance_consistency()
            results["checks"].append(finance_check)
            if not finance_check.get("consistent", True):
                results["issues"].extend(finance_check.get("issues", []))
        
        if check_type in ["all", "processes"]:
            process_check = await self._check_processes_consistency()
            results["checks"].append(process_check)
            if not process_check.get("consistent", True):
                results["issues"].extend(process_check.get("issues", []))
        
        results["consistent"] = len(results["issues"]) == 0
        
        return results
    
    async def _check_orders_consistency(self) -> Dict[str, Any]:
        """检查订单数据一致性"""
        issues = []
        
        # 检查订单金额是否一致
        orders = self.db.query(Order).all()
        for order in orders:
            if order.total_amount and order.total_amount < 0:
                issues.append({
                    "type": "negative_amount",
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "amount": float(order.total_amount)
                })
        
        return {
            "type": "orders",
            "consistent": len(issues) == 0,
            "issues": issues
        }
    
    async def _check_finance_consistency(self) -> Dict[str, Any]:
        """检查财务数据一致性"""
        issues = []
        
        # 检查财务数据是否与订单数据一致
        orders = self.db.query(Order).filter(Order.status == "completed").all()
        total_order_amount = sum(float(o.total_amount) if o.total_amount else 0 for o in orders)
        
        financial_data = self.db.query(FinancialData).filter(
            FinancialData.category == FinancialCategory.REVENUE.value
        ).all()
        total_finance_amount = sum(float(f.amount) if f.amount else 0 for f in financial_data)
        
        if abs(total_order_amount - total_finance_amount) > 1000:  # 允许1000的误差
            issues.append({
                "type": "amount_mismatch",
                "order_total": total_order_amount,
                "finance_total": total_finance_amount,
                "difference": abs(total_order_amount - total_finance_amount)
            })
        
        return {
            "type": "finance",
            "consistent": len(issues) == 0,
            "issues": issues
        }
    
    async def _check_processes_consistency(self) -> Dict[str, Any]:
        """检查流程数据一致性"""
        issues = []
        
        # 检查流程状态是否合理
        processes = self.db.query(ProcessInstance).all()
        for process in processes:
            if hasattr(process, 'progress_percentage'):
                if process.progress_percentage < 0 or process.progress_percentage > 100:
                    issues.append({
                        "type": "invalid_progress",
                        "process_id": process.id,
                        "progress": process.progress_percentage
                    })
        
        return {
            "type": "processes",
            "consistent": len(issues) == 0,
            "issues": issues
        }
    
    # ============ 批量同步 ============
    
    async def batch_sync_to_operations(
        self,
        sync_types: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        批量同步多个类型的数据到运营管理
        
        Args:
            sync_types: 同步类型列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            批量同步结果
        """
        results = {}
        total_count = 0
        
        for sync_type in sync_types:
            result = await self.sync_to_operations(sync_type, start_date, end_date)
            results[sync_type] = result
            if result.get("success"):
                total_count += result.get("count", 0)
        
        return {
            "success": True,
            "sync_types": sync_types,
            "results": results,
            "total_count": total_count,
            "sync_time": datetime.now().isoformat()
        }
    
    async def batch_sync_to_finance(
        self,
        sync_types: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        auto_create: bool = False
    ) -> Dict[str, Any]:
        """
        批量同步多个类型的数据到财务管理
        
        Args:
            sync_types: 同步类型列表
            start_date: 开始日期
            end_date: 结束日期
            auto_create: 是否自动创建财务数据
            
        Returns:
            批量同步结果
        """
        results = {}
        total_amount = 0
        created_count = 0
        
        for sync_type in sync_types:
            result = await self.sync_to_finance(sync_type, start_date, end_date)
            results[sync_type] = result
            
            if result.get("success"):
                total_amount += result.get("total_amount", 0)
                
                # 如果设置了自动创建，将数据写入财务表
                if auto_create:
                    from core.database_models import FinancialData, FinancialCategory, PeriodType
                    
                    for item in result.get("data", []):
                        try:
                            financial_data = FinancialData(
                                date=datetime.fromisoformat(item["date"]).date() if item.get("date") else date.today(),
                                period_type=PeriodType.DAILY.value,
                                category=item.get("category", FinancialCategory.REVENUE.value),
                                subcategory=item.get("subcategory"),
                                amount=item.get("amount", 0),
                                description=item.get("description"),
                                source_document=item.get("source_no")
                            )
                            self.db.add(financial_data)
                            created_count += 1
                        except Exception as e:
                            continue
            
            if auto_create and created_count > 0:
                self.db.commit()
        
        return {
            "success": True,
            "sync_types": sync_types,
            "results": results,
            "total_amount": total_amount,
            "auto_created": created_count,
            "sync_time": datetime.now().isoformat()
        }
    
    # ============ 同步历史记录 ============
    
    async def get_sync_history(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取同步历史记录
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            同步历史记录列表
        """
        # TODO: 实现同步历史记录存储和查询
        # 这里返回模拟数据，实际应该从数据库查询
        return [
            {
                "sync_id": f"sync_{datetime.now().timestamp()}",
                "sync_type": "orders",
                "target_module": "operations",
                "count": 100,
                "sync_time": datetime.now().isoformat(),
                "status": "success"
            }
        ]
    
    # ============ 数据同步监控 ============
    
    async def get_sync_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取数据同步统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            同步统计信息
        """
        stats = {
            "operations_sync": {
                "orders": 0,
                "processes": 0,
                "production": 0,
                "inventory": 0
            },
            "finance_sync": {
                "revenue": 0,
                "expense": 0,
                "payment": 0,
                "invoice": 0
            },
            "total_sync_count": 0,
            "last_sync_time": None
        }
        
        # 统计各类型同步数量
        for sync_type in ["orders", "processes", "production", "inventory"]:
            result = await self.sync_to_operations(sync_type, start_date, end_date)
            if result.get("success"):
                stats["operations_sync"][sync_type] = result.get("count", 0)
                stats["total_sync_count"] += result.get("count", 0)
        
        for sync_type in ["revenue", "expense", "payment", "invoice"]:
            result = await self.sync_to_finance(sync_type, start_date, end_date)
            if result.get("success"):
                stats["finance_sync"][sync_type] = result.get("count", 0)
                stats["total_sync_count"] += result.get("count", 0)
        
        stats["last_sync_time"] = datetime.now().isoformat()
        
        return stats

