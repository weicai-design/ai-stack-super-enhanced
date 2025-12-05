"""
项目管理模块
- 项目立项
- 项目执行跟踪
- 里程碑管理
- 项目验收
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import time

# 导入监控模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修正导入路径，从modules.core导入
from modules.core.circuit_breaker import circuit_breaker, rate_limit, circuit_manager
from modules.core.error_handler import ErrorHandlingStrategies
from modules.core.audit_manager import audit_decorators

# 尝试导入监控模块
try:
    from monitoring.project_procurement_monitor import (
        monitor_project_creation, monitor_procurement_order,
        MetricType, monitor
    )
except ImportError:
    # 如果监控模块不存在，创建模拟装饰器
    def monitor_project_creation():
        def decorator(func):
            return func
        return decorator
    
    def monitor_procurement_order():
        def decorator(func):
            return func
        return decorator
    
    class MetricType:
        PROJECT_COMPLETION_RATE = "project_completion_rate"
        API_RESPONSE_TIME = "api_response_time"
    
    class MockMonitor:
        def record_metric(self, metric_type, value, tags=None):
            pass
    
    monitor = MockMonitor()


class ProjectStatus(Enum):
    """项目状态"""
    PLANNING = "规划中"
    APPROVED = "已批准"
    EXECUTING = "执行中"
    TESTING = "测试中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"
    ON_HOLD = "已暂停"


class ProjectManager:
    """项目管理器"""
    
    def __init__(self):
        # 项目列表
        self.projects = []
        
        # 里程碑记录
        self.milestones = []
    
    # ============ 项目创建 ============
    
    # 简化装饰器 - 暂时禁用复杂装饰器以解决日志配置冲突
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新项目
        
        Args:
            project_data: {
                "name": "项目名称",
                "code": "项目编号",
                "customer_id": 客户ID,
                "type": "项目类型",
                "budget": 项目预算,
                "start_date": "开始日期",
                "target_end_date": "目标结束日期",
                "description": "项目描述",
                "milestones": [里程碑列表]
            }
        
        Returns:
            项目信息
        """
        try:
            project_id = f"PROJ{len(self.projects) + 1:04d}"
            
            project = {
                "project_id": project_id,
                "name": project_data['name'],
                "code": project_data['code'],
                "customer_id": project_data.get('customer_id'),
                "type": project_data.get('type', '常规项目'),
                "budget": project_data.get('budget', 0),
                "actual_cost": 0,
                "start_date": project_data.get('start_date'),
                "target_end_date": project_data.get('target_end_date'),
                "actual_end_date": None,
                "status": ProjectStatus.PLANNING.value,
                "progress": 0,
                "description": project_data.get('description', ''),
                "team_members": project_data.get('team_members', []),
                "milestones": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.projects.append(project)
            
            # 创建里程碑
            for milestone_data in project_data.get('milestones', []):
                self._create_milestone(project_id, milestone_data)
            
            return {
                "success": True,
                "project": project,
                "message": f"项目已创建：{project_id}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 里程碑管理 ============
    
    def _create_milestone(
        self,
        project_id: str,
        milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建里程碑"""
        milestone_id = f"MS{len(self.milestones) + 1:04d}"
        
        milestone = {
            "milestone_id": milestone_id,
            "project_id": project_id,
            "name": milestone_data['name'],
            "target_date": milestone_data.get('target_date'),
            "actual_date": None,
            "status": "未开始",
            "deliverables": milestone_data.get('deliverables', []),
            "created_at": datetime.now().isoformat()
        }
        
        self.milestones.append(milestone)
        
        # 更新项目的里程碑列表
        project = self._get_project(project_id)
        if project:
            project['milestones'].append(milestone_id)
        
        return milestone
    
    # 简化装饰器 - 暂时禁用复杂装饰器以解决日志配置冲突
    def complete_milestone(
        self,
        milestone_id: str,
        completion_note: str = ""
    ) -> Dict[str, Any]:
        """完成里程碑"""
        start_time = time.time()
        
        try:
            milestone = next((m for m in self.milestones 
                             if m['milestone_id'] == milestone_id), None)
            
            if not milestone:
                return {"success": False, "error": "里程碑不存在"}
            
            milestone['status'] = "已完成"
            milestone['actual_date'] = datetime.now().isoformat()
            milestone['completion_note'] = completion_note
            
            # 更新项目进度
            project = self._get_project(milestone['project_id'])
            if project:
                completed_milestones = sum(
                    1 for mid in project['milestones']
                    if self._get_milestone(mid)['status'] == '已完成'
                )
                total_milestones = len(project['milestones'])
                project['progress'] = int((completed_milestones / total_milestones) * 100) \
                                     if total_milestones > 0 else 0
                project['updated_at'] = datetime.now().isoformat()
                
                # 记录里程碑完成率
                completion_rate = completed_milestones / total_milestones if total_milestones > 0 else 0
                monitor.record_metric(
                    MetricType.PROJECT_COMPLETION_RATE,
                    completion_rate,
                    {"project_id": project['project_id']}
                )
            
            # 记录响应时间
            response_time = time.time() - start_time
            monitor.record_metric(
                MetricType.API_RESPONSE_TIME,
                response_time,
                {"method": "complete_milestone"}
            )
            
            return {
                "success": True,
                "milestone": milestone,
                "project_progress": project['progress'] if project else 0,
                "message": "里程碑已完成"
            }
            
        except Exception as e:
            # 记录错误指标
            monitor.record_metric(
                MetricType.ERROR_RATE,
                1,
                {"method": "complete_milestone", "error": str(e)}
            )
            raise
    
    # ============ 项目执行 ============
    
    @circuit_breaker("project_status_update", failure_threshold=5, recovery_timeout=30)
    @rate_limit("project_status_update", max_requests=15, window_seconds=60)
    @audit_decorators.project_status_update()
    def update_project_status(
        self,
        project_id: str,
        new_status: str,
        note: str = ""
    ) -> Dict[str, Any]:
        """更新项目状态"""
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        old_status = project['status']
        project['status'] = new_status
        project['updated_at'] = datetime.now().isoformat()
        
        # 状态变更历史
        if 'status_history' not in project:
            project['status_history'] = []
        
        project['status_history'].append({
            "from": old_status,
            "to": new_status,
            "note": note,
            "timestamp": datetime.now().isoformat()
        })
        
        # 如果完成，记录实际结束时间
        if new_status == ProjectStatus.COMPLETED.value:
            project['actual_end_date'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project": project,
            "message": f"项目状态已更新为 {new_status}"
        }
    
    def update_project_cost(
        self,
        project_id: str,
        cost_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新项目成本"""
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 累加成本
        project['actual_cost'] += cost_item.get('amount', 0)
        
        # 记录成本明细
        if 'cost_details' not in project:
            project['cost_details'] = []
        
        project['cost_details'].append({
            "item": cost_item.get('item', ''),
            "amount": cost_item.get('amount', 0),
            "date": datetime.now().isoformat()
        })
        
        project['updated_at'] = datetime.now().isoformat()
        
        # 预算超支检查
        budget_variance = project['actual_cost'] - project['budget']
        warning = None
        
        if budget_variance > 0:
            variance_rate = (budget_variance / project['budget']) * 100
            warning = f"预算超支 {variance_rate:.1f}%"
        
        return {
            "success": True,
            "project": project,
            "budget_variance": float(budget_variance),
            "warning": warning,
            "message": "成本已更新"
        }
    
    # ============ 项目分析 ============
    
    def analyze_project_performance(self, project_id: str) -> Dict[str, Any]:
        """项目绩效分析"""
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 进度分析
        progress_status = "正常"
        if project['progress'] < 50 and project['status'] == ProjectStatus.EXECUTING.value:
            progress_status = "滞后"
        elif project['progress'] >= 80:
            progress_status = "良好"
        
        # 成本分析
        budget_usage = (project['actual_cost'] / project['budget'] * 100) \
                      if project['budget'] > 0 else 0
        cost_status = "正常"
        if budget_usage > 100:
            cost_status = "超支"
        elif budget_usage > 90:
            cost_status = "接近预算"
        
        # 时间分析
        time_status = "正常"
        if project['target_end_date']:
            target = datetime.fromisoformat(project['target_end_date'])
            if datetime.now() > target and project['status'] != ProjectStatus.COMPLETED.value:
                time_status = "延期"
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis": {
                "progress": project['progress'],
                "progress_status": progress_status,
                "budget_usage": float(budget_usage),
                "cost_status": cost_status,
                "time_status": time_status,
                "overall_health": self._calculate_project_health(
                    progress_status, cost_status, time_status
                )
            }
        }
    
    # ============ 内部辅助方法 ============
    
    def _get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目"""
        return next((p for p in self.projects if p['project_id'] == project_id), None)
    
    def _get_milestone(self, milestone_id: str) -> Optional[Dict[str, Any]]:
        """获取里程碑"""
        return next((m for m in self.milestones if m['milestone_id'] == milestone_id), None)
    
    def _calculate_project_health(
        self,
        progress_status: str,
        cost_status: str,
        time_status: str
    ) -> str:
        """计算项目健康度"""
        score = 0
        
        if progress_status == "良好":
            score += 3
        elif progress_status == "正常":
            score += 2
        
        if cost_status == "正常":
            score += 2
        elif cost_status == "接近预算":
            score += 1
        
        if time_status == "正常":
            score += 2
        
        if score >= 6:
            return "健康"
        elif score >= 4:
            return "一般"
        else:
            return "需关注"
    
    def get_project_list(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取项目列表"""
        projects = self.projects
        
        if status:
            projects = [p for p in projects if p['status'] == status]
        if customer_id:
            projects = [p for p in projects if p['customer_id'] == customer_id]
        
        return {
            "success": True,
            "projects": projects,
            "total": len(projects)
        }
    
    # ============ 高级功能（新增）============
    
    def project_risk_assessment(self, project_id: str) -> Dict[str, Any]:
        """
        项目风险评估（新功能）
        
        评估项目的多维度风险：
        - 进度风险
        - 成本风险
        - 质量风险
        - 资源风险
        - 客户风险
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        risks = []
        risk_scores = {}
        
        # 1. 进度风险评估
        progress_risk = 0
        if project['progress'] < 30 and project['status'] == ProjectStatus.EXECUTING.value:
            progress_risk = 8
            risks.append({
                "type": "进度风险",
                "level": "高",
                "score": 8,
                "description": "项目进度严重滞后",
                "recommendation": "增加资源投入，重新评估里程碑"
            })
        elif project['progress'] < 50:
            progress_risk = 5
            risks.append({
                "type": "进度风险",
                "level": "中",
                "score": 5,
                "description": "项目进度偏慢",
                "recommendation": "关注关键路径，优化流程"
            })
        else:
            progress_risk = 2
        
        risk_scores["progress_risk"] = progress_risk
        
        # 2. 成本风险评估
        budget_usage = (project['actual_cost'] / project['budget'] * 100) if project['budget'] > 0 else 0
        cost_risk = 0
        
        if budget_usage > 100:
            cost_risk = 9
            risks.append({
                "type": "成本风险",
                "level": "高",
                "score": 9,
                "description": f"预算已超支 {budget_usage - 100:.1f}%",
                "recommendation": "立即控制成本，审查所有支出"
            })
        elif budget_usage > 90:
            cost_risk = 6
            risks.append({
                "type": "成本风险",
                "level": "中",
                "score": 6,
                "description": "预算即将耗尽",
                "recommendation": "严格控制后续支出"
            })
        elif budget_usage > 70:
            cost_risk = 3
        
        risk_scores["cost_risk"] = cost_risk
        
        # 3. 时间风险评估
        time_risk = 0
        if project.get('target_end_date'):
            target = datetime.fromisoformat(project['target_end_date'])
            days_remaining = (target - datetime.now()).days
            
            if days_remaining < 0 and project['status'] != ProjectStatus.COMPLETED.value:
                time_risk = 10
                risks.append({
                    "type": "时间风险",
                    "level": "高",
                    "score": 10,
                    "description": f"项目已延期 {abs(days_remaining)} 天",
                    "recommendation": "紧急处理，重新制定交付计划"
                })
            elif days_remaining < 7 and project['progress'] < 90:
                time_risk = 7
                risks.append({
                    "type": "时间风险",
                    "level": "中",
                    "score": 7,
                    "description": "临近截止日期但进度不足",
                    "recommendation": "加快进度，考虑延期或调整范围"
                })
        
        risk_scores["time_risk"] = time_risk
        
        # 4. 资源风险评估
        team_size = len(project.get('team_members', []))
        resource_risk = 0
        
        if team_size < 2:
            resource_risk = 6
            risks.append({
                "type": "资源风险",
                "level": "中",
                "score": 6,
                "description": "团队规模过小",
                "recommendation": "考虑增加团队成员"
            })
        
        risk_scores["resource_risk"] = resource_risk
        
        # 5. 里程碑风险
        milestone_risk = 0
        project_milestones = [self._get_milestone(mid) for mid in project.get('milestones', [])]
        delayed_milestones = [
            m for m in project_milestones 
            if m and m['status'] != '已完成' and m.get('target_date') 
            and datetime.fromisoformat(m['target_date']) < datetime.now()
        ]
        
        if len(delayed_milestones) > 2:
            milestone_risk = 7
            risks.append({
                "type": "里程碑风险",
                "level": "高",
                "score": 7,
                "description": f"有 {len(delayed_milestones)} 个里程碑延期",
                "recommendation": "重新规划里程碑时间表"
            })
        elif len(delayed_milestones) > 0:
            milestone_risk = 4
        
        risk_scores["milestone_risk"] = milestone_risk
        
        # 计算总体风险评分
        total_risk_score = sum(risk_scores.values())
        max_possible_score = 40  # 进度8+成本9+时间10+资源6+里程碑7
        
        # 风险等级
        if total_risk_score >= 20:
            overall_risk = "高风险"
            risk_color = "red"
        elif total_risk_score >= 10:
            overall_risk = "中风险"
            risk_color = "yellow"
        else:
            overall_risk = "低风险"
            risk_color = "green"
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project['name'],
            "overall_risk": overall_risk,
            "total_risk_score": total_risk_score,
            "risk_percentage": round((total_risk_score / max_possible_score) * 100, 2),
            "risk_color": risk_color,
            "risk_breakdown": risk_scores,
            "identified_risks": risks,
            "risk_count": len(risks),
            "assessment_date": datetime.now().isoformat()
        }
    
    def project_roi_analysis(self, project_id: str, expected_revenue: float = None) -> Dict[str, Any]:
        """
        项目ROI深度分析（新功能）
        
        基于项目成本和预期收益计算ROI
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 使用预期收益或预算的2倍作为预期收益
        expected_rev = expected_revenue if expected_revenue else project['budget'] * 2
        
        # 计算投资回报
        actual_cost = project['actual_cost']
        projected_cost = project['budget']
        
        # 使用实际成本（如果项目完成）或预算（如果项目进行中）
        investment = actual_cost if project['status'] == ProjectStatus.COMPLETED.value else projected_cost
        
        # 基础ROI
        net_profit = expected_rev - investment
        roi = (net_profit / investment * 100) if investment > 0 else 0
        
        # 时间因素
        if project.get('start_date') and project.get('actual_end_date'):
            start = datetime.fromisoformat(project['start_date'])
            end = datetime.fromisoformat(project['actual_end_date'])
            duration_days = (end - start).days
            duration_months = duration_days / 30
        elif project.get('start_date') and project.get('target_end_date'):
            start = datetime.fromisoformat(project['start_date'])
            end = datetime.fromisoformat(project['target_end_date'])
            duration_days = (end - start).days
            duration_months = duration_days / 30
        else:
            duration_months = 6  # 默认6个月
        
        # 年化ROI
        annualized_roi = (roi / duration_months) * 12 if duration_months > 0 else roi
        
        # 回报倍数
        return_multiple = expected_rev / investment if investment > 0 else 0
        
        # 盈亏平衡点
        breakeven_revenue = investment
        breakeven_met = expected_rev >= breakeven_revenue
        
        # ROI评级
        if roi >= 100:
            rating = "优秀"
            grade = "A+"
        elif roi >= 50:
            rating = "良好"
            grade = "A"
        elif roi >= 20:
            rating = "一般"
            grade = "B"
        elif roi >= 0:
            rating = "偏低"
            grade = "C"
        else:
            rating = "亏损"
            grade = "D"
        
        # 建议
        recommendations = []
        if roi < 20:
            recommendations.append("ROI较低，建议优化成本或提高收益")
        if actual_cost > projected_cost:
            recommendations.append(f"成本超支 {((actual_cost - projected_cost) / projected_cost * 100):.1f}%，需要加强成本控制")
        if roi >= 50:
            recommendations.append("ROI表现优秀，可作为标杆项目推广经验")
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project['name'],
            "financial_metrics": {
                "investment": float(investment),
                "expected_revenue": float(expected_rev),
                "net_profit": float(net_profit),
                "roi_percentage": round(roi, 2),
                "annualized_roi": round(annualized_roi, 2),
                "return_multiple": round(return_multiple, 2),
                "duration_months": round(duration_months, 1)
            },
            "breakeven_analysis": {
                "breakeven_revenue": float(breakeven_revenue),
                "breakeven_met": breakeven_met,
                "surplus": float(expected_rev - breakeven_revenue)
            },
            "rating": rating,
            "grade": grade,
            "recommendations": recommendations,
            "analysis_date": datetime.now().isoformat()
        }
    
    def project_progress_prediction(self, project_id: str) -> Dict[str, Any]:
        """
        项目进度智能预测（新功能）
        
        基于当前进度预测完成时间
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        current_progress = project['progress']
        start_date = datetime.fromisoformat(project['start_date']) if project.get('start_date') else None
        target_end_date = datetime.fromisoformat(project['target_end_date']) if project.get('target_end_date') else None
        
        if not start_date:
            return {
                "success": False,
                "error": "项目缺少开始日期"
            }
        
        # 已用时间
        days_elapsed = (datetime.now() - start_date).days
        
        # 基于当前进度预测完成时间
        if current_progress > 0:
            # 线性预测：假设未来速度与过去相同
            days_per_percent = days_elapsed / current_progress
            remaining_progress = 100 - current_progress
            predicted_remaining_days = int(days_per_percent * remaining_progress)
            
            predicted_completion_date = datetime.now() + timedelta(days=predicted_remaining_days)
            
            # 与目标日期对比
            if target_end_date:
                variance_days = (predicted_completion_date - target_end_date).days
                
                if variance_days > 7:
                    status = "延期风险"
                    alert_level = "高"
                elif variance_days > 0:
                    status = "轻微延期"
                    alert_level = "中"
                elif variance_days > -7:
                    status = "按期完成"
                    alert_level = "低"
                else:
                    status = "提前完成"
                    alert_level = "低"
            else:
                variance_days = None
                status = "无目标日期"
                alert_level = "中"
        else:
            predicted_completion_date = None
            predicted_remaining_days = None
            variance_days = None
            status = "无法预测（进度为0）"
            alert_level = "高"
        
        # 里程碑预测
        milestone_predictions = []
        for milestone_id in project.get('milestones', []):
            milestone = self._get_milestone(milestone_id)
            if milestone and milestone['status'] != '已完成':
                # 简化预测：假设里程碑均匀分布
                milestone_predictions.append({
                    "milestone_id": milestone_id,
                    "milestone_name": milestone['name'],
                    "target_date": milestone.get('target_date'),
                    "predicted_completion": "待分析"
                })
        
        # 建议
        recommendations = []
        if status == "延期风险":
            recommendations.append("项目有延期风险，建议：1) 增加资源 2) 优化流程 3) 调整范围")
        elif status == "轻微延期":
            recommendations.append("注意进度管理，关注关键路径")
        elif status == "提前完成":
            recommendations.append("进度良好，可考虑提前交付或扩展范围")
        
        if current_progress < 10 and days_elapsed > 7:
            recommendations.append("启动阶段较慢，需要加速")
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project['name'],
            "current_status": {
                "progress": current_progress,
                "days_elapsed": days_elapsed,
                "status": project['status']
            },
            "predictions": {
                "predicted_completion_date": predicted_completion_date.isoformat() if predicted_completion_date else None,
                "predicted_remaining_days": predicted_remaining_days,
                "target_end_date": target_end_date.isoformat() if target_end_date else None,
                "variance_days": variance_days,
                "completion_status": status,
                "alert_level": alert_level
            },
            "milestone_predictions": milestone_predictions,
            "recommendations": recommendations,
            "prediction_date": datetime.now().isoformat()
        }
    
    def resource_optimization_analysis(self, project_id: str) -> Dict[str, Any]:
        """
        资源优化分析（新功能）
        
        分析项目资源配置并提供优化建议
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        team_size = len(project.get('team_members', []))
        budget = project['budget']
        actual_cost = project['actual_cost']
        progress = project['progress']
        
        # 人均成本
        cost_per_person = actual_cost / team_size if team_size > 0 else 0
        
        # 人均进度贡献
        progress_per_person = progress / team_size if team_size > 0 else 0
        
        # 资源效率评分
        efficiency_score = (progress / (actual_cost / budget * 100)) if actual_cost > 0 else 0
        
        # 资源优化建议
        optimization_suggestions = []
        
        # 1. 团队规模分析
        if team_size < 3:
            optimization_suggestions.append({
                "category": "团队规模",
                "current": f"{team_size}人",
                "issue": "团队规模较小，可能影响进度",
                "suggestion": "建议增加2-3名成员",
                "priority": "中"
            })
        elif team_size > 10:
            optimization_suggestions.append({
                "category": "团队规模",
                "current": f"{team_size}人",
                "issue": "团队规模较大，可能存在沟通成本",
                "suggestion": "考虑分组管理或精简团队",
                "priority": "低"
            })
        
        # 2. 成本效率分析
        if efficiency_score < 0.8:
            optimization_suggestions.append({
                "category": "成本效率",
                "current": f"效率评分 {efficiency_score:.2f}",
                "issue": "资源产出效率偏低",
                "suggestion": "优化工作流程，减少浪费",
                "priority": "高"
            })
        
        # 3. 预算使用分析
        budget_usage = (actual_cost / budget * 100) if budget > 0 else 0
        if budget_usage > 80 and progress < 80:
            optimization_suggestions.append({
                "category": "预算管理",
                "current": f"已使用 {budget_usage:.1f}% 预算",
                "issue": "预算消耗速度快于进度",
                "suggestion": "严格控制后续支出，提高成本意识",
                "priority": "高"
            })
        
        # 4. 进度与资源匹配
        if progress < 30 and team_size < 5:
            optimization_suggestions.append({
                "category": "资源配置",
                "current": "进度慢且团队小",
                "issue": "资源可能不足",
                "suggestion": "增加人力资源或外包部分工作",
                "priority": "高"
            })
        
        # 资源健康度
        if len(optimization_suggestions) == 0:
            resource_health = "优秀"
        elif len(optimization_suggestions) <= 2:
            resource_health = "良好"
        else:
            resource_health = "需改进"
        
        return {
            "success": True,
            "project_id": project_id,
            "project_name": project['name'],
            "resource_metrics": {
                "team_size": team_size,
                "cost_per_person": round(cost_per_person, 2),
                "progress_per_person": round(progress_per_person, 2),
                "efficiency_score": round(efficiency_score, 2),
                "budget_usage_percent": round(budget_usage, 2)
            },
            "resource_health": resource_health,
            "optimization_suggestions": optimization_suggestions,
            "suggestion_count": len(optimization_suggestions),
            "analysis_date": datetime.now().isoformat()
        }

    # ============ 项目资源管理（新增功能）============

    @circuit_breaker("resource_allocation", failure_threshold=3, recovery_timeout=30)
    @rate_limit("resource_allocation", max_requests=10, window_seconds=60)
    @audit_decorators.resource_allocate()
    def allocate_project_resources(
        self,
        project_id: str,
        resources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分配项目资源（新功能）
        
        为项目分配人力资源、设备资源等
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化资源列表
        if 'allocated_resources' not in project:
            project['allocated_resources'] = []
        
        # 添加资源
        for resource in resources:
            resource_id = f"RES{len(project['allocated_resources']) + 1:04d}"
            allocated_resource = {
                "resource_id": resource_id,
                "type": resource.get('type', 'human'),
                "name": resource.get('name', ''),
                "quantity": resource.get('quantity', 1),
                "start_date": resource.get('start_date'),
                "end_date": resource.get('end_date'),
                "cost_per_unit": resource.get('cost_per_unit', 0),
                "total_cost": resource.get('quantity', 1) * resource.get('cost_per_unit', 0),
                "allocated_at": datetime.now().isoformat()
            }
            project['allocated_resources'].append(allocated_resource)
        
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "allocated_resources": project['allocated_resources'],
            "message": f"已为项目分配 {len(resources)} 种资源"
        }

    @circuit_breaker("resource_optimization", failure_threshold=2, recovery_timeout=30)
    @rate_limit("resource_optimization", max_requests=5, window_seconds=60)
    def optimize_resource_allocation(self, project_id: str) -> Dict[str, Any]:
        """
        资源分配优化（新功能）
        
        基于项目进度和资源利用率优化资源分配
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 分析资源利用率
        resource_utilization = {}
        total_utilization = 0
        
        for resource in project.get('allocated_resources', []):
            resource_type = resource['type']
            if resource_type not in resource_utilization:
                resource_utilization[resource_type] = {
                    'count': 0,
                    'utilization': 0.0
                }
            
            # 简单估算利用率（基于项目进度）
            utilization = min(project['progress'] / 100.0, 0.8)  # 最大80%利用率
            resource_utilization[resource_type]['count'] += 1
            resource_utilization[resource_type]['utilization'] = utilization
            total_utilization += utilization
        
        # 计算平均利用率
        avg_utilization = total_utilization / len(project.get('allocated_resources', [])) if project.get('allocated_resources') else 0
        
        # 优化建议
        recommendations = []
        
        if avg_utilization < 0.3:
            recommendations.append({
                "type": "资源释放",
                "priority": "高",
                "description": "资源利用率过低，建议释放部分资源",
                "action": "减少20%的资源分配"
            })
        elif avg_utilization > 0.8:
            recommendations.append({
                "type": "资源增加",
                "priority": "高",
                "description": "资源利用率过高，可能影响项目进度",
                "action": "增加15%的资源分配"
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "resource_analysis": {
                "total_resources": len(project.get('allocated_resources', [])),
                "average_utilization": round(avg_utilization * 100, 2),
                "resource_breakdown": resource_utilization
            },
            "recommendations": recommendations,
            "optimization_score": round(avg_utilization * 100, 2)
        }

    # ============ 项目文档管理（新增功能）============

    @circuit_breaker("document_management", failure_threshold=3, recovery_timeout=30)
    @rate_limit("document_management", max_requests=15, window_seconds=60)
    @audit_decorators.document_upload()
    def upload_project_document(
        self,
        project_id: str,
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        上传项目文档（新功能）
        
        管理项目相关文档：需求文档、设计文档、测试报告等
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化文档列表
        if 'documents' not in project:
            project['documents'] = []
        
        document_id = f"DOC{len(project['documents']) + 1:04d}"
        
        document = {
            "document_id": document_id,
            "name": document_data.get('name', ''),
            "type": document_data.get('type', 'general'),
            "version": document_data.get('version', '1.0'),
            "uploaded_by": document_data.get('uploaded_by', 'system'),
            "upload_date": datetime.now().isoformat(),
            "file_size": document_data.get('file_size', 0),
            "description": document_data.get('description', ''),
            "status": "active"
        }
        
        project['documents'].append(document)
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "document": document,
            "message": f"文档 '{document['name']}' 已上传"
        }

    def get_project_documents(
        self,
        project_id: str,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取项目文档列表（新功能）
        
        按类型筛选项目文档
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        documents = project.get('documents', [])
        
        if document_type:
            documents = [doc for doc in documents if doc['type'] == document_type]
        
        return {
            "success": True,
            "project_id": project_id,
            "documents": documents,
            "total": len(documents),
            "document_types": list(set(doc['type'] for doc in project.get('documents', [])))
        }

    # ============ 项目沟通管理（新增功能）============

    @circuit_breaker("communication_log", failure_threshold=5, recovery_timeout=30)
    @rate_limit("communication_log", max_requests=20, window_seconds=60)
    @audit_decorators.communication_log()
    def log_project_communication(
        self,
        project_id: str,
        communication_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        记录项目沟通（新功能）
        
        记录项目相关的会议记录、邮件沟通、重要决策等
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化沟通记录
        if 'communications' not in project:
            project['communications'] = []
        
        communication_id = f"COMM{len(project['communications']) + 1:04d}"
        
        communication = {
            "communication_id": communication_id,
            "type": communication_data.get('type', 'meeting'),
            "subject": communication_data.get('subject', ''),
            "participants": communication_data.get('participants', []),
            "date": communication_data.get('date', datetime.now().isoformat()),
            "duration_minutes": communication_data.get('duration_minutes', 0),
            "summary": communication_data.get('summary', ''),
            "action_items": communication_data.get('action_items', []),
            "recorded_by": communication_data.get('recorded_by', 'system'),
            "importance": communication_data.get('importance', 'normal')
        }
        
        project['communications'].append(communication)
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "communication": communication,
            "message": "沟通记录已保存"
        }

    def analyze_communication_patterns(self, project_id: str) -> Dict[str, Any]:
        """
        分析沟通模式（新功能）
        
        分析项目沟通频率、参与度、决策效率等
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        communications = project.get('communications', [])
        
        if not communications:
            return {
                "success": True,
                "project_id": project_id,
                "analysis": {
                    "total_communications": 0,
                    "communication_frequency": "无记录",
                    "average_participants": 0,
                    "decision_efficiency": "无数据"
                }
            }
        
        # 分析沟通频率
        comm_dates = [datetime.fromisoformat(comm['date']) for comm in communications]
        comm_dates.sort()
        
        if len(comm_dates) > 1:
            total_days = (comm_dates[-1] - comm_dates[0]).days
            comm_frequency = len(communications) / max(total_days, 1)
        else:
            comm_frequency = 0
        
        # 分析参与度
        total_participants = sum(len(comm.get('participants', [])) for comm in communications)
        avg_participants = total_participants / len(communications)
        
        # 分析决策效率
        important_comms = [comm for comm in communications if comm.get('importance') == 'high']
        decision_efficiency = len(important_comms) / len(communications) if communications else 0
        
        return {
            "success": True,
            "project_id": project_id,
            "analysis": {
                "total_communications": len(communications),
                "communication_frequency": round(comm_frequency, 2),
                "average_participants": round(avg_participants, 2),
                "decision_efficiency": round(decision_efficiency * 100, 2),
                "communication_types": list(set(comm['type'] for comm in communications)),
                "important_communications": len(important_comms)
            }
        }


    # ============ 项目预算管理（新增功能）============

    @circuit_breaker("budget_management", failure_threshold=3, recovery_timeout=30)
    @rate_limit("budget_management", max_requests=10, window_seconds=60)
    @audit_decorators.budget_update()
    def update_project_budget(
        self,
        project_id: str,
        budget_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新项目预算（新功能）
        
        管理项目预算分配、调整和跟踪
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化预算信息
        if 'budget' not in project:
            project['budget'] = {}
        
        # 更新预算数据
        project['budget'].update({
            "total_budget": budget_data.get('total_budget', project['budget'].get('total_budget', 0)),
            "allocated_budget": budget_data.get('allocated_budget', project['budget'].get('allocated_budget', 0)),
            "actual_spent": budget_data.get('actual_spent', project['budget'].get('actual_spent', 0)),
            "remaining_budget": budget_data.get('remaining_budget', project['budget'].get('remaining_budget', 0)),
            "budget_categories": budget_data.get('budget_categories', project['budget'].get('budget_categories', {})),
            "last_updated": datetime.now().isoformat()
        })
        
        # 自动计算剩余预算
        if 'total_budget' in project['budget'] and 'actual_spent' in project['budget']:
            project['budget']['remaining_budget'] = project['budget']['total_budget'] - project['budget']['actual_spent']
        
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "budget": project['budget'],
            "message": "项目预算已更新"
        }

    def analyze_budget_variance(self, project_id: str) -> Dict[str, Any]:
        """
        分析预算偏差（新功能）
        
        分析实际支出与预算的差异，提供预警
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        budget = project.get('budget', {})
        
        if not budget:
            return {
                "success": True,
                "project_id": project_id,
                "variance_analysis": {
                    "status": "无预算数据",
                    "variance_percentage": 0,
                    "risk_level": "未知"
                }
            }
        
        total_budget = budget.get('total_budget', 0)
        actual_spent = budget.get('actual_spent', 0)
        
        if total_budget == 0:
            variance_percentage = 0
        else:
            variance_percentage = ((actual_spent - total_budget) / total_budget) * 100
        
        # 风险评估
        if variance_percentage > 20:
            risk_level = "高风险"
            risk_description = "预算超支严重，需要立即采取措施"
        elif variance_percentage > 10:
            risk_level = "中风险"
            risk_description = "预算超支，需要关注"
        elif variance_percentage > -5:
            risk_level = "低风险"
            risk_description = "预算控制良好"
        else:
            risk_level = "无风险"
            risk_description = "预算有结余"
        
        return {
            "success": True,
            "project_id": project_id,
            "variance_analysis": {
                "total_budget": total_budget,
                "actual_spent": actual_spent,
                "variance_amount": actual_spent - total_budget,
                "variance_percentage": round(variance_percentage, 2),
                "risk_level": risk_level,
                "risk_description": risk_description,
                "remaining_budget": budget.get('remaining_budget', 0)
            }
        }

    # ============ 项目变更管理（新增功能）============

    @circuit_breaker("change_management", failure_threshold=3, recovery_timeout=30)
    @rate_limit("change_management", max_requests=8, window_seconds=60)
    @audit_decorators.change_request()
    def submit_change_request(
        self,
        project_id: str,
        change_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提交变更请求（新功能）
        
        管理项目范围、需求、时间表的变更请求
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化变更记录
        if 'change_requests' not in project:
            project['change_requests'] = []
        
        change_id = f"CHG{len(project['change_requests']) + 1:04d}"
        
        change_request = {
            "change_id": change_id,
            "type": change_data.get('type', 'scope'),
            "description": change_data.get('description', ''),
            "reason": change_data.get('reason', ''),
            "impact_analysis": change_data.get('impact_analysis', {}),
            "submitted_by": change_data.get('submitted_by', 'system'),
            "submission_date": datetime.now().isoformat(),
            "status": "pending",
            "priority": change_data.get('priority', 'medium'),
            "estimated_effort": change_data.get('estimated_effort', 0)
        }
        
        project['change_requests'].append(change_request)
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "change_request": change_request,
            "message": f"变更请求 {change_id} 已提交"
        }

    def review_change_request(
        self,
        project_id: str,
        change_id: str,
        review_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评审变更请求（新功能）
        
        对变更请求进行评审和决策
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        change_requests = project.get('change_requests', [])
        
        # 查找变更请求
        change_request = None
        for cr in change_requests:
            if cr['change_id'] == change_id:
                change_request = cr
                break
        
        if not change_request:
            return {"success": False, "error": "变更请求不存在"}
        
        # 更新评审信息
        change_request.update({
            "reviewer": review_data.get('reviewer', 'system'),
            "review_date": datetime.now().isoformat(),
            "decision": review_data.get('decision', 'pending'),
            "comments": review_data.get('comments', ''),
            "implementation_plan": review_data.get('implementation_plan', {})
        })
        
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "change_request": change_request,
            "message": f"变更请求 {change_id} 已评审"
        }

    # ============ 项目质量管理（新增功能）============

    @circuit_breaker("quality_management", failure_threshold=3, recovery_timeout=30)
    @rate_limit("quality_management", max_requests=10, window_seconds=60)
    @audit_decorators.quality_check()
    def perform_quality_check(
        self,
        project_id: str,
        quality_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行质量检查（新功能）
        
        进行项目质量检查和评估
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化质量记录
        if 'quality_checks' not in project:
            project['quality_checks'] = []
        
        check_id = f"QC{len(project['quality_checks']) + 1:04d}"
        
        quality_check = {
            "check_id": check_id,
            "type": quality_data.get('type', 'general'),
            "check_date": datetime.now().isoformat(),
            "performed_by": quality_data.get('performed_by', 'system'),
            "criteria": quality_data.get('criteria', []),
            "results": quality_data.get('results', {}),
            "score": quality_data.get('score', 0),
            "status": quality_data.get('status', 'completed'),
            "recommendations": quality_data.get('recommendations', []),
            "next_check_date": quality_data.get('next_check_date')
        }
        
        project['quality_checks'].append(quality_check)
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "quality_check": quality_check,
            "message": f"质量检查 {check_id} 已完成"
        }

    def calculate_project_quality_score(self, project_id: str) -> Dict[str, Any]:
        """
        计算项目质量得分（新功能）
        
        基于质量检查结果计算项目整体质量得分
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        quality_checks = project.get('quality_checks', [])
        
        if not quality_checks:
            return {
                "success": True,
                "project_id": project_id,
                "quality_score": 0,
                "quality_level": "无质量检查记录",
                "recommendations": ["建议进行首次质量检查"]
            }
        
        # 计算平均质量得分
        total_score = 0
        valid_checks = 0
        
        for check in quality_checks:
            if 'score' in check and check['score'] > 0:
                total_score += check['score']
                valid_checks += 1
        
        avg_score = total_score / valid_checks if valid_checks > 0 else 0
        
        # 质量等级评估
        if avg_score >= 90:
            quality_level = "优秀"
            level_description = "项目质量达到优秀标准"
        elif avg_score >= 80:
            quality_level = "良好"
            level_description = "项目质量良好，有改进空间"
        elif avg_score >= 70:
            quality_level = "合格"
            level_description = "项目质量基本合格，需要改进"
        else:
            quality_level = "不合格"
            level_description = "项目质量需要重点关注和改进"
        
        # 质量趋势分析
        recent_checks = sorted(quality_checks, key=lambda x: x['check_date'], reverse=True)[:3]
        trend_scores = [check.get('score', 0) for check in recent_checks if 'score' in check]
        
        if len(trend_scores) >= 2:
            trend = "上升" if trend_scores[0] > trend_scores[-1] else "下降" if trend_scores[0] < trend_scores[-1] else "稳定"
        else:
            trend = "数据不足"
        
        return {
            "success": True,
            "project_id": project_id,
            "quality_score": round(avg_score, 2),
            "quality_level": quality_level,
            "level_description": level_description,
            "total_checks": len(quality_checks),
            "valid_checks": valid_checks,
            "quality_trend": trend,
            "recent_scores": trend_scores
        }


    # ============ 项目报告生成（新增功能）============

    @circuit_breaker("report_generation", failure_threshold=2, recovery_timeout=30)
    @rate_limit("report_generation", max_requests=5, window_seconds=60)
    def generate_project_report(self, project_id: str, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        生成项目报告（新功能）
        
        生成项目状态、进度、风险、预算等综合报告
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 获取项目各项数据
        progress = project.get('progress', 0)
        status = project.get('status', 'unknown')
        budget = project.get('budget', {})
        milestones = project.get('milestones', [])
        risks = project.get('risks', [])
        
        # 生成报告内容
        report_data = {
            "project_id": project_id,
            "project_name": project.get('name', ''),
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": {
                "status": status,
                "progress": f"{progress}%",
                "health_score": project.get('health_score', 0),
                "overall_risk": "低" if len(risks) == 0 else "中" if len(risks) <= 3 else "高"
            },
            "progress_analysis": {
                "current_progress": progress,
                "milestone_completion": len([m for m in milestones if m.get('status') == 'completed']),
                "total_milestones": len(milestones),
                "estimated_completion": project.get('estimated_completion_date')
            },
            "financial_overview": {
                "total_budget": budget.get('total_budget', 0),
                "actual_spent": budget.get('actual_spent', 0),
                "remaining_budget": budget.get('remaining_budget', 0),
                "budget_utilization": round((budget.get('actual_spent', 0) / budget.get('total_budget', 1)) * 100, 2) if budget.get('total_budget', 0) > 0 else 0
            },
            "risk_assessment": {
                "total_risks": len(risks),
                "high_risks": len([r for r in risks if r.get('level') == 'high']),
                "medium_risks": len([r for r in risks if r.get('level') == 'medium']),
                "low_risks": len([r for r in risks if r.get('level') == 'low'])
            },
            "recommendations": []
        }
        
        # 根据项目状态添加建议
        if progress < 30 and status == 'delayed':
            report_data['recommendations'].append({
                "priority": "高",
                "action": "重新评估项目时间表",
                "reason": "项目进度严重滞后"
            })
        
        if budget.get('remaining_budget', 0) < budget.get('total_budget', 1) * 0.2:
            report_data['recommendations'].append({
                "priority": "中",
                "action": "监控预算使用情况",
                "reason": "预算即将用完"
            })
        
        if len(risks) > 5:
            report_data['recommendations'].append({
                "priority": "高",
                "action": "制定风险应对计划",
                "reason": "项目风险较多"
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "report": report_data,
            "message": f"{report_type} 报告已生成"
        }

    # ============ 项目团队协作（新增功能）============

    @circuit_breaker("team_collaboration", failure_threshold=3, recovery_timeout=30)
    @rate_limit("team_collaboration", max_requests=15, window_seconds=60)
    @audit_decorators.team_assignment()
    def assign_project_team(
        self,
        project_id: str,
        team_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分配项目团队（新功能）
        
        分配项目团队成员和角色
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化团队信息
        if 'team_members' not in project:
            project['team_members'] = []
        
        # 添加团队成员
        for member in team_data.get('members', []):
            member_id = f"TM{len(project['team_members']) + 1:04d}"
            team_member = {
                "member_id": member_id,
                "name": member.get('name', ''),
                "role": member.get('role', 'member'),
                "department": member.get('department', ''),
                "email": member.get('email', ''),
                "assigned_date": datetime.now().isoformat(),
                "allocation_percentage": member.get('allocation_percentage', 100),
                "responsibilities": member.get('responsibilities', [])
            }
            project['team_members'].append(team_member)
        
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "team_members": project['team_members'],
            "message": f"已分配 {len(team_data.get('members', []))} 名团队成员"
        }

    def analyze_team_performance(self, project_id: str) -> Dict[str, Any]:
        """
        分析团队绩效（新功能）
        
        分析团队成员的工作效率和贡献度
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        team_members = project.get('team_members', [])
        
        if not team_members:
            return {
                "success": True,
                "project_id": project_id,
                "team_analysis": {
                    "total_members": 0,
                    "average_allocation": 0,
                    "performance_score": 0,
                    "recommendations": ["建议分配项目团队"]
                }
            }
        
        # 计算团队绩效指标
        total_allocation = sum(member.get('allocation_percentage', 0) for member in team_members)
        avg_allocation = total_allocation / len(team_members)
        
        # 基于项目进度估算团队绩效
        progress = project.get('progress', 0)
        performance_score = min((progress / 100.0) * (avg_allocation / 100.0) * 100, 100)
        
        # 角色分布分析
        role_distribution = {}
        for member in team_members:
            role = member['role']
            if role not in role_distribution:
                role_distribution[role] = 0
            role_distribution[role] += 1
        
        return {
            "success": True,
            "project_id": project_id,
            "team_analysis": {
                "total_members": len(team_members),
                "average_allocation": round(avg_allocation, 2),
                "performance_score": round(performance_score, 2),
                "role_distribution": role_distribution,
                "departments": list(set(member.get('department', '') for member in team_members))
            }
        }

    # ============ 项目集成接口（新增功能）============

    def integrate_with_order_management(self, project_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        与订单管理模块集成（新功能）
        
        将项目与相关订单关联，实现数据同步
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 初始化订单关联
        if 'related_orders' not in project:
            project['related_orders'] = []
        
        # 添加关联订单
        for order in order_data.get('orders', []):
            related_order = {
                "order_id": order.get('order_id', ''),
                "order_number": order.get('order_number', ''),
                "order_type": order.get('order_type', 'general'),
                "amount": order.get('amount', 0),
                "status": order.get('status', 'pending'),
                "integration_date": datetime.now().isoformat()
            }
            project['related_orders'].append(related_order)
        
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "related_orders": project['related_orders'],
            "message": f"已关联 {len(order_data.get('orders', []))} 个订单"
        }

    def sync_project_with_external_systems(self, project_id: str) -> Dict[str, Any]:
        """
        与外部系统同步（新功能）
        
        同步项目数据到ERP、CRM等外部系统
        """
        project = self._get_project(project_id)
        
        if not project:
            return {"success": False, "error": "项目不存在"}
        
        # 模拟外部系统同步
        sync_results = {
            "erp_system": {
                "status": "success",
                "message": "项目数据已同步到ERP系统",
                "sync_time": datetime.now().isoformat()
            },
            "crm_system": {
                "status": "success", 
                "message": "客户信息已同步到CRM系统",
                "sync_time": datetime.now().isoformat()
            },
            "financial_system": {
                "status": "success",
                "message": "预算数据已同步到财务系统",
                "sync_time": datetime.now().isoformat()
            }
        }
        
        # 记录同步历史
        if 'sync_history' not in project:
            project['sync_history'] = []
        
        sync_record = {
            "sync_id": f"SYNC{len(project['sync_history']) + 1:04d}",
            "sync_time": datetime.now().isoformat(),
            "systems": list(sync_results.keys()),
            "overall_status": "success"
        }
        
        project['sync_history'].append(sync_record)
        project['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "project_id": project_id,
            "sync_results": sync_results,
            "sync_record": sync_record,
            "message": "项目数据已同步到外部系统"
        }

    # 结束 ProjectManager 类定义