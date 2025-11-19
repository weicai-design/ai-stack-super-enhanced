"""任务管理器"""
import logging
from typing import Dict, List
from collections import defaultdict
from .models import Task, TaskPlan, TaskExecution

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, List[Task]] = defaultdict(list)
        self.plans: Dict[str, List[TaskPlan]] = defaultdict(list)
        self.executions: Dict[str, List[TaskExecution]] = defaultdict(list)
        logger.info("✅ 任务管理器已初始化")
    
    def create_task(self, tenant_id: str, task: Task) -> Task:
        task.tenant_id = tenant_id
        self.tasks[tenant_id].append(task)
        return task
    
    def create_plan(self, tenant_id: str, plan: TaskPlan) -> TaskPlan:
        plan.tenant_id = tenant_id
        self.plans[tenant_id].append(plan)
        return plan
    
    def execute_task(self, task_id: str, execution: TaskExecution) -> TaskExecution:
        self.executions[task_id].append(execution)
        return execution

task_manager = TaskManager()



























