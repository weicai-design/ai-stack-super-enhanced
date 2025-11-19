"""
工作流因果分析器
P0-013: 工作流埋点/因果分析/策略优化与交互建议引擎
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class WorkflowCausalAnalyzer:
    """
    工作流因果分析器
    
    功能：
    1. 工作流埋点数据收集
    2. 因果分析（5Why、相关性分析）
    3. 策略优化建议
    4. 交互建议引擎
    """
    
    def __init__(self, workflow_monitor=None, learning_monitor=None):
        self.workflow_monitor = workflow_monitor
        self.learning_monitor = learning_monitor
        self.workflow_traces: List[Dict[str, Any]] = []
        self.causal_chains: List[Dict[str, Any]] = []
        self.optimization_strategies: List[Dict[str, Any]] = []
        self.interaction_suggestions: List[Dict[str, Any]] = []
        
    async def record_workflow_trace(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ):
        """
        记录工作流埋点数据
        
        Args:
            workflow_id: 工作流ID
            steps: 步骤列表
            metrics: 性能指标
        """
        trace = {
            "workflow_id": workflow_id,
            "timestamp": datetime.now().isoformat(),
            "steps": steps,
            "metrics": metrics,
            "total_duration": metrics.get("total_duration", 0),
            "success": metrics.get("success", True),
            "bottlenecks": metrics.get("bottlenecks", []),
            "errors": metrics.get("errors", [])
        }
        self.workflow_traces.append(trace)
        
        # 保留最近1000条
        if len(self.workflow_traces) > 1000:
            self.workflow_traces = self.workflow_traces[-1000:]
        
        # 自动触发因果分析
        if not metrics.get("success") or metrics.get("total_duration", 0) > 2.0:
            await self._analyze_causal_chain(trace)
    
    async def _analyze_causal_chain(self, trace: Dict[str, Any]):
        """
        因果分析（5Why方法）
        
        Args:
            trace: 工作流追踪数据
        """
        if trace.get("success"):
            # 性能问题分析
            if trace.get("total_duration", 0) > 2.0:
                causal_chain = await self._five_why_analysis(
                    issue_type="performance",
                    issue_description=f"响应时间过长: {trace['total_duration']:.2f}秒",
                    trace=trace
                )
                if causal_chain:
                    self.causal_chains.append(causal_chain)
        else:
            # 错误问题分析
            errors = trace.get("errors", [])
            if errors:
                for error in errors:
                    causal_chain = await self._five_why_analysis(
                        issue_type="error",
                        issue_description=error.get("message", "未知错误"),
                        trace=trace
                    )
                    if causal_chain:
                        self.causal_chains.append(causal_chain)
    
    async def _five_why_analysis(
        self,
        issue_type: str,
        issue_description: str,
        trace: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        5Why因果分析
        
        Args:
            issue_type: 问题类型
            issue_description: 问题描述
            trace: 工作流追踪
            
        Returns:
            因果链分析结果
        """
        why_chain = []
        
        # Level 1: 表面问题
        why_chain.append({
            "level": 1,
            "question": f"为什么出现{issue_type}问题？",
            "answer": issue_description,
            "evidence": self._extract_evidence(trace, issue_type)
        })
        
        # Level 2-5: 深入分析
        if issue_type == "performance":
            # 性能问题分析
            bottlenecks = trace.get("bottlenecks", [])
            if bottlenecks:
                slowest_step = max(bottlenecks, key=lambda x: x.get("duration", 0))
                why_chain.append({
                    "level": 2,
                    "question": "为什么响应时间过长？",
                    "answer": f"步骤 {slowest_step.get('step_name')} 耗时 {slowest_step.get('duration', 0):.2f}秒",
                    "evidence": slowest_step
                })
                
                why_chain.append({
                    "level": 3,
                    "question": f"为什么步骤 {slowest_step.get('step_name')} 耗时过长？",
                    "answer": self._infer_bottleneck_reason(slowest_step),
                    "evidence": slowest_step.get("data", {})
                })
                
                why_chain.append({
                    "level": 4,
                    "question": "为什么会出现这个根本原因？",
                    "answer": self._infer_root_cause(slowest_step),
                    "evidence": trace.get("steps", [])
                })
                
                why_chain.append({
                    "level": 5,
                    "question": "为什么系统设计允许这个问题存在？",
                    "answer": "缺少性能监控和优化机制",
                    "evidence": {"suggestion": "需要建立持续优化流程"}
                })
        
        elif issue_type == "error":
            # 错误问题分析
            errors = trace.get("errors", [])
            if errors:
                first_error = errors[0]
                why_chain.append({
                    "level": 2,
                    "question": "为什么发生错误？",
                    "answer": first_error.get("message", "未知错误"),
                    "evidence": first_error
                })
                
                why_chain.append({
                    "level": 3,
                    "question": "为什么会出现这个错误？",
                    "answer": self._infer_error_reason(first_error),
                    "evidence": first_error.get("context", {})
                })
                
                why_chain.append({
                    "level": 4,
                    "question": "为什么错误处理机制没有生效？",
                    "answer": "错误处理逻辑不完善或缺少预防措施",
                    "evidence": {"suggestion": "需要增强错误处理"}
                })
                
                why_chain.append({
                    "level": 5,
                    "question": "为什么系统设计允许这个错误发生？",
                    "answer": "缺少完善的错误预防和恢复机制",
                    "evidence": {"suggestion": "需要建立错误预防体系"}
                })
        
        if why_chain:
            causal_chain = {
                "workflow_id": trace.get("workflow_id"),
                "issue_type": issue_type,
                "issue_description": issue_description,
                "why_chain": why_chain,
                "root_cause": why_chain[-1].get("answer") if why_chain else None,
                "timestamp": datetime.now().isoformat()
            }
            return causal_chain
        
        return None
    
    def _extract_evidence(self, trace: Dict[str, Any], issue_type: str) -> Dict[str, Any]:
        """提取证据"""
        if issue_type == "performance":
            return {
                "total_duration": trace.get("total_duration", 0),
                "bottlenecks": trace.get("bottlenecks", []),
                "step_count": len(trace.get("steps", []))
            }
        else:
            return {
                "errors": trace.get("errors", []),
                "failed_steps": [s for s in trace.get("steps", []) if not s.get("success", True)]
            }
    
    def _infer_bottleneck_reason(self, bottleneck: Dict[str, Any]) -> str:
        """推断瓶颈原因"""
        step_name = bottleneck.get("step_name", "")
        step_type = bottleneck.get("step_type", "")
        
        if "rag" in step_type.lower():
            return "RAG检索查询复杂或知识库数据量大"
        elif "execution" in step_type.lower():
            return "模块执行逻辑复杂或资源不足"
        elif "routing" in step_type.lower():
            return "专家路由算法计算量大"
        else:
            return "步骤处理逻辑需要优化"
    
    def _infer_root_cause(self, bottleneck: Dict[str, Any]) -> str:
        """推断根本原因"""
        step_data = bottleneck.get("data", {})
        
        if "top_k" in step_data:
            return "检索参数设置不合理，检索范围过大"
        elif "cache" not in step_data:
            return "缺少缓存机制，重复计算"
        else:
            return "算法或数据结构需要优化"
    
    def _infer_error_reason(self, error: Dict[str, Any]) -> str:
        """推断错误原因"""
        error_type = error.get("type", "")
        error_message = error.get("message", "")
        
        if "timeout" in error_message.lower():
            return "请求超时，可能是网络延迟或服务响应慢"
        elif "connection" in error_message.lower():
            return "连接失败，可能是服务不可用或网络问题"
        elif "permission" in error_message.lower():
            return "权限不足，可能是配置错误"
        else:
            return "未知错误，需要查看详细日志"
    
    async def generate_optimization_strategy(
        self,
        causal_chain: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成策略优化建议
        
        Args:
            causal_chain: 因果链分析结果
            
        Returns:
            优化策略
        """
        root_cause = causal_chain.get("root_cause", "")
        issue_type = causal_chain.get("issue_type", "")
        
        strategies = []
        
        if issue_type == "performance":
            if "缓存" in root_cause or "cache" in root_cause.lower():
                strategies.append({
                    "type": "caching",
                    "priority": "high",
                    "action": "启用结果缓存机制",
                    "expected_improvement": "响应时间减少30-50%",
                    "implementation": "在RAG检索和模块执行结果中添加缓存层"
                })
            
            if "检索" in root_cause or "retrieval" in root_cause.lower():
                strategies.append({
                    "type": "retrieval_optimization",
                    "priority": "high",
                    "action": "优化RAG检索策略",
                    "expected_improvement": "检索时间减少20-40%",
                    "implementation": "调整top_k参数，使用混合检索，启用结果重排序"
                })
            
            if "算法" in root_cause or "algorithm" in root_cause.lower():
                strategies.append({
                    "type": "algorithm_optimization",
                    "priority": "medium",
                    "action": "优化算法复杂度",
                    "expected_improvement": "计算时间减少10-30%",
                    "implementation": "使用更高效的算法或数据结构"
                })
            
            strategies.append({
                "type": "async_processing",
                "priority": "medium",
                "action": "使用异步并行处理",
                "expected_improvement": "总体响应时间减少15-25%",
                "implementation": "将独立步骤改为异步并行执行"
            })
        
        elif issue_type == "error":
            strategies.append({
                "type": "error_handling",
                "priority": "high",
                "action": "增强错误处理机制",
                "expected_improvement": "错误恢复率提升50%",
                "implementation": "添加重试逻辑、降级方案、详细错误日志"
            })
            
            strategies.append({
                "type": "prevention",
                "priority": "high",
                "action": "建立错误预防机制",
                "expected_improvement": "错误发生率降低30%",
                "implementation": "输入验证、资源检查、超时控制"
            })
        
        if strategies:
            strategy = {
                "workflow_id": causal_chain.get("workflow_id"),
                "causal_chain_id": len(self.causal_chains),
                "strategies": strategies,
                "has_high_priority": any(s.get("priority") == "high" for s in strategies),
                "timestamp": datetime.now().isoformat()
            }
            self.optimization_strategies.append(strategy)
            return strategy
        
        return {}
    
    async def generate_interaction_suggestions(
        self,
        workflow_trace: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成交互建议
        
        Args:
            workflow_trace: 工作流追踪
            user_context: 用户上下文
            
        Returns:
            交互建议列表
        """
        suggestions = []
        
        # 基于性能建议
        if workflow_trace.get("total_duration", 0) > 2.0:
            suggestions.append({
                "type": "performance_hint",
                "severity": "info",
                "message": "本次响应时间较长，系统正在优化中",
                "action": "可以尝试简化查询或稍后重试",
                "auto_apply": False
            })
        
        # 基于错误建议
        errors = workflow_trace.get("errors", [])
        if errors:
            suggestions.append({
                "type": "error_recovery",
                "severity": "warning",
                "message": "检测到错误，系统已尝试自动恢复",
                "action": "如问题持续，请检查输入或联系支持",
                "auto_apply": True
            })
        
        # 基于用户行为建议
        if user_context:
            query_complexity = self._assess_query_complexity(
                workflow_trace.get("steps", [])
            )
            if query_complexity == "high":
                suggestions.append({
                    "type": "query_optimization",
                    "severity": "info",
                    "message": "检测到复杂查询，建议拆分为多个简单查询",
                    "action": "系统可以自动拆分查询以提高响应速度",
                    "auto_apply": False
                })
        
        # 基于历史模式建议
        similar_traces = self._find_similar_traces(workflow_trace)
        if similar_traces:
            avg_duration = sum(t.get("total_duration", 0) for t in similar_traces) / len(similar_traces)
            if avg_duration < workflow_trace.get("total_duration", 0) * 0.8:
                suggestions.append({
                    "type": "pattern_suggestion",
                    "severity": "info",
                    "message": "类似查询通常更快，系统已识别优化模式",
                    "action": "建议使用更具体的查询关键词",
                    "auto_apply": False
                })
        
        if suggestions:
            suggestion_record = {
                "workflow_id": workflow_trace.get("workflow_id"),
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
            self.interaction_suggestions.append(suggestion_record)
        
        return suggestions
    
    def _assess_query_complexity(self, steps: List[Dict[str, Any]]) -> str:
        """评估查询复杂度"""
        step_count = len(steps)
        total_duration = sum(s.get("duration", 0) for s in steps)
        
        if step_count > 5 or total_duration > 3.0:
            return "high"
        elif step_count > 3 or total_duration > 1.5:
            return "medium"
        else:
            return "low"
    
    def _find_similar_traces(
        self,
        current_trace: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """查找相似的工作流追踪"""
        current_steps = current_trace.get("steps", [])
        current_step_types = [s.get("step_type") for s in current_steps]
        
        similar = []
        for trace in self.workflow_traces[-100:]:  # 最近100条
            if trace.get("workflow_id") == current_trace.get("workflow_id"):
                continue
            
            trace_step_types = [s.get("step_type") for s in trace.get("steps", [])]
            similarity = len(set(current_step_types) & set(trace_step_types)) / max(
                len(set(current_step_types)), 1
            )
            
            if similarity > 0.5:
                similar.append(trace)
        
        return similar[:limit]
    
    def get_causal_analysis_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取因果分析报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            分析报告
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()
        
        # 筛选时间范围内的因果链
        filtered_chains = [
            c for c in self.causal_chains
            if start_date <= c.get("timestamp", "") <= end_date
        ]
        
        # 统计问题类型
        issue_types = defaultdict(int)
        root_causes = defaultdict(int)
        
        for chain in filtered_chains:
            issue_types[chain.get("issue_type", "unknown")] += 1
            root_cause = chain.get("root_cause", "")
            if root_cause:
                root_causes[root_cause] += 1
        
        # 统计优化策略
        filtered_strategies = [
            s for s in self.optimization_strategies
            if start_date <= s.get("timestamp", "") <= end_date
        ]
        
        strategy_types = defaultdict(int)
        for strategy in filtered_strategies:
            for s in strategy.get("strategies", []):
                strategy_types[s.get("type", "unknown")] += 1
        
        return {
            "period": {"start": start_date, "end": end_date},
            "total_causal_chains": len(filtered_chains),
            "issue_type_distribution": dict(issue_types),
            "top_root_causes": dict(sorted(
                root_causes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            "optimization_strategies": {
                "total": len(filtered_strategies),
                "type_distribution": dict(strategy_types)
            },
            "recent_chains": filtered_chains[-10:],
            "recent_strategies": filtered_strategies[-10:]
        }
    
    def get_interaction_suggestions_summary(
        self,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取交互建议摘要
        
        Args:
            limit: 返回数量限制
            
        Returns:
            建议摘要
        """
        recent_suggestions = self.interaction_suggestions[-limit:]
        
        suggestion_types = defaultdict(int)
        for record in recent_suggestions:
            for suggestion in record.get("suggestions", []):
                suggestion_types[suggestion.get("type", "unknown")] += 1
        
        return {
            "total_suggestions": len(recent_suggestions),
            "suggestion_type_distribution": dict(suggestion_types),
            "recent_suggestions": recent_suggestions
        }

