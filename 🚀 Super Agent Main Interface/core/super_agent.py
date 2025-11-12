"""
超级Agent核心引擎
实现AI工作流9步骤，包括2次RAG检索
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

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
        
        # 自动初始化依赖
        self._initialize_dependencies()
    
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
            rag_result_1 = await self._first_rag_retrieval(user_input, context)
            
            # 步骤4: 路由到对应专家
            expert = await self._route_to_expert(user_input, rag_result_1)
            
            # 步骤5: 专家分析并调用模块功能执行
            module_result = await self._execute_module_function(expert, user_input, rag_result_1)
            
            # 步骤6: 功能模块执行任务，返回结果
            execution_result = await self._get_execution_result(module_result)
            
            # 步骤7: 专家接收结果，第2次RAG检索（整合经验知识）⭐优化版（缓存+超时）
            rag_result_2 = await self._second_rag_retrieval(
                user_input, execution_result, rag_result_1
            )
            
            # 步骤8: 专家综合生成最终回复
            final_response = await self._generate_final_response(
                expert, execution_result, rag_result_2
            )
            
            # 步骤2完成：处理备忘录（异步执行，不阻塞主流程）
            memo_created = False
            if memo_task:
                try:
                    important_info = await memo_task
                    if important_info and self.memo_system:
                        memo = await self.memo_system.add_memo(important_info)
                        memo_created = True
                        
                        # 如果是任务类型，异步提炼到任务规划系统
                        if important_info.get("type") == "task" and self.task_planning:
                            asyncio.create_task(
                                self.task_planning.extract_tasks_from_memos()
                            )
                except asyncio.TimeoutError:
                    pass  # 超时不影响主流程
                except Exception:
                    pass  # 错误不影响主流程
            
            # 步骤9: 返回给用户
            response_time = (datetime.now() - start_time).total_seconds()
            
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
                "memo_created": memo_created
            }
            
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
        
        # 判断是否应该创建备忘录（提高识别准确率）
        should_create = (
            has_task or  # 包含任务关键词
            len(dates) > 0 or  # 包含日期
            len(times) > 0 or  # 包含时间
            len(contacts) > 0 or  # 包含联系人
            importance >= 4 or  # 重要性高
            len(content) > 50  # 内容较长（可能是重要信息）
        )
        
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
                top_k=5,
                context=context
            )
            understanding_task = self.rag_service.understand_intent(user_input)
            
            # 设置超时
            knowledge, understanding = await asyncio.wait_for(
                asyncio.gather(knowledge_task, understanding_task),
                timeout=self.timeout_config["rag_retrieval"]
            )
            
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
                "understanding": {"intent": "query", "confidence": 0.5},
                "query": user_input,
                "timeout": True,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _route_to_expert(
        self,
        user_input: str,
        rag_result: Dict
    ) -> Dict[str, Any]:
        """路由到对应专家⭐优化版（0.5秒超时）"""
        if not self.expert_router:
            return {"expert": "default", "confidence": 0.5}
        
        # 检查缓存
        cache_key = f"expert:{user_input[:50]}:{rag_result.get('understanding', {}).get('intent', '')}"
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
        rag_result: Dict
    ) -> Dict[str, Any]:
        """执行模块功能⭐优化版（3秒超时）"""
        if not self.module_executor:
            return {"result": "功能未实现", "type": "error"}
        
        try:
            # 带超时控制
            result = await asyncio.wait_for(
                self.module_executor.execute(
                    expert=expert,
                    input=user_input,
                    context=rag_result
                ),
                timeout=self.timeout_config["module_execution"]
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
        if not self.rag_service:
            return {
                "experience": [],
                "best_practices": [],
                "similar_cases": [],
                "integrated_knowledge": "",
                "recommendations": []
            }
        
        # 检查缓存⭐新增
        cache_key = f"rag2:{user_input[:50]}:{execution_result.get('module', '')}:{execution_result.get('type', '')}"
        if cache_key in self.rag2_cache:
            cached = self.rag2_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < 300:
                return cached["result"]
        
        module = execution_result.get("module", "default")
        result_type = execution_result.get("type", "unknown")
        
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
        rag_result_2: Dict
    ) -> str:
        """生成最终回复"""
        # 综合专家分析、执行结果和经验知识
        response_parts = []
        
        # 添加执行结果
        result_data = execution_result.get("result", {})
        if isinstance(result_data, dict):
            if result_data.get("message"):
                response_parts.append(result_data["message"])
            elif result_data.get("type"):
                response_parts.append(f"✅ {result_data['type']}模块执行完成")
        elif isinstance(result_data, str):
            response_parts.append(result_data)
        
        # ⭐第2次RAG检索的灵魂：优先使用整合后的知识
        integrated_knowledge = rag_result_2.get("integrated_knowledge", "")
        if integrated_knowledge and integrated_knowledge != "暂无相关经验知识":
            response_parts.append("\n\n" + "="*50)
            response_parts.append("🧠 基于历史经验和最佳实践的综合知识（第2次RAG检索）：")
            response_parts.append("="*50)
            response_parts.append(integrated_knowledge)
        
        # 添加智能推荐建议（第2次RAG检索的另一个灵魂功能）
        recommendations = rag_result_2.get("recommendations", [])
        if recommendations:
            response_parts.append("\n\n💡 智能推荐建议：")
            for i, rec in enumerate(recommendations, 1):
                response_parts.append(f"{i}. {rec}")
        
        # 如果整合知识为空，则使用原始数据（向后兼容）
        if not integrated_knowledge or integrated_knowledge == "暂无相关经验知识":
            best_practices = rag_result_2.get("best_practices", [])
            if best_practices:
                response_parts.append("\n\n💡 基于历史经验的最佳实践：")
                for i, practice in enumerate(best_practices[:3], 1):
                    response_parts.append(f"{i}. {practice}")
            
            similar_cases = rag_result_2.get("similar_cases", [])
            if similar_cases:
                response_parts.append("\n\n📚 参考类似案例：")
                for i, case in enumerate(similar_cases[:2], 1):
                    title = case.get("title") or case.get("content", "案例")[:50]
                    response_parts.append(f"{i}. {title}")
            
            experience = rag_result_2.get("experience", [])
            if experience:
                response_parts.append("\n\n🔍 相关历史经验：")
                for i, exp in enumerate(experience[:2], 1):
                    content = exp.get("content", "")[:100]
                    if content:
                        response_parts.append(f"{i}. {content}...")
        
        # 如果没有内容，返回默认回复
        if not response_parts:
            response_parts.append("✅ 任务执行完成")
        
        return "\n".join(response_parts)
    
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
    
    def set_resource_monitor(self, resource_monitor):
        """设置资源监控"""
        self.resource_monitor = resource_monitor
    
    def set_task_planning(self, task_planning):
        """设置任务规划系统"""
        self.task_planning = task_planning
    
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

