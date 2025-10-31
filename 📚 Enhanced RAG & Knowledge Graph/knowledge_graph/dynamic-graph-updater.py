"""
动态知识图谱更新引擎
功能：实时监控和更新知识图谱，支持增量更新和一致性维护
"""

import hashlib
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx


@dataclass
class GraphUpdate:
    """图谱更新操作"""

    operation: (
        str  # add_node, remove_node, add_edge, remove_edge, update_node, update_edge
    )
    target_type: str  # node or edge
    target_id: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    confidence: float = 1.0


@dataclass
class ChangeSet:
    """变更集合"""

    updates: List[GraphUpdate]
    timestamp: datetime
    version: str


class DynamicGraphUpdater:
    """动态知识图谱更新引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 知识图谱实例
        self.knowledge_graph = nx.MultiDiGraph()

        # 更新历史
        self.update_history = deque(maxlen=config.get("max_history_size", 1000))
        self.change_sets: List[ChangeSet] = []

        # 一致性检查配置
        self.consistency_rules = self._load_consistency_rules()

        # 版本管理
        self.current_version = "1.0.0"
        self.auto_versioning = config.get("auto_versioning", True)

        # 缓存和性能优化
        self.entity_cache: Dict[str, Dict] = {}
        self.relationship_cache: Dict[Tuple[str, str], Dict] = {}
        self.cache_ttl = timedelta(minutes=config.get("cache_ttl_minutes", 30))
        self.last_cache_cleanup = datetime.now()

        self.logger.info("动态知识图谱更新引擎初始化完成")

    def _load_consistency_rules(self) -> Dict[str, Any]:
        """加载一致性规则"""
        return {
            "node_integrity": {
                "required_fields": ["id", "name", "type"],
                "type_constraints": {
                    "person": ["name", "age", "profession"],
                    "organization": ["name", "industry", "location"],
                    "concept": ["name", "category", "definition"],
                },
            },
            "relationship_constraints": {
                "allowed_relationships": {
                    "person": ["works_for", "knows", "located_in"],
                    "organization": ["has_employee", "located_in", "competes_with"],
                    "concept": ["is_a", "related_to", "part_of"],
                },
                "cardinality_limits": {
                    "works_for": {"max_per_source": 5},
                    "located_in": {"max_per_source": 3},
                },
            },
        }

    async def initialize(self):
        """异步初始化"""
        self.logger.info("开始异步初始化动态图谱更新引擎")
        await self._load_initial_graph()
        self.logger.info("动态图谱更新引擎异步初始化完成")

    async def _load_initial_graph(self):
        """加载初始图谱数据"""
        # 这里可以连接数据库或文件加载现有图谱
        # 暂时创建空图谱
        self.knowledge_graph = nx.MultiDiGraph()
        self.logger.info("初始图谱加载完成")

    async def apply_updates(self, updates: List[GraphUpdate]) -> Dict[str, Any]:
        """
        应用批量更新

        Args:
            updates: 更新操作列表

        Returns:
            更新结果统计
        """
        self.logger.info(f"开始应用 {len(updates)} 个更新")

        results = {"successful": 0, "failed": 0, "errors": [], "warnings": []}

        successful_updates = []

        for update in updates:
            try:
                # 验证更新操作
                validation_result = await self._validate_update(update)
                if not validation_result["valid"]:
                    results["failed"] += 1
                    results["errors"].append(
                        {
                            "update": update.operation,
                            "target": update.target_id,
                            "error": validation_result["error"],
                        }
                    )
                    continue

                # 执行更新操作
                await self._execute_update(update)
                successful_updates.append(update)
                results["successful"] += 1

                # 记录警告
                if validation_result.get("warnings"):
                    results["warnings"].extend(validation_result["warnings"])

            except Exception as e:
                self.logger.error(f"应用更新失败: {str(e)}")
                results["failed"] += 1
                results["errors"].append(
                    {
                        "update": update.operation,
                        "target": update.target_id,
                        "error": str(e),
                    }
                )

        # 如果有关成功的更新，创建变更集
        if successful_updates:
            await self._create_change_set(successful_updates)

            # 执行一致性检查
            consistency_results = await self._check_consistency()
            results["consistency_issues"] = consistency_results

            # 清理缓存
            await self._cleanup_cache()

        self.logger.info(
            f"更新应用完成: {results['successful']} 成功, {results['failed']} 失败"
        )
        return results

    async def _validate_update(self, update: GraphUpdate) -> Dict[str, Any]:
        """验证更新操作"""
        result = {"valid": True, "warnings": []}

        # 基础验证
        if not update.target_id:
            result["valid"] = False
            result["error"] = "目标ID不能为空"
            return result

        if update.operation not in [
            "add_node",
            "remove_node",
            "add_edge",
            "remove_edge",
            "update_node",
            "update_edge",
        ]:
            result["valid"] = False
            result["error"] = f"不支持的操作类型: {update.operation}"
            return result

        # 操作特定验证
        if update.operation.startswith("add_"):
            if update.operation == "add_node" and not update.data.get("name"):
                result["valid"] = False
                result["error"] = "添加节点必须包含名称"
                return result

            if update.operation == "add_edge" and not all(
                key in update.data for key in ["source", "target", "relation_type"]
            ):
                result["valid"] = False
                result["error"] = "添加边必须包含源节点、目标节点和关系类型"
                return result

        elif update.operation.startswith("remove_"):
            if update.operation == "remove_node" and not self.knowledge_graph.has_node(
                update.target_id
            ):
                result["valid"] = False
                result["error"] = f"节点不存在: {update.target_id}"
                return result

            if update.operation == "remove_edge" and not self.knowledge_graph.has_edge(
                update.data.get("source"), update.data.get("target")
            ):
                result["valid"] = False
                result["error"] = (
                    f"边不存在: {update.data.get('source')} -> {update.data.get('target')}"
                )
                return result

        # 一致性规则验证
        consistency_check = await self._check_update_consistency(update)
        if not consistency_check["valid"]:
            result["valid"] = False
            result["error"] = consistency_check["error"]
            return result

        result["warnings"] = consistency_check.get("warnings", [])
        return result

    async def _check_update_consistency(self, update: GraphUpdate) -> Dict[str, Any]:
        """检查更新一致性"""
        result = {"valid": True}

        if update.operation == "add_node":
            # 检查节点类型约束
            node_type = update.data.get("type")
            if (
                node_type
                in self.consistency_rules["node_integrity"]["type_constraints"]
            ):
                required_fields = self.consistency_rules["node_integrity"][
                    "type_constraints"
                ][node_type]
                missing_fields = [
                    field for field in required_fields if field not in update.data
                ]
                if missing_fields:
                    result["valid"] = False
                    result["error"] = (
                        f"节点类型 {node_type} 缺少必需字段: {missing_fields}"
                    )

        elif update.operation == "add_edge":
            source_node = update.data.get("source")
            target_node = update.data.get("target")
            relation_type = update.data.get("relation_type")

            # 检查源节点类型
            if self.knowledge_graph.has_node(source_node):
                source_type = self.knowledge_graph.nodes[source_node].get("type")
                allowed_relations = self.consistency_rules["relationship_constraints"][
                    "allowed_relationships"
                ].get(source_type, [])
                if relation_type not in allowed_relations:
                    result["warnings"] = [
                        f"关系类型 {relation_type} 可能不适合节点类型 {source_type}"
                    ]

            # 检查基数限制
            if (
                relation_type
                in self.consistency_rules["relationship_constraints"][
                    "cardinality_limits"
                ]
            ):
                limit = self.consistency_rules["relationship_constraints"][
                    "cardinality_limits"
                ][relation_type]
                current_count = len(
                    [
                        edge
                        for edge in self.knowledge_graph.edges(source_node, data=True)
                        if edge[2].get("relation_type") == relation_type
                    ]
                )
                if current_count >= limit.get("max_per_source", float("inf")):
                    result["warnings"] = [f"关系 {relation_type} 已达到基数限制"]

        return result

    async def _execute_update(self, update: GraphUpdate):
        """执行单个更新操作"""
        if update.operation == "add_node":
            self.knowledge_graph.add_node(update.target_id, **update.data)
            self.entity_cache[update.target_id] = update.data

        elif update.operation == "remove_node":
            self.knowledge_graph.remove_node(update.target_id)
            self.entity_cache.pop(update.target_id, None)

        elif update.operation == "add_edge":
            source = update.data["source"]
            target = update.data["target"]
            edge_data = {
                k: v for k, v in update.data.items() if k not in ["source", "target"]
            }
            self.knowledge_graph.add_edge(source, target, **edge_data)
            self.relationship_cache[(source, target)] = edge_data

        elif update.operation == "remove_edge":
            source = update.data["source"]
            target = update.data["target"]
            self.knowledge_graph.remove_edge(source, target)
            self.relationship_cache.pop((source, target), None)

        elif update.operation == "update_node":
            if self.knowledge_graph.has_node(update.target_id):
                current_data = self.knowledge_graph.nodes[update.target_id]
                current_data.update(update.data)
                self.entity_cache[update.target_id] = current_data

        elif update.operation == "update_edge":
            source = update.data.get("source")
            target = update.data.get("target")
            if source and target and self.knowledge_graph.has_edge(source, target):
                edge_data = self.knowledge_graph[source][target]
                for key, value in update.data.items():
                    if key not in ["source", "target"]:
                        edge_data[key] = value
                self.relationship_cache[(source, target)] = edge_data

        # 记录更新历史
        self.update_history.append(update)

    async def _create_change_set(self, updates: List[GraphUpdate]):
        """创建变更集"""
        change_set = ChangeSet(
            updates=updates,
            timestamp=datetime.now(),
            version=self._generate_version_hash(updates),
        )

        self.change_sets.append(change_set)

        # 更新版本号
        if self.auto_versioning:
            self.current_version = self._increment_version(self.current_version)

        self.logger.info(f"创建变更集 {change_set.version}，包含 {len(updates)} 个更新")

    def _generate_version_hash(self, updates: List[GraphUpdate]) -> str:
        """生成版本哈希"""
        update_data = json.dumps(
            [
                {
                    "operation": update.operation,
                    "target": update.target_id,
                    "timestamp": update.timestamp.isoformat(),
                }
                for update in updates
            ],
            sort_keys=True,
        )

        return hashlib.md5(update_data.encode()).hexdigest()[:8]

    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        parts = current_version.split(".")
        if len(parts) == 3:
            try:
                major, minor, patch = map(int, parts)
                patch += 1
                return f"{major}.{minor}.{patch}"
            except ValueError:
                pass
        return current_version

    async def _check_consistency(self) -> List[Dict[str, Any]]:
        """执行一致性检查"""
        issues = []

        # 检查孤立节点
        isolated_nodes = list(nx.isolates(self.knowledge_graph))
        if isolated_nodes:
            issues.append(
                {
                    "type": "isolated_nodes",
                    "severity": "warning",
                    "message": f"发现 {len(isolated_nodes)} 个孤立节点",
                    "details": isolated_nodes,
                }
            )

        # 检查重复节点
        node_names = defaultdict(list)
        for node_id, node_data in self.knowledge_graph.nodes(data=True):
            name = node_data.get("name")
            if name:
                node_names[name].append(node_id)

        duplicate_names = {
            name: nodes for name, nodes in node_names.items() if len(nodes) > 1
        }
        if duplicate_names:
            issues.append(
                {
                    "type": "duplicate_names",
                    "severity": "warning",
                    "message": f"发现 {len(duplicate_names)} 个重复名称的节点",
                    "details": duplicate_names,
                }
            )

        # 检查循环关系
        try:
            cycles = list(nx.simple_cycles(self.knowledge_graph))
            if cycles:
                issues.append(
                    {
                        "type": "cycles",
                        "severity": "info",
                        "message": f"发现 {len(cycles)} 个循环关系",
                        "details": cycles,
                    }
                )
        except Exception as e:
            self.logger.warning(f"检查循环关系时出错: {str(e)}")

        return issues

    async def _cleanup_cache(self):
        """清理缓存"""
        current_time = datetime.now()
        if current_time - self.last_cache_cleanup > self.cache_ttl:
            self.entity_cache.clear()
            self.relationship_cache.clear()
            self.last_cache_cleanup = current_time
            self.logger.debug("缓存清理完成")

    async def rollback_changes(self, target_version: str = None) -> Dict[str, Any]:
        """
        回滚变更到指定版本

        Args:
            target_version: 目标版本号，如果为None则回滚到最后一次变更前

        Returns:
            回滚结果
        """
        self.logger.info(f"开始回滚变更到版本: {target_version or '上一次变更前'}")

        if not self.change_sets:
            return {"success": False, "error": "没有可回滚的变更集"}

        # 找到目标变更集
        target_index = -1
        if target_version:
            for i, change_set in enumerate(self.change_sets):
                if change_set.version == target_version:
                    target_index = i
                    break

        if target_index == -1 and target_version:
            return {"success": False, "error": f"未找到版本: {target_version}"}

        # 执行回滚
        rollback_updates = []
        for change_set in self.change_sets[target_index + 1 :]:
            for update in reversed(change_set.updates):
                # 创建反向操作
                reverse_update = await self._create_reverse_update(update)
                if reverse_update:
                    rollback_updates.append(reverse_update)

        # 应用回滚更新
        if rollback_updates:
            result = await self.apply_updates(rollback_updates)
            # 移除回滚的变更集
            self.change_sets = self.change_sets[: target_index + 1]
            return {
                "success": True,
                "rollback_updates": len(rollback_updates),
                "details": result,
            }
        else:
            return {"success": True, "message": "无需回滚操作"}

    async def _create_reverse_update(
        self, update: GraphUpdate
    ) -> Optional[GraphUpdate]:
        """创建反向更新操作"""
        if update.operation == "add_node":
            return GraphUpdate(
                operation="remove_node",
                target_type="node",
                target_id=update.target_id,
                data={},
                timestamp=datetime.now(),
                source="rollback",
            )

        elif update.operation == "remove_node":
            # 需要保存被删除节点的数据以便恢复
            return None  # 复杂情况，暂不实现

        elif update.operation == "add_edge":
            return GraphUpdate(
                operation="remove_edge",
                target_type="edge",
                target_id=f"{update.data['source']}_{update.data['target']}",
                data={"source": update.data["source"], "target": update.data["target"]},
                timestamp=datetime.now(),
                source="rollback",
            )

        elif update.operation == "remove_edge":
            return None  # 复杂情况，暂不实现

        return None

    async def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        return {
            "total_nodes": self.knowledge_graph.number_of_nodes(),
            "total_edges": self.knowledge_graph.number_of_edges(),
            "graph_density": nx.density(self.knowledge_graph),
            "connected_components": nx.number_weakly_connected_components(
                self.knowledge_graph
            ),
            "average_clustering": nx.average_clustering(
                self.knowledge_graph.to_undirected()
            ),
            "last_update": (
                self.update_history[-1].timestamp if self.update_history else None
            ),
            "current_version": self.current_version,
            "total_change_sets": len(self.change_sets),
        }

    async def export_graph(self, format: str = "gexf") -> str:
        """导出图谱数据"""
        if format == "gexf":
            return await self._export_gexf()
        elif format == "json":
            return await self._export_json()
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    async def _export_gexf(self) -> str:
        """导出为GEXF格式"""
        return "\n".join(nx.generate_gexf(self.knowledge_graph))

    async def _export_json(self) -> str:
        """导出为JSON格式"""
        graph_data = nx.node_link_data(self.knowledge_graph)
        return json.dumps(graph_data, indent=2, ensure_ascii=False)

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理动态图谱更新引擎资源")
        self.knowledge_graph.clear()
        self.update_history.clear()
        self.change_sets.clear()
        self.entity_cache.clear()
        self.relationship_cache.clear()
