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


# 全局实例
project_manager = ProjectManager()
