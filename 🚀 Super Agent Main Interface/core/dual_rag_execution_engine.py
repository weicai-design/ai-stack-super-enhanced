#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双RAG执行引擎
P1-203: 实现"双RAG + 专家路由 + 模块执行 + 再检索"模型

流程：
1. 第一次RAG检索：基于用户查询进行初始检索
2. 专家路由：基于第一次RAG结果进行智能路由
3. 模块执行：执行对应模块的功能
4. 第二次RAG检索：基于执行结果进行增强检索
5. 结果融合：融合两次检索和执行结果
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
import time

logger = logging.getLogger(__name__)


@dataclass
class DualRAGExecutionResult:
    """双RAG执行结果"""
    query: str
    first_rag_results: List[Dict[str, Any]]
    routing_result: Dict[str, Any]
    module_execution_result: Dict[str, Any]
    second_rag_results: List[Dict[str, Any]]
    final_result: Dict[str, Any]
    execution_time: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "first_rag_results": self.first_rag_results,
            "routing_result": self.routing_result,
            "module_execution_result": self.module_execution_result,
            "second_rag_results": self.second_rag_results,
            "final_result": self.final_result,
            "execution_time": self.execution_time,
            "performance_metrics": self.performance_metrics,
            "timestamp": self.timestamp,
        }


