"""
质量管理模块
- 质量检验管理
- 不合格品处理
- 质量分析统计
- 质量改进跟踪
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal


class QualityManager:
    """质量管理器"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_inspection_record(self, inspection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建质检记录
        
        Args:
            inspection_data: {
                "production_plan_id": 生产计划ID,
                "product_name": "产品名称",
                "inspection_quantity": 检验数量,
                "qualified_quantity": 合格数量,
                "rejected_quantity": 不合格数量,
                "inspector": "检验员",
                "inspection_date": "检验日期",
                "defect_types": ["缺陷类型"],
                "note": "备注"
            }
        """
        try:
            qualified_rate = (inspection_data['qualified_quantity'] / 
                            inspection_data['inspection_quantity'] * 100) \
                            if inspection_data['inspection_quantity'] > 0 else 0
            
            record = {
                "id": self._generate_id(),
                "production_plan_id": inspection_data['production_plan_id'],
                "product_name": inspection_data['product_name'],
                "inspection_quantity": inspection_data['inspection_quantity'],
                "qualified_quantity": inspection_data['qualified_quantity'],
                "rejected_quantity": inspection_data['rejected_quantity'],
                "qualified_rate": float(qualified_rate),
                "inspector": inspection_data.get('inspector'),
                "inspection_date": inspection_data.get('inspection_date', datetime.utcnow().isoformat()),
                "defect_types": inspection_data.get('defect_types', []),
                "note": inspection_data.get('note', ''),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # 这里简化处理，实际应该存入数据库
            # 暂时返回成功
            
            return {
                "success": True,
                "inspection": record,
                "message": "质检记录已创建"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_quality_trend(
        self,
        period: str = "month",
        months: int = 6
    ) -> Dict[str, Any]:
        """
        质量趋势分析
        
        Returns:
            合格率趋势、主要缺陷类型等
        """
        try:
            # 简化实现
            trend_data = []
            
            # 模拟数据（实际应从数据库读取）
            for i in range(months):
                date = datetime.utcnow() - timedelta(days=30*i)
                trend_data.append({
                    "period": date.strftime("%Y-%m"),
                    "qualified_rate": 95.0 + (i % 3),  # 模拟数据
                    "total_inspections": 100 + i*10,
                    "total_rejected": 5 + i
                })
            
            return {
                "success": True,
                "period": period,
                "trend_data": trend_data[::-1]  # 倒序，最早的在前
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """获取质量统计"""
        try:
            # 简化实现
            return {
                "success": True,
                "statistics": {
                    "total_inspections": 1000,
                    "total_qualified": 950,
                    "total_rejected": 50,
                    "overall_qualified_rate": 95.0,
                    "main_defect_types": [
                        {"type": "尺寸偏差", "count": 20},
                        {"type": "表面缺陷", "count": 15},
                        {"type": "功能异常", "count": 15}
                    ]
                }
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_id(self) -> str:
        """生成ID"""
        return f"QC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # ============ 高级功能（新增）============
    
    def quality_trend_prediction(self, months_ahead: int = 3) -> Dict[str, Any]:
        """
        质量趋势预测（新功能）
        
        基于历史数据预测未来质量走势
        """
        try:
            # 获取历史质量数据（模拟）
            historical_rates = [95.5, 94.8, 96.2, 95.0, 96.5, 95.8]  # 过去6个月
            
            # 简单的线性预测
            avg_rate = sum(historical_rates) / len(historical_rates)
            
            # 计算趋势
            if len(historical_rates) >= 2:
                trend_slope = (historical_rates[-1] - historical_rates[0]) / len(historical_rates)
            else:
                trend_slope = 0
            
            # 预测未来
            predictions = []
            for i in range(1, months_ahead + 1):
                predicted_rate = avg_rate + (trend_slope * i)
                # 限制在合理范围内
                predicted_rate = max(85, min(100, predicted_rate))
                
                predictions.append({
                    "month": i,
                    "predicted_qualified_rate": round(predicted_rate, 2),
                    "confidence": "高" if i <= 2 else "中" if i <= 4 else "低"
                })
            
            # 趋势判断
            if trend_slope > 0.5:
                trend_status = "持续改善"
                trend_color = "green"
            elif trend_slope > -0.5:
                trend_status = "基本稳定"
                trend_color = "yellow"
            else:
                trend_status = "下降趋势"
                trend_color = "red"
            
            # 建议
            recommendations = []
            if trend_status == "下降趋势":
                recommendations.append("质量趋势下降，需要：1)分析根本原因 2)加强过程控制 3)员工再培训")
            if avg_rate < 95:
                recommendations.append("平均合格率低于95%，建议设定质量改进目标")
            if predictions[-1]["predicted_qualified_rate"] < 90:
                recommendations.append("预测合格率可能跌破90%，需要紧急干预")
            
            return {
                "success": True,
                "historical_data": {
                    "average_qualified_rate": round(avg_rate, 2),
                    "trend_slope": round(trend_slope, 4),
                    "trend_status": trend_status,
                    "trend_color": trend_color
                },
                "predictions": predictions,
                "recommendations": recommendations,
                "prediction_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def defect_root_cause_analysis(self) -> Dict[str, Any]:
        """
        缺陷根因分析（新功能）
        
        使用帕累托分析识别主要缺陷类型
        """
        try:
            # 模拟缺陷数据（实际应从数据库读取）
            defect_data = [
                {"type": "尺寸偏差", "count": 120, "percentage": 0},
                {"type": "表面划伤", "count": 85, "percentage": 0},
                {"type": "组装错误", "count": 45, "percentage": 0},
                {"type": "焊接不良", "count": 30, "percentage": 0},
                {"type": "材料瑕疵", "count": 25, "percentage": 0},
                {"type": "涂装问题", "count": 15, "percentage": 0},
                {"type": "其他", "count": 10, "percentage": 0}
            ]
            
            # 计算总数和百分比
            total_defects = sum(d["count"] for d in defect_data)
            
            cumulative = 0
            for defect in defect_data:
                defect["percentage"] = round((defect["count"] / total_defects * 100), 2)
                cumulative += defect["percentage"]
                defect["cumulative_percentage"] = round(cumulative, 2)
            
            # 帕累托分析：识别占80%的关键缺陷
            key_defects = []
            other_defects = []
            
            for defect in defect_data:
                if defect["cumulative_percentage"] <= 80:
                    key_defects.append(defect)
                else:
                    other_defects.append(defect)
            
            # 根因分析建议
            root_cause_suggestions = []
            for defect in key_defects[:3]:  # 前3个主要缺陷
                if defect["type"] == "尺寸偏差":
                    root_cause_suggestions.append({
                        "defect_type": defect["type"],
                        "count": defect["count"],
                        "percentage": defect["percentage"],
                        "possible_causes": [
                            "设备精度不足",
                            "刀具磨损",
                            "操作不规范",
                            "环境温度影响"
                        ],
                        "corrective_actions": [
                            "校准测量设备",
                            "定期更换刀具",
                            "加强操作培训",
                            "控制车间温湿度"
                        ],
                        "priority": "P0"
                    })
                elif defect["type"] == "表面划伤":
                    root_cause_suggestions.append({
                        "defect_type": defect["type"],
                        "count": defect["count"],
                        "percentage": defect["percentage"],
                        "possible_causes": [
                            "运输过程碰撞",
                            "存放不当",
                            "工装设计问题"
                        ],
                        "corrective_actions": [
                            "改进包装方式",
                            "使用防护材料",
                            "优化工装设计"
                        ],
                        "priority": "P1"
                    })
                else:
                    root_cause_suggestions.append({
                        "defect_type": defect["type"],
                        "count": defect["count"],
                        "percentage": defect["percentage"],
                        "possible_causes": ["需要具体分析"],
                        "corrective_actions": ["组织专项分析"],
                        "priority": "P1"
                    })
            
            return {
                "success": True,
                "total_defects": total_defects,
                "defect_distribution": defect_data,
                "key_defects": key_defects,
                "key_defects_percentage": sum(d["percentage"] for d in key_defects),
                "root_cause_analysis": root_cause_suggestions,
                "recommendations": [
                    f"关注前{len(key_defects)}类缺陷，占总缺陷的{sum(d['percentage'] for d in key_defects):.1f}%",
                    "使用5Why分析法深入挖掘根本原因",
                    "制定PDCA改进计划"
                ],
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def quality_cost_analysis(self) -> Dict[str, Any]:
        """
        质量成本分析（新功能）
        
        分析质量相关的各项成本
        """
        try:
            # 质量成本的四个分类
            # 1. 预防成本
            prevention_costs = {
                "quality_planning": 50000,
                "training": 80000,
                "process_improvement": 120000,
                "equipment_maintenance": 100000
            }
            total_prevention = sum(prevention_costs.values())
            
            # 2. 鉴定成本
            appraisal_costs = {
                "incoming_inspection": 60000,
                "process_inspection": 90000,
                "final_inspection": 70000,
                "testing_equipment": 40000
            }
            total_appraisal = sum(appraisal_costs.values())
            
            # 3. 内部失败成本
            internal_failure_costs = {
                "scrap": 150000,
                "rework": 180000,
                "downtime": 100000,
                "re_inspection": 30000
            }
            total_internal_failure = sum(internal_failure_costs.values())
            
            # 4. 外部失败成本
            external_failure_costs = {
                "returns": 200000,
                "warranty_claims": 150000,
                "customer_complaints": 80000,
                "reputation_loss": 100000
            }
            total_external_failure = sum(external_failure_costs.values())
            
            # 总质量成本
            total_quality_cost = (total_prevention + total_appraisal + 
                                 total_internal_failure + total_external_failure)
            
            # 成本结构分析
            cost_structure = {
                "prevention_cost": {
                    "amount": total_prevention,
                    "percentage": round((total_prevention / total_quality_cost * 100), 2),
                    "details": prevention_costs
                },
                "appraisal_cost": {
                    "amount": total_appraisal,
                    "percentage": round((total_appraisal / total_quality_cost * 100), 2),
                    "details": appraisal_costs
                },
                "internal_failure_cost": {
                    "amount": total_internal_failure,
                    "percentage": round((total_internal_failure / total_quality_cost * 100), 2),
                    "details": internal_failure_costs
                },
                "external_failure_cost": {
                    "amount": total_external_failure,
                    "percentage": round((total_external_failure / total_quality_cost * 100), 2),
                    "details": external_failure_costs
                }
            }
            
            # 质量成本比率（占销售额的百分比，假设销售额1000万）
            assumed_revenue = 10000000
            quality_cost_ratio = (total_quality_cost / assumed_revenue * 100)
            
            # 优化建议
            recommendations = []
            
            # 失败成本过高
            failure_cost = total_internal_failure + total_external_failure
            failure_percentage = (failure_cost / total_quality_cost * 100)
            
            if failure_percentage > 50:
                recommendations.append({
                    "issue": f"失败成本占比{failure_percentage:.1f}%过高",
                    "suggestion": "增加预防成本投入，从源头减少缺陷",
                    "expected_benefit": "每增加1元预防成本，可减少3-5元失败成本",
                    "priority": "高"
                })
            
            # 外部失败成本高
            if total_external_failure > total_internal_failure:
                recommendations.append({
                    "issue": "外部失败成本高于内部失败成本",
                    "suggestion": "加强出厂检验，在内部发现并解决问题",
                    "expected_benefit": "降低客户退货和索赔",
                    "priority": "高"
                })
            
            # 质量成本率高
            if quality_cost_ratio > 10:
                recommendations.append({
                    "issue": f"质量成本率{quality_cost_ratio:.1f}%偏高（标准<10%）",
                    "suggestion": "全面质量管理，降低整体质量成本",
                    "expected_benefit": "提升利润率",
                    "priority": "中"
                })
            
            return {
                "success": True,
                "total_quality_cost": total_quality_cost,
                "quality_cost_ratio": round(quality_cost_ratio, 2),
                "cost_structure": cost_structure,
                "cost_distribution": {
                    "prevention_percentage": cost_structure["prevention_cost"]["percentage"],
                    "appraisal_percentage": cost_structure["appraisal_cost"]["percentage"],
                    "internal_failure_percentage": cost_structure["internal_failure_cost"]["percentage"],
                    "external_failure_percentage": cost_structure["external_failure_cost"]["percentage"]
                },
                "optimization_recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def supplier_quality_rating(self) -> Dict[str, Any]:
        """
        供应商质量评估（新功能）
        
        评估供应商的质量表现
        """
        try:
            # 模拟供应商质量数据（实际应从到料检验记录读取）
            suppliers = [
                {
                    "supplier_id": "SUP001",
                    "supplier_name": "供应商A",
                    "total_batches": 120,
                    "qualified_batches": 115,
                    "total_quantity": 50000,
                    "qualified_quantity": 48500,
                    "defect_types": {"尺寸偏差": 15, "材质问题": 5},
                    "on_time_delivery_rate": 95.0
                },
                {
                    "supplier_id": "SUP002",
                    "supplier_name": "供应商B",
                    "total_batches": 100,
                    "qualified_batches": 92,
                    "total_quantity": 40000,
                    "qualified_quantity": 37600,
                    "defect_types": {"表面问题": 20, "包装不良": 8},
                    "on_time_delivery_rate": 88.0
                },
                {
                    "supplier_id": "SUP003",
                    "supplier_name": "供应商C",
                    "total_batches": 80,
                    "qualified_batches": 78,
                    "total_quantity": 30000,
                    "qualified_quantity": 29400,
                    "defect_types": {"功能异常": 6},
                    "on_time_delivery_rate": 97.0
                }
            ]
            
            # 为每个供应商计算质量评分
            supplier_ratings = []
            
            for supplier in suppliers:
                # 计算合格率
                batch_qualified_rate = (supplier["qualified_batches"] / supplier["total_batches"] * 100)
                quantity_qualified_rate = (supplier["qualified_quantity"] / supplier["total_quantity"] * 100)
                
                # 综合评分（满分100）
                score = 0
                
                # 1. 批次合格率（40分）
                if batch_qualified_rate >= 98:
                    score += 40
                elif batch_qualified_rate >= 95:
                    score += 35
                elif batch_qualified_rate >= 90:
                    score += 28
                else:
                    score += batch_qualified_rate / 3
                
                # 2. 数量合格率（40分）
                if quantity_qualified_rate >= 98:
                    score += 40
                elif quantity_qualified_rate >= 95:
                    score += 35
                elif quantity_qualified_rate >= 90:
                    score += 28
                else:
                    score += quantity_qualified_rate / 3
                
                # 3. 准时交付率（20分）
                delivery_score = supplier["on_time_delivery_rate"] / 5
                score += min(delivery_score, 20)
                
                # 等级评定
                if score >= 90:
                    rating = "A级优秀供应商"
                    color = "green"
                elif score >= 80:
                    rating = "B级良好供应商"
                    color = "blue"
                elif score >= 70:
                    rating = "C级合格供应商"
                    color = "yellow"
                else:
                    rating = "D级需改进供应商"
                    color = "red"
                
                # 建议
                recommendations = []
                if batch_qualified_rate < 95:
                    recommendations.append("批次合格率偏低，需要供应商改进")
                if quantity_qualified_rate < 95:
                    recommendations.append("数量合格率偏低，加强来料检验")
                if supplier["on_time_delivery_rate"] < 90:
                    recommendations.append("准时交付率低，影响生产计划")
                
                supplier_ratings.append({
                    "supplier_id": supplier["supplier_id"],
                    "supplier_name": supplier["supplier_name"],
                    "quality_metrics": {
                        "batch_qualified_rate": round(batch_qualified_rate, 2),
                        "quantity_qualified_rate": round(quantity_qualified_rate, 2),
                        "on_time_delivery_rate": supplier["on_time_delivery_rate"]
                    },
                    "quality_score": round(score, 2),
                    "rating": rating,
                    "color": color,
                    "defect_summary": supplier["defect_types"],
                    "recommendations": recommendations
                })
            
            # 按评分排序
            supplier_ratings.sort(key=lambda x: x["quality_score"], reverse=True)
            
            return {
                "success": True,
                "total_suppliers": len(suppliers),
                "supplier_ratings": supplier_ratings,
                "best_supplier": supplier_ratings[0] if supplier_ratings else None,
                "worst_supplier": supplier_ratings[-1] if supplier_ratings else None,
                "recommendations": [
                    "优先选择A级供应商",
                    "与B级供应商签订质量改进协议",
                    "对D级供应商启动淘汰或整改流程"
                ],
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def quality_improvement_tracking(self) -> Dict[str, Any]:
        """
        质量改进跟踪（新功能）
        
        跟踪质量改进措施的效果
        """
        try:
            # 模拟改进项目数据
            improvement_projects = [
                {
                    "project_id": "QI001",
                    "project_name": "减少尺寸偏差",
                    "start_date": "2025-01-01",
                    "target_completion": "2025-03-31",
                    "status": "进行中",
                    "before_defect_rate": 4.5,
                    "current_defect_rate": 2.8,
                    "target_defect_rate": 2.0,
                    "progress": 68
                },
                {
                    "project_id": "QI002",
                    "project_name": "降低表面划伤",
                    "start_date": "2024-12-01",
                    "target_completion": "2025-02-28",
                    "status": "已完成",
                    "before_defect_rate": 3.2,
                    "current_defect_rate": 1.5,
                    "target_defect_rate": 1.5,
                    "progress": 100
                },
                {
                    "project_id": "QI003",
                    "project_name": "提升焊接质量",
                    "start_date": "2025-02-01",
                    "target_completion": "2025-04-30",
                    "status": "计划中",
                    "before_defect_rate": 2.8,
                    "current_defect_rate": 2.8,
                    "target_defect_rate": 1.0,
                    "progress": 0
                }
            ]
            
            # 统计
            total_projects = len(improvement_projects)
            in_progress = sum(1 for p in improvement_projects if p["status"] == "进行中")
            completed = sum(1 for p in improvement_projects if p["status"] == "已完成")
            planned = sum(1 for p in improvement_projects if p["status"] == "计划中")
            
            # 计算整体改进效果
            total_improvement_rate = 0
            effective_projects = 0
            
            for project in improvement_projects:
                if project["before_defect_rate"] > project["current_defect_rate"]:
                    improvement = ((project["before_defect_rate"] - project["current_defect_rate"]) / 
                                 project["before_defect_rate"] * 100)
                    total_improvement_rate += improvement
                    effective_projects += 1
                    project["improvement_rate"] = round(improvement, 2)
                    project["effectiveness"] = "有效"
                else:
                    project["improvement_rate"] = 0
                    project["effectiveness"] = "待观察"
            
            avg_improvement_rate = (total_improvement_rate / effective_projects) if effective_projects > 0 else 0
            
            # 识别需要关注的项目
            attention_needed = []
            for project in improvement_projects:
                if project["status"] == "进行中" and project["progress"] < 30:
                    attention_needed.append({
                        "project_id": project["project_id"],
                        "project_name": project["project_name"],
                        "reason": "进度缓慢",
                        "action": "加快推进"
                    })
                elif project["status"] == "进行中" and project["improvement_rate"] < 10:
                    attention_needed.append({
                        "project_id": project["project_id"],
                        "project_name": project["project_name"],
                        "reason": "改进效果不明显",
                        "action": "重新评估措施有效性"
                    })
            
            return {
                "success": True,
                "improvement_projects": improvement_projects,
                "statistics": {
                    "total_projects": total_projects,
                    "in_progress": in_progress,
                    "completed": completed,
                    "planned": planned,
                    "effective_projects": effective_projects,
                    "average_improvement_rate": round(avg_improvement_rate, 2)
                },
                "attention_needed": attention_needed,
                "overall_assessment": "良好" if avg_improvement_rate > 30 else "一般" if avg_improvement_rate > 15 else "需加强",
                "recommendations": [
                    "继续推进进行中的改进项目",
                    "对已完成项目进行效果验证",
                    "将成功经验推广到其他领域"
                ],
                "analysis_date": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# 工具函数
def get_quality_manager(db_session: Session) -> QualityManager:
    """获取质量管理器实例"""
    return QualityManager(db_session)











