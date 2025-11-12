"""
计划生成器
生成智能工作计划
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class PlanGenerator:
    """
    计划生成器
    
    功能：
    1. 从任务生成工作计划
    2. 任务排序和优先级
    3. 时间规划
    4. 资源分配
    """
    
    def __init__(self, task_analyzer=None):
        self.task_analyzer = task_analyzer
    
    def generate_plan(
        self,
        tasks: List[Dict[str, Any]],
        start_date: Optional[str] = None,
        duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        生成工作计划
        
        Args:
            tasks: 任务列表
            start_date: 开始日期（可选）
            duration_days: 计划时长（天）
            
        Returns:
            工作计划
        """
        if not start_date:
            start_date = datetime.now().isoformat()
        
        # 分析每个任务
        analyzed_tasks = []
        if self.task_analyzer:
            for task in tasks:
                analysis = await self.task_analyzer.analyze_task(task)
                task["analysis"] = analysis
                analyzed_tasks.append(task)
        else:
            analyzed_tasks = tasks
        
        # 按优先级和复杂度排序
        sorted_tasks = sorted(
            analyzed_tasks,
            key=lambda x: (
                -x.get("priority", 0),
                x.get("analysis", {}).get("complexity", "medium") == "simple"
            )
        )
        
        # 分配时间
        plan_tasks = []
        current_date = datetime.fromisoformat(start_date)
        
        for task in sorted_tasks:
            # 使用分析结果估算时长
            if self.task_analyzer and task.get("analysis"):
                estimated_hours = task["analysis"].get("estimated_time_hours", 2.0)
            else:
                estimated_hours = self._estimate_task_duration(task)
            
            plan_tasks.append({
                **task,
                "scheduled_date": current_date.isoformat(),
                "estimated_hours": estimated_hours,
                "estimated_completion": (current_date + timedelta(hours=estimated_hours)).isoformat()
            })
            
            # 移动到下一个时间段
            current_date += timedelta(hours=estimated_hours)
        
        plan = {
            "id": len(plan_tasks),
            "tasks": plan_tasks,
            "start_date": start_date,
            "end_date": current_date.isoformat(),
            "duration_days": duration_days,
            "total_tasks": len(plan_tasks),
            "created_at": datetime.now().isoformat()
        }
        
        return plan
    
    def _estimate_task_duration(self, task: Dict[str, Any]) -> float:
        """估算任务时长（小时）"""
        # TODO: 基于任务类型和历史数据估算
        priority = task.get("priority", 2)
        
        # 优先级越高，估算时长越短
        base_hours = 2.0
        if priority >= 4:
            return base_hours * 0.5  # 紧急任务，0.5小时
        elif priority >= 3:
            return base_hours  # 高优先级，1小时
        else:
            return base_hours * 2  # 普通任务，2小时

