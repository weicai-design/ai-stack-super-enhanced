"""
高级任务执行器
- 任务自动分解
- 并行执行
- 依赖管理
- 执行监控
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "待执行"
    RUNNING = "执行中"
    PAUSED = "已暂停"
    COMPLETED = "已完成"
    FAILED = "执行失败"
    CANCELLED = "已取消"


class AdvancedTaskExecutor:
    """高级任务执行器"""
    
    def __init__(self):
        # 任务队列
        self.tasks = []
        
        # 正在执行的任务
        self.running_tasks = {}
        
        # 执行历史
        self.execution_history = []
    
    # ============ 任务创建 ============
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建任务
        
        Args:
            task_data: {
                "name": "任务名称",
                "type": "任务类型",
                "steps": [任务步骤],
                "dependencies": [依赖的任务ID],
                "priority": "优先级（低/中/高/紧急）",
                "auto_execute": True/False,
                "params": {任务参数}
            }
        
        Returns:
            任务信息
        """
        try:
            task_id = f"TASK{len(self.tasks) + 1:04d}"
            
            task = {
                "task_id": task_id,
                "name": task_data['name'],
                "type": task_data.get('type', 'general'),
                "steps": task_data.get('steps', []),
                "dependencies": task_data.get('dependencies', []),
                "priority": task_data.get('priority', '中'),
                "auto_execute": task_data.get('auto_execute', False),
                "params": task_data.get('params', {}),
                "status": TaskStatus.PENDING.value,
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "start_time": None,
                "end_time": None,
                "result": None,
                "error": None
            }
            
            self.tasks.append(task)
            
            # 如果设置自动执行，加入执行队列
            if task['auto_execute']:
                asyncio.create_task(self.execute_task(task_id))
            
            return {
                "success": True,
                "task": task,
                "message": f"任务已创建：{task_id}"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 任务执行 ============
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            执行结果
        """
        try:
            task = self._get_task(task_id)
            if not task:
                return {
                    "success": False,
                    "error": f"任务 {task_id} 不存在"
                }
            
            # 检查依赖
            if not await self._check_dependencies(task):
                return {
                    "success": False,
                    "error": "任务依赖未满足"
                }
            
            # 更新状态
            task['status'] = TaskStatus.RUNNING.value
            task['start_time'] = datetime.now().isoformat()
            self.running_tasks[task_id] = task
            
            # 执行步骤
            step_results = []
            for i, step in enumerate(task['steps']):
                # 更新进度
                task['progress'] = int((i / len(task['steps'])) * 100)
                
                # 执行步骤
                step_result = await self._execute_step(step, task['params'])
                step_results.append(step_result)
                
                if not step_result.get('success'):
                    # 步骤失败
                    task['status'] = TaskStatus.FAILED.value
                    task['error'] = step_result.get('error')
                    break
            
            # 完成
            if task['status'] == TaskStatus.RUNNING.value:
                task['status'] = TaskStatus.COMPLETED.value
                task['progress'] = 100
            
            task['end_time'] = datetime.now().isoformat()
            task['result'] = step_results
            task['updated_at'] = datetime.now().isoformat()
            
            # 从运行列表移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # 记录历史
            self.execution_history.append({
                "task_id": task_id,
                "name": task['name'],
                "status": task['status'],
                "start_time": task['start_time'],
                "end_time": task['end_time'],
                "duration": self._calculate_duration(task['start_time'], task['end_time'])
            })
            
            return {
                "success": task['status'] == TaskStatus.COMPLETED.value,
                "task": task,
                "message": f"任务执行{'成功' if task['status'] == TaskStatus.COMPLETED.value else '失败'}"
            }
        
        except Exception as e:
            task['status'] = TaskStatus.FAILED.value
            task['error'] = str(e)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ 任务监控 ============
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        task = self._get_task(task_id)
        
        if not task:
            return {
                "success": False,
                "error": "任务不存在"
            }
        
        return {
            "success": True,
            "task": task
        }
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取任务列表"""
        tasks = self.tasks
        
        if status:
            tasks = [t for t in tasks if t['status'] == status]
        if priority:
            tasks = [t for t in tasks if t['priority'] == priority]
        
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }
    
    def get_running_tasks(self) -> Dict[str, Any]:
        """获取正在执行的任务"""
        return {
            "success": True,
            "running_tasks": list(self.running_tasks.values()),
            "count": len(self.running_tasks)
        }
    
    # ============ 任务控制 ============
    
    def pause_task(self, task_id: str) -> Dict[str, Any]:
        """暂停任务"""
        task = self._get_task(task_id)
        
        if not task:
            return {"success": False, "error": "任务不存在"}
        
        if task['status'] != TaskStatus.RUNNING.value:
            return {"success": False, "error": "任务未在运行"}
        
        task['status'] = TaskStatus.PAUSED.value
        task['updated_at'] = datetime.now().isoformat()
        
        return {
            "success": True,
            "task": task,
            "message": "任务已暂停"
        }
    
    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """恢复任务"""
        task = self._get_task(task_id)
        
        if not task:
            return {"success": False, "error": "任务不存在"}
        
        if task['status'] != TaskStatus.PAUSED.value:
            return {"success": False, "error": "任务未暂停"}
        
        # 重新执行
        asyncio.create_task(self.execute_task(task_id))
        
        return {
            "success": True,
            "message": "任务已恢复执行"
        }
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        task = self._get_task(task_id)
        
        if not task:
            return {"success": False, "error": "任务不存在"}
        
        task['status'] = TaskStatus.CANCELLED.value
        task['end_time'] = datetime.now().isoformat()
        task['updated_at'] = datetime.now().isoformat()
        
        # 从运行列表移除
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        return {
            "success": True,
            "task": task,
            "message": "任务已取消"
        }
    
    # ============ 任务分析 ============
    
    def analyze_task_performance(self) -> Dict[str, Any]:
        """任务性能分析"""
        total = len(self.execution_history)
        
        if total == 0:
            return {
                "success": True,
                "analysis": {
                    "total_tasks": 0,
                    "message": "暂无执行历史"
                }
            }
        
        completed = sum(1 for h in self.execution_history 
                       if h['status'] == TaskStatus.COMPLETED.value)
        failed = sum(1 for h in self.execution_history 
                    if h['status'] == TaskStatus.FAILED.value)
        
        avg_duration = sum(h.get('duration', 0) for h in self.execution_history) / total
        
        return {
            "success": True,
            "analysis": {
                "total_tasks": total,
                "completed": completed,
                "failed": failed,
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "average_duration": float(avg_duration)
            }
        }
    
    # ============ 内部辅助方法 ============
    
    def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务"""
        return next((t for t in self.tasks if t['task_id'] == task_id), None)
    
    async def _check_dependencies(self, task: Dict[str, Any]) -> bool:
        """检查任务依赖"""
        for dep_id in task.get('dependencies', []):
            dep_task = self._get_task(dep_id)
            if not dep_task or dep_task['status'] != TaskStatus.COMPLETED.value:
                return False
        
        return True
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        try:
            # 模拟步骤执行
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "step_name": step.get('name', 'unknown'),
                "result": "执行成功"
            }
        
        except Exception as e:
            return {
                "success": False,
                "step_name": step.get('name', 'unknown'),
                "error": str(e)
            }
    
    def _calculate_duration(self, start: str, end: str) -> float:
        """计算持续时间（秒）"""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            return (end_dt - start_dt).total_seconds()
        except:
            return 0.0


# 全局实例
task_executor = AdvancedTaskExecutor()








