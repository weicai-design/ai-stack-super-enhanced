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
    
    def complete_milestone(
        self,
        milestone_id: str,
        completion_note: str = ""
    ) -> Dict[str, Any]:
        """完成里程碑"""
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
        
        return {
            "success": True,
            "milestone": milestone,
            "project_progress": project['progress'] if project else 0,
            "message": "里程碑已完成"
        }
    
    # ============ 项目执行 ============
    
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


# 全局实例
project_manager = ProjectManager()
