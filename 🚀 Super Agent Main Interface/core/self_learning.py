"""
自我学习监控系统
整合自🧠 Self Learning System/，融合到超级Agent
集成工作流监控和资源自动调节功能
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .workflow_monitor import WorkflowMonitor
from .resource_auto_adjuster import ResourceAutoAdjuster
from .learning_events import LearningEventBus, LearningEventType

class SelfLearningMonitor:
    """
    自我学习监控系统
    
    功能：
    1. 监控AI工作流9步骤
    2. 识别问题和优化机会
    3. 调用编程助手优化代码
    4. 将问题和解决方案存入RAG
    """
    
    def __init__(self, rag_service=None, coding_assistant=None, resource_manager=None, event_bus: Optional[LearningEventBus] = None):
        self.rag_service = rag_service
        self.coding_assistant = coding_assistant
        self.resource_manager = resource_manager
        self.event_bus = event_bus
        self.workflow_logs = []
        self.problems = []
        self.solutions = []
        self.latest_recommendations: Dict[str, Dict[str, Any]] = {}
        self.latest_resource_signals: List[Dict[str, Any]] = []

    def set_event_bus(self, event_bus: LearningEventBus):
        self.event_bus = event_bus

    async def _publish_event(self, event_type: LearningEventType, severity: str, payload: Dict[str, Any]):
        if self.event_bus:
            await self.event_bus.publish_event(
                event_type=event_type,
                source="self_learning_monitor",
                severity=severity,
                payload=payload
            )

        # 如果coding_assistant是URL，创建HTTP客户端
        if isinstance(coding_assistant, str):
            self.coding_assistant_url = coding_assistant
        else:
            self.coding_assistant_url = None
        
        # 初始化工作流监控器
        self.workflow_monitor = WorkflowMonitor(
            rag_service=rag_service,
            resource_manager=resource_manager
        )
        
        # 初始化资源自动调节器
        self.resource_adjuster = ResourceAutoAdjuster(
            resource_manager=resource_manager
        )
        
        # 启动后台监控任务
        self._background_task = None
        
    async def monitor_workflow(self, workflow_data: Dict[str, Any]):
        """
        监控AI工作流
        
        Args:
            workflow_data: 工作流数据，包含9步骤的完整信息
        """
        # 记录工作流日志
        self.workflow_logs.append({
            **workflow_data,
            "timestamp": datetime.now().isoformat()
        })
        
        # 分析工作流性能
        await self._analyze_performance(workflow_data)
        
        # 检测问题
        problems = await self._detect_problems(workflow_data)
        if problems:
            await self._handle_problems(problems, workflow_data)
    
    async def _analyze_performance(self, workflow_data: Dict):
        """分析工作流性能⭐增强版"""
        response_time = workflow_data.get("response_time", 0)
        
        # 分析各步骤耗时
        step_times = self._analyze_step_times(workflow_data)
        
        # 如果响应时间超过2秒，记录性能问题
        if response_time > 2.0:
            await self._record_performance_issue(response_time, workflow_data)
        
        # 分析性能趋势（基于历史数据）
        if len(self.workflow_logs) > 10:
            trend = self._analyze_performance_trend()
            if trend.get("degrading"):
                await self._handle_performance_degradation(trend, workflow_data)
        
        # 识别性能瓶颈
        bottlenecks = self._identify_bottlenecks(step_times, response_time)
        if bottlenecks:
            await self._handle_bottlenecks(bottlenecks, workflow_data)
    
    def _analyze_step_times(self, workflow_data: Dict) -> Dict[str, float]:
        """分析各步骤耗时"""
        # 估算各步骤耗时（基于工作流数据）
        step_times = {}
        
        # 第1次RAG检索耗时
        rag_1 = workflow_data.get("rag_1", {})
        if rag_1:
            step_times["rag_1"] = 0.3  # 估算值
        
        # 专家路由耗时
        expert = workflow_data.get("expert", {})
        if expert:
            step_times["routing"] = 0.1
        
        # 模块执行耗时
        execution = workflow_data.get("execution", {})
        if execution:
            step_times["execution"] = 0.5  # 估算值
        
        # 第2次RAG检索耗时
        rag_2 = workflow_data.get("rag_2", {})
        if rag_2:
            step_times["rag_2"] = 0.4
        
        # 生成回复耗时
        response = workflow_data.get("response", {})
        if response:
            step_times["response"] = 0.2
        
        return step_times
    
    def _analyze_performance_trend(self) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(self.workflow_logs) < 10:
            return {"degrading": False}
        
        # 获取最近20条记录
        recent_logs = self.workflow_logs[-20:]
        older_logs = self.workflow_logs[-40:-20] if len(self.workflow_logs) >= 40 else []
        
        if not older_logs:
            return {"degrading": False}
        
        # 计算平均响应时间
        recent_avg = sum(
            log.get("response_time", 0) 
            for log in recent_logs 
            if "response_time" in log
        ) / len(recent_logs)
        
        older_avg = sum(
            log.get("response_time", 0) 
            for log in older_logs 
            if "response_time" in log
        ) / len(older_logs)
        
        # 如果性能下降超过20%，认为在退化
        degrading = recent_avg > older_avg * 1.2
        
        return {
            "degrading": degrading,
            "recent_avg": recent_avg,
            "older_avg": older_avg,
            "degradation_rate": (recent_avg - older_avg) / older_avg * 100 if older_avg > 0 else 0
        }
    
    async def _handle_performance_degradation(self, trend: Dict, workflow_data: Dict):
        """处理性能退化"""
        problem = {
            "type": "performance_degradation",
            "severity": "high",
            "description": f"性能退化 {trend['degradation_rate']:.1f}%，最近平均响应时间 {trend['recent_avg']:.2f}秒",
            "trend": trend
        }
        
        # 尝试自动优化
        solution = await self._auto_optimize_performance(problem, workflow_data)
        if solution:
            await self._save_solution(problem, solution)
    
    def _identify_bottlenecks(self, step_times: Dict[str, float], total_time: float) -> List[Dict]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        if not step_times or total_time == 0:
            return bottlenecks
        
        # 找出耗时超过总时间30%的步骤
        threshold = total_time * 0.3
        
        for step, time in step_times.items():
            if time > threshold:
                bottlenecks.append({
                    "step": step,
                    "time": time,
                    "percentage": (time / total_time * 100) if total_time > 0 else 0,
                    "threshold": threshold
                })
        
        return bottlenecks
    
    async def _handle_bottlenecks(self, bottlenecks: List[Dict], workflow_data: Dict):
        """处理性能瓶颈"""
        for bottleneck in bottlenecks:
            problem = {
                "type": "bottleneck",
                "severity": "medium",
                "description": f"步骤 {bottleneck['step']} 耗时过长，占总时间 {bottleneck['percentage']:.1f}%",
                "bottleneck": bottleneck
            }
            
            # 生成优化建议
            solution = await self._generate_bottleneck_solution(bottleneck, workflow_data)
            if solution:
                await self._save_solution(problem, solution)
    
    async def _generate_bottleneck_solution(self, bottleneck: Dict, workflow_data: Dict) -> Optional[Dict]:
        """生成瓶颈优化方案"""
        step = bottleneck.get("step", "")
        
        solutions = {
            "rag_1": {
                "type": "optimization",
                "suggestions": [
                    "优化RAG检索查询，使用更精确的关键词",
                    "减少检索数量（top_k）",
                    "启用缓存机制",
                    "使用并行检索"
                ],
                "priority": "high"
            },
            "rag_2": {
                "type": "optimization",
                "suggestions": [
                    "优化第2次RAG检索策略",
                    "减少检索的案例数量",
                    "使用异步并行检索",
                    "启用结果缓存"
                ],
                "priority": "high"
            },
            "execution": {
                "type": "optimization",
                "suggestions": [
                    "优化模块执行逻辑",
                    "使用异步执行",
                    "添加执行结果缓存",
                    "优化数据库查询"
                ],
                "priority": "medium"
            },
            "routing": {
                "type": "optimization",
                "suggestions": [
                    "优化专家路由算法",
                    "使用缓存的路由结果",
                    "简化路由逻辑"
                ],
                "priority": "low"
            }
        }
        
        solution = solutions.get(step)
        if solution:
            return {
                **solution,
                "bottleneck": bottleneck,
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    async def _auto_optimize_performance(self, problem: Dict, workflow_data: Dict) -> Optional[Dict]:
        """自动优化性能⭐增强版"""
        # 生成优化建议
        optimization_suggestions = []
        
        # 基于问题类型生成建议
        if problem.get("type") == "performance_degradation":
            optimization_suggestions.extend([
                "检查最近代码变更是否引入性能问题",
                "分析资源使用情况（CPU/内存）",
                "检查数据库查询性能",
                "优化RAG检索策略",
                "启用缓存机制"
            ])
        
        # 调用编程助手进行代码优化
        if self.coding_assistant_url or self.coding_assistant:
            code_optimization = await self._auto_fix_problem(problem, workflow_data)
            if code_optimization:
                optimization_suggestions.append("代码优化建议已生成")
        
        if optimization_suggestions:
            return {
                "type": "performance_optimization",
                "suggestions": optimization_suggestions,
                "problem": problem,
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    async def _detect_problems(self, workflow_data: Dict) -> List[Dict]:
        """检测问题"""
        problems = []
        
        # 检测错误
        if not workflow_data.get("response", {}).get("success", True):
            problems.append({
                "type": "error",
                "severity": "high",
                "description": workflow_data.get("response", {}).get("error", "未知错误")
            })
        
        # 检测性能问题
        response_time = workflow_data.get("response_time", 0)
        if response_time > 2.0:
            problems.append({
                "type": "performance",
                "severity": "medium",
                "description": f"响应时间过长: {response_time:.2f}秒"
            })
        
        # 检测RAG检索质量问题
        rag_1 = workflow_data.get("rag_1", {})
        rag_2 = workflow_data.get("rag_2", {})
        
        if not rag_1.get("knowledge") or len(rag_1.get("knowledge", [])) == 0:
            problems.append({
                "type": "rag_quality",
                "severity": "medium",
                "description": "第1次RAG检索未找到相关知识"
            })
        
        if not rag_2.get("experience") or len(rag_2.get("experience", [])) == 0:
            problems.append({
                "type": "rag_quality",
                "severity": "low",
                "description": "第2次RAG检索未找到相关经验"
            })
        
        return problems
    
    async def _handle_problems(self, problems: List[Dict], workflow_data: Dict):
        """处理问题"""
        for problem in problems:
            # 记录问题
            self.problems.append({
                **problem,
                "workflow_data": workflow_data,
                "timestamp": datetime.now().isoformat()
            })
            
            await self._publish_event(
                LearningEventType.WORKFLOW_ANOMALY,
                severity=problem.get("severity", "medium"),
                payload={"problem": problem, "workflow": workflow_data}
            )
            
            # 尝试自动解决
            if problem["severity"] in ["high", "medium"]:
                solution = await self._auto_fix_problem(problem, workflow_data)
                if solution:
                    await self._save_solution(problem, solution)
    
    async def _auto_fix_problem(self, problem: Dict, workflow_data: Dict) -> Optional[Dict]:
        """自动修复问题⭐增强版"""
        problem_type = problem.get("type", "")
        
        # 性能问题优化
        if problem_type in ["performance", "performance_degradation", "bottleneck"]:
            # 调用编程助手优化代码
            if self.coding_assistant_url:
                # 通过HTTP调用
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        # 构建优化请求
                        optimization_request = {
                            "problem_description": problem.get("description", ""),
                            "problem_type": problem_type,
                            "context": {
                                "workflow_data": workflow_data,
                                "problem": problem
                            },
                            "optimization_type": "performance"
                        }
                        
                        response = await client.post(
                            f"{self.coding_assistant_url}/optimize",
                            json=optimization_request
                        )
                        if response.status_code == 200:
                            optimization = response.json()
                            return {
                                "type": "code_optimization",
                                "optimization": optimization,
                                "applied": False,  # 需要人工确认
                                "timestamp": datetime.now().isoformat()
                            }
                except Exception as e:
                    print(f"调用编程助手失败: {e}")
                    # 返回基础优化建议
                    return self._generate_basic_optimization(problem, workflow_data)
            elif self.coding_assistant:
                # 直接调用对象
                try:
                    optimization = await self.coding_assistant.optimize_performance(
                        problem_description=problem.get("description", ""),
                        context=workflow_data
                    )
                    return {
                        "type": "code_optimization",
                        "optimization": optimization,
                        "applied": False,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    print(f"调用编程助手失败: {e}")
                    return self._generate_basic_optimization(problem, workflow_data)
            else:
                # 没有编程助手，返回基础优化建议
                return self._generate_basic_optimization(problem, workflow_data)
        
        # RAG质量问题优化
        elif problem_type == "rag_quality":
            return await self._optimize_rag_quality(problem, workflow_data)
        
        # 错误问题处理
        elif problem_type == "error":
            return await self._handle_error_problem(problem, workflow_data)
        
        return None
    
    def _generate_basic_optimization(self, problem: Dict, workflow_data: Dict) -> Dict:
        """生成基础优化建议（当编程助手不可用时）"""
        suggestions = []
        
        if problem.get("type") == "performance":
            suggestions.extend([
                "检查是否有不必要的数据库查询",
                "启用结果缓存",
                "使用异步处理",
                "优化算法复杂度"
            ])
        
        return {
            "type": "basic_optimization",
            "suggestions": suggestions,
            "problem": problem,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _optimize_rag_quality(self, problem: Dict, workflow_data: Dict) -> Optional[Dict]:
        """优化RAG检索质量"""
        rag_step = "rag_1" if "第1次" in problem.get("description", "") else "rag_2"
        rag_data = workflow_data.get(rag_step, {})
        
        suggestions = []
        
        # 如果检索结果为空，建议优化查询
        if not rag_data.get("knowledge") or len(rag_data.get("knowledge", [])) == 0:
            suggestions.extend([
                "优化RAG查询关键词",
                "扩大检索范围（增加top_k）",
                "检查知识库是否有相关内容",
                "使用同义词扩展查询"
            ])
        
        # 如果检索结果相关性低
        if rag_data.get("knowledge"):
            avg_score = sum(
                item.get("score", 0) 
                for item in rag_data.get("knowledge", [])
            ) / len(rag_data.get("knowledge", []))
            
            if avg_score < 0.5:
                suggestions.extend([
                    "优化向量检索模型",
                    "改进查询预处理",
                    "使用混合检索（向量+关键词）",
                    "调整检索参数"
                ])
        
        if suggestions:
            return {
                "type": "rag_optimization",
                "suggestions": suggestions,
                "rag_step": rag_step,
                "problem": problem,
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    async def _handle_error_problem(self, problem: Dict, workflow_data: Dict) -> Optional[Dict]:
        """处理错误问题"""
        error_description = problem.get("description", "")
        
        suggestions = []
        
        # 根据错误类型生成建议
        if "timeout" in error_description.lower():
            suggestions.extend([
                "增加请求超时时间",
                "优化慢查询",
                "使用异步处理",
                "添加重试机制"
            ])
        elif "connection" in error_description.lower():
            suggestions.extend([
                "检查网络连接",
                "增加连接池大小",
                "添加连接重试机制",
                "检查服务可用性"
            ])
        else:
            suggestions.extend([
                "检查错误日志",
                "添加更详细的错误处理",
                "实现错误恢复机制",
                "记录错误上下文"
            ])
        
        return {
            "type": "error_handling",
            "suggestions": suggestions,
            "problem": problem,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _save_solution(self, problem: Dict, solution: Dict):
        """保存解决方案到RAG"""
        if self.rag_service:
            knowledge_entry = {
                "type": "problem_solution",
                "problem": problem,
                "solution": solution,
                "timestamp": datetime.now().isoformat()
            }
            await self.rag_service.store_knowledge(knowledge_entry)
        
        self.solutions.append({
            "problem": problem,
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        })
        
        await self._publish_event(
            LearningEventType.PERFORMANCE,
            severity=problem.get("severity", "info"),
            payload={"problem": problem, "solution": solution}
        )
    
    async def _record_performance_issue(self, response_time: float, workflow_data: Dict):
        """记录性能问题"""
        issue = {
            "type": "performance",
            "response_time": response_time,
            "threshold": 2.0,
            "workflow": workflow_data,
            "timestamp": datetime.now().isoformat()
        }
        self.problems.append(issue)
        await self._publish_event(
            LearningEventType.PERFORMANCE,
            severity="medium",
            payload=issue
        )
    
    async def record_error(self, error_info: Dict):
        """记录错误"""
        error_entry = {
            "type": "error",
            "severity": "high",
            **error_info
        }
        self.problems.append(error_entry)
        await self._publish_event(
            LearningEventType.WORKFLOW_ANOMALY,
            severity="high",
            payload=error_entry
        )
        
        # 存入RAG
        if self.rag_service:
            await self.rag_service.store_knowledge({
                "type": "error_log",
                **error_entry
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息⭐增强版"""
        stats = {
            "total_workflows": len(self.workflow_logs),
            "total_problems": len(self.problems),
            "total_solutions": len(self.solutions),
            "average_response_time": self._calculate_avg_response_time(),
            "problem_types": self._get_problem_types(),
            "solution_rate": self._calculate_solution_rate(),
            "performance_trend": self._get_performance_trend(),
            "top_bottlenecks": self._get_top_bottlenecks(),
            "status": "active" if self.workflow_logs else "idle",
            "optimization_suggestions": self._get_optimization_suggestions(),
            "last_update": datetime.now().isoformat()
        }
        stats["interaction_recommendations"] = self._generate_interaction_recommendations(stats)
        stats["resource_signals"] = self._generate_resource_signals()
        stats["alert_level"] = self._calculate_alert_level(stats)
        return stats
    
    def _get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 基于问题统计生成建议
        if len(self.problems) > 10:
            suggestions.append(f"检测到{len(self.problems)}个问题，建议优先处理高优先级问题")
        
        # 基于响应时间生成建议
        avg_time = self._calculate_avg_response_time()
        if avg_time > 2.0:
            suggestions.append(f"平均响应时间{avg_time:.2f}秒，超过2秒目标，建议优化性能瓶颈")
        
        # 基于瓶颈生成建议
        bottlenecks = self._get_top_bottlenecks(3)
        if bottlenecks:
            suggestions.append(f"发现{len(bottlenecks)}个性能瓶颈，建议优化相关模块")
        
        return suggestions[:5]  # 最多返回5条建议
    
    def _calculate_solution_rate(self) -> float:
        """计算问题解决率"""
        if not self.problems:
            return 0.0
        
        solved_problems = len([
            p for p in self.problems 
            if any(s.get("problem", {}).get("type") == p.get("type") 
                   for s in self.solutions)
        ])
        
        return (solved_problems / len(self.problems) * 100) if self.problems else 0.0

    def _generate_interaction_recommendations(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成交互/资源建议"""
        recommendations: List[Dict[str, Any]] = []
        avg_response = stats.get("average_response_time") or 0.0
        problem_types = stats.get("problem_types", {})
        timestamp = datetime.now().isoformat()

        def _add(payload: Dict[str, Any]):
            rec_id = payload.get("id") or f"rec_{len(recommendations)+1}_{int(datetime.now().timestamp())}"
            payload["id"] = rec_id
            payload["timestamp"] = timestamp
            recommendations.append(payload)

        if avg_response > 2.0:
            _add({
                "title": "响应时延过高 · 建议扩容算力",
                "description": f"最近平均响应 {avg_response:.2f}s，已超过2秒 SLO，可触发一次 LLM 推理扩容。",
                "severity": "high",
                "action_type": "resource_authorization",
                "payload": {
                    "description": "扩容LLM推理节点 CPU/内存",
                    "action_type": "scale_up",
                    "risk_level": "medium",
                    "expected_improvement": "降低响应时间",
                    "rollback_plan": "性能稳定后恢复原配置"
                }
            })

        rag_quality_issues = problem_types.get("rag_quality", 0)
        if rag_quality_issues:
            _add({
                "title": "RAG命中不足 · 建议刷新索引",
                "description": f"检测到 {rag_quality_issues} 次 RAG 命中不足，可重新执行预处理/入库。",
                "severity": "medium",
                "action_type": "interaction",
                "payload": {
                    "instruction": "在RAG管理页执行一次批量清洗与向量重建。",
                    "module": "rag"
                }
            })

        performance_trend = stats.get("performance_trend", {})
        if performance_trend.get("trend") == "degrading":
            _add({
                "title": "性能趋势下滑 · 建议执行学习回放",
                "description": f"性能退化率 {performance_trend.get('degradation_rate', 0):.1f}%，可调度学习回放脚本。",
                "severity": "medium",
                "action_type": "interaction",
                "payload": {
                    "instruction": "触发自学习优化脚本，回放最近任务。",
                    "module": "self_learning"
                }
            })

        self.latest_recommendations = {rec["id"]: rec for rec in recommendations}
        return recommendations

    def _generate_resource_signals(self) -> List[Dict[str, Any]]:
        """输出资源信号"""
        signals: List[Dict[str, Any]] = []
        if not self.resource_manager:
            self.latest_resource_signals = []
            return signals
        try:
            snapshot = self.resource_manager.get_current_status()
        except Exception:
            self.latest_resource_signals = []
            return []

        def _push(name: str, value: Optional[float], threshold: float, suggestion: str):
            if value is None:
                return
            severity = "high" if value >= threshold + 10 else "medium"
            signals.append({
                "resource": name,
                "value": round(value, 1),
                "threshold": threshold,
                "severity": severity,
                "suggestion": suggestion
            })

        cpu_percent = snapshot.get("cpu", {}).get("percent")
        memory_percent = snapshot.get("memory", {}).get("percent")
        disk_percent = snapshot.get("disk", {}).get("percent")
        _push("CPU", cpu_percent, 75, "评估推理请求并考虑扩容/限流")
        _push("内存", memory_percent, 80, "清理缓存或扩容内存")
        _push("磁盘", disk_percent, 85, "释放空间或扩展磁盘容量")
        self.latest_resource_signals = signals
        return signals

    def _calculate_alert_level(self, stats: Dict[str, Any]) -> str:
        score = 0
        if stats.get("total_problems", 0) > 5:
            score += 2
        elif stats.get("total_problems", 0) > 0:
            score += 1
        avg_response = stats.get("average_response_time", 0.0)
        if avg_response > 2.0:
            score += 2
        elif avg_response > 1.5:
            score += 1
        if len(self.latest_resource_signals) >= 2:
            score += 2
        elif self.latest_resource_signals:
            score += 1
        if score >= 4:
            return "high"
        if score >= 2:
            return "medium"
        return "low"

    def get_recommendation(self, rec_id: str) -> Optional[Dict[str, Any]]:
        return self.latest_recommendations.get(rec_id)

    def mark_recommendation_applied(self, rec_id: str) -> Optional[Dict[str, Any]]:
        rec = self.latest_recommendations.get(rec_id)
        if rec:
            rec["applied_at"] = datetime.now().isoformat()
        return rec
    
    def _get_performance_trend(self) -> Dict[str, Any]:
        """获取性能趋势"""
        if len(self.workflow_logs) < 5:
            return {"trend": "insufficient_data"}
        
        recent_logs = self.workflow_logs[-10:]
        response_times = [
            log.get("response_time", 0) 
            for log in recent_logs 
            if "response_time" in log
        ]
        
        if not response_times:
            return {"trend": "no_data"}
        
        # 计算趋势（简单线性回归）
        n = len(response_times)
        x = list(range(n))
        y = response_times
        
        avg_x = sum(x) / n
        avg_y = sum(y) / n
        
        numerator = sum((x[i] - avg_x) * (y[i] - avg_y) for i in range(n))
        denominator = sum((x[i] - avg_x) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        if slope > 0.01:
            trend = "degrading"
        elif slope < -0.01:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "slope": slope,
            "recent_avg": avg_y,
            "min": min(response_times),
            "max": max(response_times)
        }
    
    def _get_top_bottlenecks(self, top_n: int = 3) -> List[Dict]:
        """获取主要性能瓶颈"""
        bottleneck_problems = [
            p for p in self.problems 
            if p.get("type") == "bottleneck"
        ]
        
        # 按严重程度排序
        bottleneck_problems.sort(
            key=lambda x: x.get("bottleneck", {}).get("percentage", 0),
            reverse=True
        )
        
        return bottleneck_problems[:top_n]
    
    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if not self.workflow_logs:
            return 0.0
        
        total_time = sum(
            log.get("response_time", 0) 
            for log in self.workflow_logs 
            if "response_time" in log
        )
        return total_time / len(self.workflow_logs)
    
    def _get_problem_types(self) -> Dict[str, int]:
        """获取问题类型统计"""
        types = {}
        for problem in self.problems:
            ptype = problem.get("type", "unknown")
            types[ptype] = types.get(ptype, 0) + 1
        return types

