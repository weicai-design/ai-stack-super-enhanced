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


# 全局实例
closed_loop_monitor = ClosedLoopMonitor()







