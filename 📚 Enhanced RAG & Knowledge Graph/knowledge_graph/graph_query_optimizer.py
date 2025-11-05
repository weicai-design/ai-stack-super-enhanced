"""
知识图谱查询优化引擎
功能：优化图谱查询性能，支持复杂查询的智能优化和缓存管理
"""

import asyncio
import hashlib
import json
import logging
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import networkx as nx


@dataclass
class QueryPlan:
    """查询计划"""

    query_id: str
    original_query: str
    optimized_steps: List[Dict[str, Any]]
    estimated_cost: float
    actual_cost: float = 0.0
    execution_time: float = 0.0
    result_count: int = 0


@dataclass
class CacheEntry:
    """缓存条目"""

    query_hash: str
    results: Any
    timestamp: datetime
    access_count: int = 0
    size: int = 0


class GraphQueryOptimizer:
    """知识图谱查询优化引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 查询缓存
        self.query_cache: Dict[str, CacheEntry] = {}
        self.max_cache_size = config.get("max_cache_size", 1000)
        self.cache_ttl = timedelta(minutes=config.get("cache_ttl_minutes", 60))

        # 查询计划历史
        self.query_plans: Dict[str, QueryPlan] = {}
        self.plan_history = deque(maxlen=config.get("max_plan_history", 500))

        # 性能统计
        self.performance_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_execution_time": 0.0,
            "query_types": defaultdict(int),
        }

        # 优化规则
        self.optimization_rules = self._load_optimization_rules()

        # 成本模型
        self.cost_model = self._initialize_cost_model()

        self.logger.info("知识图谱查询优化引擎初始化完成")

    def _load_optimization_rules(self) -> Dict[str, Any]:
        """加载优化规则"""
        return {
            "predicate_pushdown": {"enabled": True, "priority": 1},
            "join_reordering": {"enabled": True, "priority": 2},
            "index_usage": {"enabled": True, "priority": 3},
            "subquery_optimization": {"enabled": True, "priority": 4},
            "cache_utilization": {"enabled": True, "priority": 5},
        }

    def _initialize_cost_model(self) -> Dict[str, float]:
        """初始化成本模型"""
        return {
            "node_scan": 1.0,
            "edge_traversal": 2.0,
            "filter_application": 0.5,
            "join_operation": 3.0,
            "aggregation": 2.0,
            "sort_operation": 1.5,
        }

    async def initialize(self):
        """异步初始化"""
        self.logger.info("开始异步初始化查询优化引擎")
        await self._preload_optimization_data()
        self.logger.info("查询优化引擎异步初始化完成")

    async def _preload_optimization_data(self):
        """预加载优化数据"""
        # 预加载常用查询模式
        await asyncio.sleep(0.1)

    async def optimize_query(
        self,
        query: Union[str, Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any] = None,
    ) -> QueryPlan:
        """
        优化查询并生成执行计划

        Args:
            query: 查询语句或查询对象
            graph: 知识图谱实例
            context: 查询上下文

        Returns:
            优化后的查询计划
        """
        self.performance_stats["total_queries"] += 1

        # 生成查询ID
        query_id = self._generate_query_id(query, context)

        # 检查缓存
        cached_result = await self._check_query_cache(query, context)
        if cached_result:
            self.performance_stats["cache_hits"] += 1
            self.logger.info(f"查询缓存命中: {query_id}")
            return cached_result

        self.performance_stats["cache_misses"] += 1

        # 解析查询
        parsed_query = await self._parse_query(query, context)

        # 生成初始执行计划
        initial_plan = await self._generate_initial_plan(parsed_query, graph)

        # 应用优化规则
        optimized_plan = await self._apply_optimizations(initial_plan, graph, context)

        # 估算成本
        estimated_cost = await self._estimate_cost(optimized_plan, graph)
        optimized_plan.estimated_cost = estimated_cost

        # 存储计划
        self.query_plans[query_id] = optimized_plan

        self.logger.info(f"查询优化完成: {query_id}, 估算成本: {estimated_cost}")
        return optimized_plan

    def _generate_query_id(self, query: Any, context: Dict[str, Any] = None) -> str:
        """生成查询ID"""
        query_str = (
            json.dumps(query, sort_keys=True) if isinstance(query, dict) else str(query)
        )
        context_str = json.dumps(context, sort_keys=True) if context else ""

        combined = f"{query_str}|{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    async def _check_query_cache(
        self, query: Any, context: Dict[str, Any] = None
    ) -> Optional[QueryPlan]:
        """检查查询缓存"""
        query_hash = self._generate_query_id(query, context)

        if query_hash in self.query_cache:
            entry = self.query_cache[query_hash]

            # 检查TTL
            if datetime.now() - entry.timestamp < self.cache_ttl:
                entry.access_count += 1
                return entry.results

        return None

    async def _parse_query(
        self, query: Union[str, Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析查询"""
        if isinstance(query, dict):
            # 已经是结构化查询
            return query

        # 解析文本查询
        return await self._parse_text_query(query, context)

    async def _parse_text_query(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析文本查询"""
        parsed = {
            "type": "unknown",
            "filters": [],
            "projections": [],
            "operations": [],
            "limit": None,
            "order_by": [],
        }

        # 简单的关键词匹配（实际应用中需要更复杂的解析）
        query_lower = query.lower()

        # 检测查询类型
        if "连接" in query_lower or "connected" in query_lower:
            parsed["type"] = "connectivity"
        elif "路径" in query_lower or "path" in query_lower:
            parsed["type"] = "path_finding"
        elif "邻居" in query_lower or "neighbor" in query_lower:
            parsed["type"] = "neighborhood"
        elif "搜索" in query_lower or "search" in query_lower:
            parsed["type"] = "search"
        else:
            parsed["type"] = "general"

        # 提取过滤器
        filters = self._extract_filters(query)
        parsed["filters"] = filters

        # 提取限制
        limit_match = re.search(r"limit\s+(\d+)", query_lower)
        if limit_match:
            parsed["limit"] = int(limit_match.group(1))

        return parsed

    def _extract_filters(self, query: str) -> List[Dict[str, Any]]:
        """从查询中提取过滤器"""
        filters = []

        # 简单的模式匹配（实际应用中需要更复杂的NLP）
        patterns = [
            (r"类型[：:]\s*(\w+)", "type"),
            (r"名称[：:]\s*(\w+)", "name"),
            (r"属性[：:]\s*(\w+)\s*[=:]\s*(\w+)", "attribute"),
        ]

        for pattern, filter_type in patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                if filter_type == "attribute":
                    filters.append(
                        {
                            "type": "attribute",
                            "key": match.group(1),
                            "value": match.group(2),
                            "operator": "equals",
                        }
                    )
                else:
                    filters.append(
                        {
                            "type": filter_type,
                            "value": match.group(1),
                            "operator": "equals",
                        }
                    )

        return filters

    async def _generate_initial_plan(
        self, parsed_query: Dict[str, Any], graph: nx.MultiDiGraph
    ) -> QueryPlan:
        """生成初始执行计划"""
        query_id = self._generate_query_id(parsed_query)
        steps = []

        # 根据查询类型生成基本步骤
        if parsed_query["type"] == "connectivity":
            steps = await self._plan_connectivity_query(parsed_query, graph)
        elif parsed_query["type"] == "path_finding":
            steps = await self._plan_path_query(parsed_query, graph)
        elif parsed_query["type"] == "neighborhood":
            steps = await self._plan_neighborhood_query(parsed_query, graph)
        else:
            steps = await self._plan_general_query(parsed_query, graph)

        return QueryPlan(
            query_id=query_id,
            original_query=str(parsed_query),
            optimized_steps=steps,
            estimated_cost=0.0,
        )

    async def _plan_connectivity_query(
        self, parsed_query: Dict[str, Any], graph: nx.MultiDiGraph
    ) -> List[Dict[str, Any]]:
        """规划连通性查询"""
        steps = [
            {
                "type": "node_scan",
                "description": "扫描相关节点",
                "cost": self.cost_model["node_scan"],
            },
            {
                "type": "connectivity_check",
                "description": "检查节点连通性",
                "cost": self.cost_model["edge_traversal"] * 2,
            },
            {
                "type": "result_assembly",
                "description": "组装结果",
                "cost": self.cost_model["aggregation"],
            },
        ]

        # 添加过滤步骤
        if parsed_query["filters"]:
            steps.insert(
                1,
                {
                    "type": "filter_application",
                    "description": "应用查询过滤器",
                    "cost": self.cost_model["filter_application"]
                    * len(parsed_query["filters"]),
                },
            )

        return steps

    async def _plan_path_query(
        self, parsed_query: Dict[str, Any], graph: nx.MultiDiGraph
    ) -> List[Dict[str, Any]]:
        """规划路径查询"""
        steps = [
            {
                "type": "path_finding_init",
                "description": "初始化路径查找",
                "cost": self.cost_model["node_scan"],
            },
            {
                "type": "graph_traversal",
                "description": "图遍历搜索路径",
                "cost": self.cost_model["edge_traversal"] * 10,  # 估计值
            },
            {
                "type": "path_optimization",
                "description": "路径优化和排序",
                "cost": self.cost_model["sort_operation"],
            },
        ]

        return steps

    async def _plan_neighborhood_query(
        self, parsed_query: Dict[str, Any], graph: nx.MultiDiGraph
    ) -> List[Dict[str, Any]]:
        """规划邻居查询"""
        steps = [
            {
                "type": "target_node_lookup",
                "description": "查找目标节点",
                "cost": self.cost_model["node_scan"],
            },
            {
                "type": "neighbor_expansion",
                "description": "扩展邻居节点",
                "cost": self.cost_model["edge_traversal"] * 5,  # 估计值
            },
            {
                "type": "neighbor_filtering",
                "description": "过滤邻居节点",
                "cost": self.cost_model["filter_application"],
            },
        ]

        return steps

    async def _plan_general_query(
        self, parsed_query: Dict[str, Any], graph: nx.MultiDiGraph
    ) -> List[Dict[str, Any]]:
        """规划通用查询"""
        steps = [
            {
                "type": "full_graph_scan",
                "description": "全图扫描",
                "cost": self.cost_model["node_scan"] * graph.number_of_nodes(),
            },
            {
                "type": "filter_application",
                "description": "应用所有过滤器",
                "cost": self.cost_model["filter_application"]
                * len(parsed_query["filters"]),
            },
            {
                "type": "result_processing",
                "description": "结果处理",
                "cost": self.cost_model["aggregation"],
            },
        ]

        return steps

    async def _apply_optimizations(
        self, plan: QueryPlan, graph: nx.MultiDiGraph, context: Dict[str, Any]
    ) -> QueryPlan:
        """应用优化规则"""
        optimized_steps = plan.optimized_steps.copy()

        # 按优先级应用优化规则
        enabled_rules = [
            (rule_name, rule_config)
            for rule_name, rule_config in self.optimization_rules.items()
            if rule_config["enabled"]
        ]
        enabled_rules.sort(key=lambda x: x[1]["priority"])

        for rule_name, rule_config in enabled_rules:
            optimization_method = getattr(self, f"_apply_{rule_name}", None)
            if optimization_method:
                try:
                    optimized_steps = await optimization_method(
                        optimized_steps, graph, context
                    )
                    self.logger.debug(f"应用优化规则: {rule_name}")
                except Exception as e:
                    self.logger.warning(f"应用优化规则 {rule_name} 失败: {str(e)}")

        plan.optimized_steps = optimized_steps
        return plan

    async def _apply_predicate_pushdown(
        self,
        steps: List[Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用谓词下推优化"""
        # 查找过滤步骤
        filter_steps = [
            i for i, step in enumerate(steps) if step["type"] == "filter_application"
        ]

        if not filter_steps:
            return steps

        # 将过滤步骤尽可能提前
        filter_index = filter_steps[0]
        if filter_index > 0:
            # 尝试将过滤步骤提前
            steps.insert(0, steps.pop(filter_index))

        return steps

    async def _apply_join_reordering(
        self,
        steps: List[Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用连接重排序优化"""
        # 简单的基于成本的重新排序
        join_steps = [i for i, step in enumerate(steps) if "join" in step["type"]]

        if len(join_steps) >= 2:
            # 根据估计成本重新排序连接操作
            join_costs = [(i, steps[i]["cost"]) for i in join_steps]
            join_costs.sort(key=lambda x: x[1])  # 按成本升序排序

            # 重新排列步骤
            new_steps = []
            join_indices = [i for i, _ in join_costs]

            for i, step in enumerate(steps):
                if i in join_steps:
                    continue
                new_steps.append(step)

            # 插入排序后的连接步骤
            for join_index in join_indices:
                new_steps.insert(join_index, steps[join_index])

            return new_steps

        return steps

    async def _apply_index_usage(
        self,
        steps: List[Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用索引使用优化"""
        # 检查是否有扫描步骤可以替换为索引查找
        for i, step in enumerate(steps):
            if step["type"] in ["node_scan", "full_graph_scan"]:
                # 如果有合适的索引，替换为索引查找
                if await self._has_suitable_index(step, graph, context):
                    steps[i] = {
                        "type": "index_lookup",
                        "description": "索引查找",
                        "cost": step["cost"] * 0.1,  # 索引查找成本更低
                    }

        return steps

    async def _has_suitable_index(
        self, step: Dict[str, Any], graph: nx.MultiDiGraph, context: Dict[str, Any]
    ) -> bool:
        """检查是否有合适的索引"""
        # 简化的索引检查逻辑
        # 实际应用中需要维护索引元数据
        return graph.number_of_nodes() > 1000  # 当图较大时假设有索引

    async def _apply_subquery_optimization(
        self,
        steps: List[Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用子查询优化"""
        # 识别和优化子查询模式
        # 这里实现简单的子查询扁平化
        optimized_steps = []
        i = 0

        while i < len(steps):
            step = steps[i]
            optimized_steps.append(step)
            i += 1

        return optimized_steps

    async def _apply_cache_utilization(
        self,
        steps: List[Dict[str, Any]],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用缓存利用优化"""
        # 在计划开始添加缓存检查步骤
        cache_step = {
            "type": "cache_check",
            "description": "检查查询缓存",
            "cost": 0.1,  # 缓存检查成本很低
        }

        steps.insert(0, cache_step)
        return steps

    async def _estimate_cost(self, plan: QueryPlan, graph: nx.MultiDiGraph) -> float:
        """估算查询成本"""
        total_cost = 0.0

        for step in plan.optimized_steps:
            total_cost += step.get("cost", 0.0)

        # 根据图大小调整成本
        scale_factor = max(1.0, graph.number_of_nodes() / 1000.0)
        return total_cost * scale_factor

    async def execute_query(
        self,
        query_plan: QueryPlan,
        graph: nx.MultiDiGraph,
        context: Dict[str, Any] = None,
    ) -> Any:
        """
        执行查询计划

        Args:
            query_plan: 查询计划
            graph: 知识图谱
            context: 执行上下文

        Returns:
            查询结果
        """
        start_time = datetime.now()

        try:
            # 执行计划步骤
            results = None
            for step in query_plan.optimized_steps:
                results = await self._execute_plan_step(step, graph, context, results)

            # 更新计划统计
            execution_time = (datetime.now() - start_time).total_seconds()
            query_plan.execution_time = execution_time
            query_plan.actual_cost = execution_time
            query_plan.result_count = len(results) if hasattr(results, "__len__") else 1

            # 更新性能统计
            self._update_performance_stats(query_plan)

            # 缓存结果
            await self._cache_query_results(query_plan, results)

            self.logger.info(
                f"查询执行完成: {query_plan.query_id}, 执行时间: {execution_time:.3f}s"
            )
            return results

        except Exception as e:
            self.logger.error(f"查询执行失败: {str(e)}")
            raise

    async def _execute_plan_step(
        self,
        step: Dict[str, Any],
        graph: nx.MultiDiGraph,
        context: Dict[str, Any],
        previous_results: Any,
    ) -> Any:
        """执行单个计划步骤"""
        step_type = step["type"]

        if step_type == "cache_check":
            # 缓存检查已在优化阶段处理
            return previous_results

        elif step_type == "node_scan":
            return list(graph.nodes(data=True))

        elif step_type == "filter_application":
            return await self._apply_filters(previous_results, context)

        elif step_type == "connectivity_check":
            return await self._check_connectivity(previous_results, graph)

        # 其他步骤的实现...

        return previous_results

    async def _apply_filters(
        self, nodes: List[Any], context: Dict[str, Any]
    ) -> List[Any]:
        """应用过滤器"""
        # 简化的过滤实现
        filtered_nodes = []

        for node in nodes:
            if isinstance(node, tuple) and len(node) == 2:
                node_id, node_data = node
                # 这里实现具体的过滤逻辑
                filtered_nodes.append(node)

        return filtered_nodes

    async def _check_connectivity(
        self, nodes: List[Any], graph: nx.MultiDiGraph
    ) -> List[Any]:
        """检查连通性"""
        # 简化的连通性检查
        connected_components = []

        if nodes:
            # 使用子图进行连通性分析
            subgraph = graph.subgraph([node[0] for node in nodes])
            connected_components = list(nx.weakly_connected_components(subgraph))

        return connected_components

    def _update_performance_stats(self, query_plan: QueryPlan):
        """更新性能统计"""
        execution_time = query_plan.execution_time

        # 更新平均执行时间
        total_queries = self.performance_stats["total_queries"]
        current_avg = self.performance_stats["average_execution_time"]
        new_avg = (current_avg * (total_queries - 1) + execution_time) / total_queries
        self.performance_stats["average_execution_time"] = new_avg

        # 更新查询类型统计
        query_type = "unknown"
        for step in query_plan.optimized_steps:
            if "connectivity" in step["description"]:
                query_type = "connectivity"
                break
            elif "path" in step["description"]:
                query_type = "path_finding"
                break

        self.performance_stats["query_types"][query_type] += 1

    async def _cache_query_results(self, query_plan: QueryPlan, results: Any):
        """缓存查询结果"""
        if len(self.query_cache) >= self.max_cache_size:
            # 执行缓存清理
            await self._cleanup_cache()

        query_hash = query_plan.query_id
        cache_entry = CacheEntry(
            query_hash=query_hash,
            results=query_plan,  # 缓存整个查询计划
            timestamp=datetime.now(),
            access_count=1,
            size=1,  # 简化的大小估算
        )

        self.query_cache[query_hash] = cache_entry

    async def _cleanup_cache(self):
        """清理缓存"""
        current_time = datetime.now()

        # 移除过期的缓存条目
        expired_keys = [
            key
            for key, entry in self.query_cache.items()
            if current_time - entry.timestamp > self.cache_ttl
        ]

        for key in expired_keys:
            del self.query_cache[key]

        # 如果仍然超过大小限制，移除最不常用的
        if len(self.query_cache) > self.max_cache_size:
            sorted_entries = sorted(
                self.query_cache.items(), key=lambda x: x[1].access_count
            )

            remove_count = len(self.query_cache) - self.max_cache_size
            for i in range(remove_count):
                del self.query_cache[sorted_entries[i][0]]

        self.logger.debug(f"缓存清理完成，当前缓存大小: {len(self.query_cache)}")

    async def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            "performance": self.performance_stats,
            "cache_effectiveness": {
                "hit_rate": self.performance_stats["cache_hits"]
                / max(1, self.performance_stats["total_queries"]),
                "current_cache_size": len(self.query_cache),
                "max_cache_size": self.max_cache_size,
            },
            "query_plans_generated": len(self.query_plans),
            "average_optimization_time": 0.0,  # 可以添加实际的时间统计
        }

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理查询优化引擎资源")
        self.query_cache.clear()
        self.query_plans.clear()
        self.plan_history.clear()
        self.performance_stats.clear()
