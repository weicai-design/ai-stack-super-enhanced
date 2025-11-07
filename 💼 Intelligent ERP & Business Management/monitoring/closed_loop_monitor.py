"""
闭环监控系统
- 异常检测
- 改进跟踪
- 闭环验证
- 效果评估
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class IssueStatus(Enum):
    """问题状态"""
    DETECTED = "已发现"
    ANALYZING = "分析中"
    FIXING = "修复中"
    VERIFYING = "验证中"
    CLOSED = "已闭环"
    REOPENED = "重新打开"


class ClosedLoopMonitor:
    """闭环监控系统"""
    
    def __init__(self):
        # 问题记录
        self.issues = []
        
        # 改进记录
        self.improvements = []
    
    # ============ 问题检测 ============
    
    def detect_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测并记录问题
        
        Args:
            issue_data: {
                "module": "模块名称（财务/生产/质量等）",
                "issue_type": "问题类型",
                "severity": "严重程度（低/中/高/紧急）",
                "description": "问题描述",
                "detected_by": "检测方式（系统自动/用户反馈）",
                "data": "相关数据"
            }
        
        Returns:
            问题记录
        """
        try:
            issue_id = f"ISSUE{len(self.issues) + 1:04d}"
            
            issue = {
                "issue_id": issue_id,
                "module": issue_data['module'],
                "issue_type": issue_data['issue_type'],
                "severity": issue_data.get('severity', '中'),
                "description": issue_data['description'],
                "detected_by": issue_data.get('detected_by', '系统自动'),
                "status": IssueStatus.DETECTED.value,
                "data": issue_data.get('data', {}),
                "detected_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "improvements": [],  # 关联的改进措施
                "verification_results": []  # 验证结果
            }
            
            self.issues.append(issue)
            
            return {
                "success": True,
                "issue": issue,
                "message": f"问题已记录：{issue_id}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 改进措施 ============
    
    def create_improvement(self, improvement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建改进措施
        
        Args:
            improvement_data: {
                "issue_id": "关联的问题ID",
                "improvement_type": "改进类型",
                "description": "改进措施描述",
                "responsible_person": "责任人",
                "target_date": "目标完成日期",
                "action_plan": "行动计划"
            }
        
        Returns:
            改进记录
        """
        try:
            # 查找关联问题
            issue = next((i for i in self.issues 
                         if i['issue_id'] == improvement_data['issue_id']), None)
            
            if not issue:
                return {
                    "success": False,
                    "error": f"问题 {improvement_data['issue_id']} 不存在"
                }
            
            improvement_id = f"IMP{len(self.improvements) + 1:04d}"
            
            improvement = {
                "improvement_id": improvement_id,
                "issue_id": improvement_data['issue_id'],
                "improvement_type": improvement_data['improvement_type'],
                "description": improvement_data['description'],
                "responsible_person": improvement_data.get('responsible_person'),
                "target_date": improvement_data.get('target_date'),
                "action_plan": improvement_data.get('action_plan', []),
                "status": "计划中",
                "progress": 0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "completion_date": None
            }
            
            self.improvements.append(improvement)
            
            # 更新问题状态
            issue['status'] = IssueStatus.FIXING.value
            issue['improvements'].append(improvement_id)
            issue['updated_at'] = datetime.utcnow().isoformat()
            
            return {
                "success": True,
                "improvement": improvement,
                "message": f"改进措施已创建：{improvement_id}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_improvement_progress(
        self,
        improvement_id: str,
        progress: int,
        note: str = ""
    ) -> Dict[str, Any]:
        """
        更新改进进度
        
        Args:
            improvement_id: 改进ID
            progress: 进度（0-100）
            note: 进度说明
        
        Returns:
            更新结果
        """
        try:
            improvement = next((i for i in self.improvements 
                              if i['improvement_id'] == improvement_id), None)
            
            if not improvement:
                return {
                    "success": False,
                    "error": f"改进措施 {improvement_id} 不存在"
                }
            
            improvement['progress'] = min(100, max(0, progress))
            improvement['updated_at'] = datetime.utcnow().isoformat()
            
            # 添加进度记录
            if 'progress_history' not in improvement:
                improvement['progress_history'] = []
            
            improvement['progress_history'].append({
                "progress": progress,
                "note": note,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 如果达到100%，标记为完成
            if progress >= 100:
                improvement['status'] = "已完成"
                improvement['completion_date'] = datetime.utcnow().isoformat()
                
                # 触发验证流程
                issue_id = improvement['issue_id']
                self._trigger_verification(issue_id)
            
            return {
                "success": True,
                "improvement": improvement,
                "message": f"改进进度已更新：{progress}%"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 验证和闭环 ============
    
    def _trigger_verification(self, issue_id: str):
        """触发验证流程"""
        issue = next((i for i in self.issues if i['issue_id'] == issue_id), None)
        
        if issue:
            issue['status'] = IssueStatus.VERIFYING.value
            issue['updated_at'] = datetime.utcnow().isoformat()
    
    def verify_improvement(
        self,
        issue_id: str,
        verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证改进效果
        
        Args:
            issue_id: 问题ID
            verification_data: {
                "verified_by": "验证人",
                "result": "通过/不通过",
                "evidence": "验证依据",
                "note": "备注"
            }
        
        Returns:
            验证结果
        """
        try:
            issue = next((i for i in self.issues if i['issue_id'] == issue_id), None)
            
            if not issue:
                return {
                    "success": False,
                    "error": f"问题 {issue_id} 不存在"
                }
            
            verification = {
                "verified_by": verification_data['verified_by'],
                "result": verification_data['result'],
                "evidence": verification_data.get('evidence', ''),
                "note": verification_data.get('note', ''),
                "verified_at": datetime.utcnow().isoformat()
            }
            
            issue['verification_results'].append(verification)
            issue['updated_at'] = datetime.utcnow().isoformat()
            
            # 如果验证通过，闭环
            if verification_data['result'] == '通过':
                issue['status'] = IssueStatus.CLOSED.value
                issue['closed_at'] = datetime.utcnow().isoformat()
                
                # 计算闭环周期
                detected_at = datetime.fromisoformat(issue['detected_at'])
                closed_at = datetime.utcnow()
                cycle_days = (closed_at - detected_at).days
                issue['cycle_days'] = cycle_days
            
            else:
                # 验证不通过，重新打开
                issue['status'] = IssueStatus.REOPENED.value
            
            return {
                "success": True,
                "issue": issue,
                "message": f"验证结果已记录：{verification_data['result']}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 统计和分析 ============
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """获取监控看板数据"""
        try:
            total_issues = len(self.issues)
            
            # 按状态统计
            status_stats = {}
            for issue in self.issues:
                status = issue['status']
                status_stats[status] = status_stats.get(status, 0) + 1
            
            # 按严重程度统计
            severity_stats = {}
            for issue in self.issues:
                severity = issue['severity']
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            # 闭环率
            closed_count = status_stats.get(IssueStatus.CLOSED.value, 0)
            closure_rate = (closed_count / total_issues * 100) if total_issues > 0 else 0
            
            # 平均闭环周期
            closed_issues = [i for i in self.issues if i['status'] == IssueStatus.CLOSED.value]
            avg_cycle = (sum(i.get('cycle_days', 0) for i in closed_issues) / len(closed_issues)) \
                       if closed_issues else 0
            
            return {
                "success": True,
                "dashboard": {
                    "total_issues": total_issues,
                    "status_distribution": status_stats,
                    "severity_distribution": severity_stats,
                    "closure_rate": float(closure_rate),
                    "average_cycle_days": float(avg_cycle),
                    "active_improvements": len([i for i in self.improvements 
                                               if i['status'] != '已完成'])
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_issue_list(
        self,
        module: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取问题列表"""
        try:
            filtered = self.issues
            
            if module:
                filtered = [i for i in filtered if i['module'] == module]
            if status:
                filtered = [i for i in filtered if i['status'] == status]
            if severity:
                filtered = [i for i in filtered if i['severity'] == severity]
            
            return {
                "success": True,
                "issues": filtered,
                "total": len(filtered)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


    def get_improvement_progress(
        self,
        issue_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取改进进度追踪
        
        Args:
            issue_id: 问题ID（可选）
        
        Returns:
            改进进度列表
        """
        try:
            filtered_improvements = self.improvements
            
            if issue_id:
                filtered_improvements = [
                    i for i in self.improvements 
                    if i['issue_id'] == issue_id
                ]
            
            # 计算总体进度
            total_progress = 0
            if filtered_improvements:
                total_progress = sum(i['progress'] for i in filtered_improvements) / len(filtered_improvements)
            
            return {
                "success": True,
                "improvements": filtered_improvements,
                "total_count": len(filtered_improvements),
                "average_progress": round(total_progress, 2)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_module_analysis(self, module: str) -> Dict[str, Any]:
        """
        获取模块分析
        
        Args:
            module: 模块名称
        
        Returns:
            模块问题分析
        """
        try:
            module_issues = [i for i in self.issues if i['module'] == module]
            
            if not module_issues:
                return {
                    "success": True,
                    "module": module,
                    "message": "该模块暂无问题记录"
                }
            
            # 统计分析
            total = len(module_issues)
            closed = len([i for i in module_issues if i['status'] == IssueStatus.CLOSED.value])
            active = total - closed
            
            # 问题类型分布
            type_dist = {}
            for issue in module_issues:
                itype = issue['issue_type']
                type_dist[itype] = type_dist.get(itype, 0) + 1
            
            # 平均闭环周期
            closed_issues = [i for i in module_issues if i['status'] == IssueStatus.CLOSED.value and 'cycle_days' in i]
            avg_cycle = (sum(i['cycle_days'] for i in closed_issues) / len(closed_issues)) if closed_issues else 0
            
            return {
                "success": True,
                "module": module,
                "analysis": {
                    "total_issues": total,
                    "closed_issues": closed,
                    "active_issues": active,
                    "closure_rate": round((closed / total * 100), 2),
                    "average_cycle_days": round(avg_cycle, 2),
                    "issue_type_distribution": type_dist
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trend_analysis(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        获取趋势分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            趋势分析数据
        """
        try:
            # 筛选时间范围内的问题
            issues_in_range = [
                i for i in self.issues
                if start_date <= i['detected_at'][:10] <= end_date
            ]
            
            # 按日期统计
            daily_stats = {}
            for issue in issues_in_range:
                date = issue['detected_at'][:10]
                if date not in daily_stats:
                    daily_stats[date] = {
                        "detected": 0,
                        "closed": 0
                    }
                daily_stats[date]["detected"] += 1
                
                if issue['status'] == IssueStatus.CLOSED.value and issue.get('closed_at'):
                    closed_date = issue['closed_at'][:10]
                    if start_date <= closed_date <= end_date:
                        if closed_date not in daily_stats:
                            daily_stats[closed_date] = {"detected": 0, "closed": 0}
                        daily_stats[closed_date]["closed"] += 1
            
            # 按模块统计趋势
            module_trends = {}
            for issue in issues_in_range:
                module = issue['module']
                if module not in module_trends:
                    module_trends[module] = {
                        "detected": 0,
                        "closed": 0,
                        "avg_cycle_days": 0
                    }
                module_trends[module]["detected"] += 1
                
                if issue['status'] == IssueStatus.CLOSED.value:
                    module_trends[module]["closed"] += 1
            
            return {
                "success": True,
                "period": {"start": start_date, "end": end_date},
                "daily_statistics": daily_stats,
                "module_trends": module_trends,
                "total_detected": len(issues_in_range)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def auto_detect_anomalies(
        self,
        module: str,
        metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        自动检测异常
        
        Args:
            module: 模块名称
            metrics: 指标数据 {"metric_name": value}
        
        Returns:
            检测到的异常列表
        """
        anomalies = []
        
        # 预定义的异常规则
        anomaly_rules = {
            "quality_pass_rate": {
                "threshold": 95,
                "operator": "<",
                "severity": "高",
                "description": "质量合格率低于95%"
            },
            "on_time_delivery_rate": {
                "threshold": 90,
                "operator": "<",
                "severity": "中",
                "description": "准时交付率低于90%"
            },
            "inventory_turnover": {
                "threshold": 0.5,
                "operator": "<",
                "severity": "低",
                "description": "库存周转率过低"
            },
            "cost_variance": {
                "threshold": 10,
                "operator": ">",
                "severity": "中",
                "description": "成本偏差超过10%"
            }
        }
        
        for metric_name, value in metrics.items():
            if metric_name in anomaly_rules:
                rule = anomaly_rules[metric_name]
                threshold = rule["threshold"]
                
                is_anomaly = False
                if rule["operator"] == "<" and value < threshold:
                    is_anomaly = True
                elif rule["operator"] == ">" and value > threshold:
                    is_anomaly = True
                
                if is_anomaly:
                    # 自动记录问题
                    anomaly_result = self.detect_issue({
                        "module": module,
                        "issue_type": f"{metric_name}_异常",
                        "severity": rule["severity"],
                        "description": f"{rule['description']}: 当前值{value}, 阈值{threshold}",
                        "detected_by": "系统自动",
                        "data": {
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold
                        }
                    })
                    
                    if anomaly_result["success"]:
                        anomalies.append(anomaly_result["issue"])
        
        return anomalies
    
    def generate_closed_loop_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        生成闭环监控报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            闭环监控报告
        """
        try:
            # 筛选时间范围内的问题
            issues_in_range = [
                i for i in self.issues
                if start_date <= i['detected_at'][:10] <= end_date
            ]
            
            total_issues = len(issues_in_range)
            
            # 按状态统计
            status_summary = {}
            for issue in issues_in_range:
                status = issue['status']
                status_summary[status] = status_summary.get(status, 0) + 1
            
            # 闭环统计
            closed_issues = [i for i in issues_in_range if i['status'] == IssueStatus.CLOSED.value]
            closure_rate = (len(closed_issues) / total_issues * 100) if total_issues > 0 else 0
            
            # 平均闭环周期
            avg_cycle_days = (sum(i.get('cycle_days', 0) for i in closed_issues) / len(closed_issues)) if closed_issues else 0
            
            # 按模块统计
            module_summary = {}
            for issue in issues_in_range:
                module = issue['module']
                if module not in module_summary:
                    module_summary[module] = {
                        "total": 0,
                        "closed": 0,
                        "active": 0
                    }
                module_summary[module]["total"] += 1
                if issue['status'] == IssueStatus.CLOSED.value:
                    module_summary[module]["closed"] += 1
                else:
                    module_summary[module]["active"] += 1
            
            # 改进措施统计
            improvements_in_range = [
                imp for imp in self.improvements
                if imp['issue_id'] in [i['issue_id'] for i in issues_in_range]
            ]
            
            total_improvements = len(improvements_in_range)
            completed_improvements = len([i for i in improvements_in_range if i['status'] == '已完成'])
            
            # TOP问题类型
            issue_type_count = {}
            for issue in issues_in_range:
                itype = issue['issue_type']
                issue_type_count[itype] = issue_type_count.get(itype, 0) + 1
            
            top_issue_types = sorted(
                issue_type_count.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            report = {
                "report_period": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "generated_at": datetime.utcnow().isoformat()
                },
                "executive_summary": {
                    "total_issues_detected": total_issues,
                    "total_issues_closed": len(closed_issues),
                    "closure_rate_percent": round(closure_rate, 2),
                    "average_cycle_days": round(avg_cycle_days, 2),
                    "total_improvements": total_improvements,
                    "completed_improvements": completed_improvements
                },
                "status_breakdown": status_summary,
                "module_performance": module_summary,
                "top_issue_types": dict(top_issue_types),
                "active_high_severity": len([
                    i for i in issues_in_range
                    if i['severity'] in ['高', '紧急'] and i['status'] != IssueStatus.CLOSED.value
                ])
            }
            
            return {
                "success": True,
                "report": report
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 高级功能（新增）============
    
    def intelligent_root_cause_analysis(self, issue_id: str) -> Dict[str, Any]:
        """
        智能根因分析（新功能）
        
        使用5Why方法和数据分析自动推断问题根本原因
        """
        try:
            issue = next((i for i in self.issues if i['issue_id'] == issue_id), None)
            
            if not issue:
                return {"success": False, "error": "问题不存在"}
            
            # 根据问题类型和模块推断可能的根因
            root_causes = []
            
            # 质量相关
            if issue['module'] == '质量管理' or 'quality' in issue['issue_type'].lower():
                root_causes = [
                    {"level": 1, "why": "为什么出现质量问题？", "possible_cause": "生产过程控制不足"},
                    {"level": 2, "why": "为什么控制不足？", "possible_cause": "缺少标准操作程序或员工未遵守"},
                    {"level": 3, "why": "为什么没有遵守？", "possible_cause": "培训不足或监督不到位"},
                    {"level": 4, "why": "为什么培训不足？", "possible_cause": "培训体系不完善"},
                    {"level": 5, "why": "为什么体系不完善？", "possible_cause": "质量管理重视程度不够"}
                ]
            
            # 成本相关
            elif issue['module'] == '财务管理' and 'cost' in issue['issue_type'].lower():
                root_causes = [
                    {"level": 1, "why": "为什么成本超支？", "possible_cause": "实际消耗超过预算"},
                    {"level": 2, "why": "为什么消耗超标？", "possible_cause": "采购价格上涨或浪费增加"},
                    {"level": 3, "why": "为什么价格上涨？", "possible_cause": "供应商选择不当或缺少议价"},
                    {"level": 4, "why": "为什么选择不当？", "possible_cause": "供应商评估体系不完善"},
                    {"level": 5, "why": "为什么体系不完善？", "possible_cause": "采购管理流程缺失"}
                ]
            
            # 延期相关
            elif 'delay' in issue['issue_type'].lower() or 'overdue' in issue['issue_type'].lower():
                root_causes = [
                    {"level": 1, "why": "为什么延期？", "possible_cause": "资源不足或进度滞后"},
                    {"level": 2, "why": "为什么资源不足？", "possible_cause": "计划不合理或临时任务增加"},
                    {"level": 3, "why": "为什么计划不合理？", "possible_cause": "缺少科学的排程方法"},
                    {"level": 4, "why": "为什么缺少方法？", "possible_cause": "未使用智能排产系统"},
                    {"level": 5, "why": "为什么未使用？", "possible_cause": "系统尚未部署或人员不熟悉"}
                ]
            
            else:
                root_causes = [
                    {"level": 1, "why": "问题表象", "possible_cause": "需要具体分析"},
                    {"level": 2, "why": "直接原因", "possible_cause": "待调查"},
                    {"level": 3, "why": "间接原因", "possible_cause": "待调查"},
                    {"level": 4, "why": "系统原因", "possible_cause": "待调查"},
                    {"level": 5, "why": "根本原因", "possible_cause": "待调查"}
                ]
            
            # 推荐改进措施
            corrective_actions = [
                "短期措施：立即解决表面问题",
                "中期措施：完善相关流程和制度",
                "长期措施：建立预防机制和监控系统"
            ]
            
            return {
                "success": True,
                "issue_id": issue_id,
                "issue_type": issue['issue_type'],
                "module": issue['module'],
                "five_why_analysis": root_causes,
                "probable_root_cause": root_causes[-1]["possible_cause"] if root_causes else "需要深入分析",
                "corrective_actions": corrective_actions,
                "analysis_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def continuous_improvement_maturity_assessment(self) -> Dict[str, Any]:
        """
        持续改进成熟度评估（新功能）
        
        评估组织的持续改进能力成熟度
        """
        try:
            # 计算各项指标
            total_issues = len(self.issues)
            closed_issues = [i for i in self.issues if i['status'] == IssueStatus.CLOSED.value]
            
            if total_issues == 0:
                return {
                    "success": True,
                    "maturity_level": "初级",
                    "message": "暂无问题记录，无法评估"
                }
            
            # 1. 问题发现能力（25分）
            system_detected = len([i for i in self.issues if i.get('detected_by') == '系统自动'])
            detection_score = min(25, (system_detected / total_issues * 100) / 4)
            
            # 2. 闭环完成率（30分）
            closure_rate = (len(closed_issues) / total_issues * 100)
            closure_score = min(30, closure_rate / 100 * 30)
            
            # 3. 响应速度（20分）
            if closed_issues:
                avg_cycle = sum(i.get('cycle_days', 30) for i in closed_issues) / len(closed_issues)
                if avg_cycle <= 7:
                    response_score = 20
                elif avg_cycle <= 14:
                    response_score = 15
                elif avg_cycle <= 30:
                    response_score = 10
                else:
                    response_score = 5
            else:
                response_score = 0
            
            # 4. 改进执行力（25分）
            total_improvements = len(self.improvements)
            completed_improvements = len([i for i in self.improvements if i['status'] == '已完成'])
            improvement_rate = (completed_improvements / total_improvements * 100) if total_improvements > 0 else 0
            execution_score = min(25, improvement_rate / 100 * 25)
            
            # 总分
            total_score = detection_score + closure_score + response_score + execution_score
            
            # 成熟度等级
            if total_score >= 85:
                maturity_level = "5级-优化级"
                description = "持续改进文化深入，系统高效运转"
            elif total_score >= 70:
                maturity_level = "4级-量化管理级"
                description = "改进活动有数据支撑，效果可衡量"
            elif total_score >= 55:
                maturity_level = "3级-已定义级"
                description = "改进流程已建立，但需加强执行"
            elif total_score >= 40:
                maturity_level = "2级-可重复级"
                description = "有基本的改进活动，但不够系统"
            else:
                maturity_level = "1级-初始级"
                description = "改进活动零散，缺少系统性"
            
            # 提升建议
            recommendations = []
            if detection_score < 15:
                recommendations.append("加强自动检测能力，减少依赖人工发现")
            if closure_score < 20:
                recommendations.append("提高问题闭环率，确保问题得到根本解决")
            if response_score < 15:
                recommendations.append("缩短响应时间，快速处理问题")
            if execution_score < 18:
                recommendations.append("提升改进措施执行力，确保落地")
            
            return {
                "success": True,
                "maturity_assessment": {
                    "total_score": round(total_score, 2),
                    "maturity_level": maturity_level,
                    "description": description
                },
                "score_breakdown": {
                    "detection_capability": round(detection_score, 2),
                    "closure_efficiency": round(closure_score, 2),
                    "response_speed": round(response_score, 2),
                    "execution_power": round(execution_score, 2)
                },
                "key_metrics": {
                    "total_issues": total_issues,
                    "closure_rate": round(closure_rate, 2),
                    "average_cycle_days": round(avg_cycle, 2) if closed_issues else 0,
                    "improvement_completion_rate": round(improvement_rate, 2)
                },
                "improvement_recommendations": recommendations,
                "assessment_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def improvement_effectiveness_prediction(
        self,
        improvement_id: str
    ) -> Dict[str, Any]:
        """
        改进效果预测（新功能）
        
        基于历史数据预测改进措施的效果
        """
        try:
            improvement = next((i for i in self.improvements 
                              if i['improvement_id'] == improvement_id), None)
            
            if not improvement:
                return {"success": False, "error": "改进措施不存在"}
            
            # 基于改进类型预测效果
            improvement_type = improvement.get('improvement_type', '流程优化')
            
            # 效果预测模型（简化）
            effect_models = {
                "流程优化": {
                    "expected_improvement": "15-25%",
                    "time_to_effect": "1-2个月",
                    "success_probability": 85,
                    "roi": "高"
                },
                "技术升级": {
                    "expected_improvement": "30-50%",
                    "time_to_effect": "3-6个月",
                    "success_probability": 70,
                    "roi": "很高"
                },
                "人员培训": {
                    "expected_improvement": "10-20%",
                    "time_to_effect": "2-3个月",
                    "success_probability": 75,
                    "roi": "中"
                },
                "制度完善": {
                    "expected_improvement": "20-30%",
                    "time_to_effect": "1-3个月",
                    "success_probability": 80,
                    "roi": "高"
                }
            }
            
            prediction = effect_models.get(improvement_type, {
                "expected_improvement": "10-20%",
                "time_to_effect": "1-3个月",
                "success_probability": 70,
                "roi": "中"
            })
            
            # 风险因素
            risk_factors = []
            if improvement['progress'] < 30:
                risk_factors.append("当前进度较慢，可能影响效果")
            
            # 关键成功因素
            success_factors = [
                "管理层支持",
                "充足的资源投入",
                "团队积极配合",
                "定期跟踪评估"
            ]
            
            return {
                "success": True,
                "improvement_id": improvement_id,
                "improvement_type": improvement_type,
                "current_progress": improvement['progress'],
                "effect_prediction": prediction,
                "risk_factors": risk_factors,
                "success_factors": success_factors,
                "recommendations": [
                    "定期review进度",
                    "及时调整策略",
                    "做好效果验证准备"
                ],
                "prediction_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局实例
closed_loop_monitor = ClosedLoopMonitor()







