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


# 全局实例
closed_loop_monitor = ClosedLoopMonitor()








