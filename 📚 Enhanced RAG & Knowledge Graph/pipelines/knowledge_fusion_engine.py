#!/usr/bin/env python3
"""
知识融合引擎 - RAG多源知识智能融合
功能：融合来自不同来源的知识，解决冲突，生成统一知识表示
版本：1.0.0
"""

import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """冲突解决策略枚举"""

    MAJORITY_VOTE = "majority_vote"
    SOURCE_RELIABILITY = "source_reliability"
    TEMPORAL_RECENCY = "temporal_recency"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    EXPERT_CONSENSUS = "expert_consensus"


class FusionLevel(Enum):
    """融合级别枚举"""

    ENTITY_LEVEL = "entity_level"
    FACT_LEVEL = "fact_level"
    DOCUMENT_LEVEL = "document_level"
    KNOWLEDGE_GRAPH_LEVEL = "knowledge_graph_level"


@dataclass
class KnowledgePiece:
    """知识片段数据结构"""

    id: str
    content: str
    source: str
    source_reliability: float
    timestamp: datetime
    confidence: float
    entities: List[str]
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


@dataclass
class FusedKnowledge:
    """融合后的知识结构"""

    id: str
    content: str
    supporting_sources: List[str]
    confidence_score: float
    resolution_strategy: str
    fused_metadata: Dict[str, Any]
    entities: List[str]
    creation_time: datetime


@dataclass
class ConflictInfo:
    """冲突信息"""

    conflicting_pieces: List[KnowledgePiece]
    conflict_type: str
    severity: float
    resolution_suggestion: str


