"""
Agentic RAG
自主RAG系统

实现Agentic RAG（差距7）：
1. 自主规划和迭代优化
2. 多轮检索规划
3. 自我改进循环
4. 任务分解和子目标规划
5. 执行评估机制
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class SubGoalStatus(Enum):
    """子目标状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubGoal:
    """子目标"""
    id: str
    description: str
    query: str
    status: SubGoalStatus = SubGoalStatus.NOT_STARTED
    result: Optional[Dict[str, Any]] = None
    confidence: float = 0.0


@dataclass
class TaskPlan:
    """任务计划"""
    task_id: str
    goal: str
    sub_goals: List[SubGoal] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    iterations: int = 0
    max_iterations: int = 5


class AgenticRAG:
    """
    Agentic RAG系统
    
    实现自主规划、执行和优化
    """

    def __init__(
        self,
        rag_retriever: Any = None,
        enable_planning: bool = True,
        enable_self_improvement: bool = True,
        max_iterations: int = 5,
    ):
        """
        初始化Agentic RAG
        
        Args:
            rag_retriever: RAG检索器实例
            enable_planning: 是否启用任务规划
            enable_self_improvement: 是否启用自我改进
            max_iterations: 最大迭代次数
        """
        self.rag_retriever = rag_retriever
        self.enable_planning = enable_planning
        self.enable_self_improvement = enable_self_improvement
        self.max_iterations = max_iterations
        
        # 任务历史
        self.task_history: Dict[str, TaskPlan] = {}

    async def execute_task(
        self,
        goal: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行任务（自主规划、执行、评估）
        
        Args:
            goal: 任务目标
            context: 上下文信息（可选）
            
        Returns:
            任务执行结果
        """
        task_id = self._generate_task_id(goal)
        
        # 创建任务计划
        plan = TaskPlan(
            task_id=task_id,
            goal=goal,
            max_iterations=self.max_iterations,
        )
        self.task_history[task_id] = plan
        
        # 第一步：任务规划
        if self.enable_planning:
            plan.sub_goals = await self._plan_task(goal, context)
            plan.status = TaskStatus.PLANNING
        
        # 第二步：执行子目标
        plan.status = TaskStatus.EXECUTING
        for sub_goal in plan.sub_goals:
            sub_goal.status = SubGoalStatus.IN_PROGRESS
            
            # 执行子目标检索
            sub_result = await self._execute_sub_goal(sub_goal, context)
            sub_goal.result = sub_result
            sub_goal.status = SubGoalStatus.COMPLETED if sub_result else SubGoalStatus.FAILED
        
        # 第三步：评估结果
        plan.status = TaskStatus.EVALUATING
        evaluation = await self._evaluate_results(plan)
        
        # 第四步：自我改进（如果需要）
        if self.enable_self_improvement and evaluation.get("needs_improvement"):
            plan.iterations += 1
            if plan.iterations < plan.max_iterations:
                # 改进查询并重新执行
                improved_plan = await self._improve_plan(plan, evaluation)
                # 递归执行改进后的计划（简化：只执行一次改进）
                return await self._execute_improved_plan(improved_plan, context)
        
        # 第五步：综合结果
        plan.status = TaskStatus.COMPLETED
        final_result = await self._synthesize_results(plan)
        
        return {
            "task_id": task_id,
            "goal": goal,
            "status": plan.status.value,
            "iterations": plan.iterations,
            "sub_goals": [
                {
                    "id": sg.id,
                    "description": sg.description,
                    "status": sg.status.value,
                    "confidence": sg.confidence,
                }
                for sg in plan.sub_goals
            ],
            "result": final_result,
            "confidence": evaluation.get("overall_confidence", 0.0),
        }

    async def _plan_task(
        self,
        goal: str,
        context: Optional[str],
    ) -> List[SubGoal]:
        """
        规划任务（分解为子目标）
        
        将复杂任务分解为多个子任务
        """
        sub_goals = []
        
        # 简单策略：根据查询类型和关键词分解
        # 实际应该使用更智能的任务分解
        
        # 1. 识别关键实体和概念
        keywords = self._extract_keywords(goal)
        
        # 2. 为每个关键概念创建子目标
        for i, keyword in enumerate(keywords[:5]):  # 最多5个子目标
            sub_goal = SubGoal(
                id=f"subgoal-{i}",
                description=f"检索关于'{keyword}'的信息",
                query=keyword,
            )
            sub_goals.append(sub_goal)
        
        # 3. 添加整体查询子目标
        if len(keywords) > 1:
            sub_goal = SubGoal(
                id="subgoal-overall",
                description=f"检索关于'{goal}'的整体信息",
                query=goal,
            )
            sub_goals.append(sub_goal)
        
        # 如果没有提取到关键词，使用原始查询作为单一子目标
        if not sub_goals:
            sub_goal = SubGoal(
                id="subgoal-0",
                description=goal,
                query=goal,
            )
            sub_goals.append(sub_goal)
        
        logger.debug(f"任务规划完成：{len(sub_goals)} 个子目标")
        return sub_goals

    async def _execute_sub_goal(
        self,
        sub_goal: SubGoal,
        context: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        执行子目标
        
        执行检索并返回结果
        """
        if not self.rag_retriever:
            return None
        
        try:
            # 调用检索器
            if hasattr(self.rag_retriever, "retrieve_for_response"):
                result = await self.rag_retriever.retrieve_for_response(
                    user_query=sub_goal.query,
                    top_k=5,
                )
                items = result.get("knowledge_items", [])
            elif hasattr(self.rag_retriever, "search"):
                result = await self.rag_retriever.search(
                    query=sub_goal.query,
                    top_k=5,
                )
                items = result.get("items", [])
            else:
                items = []
            
            # 计算置信度（基于结果数量和分数）
            if items:
                avg_score = sum(item.get("score", 0.0) for item in items) / len(items)
                sub_goal.confidence = min(1.0, avg_score * 1.2)
            else:
                sub_goal.confidence = 0.0
            
            return {
                "query": sub_goal.query,
                "items": items,
                "count": len(items),
                "confidence": sub_goal.confidence,
            }
        except Exception as e:
            logger.error(f"子目标执行失败: {e}")
            return None

    async def _evaluate_results(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        评估任务执行结果
        
        判断是否需要改进
        """
        # 计算总体置信度
        completed_goals = [sg for sg in plan.sub_goals if sg.status == SubGoalStatus.COMPLETED]
        total_confidence = sum(sg.confidence for sg in completed_goals)
        avg_confidence = total_confidence / len(completed_goals) if completed_goals else 0.0
        
        # 计算完成率
        completion_rate = len(completed_goals) / len(plan.sub_goals) if plan.sub_goals else 0.0
        
        # 判断是否需要改进
        needs_improvement = (
            avg_confidence < 0.6 or  # 置信度太低
            completion_rate < 0.7 or  # 完成率太低
            len(completed_goals) == 0  # 没有完成的子目标
        )
        
        return {
            "overall_confidence": avg_confidence,
            "completion_rate": completion_rate,
            "needs_improvement": needs_improvement,
            "completed_goals": len(completed_goals),
            "total_goals": len(plan.sub_goals),
        }

    async def _improve_plan(
        self,
        plan: TaskPlan,
        evaluation: Dict[str, Any],
    ) -> TaskPlan:
        """
        改进任务计划
        
        根据评估结果优化查询和策略
        """
        # 改进失败的子目标
        for sub_goal in plan.sub_goals:
            if sub_goal.status == SubGoalStatus.FAILED:
                # 扩展查询
                improved_query = self._improve_query(sub_goal.query)
                sub_goal.query = improved_query
                sub_goal.status = SubGoalStatus.NOT_STARTED
        
        # 添加新的子目标（如果需要）
        if evaluation.get("completion_rate", 0) < 0.5:
            # 添加更细粒度的子目标
            new_sub_goal = SubGoal(
                id=f"subgoal-improved-{len(plan.sub_goals)}",
                description=f"改进检索：{plan.goal}",
                query=self._improve_query(plan.goal),
            )
            plan.sub_goals.append(new_sub_goal)
        
        logger.debug(f"任务计划已改进：{len(plan.sub_goals)} 个子目标")
        return plan

    async def _execute_improved_plan(
        self,
        plan: TaskPlan,
        context: Optional[str],
    ) -> Dict[str, Any]:
        """
        执行改进后的计划
        """
        # 重新执行未完成的子目标
        for sub_goal in plan.sub_goals:
            if sub_goal.status in [SubGoalStatus.NOT_STARTED, SubGoalStatus.FAILED]:
                sub_goal.status = SubGoalStatus.IN_PROGRESS
                sub_result = await self._execute_sub_goal(sub_goal, context)
                sub_goal.result = sub_result
                sub_goal.status = SubGoalStatus.COMPLETED if sub_result else SubGoalStatus.FAILED
        
        # 重新评估
        evaluation = await self._evaluate_results(plan)
        
        # 综合结果
        final_result = await self._synthesize_results(plan)
        
        return {
            "task_id": plan.task_id,
            "goal": plan.goal,
            "status": plan.status.value,
            "iterations": plan.iterations,
            "result": final_result,
            "confidence": evaluation.get("overall_confidence", 0.0),
        }

    async def _synthesize_results(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        综合所有子目标的结果
        
        合并和去重检索结果
        """
        all_items = []
        seen_ids = set()
        
        for sub_goal in plan.sub_goals:
            if sub_goal.result and sub_goal.status == SubGoalStatus.COMPLETED:
                items = sub_goal.result.get("items", [])
                for item in items:
                    item_id = item.get("id") or item.get("document_id", "")
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_items.append(item)
        
        # 按分数排序
        all_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        
        return {
            "items": all_items,
            "total_count": len(all_items),
            "sub_goals_count": len([sg for sg in plan.sub_goals if sg.status == SubGoalStatus.COMPLETED]),
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词（简化实现）
        """
        # 简单的关键词提取：去除停用词
        stop_words = {"的", "和", "与", "或", "是", "在", "有", "为", "一个", "这个", "that", "the", "a", "an", "is", "are"}
        
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # 最多10个关键词

    def _improve_query(self, query: str) -> str:
        """
        改进查询
        
        添加相关术语和同义词
        """
        # 简单策略：添加相关术语
        # 实际应该使用同义词库或查询扩展
        
        improved = query
        
        # 添加常见的查询增强词
        enhancement_patterns = {
            "什么是": "定义 解释",
            "如何": "方法 步骤",
            "为什么": "原因 原理",
        }
        
        for pattern, enhancement in enhancement_patterns.items():
            if pattern in query:
                improved = f"{query} {enhancement}"
                break
        
        return improved

    def _generate_task_id(self, goal: str) -> str:
        """
        生成任务ID
        """
        import hashlib
        import time
        
        task_str = f"{goal}-{time.time()}"
        return hashlib.md5(task_str.encode()).hexdigest()[:12]


# 全局Agentic RAG实例
_global_agentic_rag: Optional[AgenticRAG] = None


def get_agentic_rag(rag_retriever: Any = None) -> AgenticRAG:
    """
    获取Agentic RAG实例（单例模式）
    
    Args:
        rag_retriever: RAG检索器实例
        
    Returns:
        AgenticRAG实例
    """
    global _global_agentic_rag
    
    if _global_agentic_rag is None:
        _global_agentic_rag = AgenticRAG(rag_retriever=rag_retriever)
    
    return _global_agentic_rag

