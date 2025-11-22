"""
超级Agent核心引擎
实现AI工作流9步骤，包括2次RAG检索
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import time

from .workflow_monitor import WorkflowMonitor
from .learning_events import LearningEventBus
from .task_orchestrator import TaskOrchestrator
from .closure_recorder import ClosureRecorder
from .context_compressor import ContextCompressor
from .unified_event_bus import UnifiedEventBus, get_unified_event_bus
from .closed_loop_engine import ClosedLoopEngine
from .execution_checker import ExecutionChecker
from .feedback_handler import FeedbackHandler
from .evidence_recorder import EvidenceRecorder
from .dual_rag_engine import DualRAGEngine
from .enhanced_expert_router import EnhancedExpertRouter
from .enhanced_workflow_monitor import EnhancedWorkflowMonitor, WorkflowStepType

class SuperAgent:
    """
    超级Agent核心引擎
    
    实现AI工作流9步骤：
    1. 用户输入
    2. 识别重要信息→备忘录
    3. 第1次RAG检索（理解需求）
    4. 路由到对应专家
    5. 专家分析并调用模块功能
    6. 功能模块执行任务
    7. 第2次RAG检索（整合经验知识）⭐灵魂
    8. 专家综合生成回复
    9. 返回给用户
    """
    
    def __init__(self):
        self.memo_system = None  # 将在初始化时注入
        self.rag_service = None  # RAG服务
        self.expert_router = None  # 专家路由
        self.module_executor = None  # 模块执行器
        self.learning_monitor = None  # 学习监控
        self.resource_monitor = None  # 资源监控
        self.task_planning = None  # 任务规划系统
        self.workflow_monitor = None  # 工作流监控器
        self.event_bus = LearningEventBus()
        self.closure_recorder = ClosureRecorder()
        self.closure_recorder.attach_to_event_bus(self.event_bus)
        self.task_orchestrator: Optional[TaskOrchestrator] = None
        
        # P0-001: 闭环系统组件
        self.unified_event_bus = get_unified_event_bus()
        self.execution_checker = ExecutionChecker(self.unified_event_bus)
        self.feedback_handler = FeedbackHandler(self.unified_event_bus)
        self.evidence_recorder = EvidenceRecorder(self.unified_event_bus)
        self.closed_loop_engine = ClosedLoopEngine(
            event_bus=self.unified_event_bus,
            execution_checker=self.execution_checker,
            feedback_handler=self.feedback_handler,
            evidence_recorder=self.evidence_recorder,
            closure_recorder=self.closure_recorder,
        )
        
        # P0-002: 双RAG检索和增强专家路由
        self.dual_rag_engine = DualRAGEngine(rag_service=None, cache_enabled=True)
        self.enhanced_expert_router = EnhancedExpertRouter()
        self.enhanced_workflow_monitor = EnhancedWorkflowMonitor()
        
        # 自动初始化依赖
        self._initialize_dependencies()
        
        # 初始化工作流监控器
        self.workflow_monitor = WorkflowMonitor()
        
        # 初始化缓存
        self.response_cache = {}
        self.rag_cache = {}
        self.expert_cache = {}
        self.rag2_cache = {}
        self.max_cache_size = 1000
        self.cache_ttl = 300  # 5分钟
        self.timeout_config = {
            "memo_extraction": 0.3,  # 优化：减少到0.3秒
            "rag_retrieval": 2.0,  # 优化：减少到2秒
            "expert_routing": 0.3,  # 优化：减少到0.3秒
            "module_execution": 2.5,  # 优化：减少到2.5秒
            "rag2_retrieval": 1.0  # 优化：减少到1秒
        }
        self.context_compressor = ContextCompressor()
    
    def _initialize_dependencies(self):
        """初始化依赖组件"""
        from .rag_service_adapter import RAGServiceAdapter
        from .expert_router import ExpertRouter
        from .module_executor import ModuleExecutor
        
        # 初始化RAG服务适配器
        self.rag_service = RAGServiceAdapter()
        
        # 初始化专家路由
        self.expert_router = ExpertRouter()
        
        # 初始化模块执行器
        self.module_executor = ModuleExecutor()
        
        # 设置模块执行器到学习监控（用于自动优化）
        if self.learning_monitor:
            self.learning_monitor.coding_assistant = f"{self.module_executor.module_apis.get('coding', 'http://localhost:8000')}/api/coding-assistant"
        
    async def process_user_input(
        self,
        user_input: str,
        input_type: str = "text",  # text, voice, file, search
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理用户输入，执行完整的AI工作流⭐优化版（2秒响应目标）
        
        Args:
            user_input: 用户输入内容
            input_type: 输入类型
            context: 上下文信息
            
        Returns:
            处理结果
        """
        start_time = datetime.now()
        
        # 规范化上下文（含外部搜索结果）
        context = context or {}
        external_search_context = self._prepare_external_search_context(context.get("external_search"))
        if external_search_context:
            context["external_search"] = external_search_context
        elif "external_search" in context:
            context.pop("external_search", None)
        slo_context = context.get("slo", {})
        
        # 开始工作流监控
        workflow_id = None
        if self.workflow_monitor:
            workflow_id = await self.workflow_monitor.start_workflow(user_input, context)
            await self.workflow_monitor.record_step("user_input", "user_input", success=True, data={"input": user_input})
        
        # P0-002: 增强工作流监控
        enhanced_workflow_id = None
        if self.enhanced_workflow_monitor:
            enhanced_workflow_id = await self.enhanced_workflow_monitor.start_workflow(user_input, context)
        
        # 检查缓存（简单查询可以缓存）
        cache_key = f"{user_input}:{input_type}"
        if cache_key in self.response_cache:
            cached_result = self.response_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached_result["cached_at"])).total_seconds() < self.cache_ttl:
                return {
                    **cached_result["result"],
                    "from_cache": True,
                    "response_time": (datetime.now() - start_time).total_seconds()
                }
        
        try:
            # 步骤1: 用户输入
            input_data = {
                "content": user_input,
                "type": input_type,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # 步骤2: 识别重要信息→备忘录⭐优化版（异步+超时）
            memo_task = asyncio.create_task(
                asyncio.wait_for(
                    self._extract_important_info(input_data),
                    timeout=self.timeout_config["memo_extraction"]
                )
            ) if self.memo_system else None
            
            # 步骤3: 第1次RAG检索（理解需求 + 检索相关知识）⭐并行
            if self.workflow_monitor:
                await self.workflow_monitor.record_step("rag_retrieval_1", "rag_retrieval")
            
            # P0-002: 使用双RAG引擎进行第1次检索
            if self.dual_rag_engine:
                rag1_result = await self.dual_rag_engine.first_rag_retrieval(
                    user_input=user_input,
                    context=context,
                    top_k=3,
                    timeout=2.0,
                )
                rag_result_1 = rag1_result.to_dict() if hasattr(rag1_result, 'to_dict') else {
                    "knowledge": rag1_result.knowledge_items if hasattr(rag1_result, 'knowledge_items') else [],
                    "understanding": rag1_result.understanding if hasattr(rag1_result, 'understanding') else {},
                    "query": user_input,
                }
                
                # P0-002: 记录到增强工作流监控
                if self.enhanced_workflow_monitor:
                    await self.enhanced_workflow_monitor.record_step(
                        step_name="rag_retrieval_1",
                        step_type=WorkflowStepType.RAG_RETRIEVAL_1,
                        data=rag_result_1,
                    )
            else:
                rag_result_1 = await self._first_rag_retrieval(user_input, context)
            
            if self.workflow_monitor:
                await self.workflow_monitor.complete_step("rag_retrieval_1", success=True, result=rag_result_1)
            
            if self.enhanced_workflow_monitor:
                await self.enhanced_workflow_monitor.complete_step("rag_retrieval_1", success=True, result=rag_result_1)
            
            if external_search_context:
                self._augment_rag_with_search(rag_result_1, external_search_context)
            
            # 步骤4: 路由到对应专家
            if self.workflow_monitor:
                await self.workflow_monitor.record_step("expert_routing", "expert_routing")
            
            # P0-002: 使用增强专家路由
            if self.enhanced_expert_router:
                expert_result = await self.enhanced_expert_router.route(
                    user_input=user_input,
                    rag_result=rag_result_1,
                    timeout=0.5,
                )
                expert = expert_result.to_dict() if hasattr(expert_result, 'to_dict') else {
                    "expert": expert_result.expert if hasattr(expert_result, 'expert') else "default",
                    "domain": expert_result.domain if hasattr(expert_result, 'domain') else "general",
                    "module": expert_result.module if hasattr(expert_result, 'module') else "rag",
                    "confidence": expert_result.confidence if hasattr(expert_result, 'confidence') else 0.7,
                    "intent": expert_result.intent if hasattr(expert_result, 'intent') else {},
                }
                
                # P0-002: 记录到增强工作流监控
                if self.enhanced_workflow_monitor:
                    await self.enhanced_workflow_monitor.record_step(
                        step_name="expert_routing",
                        step_type=WorkflowStepType.EXPERT_ROUTING,
                        data=expert,
                    )
            else:
                expert = await self._route_to_expert(user_input, rag_result_1)
            
            if self.workflow_monitor:
                await self.workflow_monitor.complete_step("expert_routing", success=True, result=expert)
            
            if self.enhanced_workflow_monitor:
                await self.enhanced_workflow_monitor.complete_step("expert_routing", success=True, result=expert)
            
            # 步骤5: 专家分析并调用模块功能执行
            if self.workflow_monitor:
                await self.workflow_monitor.record_step("module_execution", "module_execution")
            module_result = await self._execute_module_function(expert, user_input, rag_result_1, slo_context)
            if self.workflow_monitor:
                await self.workflow_monitor.complete_step("module_execution", success=True, result=module_result)
            
            # 步骤6: 功能模块执行任务，返回结果
            execution_result = await self._get_execution_result(module_result)
            
            # 步骤7: 专家接收结果，第2次RAG检索（整合经验知识）⭐优化版（缓存+超时）
            if self.workflow_monitor:
                await self.workflow_monitor.record_step("rag_retrieval_2", "rag_retrieval")
            
            # P0-002: 使用双RAG引擎进行第2次检索
            if self.dual_rag_engine:
                rag1_result_obj = None
                if hasattr(rag_result_1, 'knowledge_items'):
                    rag1_result_obj = rag_result_1
                elif isinstance(rag_result_1, dict):
                    # 转换为RAGRetrievalResult对象（简化处理）
                    from .dual_rag_engine import RAGRetrievalResult
                    rag1_result_obj = RAGRetrievalResult(
                        retrieval_id=f"rag1_{uuid4()}",
                        query=user_input,
                        knowledge_items=rag_result_1.get("knowledge", []),
                        understanding=rag_result_1.get("understanding", {}),
                        retrieval_time=0.0,
                    )
                
                rag2_result = await self.dual_rag_engine.second_rag_retrieval(
                    user_input=user_input,
                    execution_result=execution_result,
                    rag1_result=rag1_result_obj,
                    top_k=3,
                    timeout=1.0,
                )
                rag_result_2 = rag2_result.to_dict() if hasattr(rag2_result, 'to_dict') else {
                    "experience": rag2_result.knowledge_items if hasattr(rag2_result, 'knowledge_items') else [],
                    "understanding": rag2_result.understanding if hasattr(rag2_result, 'understanding') else {},
                }
                
                # P0-002: 记录到增强工作流监控
                if self.enhanced_workflow_monitor:
                    await self.enhanced_workflow_monitor.record_step(
                        step_name="rag_retrieval_2",
                        step_type=WorkflowStepType.RAG_RETRIEVAL_2,
                        data=rag_result_2,
                    )
            else:
                rag_result_2 = await self._second_rag_retrieval(
                    user_input, execution_result, rag_result_1
                )
            
            if self.workflow_monitor:
                await self.workflow_monitor.complete_step("rag_retrieval_2", success=True, result=rag_result_2)
            
            if self.enhanced_workflow_monitor:
                await self.enhanced_workflow_monitor.complete_step("rag_retrieval_2", success=True, result=rag_result_2)
            
            # 步骤8: 专家综合生成最终回复
            if self.workflow_monitor:
                await self.workflow_monitor.record_step("response_generation", "response_generation")
            
            # P0-002: 记录到增强工作流监控
            if self.enhanced_workflow_monitor:
                await self.enhanced_workflow_monitor.record_step(
                    step_name="response_generation",
                    step_type=WorkflowStepType.RESPONSE_GENERATION,
                )
            
            final_response = await self._generate_final_response(
                expert, execution_result, rag_result_2, external_search_context, slo_context
            )
            
            if self.workflow_monitor:
                await self.workflow_monitor.complete_step("response_generation", success=True, result=final_response)
            
            if self.enhanced_workflow_monitor:
                await self.enhanced_workflow_monitor.complete_step("response_generation", success=True, result=final_response)
            
            # 步骤2完成：处理备忘录（异步执行，不阻塞主流程）⭐增强版
            memo_created = False
            memo_info = None
            if memo_task:
                try:
                    important_info = await memo_task
                    if important_info and self.memo_system:
                        memo = await self.memo_system.add_memo(important_info)
                        memo_created = True
                        memo_info = {
                            "memo_id": memo.get("id") if isinstance(memo, dict) else None,
                            "title": important_info.get("title"),
                            "type": important_info.get("type"),
                            "importance": important_info.get("importance")
                        }
                        
                        # 如果是任务类型，异步提炼到任务规划系统⭐增强版
                        if important_info.get("type") == "task" and self.task_planning:
                            asyncio.create_task(
                                self._extract_and_plan_tasks(important_info)
                            )
                except asyncio.TimeoutError:
                    pass  # 超时不影响主流程
                except Exception as e:
                    logger.warning(f"备忘录创建失败: {e}")  # 记录错误但不影响主流程
            
            # 步骤9: 返回给用户
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 完成工作流监控
            if self.workflow_monitor and workflow_id:
                workflow_result = await self.workflow_monitor.complete_workflow(final_response, response_time)
            
            # P0-002: 完成增强工作流监控
            if self.enhanced_workflow_monitor and enhanced_workflow_id:
                enhanced_workflow_result = await self.enhanced_workflow_monitor.complete_workflow(final_response, response_time)
            
            # 并行：自我学习监控
            if self.learning_monitor:
                asyncio.create_task(self.learning_monitor.monitor_workflow({
                    "input": input_data,
                    "rag_1": rag_result_1,
                    "expert": expert,
                    "execution": execution_result,
                    "rag_2": rag_result_2,
                    "response": final_response,
                    "response_time": response_time
                }))
            
            result = {
                "success": True,
                "response": final_response,
                "response_time": response_time,
                "rag_retrievals": {
                    "first": rag_result_1,
                    "second": rag_result_2
                },
                "execution": execution_result,
                "timestamp": datetime.now().isoformat(),
                "memo_created": memo_created,
                "memo_info": memo_info,  # 添加备忘录信息，供前端显示
                "task_plan_created": False,  # 任务计划创建标志
                "task_plan": None,  # 任务计划数据
                "slo": slo_context
            }
            
            if external_search_context:
                result["search_context"] = external_search_context
            
            # 检查是否创建了任务计划
            if memo_info and memo_info.get("type") == "task" and self.task_planning:
                try:
                    extracted_tasks = await self.task_planning.extract_tasks_from_memos()
                    if extracted_tasks:
                        plan = await self.task_planning.create_plan(extracted_tasks)
                        result["task_plan_created"] = True
                        result["task_plan"] = plan
                except Exception as e:
                    logger.warning(f"任务计划创建失败: {e}")
            
            # 缓存结果（优化策略：缓存更多查询）
            should_cache = (
                input_type == "text" and 
                len(user_input) < 200 and
                response_time < 1.5 and
                not result.get("execution", {}).get("type") in ["complex", "long_running"]
            )
            
            if should_cache:
                self.response_cache[cache_key] = {
                    "result": result,
                    "cached_at": datetime.now().isoformat()
                }
                # 限制缓存大小
                self._cleanup_cache("response_cache", self.max_cache_size)
            
            return result
            
        except Exception as e:
            # 错误处理
            error_info = {
                "error": str(e),
                "input": user_input,
                "timestamp": datetime.now().isoformat()
            }
            
            # 记录错误到RAG
            if self.learning_monitor:
                await self.learning_monitor.record_error(error_info)
            
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _extract_and_plan_tasks(self, memo_info: Dict):
        """
        从备忘录提炼任务并创建计划⭐增强版
        
        Args:
            memo_info: 备忘录信息
        """
        try:
            # 提炼任务
            extracted_tasks = await self.task_planning.extract_tasks_from_memos()
            
            if extracted_tasks:
                # 创建工作计划
                plan = await self.task_planning.create_plan(extracted_tasks)
                
                # 记录到工作流监控
                if self.workflow_monitor:
                    await self.workflow_monitor.record_step(
                        "task_extraction",
                        "task_planning",
                        success=True,
                        data={
                            "tasks_count": len(extracted_tasks),
                            "plan_id": plan.get("id")
                        }
                    )
                
                logger.info(f"已从备忘录提炼 {len(extracted_tasks)} 个任务，创建计划 {plan.get('id')}")
        except Exception as e:
            logger.warning(f"任务提炼失败: {e}")
    
    async def _extract_important_info(self, input_data: Dict) -> Optional[Dict]:
        """提取重要信息到备忘录⭐增强版"""
        import re
        from datetime import datetime, timedelta
        
        content = input_data.get("content", "")
        if not content or len(content.strip()) < 3:
            return None
        
        # 增强的任务关键词识别
        task_keywords = [
            "需要", "应该", "记得", "要", "必须", "完成", "处理", "执行",
            "计划", "安排", "准备", "检查", "审核", "确认", "提醒", "通知",
            "开会", "会议", "讨论", "汇报", "提交", "交付", "截止", "deadline"
        ]
        has_task = any(keyword in content for keyword in task_keywords)
        
        # 增强的日期识别
        date_patterns = [
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",  # 2024-01-15
            r"(\d{1,2}[-/]\d{1,2})",  # 01-15
            r"(\d{1,2}月\d{1,2}日)",  # 1月15日
            r"(明天|后天|大后天|下周|下周一|下周二|下周三|下周四|下周五|下周六|下周日)",
            r"(今天|明天|后天|本周|下周|本月|下月)",
            r"(\d+天后|\d+周后|\d+个月后)"
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            dates.extend(matches)
        
        # 识别时间点
        time_patterns = [
            r"(\d{1,2}:\d{2})",  # 14:30
            r"(\d{1,2}点\d{0,2}分?)",  # 下午2点30分
            r"(上午|下午|晚上|凌晨)(\d{1,2}点)"
        ]
        times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            times.extend(matches)
        
        # 识别联系人
        contact_patterns = [
            r"@(\w+)",
            r"联系(\w+)",
            r"通知(\w+)",
            r"告诉(\w+)",
            r"和(\w+)(一起|讨论|开会)"
        ]
        contacts = []
        for pattern in contact_patterns:
            matches = re.findall(pattern, content)
            if isinstance(matches[0], tuple):
                contacts.extend([m for m in matches[0] if m])
            else:
                contacts.extend(matches)
        
        # 识别重要程度（通过关键词）
        importance_keywords = {
            5: ["紧急", "重要", "必须", "立即", "马上", "尽快"],
            4: ["需要", "应该", "记得", "要"],
            3: ["可以", "建议", "考虑", "如果"],
            2: ["可能", "也许", "或者"]
        }
        importance = 2  # 默认
        for level, keywords in importance_keywords.items():
            if any(keyword in content for keyword in keywords):
                importance = max(importance, level)
                break
        
        # 识别标签
        tags = []
        if has_task:
            tags.append("任务")
        if dates:
            tags.append("有日期")
        if times:
            tags.append("有时间")
        if contacts:
            tags.append("涉及人员")
        
        # 提取标题（前30个字符或第一句话）
        title = content[:30] if len(content) <= 30 else content.split("。")[0][:30]
        if not title:
            title = content[:30]
        
        # 判断是否应该创建备忘录（提高识别准确率）⭐增强版
        should_create = (
            has_task or  # 包含任务关键词
            len(dates) > 0 or  # 包含日期
            len(times) > 0 or  # 包含时间
            len(contacts) > 0 or  # 包含联系人
            importance >= 4 or  # 重要性高
            len(content) > 50 or  # 内容较长（可能是重要信息）
            any(keyword in content for keyword in ["重要", "记住", "备忘", "记录", "保存", "提醒"])  # 明确要求记录
        )
        
        # 如果包含明确的记录要求，提高重要性
        if any(keyword in content for keyword in ["重要", "记住", "备忘", "记录"]):
            importance = max(importance, 4)
        
        if should_create:
            return {
                "title": title,
                "content": content,
                "type": "task" if has_task else "note",
                "importance": importance,
                "tags": tags,
                "dates": dates,
                "times": times,
                "contacts": contacts,
                "metadata": {
                    "source": "chat",
                    "input_type": input_data.get("type", "text"),
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        return None
    
    async def _first_rag_retrieval(
        self,
        user_input: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        第1次RAG检索：理解需求 + 检索相关知识⭐优化版（1.5秒超时）
        
        这是AI工作流的关键步骤之一
        """
        slo_config = context.get("slo", {}) if context else {}
        rag_top_k = slo_config.get("rag_top_k", 3)

        if not self.rag_service:
            return {"knowledge": [], "understanding": {"intent": "query", "confidence": 0.5}}
        
        # 检查缓存
        cache_key = f"rag1:{user_input[:50]}"
        if cache_key in self.rag_cache:
            cached = self.rag_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < 300:
                return cached["result"]
        
        try:
            # 并行执行：检索知识 + 理解意图（带超时控制）
            knowledge_task = self.rag_service.retrieve(
                query=user_input,
                top_k=rag_top_k,
                context=context
            )
            understanding_task = self.rag_service.understand_intent(user_input)
            
            # 设置超时
            knowledge, understanding = await asyncio.wait_for(
                asyncio.gather(knowledge_task, understanding_task),
                timeout=self.timeout_config["rag_retrieval"]
            )
            
            # 确保understanding不为None
            if understanding is None:
                understanding = {"intent": "query", "domain": "general", "confidence": 0.5}
            
            # 确保knowledge是列表
            if knowledge is None:
                knowledge = []
            elif not isinstance(knowledge, list):
                knowledge = []
            
            result = {
                "knowledge": knowledge,
                "understanding": understanding,
                "query": user_input,
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果
            self._cache_rag_result(cache_key, result)
            
            return result
        except asyncio.TimeoutError:
            # 超时返回快速结果
            return {
                "knowledge": [],
                "understanding": {"intent": "query", "domain": "general", "confidence": 0.5},
                "query": user_input,
                "timeout": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # 异常时返回默认结果
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"RAG检索异常: {e}")
            return {
                "knowledge": [],
                "understanding": {"intent": "query", "domain": "general", "confidence": 0.5},
                "query": user_input,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _route_to_expert(
        self,
        user_input: str,
        rag_result: Dict
    ) -> Dict[str, Any]:
        """路由到对应专家⭐优化版（0.5秒超时）"""
        # 确保rag_result不为None
        if rag_result is None:
            rag_result = {"knowledge": [], "understanding": {"intent": "query", "domain": "general", "confidence": 0.5}}
        
        if not self.expert_router:
            return {"expert": "default", "domain": "general", "confidence": 0.5}
        
        # 检查缓存
        understanding = rag_result.get("understanding", {}) if rag_result else {}
        intent = understanding.get("intent", "") if isinstance(understanding, dict) else ""
        cache_key = f"expert:{user_input[:50]}:{intent}"
        if cache_key in self.expert_cache:
            cached = self.expert_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < 300:
                return cached["result"]
        
        try:
            # 带超时控制
            expert = await asyncio.wait_for(
                self.expert_router.route(user_input, rag_result),
                timeout=self.timeout_config["expert_routing"]
            )
            
            # 缓存结果
            self._cache_expert_result(cache_key, expert)
            
            return expert
        except asyncio.TimeoutError:
            # 超时返回默认专家
            return {"expert": "default", "confidence": 0.5, "timeout": True}
    
    async def _execute_module_function(
        self,
        expert: Dict,
        user_input: str,
        rag_result: Dict,
        slo_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行模块功能⭐优化版（3秒超时）"""
        if not self.module_executor:
            return {"result": "功能未实现", "type": "error"}
        
        try:
            slo_timeout = (slo_config or {}).get("module_timeout")
            module_timeout = slo_timeout or self.timeout_config["module_execution"]
            # 带超时控制
            result = await asyncio.wait_for(
                self.module_executor.execute(
                    expert=expert,
                    input=user_input,
                    context=rag_result
                ),
                timeout=module_timeout
            )
            return result
        except asyncio.TimeoutError:
            # 超时返回快速响应
            return {
                "result": "执行超时，请稍后重试或简化请求",
                "type": "timeout",
                "expert": expert.get("expert", "unknown")
            }
    
    async def _get_execution_result(self, module_result: Dict) -> Dict[str, Any]:
        """获取执行结果"""
        return module_result
    
    async def _second_rag_retrieval(
        self,
        user_input: str,
        execution_result: Dict,
        rag_result_1: Dict
    ) -> Dict[str, Any]:
        """
        第2次RAG检索：整合经验知识⭐优化版（缓存+超时）
        
        这是AI工作流最关键的步骤！
        通过检索历史经验和最佳实践，提升回答质量
        """
        # 确保execution_result和rag_result_1不为None
        if execution_result is None:
            execution_result = {"module": "default", "type": "unknown", "result": {}}
        if rag_result_1 is None:
            rag_result_1 = {"knowledge": [], "understanding": {"intent": "query"}}
        
        if not self.rag_service:
            return {
                "experience": [],
                "best_practices": [],
                "similar_cases": [],
                "integrated_knowledge": "",
                "recommendations": []
            }
        
        # 检查缓存⭐新增
        module = execution_result.get("module", "") if execution_result else ""
        result_type = execution_result.get("type", "") if execution_result else ""
        cache_key = f"rag2:{user_input[:50]}:{module}:{result_type}"
        if cache_key in self.rag2_cache:
            cached = self.rag2_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < 300:
                return cached["result"]
        
        # module和result_type已在上面定义
        
        # 构建更精准的查询语句
        execution_summary = self._summarize_execution_result(execution_result)
        experience_query = f"{user_input} {execution_summary} 历史经验 最佳实践 解决方案 成功案例"
        
        try:
            # 并行执行多个检索任务（带超时控制）⭐优化
            experience_task = self.rag_service.retrieve(
                query=experience_query,
                top_k=3,  # 减少检索数量以提升速度
                filter_type="experience",
                context={
                    "module": module,
                    "result_type": result_type,
                    "first_rag_result": rag_result_1
                }
            )
            
            similar_cases_task = self.rag_service.find_similar_cases(
                execution_result,
                top_k=3  # 减少案例数量
            )
            
            best_practices_task = self.rag_service.get_best_practices(
                module,
                top_k=3  # 减少最佳实践数量
            )
            
            # 并行执行所有检索（带超时）
            experience, similar_cases, best_practices = await asyncio.wait_for(
                asyncio.gather(
                    experience_task,
                    similar_cases_task,
                    best_practices_task,
                    return_exceptions=True
                ),
                timeout=self.timeout_config["rag2_retrieval"]
            )
            
            # 处理异常
            if isinstance(experience, Exception):
                experience = []
            if isinstance(similar_cases, Exception):
                similar_cases = []
            if isinstance(best_practices, Exception):
                best_practices = []
            
            # 整合所有知识，形成综合建议（这是"灵魂"的核心）
            integrated_knowledge = self._integrate_knowledge(
                experience, similar_cases, best_practices, [], execution_result
            )
            
            # 生成推荐建议
            recommendations = self._generate_recommendations(
                experience, similar_cases, best_practices, execution_result
            )
            
            result = {
                "experience": experience,
                "similar_cases": similar_cases,
                "best_practices": best_practices,
                "solutions": [],
                "integrated_knowledge": integrated_knowledge,
                "recommendations": recommendations,
                "module": module,
                "retrieval_count": {
                    "experience": len(experience) if isinstance(experience, list) else 0,
                    "cases": len(similar_cases) if isinstance(similar_cases, list) else 0,
                    "practices": len(best_practices) if isinstance(best_practices, list) else 0,
                    "solutions": 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 缓存结果⭐新增
            self._cache_rag2_result(cache_key, result)
            
            return result
            
        except asyncio.TimeoutError:
            # 超时返回快速结果
            return {
                "experience": [],
                "similar_cases": [],
                "best_practices": [],
                "solutions": [],
                "integrated_knowledge": "",
                "recommendations": [],
                "module": module,
                "timeout": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _summarize_execution_result(self, execution_result: Dict) -> str:
        """总结执行结果，用于构建查询"""
        summary_parts = []
        
        module = execution_result.get("module", "")
        if module:
            summary_parts.append(f"模块：{module}")
        
        result_type = execution_result.get("type", "")
        if result_type:
            summary_parts.append(f"类型：{result_type}")
        
        result_data = execution_result.get("result", {})
        if isinstance(result_data, dict):
            status = result_data.get("status", "")
            if status:
                summary_parts.append(f"状态：{status}")
        
        return " ".join(summary_parts)
    
    def _integrate_knowledge(
        self,
        experience: List[Dict],
        similar_cases: List[Dict],
        best_practices: List[str],
        solutions: List[Dict],
        execution_result: Dict
    ) -> str:
        """
        整合所有知识，形成综合知识摘要⭐灵魂的核心
        
        这是第2次RAG检索的"灵魂"所在：
        不是简单返回检索结果，而是智能整合所有知识
        """
        knowledge_parts = []
        
        # 整合最佳实践
        if best_practices:
            knowledge_parts.append("💡 最佳实践：")
            for i, practice in enumerate(best_practices[:3], 1):
                knowledge_parts.append(f"  {i}. {practice}")
        
        # 整合类似案例
        if similar_cases:
            knowledge_parts.append("\n📚 类似案例：")
            for i, case in enumerate(similar_cases[:3], 1):
                title = case.get("title") or case.get("content", "案例")[:60]
                knowledge_parts.append(f"  {i}. {title}")
        
        # 整合历史经验
        if experience:
            knowledge_parts.append("\n🔍 历史经验：")
            for i, exp in enumerate(experience[:3], 1):
                content = exp.get("content", "")[:80]
                if content:
                    knowledge_parts.append(f"  {i}. {content}...")
        
        # 整合解决方案
        if solutions:
            knowledge_parts.append("\n✅ 解决方案：")
            for i, solution in enumerate(solutions[:2], 1):
                content = solution.get("content", "")[:80]
                if content:
                    knowledge_parts.append(f"  {i}. {content}...")
        
        return "\n".join(knowledge_parts) if knowledge_parts else "暂无相关经验知识"
    
    def _generate_recommendations(
        self,
        experience: List[Dict],
        similar_cases: List[Dict],
        best_practices: List[str],
        execution_result: Dict
    ) -> List[str]:
        """
        基于检索到的知识生成推荐建议⭐
        
        这是第2次RAG检索的另一个"灵魂"功能：
        不仅检索知识，还要基于知识生成智能建议
        """
        recommendations = []
        
        # 基于最佳实践生成建议
        if best_practices:
            recommendations.extend([
                f"建议遵循最佳实践：{practice}"
                for practice in best_practices[:2]
            ])
        
        # 基于类似案例生成建议
        if similar_cases:
            for case in similar_cases[:2]:
                if case.get("metadata", {}).get("success", False):
                    recommendations.append(
                        f"参考成功案例：{case.get('title', '案例')}"
                    )
        
        # 基于历史经验生成建议
        if experience:
            for exp in experience[:2]:
                content = exp.get("content", "")
                if "优化" in content or "改进" in content:
                    recommendations.append(f"历史经验提示：{content[:50]}...")
        
        return recommendations[:5]  # 最多返回5条建议
    
    async def _generate_final_response(
        self,
        expert: Dict,
        execution_result: Dict,
        rag_result_2: Dict,
        search_context: Optional[Dict] = None,
        slo_context: Optional[Dict] = None
    ) -> str:
        """生成最终回复⭐使用真实LLM生成"""
        # 确保参数不为None
        if expert is None:
            expert = {"expert": "default", "domain": "general", "confidence": 0.5}
        if execution_result is None:
            execution_result = {"module": "default", "type": "unknown", "result": {}}
        if rag_result_2 is None:
            rag_result_2 = {
                "experience": [],
                "best_practices": [],
                "similar_cases": [],
                "integrated_knowledge": "",
                "recommendations": []
            }
        
        try:
            # 导入LLM服务
            from .llm_service import get_llm_service
            
            # 构建上下文信息
            context_parts = []
            
            # 添加执行结果
            result_data = execution_result.get("result", {}) if execution_result else {}
            if isinstance(result_data, dict):
                if result_data.get("message"):
                    context_parts.append(f"执行结果: {result_data['message']}")
                elif result_data.get("type"):
                    context_parts.append(f"模块类型: {result_data['type']}")
            elif isinstance(result_data, str):
                context_parts.append(f"执行结果: {result_data}")
            
            # 添加RAG检索的知识
            integrated_knowledge = rag_result_2.get("integrated_knowledge", "") if rag_result_2 else ""
            if integrated_knowledge and integrated_knowledge != "暂无相关经验知识":
                context_parts.append(f"相关知识: {integrated_knowledge}")
            
            best_practices = rag_result_2.get("best_practices", []) if rag_result_2 else []
            if best_practices:
                context_parts.append(f"最佳实践: {', '.join(best_practices[:3])}")
            
            similar_cases = rag_result_2.get("similar_cases", []) if rag_result_2 else []
            if similar_cases:
                case_summaries = []
                for case in similar_cases[:2]:
                    title = case.get("title") or case.get("content", "案例")[:50] if isinstance(case, dict) else str(case)[:50]
                    case_summaries.append(title)
                context_parts.append(f"类似案例: {', '.join(case_summaries)}")
            
            recommendations = rag_result_2.get("recommendations", []) if rag_result_2 else []
            if recommendations:
                context_parts.append(f"推荐建议: {', '.join(recommendations[:3])}")
            
            if search_context and search_context.get("results"):
                search_lines = []
                for idx, item in enumerate(search_context.get("results", [])[:3], 1):
                    title = item.get("title") or "外部结果"
                    snippet = item.get("snippet") or ""
                    url = item.get("url") or ""
                    search_lines.append(f"  {idx}. {title} - {snippet[:80]} ({url})")
                if search_lines:
                    engine = search_context.get("engine", "external")
                    context_parts.append(f"外部搜索（{engine}）：\n" + "\n".join(search_lines))
            
            if self.context_compressor:
                context_parts = self.context_compressor.compress_sections(context_parts)
            
            # 构建提示词
            system_prompt = """你是一个智能助手，能够根据执行结果、RAG检索的知识和历史经验，生成专业、准确、有用的回复。
请用中文回复，语言自然流畅，逻辑清晰。"""
            
            user_prompt = f"""基于以下信息生成回复：

{chr(10).join(context_parts) if context_parts else '任务执行完成'}

请综合以上信息，生成一个专业、有用的回复。"""
            
            # 调用真实LLM生成回复（优化：使用更快模型和更少token）
            llm_service = get_llm_service()
            temperature = 0.3
            max_tokens = 256
            if slo_context and slo_context.get("use_fast_model"):
                temperature = 0.2
                max_tokens = 200
            response = await llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
            
        except Exception as e:
            # 如果LLM调用失败，使用模板回复（但明确告知用户）
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM生成失败，使用模板回复: {e}")
            
            # 降级到模板回复
            response_parts = []
            result_data = execution_result.get("result", {})
            if isinstance(result_data, dict):
                if result_data.get("message"):
                    response_parts.append(result_data["message"])
                elif result_data.get("type"):
                    response_parts.append(f"✅ {result_data['type']}模块执行完成")
            elif isinstance(result_data, str):
                response_parts.append(result_data)
            
            integrated_knowledge = rag_result_2.get("integrated_knowledge", "")
            if integrated_knowledge and integrated_knowledge != "暂无相关经验知识":
                response_parts.append(f"\n\n🧠 相关知识:\n{integrated_knowledge}")
            
            if rag_result_2.get("recommendations"):
                recommendations_text = "\n".join([
                    f"- {rec}" for rec in rag_result_2["recommendations"][:3]
                ])
                response_parts.append(f"\n🔍 推荐建议:\n{recommendations_text}")
            
            if search_context and search_context.get("results"):
                external_text = "\n".join([
                    f"- {item.get('title', '结果')} ({item.get('url', '')})"
                    for item in search_context["results"][:3]
                ])
                response_parts.append(f"\n🌐 外部搜索参考:\n{external_text}")
            
            if slo_context and slo_context.get("enable_streaming"):
                response_parts.append("\n⏱️ 系统采用流式降级策略，优先返回概要结果。")
            
            if not response_parts:
                response_parts.append("✅ 任务执行完成")
            
            return "\n".join(response_parts) + f"\n\n⚠️ 注意: LLM服务暂时不可用，这是模板回复。错误: {str(e)}"

    def _prepare_external_search_context(self, search_context: Optional[Dict]) -> Optional[Dict]:
        """规范化外部搜索上下文"""
        if not search_context or not isinstance(search_context, dict):
            return None
        
        results = search_context.get("results") or []
        normalized_results = []
        for item in results[:5]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or "外部搜索结果"
            snippet = item.get("snippet") or item.get("description") or item.get("content") or ""
            url = item.get("url") or item.get("link") or ""
            if not snippet and not url:
                continue
            normalized_results.append({
                "title": title[:120],
                "snippet": snippet[:300],
                "url": url,
                "source": item.get("source") or search_context.get("engine") or "external",
                "score": item.get("score"),
            })
        
        if not normalized_results:
            return None
        
        return {
            "query": search_context.get("query", ""),
            "engine": search_context.get("engine", "auto"),
            "search_type": search_context.get("search_type", "web"),
            "fetched_at": search_context.get("fetched_at", datetime.now().isoformat()),
            "results": normalized_results
        }
    
    def _augment_rag_with_search(self, rag_result: Optional[Dict], search_context: Dict):
        """将外部搜索结果注入RAG检索知识中"""
        if not rag_result or not search_context:
            return
        
        results = search_context.get("results") or []
        if not results:
            return
        
        knowledge = rag_result.setdefault("knowledge", [])
        for item in results[:3]:
            knowledge.append({
                "title": item.get("title", "外部搜索"),
                "content": item.get("snippet", ""),
                "source": item.get("url"),
                "type": "external_search",
                "engine": search_context.get("engine"),
                "search_type": search_context.get("search_type")
            })
    
    def set_memo_system(self, memo_system):
        """设置备忘录系统"""
        self.memo_system = memo_system
    
    def set_rag_service(self, rag_service):
        """设置RAG服务"""
        self.rag_service = rag_service
    
    def set_expert_router(self, expert_router):
        """设置专家路由"""
        self.expert_router = expert_router
    
    def set_module_executor(self, module_executor):
        """设置模块执行器"""
        self.module_executor = module_executor
    
    def set_learning_monitor(self, learning_monitor):
        """设置学习监控"""
        self.learning_monitor = learning_monitor
        if self.learning_monitor and hasattr(self.learning_monitor, "set_event_bus"):
            self.learning_monitor.set_event_bus(self.event_bus)
    
    def set_resource_monitor(self, resource_monitor):
        """设置资源监控"""
        self.resource_monitor = resource_monitor
    
    def set_task_planning(self, task_planning):
        """设置任务规划系统"""
        self.task_planning = task_planning
        self._initialize_task_orchestrator()

    def _initialize_task_orchestrator(self):
        if self.task_planning:
            self.task_orchestrator = TaskOrchestrator(
                task_planning=self.task_planning,
                event_bus=self.event_bus,
                closure_recorder=self.closure_recorder
            )
    
    def _cache_rag_result(self, cache_key: str, result: Dict):
        """缓存RAG检索结果"""
        self.rag_cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now().isoformat()
        }
        self._cleanup_cache("rag_cache", self.max_cache_size)
    
    def _cache_expert_result(self, cache_key: str, result: Dict):
        """缓存专家路由结果"""
        self.expert_cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now().isoformat()
        }
        self._cleanup_cache("expert_cache", self.max_cache_size)
    
    def _cache_rag2_result(self, cache_key: str, result: Dict):
        """缓存第2次RAG检索结果"""
        self.rag2_cache[cache_key] = {
            "result": result,
            "cached_at": datetime.now().isoformat()
        }
        self._cleanup_cache("rag2_cache", self.max_cache_size)
    
    def _cleanup_cache(self, cache_name: str, max_size: int):
        """清理缓存（LRU策略）"""
        cache = getattr(self, cache_name, {})
        if len(cache) > max_size:
            # 删除最旧的缓存项
            oldest_key = min(cache.keys(), 
                           key=lambda k: cache[k]["cached_at"])
            del cache[oldest_key]