class KnowledgeFusionEngine:
    """
    知识融合引擎 - 多源知识智能融合与冲突解决
    支持多种融合策略和冲突解决机制
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conflict_resolvers = {}
        self.fusion_strategies = {}
        self.source_reliability_scores = {}
        self._initialize_engine()

        logger.info("知识融合引擎初始化完成")

    def _initialize_engine(self):
        """初始化引擎组件"""
        # 初始化冲突解决器
        self._initialize_conflict_resolvers()

        # 初始化融合策略
        self._initialize_fusion_strategies()

        # 加载源可靠性数据
        self._load_source_reliability()

        # 初始化缓存
        self.fusion_cache = {}
        self.conflict_history = {}

    def _initialize_conflict_resolvers(self):
        """初始化冲突解决器"""
        self.conflict_resolvers = {
            ConflictResolutionStrategy.MAJORITY_VOTE: self._resolve_by_majority_vote,
            ConflictResolutionStrategy.SOURCE_RELIABILITY: self._resolve_by_source_reliability,
            ConflictResolutionStrategy.TEMPORAL_RECENCY: self._resolve_by_temporal_recency,
            ConflictResolutionStrategy.CONFIDENCE_WEIGHTED: self._resolve_by_confidence_weighted,
            ConflictResolutionStrategy.EXPERT_CONSENSUS: self._resolve_by_expert_consensus,
        }

    def _initialize_fusion_strategies(self):
        """初始化融合策略"""
        self.fusion_strategies = {
            FusionLevel.ENTITY_LEVEL: self._fuse_at_entity_level,
            FusionLevel.FACT_LEVEL: self._fuse_at_fact_level,
            FusionLevel.DOCUMENT_LEVEL: self._fuse_at_document_level,
            FusionLevel.KNOWLEDGE_GRAPH_LEVEL: self._fuse_at_knowledge_graph_level,
        }

    def _load_source_reliability(self):
        """加载源可靠性数据"""
        # 从配置或外部存储加载源可靠性分数
        default_scores = self.config.get("source_reliability", {})
        self.source_reliability_scores = defaultdict(lambda: 0.5, default_scores)

    async def fuse_knowledge(
        self,
        knowledge_pieces: List[KnowledgePiece],
        fusion_level: FusionLevel = FusionLevel.FACT_LEVEL,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.CONFIDENCE_WEIGHTED,
    ) -> Tuple[List[FusedKnowledge], List[ConflictInfo]]:
        """
        融合知识片段 - 主要入口方法

        Args:
            knowledge_pieces: 知识片段列表
            fusion_level: 融合级别
            conflict_strategy: 冲突解决策略

        Returns:
            融合后的知识列表和冲突信息列表
        """
        if not knowledge_pieces:
            logger.warning("输入知识片段为空")
            return [], []

        logger.info(
            f"开始融合 {len(knowledge_pieces)} 个知识片段，级别: {fusion_level}"
        )

        try:
            # 步骤1: 知识分组
            knowledge_groups = await self._group_knowledge_pieces(
                knowledge_pieces, fusion_level
            )

            # 步骤2: 组内融合
            fused_knowledge_list = []
            all_conflicts = []

            for group_id, group_pieces in knowledge_groups.items():
                fused_knowledge, conflicts = await self._fuse_knowledge_group(
                    group_pieces, fusion_level, conflict_strategy
                )
                fused_knowledge_list.extend(fused_knowledge)
                all_conflicts.extend(conflicts)

            # 步骤3: 后处理优化
            optimized_knowledge = await self._post_process_fusion(fused_knowledge_list)

            logger.info(
                f"融合完成，生成 {len(optimized_knowledge)} 个融合知识，发现 {len(all_conflicts)} 个冲突"
            )
            return optimized_knowledge, all_conflicts

        except Exception as e:
            logger.error(f"知识融合失败: {e}")
            raise

    async def _group_knowledge_pieces(
        self, pieces: List[KnowledgePiece], fusion_level: FusionLevel
    ) -> Dict[str, List[KnowledgePiece]]:
        """根据融合级别对知识片段进行分组"""
        groups = defaultdict(list)

        if fusion_level == FusionLevel.ENTITY_LEVEL:
            # 基于实体进行分组
            for piece in pieces:
                for entity in piece.entities:
                    groups[entity].append(piece)

        elif fusion_level == FusionLevel.FACT_LEVEL:
            # 基于内容相似度进行分组
            content_groups = await self._group_by_content_similarity(pieces)
            for i, group_pieces in enumerate(content_groups):
                groups[f"fact_group_{i}"] = group_pieces

        elif fusion_level == FusionLevel.DOCUMENT_LEVEL:
            # 基于源文档进行分组
            for piece in pieces:
                groups[piece.source].append(piece)

        elif fusion_level == FusionLevel.KNOWLEDGE_GRAPH_LEVEL:
            # 基于知识图谱结构进行分组
            kg_groups = await self._group_by_knowledge_graph(pieces)
            groups.update(kg_groups)

        # 过滤过小的分组
        filtered_groups = {
            group_id: group_pieces
            for group_id, group_pieces in groups.items()
            if len(group_pieces) >= self.config.get("min_group_size", 1)
        }

        return filtered_groups

    async def _group_by_content_similarity(
        self, pieces: List[KnowledgePiece]
    ) -> List[List[KnowledgePiece]]:
        """基于内容相似度分组"""
        if len(pieces) <= 1:
            return [pieces]

        # 使用嵌入向量进行聚类
        from sklearn.cluster import DBSCAN

        embeddings = []
        valid_pieces = []

        for piece in pieces:
            if piece.embedding is not None:
                embeddings.append(piece.embedding)
                valid_pieces.append(piece)

        if not embeddings:
            return [pieces]

        # DBSCAN聚类
        clustering = DBSCAN(
            eps=self.config.get("clustering_epsilon", 0.5),
            min_samples=self.config.get("min_cluster_samples", 2),
        )

        labels = clustering.fit_predict(embeddings)

        # 构建分组
        groups_dict = defaultdict(list)
        for piece, label in zip(valid_pieces, labels):
            if label != -1:  # 忽略噪声点
                groups_dict[label].append(piece)

        # 将噪声点各自作为独立分组
        for i, piece in enumerate(valid_pieces):
            if labels[i] == -1:
                groups_dict[f"noise_{i}"] = [piece]

        return list(groups_dict.values())

    async def _group_by_knowledge_graph(
        self, pieces: List[KnowledgePiece]
    ) -> Dict[str, List[KnowledgePiece]]:
        """基于知识图谱结构分组"""
        # 这里可以集成实际的知识图谱服务
        # 当前使用基于实体的简化分组

        entity_groups = defaultdict(list)
        for piece in pieces:
            # 使用第一个实体作为分组键
            if piece.entities:
                primary_entity = piece.entities[0]
                entity_groups[primary_entity].append(piece)
            else:
                # 没有实体的片段放入单独分组
                entity_groups["no_entity"].append(piece)

        return dict(entity_groups)

    async def _fuse_knowledge_group(
        self,
        group_pieces: List[KnowledgePiece],
        fusion_level: FusionLevel,
        conflict_strategy: ConflictResolutionStrategy,
    ) -> Tuple[List[FusedKnowledge], List[ConflictInfo]]:
        """融合单个知识分组"""
        if not group_pieces:
            return [], []

        if len(group_pieces) == 1:
            # 单一片段，直接转换
            single_piece = group_pieces[0]
            fused_knowledge = FusedKnowledge(
                id=self._generate_fusion_id([single_piece]),
                content=single_piece.content,
                supporting_sources=[single_piece.source],
                confidence_score=single_piece.confidence,
                resolution_strategy="single_source",
                fused_metadata=single_piece.metadata,
                entities=single_piece.entities,
                creation_time=datetime.now(),
            )
            return [fused_knowledge], []

        # 检测冲突
        conflicts = await self._detect_conflicts(group_pieces, fusion_level)

        # 应用融合策略
        fusion_strategy = self.fusion_strategies.get(fusion_level)
        if not fusion_strategy:
            logger.warning(f"未找到融合策略: {fusion_level}")
            return [], conflicts

        fused_results = await fusion_strategy(
            group_pieces, conflict_strategy, conflicts
        )

        return fused_results, conflicts

    async def _detect_conflicts(
        self, pieces: List[KnowledgePiece], fusion_level: FusionLevel
    ) -> List[ConflictInfo]:
        """检测知识冲突"""
        conflicts = []

        if fusion_level == FusionLevel.FACT_LEVEL:
            # 事实级别的冲突检测
            conflicts.extend(await self._detect_factual_conflicts(pieces))

        elif fusion_level == FusionLevel.ENTITY_LEVEL:
            # 实体级别的冲突检测
            conflicts.extend(await self._detect_entity_conflicts(pieces))

        # 时间一致性冲突检测
        conflicts.extend(await self._detect_temporal_conflicts(pieces))

        # 数值冲突检测
        conflicts.extend(await self._detect_numerical_conflicts(pieces))

        return conflicts

    async def _detect_factual_conflicts(
        self, pieces: List[KnowledgePiece]
    ) -> List[ConflictInfo]:
        """检测事实冲突"""
        conflicts = []

        # 基于语义相似度和内容矛盾性检测冲突
        from sentence_transformers import util

        # 提取关键事实陈述
        factual_statements = await self._extract_factual_statements(pieces)

        for i, (stmt1, piece1) in enumerate(factual_statements):
            for j, (stmt2, piece2) in enumerate(factual_statements[i + 1 :], i + 1):
                similarity = (
                    util.cos_sim(piece1.embedding, piece2.embedding).item()
                    if piece1.embedding is not None and piece2.embedding is not None
                    else 0
                )

                contradiction_score = await self._calculate_contradiction_score(
                    stmt1, stmt2
                )

                if similarity > 0.7 and contradiction_score > 0.6:
                    conflict = ConflictInfo(
                        conflicting_pieces=[piece1, piece2],
                        conflict_type="factual_contradiction",
                        severity=contradiction_score,
                        resolution_suggestion="使用源可靠性加权平均",
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _extract_factual_statements(
        self, pieces: List[KnowledgePiece]
    ) -> List[Tuple[str, KnowledgePiece]]:
        """提取事实陈述"""
        # 这里可以集成NLP模型进行事实提取
        # 当前返回原始内容作为事实陈述
        return [(piece.content, piece) for piece in pieces]

    async def _calculate_contradiction_score(self, text1: str, text2: str) -> float:
        """计算文本矛盾性分数"""
        # 这里可以集成矛盾检测模型
        # 当前使用基于关键词的简单检测

        contradiction_keywords = ["不是", "没有", "错误", "不", "反对", "否认"]
        support_keywords = ["是", "有", "正确", "支持", "确认"]

        score = 0.0

        # 简单的关键词匹配
        for keyword in contradiction_keywords:
            if keyword in text1 and keyword not in text2:
                score += 0.2
            if keyword in text2 and keyword not in text1:
                score += 0.2

        return min(score, 1.0)

    async def _detect_entity_conflicts(
        self, pieces: List[KnowledgePiece]
    ) -> List[ConflictInfo]:
        """检测实体冲突"""
        conflicts = []

        # 检测实体属性冲突
        entity_attributes = defaultdict(dict)

        for piece in pieces:
            for entity in piece.entities:
                # 提取实体属性（简化处理）
                attributes = await self._extract_entity_attributes(
                    piece.content, entity
                )
                for attr_name, attr_value in attributes.items():
                    if attr_name in entity_attributes[entity]:
                        existing_value = entity_attributes[entity][attr_name]
                        if existing_value != attr_value:
                            conflict = ConflictInfo(
                                conflicting_pieces=[piece],
                                conflict_type="entity_attribute_conflict",
                                severity=0.5,
                                resolution_suggestion=f"实体 {entity} 属性 {attr_name} 冲突: {existing_value} vs {attr_value}",
                            )
                            conflicts.append(conflict)
                    else:
                        entity_attributes[entity][attr_name] = attr_value

        return conflicts

    async def _extract_entity_attributes(
        self, text: str, entity: str
    ) -> Dict[str, str]:
        """提取实体属性"""
        # 这里可以集成实体属性提取模型
        # 当前返回空字典
        return {}

    async def _detect_temporal_conflicts(
        self, pieces: List[KnowledgePiece]
    ) -> List[ConflictInfo]:
        """检测时间冲突"""
        conflicts = []

        # 按时间排序
        sorted_pieces = sorted(pieces, key=lambda x: x.timestamp)

        # 检测时间顺序矛盾
        for i in range(1, len(sorted_pieces)):
            time_diff = (
                sorted_pieces[i].timestamp - sorted_pieces[i - 1].timestamp
            ).total_seconds()

            # 如果时间戳差异很大但内容相似，可能有时序冲突
            if time_diff > 86400:  # 1天
                content_similarity = await self._calculate_content_similarity(
                    sorted_pieces[i].content, sorted_pieces[i - 1].content
                )

                if content_similarity > 0.8:
                    conflict = ConflictInfo(
                        conflicting_pieces=[sorted_pieces[i - 1], sorted_pieces[i]],
                        conflict_type="temporal_inconsistency",
                        severity=0.3,
                        resolution_suggestion="使用最新时间戳的信息",
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _detect_numerical_conflicts(
        self, pieces: List[KnowledgePiece]
    ) -> List[ConflictInfo]:
        """检测数值冲突"""
        conflicts = []

        # 提取数值信息并比较
        numerical_data = defaultdict(list)

        for piece in pieces:
            numbers = await self._extract_numbers(piece.content)
            for number in numbers:
                numerical_data[number["context"]].append(
                    {
                        "value": number["value"],
                        "piece": piece,
                        "unit": number.get("unit", ""),
                    }
                )

        # 检测数值冲突
        for context, numbers in numerical_data.items():
            if len(numbers) > 1:
                values = [n["value"] for n in numbers]
                if max(values) - min(values) > np.mean(values) * 0.5:  # 差异超过50%
                    conflict = ConflictInfo(
                        conflicting_pieces=[n["piece"] for n in numbers],
                        conflict_type="numerical_discrepancy",
                        severity=0.7,
                        resolution_suggestion=f"数值 {context} 存在较大差异: {min(values)} - {max(values)}",
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _extract_numbers(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取数值信息"""
        import re

        numbers = []

        # 匹配数字模式
        number_patterns = [
            r"\d+\.?\d*",  # 整数和小数
        ]

        for pattern in number_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    value = float(match.group())
                    # 获取数值上下文
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end].strip()

                    numbers.append(
                        {
                            "value": value,
                            "context": context,
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )
                except ValueError:
                    continue

        return numbers

    async def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """计算内容相似度"""
        # 这里可以集成更复杂的相似度计算
        # 当前使用简单的Jaccard相似度

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union

    async def _fuse_at_fact_level(
        self,
        pieces: List[KnowledgePiece],
        conflict_strategy: ConflictResolutionStrategy,
        conflicts: List[ConflictInfo],
    ) -> List[FusedKnowledge]:
        """事实级别融合"""
        resolver = self.conflict_resolvers.get(conflict_strategy)
        if not resolver:
            logger.warning(f"未找到冲突解决器: {conflict_strategy}")
            return []

        # 应用冲突解决
        resolved_content, resolution_info = await resolver(pieces, conflicts)

        # 构建融合知识
        fused_knowledge = FusedKnowledge(
            id=self._generate_fusion_id(pieces),
            content=resolved_content,
            supporting_sources=[piece.source for piece in pieces],
            confidence_score=await self._calculate_fusion_confidence(pieces),
            resolution_strategy=conflict_strategy.value,
            fused_metadata=await self._fuse_metadata(pieces),
            entities=await self._fuse_entities(pieces),
            creation_time=datetime.now(),
        )

        return [fused_knowledge]

    async def _resolve_by_confidence_weighted(
        self, pieces: List[KnowledgePiece], conflicts: List[ConflictInfo]
    ) -> Tuple[str, Dict[str, Any]]:
        """基于置信度加权的冲突解决"""
        # 计算加权平均内容（简化处理）
        total_confidence = sum(piece.confidence for piece in pieces)

        if total_confidence == 0:
            # 使用最新内容
            latest_piece = max(pieces, key=lambda x: x.timestamp)
            return latest_piece.content, {"method": "latest_content"}

        # 选择置信度最高的内容
        best_piece = max(pieces, key=lambda x: x.confidence)
        return best_piece.content, {"method": "highest_confidence"}

    async def _resolve_by_majority_vote(
        self, pieces: List[KnowledgePiece], conflicts: List[ConflictInfo]
    ) -> Tuple[str, Dict[str, Any]]:
        """基于多数投票的冲突解决"""
        # 按内容分组统计
        content_groups = defaultdict(list)
        for piece in pieces:
            content_groups[piece.content].append(piece)

        # 选择最多的内容
        most_common_content = max(content_groups.items(), key=lambda x: len(x[1]))
        return most_common_content[0], {
            "method": "majority_vote",
            "vote_count": len(most_common_content[1]),
            "total_votes": len(pieces),
        }

    async def _resolve_by_source_reliability(
        self, pieces: List[KnowledgePiece], conflicts: List[ConflictInfo]
    ) -> Tuple[str, Dict[str, Any]]:
        """基于源可靠性的冲突解决"""
        # 计算源可靠性加权
        source_scores = []
        for piece in pieces:
            reliability = self.source_reliability_scores[piece.source]
            weighted_score = reliability * piece.confidence
            source_scores.append((piece, weighted_score))

        # 选择加权分数最高的内容
        best_piece = max(source_scores, key=lambda x: x[1])[0]
        return best_piece.content, {
            "method": "source_reliability",
            "best_source": best_piece.source,
            "reliability_score": self.source_reliability_scores[best_piece.source],
        }

    async def _resolve_by_temporal_recency(
        self, pieces: List[KnowledgePiece], conflicts: List[ConflictInfo]
    ) -> Tuple[str, Dict[str, Any]]:
        """基于时间新近度的冲突解决"""
        # 选择最新的内容
        latest_piece = max(pieces, key=lambda x: x.timestamp)
        return latest_piece.content, {
            "method": "temporal_recency",
            "latest_timestamp": latest_piece.timestamp.isoformat(),
        }

    async def _resolve_by_expert_consensus(
        self, pieces: List[KnowledgePiece], conflicts: List[ConflictInfo]
    ) -> Tuple[str, Dict[str, Any]]:
        """基于专家共识的冲突解决"""
        # 这里可以集成专家系统或规则引擎
        # 当前使用置信度和源可靠性的组合

        combined_scores = []
        for piece in pieces:
            reliability = self.source_reliability_scores[piece.source]
            time_factor = await self._calculate_time_factor(piece.timestamp)
            combined_score = piece.confidence * reliability * time_factor
            combined_scores.append((piece, combined_score))

        best_piece = max(combined_scores, key=lambda x: x[1])[0]
        return best_piece.content, {
            "method": "expert_consensus",
            "combined_score": max(combined_scores, key=lambda x: x[1])[1],
        }

    async def _calculate_time_factor(self, timestamp: datetime) -> float:
        """计算时间因子"""
        now = datetime.now()
        time_diff = (now - timestamp).total_seconds()

        # 时间衰减因子：越近的信息权重越高
        decay_days = self.config.get("temporal_decay_days", 30)
        time_factor = max(0.1, 1 - (time_diff / (decay_days * 86400)))

        return time_factor

    async def _calculate_fusion_confidence(self, pieces: List[KnowledgePiece]) -> float:
        """计算融合置信度"""
        if not pieces:
            return 0.0

        # 基于源可靠性、个体置信度和一致性计算
        reliabilities = [
            self.source_reliability_scores[piece.source] for piece in pieces
        ]
        confidences = [piece.confidence for piece in pieces]

        avg_reliability = np.mean(reliabilities)
        avg_confidence = np.mean(confidences)

        # 计算内容一致性
        consistency_score = await self._calculate_consistency_score(pieces)

        fusion_confidence = (avg_reliability + avg_confidence + consistency_score) / 3
        return float(fusion_confidence)

    async def _calculate_consistency_score(self, pieces: List[KnowledgePiece]) -> float:
        """计算一致性分数"""
        if len(pieces) <= 1:
            return 1.0

        # 基于内容相似度计算一致性
        similarities = []
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                similarity = await self._calculate_content_similarity(
                    pieces[i].content, pieces[j].content
                )
                similarities.append(similarity)

        return float(np.mean(similarities)) if similarities else 0.5

    async def _fuse_metadata(self, pieces: List[KnowledgePiece]) -> Dict[str, Any]:
        """融合元数据"""
        fused_metadata = {
            "source_count": len(pieces),
            "sources": [piece.source for piece in pieces],
            "timestamp_range": {
                "min": min(piece.timestamp for piece in pieces).isoformat(),
                "max": max(piece.timestamp for piece in pieces).isoformat(),
            },
            "confidence_scores": [piece.confidence for piece in pieces],
        }

        # 合并其他元数据字段
        all_keys = set()
        for piece in pieces:
            all_keys.update(piece.metadata.keys())

        for key in all_keys:
            values = [
                piece.metadata.get(key) for piece in pieces if key in piece.metadata
            ]
            if values:
                # 选择最常见的值或合并值
                if all(v == values[0] for v in values):
                    fused_metadata[key] = values[0]
                else:
                    fused_metadata[f"{key}_sources"] = values

        return fused_metadata

    async def _fuse_entities(self, pieces: List[KnowledgePiece]) -> List[str]:
        """融合实体"""
        all_entities = []
        for piece in pieces:
            all_entities.extend(piece.entities)

        # 去重并排序
        return sorted(list(set(all_entities)))

    async def _fuse_at_entity_level(self, *args, **kwargs):
        """实体级别融合"""
        # 实现实体级别融合逻辑
        return await self._fuse_at_fact_level(*args, **kwargs)

    async def _fuse_at_document_level(self, *args, **kwargs):
        """文档级别融合"""
        # 实现文档级别融合逻辑
        return await self._fuse_at_fact_level(*args, **kwargs)

    async def _fuse_at_knowledge_graph_level(self, *args, **kwargs):
        """知识图谱级别融合"""
        # 实现知识图谱级别融合逻辑
        return await self._fuse_at_fact_level(*args, **kwargs)

    async def _post_process_fusion(
        self, fused_knowledge_list: List[FusedKnowledge]
    ) -> List[FusedKnowledge]:
        """后处理融合结果"""
        # 过滤低置信度的融合结果
        min_confidence = self.config.get("min_fusion_confidence", 0.3)
        filtered = [
            knowledge
            for knowledge in fused_knowledge_list
            if knowledge.confidence_score >= min_confidence
        ]

        # 按置信度排序
        filtered.sort(key=lambda x: x.confidence_score, reverse=True)

        return filtered

    def _generate_fusion_id(self, pieces: List[KnowledgePiece]) -> str:
        """生成融合ID"""
        piece_ids = sorted([piece.id for piece in pieces])
        id_string = "_".join(piece_ids)

        # 使用哈希生成唯一ID
        hash_object = hashlib.md5(id_string.encode())
        return f"fused_{hash_object.hexdigest()[:12]}"

    def update_source_reliability(self, source: str, reliability: float):
        """更新源可靠性分数"""
        self.source_reliability_scores[source] = max(0.0, min(1.0, reliability))
        logger.info(f"更新源可靠性: {source} -> {reliability}")

    def get_engine_metrics(self) -> Dict[str, Any]:
        """获取引擎性能指标"""
        return {
            "active_resolvers": [
                str(resolver) for resolver in self.conflict_resolvers.keys()
            ],
            "source_count": len(self.source_reliability_scores),
            "fusion_cache_size": len(self.fusion_cache),
            "status": "active",
        }


# 工厂函数
async def create_knowledge_fusion_engine(
    config: Dict[str, Any],
) -> KnowledgeFusionEngine:
    """创建知识融合引擎实例"""
    return KnowledgeFusionEngine(config)


if __name__ == "__main__":
    # 测试代码
    async def test_fusion_engine():
        config = {
            "source_reliability": {"source_a": 0.9, "source_b": 0.7, "source_c": 0.8},
            "min_fusion_confidence": 0.5,
            "temporal_decay_days": 30,
        }

        engine = KnowledgeFusionEngine(config)

        # 创建测试数据
        test_pieces = [
            KnowledgePiece(
                id=f"piece_{i}",
                content=f"测试知识内容 {i}",
                source=f"source_{chr(97 + i)}",  # a, b, c
                source_reliability=0.8,
                timestamp=datetime.now(),
                confidence=0.9,
                entities=[f"entity_{i}"],
                metadata={"test": True},
            )
            for i in range(3)
        ]

        fused_knowledge, conflicts = await engine.fuse_knowledge(test_pieces)
        print(f"生成 {len(fused_knowledge)} 个融合知识，发现 {len(conflicts)} 个冲突")

    asyncio.run(test_fusion_engine())
