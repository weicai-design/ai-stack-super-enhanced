"""
生产管理模块
- 生产计划管理
- 生产执行跟踪
- 产能分析
- 物料需求计划（MRP）
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from decimal import Decimal
import sys
sys.path.append('../..')
from core.database_models import Order, ProductionPlan, Material


class ProductionManager:
    """生产管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============ 生产计划管理 ============
    
    def create_production_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建生产计划
        
        Args:
            plan_data: {
                "order_id": 订单ID,
                "product_name": "产品名称",
                "quantity": 数量,
                "plan_start_date": "计划开始日期",
                "plan_end_date": "计划完成日期",
                "status": "计划中/生产中/已完成"
            }
        """
        try:
            # 验证订单是否存在
            order = self.db.query(Order).filter(
                Order.id == plan_data['order_id']
            ).first()
            
            if not order:
                return {"success": False, "error": "订单不存在"}
            
            plan = ProductionPlan(
                order_id=plan_data['order_id'],
                product_name=plan_data['product_name'],
                quantity=plan_data['quantity'],
                plan_start_date=datetime.fromisoformat(plan_data['plan_start_date'])
                               if isinstance(plan_data.get('plan_start_date'), str)
                               else plan_data.get('plan_start_date'),
                plan_end_date=datetime.fromisoformat(plan_data['plan_end_date'])
                             if isinstance(plan_data.get('plan_end_date'), str)
                             else plan_data.get('plan_end_date'),
                status=plan_data.get('status', '计划中'),
                extra_metadata=plan_data.get('extra_metadata', {})
            )
            
            self.db.add(plan)
            self.db.commit()
            self.db.refresh(plan)
            
            # 自动生成物料需求计划
            mrp_result = self._generate_mrp(plan.id, plan_data['product_name'], plan_data['quantity'])
            
            return {
                "success": True,
                "plan": self._plan_to_dict(plan),
                "mrp": mrp_result,
                "message": "生产计划创建成功"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def list_production_plans(
        self,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取生产计划列表"""
        try:
            query = self.db.query(ProductionPlan)
            
            if status:
                query = query.filter(ProductionPlan.status == status)
            if start_date:
                query = query.filter(ProductionPlan.plan_start_date >= start_date)
            if end_date:
                query = query.filter(ProductionPlan.plan_end_date <= end_date)
            
            total = query.count()
            offset = (page - 1) * page_size
            plans = query.order_by(ProductionPlan.plan_start_date.desc())\
                        .offset(offset).limit(page_size).all()
            
            stats = self._get_production_statistics()
            
            return {
                "success": True,
                "plans": [self._plan_to_dict(p) for p in plans],
                "total": total,
                "page": page,
                "page_size": page_size,
                "statistics": stats
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_production_status(
        self,
        plan_id: int,
        new_status: str,
        actual_quantity: Optional[int] = None,
        note: str = ""
    ) -> Dict[str, Any]:
        """更新生产状态"""
        try:
            plan = self.db.query(ProductionPlan).filter(
                ProductionPlan.id == plan_id
            ).first()
            
            if not plan:
                return {"success": False, "error": "生产计划不存在"}
            
            old_status = plan.status
            plan.status = new_status
            
            if actual_quantity:
                plan.actual_quantity = actual_quantity
            
            # 记录状态变更
            if not plan.extra_metadata:
                plan.extra_metadata = {}
            
            if 'status_history' not in plan.extra_metadata:
                plan.extra_metadata['status_history'] = []
            
            plan.extra_metadata['status_history'].append({
                "from": old_status,
                "to": new_status,
                "note": note,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 如果完成，记录实际完成时间
            if new_status == '已完成' and not plan.actual_end_date:
                plan.actual_end_date = datetime.utcnow()
            
            plan.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(plan)
            
            return {
                "success": True,
                "plan": self._plan_to_dict(plan),
                "message": f"生产状态已更新为 {new_status}"
            }
        
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    # ============ 产能分析 ============
    
    def analyze_production_capacity(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        产能分析
        - 计划产能 vs 实际产能
        - 产能利用率
        - 瓶颈识别
        """
        try:
            # 获取最近数据
            if period == "month":
                start_date = datetime.utcnow() - timedelta(days=30)
            elif period == "quarter":
                start_date = datetime.utcnow() - timedelta(days=90)
            else:
                start_date = datetime.utcnow() - timedelta(days=365)
            
            plans = self.db.query(ProductionPlan).filter(
                ProductionPlan.plan_start_date >= start_date
            ).all()
            
            # 统计
            total_planned = sum(p.quantity for p in plans)
            total_actual = sum(p.actual_quantity for p in plans if p.actual_quantity)
            completed = sum(1 for p in plans if p.status == '已完成')
            
            utilization_rate = (total_actual / total_planned * 100) if total_planned > 0 else 0
            completion_rate = (completed / len(plans) * 100) if len(plans) > 0 else 0
            
            return {
                "success": True,
                "period": period,
                "analysis": {
                    "total_plans": len(plans),
                    "completed_plans": completed,
                    "total_planned_quantity": total_planned,
                    "total_actual_quantity": total_actual,
                    "capacity_utilization": float(utilization_rate),
                    "completion_rate": float(completion_rate)
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_production_efficiency(self) -> Dict[str, Any]:
        """生产效率分析"""
        try:
            # 获取已完成的生产计划
            completed = self.db.query(ProductionPlan).filter(
                ProductionPlan.status == '已完成',
                ProductionPlan.plan_end_date.isnot(None),
                ProductionPlan.actual_end_date.isnot(None)
            ).all()
            
            on_time = 0
            delayed = 0
            total_delay_days = 0
            
            for plan in completed:
                if plan.actual_end_date <= plan.plan_end_date:
                    on_time += 1
                else:
                    delayed += 1
                    delay_days = (plan.actual_end_date - plan.plan_end_date).days
                    total_delay_days += delay_days
            
            on_time_rate = (on_time / len(completed) * 100) if len(completed) > 0 else 0
            avg_delay = (total_delay_days / delayed) if delayed > 0 else 0
            
            return {
                "success": True,
                "analysis": {
                    "total_completed": len(completed),
                    "on_time": on_time,
                    "delayed": delayed,
                    "on_time_rate": float(on_time_rate),
                    "average_delay_days": float(avg_delay)
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============ 物料需求计划（MRP） ============
    
    def _generate_mrp(
        self,
        plan_id: int,
        product_name: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        生成物料需求计划
        
        根据产品BOM（物料清单）自动计算所需物料
        """
        try:
            # 这里简化处理，实际应该从BOM表读取
            # 示例：假设每个产品需要固定物料
            bom_template = {
                "默认产品": [
                    {"material_code": "MAT001", "material_name": "原材料A", "quantity_per_unit": 2},
                    {"material_code": "MAT002", "material_name": "原材料B", "quantity_per_unit": 1},
                ]
            }
            
            bom = bom_template.get(product_name, bom_template["默认产品"])
            
            mrp = []
            for item in bom:
                required_qty = item['quantity_per_unit'] * quantity
                
                # 检查库存
                material = self.db.query(Material).filter(
                    Material.code == item['material_code']
                ).first()
                
                current_stock = material.quantity if material else 0
                shortage = max(0, required_qty - current_stock)
                
                mrp.append({
                    "material_code": item['material_code'],
                    "material_name": item['material_name'],
                    "required_quantity": required_qty,
                    "current_stock": current_stock,
                    "shortage": shortage,
                    "need_purchase": shortage > 0
                })
            
            return {
                "success": True,
                "plan_id": plan_id,
                "product_name": product_name,
                "production_quantity": quantity,
                "mrp": mrp
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============ 内部辅助方法 ============
    
    def _plan_to_dict(self, plan: ProductionPlan) -> Dict[str, Any]:
        """生产计划对象转字典"""
        return {
            "id": plan.id,
            "order_id": plan.order_id,
            "product_name": plan.product_name,
            "quantity": plan.quantity,
            "actual_quantity": plan.actual_quantity,
            "plan_start_date": plan.plan_start_date.isoformat() if plan.plan_start_date else None,
            "plan_end_date": plan.plan_end_date.isoformat() if plan.plan_end_date else None,
            "actual_end_date": plan.actual_end_date.isoformat() if plan.actual_end_date else None,
            "status": plan.status,
            "extra_metadata": plan.extra_metadata,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
        }
    
    def _get_production_statistics(self) -> Dict[str, Any]:
        """生产统计"""
        total = self.db.query(ProductionPlan).count()
        planned = self.db.query(ProductionPlan).filter(
            ProductionPlan.status == '计划中'
        ).count()
        producing = self.db.query(ProductionPlan).filter(
            ProductionPlan.status == '生产中'
        ).count()
        completed = self.db.query(ProductionPlan).filter(
            ProductionPlan.status == '已完成'
        ).count()
        
        return {
            "total": total,
            "planned": planned,
            "producing": producing,
            "completed": completed
        }


# 临时添加缺失的数据模型
class ProductionPlan:
    """生产计划表（临时）"""
    pass


class Material:
    """物料表（临时）"""
    pass