class DualRAGExecutionEngine:
    """
    双RAG执行引擎
    
    实现完整的"双RAG + 专家路由 + 模块执行 + 再检索"流程
    """
    
    def __init__(
        self,
        rag_service: Any = None,
        expert_router: Any = None,
        module_executors: Optional[Dict[str, Callable]] = None,
    ):
        """
        初始化双RAG执行引擎
        
        Args:
            rag_service: RAG服务实例
            expert_router: 专家路由器实例
            module_executors: 模块执行器字典 {module_name: executor_function}
        """
        self.rag_service = rag_service
        self.expert_router = expert_router
        self.module_executors = module_executors or {}
        
        # 性能指标
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "avg_first_rag_time": 0.0,
            "avg_routing_time": 0.0,
            "avg_module_execution_time": 0.0,
            "avg_second_rag_time": 0.0,
            "by_module": {},
        }
        
        # 执行历史
        self.execution_history: List[DualRAGExecutionResult] = []
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        top_k_first: int = 5,
        top_k_second: int = 3,
        enable_second_rag: bool = True,
    ) -> DualRAGExecutionResult:
        """
        执行完整的双RAG流程
        
        Args:
            query: 用户查询
            context: 上下文信息
            top_k_first: 第一次RAG检索返回数量
            top_k_second: 第二次RAG检索返回数量
            enable_second_rag: 是否启用第二次RAG检索
            
        Returns:
            执行结果
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # 1. 第一次RAG检索
            first_rag_start = time.time()
            first_rag_results = await self._first_rag_retrieval(query, top_k_first)
            first_rag_time = time.time() - first_rag_start
            
            # 2. 专家路由
            routing_start = time.time()
            routing_result = await self._expert_routing(query, first_rag_results)
            routing_time = time.time() - routing_start
            
            # 3. 模块执行
            module_start = time.time()
            module_execution_result = await self._module_execution(
                query,
                routing_result,
                first_rag_results,
                context,
            )
            module_time = time.time() - module_start
            
            # 4. 第二次RAG检索（基于执行结果）
            second_rag_results = []
            second_rag_time = 0.0
            if enable_second_rag and module_execution_result.get("success"):
                second_rag_start = time.time()
                second_rag_results = await self._second_rag_retrieval(
                    query,
                    module_execution_result,
                    first_rag_results,
                    top_k_second,
                )
                second_rag_time = time.time() - second_rag_start
            
            # 5. 结果融合
            final_result = self._merge_results(
                query,
                first_rag_results,
                routing_result,
                module_execution_result,
                second_rag_results,
            )
            
            execution_time = time.time() - start_time
            
            # 构建结果
            result = DualRAGExecutionResult(
                query=query,
                first_rag_results=first_rag_results,
                routing_result=routing_result,
                module_execution_result=module_execution_result,
                second_rag_results=second_rag_results,
                final_result=final_result,
                execution_time=execution_time,
                performance_metrics={
                    "first_rag_time": first_rag_time,
                    "routing_time": routing_time,
                    "module_execution_time": module_time,
                    "second_rag_time": second_rag_time,
                    "total_time": execution_time,
                },
            )
            
            # 更新性能指标
            self._update_performance_metrics(result)
            
            # 保存执行历史
            self.execution_history.append(result)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
            
            logger.info(
                f"双RAG执行完成: query='{query[:50]}...', "
                f"module={routing_result.get('module')}, "
                f"time={execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"双RAG执行失败: {e}", exc_info=True)
            self.performance_metrics["failed_executions"] += 1
            
            # 返回错误结果
            return DualRAGExecutionResult(
                query=query,
                first_rag_results=[],
                routing_result={"error": str(e)},
                module_execution_result={"success": False, "error": str(e)},
                second_rag_results=[],
                final_result={"success": False, "error": str(e)},
                execution_time=time.time() - start_time,
            )
    
    async def _first_rag_retrieval(
        self,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """第一次RAG检索"""
        if not self.rag_service:
            logger.warning("RAG服务未初始化，返回空结果")
            return []
        
        try:
            # 调用RAG服务进行检索
            if hasattr(self.rag_service, "search"):
                results = await self.rag_service.search(query, top_k=top_k)
            elif hasattr(self.rag_service, "retrieve"):
                results = await self.rag_service.retrieve(query, top_k=top_k)
            else:
                logger.warning("RAG服务不支持search或retrieve方法")
                return []
            
            # 标准化结果格式
            standardized_results = []
            for result in results:
                if isinstance(result, dict):
                    standardized_results.append({
                        "content": result.get("content", result.get("text", "")),
                        "score": result.get("score", 0.0),
                        "metadata": result.get("metadata", {}),
                        "source": result.get("source", "rag"),
                    })
                else:
                    standardized_results.append({
                        "content": str(result),
                        "score": 0.0,
                        "metadata": {},
                        "source": "rag",
                    })
            
            return standardized_results[:top_k]
            
        except Exception as e:
            logger.error(f"第一次RAG检索失败: {e}")
            return []
    
    async def _expert_routing(
        self,
        query: str,
        first_rag_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """专家路由"""
        if not self.expert_router:
            logger.warning("专家路由器未初始化，使用默认路由")
            return {
                "expert": "default",
                "module": "general",
                "confidence": 0.5,
            }
        
        try:
            # 构建RAG结果摘要用于路由
            rag_summary = {
                "results": first_rag_results,
                "top_content": " ".join([r.get("content", "")[:100] for r in first_rag_results[:3]]),
            }
            
            # 调用专家路由器
            if hasattr(self.expert_router, "route"):
                routing_result = await self.expert_router.route(
                    user_input=query,
                    rag_result=rag_summary,
                )
                
                # 转换为字典格式
                if hasattr(routing_result, "to_dict"):
                    return routing_result.to_dict()
                elif isinstance(routing_result, dict):
                    return routing_result
                else:
                    return {
                        "expert": str(routing_result),
                        "module": "unknown",
                        "confidence": 0.5,
                    }
            else:
                logger.warning("专家路由器不支持route方法")
                return {
                    "expert": "default",
                    "module": "general",
                    "confidence": 0.5,
                }
                
        except Exception as e:
            logger.error(f"专家路由失败: {e}")
            return {
                "expert": "default",
                "module": "general",
                "confidence": 0.5,
                "error": str(e),
            }
    
    async def _module_execution(
        self,
        query: str,
        routing_result: Dict[str, Any],
        first_rag_results: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """模块执行"""
        module_name = routing_result.get("module", "general")
        expert = routing_result.get("expert", "default")
        
        # 获取模块执行器
        executor = self.module_executors.get(module_name)
        
        if not executor:
            logger.warning(f"模块 {module_name} 的执行器未注册")
            return {
                "success": False,
                "error": f"模块 {module_name} 的执行器未注册",
                "module": module_name,
            }
        
        try:
            # 执行模块功能
            execution_context = {
                "query": query,
                "routing_result": routing_result,
                "first_rag_results": first_rag_results,
                "context": context,
            }
            
            if asyncio.iscoroutinefunction(executor):
                result = await executor(execution_context)
            else:
                result = executor(execution_context)
            
            # 标准化结果格式
            if isinstance(result, dict):
                result.setdefault("success", True)
                result.setdefault("module", module_name)
                result.setdefault("expert", expert)
                return result
            else:
                return {
                    "success": True,
                    "module": module_name,
                    "expert": expert,
                    "result": result,
                }
                
        except Exception as e:
            logger.error(f"模块执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "module": module_name,
                "expert": expert,
            }
    
    async def _second_rag_retrieval(
        self,
        query: str,
        module_execution_result: Dict[str, Any],
        first_rag_results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """第二次RAG检索（基于执行结果）"""
        if not self.rag_service:
            return []
        
        try:
            # 基于执行结果构建增强查询
            enhanced_query = self._build_enhanced_query(
                query,
                module_execution_result,
                first_rag_results,
            )
            
            # 执行第二次检索
            if hasattr(self.rag_service, "search"):
                results = await self.rag_service.search(enhanced_query, top_k=top_k)
            elif hasattr(self.rag_service, "retrieve"):
                results = await self.rag_service.retrieve(enhanced_query, top_k=top_k)
            else:
                return []
            
            # 标准化结果格式
            standardized_results = []
            for result in results:
                if isinstance(result, dict):
                    standardized_results.append({
                        "content": result.get("content", result.get("text", "")),
                        "score": result.get("score", 0.0),
                        "metadata": result.get("metadata", {}),
                        "source": "second_rag",
                    })
                else:
                    standardized_results.append({
                        "content": str(result),
                        "score": 0.0,
                        "metadata": {},
                        "source": "second_rag",
                    })
            
            return standardized_results[:top_k]
            
        except Exception as e:
            logger.error(f"第二次RAG检索失败: {e}")
            return []
    
    def _build_enhanced_query(
        self,
        original_query: str,
        module_execution_result: Dict[str, Any],
        first_rag_results: List[Dict[str, Any]],
    ) -> str:
        """构建增强查询"""
        # 提取执行结果的关键信息
        execution_summary = ""
        if module_execution_result.get("success"):
            result_data = module_execution_result.get("result", {})
            if isinstance(result_data, dict):
                # 提取关键字段
                key_fields = ["summary", "insights", "analysis", "recommendations"]
                for field in key_fields:
                    if field in result_data:
                        execution_summary += f" {result_data[field]}"
            else:
                execution_summary = str(result_data)[:200]
        
        # 构建增强查询
        enhanced_query = f"{original_query}"
        if execution_summary:
            enhanced_query += f" {execution_summary}"
        
        # 添加第一次RAG结果的摘要
        if first_rag_results:
            rag_summary = " ".join([r.get("content", "")[:50] for r in first_rag_results[:2]])
            enhanced_query += f" {rag_summary}"
        
        return enhanced_query[:500]  # 限制长度
    
    def _merge_results(
        self,
        query: str,
        first_rag_results: List[Dict[str, Any]],
        routing_result: Dict[str, Any],
        module_execution_result: Dict[str, Any],
        second_rag_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """融合结果"""
        merged = {
            "query": query,
            "success": module_execution_result.get("success", False),
            "module": routing_result.get("module", "unknown"),
            "expert": routing_result.get("expert", "default"),
            "confidence": routing_result.get("confidence", 0.5),
            "execution_result": module_execution_result,
            "knowledge_base": {
                "first_rag": first_rag_results,
                "second_rag": second_rag_results,
                "total_knowledge_items": len(first_rag_results) + len(second_rag_results),
            },
            "enhanced_answer": self._build_enhanced_answer(
                query,
                module_execution_result,
                first_rag_results,
                second_rag_results,
            ),
        }
        
        return merged
    
    def _build_enhanced_answer(
        self,
        query: str,
        module_execution_result: Dict[str, Any],
        first_rag_results: List[Dict[str, Any]],
        second_rag_results: List[Dict[str, Any]],
    ) -> str:
        """构建增强答案"""
        answer_parts = []
        
        # 添加执行结果
        if module_execution_result.get("success"):
            result_data = module_execution_result.get("result", {})
            if isinstance(result_data, dict):
                answer = result_data.get("answer") or result_data.get("summary") or result_data.get("content")
                if answer:
                    answer_parts.append(str(answer))
            else:
                answer_parts.append(str(result_data))
        
        # 添加第二次RAG结果（更相关）
        if second_rag_results:
            rag_content = " ".join([r.get("content", "")[:100] for r in second_rag_results[:2]])
            if rag_content:
                answer_parts.append(f"\n\n相关参考：{rag_content}")
        
        # 如果没有执行结果，使用第一次RAG结果
        if not answer_parts and first_rag_results:
            rag_content = " ".join([r.get("content", "")[:100] for r in first_rag_results[:2]])
            if rag_content:
                answer_parts.append(rag_content)
        
        return "\n".join(answer_parts) if answer_parts else "暂无结果"
    
    def _update_performance_metrics(self, result: DualRAGExecutionResult):
        """更新性能指标"""
        self.performance_metrics["total_executions"] += 1
        
        if result.final_result.get("success"):
            self.performance_metrics["successful_executions"] += 1
        else:
            self.performance_metrics["failed_executions"] += 1
        
        # 更新平均时间
        metrics = result.performance_metrics
        total = self.performance_metrics["total_executions"]
        
        # 计算移动平均
        alpha = 0.1  # 平滑因子
        self.performance_metrics["avg_execution_time"] = (
            (1 - alpha) * self.performance_metrics["avg_execution_time"] +
            alpha * result.execution_time
        )
        self.performance_metrics["avg_first_rag_time"] = (
            (1 - alpha) * self.performance_metrics["avg_first_rag_time"] +
            alpha * metrics.get("first_rag_time", 0)
        )
        self.performance_metrics["avg_routing_time"] = (
            (1 - alpha) * self.performance_metrics["avg_routing_time"] +
            alpha * metrics.get("routing_time", 0)
        )
        self.performance_metrics["avg_module_execution_time"] = (
            (1 - alpha) * self.performance_metrics["avg_module_execution_time"] +
            alpha * metrics.get("module_execution_time", 0)
        )
        self.performance_metrics["avg_second_rag_time"] = (
            (1 - alpha) * self.performance_metrics["avg_second_rag_time"] +
            alpha * metrics.get("second_rag_time", 0)
        )
        
        # 按模块统计
        module = result.routing_result.get("module", "unknown")
        if module not in self.performance_metrics["by_module"]:
            self.performance_metrics["by_module"][module] = {
                "count": 0,
                "success_count": 0,
                "avg_time": 0.0,
            }
        
        module_metrics = self.performance_metrics["by_module"][module]
        module_metrics["count"] += 1
        if result.final_result.get("success"):
            module_metrics["success_count"] += 1
        module_metrics["avg_time"] = (
            (1 - alpha) * module_metrics["avg_time"] +
            alpha * result.execution_time
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            **self.performance_metrics,
            "success_rate": (
                self.performance_metrics["successful_executions"] /
                max(self.performance_metrics["total_executions"], 1)
            ),
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return [r.to_dict() for r in self.execution_history[-limit:]]

