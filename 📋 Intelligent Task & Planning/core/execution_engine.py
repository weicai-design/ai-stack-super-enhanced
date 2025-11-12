"""
执行引擎
执行任务并监控进度
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

class ExecutionEngine:
    """
    执行引擎
    
    功能：
    1. 任务调度
    2. 调用相关模块执行
    3. 进度监控
    4. 结果反馈
    5. 异常处理
    """
    
    def __init__(self, module_executor=None, super_agent_integration=None):
        self.executing_tasks = {}
        self.execution_history = []
        self.module_executor = module_executor
        self.super_agent_integration = super_agent_integration
        
    async def execute_task(
        self,
        task: Dict[str, Any],
        module_executor: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务信息
            module_executor: 模块执行器
            
        Returns:
            执行结果
        """
        task_id = task.get("id")
        
        # 检查依赖
        dependencies = task.get("dependencies", [])
        if dependencies:
            for dep_id in dependencies:
                dep_task = self.execution_history[-1] if self.execution_history else None
                if not dep_task or dep_task.get("status") != "completed":
                    return {
                        "success": False,
                        "error": f"依赖任务 {dep_id} 未完成"
                    }
        
        # 开始执行
        task["status"] = "in_progress"
        task["started_at"] = datetime.now().isoformat()
        self.executing_tasks[task_id] = task
        
        try:
            # 调用模块执行器
            executor = module_executor or self.module_executor
            if executor:
                # 构建执行上下文
                execution_context = {
                    "task": task,
                    "module": self._identify_module(task),
                    "user_input": task.get("description", "")
                }
                result = await executor.execute(
                    expert={"module": execution_context["module"]},
                    input=task.get("description", ""),
                    context=execution_context
                )
            else:
                # 默认执行逻辑
                result = await self._default_execute(task)
            
            # 记录执行结果
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result
            
            self.execution_history.append(task)
            if task_id in self.executing_tasks:
                del self.executing_tasks[task_id]
            
            # 通知超级Agent任务完成
            if self.super_agent_integration:
                asyncio.create_task(
                    self.super_agent_integration.notify_task_completion(task_id, result)
                )
            
            return {
                "success": True,
                "task": task,
                "result": result
            }
            
        except Exception as e:
            # 执行失败
            task["status"] = "failed"
            task["error"] = str(e)
            task["failed_at"] = datetime.now().isoformat()
            
            self.execution_history.append(task)
            if task_id in self.executing_tasks:
                del self.executing_tasks[task_id]
            
            return {
                "success": False,
                "error": str(e),
                "task": task
            }
    
    async def _default_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """默认执行逻辑"""
        # TODO: 实现默认执行逻辑
        await asyncio.sleep(0.1)  # 模拟执行
        
        return {
            "message": f"任务 '{task.get('title')}' 执行完成",
            "execution_time": 0.1
        }
    
    def get_execution_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        if task_id in self.executing_tasks:
            return self.executing_tasks[task_id]
        
        # 从历史记录查找
        for task in self.execution_history:
            if task.get("id") == task_id:
                return task
        
        return None
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history[-limit:]
    
    def _identify_module(self, task: Dict[str, Any]) -> str:
        """识别任务所属模块"""
        description = task.get("description", "").lower()
        title = task.get("title", "").lower()
        text = f"{description} {title}"
        
        module_keywords = {
            "rag": ["知识", "文档", "检索", "RAG"],
            "erp": ["订单", "客户", "项目", "ERP", "企业"],
            "content": ["内容", "创作", "文章", "视频"],
            "trend": ["趋势", "分析", "预测"],
            "stock": ["股票", "交易", "投资"],
            "operations": ["运营", "管理", "数据分析"],
            "finance": ["财务", "价格", "成本"],
            "coding": ["代码", "编程", "开发", "函数"],
            "task": ["任务", "计划", "工作"]
        }
        
        for module, keywords in module_keywords.items():
            if any(keyword in text for keyword in keywords):
                return module
        
        return "general"

