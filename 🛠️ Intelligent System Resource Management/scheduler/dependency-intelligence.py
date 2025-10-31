"""
依赖智能分析系统
负责服务依赖关系的智能分析、循环依赖检测、依赖优化建议
对应需求: 8.3/8.5 - 依赖解析、启动顺序优化、自我进化
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List

import networkx as nx

from . import DependencyResolutionError, DependencyType, ServiceDependency, logger


@dataclass
class DependencyAnalysis:
    """依赖分析结果"""

    service_name: str
    direct_dependencies: List[str]
    transitive_dependencies: List[str]
    dependents: List[str]
    dependency_depth: int
    criticality_score: float
    optimization_suggestions: List[str]
    potential_issues: List[str]


@dataclass
class DependencyGraphMetrics:
    """依赖图指标"""

    total_services: int
    total_dependencies: int
    max_dependency_depth: int
    average_dependency_depth: float
    cyclic_dependencies: List[List[str]]
    strongly_connected_components: List[List[str]]
    critical_services: List[str]
    leaf_services: List[str]


@dataclass
class OptimizationRecommendation:
    """优化建议"""

    type: str  # 'dependency_break', 'service_merge', 'interface_extract'
    description: str
    services_involved: List[str]
    expected_benefit: float  # 0-1的收益评分
    implementation_complexity: float  # 0-1的实现复杂度
    priority: int  # 优先级 1-5


class DependencyIntelligence:
    """
    依赖智能分析系统
    提供依赖关系分析、优化建议、循环检测等智能功能
    """

    def __init__(self, service_scheduler=None):
        self.service_scheduler = service_scheduler
        self.dependency_graph = nx.DiGraph()
        self.analysis_cache = {}
        self.cache_ttl = 300  # 缓存5分钟
        self.last_analysis_time = 0

        # 优化规则库
        self.optimization_rules = {
            "circular_dependency": self._detect_circular_dependencies,
            "long_chain": self._detect_long_dependency_chains,
            "bottleneck": self._detect_bottleneck_services,
            "over_coupling": self._detect_over_coupling,
            "under_utilization": self._detect_under_utilized_services,
        }

        logger.info("依赖智能分析系统初始化完成")

    async def analyze_service_dependencies(
        self, service_name: str
    ) -> DependencyAnalysis:
        """
        分析单个服务的依赖关系

        Args:
            service_name: 服务名称

        Returns:
            DependencyAnalysis: 依赖分析结果
        """
        # 检查缓存
        cache_key = f"analysis_{service_name}"
        if cache_key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data

        try:
            # 构建依赖图（如果尚未构建）
            await self._build_dependency_graph()

            if service_name not in self.dependency_graph:
                raise DependencyResolutionError(f"服务不在依赖图中: {service_name}")

            # 计算各种依赖指标
            direct_deps = list(self.dependency_graph.predecessors(service_name))
            transitive_deps = await self._find_transitive_dependencies(service_name)
            dependents = list(self.dependency_graph.successors(service_name))
            depth = await self._calculate_dependency_depth(service_name)
            criticality = await self._calculate_criticality_score(service_name)

            # 生成优化建议
            suggestions = await self._generate_optimization_suggestions(service_name)
            issues = await self._detect_potential_issues(service_name)

            analysis = DependencyAnalysis(
                service_name=service_name,
                direct_dependencies=direct_deps,
                transitive_dependencies=transitive_deps,
                dependents=dependents,
                dependency_depth=depth,
                criticality_score=criticality,
                optimization_suggestions=suggestions,
                potential_issues=issues,
            )

            # 更新缓存
            self.analysis_cache[cache_key] = (analysis, time.time())

            logger.info(f"服务依赖分析完成: {service_name}")
            return analysis

        except Exception as e:
            logger.error(f"服务依赖分析失败 {service_name}: {str(e)}")
            raise DependencyResolutionError(f"依赖分析失败: {str(e)}")

    async def analyze_global_dependencies(self) -> DependencyGraphMetrics:
        """
        分析全局依赖关系

        Returns:
            DependencyGraphMetrics: 全局依赖指标
        """
        try:
            await self._build_dependency_graph()

            # 计算各种全局指标
            total_services = self.dependency_graph.number_of_nodes()
            total_dependencies = self.dependency_graph.number_of_edges()

            # 计算依赖深度
            depths = [
                await self._calculate_dependency_depth(node)
                for node in self.dependency_graph.nodes()
            ]
            max_depth = max(depths) if depths else 0
            avg_depth = sum(depths) / len(depths) if depths else 0

            # 检测循环依赖
            cycles = list(nx.simple_cycles(self.dependency_graph))

            # 强连通分量（包含循环）
            scc = list(nx.strongly_connected_components(self.dependency_graph))
            non_trivial_scc = [
                list(component) for component in scc if len(component) > 1
            ]

            # 关键服务（被很多服务依赖）
            in_degrees = dict(self.dependency_graph.in_degree())
            critical_services = [
                node
                for node, degree in in_degrees.items()
                if degree >= 3  # 被3个以上服务依赖
            ]

            # 叶子服务（不依赖其他服务）
            leaf_services = [
                node
                for node in self.dependency_graph.nodes()
                if self.dependency_graph.out_degree(node) == 0
            ]

            metrics = DependencyGraphMetrics(
                total_services=total_services,
                total_dependencies=total_dependencies,
                max_dependency_depth=max_depth,
                average_dependency_depth=avg_depth,
                cyclic_dependencies=cycles,
                strongly_connected_components=non_trivial_scc,
                critical_services=critical_services,
                leaf_services=leaf_services,
            )

            self.last_analysis_time = time.time()
            logger.info("全局依赖分析完成")
            return metrics

        except Exception as e:
            logger.error(f"全局依赖分析失败: {str(e)}")
            raise DependencyResolutionError(f"全局依赖分析失败: {str(e)}")

    async def optimize_dependency_structure(self) -> List[OptimizationRecommendation]:
        """
        优化依赖结构

        Returns:
            List[OptimizationRecommendation]: 优化建议列表
        """
        recommendations = []

        try:
            await self._build_dependency_graph()

            # 应用各种优化规则
            for rule_name, rule_func in self.optimization_rules.items():
                rule_recommendations = await rule_func()
                recommendations.extend(rule_recommendations)

            # 按优先级排序
            recommendations.sort(key=lambda x: (-x.priority, -x.expected_benefit))

            logger.info(f"生成 {len(recommendations)} 条依赖优化建议")
            return recommendations

        except Exception as e:
            logger.error(f"依赖结构优化失败: {str(e)}")
            return []

    async def validate_dependency_changes(
        self, service_name: str, new_dependencies: List[ServiceDependency]
    ) -> Dict[str, Any]:
        """
        验证依赖变更是否安全

        Args:
            service_name: 服务名称
            new_dependencies: 新的依赖列表

        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 创建临时图验证变更
            temp_graph = self.dependency_graph.copy()

            # 移除现有依赖
            if service_name in temp_graph:
                predecessors = list(temp_graph.predecessors(service_name))
                for pred in predecessors:
                    temp_graph.remove_edge(pred, service_name)

            # 添加新依赖
            for dependency in new_dependencies:
                temp_graph.add_edge(dependency.service_name, service_name)

            # 检查循环依赖
            try:
                cycles = list(nx.simple_cycles(temp_graph))
                has_cycles = len(cycles) > 0
            except Exception:
                has_cycles = True

            # 计算关键指标变化
            old_criticality = await self._calculate_criticality_score(service_name)
            new_criticality = await self._calculate_criticality_for_graph(
                temp_graph, service_name
            )

            # 检查依赖深度
            old_depth = await self._calculate_dependency_depth(service_name)
            new_depth = await self._calculate_depth_for_graph(temp_graph, service_name)

            return {
                "valid": not has_cycles,
                "cyclic_dependencies": cycles if has_cycles else [],
                "criticality_change": new_criticality - old_criticality,
                "depth_change": new_depth - old_depth,
                "risk_level": "high" if has_cycles else "low",
                "recommendations": await self._generate_change_recommendations(
                    service_name, new_dependencies, has_cycles
                ),
            }

        except Exception as e:
            logger.error(f"依赖变更验证失败 {service_name}: {str(e)}")
            return {"valid": False, "error": str(e), "risk_level": "high"}

    async def find_optimal_startup_sequence(self) -> List[str]:
        """
        寻找最优启动顺序

        Returns:
            List[str]: 最优启动顺序
        """
        try:
            await self._build_dependency_graph()

            # 使用拓扑排序
            try:
                topological_order = list(nx.topological_sort(self.dependency_graph))
                return topological_order
            except nx.NetworkXUnfeasible:
                # 有循环依赖，使用强连通分量分解
                scc = list(nx.strongly_connected_components(self.dependency_graph))
                condensed = nx.condensation(self.dependency_graph, scc)
                scc_order = list(nx.topological_sort(condensed))

                # 展开强连通分量
                optimal_order = []
                for scc_node in scc_order:
                    services_in_scc = list(scc[scc_node])
                    # 在强连通分量内，按依赖数排序
                    services_in_scc.sort(
                        key=lambda s: (
                            self.dependency_graph.in_degree(s),
                            self.dependency_graph.out_degree(s),
                        )
                    )
                    optimal_order.extend(services_in_scc)

                return optimal_order

        except Exception as e:
            logger.error(f"最优启动顺序计算失败: {str(e)}")
            # 返回基于依赖数的简单排序
            services_by_deps = sorted(
                self.dependency_graph.nodes(),
                key=lambda s: (
                    self.dependency_graph.in_degree(s),
                    self.dependency_graph.out_degree(s),
                ),
            )
            return services_by_deps

    async def detect_circular_dependencies(self) -> List[List[str]]:
        """
        检测循环依赖

        Returns:
            List[List[str]]: 循环依赖列表
        """
        try:
            await self._build_dependency_graph()
            cycles = list(nx.simple_cycles(self.dependency_graph))

            # 过滤掉自循环（单个节点的循环）
            meaningful_cycles = [cycle for cycle in cycles if len(cycle) > 1]

            logger.info(f"检测到 {len(meaningful_cycles)} 个循环依赖")
            return meaningful_cycles

        except Exception as e:
            logger.error(f"循环依赖检测失败: {str(e)}")
            return []

    async def break_circular_dependencies(
        self, cycle: List[str]
    ) -> List[OptimizationRecommendation]:
        """
        打破循环依赖

        Args:
            cycle: 循环依赖列表

        Returns:
            List[OptimizationRecommendation]: 打破循环的建议
        """
        recommendations = []

        try:
            if len(cycle) < 2:
                return recommendations

            # 分析循环中的服务
            cycle_analysis = []
            for service_name in cycle:
                deps_in_cycle = [
                    dep
                    for dep in self.dependency_graph.predecessors(service_name)
                    if dep in cycle
                ]
                cycle_analysis.append((service_name, len(deps_in_cycle)))

            # 找到依赖最少的服务作为突破口
            cycle_analysis.sort(key=lambda x: x[1])
            candidate_service = cycle_analysis[0][0]

            # 生成打破循环的建议
            recommendation = OptimizationRecommendation(
                type="dependency_break",
                description=f"打破循环依赖: 建议重构服务 {candidate_service} 的依赖关系",
                services_involved=cycle,
                expected_benefit=0.8,
                implementation_complexity=0.6,
                priority=5,  # 高优先级
            )
            recommendations.append(recommendation)

            # 其他可能的解决方案
            if len(cycle) == 2:
                # 对于双向依赖，建议提取接口
                rec = OptimizationRecommendation(
                    type="interface_extract",
                    description=f"提取公共接口以解耦双向依赖: {cycle[0]} <-> {cycle[1]}",
                    services_involved=cycle,
                    expected_benefit=0.7,
                    implementation_complexity=0.7,
                    priority=4,
                )
                recommendations.append(rec)

            logger.info(f"为循环依赖生成 {len(recommendations)} 条解决方案")
            return recommendations

        except Exception as e:
            logger.error(f"打破循环依赖失败: {str(e)}")
            return []

    # ========== 依赖图构建和分析 ==========

    async def _build_dependency_graph(self):
        """构建依赖图"""
        if not self.service_scheduler or not hasattr(
            self.service_scheduler, "services"
        ):
            logger.warning("服务调度器不可用，无法构建依赖图")
            return

        # 如果图已构建且服务没有变化，则跳过
        if self.dependency_graph.number_of_nodes() == len(
            self.service_scheduler.services
        ):
            return

        self.dependency_graph.clear()

        # 添加所有服务节点
        for service_name in self.service_scheduler.services:
            self.dependency_graph.add_node(service_name)

        # 添加依赖边
        for service_name, scheduled_service in self.service_scheduler.services.items():
            for dependency in scheduled_service.info.dependencies:
                if dependency.service_name in self.dependency_graph.nodes():
                    self.dependency_graph.add_edge(
                        dependency.service_name, service_name
                    )

        logger.debug(
            f"依赖图构建完成: {self.dependency_graph.number_of_nodes()} 节点, "
            f"{self.dependency_graph.number_of_edges()} 边"
        )

    async def _find_transitive_dependencies(self, service_name: str) -> List[str]:
        """查找传递依赖"""
        try:
            # 使用BFS查找所有传递依赖
            visited = set()
            queue = deque([service_name])
            transitive_deps = []

            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)

                # 添加直接依赖（排除自己）
                deps = list(self.dependency_graph.predecessors(current))
                for dep in deps:
                    if dep != service_name and dep not in visited:
                        transitive_deps.append(dep)
                        queue.append(dep)

            return list(set(transitive_deps))

        except Exception as e:
            logger.error(f"传递依赖查找失败 {service_name}: {str(e)}")
            return []

    async def _calculate_dependency_depth(self, service_name: str) -> int:
        """计算依赖深度"""
        try:
            # 找到最长的依赖路径长度
            if not list(self.dependency_graph.predecessors(service_name)):
                return 0  # 没有依赖

            # 使用BFS计算最长路径
            max_depth = 0
            visited = {service_name: 0}
            queue = deque([(service_name, 0)])

            while queue:
                current, depth = queue.popleft()
                max_depth = max(max_depth, depth)

                for predecessor in self.dependency_graph.predecessors(current):
                    if predecessor not in visited or visited[predecessor] < depth + 1:
                        visited[predecessor] = depth + 1
                        queue.append((predecessor, depth + 1))

            return max_depth

        except Exception as e:
            logger.error(f"依赖深度计算失败 {service_name}: {str(e)}")
            return 0

    async def _calculate_criticality_score(self, service_name: str) -> float:
        """计算服务关键性分数"""
        try:
            # 基于被依赖数量和类型计算关键性
            dependents = list(self.dependency_graph.successors(service_name))

            if not dependents:
                return 0.1  # 叶子服务关键性低

            # 计算强依赖数量
            strong_dependents = 0
            for dependent in dependents:
                service = self.service_scheduler.services.get(dependent)
                if service:
                    for dep in service.info.dependencies:
                        if (
                            dep.service_name == service_name
                            and dep.dependency_type == DependencyType.REQUIRED
                        ):
                            strong_dependents += 1
                            break

            criticality = min(1.0, strong_dependents / 10.0)  # 归一化
            return criticality

        except Exception as e:
            logger.error(f"关键性分数计算失败 {service_name}: {str(e)}")
            return 0.5

    # ========== 优化规则实现 ==========

    async def _detect_circular_dependencies(self) -> List[OptimizationRecommendation]:
        """检测循环依赖"""
        recommendations = []
        cycles = await self.detect_circular_dependencies()

        for cycle in cycles:
            cycle_recommendations = await self.break_circular_dependencies(cycle)
            recommendations.extend(cycle_recommendations)

        return recommendations

    async def _detect_long_dependency_chains(self) -> List[OptimizationRecommendation]:
        """检测长依赖链"""
        recommendations = []

        try:
            for service_name in self.dependency_graph.nodes():
                depth = await self._calculate_dependency_depth(service_name)
                if depth >= 5:  # 依赖链长度阈值
                    recommendation = OptimizationRecommendation(
                        type="dependency_break",
                        description=f"检测到长依赖链（深度 {depth}）: 建议重构服务 {service_name} 的依赖关系",
                        services_involved=[service_name],
                        expected_benefit=0.6,
                        implementation_complexity=0.5,
                        priority=3,
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"长依赖链检测失败: {str(e)}")
            return []

    async def _detect_bottleneck_services(self) -> List[OptimizationRecommendation]:
        """检测瓶颈服务"""
        recommendations = []

        try:
            # 找到被大量服务依赖的服务
            in_degrees = dict(self.dependency_graph.in_degree())
            high_dependency_services = [
                (service, degree)
                for service, degree in in_degrees.items()
                if degree >= 5  # 被5个以上服务依赖
            ]

            for service, degree in high_dependency_services:
                recommendation = OptimizationRecommendation(
                    type="service_merge",
                    description=f"检测到瓶颈服务 {service}（被 {degree} 个服务依赖）: 考虑功能拆分或服务合并",
                    services_involved=[service],
                    expected_benefit=0.7,
                    implementation_complexity=0.8,
                    priority=4,
                )
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"瓶颈服务检测失败: {str(e)}")
            return []

    async def _detect_over_coupling(self) -> List[OptimizationRecommendation]:
        """检测过度耦合"""
        recommendations = []

        try:
            for service_name in self.dependency_graph.nodes():
                # 计算耦合度（依赖数量 + 被依赖数量）
                coupling_degree = self.dependency_graph.in_degree(
                    service_name
                ) + self.dependency_graph.out_degree(service_name)

                if coupling_degree >= 8:  # 耦合度阈值
                    recommendation = OptimizationRecommendation(
                        type="interface_extract",
                        description=f"检测到过度耦合服务 {service_name}（耦合度 {coupling_degree}）: 建议提取接口或重构",
                        services_involved=[service_name],
                        expected_benefit=0.5,
                        implementation_complexity=0.7,
                        priority=3,
                    )
                    recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"过度耦合检测失败: {str(e)}")
            return []

    async def _detect_under_utilized_services(self) -> List[OptimizationRecommendation]:
        """检测低利用率服务"""
        recommendations = []

        try:
            # 找到很少被依赖的服务
            in_degrees = dict(self.dependency_graph.in_degree())
            low_usage_services = [
                service
                for service, degree in in_degrees.items()
                if degree <= 1 and self.dependency_graph.out_degree(service) > 2
            ]

            for service in low_usage_services:
                recommendation = OptimizationRecommendation(
                    type="service_merge",
                    description=f"检测到低利用率服务 {service}: 考虑合并到相关服务中",
                    services_involved=[service],
                    expected_benefit=0.4,
                    implementation_complexity=0.4,
                    priority=2,
                )
                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"低利用率服务检测失败: {str(e)}")
            return []

    # ========== 辅助方法 ==========

    async def _generate_optimization_suggestions(self, service_name: str) -> List[str]:
        """生成优化建议"""
        suggestions = []

        try:
            depth = await self._calculate_dependency_depth(service_name)
            if depth > 3:
                suggestions.append(f"依赖链较长（{depth}），考虑减少间接依赖")

            dependents = list(self.dependency_graph.successors(service_name))
            if len(dependents) > 5:
                suggestions.append(f"被 {len(dependents)} 个服务依赖，考虑功能拆分")

            # 检查是否有循环依赖风险
            cycles = await self.detect_circular_dependencies()
            involved_in_cycles = any(service_name in cycle for cycle in cycles)
            if involved_in_cycles:
                suggestions.append("涉及循环依赖，需要重构")

            return suggestions

        except Exception as e:
            logger.error(f"优化建议生成失败 {service_name}: {str(e)}")
            return []

    async def _detect_potential_issues(self, service_name: str) -> List[str]:
        """检测潜在问题"""
        issues = []

        try:
            # 检查单点故障风险
            dependents = list(self.dependency_graph.successors(service_name))
            required_dependents = 0
            for dependent in dependents:
                service = self.service_scheduler.services.get(dependent)
                if service:
                    for dep in service.info.dependencies:
                        if (
                            dep.service_name == service_name
                            and dep.dependency_type == DependencyType.REQUIRED
                        ):
                            required_dependents += 1
                            break

            if required_dependents >= 3:
                issues.append(f"单点故障风险: 被 {required_dependents} 个服务强依赖")

            # 检查依赖深度
            depth = await self._calculate_dependency_depth(service_name)
            if depth >= 4:
                issues.append(f"依赖深度较大（{depth}），可能影响启动性能")

            return issues

        except Exception as e:
            logger.error(f"潜在问题检测失败 {service_name}: {str(e)}")
            return []

    async def _calculate_criticality_for_graph(
        self, graph: nx.DiGraph, service_name: str
    ) -> float:
        """在指定图中计算服务关键性"""
        try:
            dependents = list(graph.successors(service_name))
            if not dependents:
                return 0.1

            # 简化计算：基于依赖数量
            return min(1.0, len(dependents) / 10.0)

        except Exception:
            return 0.5

    async def _calculate_depth_for_graph(
        self, graph: nx.DiGraph, service_name: str
    ) -> int:
        """在指定图中计算依赖深度"""
        try:
            if not list(graph.predecessors(service_name)):
                return 0

            max_depth = 0
            visited = {service_name: 0}
            queue = deque([(service_name, 0)])

            while queue:
                current, depth = queue.popleft()
                max_depth = max(max_depth, depth)

                for predecessor in graph.predecessors(current):
                    if predecessor not in visited or visited[predecessor] < depth + 1:
                        visited[predecessor] = depth + 1
                        queue.append((predecessor, depth + 1))

            return max_depth

        except Exception:
            return 0

    async def _generate_change_recommendations(
        self,
        service_name: str,
        new_dependencies: List[ServiceDependency],
        has_cycles: bool,
    ) -> List[str]:
        """生成变更建议"""
        recommendations = []

        if has_cycles:
            recommendations.append("变更引入循环依赖，需要重新设计依赖关系")

        # 分析依赖类型变化
        old_required_deps = 0
        new_required_deps = sum(
            1
            for dep in new_dependencies
            if dep.dependency_type == DependencyType.REQUIRED
        )

        if new_required_deps > old_required_deps:
            recommendations.append("强依赖数量增加，可能提高系统耦合度")
        elif new_required_deps < old_required_deps:
            recommendations.append("强依赖数量减少，有助于降低系统耦合度")

        return recommendations

    async def clear_cache(self):
        """清空分析缓存"""
        self.analysis_cache.clear()
        logger.info("依赖分析缓存已清空")


# 导出依赖智能分析类
__all__ = [
    "DependencyIntelligence",
    "DependencyAnalysis",
    "DependencyGraphMetrics",
    "OptimizationRecommendation",
]
