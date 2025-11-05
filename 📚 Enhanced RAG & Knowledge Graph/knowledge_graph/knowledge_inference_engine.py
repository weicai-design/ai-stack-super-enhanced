"""
知识推理引擎
功能：基于知识图谱进行逻辑推理和知识发现，支持规则推理和概率推理
"""

import logging
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx


@dataclass
class InferenceRule:
    """推理规则"""

    name: str
    condition: str  # 规则条件
    conclusion: str  # 规则结论
    confidence: float  # 规则置信度
    priority: int  # 规则优先级
    category: str  # 规则类别


@dataclass
class InferenceResult:
    """推理结果"""

    conclusion: str
    confidence: float
    evidence: List[Any]
    rule_used: str
    timestamp: datetime


@dataclass
class ReasoningPath:
    """推理路径"""

    steps: List[Dict[str, Any]]
    final_confidence: float
    depth: int


class KnowledgeInferenceEngine:
    """知识推理引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 推理规则库
        self.rules: List[InferenceRule] = []
        self.rule_categories: Set[str] = set()

        # 推理缓存
        self.inference_cache: Dict[str, InferenceResult] = {}
        self.reasoning_paths: Dict[str, ReasoningPath] = {}

        # 统计信息
        self.inference_stats = {
            "total_inferences": 0,
            "successful_inferences": 0,
            "failed_inferences": 0,
            "rule_usage": defaultdict(int),
            "average_confidence": 0.0,
            "reasoning_depth_distribution": defaultdict(int),
        }

        # 推理配置
        self.max_reasoning_depth = config.get("max_reasoning_depth", 5)
        self.min_confidence_threshold = config.get("min_confidence_threshold", 0.3)
        self.enable_probabilistic_reasoning = config.get(
            "enable_probabilistic_reasoning", True
        )

        # 初始化规则
        self._load_default_rules()

        self.logger.info("知识推理引擎初始化完成")

    def _load_default_rules(self):
        """加载默认推理规则"""
        default_rules = [
            InferenceRule(
                name="transitive_relation",
                condition="A related_to B and B related_to C",
                conclusion="A related_to C",
                confidence=0.8,
                priority=1,
                category="transitivity",
            ),
            InferenceRule(
                name="type_inheritance",
                condition="A is_a B and B is_a C",
                conclusion="A is_a C",
                confidence=0.9,
                priority=1,
                category="inheritance",
            ),
            InferenceRule(
                name="symmetric_relation",
                condition="A similar_to B",
                conclusion="B similar_to A",
                confidence=0.7,
                priority=2,
                category="symmetry",
            ),
            InferenceRule(
                name="property_inheritance",
                condition="A is_a B and B has_property P",
                conclusion="A has_property P",
                confidence=0.6,
                priority=2,
                category="inheritance",
            ),
            InferenceRule(
                name="location_inference",
                condition="A located_in B and B located_in C",
                conclusion="A located_in C",
                confidence=0.7,
                priority=2,
                category="spatial",
            ),
        ]

        self.rules.extend(default_rules)
        self.rule_categories.update(rule.category for rule in default_rules)
        self.logger.info(f"加载了 {len(default_rules)} 个默认推理规则")

    async def initialize(self):
        """异步初始化"""
        self.logger.info("开始异步初始化推理引擎")
        await self._load_custom_rules()
        await self._warmup_inference_cache()
        self.logger.info("推理引擎异步初始化完成")

    async def _load_custom_rules(self):
        """加载自定义规则"""
        # 这里可以连接数据库或文件加载自定义规则
        # 暂时为空实现
        pass

    async def _warmup_inference_cache(self):
        """预热推理缓存"""
        # 预加载常用推理模式
        pass

    async def infer_knowledge(
        self,
        graph: nx.MultiDiGraph,
        target_entities: List[str] = None,
        query: str = None,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行知识推理

        Args:
            graph: 知识图谱
            target_entities: 目标实体列表
            query: 推理查询
            context: 推理上下文

        Returns:
            推理结果
        """
        self.inference_stats["total_inferences"] += 1

        start_time = datetime.now()
        self.logger.info(f"开始知识推理，目标实体: {target_entities}, 查询: {query}")

        try:
            # 确定推理目标
            inference_targets = await self._determine_inference_targets(
                graph, target_entities, query, context
            )

            # 执行推理
            results = {}
            reasoning_paths = {}

            for target in inference_targets:
                inference_result, reasoning_path = await self._reason_about_entity(
                    graph, target, context
                )

                if (
                    inference_result
                    and inference_result.confidence >= self.min_confidence_threshold
                ):
                    results[target] = inference_result
                    reasoning_paths[target] = reasoning_path

            # 更新统计信息
            self._update_inference_stats(results, start_time)

            return {
                "inferences": results,
                "reasoning_paths": reasoning_paths,
                "metadata": {
                    "total_targets": len(inference_targets),
                    "successful_inferences": len(results),
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "average_confidence": (
                        np.mean([r.confidence for r in results.values()])
                        if results
                        else 0.0
                    ),
                },
            }

        except Exception as e:
            self.inference_stats["failed_inferences"] += 1
            self.logger.error(f"知识推理失败: {str(e)}")
            raise

    async def _determine_inference_targets(
        self,
        graph: nx.MultiDiGraph,
        target_entities: List[str],
        query: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """确定推理目标"""
        if target_entities:
            return target_entities

        if query:
            # 从查询中提取目标实体
            return await self._extract_entities_from_query(query, graph)

        # 如果没有指定目标，选择中心性高的节点
        return await self._select_central_entities(graph, limit=10)

    async def _extract_entities_from_query(
        self, query: str, graph: nx.MultiDiGraph
    ) -> List[str]:
        """从查询中提取实体"""
        entities = []

        # 简单的模式匹配提取实体
        node_names = [data.get("name", "") for _, data in graph.nodes(data=True)]

        for name in node_names:
            if name and name in query:
                entities.append(
                    next(
                        node
                        for node, data in graph.nodes(data=True)
                        if data.get("name") == name
                    )
                )

        return entities

    async def _select_central_entities(
        self, graph: nx.MultiDiGraph, limit: int = 10
    ) -> List[str]:
        """选择中心性高的实体作为推理目标"""
        if graph.number_of_nodes() == 0:
            return []

        try:
            # 计算度中心性
            degree_centrality = nx.degree_centrality(graph)
            sorted_entities = sorted(
                degree_centrality.items(), key=lambda x: x[1], reverse=True
            )

            return [entity for entity, _ in sorted_entities[:limit]]

        except Exception as e:
            self.logger.warning(f"中心性计算失败: {str(e)}，使用随机选择")
            nodes = list(graph.nodes())
            return random.sample(nodes, min(limit, len(nodes)))

    async def _reason_about_entity(
        self,
        graph: nx.MultiDiGraph,
        entity: str,
        context: Dict[str, Any],
        current_depth: int = 0,
        visited: Set[str] = None,
        current_path: List[Dict[str, Any]] = None,
    ) -> Tuple[Optional[InferenceResult], Optional[ReasoningPath]]:
        """
        关于单个实体的推理

        Args:
            graph: 知识图谱
            entity: 目标实体
            context: 推理上下文
            current_depth: 当前推理深度
            visited: 已访问实体集合
            current_path: 当前推理路径

        Returns:
            (推理结果, 推理路径)
        """
        if visited is None:
            visited = set()
        if current_path is None:
            current_path = []

        # 检查深度限制
        if current_depth >= self.max_reasoning_depth:
            return None, None

        # 检查循环推理
        if entity in visited:
            return None, None

        visited.add(entity)

        # 检查缓存
        cache_key = f"{entity}_{current_depth}_{str(context)}"
        if cache_key in self.inference_cache:
            cached_result = self.inference_cache[cache_key]
            return cached_result, self.reasoning_paths.get(cache_key)

        # 执行推理
        best_result = None
        best_confidence = 0.0
        best_rule = None
        best_evidence = []
        reasoning_steps = []

        # 应用所有相关规则
        for rule in self.rules:
            rule_result, evidence, used_entities = await self._apply_rule(
                graph, entity, rule, context, current_depth, visited
            )

            if rule_result and rule_result.confidence > best_confidence:
                best_result = rule_result
                best_confidence = rule_result.confidence
                best_rule = rule.name
                best_evidence = evidence

                # 记录推理步骤
                reasoning_steps.append(
                    {
                        "rule": rule.name,
                        "confidence": rule_result.confidence,
                        "entities_used": used_entities,
                        "depth": current_depth,
                    }
                )

        # 递归推理
        if best_result and current_depth < self.max_reasoning_depth - 1:
            # 基于当前结果进行深度推理
            related_entities = await self._get_related_entities(graph, entity)

            for related_entity in related_entities:
                if related_entity not in visited:
                    sub_result, sub_path = await self._reason_about_entity(
                        graph,
                        related_entity,
                        context,
                        current_depth + 1,
                        visited.copy(),
                        reasoning_steps,
                    )

                    if sub_result and sub_result.confidence > best_confidence:
                        best_result = sub_result
                        best_confidence = sub_result.confidence
                        best_rule = sub_result.rule_used
                        best_evidence.extend(sub_result.evidence)

                        # 合并推理步骤
                        if sub_path:
                            reasoning_steps.extend(sub_path.steps)

        # 构建最终结果
        if best_result:
            inference_result = InferenceResult(
                conclusion=best_result.conclusion,
                confidence=best_confidence,
                evidence=best_evidence,
                rule_used=best_rule or "unknown",
                timestamp=datetime.now(),
            )

            reasoning_path = ReasoningPath(
                steps=reasoning_steps,
                final_confidence=best_confidence,
                depth=current_depth,
            )

            # 更新缓存
            self.inference_cache[cache_key] = inference_result
            self.reasoning_paths[cache_key] = reasoning_path

            return inference_result, reasoning_path

        return None, None

    async def _apply_rule(
        self,
        graph: nx.MultiDiGraph,
        entity: str,
        rule: InferenceRule,
        context: Dict[str, Any],
        current_depth: int,
        visited: Set[str],
    ) -> Tuple[Optional[InferenceResult], List[Any], List[str]]:
        """
        应用单个推理规则

        Returns:
            (推理结果, 证据列表, 使用的实体列表)
        """
        try:
            # 解析规则条件
            conditions = self._parse_rule_condition(rule.condition)

            # 检查规则前提条件
            premises_met, evidence, used_entities = await self._check_rule_premises(
                graph, entity, conditions, context, current_depth, visited
            )

            if not premises_met:
                return None, [], []

            # 生成结论
            conclusion = await self._generate_conclusion(
                rule.conclusion, entity, evidence
            )

            # 计算置信度
            confidence = await self._calculate_confidence(rule, evidence, context)

            inference_result = InferenceResult(
                conclusion=conclusion,
                confidence=confidence,
                evidence=evidence,
                rule_used=rule.name,
                timestamp=datetime.now(),
            )

            return inference_result, evidence, used_entities

        except Exception as e:
            self.logger.warning(f"应用规则 {rule.name} 失败: {str(e)}")
            return None, [], []

    def _parse_rule_condition(self, condition: str) -> List[Dict[str, Any]]:
        """解析规则条件"""
        conditions = []

        # 简单的条件解析（实际应用中需要更复杂的解析器）
        parts = condition.split(" and ")

        for part in parts:
            part = part.strip()
            if " related_to " in part:
                conditions.append(
                    {"type": "relation", "relation": "related_to", "pattern": part}
                )
            elif " is_a " in part:
                conditions.append(
                    {"type": "relation", "relation": "is_a", "pattern": part}
                )
            elif " has_property " in part:
                conditions.append(
                    {"type": "property", "relation": "has_property", "pattern": part}
                )
            elif " located_in " in part:
                conditions.append(
                    {"type": "relation", "relation": "located_in", "pattern": part}
                )
            elif " similar_to " in part:
                conditions.append(
                    {"type": "relation", "relation": "similar_to", "pattern": part}
                )

        return conditions

    async def _check_rule_premises(
        self,
        graph: nx.MultiDiGraph,
        entity: str,
        conditions: List[Dict[str, Any]],
        context: Dict[str, Any],
        current_depth: int,
        visited: Set[str],
    ) -> Tuple[bool, List[Any], List[str]]:
        """检查规则前提条件"""
        evidence = []
        used_entities = [entity]
        all_premises_met = True

        for condition in conditions:
            premise_met, premise_evidence, premise_entities = (
                await self._check_single_premise(
                    graph, entity, condition, context, current_depth, visited
                )
            )

            if not premise_met:
                all_premises_met = False
                break

            evidence.extend(premise_evidence)
            used_entities.extend(premise_entities)

        return all_premises_met, evidence, list(set(used_entities))

    async def _check_single_premise(
        self,
        graph: nx.MultiDiGraph,
        entity: str,
        condition: Dict[str, Any],
        context: Dict[str, Any],
        current_depth: int,
        visited: Set[str],
    ) -> Tuple[bool, List[Any], List[str]]:
        """检查单个前提条件"""
        condition_type = condition["type"]
        relation = condition["relation"]
        pattern = condition["pattern"]

        if condition_type == "relation":
            return await self._check_relation_premise(
                graph, entity, relation, pattern, context, current_depth, visited
            )
        elif condition_type == "property":
            return await self._check_property_premise(graph, entity, relation, pattern)

        return False, [], []

    async def _check_relation_premise(
        self,
        graph: nx.MultiDiGraph,
        entity: str,
        relation: str,
        pattern: str,
        context: Dict[str, Any],
        current_depth: int,
        visited: Set[str],
    ) -> Tuple[bool, List[Any], List[str]]:
        """检查关系前提条件"""
        # 查找直接关系
        direct_relations = []
        for neighbor in graph.neighbors(entity):
            edge_data = graph.get_edge_data(entity, neighbor)
            if edge_data:
                for key, data in edge_data.items():
                    if data.get("relation_type") == relation:
                        direct_relations.append((neighbor, data))

        if direct_relations:
            evidence = [
                f"{entity} {relation} {neighbor}" for neighbor, _ in direct_relations
            ]
            entities = [entity] + [neighbor for neighbor, _ in direct_relations]
            return True, evidence, entities

        # 如果没有直接关系，尝试推理
        if current_depth < self.max_reasoning_depth - 1:
            for neighbor in graph.neighbors(entity):
                if neighbor not in visited:
                    # 递归检查
                    sub_result, sub_path = await self._reason_about_entity(
                        graph, neighbor, context, current_depth + 1, visited.copy()
                    )

                    if sub_result and relation in sub_result.conclusion:
                        evidence = [sub_result.conclusion] + sub_result.evidence
                        entities = [entity, neighbor]
                        return True, evidence, entities

        return False, [], []

    async def _check_property_premise(
        self, graph: nx.MultiDiGraph, entity: str, relation: str, pattern: str
    ) -> Tuple[bool, List[Any], List[str]]:
        """检查属性前提条件"""
        node_data = graph.nodes[entity]

        # 提取属性名
        match = re.search(r"has_property (\w+)", pattern)
        if match:
            property_name = match.group(1)
            if property_name in node_data:
                evidence = [
                    f"{entity} has_property {property_name} = {node_data[property_name]}"
                ]
                return True, evidence, [entity]

        return False, [], []

    async def _generate_conclusion(
        self, conclusion_template: str, entity: str, evidence: List[Any]
    ) -> str:
        """生成结论"""
        # 简单的模板替换
        conclusion = conclusion_template

        # 替换变量
        conclusion = conclusion.replace("A", entity)

        # 从证据中提取其他变量
        for i, evidence_item in enumerate(evidence):
            if isinstance(evidence_item, str):
                # 简单的证据解析
                if " related_to " in evidence_item:
                    parts = evidence_item.split(" related_to ")
                    if len(parts) == 2:
                        conclusion = conclusion.replace("B", parts[1])
                elif " is_a " in evidence_item:
                    parts = evidence_item.split(" is_a ")
                    if len(parts) == 2:
                        conclusion = conclusion.replace("B", parts[1])

        return conclusion

    async def _calculate_confidence(
        self, rule: InferenceRule, evidence: List[Any], context: Dict[str, Any]
    ) -> float:
        """计算推理置信度"""
        base_confidence = rule.confidence

        # 基于证据数量调整置信度
        evidence_factor = min(1.0, len(evidence) * 0.2)

        # 基于证据质量调整置信度（简化实现）
        quality_factor = 1.0
        for evidence_item in evidence:
            if isinstance(evidence_item, str) and "inferred" in evidence_item:
                quality_factor *= 0.8  # 推理证据的折扣

        final_confidence = base_confidence * evidence_factor * quality_factor

        # 应用概率推理（如果启用）
        if self.enable_probabilistic_reasoning:
            final_confidence = await self._apply_probabilistic_reasoning(
                final_confidence, evidence, context
            )

        return max(0.0, min(1.0, final_confidence))

    async def _apply_probabilistic_reasoning(
        self, base_confidence: float, evidence: List[Any], context: Dict[str, Any]
    ) -> float:
        """应用概率推理"""
        # 简化的概率推理实现
        # 实际应用中可以使用贝叶斯网络等更复杂的方法

        # 基于证据一致性的调整
        consistency_bonus = 0.0
        if len(evidence) >= 2:
            # 检查证据一致性
            consistent_count = sum(
                1 for e in evidence if self._is_consistent_evidence(e, context)
            )
            consistency_ratio = consistent_count / len(evidence)
            consistency_bonus = consistency_ratio * 0.2

        # 基于上下文的调整
        context_factor = 1.0
        if context and "domain_knowledge" in context:
            domain_match = await self._check_domain_match(
                evidence, context["domain_knowledge"]
            )
            context_factor = 0.8 + (domain_match * 0.2)

        return base_confidence * context_factor + consistency_bonus

    def _is_consistent_evidence(self, evidence: Any, context: Dict[str, Any]) -> bool:
        """检查证据一致性"""
        # 简化的一致性检查
        if isinstance(evidence, str):
            return "contradiction" not in evidence.lower()
        return True

    async def _check_domain_match(
        self, evidence: List[Any], domain_knowledge: Any
    ) -> float:
        """检查领域知识匹配度"""
        # 简化的领域匹配检查
        return 0.7  # 默认匹配度

    async def _get_related_entities(
        self, graph: nx.MultiDiGraph, entity: str
    ) -> List[str]:
        """获取相关实体"""
        related = list(graph.neighbors(entity))

        # 也可以包括反向关系
        predecessors = list(graph.predecessors(entity))
        related.extend(predecessors)

        return list(set(related))

    def _update_inference_stats(
        self, results: Dict[str, InferenceResult], start_time: datetime
    ):
        """更新推理统计"""
        successful_count = len(results)
        self.inference_stats["successful_inferences"] += successful_count

        if successful_count > 0:
            avg_confidence = (
                sum(r.confidence for r in results.values()) / successful_count
            )
            current_avg = self.inference_stats["average_confidence"]
            total_successful = self.inference_stats["successful_inferences"]

            new_avg = (
                current_avg * (total_successful - successful_count)
                + avg_confidence * successful_count
            ) / total_successful
            self.inference_stats["average_confidence"] = new_avg

        # 更新推理深度分布
        for result in results.values():
            # 简化深度估算
            depth = min(len(result.evidence), 5)
            self.inference_stats["reasoning_depth_distribution"][depth] += 1

    async def add_rule(self, rule: InferenceRule):
        """添加推理规则"""
        self.rules.append(rule)
        self.rule_categories.add(rule.category)

        # 按优先级排序
        self.rules.sort(key=lambda x: x.priority, reverse=True)

        self.logger.info(f"添加推理规则: {rule.name}")

    async def remove_rule(self, rule_name: str):
        """移除推理规则"""
        self.rules = [rule for rule in self.rules if rule.name != rule_name]
        self.logger.info(f"移除推理规则: {rule_name}")

    async def get_inference_stats(self) -> Dict[str, Any]:
        """获取推理统计信息"""
        return {
            "basic_stats": self.inference_stats,
            "rule_usage": dict(self.inference_stats["rule_usage"]),
            "cache_info": {
                "cache_size": len(self.inference_cache),
                "reasoning_paths_stored": len(self.reasoning_paths),
            },
            "rule_library": {
                "total_rules": len(self.rules),
                "categories": list(self.rule_categories),
                "rules_by_category": {
                    category: len([r for r in self.rules if r.category == category])
                    for category in self.rule_categories
                },
            },
        }

    async def clear_cache(self):
        """清理推理缓存"""
        self.inference_cache.clear()
        self.reasoning_paths.clear()
        self.logger.info("推理缓存已清理")

    async def export_rules(self, format: str = "json") -> str:
        """导出推理规则"""
        if format == "json":
            import json

            rules_data = [
                {
                    "name": rule.name,
                    "condition": rule.condition,
                    "conclusion": rule.conclusion,
                    "confidence": rule.confidence,
                    "priority": rule.priority,
                    "category": rule.category,
                }
                for rule in self.rules
            ]
            return json.dumps(rules_data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理推理引擎资源")
        self.rules.clear()
        self.inference_cache.clear()
        self.reasoning_paths.clear()
        self.inference_stats.clear()
