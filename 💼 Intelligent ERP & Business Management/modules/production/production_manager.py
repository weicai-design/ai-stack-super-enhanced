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
    
    def __init__(self, db_session: Session, data_listener=None):
        """
        初始化生产管理器
        
        Args:
            db_session: 数据库会话
            data_listener: ERP数据监听器（可选，用于自动发布事件）
        """
        self.db = db_session
        self.data_listener = data_listener
    
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
            
            # 自动发布生产计划创建事件
            if self.data_listener:
                try:
                    import asyncio
                    plan_dict = self._plan_to_dict(plan)
                    plan_dict["status"] = plan.status
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.data_listener.on_production_status_changed(
                                    str(plan.id), "", plan.status, plan_dict
                                )
                            )
                        else:
                            loop.run_until_complete(
                                self.data_listener.on_production_status_changed(
                                    str(plan.id), "", plan.status, plan_dict
                                )
                            )
                    except RuntimeError:
                        asyncio.run(
                            self.data_listener.on_production_status_changed(
                                str(plan.id), "", plan.status, plan_dict
                            )
                        )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"生产计划创建事件发布失败: {e}")
            
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
            
            # 自动发布生产状态变化事件
            if self.data_listener:
                try:
                    import asyncio
                    plan_dict = self._plan_to_dict(plan)
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(
                                self.data_listener.on_production_status_changed(
                                    str(plan_id), old_status, new_status, plan_dict
                                )
                            )
                        else:
                            loop.run_until_complete(
                                self.data_listener.on_production_status_changed(
                                    str(plan_id), old_status, new_status, plan_dict
                                )
                            )
                    except RuntimeError:
                        asyncio.run(
                            self.data_listener.on_production_status_changed(
                                str(plan_id), old_status, new_status, plan_dict
                            )
                        )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"生产状态变化事件发布失败: {e}")
            
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
    
    # ============ 高级功能（新增）============
    
    def production_capacity_load_analysis(self) -> Dict[str, Any]:
        """
        产能负载分析（新功能）
        
        分析当前生产负载情况，识别产能瓶颈
        """
        try:
            # 获取进行中和计划中的生产任务
            active_plans = self.db.query(ProductionPlan).filter(
                ProductionPlan.status.in_(['计划中', '生产中'])
            ).all()
            
            # 假设每天标准产能为100单位
            daily_capacity = 100
            
            # 按日期分组统计负载
            from collections import defaultdict
            daily_load = defaultdict(float)
            
            for plan in active_plans:
                if not plan.plan_start_date or not plan.plan_end_date:
                    continue
                
                # 计算每日生产量
                days = (plan.plan_end_date - plan.plan_start_date).days + 1
                daily_production = plan.quantity / days if days > 0 else plan.quantity
                
                # 填充每一天的负载
                current = plan.plan_start_date
                while current <= plan.plan_end_date:
                    daily_load[current.isoformat()] += daily_production
                    current += timedelta(days=1)
            
            # 识别负载过高的日期
            overload_dates = []
            high_load_dates = []
            
            for date_str, load in daily_load.items():
                load_percentage = (load / daily_capacity * 100)
                
                if load_percentage > 100:
                    overload_dates.append({
                        "date": date_str,
                        "load": round(load, 2),
                        "capacity": daily_capacity,
                        "load_percentage": round(load_percentage, 2),
                        "overload_amount": round(load - daily_capacity, 2),
                        "severity": "高" if load_percentage > 150 else "中"
                    })
                elif load_percentage > 80:
                    high_load_dates.append({
                        "date": date_str,
                        "load": round(load, 2),
                        "load_percentage": round(load_percentage, 2)
                    })
            
            # 平均负载率
            avg_load = sum(daily_load.values()) / len(daily_load) if daily_load else 0
            avg_load_percentage = (avg_load / daily_capacity * 100)
            
            # 负载状态评估
            if avg_load_percentage > 100:
                load_status = "严重超负荷"
                health = "差"
            elif avg_load_percentage > 80:
                load_status = "高负载"
                health = "一般"
            elif avg_load_percentage > 50:
                load_status = "正常负载"
                health = "良好"
            else:
                load_status = "低负载"
                health = "优秀"
            
            # 建议
            recommendations = []
            if len(overload_dates) > 0:
                recommendations.append(f"发现{len(overload_dates)}天产能超负荷，建议：1)调整生产计划 2)增加班次 3)外包部分订单")
            if avg_load_percentage > 90:
                recommendations.append("平均负载率过高，建议扩充产能或优化排产")
            if avg_load_percentage < 50:
                recommendations.append("产能利用率偏低，可以接受更多订单")
            
            return {
                "success": True,
                "capacity_analysis": {
                    "daily_standard_capacity": daily_capacity,
                    "average_daily_load": round(avg_load, 2),
                    "average_load_percentage": round(avg_load_percentage, 2),
                    "load_status": load_status,
                    "health_rating": health
                },
                "overload_dates": overload_dates[:10],  # 前10天
                "high_load_dates": high_load_dates[:10],
                "statistics": {
                    "total_days_analyzed": len(daily_load),
                    "overload_days_count": len(overload_dates),
                    "high_load_days_count": len(high_load_dates)
                },
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def intelligent_production_scheduling(self, days: int = 30) -> Dict[str, Any]:
        """
        智能排产算法（新功能）
        
        基于订单优先级、产能约束、交付日期自动生成最优生产排期
        """
        try:
            # 获取待排产的订单（已确认但未生产）
            pending_orders = self.db.query(Order).filter(
                Order.status == '已确认'
            ).all()
            
            if not pending_orders:
                return {
                    "success": True,
                    "message": "暂无待排产订单",
                    "schedule": []
                }
            
            # 假设产能参数
            daily_capacity = 100  # 每日产能
            
            # 为订单计算优先级（简化：使用交付日期和金额）
            order_list = []
            for order in pending_orders:
                # 计算紧急度
                if order.delivery_date:
                    urgency = max(1, (order.delivery_date - datetime.now()).days)
                else:
                    urgency = 30  # 默认30天
                
                order_list.append({
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                    "urgency_days": urgency,
                    "amount": float(order.order_amount) if order.order_amount else 0,
                    "estimated_production_days": 5,  # 简化：假设每个订单需要5天
                    "priority_score": (float(order.order_amount) if order.order_amount else 0) / urgency
                })
            
            # 按优先级排序
            order_list.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # 生成排产计划
            schedule = []
            current_date = datetime.now()
            
            for i, order_info in enumerate(order_list[:days], 1):
                start_date = current_date + timedelta(days=(i-1)*order_info['estimated_production_days'])
                end_date = start_date + timedelta(days=order_info['estimated_production_days'])
                
                # 检查是否会延期
                delivery_date = datetime.fromisoformat(order_info['delivery_date']) if order_info['delivery_date'] else None
                will_delay = delivery_date and end_date.date() > delivery_date.date() if delivery_date else False
                
                schedule.append({
                    "sequence": i,
                    "order_id": order_info["order_id"],
                    "order_number": order_info["order_number"],
                    "scheduled_start": start_date.date().isoformat(),
                    "scheduled_end": end_date.date().isoformat(),
                    "delivery_date": order_info["delivery_date"],
                    "estimated_days": order_info["estimated_production_days"],
                    "priority_score": round(order_info["priority_score"], 2),
                    "will_delay": will_delay,
                    "alert": "⚠️ 可能延期" if will_delay else "✓ 按时交付"
                })
            
            # 统计
            delay_count = sum(1 for s in schedule if s["will_delay"])
            
            return {
                "success": True,
                "schedule_period_days": days,
                "total_orders_scheduled": len(schedule),
                "production_schedule": schedule,
                "statistics": {
                    "on_time_orders": len(schedule) - delay_count,
                    "potential_delays": delay_count,
                    "on_time_rate": round(((len(schedule) - delay_count) / len(schedule) * 100), 2) if schedule else 0
                },
                "recommendations": [
                    "优先执行高优先级订单",
                    "关注标记为'可能延期'的订单",
                    "根据实际情况动态调整排期"
                ] + (["有订单可能延期，建议增加产能或调整交付日期"] if delay_count > 0 else []),
                "schedule_generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def production_efficiency_optimization(self) -> Dict[str, Any]:
        """
        生产效率优化分析（新功能）
        
        识别生产过程中的效率问题并提供优化建议
        """
        try:
            # 获取已完成的生产计划
            completed_plans = self.db.query(ProductionPlan).filter(
                ProductionPlan.status == '已完成',
                ProductionPlan.plan_start_date.isnot(None),
                ProductionPlan.plan_end_date.isnot(None),
                ProductionPlan.actual_end_date.isnot(None)
            ).all()
            
            if not completed_plans:
                return {
                    "success": True,
                    "message": "暂无已完成的生产计划",
                    "efficiency_score": 0
                }
            
            efficiency_issues = []
            total_efficiency_score = 0
            
            for plan in completed_plans:
                # 计算时间效率
                planned_days = (plan.plan_end_date - plan.plan_start_date).days + 1
                actual_days = (plan.actual_end_date.date() - plan.plan_start_date).days + 1
                time_efficiency = (planned_days / actual_days * 100) if actual_days > 0 else 100
                
                # 计算数量效率
                quantity_efficiency = (plan.actual_quantity / plan.quantity * 100) if plan.quantity > 0 and plan.actual_quantity else 100
                
                # 综合效率
                overall_efficiency = (time_efficiency * 0.5 + quantity_efficiency * 0.5)
                total_efficiency_score += overall_efficiency
                
                # 识别低效率生产
                if overall_efficiency < 80:
                    efficiency_issues.append({
                        "plan_id": plan.id,
                        "product_name": plan.product_name,
                        "time_efficiency": round(time_efficiency, 2),
                        "quantity_efficiency": round(quantity_efficiency, 2),
                        "overall_efficiency": round(overall_efficiency, 2),
                        "issue": "生产效率低于80%",
                        "planned_days": planned_days,
                        "actual_days": actual_days,
                        "delay_days": actual_days - planned_days
                    })
            
            # 平均效率
            avg_efficiency = total_efficiency_score / len(completed_plans) if completed_plans else 0
            
            # 效率等级
            if avg_efficiency >= 95:
                efficiency_rating = "优秀"
                grade = "A+"
            elif avg_efficiency >= 85:
                efficiency_rating = "良好"
                grade = "A"
            elif avg_efficiency >= 75:
                efficiency_rating = "一般"
                grade = "B"
            else:
                efficiency_rating = "偏低"
                grade = "C"
            
            # 优化建议
            optimization_suggestions = []
            
            if avg_efficiency < 85:
                optimization_suggestions.append({
                    "area": "整体效率",
                    "current": f"{avg_efficiency:.1f}%",
                    "target": "≥85%",
                    "suggestions": [
                        "分析低效率生产计划的共同原因",
                        "优化生产流程，减少等待时间",
                        "加强员工培训，提高技能水平",
                        "引入自动化设备提升效率"
                    ],
                    "priority": "高"
                })
            
            if len(efficiency_issues) > 5:
                optimization_suggestions.append({
                    "area": "低效率生产",
                    "current": f"{len(efficiency_issues)}个低效率计划",
                    "target": "≤3个",
                    "suggestions": [
                        "重点分析这些生产计划",
                        "找出共性问题",
                        "制定针对性改进措施"
                    ],
                    "priority": "中"
                })
            
            # 计算各效率区间分布
            efficiency_distribution = {
                "excellent_90_plus": sum(1 for p in completed_plans if self._calculate_plan_efficiency(p) >= 90),
                "good_80_to_90": sum(1 for p in completed_plans if 80 <= self._calculate_plan_efficiency(p) < 90),
                "average_70_to_80": sum(1 for p in completed_plans if 70 <= self._calculate_plan_efficiency(p) < 80),
                "poor_below_70": sum(1 for p in completed_plans if self._calculate_plan_efficiency(p) < 70)
            }
            
            return {
                "success": True,
                "efficiency_metrics": {
                    "total_plans_analyzed": len(completed_plans),
                    "average_efficiency": round(avg_efficiency, 2),
                    "efficiency_rating": efficiency_rating,
                    "grade": grade
                },
                "efficiency_distribution": efficiency_distribution,
                "low_efficiency_plans": efficiency_issues[:10],
                "low_efficiency_count": len(efficiency_issues),
                "optimization_suggestions": optimization_suggestions,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def production_abnormal_detection(self) -> Dict[str, Any]:
        """
        生产异常检测（新功能）
        
        自动检测生产过程中的各类异常
        """
        try:
            all_plans = self.db.query(ProductionPlan).all()
            
            abnormalities = {
                "delayed_production": [],
                "low_yield": [],
                "long_duration": [],
                "status_stuck": []
            }
            
            for plan in all_plans:
                # 1. 检测生产延期
                if plan.status == '生产中' and plan.plan_end_date:
                    if datetime.now().date() > plan.plan_end_date:
                        days_delayed = (datetime.now().date() - plan.plan_end_date).days
                        abnormalities["delayed_production"].append({
                            "plan_id": plan.id,
                            "product_name": plan.product_name,
                            "days_delayed": days_delayed,
                            "planned_end": plan.plan_end_date.isoformat(),
                            "severity": "高" if days_delayed > 5 else "中"
                        })
                
                # 2. 检测产出率低
                if plan.status == '已完成' and plan.actual_quantity and plan.quantity:
                    yield_rate = (plan.actual_quantity / plan.quantity * 100)
                    if yield_rate < 90:
                        abnormalities["low_yield"].append({
                            "plan_id": plan.id,
                            "product_name": plan.product_name,
                            "planned_quantity": plan.quantity,
                            "actual_quantity": plan.actual_quantity,
                            "yield_rate": round(yield_rate, 2),
                            "shortage": plan.quantity - plan.actual_quantity
                        })
                
                # 3. 检测生产周期过长
                if plan.status == '已完成' and plan.plan_start_date and plan.actual_end_date:
                    planned_duration = (plan.plan_end_date - plan.plan_start_date).days
                    actual_duration = (plan.actual_end_date.date() - plan.plan_start_date).days
                    
                    if actual_duration > planned_duration * 1.5:
                        abnormalities["long_duration"].append({
                            "plan_id": plan.id,
                            "product_name": plan.product_name,
                            "planned_days": planned_duration,
                            "actual_days": actual_duration,
                            "excess_days": actual_duration - planned_duration
                        })
                
                # 4. 检测状态停滞
                if plan.status == '生产中' and plan.updated_at:
                    days_no_update = (datetime.now() - plan.updated_at).days
                    if days_no_update > 7:
                        abnormalities["status_stuck"].append({
                            "plan_id": plan.id,
                            "product_name": plan.product_name,
                            "days_no_update": days_no_update,
                            "last_update": plan.updated_at.isoformat(),
                            "action": "检查生产进度并更新状态"
                        })
            
            total_abnormal = sum(len(v) for v in abnormalities.values())
            
            return {
                "success": True,
                "total_abnormalities": total_abnormal,
                "abnormalities": abnormalities,
                "statistics": {
                    "delayed_production": len(abnormalities["delayed_production"]),
                    "low_yield": len(abnormalities["low_yield"]),
                    "long_duration": len(abnormalities["long_duration"]),
                    "status_stuck": len(abnormalities["status_stuck"])
                },
                "requires_attention": len(abnormalities["delayed_production"]) + len(abnormalities["status_stuck"]),
                "detection_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_plan_efficiency(self, plan: ProductionPlan) -> float:
        """计算单个计划的效率"""
        if not plan.plan_start_date or not plan.plan_end_date:
            return 100
        
        if plan.status != '已完成' or not plan.actual_end_date:
            return 100
        
        planned_days = (plan.plan_end_date - plan.plan_start_date).days + 1
        actual_days = (plan.actual_end_date.date() - plan.plan_start_date).days + 1
        
        time_efficiency = (planned_days / actual_days * 100) if actual_days > 0 else 100
        quantity_efficiency = (plan.actual_quantity / plan.quantity * 100) if plan.quantity > 0 and plan.actual_quantity else 100
        
        return (time_efficiency * 0.5 + quantity_efficiency * 0.5)


# 工具函数
def get_production_manager(db_session: Session) -> ProductionManager:
    """获取生产管理器实例"""
    return ProductionManager(db_session)











