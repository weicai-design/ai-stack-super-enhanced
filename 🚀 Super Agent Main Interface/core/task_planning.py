"""
智能工作计划系统
从备忘录提炼任务，生成工作计划
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from .task_templates import TaskTemplateLibrary

class TaskPlanning:
    """
    智能工作计划系统
    
    功能：
    1. 从备忘录提炼任务
    2. AI自动识别任务
    3. 用户确认机制
    4. 任务规划/执行/监控/分析
    """
    
    def __init__(self, memo_system=None):
        self.memo_system = memo_system
        self.tasks = []
        self.plans = []
        self.template_library = TaskTemplateLibrary()  # 任务模板库
        
    async def extract_tasks_from_memos(self) -> List[Dict[str, Any]]:
        """
        从备忘录中提炼任务⭐增强版
        
        Returns:
            提取的任务列表
        """
        if not self.memo_system:
            return []
        
        # 获取所有任务类型的备忘录（包括高重要性的note）
        task_memos = await self.memo_system.get_memos(type="task")
        important_notes = await self.memo_system.get_memos(importance=4)  # 高重要性笔记也可能包含任务
        
        all_memos = task_memos + [m for m in important_notes if m not in task_memos]
        
        extracted_tasks = []
        processed_memo_ids = set()
        
        for memo in all_memos:
            memo_id = memo.get("id")
            if memo_id in processed_memo_ids:
                continue
            
            content = memo.get("content", "")
            title = memo.get("title", content[:30] if content else "未命名任务")
            
            # 智能任务提炼：分析备忘录内容，提取关键任务信息
            task_info = self._analyze_task_from_memo(memo)
            
            if task_info["is_task"]:
                # 使用模板库推荐模板
                suggested_template = self.template_library.suggest_template(content)
                template_config = None
                if suggested_template:
                    template_config = self.template_library.create_task_from_template(
                        suggested_template,
                        {
                            "title": task_info.get("title", title),
                            "description": task_info.get("description", content)
                        }
                    )
                
                task = {
                    "id": len(self.tasks) + len(extracted_tasks) + 1,
                    "title": task_info.get("title", title),
                    "description": task_info.get("description", content),
                    "source": "memo",
                    "source_id": memo_id,
                    "importance": memo.get("importance", 3),
                    "priority": task_info.get("priority", "medium"),
                    "tags": memo.get("tags", []) + task_info.get("tags", []),
                    "due_date": task_info.get("due_date"),
                    "estimated_duration": task_info.get("estimated_duration") or (
                        template_config.get("estimated_duration") if template_config else 60
                    ),
                    "dependencies": task_info.get("dependencies", []) or (
                        template_config.get("dependencies", []) if template_config else []
                    ),
                    "steps": template_config.get("steps", []) if template_config else [],
                    "template_type": suggested_template,
                    "best_practices": template_config.get("best_practices", []) if template_config else [],
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "needs_confirmation": True,  # 需要用户确认
                    "extraction_confidence": task_info.get("confidence", 0.7)
                }
                extracted_tasks.append(task)
                processed_memo_ids.add(memo_id)
        
        # 将提取的任务添加到任务列表（待确认）
        self.tasks.extend(extracted_tasks)
        
        return extracted_tasks
    
    def _analyze_task_from_memo(self, memo: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析备忘录，提取任务信息⭐智能提炼
        
        Args:
            memo: 备忘录数据
            
        Returns:
            任务信息
        """
        content = memo.get("content", "")
        title = memo.get("title", "")
        tags = memo.get("tags", [])
        dates = memo.get("dates", [])
        times = memo.get("times", [])
        
        # 判断是否是任务
        task_indicators = [
            "需要", "应该", "记得", "要", "必须", "完成", "处理", "执行",
            "计划", "安排", "准备", "检查", "审核", "确认"
        ]
        is_task = any(indicator in content for indicator in task_indicators) or memo.get("type") == "task"
        
        # 提取任务标题（从内容中提取）
        task_title = title
        if not task_title or len(task_title) < 5:
            # 尝试从内容中提取第一句话作为标题
            sentences = content.split("。")
            if sentences:
                task_title = sentences[0][:50]
        
        # 提取任务描述
        task_description = content
        
        # 确定优先级
        priority = "medium"
        if memo.get("importance", 3) >= 5:
            priority = "high"
        elif memo.get("importance", 3) <= 2:
            priority = "low"
        
        # 提取截止日期
        due_date = None
        if dates:
            due_date = dates[0]  # 使用第一个日期
        
        # 估算任务时长（基于内容长度和复杂度）⭐增强版
        estimated_duration = self._estimate_task_duration(content, priority)
        
        # 提取任务依赖关系
        dependencies = self._extract_dependencies(content)
        
        # 提取任务步骤（智能分解）
        steps = self._extract_task_steps(content, task_title)
        
        # 计算提取置信度
        confidence = self._calculate_extraction_confidence(memo, task_info)
        
        return {
            "is_task": is_task,
            "title": task_title,
            "description": task_description,
            "priority": priority,
            "due_date": due_date,
            "estimated_duration": estimated_duration,
            "dependencies": dependencies,
            "steps": steps,
            "tags": tags + (["任务"] if is_task else []),
            "confidence": confidence
        }
    
    def _estimate_task_duration(self, content: str, priority: str) -> Optional[int]:
        """估算任务时长（分钟）"""
        # 基于内容长度和关键词估算
        base_duration = len(content) // 10  # 每10个字符约1分钟
        
        # 根据优先级调整
        priority_multiplier = {
            "high": 1.5,
            "medium": 1.0,
            "low": 0.7
        }
        
        duration = int(base_duration * priority_multiplier.get(priority, 1.0))
        
        # 限制在合理范围内（5分钟到8小时）
        return max(5, min(duration, 480))
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """提取任务依赖关系"""
        dependencies = []
        
        # 识别依赖关键词
        dependency_keywords = [
            "在...之后", "等...完成", "需要先", "依赖", "基于", "前提是"
        ]
        
        for keyword in dependency_keywords:
            if keyword in content:
                # 简单提取：找到依赖的任务描述
                # TODO: 使用NLP更精确提取
                dependencies.append(f"依赖任务（基于关键词：{keyword}）")
        
        return dependencies[:3]  # 最多3个依赖
    
    def _extract_task_steps(self, content: str, title: str) -> List[Dict[str, Any]]:
        """提取任务步骤（智能分解）"""
        steps = []
        
        # 识别步骤关键词
        step_keywords = ["首先", "然后", "接着", "最后", "第一步", "第二步", "第三步"]
        
        # 尝试按步骤关键词分解
        for i, keyword in enumerate(step_keywords):
            if keyword in content:
                # 提取该步骤的内容
                parts = content.split(keyword)
                if len(parts) > 1:
                    step_content = parts[1].split("。")[0] if "。" in parts[1] else parts[1][:100]
                    steps.append({
                        "step_number": i + 1,
                        "description": step_content.strip(),
                        "status": "pending"
                    })
        
        # 如果没有找到步骤关键词，尝试按句号分解（最多5步）
        if not steps:
            sentences = [s.strip() for s in content.split("。") if s.strip()]
            for i, sentence in enumerate(sentences[:5]):
                if len(sentence) > 5:  # 过滤太短的句子
                    steps.append({
                        "step_number": i + 1,
                        "description": sentence,
                        "status": "pending"
                    })
        
        # 如果还是没有步骤，创建一个默认步骤
        if not steps:
            steps.append({
                "step_number": 1,
                "description": title or content[:50],
                "status": "pending"
            })
        
        return steps
    
    def _calculate_extraction_confidence(self, memo: Dict[str, Any], task_info: Dict[str, Any]) -> float:
        """计算任务提取置信度"""
        confidence = 0.5  # 基础置信度
        
        # 如果明确标记为任务类型，提高置信度
        if memo.get("type") == "task":
            confidence += 0.2
        
        # 如果有日期，提高置信度
        if task_info.get("due_date"):
            confidence += 0.1
        
        # 如果重要性高，提高置信度
        if memo.get("importance", 3) >= 4:
            confidence += 0.1
        
        # 如果提取到了步骤，提高置信度
        if task_info.get("steps"):
            confidence += 0.1
        
        return min(confidence, 1.0)  # 限制在0-1之间
    
    async def create_plan(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建工作计划⭐增强版（世界级功能）
        
        Args:
            tasks: 任务列表
            
        Returns:
            工作计划
        """
        # 智能任务排序（按优先级、依赖关系、截止日期）
        sorted_tasks = self._sort_tasks_intelligently(tasks)
        
        # 计算计划总时长
        total_duration = sum(t.get("estimated_duration", 0) for t in sorted_tasks)
        
        # 识别关键路径（最长依赖链）
        critical_path = self._identify_critical_path(sorted_tasks)
        
        # 生成计划建议
        suggestions = self._generate_plan_suggestions(sorted_tasks, total_duration)
        
        plan = {
            "id": len(self.plans) + 1,
            "tasks": sorted_tasks,
            "total_tasks": len(sorted_tasks),
            "pending_tasks": len([t for t in sorted_tasks if t.get("status") == "pending"]),
            "completed_tasks": len([t for t in sorted_tasks if t.get("status") == "completed"]),
            "total_duration_minutes": total_duration,
            "estimated_completion_time": self._estimate_completion_time(sorted_tasks),
            "critical_path": critical_path,
            "suggestions": suggestions,
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "needs_confirmation": True  # 需要用户确认
        }
        
        self.plans.append(plan)
        return plan
    
    def _sort_tasks_intelligently(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """智能任务排序"""
        # 1. 按优先级排序（high > medium > low）
        priority_order = {"high": 3, "medium": 2, "low": 1}
        
        # 2. 按截止日期排序（有日期的优先）
        # 3. 按依赖关系排序（无依赖的优先）
        
        def sort_key(task):
            priority_score = priority_order.get(task.get("priority", "medium"), 2)
            has_due_date = 1 if task.get("due_date") else 0
            has_dependencies = 0 if not task.get("dependencies") else 1
            importance = task.get("importance", 3)
            
            return (
                -priority_score,  # 优先级高的在前
                -has_due_date,  # 有截止日期的在前
                has_dependencies,  # 无依赖的在前
                -importance  # 重要性高的在前
            )
        
        return sorted(tasks, key=sort_key)
    
    def _identify_critical_path(self, tasks: List[Dict[str, Any]]) -> List[int]:
        """识别关键路径（最长依赖链）"""
        # 简化实现：找到依赖链最长的任务序列
        critical_path = []
        max_depth = 0
        
        def get_dependency_depth(task_id: int, visited: set) -> int:
            if task_id in visited:
                return 0
            
            task = next((t for t in tasks if t["id"] == task_id), None)
            if not task:
                return 0
            
            dependencies = task.get("dependencies", [])
            if not dependencies:
                return 1
            
            visited.add(task_id)
            max_dep_depth = max(
                [get_dependency_depth(dep_id, visited.copy()) for dep_id in dependencies],
                default=0
            )
            return max_dep_depth + 1
        
        for task in tasks:
            depth = get_dependency_depth(task["id"], set())
            if depth > max_depth:
                max_depth = depth
                critical_path = [task["id"]]
        
        return critical_path
    
    def _generate_plan_suggestions(self, tasks: List[Dict[str, Any]], total_duration: int) -> List[str]:
        """生成计划建议"""
        suggestions = []
        
        # 如果总时长超过8小时，建议分批执行
        if total_duration > 480:
            suggestions.append(f"计划总时长 {total_duration//60} 小时，建议分批执行")
        
        # 如果有高优先级任务，建议优先处理
        high_priority_count = len([t for t in tasks if t.get("priority") == "high"])
        if high_priority_count > 0:
            suggestions.append(f"有 {high_priority_count} 个高优先级任务，建议优先处理")
        
        # 如果有依赖关系，建议按顺序执行
        tasks_with_deps = [t for t in tasks if t.get("dependencies")]
        if tasks_with_deps:
            suggestions.append(f"有 {len(tasks_with_deps)} 个任务存在依赖关系，请按顺序执行")
        
        # 如果有截止日期，提醒时间管理
        tasks_with_due_date = [t for t in tasks if t.get("due_date")]
        if tasks_with_due_date:
            suggestions.append(f"有 {len(tasks_with_due_date)} 个任务有截止日期，请注意时间管理")
        
        return suggestions
    
    def _estimate_completion_time(self, tasks: List[Dict[str, Any]]) -> str:
        """估算完成时间"""
        total_minutes = sum(t.get("estimated_duration", 0) for t in tasks)
        
        if total_minutes < 60:
            return f"{total_minutes} 分钟"
        elif total_minutes < 1440:  # 24小时
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours} 小时 {minutes} 分钟"
        else:
            days = total_minutes // 1440
            hours = (total_minutes % 1440) // 60
            return f"{days} 天 {hours} 小时"
    
    async def confirm_task(self, task_id: int, confirmed: bool, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        用户确认任务
        
        Args:
            task_id: 任务ID
            confirmed: 是否确认
            reason: 拒绝原因（如果未确认）
            
        Returns:
            更新后的任务
        """
        for task in self.tasks:
            if task["id"] == task_id:
                if confirmed:
                    task["status"] = "confirmed"
                    task["confirmed_at"] = datetime.now().isoformat()
                else:
                    task["status"] = "rejected"
                    task["rejection_reason"] = reason
                    task["rejected_at"] = datetime.now().isoformat()
                
                task["needs_confirmation"] = False
                return task
        
        return None
    
    async def execute_task(self, task_id: int) -> Dict[str, Any]:
        """
        执行任务⭐完善版（100%）
        
        Args:
            task_id: 任务ID
            
        Returns:
            执行结果
        """
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return {"success": False, "error": "任务不存在"}
        
        if task.get("status") != "confirmed":
            return {"success": False, "error": "任务未确认"}
        
        # 检查依赖任务是否完成
        dependencies = task.get("dependencies", [])
        if dependencies:
            for dep_task_id in dependencies:
                dep_task = next((t for t in self.tasks if t["id"] == dep_task_id), None)
                if dep_task and dep_task.get("status") != "completed":
                    return {
                        "success": False,
                        "error": f"依赖任务 {dep_task_id} 尚未完成",
                        "blocked_by": dep_task_id
                    }
        
        # 执行任务
        task["status"] = "in_progress"
        task["started_at"] = datetime.now().isoformat()
        task["progress"] = 0
        task.setdefault("execution_log", [])
        
        # 执行任务步骤
        steps = task.get("steps", [])
        if steps:
            total_steps = len(steps)
            completed_steps = 0
            
            for step in sorted(steps, key=lambda x: x.get("order", 0)):
                step_name = step.get("name", "未知步骤")
                step_duration = step.get("estimated_duration", 0)
                # 重试控制
                max_retries = int(step.get("retries", task.get("retries", 0)) or 0)
                backoff = float(step.get("retry_backoff_sec", task.get("retry_backoff_sec", 0.0)) or 0.0)
                attempt = 0
                while True:
                    try:
                        step_result = await self._execute_task_step(task, step)
                        # 记录日志
                        task["execution_log"].append({
                            "step": step_name,
                            "attempt": attempt + 1,
                            "success": step_result.get("success", False),
                            "result": step_result.get("result"),
                            "ts": datetime.now().isoformat()
                        })
                        if step_result.get("success"):
                            completed_steps += 1
                            task["progress"] = int((completed_steps / total_steps) * 100)
                            break
                        else:
                            if attempt < max_retries:
                                attempt += 1
                                if backoff > 0:
                                    import asyncio as _asyncio
                                    await _asyncio.sleep(backoff * attempt)
                                continue
                            task["status"] = "failed"
                            task["failed_at"] = datetime.now().isoformat()
                            task["failure_reason"] = step_result.get("error", "步骤执行失败")
                            return {
                                "success": False,
                                "error": f"步骤 '{step_name}' 执行失败",
                                "task": task
                            }
                    except Exception as e:
                        task["execution_log"].append({
                            "step": step_name,
                            "attempt": attempt + 1,
                            "success": False,
                            "error": str(e),
                            "ts": datetime.now().isoformat()
                        })
                        if attempt < max_retries:
                            attempt += 1
                            if backoff > 0:
                                import asyncio as _asyncio
                                await _asyncio.sleep(backoff * attempt)
                            continue
                        task["status"] = "failed"
                        task["failed_at"] = datetime.now().isoformat()
                        task["failure_reason"] = str(e)
                        return {
                            "success": False,
                            "error": f"步骤 '{step_name}' 执行异常: {str(e)}",
                            "task": task
                        }
        else:
            # 没有步骤，直接标记为完成
            task["progress"] = 100
        
        # 任务完成
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        task["progress"] = 100
        
        return {
            "success": True,
            "task": task,
            "execution_time": (
                datetime.fromisoformat(task["completed_at"]) - 
                datetime.fromisoformat(task["started_at"])
            ).total_seconds()
        }
    
    async def _execute_task_step(self, task: Dict, step: Dict) -> Dict[str, Any]:
        """
        执行任务步骤
        
        Args:
            task: 任务信息
            step: 步骤信息
            
        Returns:
            步骤执行结果
        """
        step_name = step.get("name", "")
        task_type = task.get("template_type", "general")
        
        # 根据任务类型和步骤名称执行相应的操作
        # 这里可以集成到Super Agent的模块执行器
        
        # 模拟步骤执行（实际应该调用相应的模块）
        import asyncio
        await asyncio.sleep(0.1)  # 模拟执行时间
        
        return {
            "success": True,
            "step_name": step_name,
            "result": f"步骤 '{step_name}' 执行完成"
        }
    
    def get_tasks(
        self,
        status: Optional[str] = None,
        needs_confirmation: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """获取任务列表"""
        filtered = self.tasks
        
        if status:
            filtered = [t for t in filtered if t.get("status") == status]
        
        if needs_confirmation is not None:
            filtered = [t for t in filtered if t.get("needs_confirmation") == needs_confirmation]
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息⭐增强版"""
        completed_tasks = [t for t in self.tasks if t.get("status") == "completed"]
        in_progress_tasks = [t for t in self.tasks if t.get("status") == "in_progress"]
        
        # 计算平均完成时间
        avg_completion_time = 0
        if completed_tasks:
            completion_times = []
            for task in completed_tasks:
                if task.get("started_at") and task.get("completed_at"):
                    try:
                        start = datetime.fromisoformat(task["started_at"])
                        end = datetime.fromisoformat(task["completed_at"])
                        completion_times.append((end - start).total_seconds())
                    except:
                        pass
            if completion_times:
                avg_completion_time = sum(completion_times) / len(completion_times)
        
        # 计算平均进度
        avg_progress = 0
        if in_progress_tasks:
            progresses = [t.get("progress", 0) for t in in_progress_tasks if t.get("progress") is not None]
            if progresses:
                avg_progress = sum(progresses) / len(progresses)
        
        return {
            "total_tasks": len(self.tasks),
            "pending": len([t for t in self.tasks if t.get("status") == "pending"]),
            "confirmed": len([t for t in self.tasks if t.get("status") == "confirmed"]),
            "in_progress": len(in_progress_tasks),
            "completed": len(completed_tasks),
            "rejected": len([t for t in self.tasks if t.get("status") == "rejected"]),
            "failed": len([t for t in self.tasks if t.get("status") == "failed"]),
            "needs_confirmation": len([t for t in self.tasks if t.get("needs_confirmation")]),
            "avg_completion_time": avg_completion_time,
            "avg_progress": avg_progress,
            "completion_rate": len(completed_tasks) / len(self.tasks) * 100 if self.tasks else 0
        }

