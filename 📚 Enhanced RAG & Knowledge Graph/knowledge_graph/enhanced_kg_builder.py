"""
Enhanced Knowledge Graph Builder
增强的知识图谱构建器

根据需求1.8：优化知识图谱构建功能

功能：
1. 实体提取增强
2. 关系抽取优化
3. 图谱结构优化
4. 增量构建
5. 质量评估
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
from urllib.parse import urlparse
import email.utils

logger = logging.getLogger(__name__)


class EnhancedKGBuilder:
    """
    增强的知识图谱构建器
    
    提供更强大的实体提取和关系抽取能力
    """

    def __init__(self):
        """初始化构建器"""
        # 实体提取模式
        self.entity_patterns = {
            "email": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            "url": re.compile(
                r'https?://[^\s<>"{}|\\^`\[\]]+',
                re.IGNORECASE
            ),
            "phone": re.compile(
                r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),
            "ip_address": re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
            "date": re.compile(
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
            ),
        }

        # 关系提取模式
        self.relation_patterns = [
            (r"([^。！？]+)(属于|包含|位于|来自|联系)([^。！？]+)", "belongs_to"),
            (r"([^。！？]+)(联系|联系人是|邮箱是)([^。！？]+)", "contact"),
            (r"([^。！？]+)(访问|浏览|查看)([^。！？]+)", "accesses"),
        ]

    def extract_entities(self, text: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        从文本中提取实体
        
        Args:
            text: 文本内容
            doc_id: 文档ID
            
        Returns:
            实体列表
        """
        entities = []

        # 提取各种类型的实体
        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                value = match.group(0)
                start_pos = match.start()
                end_pos = match.end()

                # 验证实体（某些类型需要额外验证）
                if self._validate_entity(entity_type, value):
                    entity = {
                        "type": entity_type,
                        "value": value,
                        "doc_id": doc_id,
                        "position": (start_pos, end_pos),
                        "confidence": 0.9,  # 正则匹配的高置信度
                    }
                    entities.append(entity)

        return entities

    def _validate_entity(self, entity_type: str, value: str) -> bool:
        """
        验证实体值的有效性
        
        Args:
            entity_type: 实体类型
            value: 实体值
            
        Returns:
            是否有效
        """
        if entity_type == "email":
            try:
                email.utils.parseaddr(value)
                return "@" in value and "." in value.split("@")[1]
            except:
                return False

        elif entity_type == "url":
            try:
                result = urlparse(value)
                return all([result.scheme, result.netloc])
            except:
                return False

        elif entity_type == "phone":
            # 简单验证：至少包含7位数字
            digits = sum(c.isdigit() for c in value)
            return digits >= 7

        elif entity_type == "ip_address":
            parts = value.split(".")
            if len(parts) != 4:
                return False
            try:
                return all(0 <= int(p) <= 255 for p in parts)
            except:
                return False

        return True

    def extract_relations(
        self, text: str, entities: List[Dict[str, Any]], doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        从文本中提取实体间的关系（增强版）
        
        增加关系强度量化
        """
        """
        从文本中提取实体间的关系
        
        Args:
            text: 文本内容
            entities: 已提取的实体列表
            doc_id: 文档ID
            
        Returns:
            关系列表
        """
        relations = []

        # 提取显式关系（基于模式）
        for pattern, relation_type in self.relation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                source_text = match.group(1).strip()
                relation_word = match.group(2)
                target_text = match.group(3).strip()

                # 查找匹配的实体
                source_entity = self._find_matching_entity(source_text, entities)
                target_entity = self._find_matching_entity(target_text, entities)

                if source_entity and target_entity:
                    # 计算关系强度
                    strength = self._calculate_relation_strength(
                        relation_type, source_text, target_text, text
                    )
                    
                    relation = {
                        "source": source_entity["value"],
                        "source_type": source_entity["type"],
                        "target": target_entity["value"],
                        "target_type": target_entity["type"],
                        "type": relation_type,
                        "doc_id": doc_id,
                        "confidence": 0.7,
                        "strength": strength,  # 新增：关系强度
                    }
                    relations.append(relation)

        # 提取共现关系（出现在同一句子或段落中的实体）
        cooccurrence_relations = self._extract_cooccurrence_relations(
            text, entities, doc_id
        )
        relations.extend(cooccurrence_relations)

        return relations

    def _find_matching_entity(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        查找匹配文本的实体
        
        Args:
            text: 文本片段
            entities: 实体列表
            
        Returns:
            匹配的实体或None
        """
        text_lower = text.lower()
        for entity in entities:
            entity_value = entity.get("value", "").lower()
            if entity_value in text_lower or text_lower in entity_value:
                return entity
        return None

    def _extract_cooccurrence_relations(
        self, text: str, entities: List[Dict[str, Any]], doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        提取共现关系（出现在同一段落的实体）
        
        Args:
            text: 文本内容
            entities: 实体列表
            doc_id: 文档ID
            
        Returns:
            关系列表
        """
        relations = []
        
        # 按段落分割
        paragraphs = text.split("\n\n")
        
        for para in paragraphs:
            # 找到出现在这个段落中的实体
            para_entities = []
            for entity in entities:
                entity_value = entity.get("value", "")
                if entity_value in para:
                    para_entities.append(entity)
            
            # 为同一段落中的实体对创建共现关系
            for i, entity1 in enumerate(para_entities):
                for entity2 in para_entities[i + 1:]:
                    # 计算共现关系强度（基于距离）
                    distance = abs(
                        para.find(entity1["value"]) - para.find(entity2["value"])
                    )
                    strength = max(0.3, 0.8 - (distance / 100))  # 距离越近强度越高
                    
                    relation = {
                        "source": entity1["value"],
                        "source_type": entity1["type"],
                        "target": entity2["value"],
                        "target_type": entity2["type"],
                        "type": "cooccurrence",
                        "doc_id": doc_id,
                        "confidence": 0.5,  # 共现关系置信度较低
                        "strength": strength,  # 新增：关系强度
                    }
                    relations.append(relation)
        
        return relations

    def build_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        构建知识图谱结构
        
        Args:
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            知识图谱数据
        """
        # 统计实体
        entity_stats = defaultdict(int)
        for entity in entities:
            entity_type = entity.get("type", "unknown")
            entity_stats[entity_type] += 1

        # 统计关系
        relation_stats = defaultdict(int)
        for relation in relations:
            relation_type = relation.get("type", "unknown")
            relation_stats[relation_type] += 1

        return {
            "entities": entities,
            "relations": relations,
            "stats": {
                "total_entities": len(entities),
                "entity_types": dict(entity_stats),
                "total_relations": len(relations),
                "relation_types": dict(relation_stats),
            },
        }


# 全局构建器实例
_kg_builder: Optional[EnhancedKGBuilder] = None


def get_kg_builder() -> EnhancedKGBuilder:
    """获取知识图谱构建器实例（单例）"""
    global _kg_builder
    if _kg_builder is None:
        _kg_builder = EnhancedKGBuilder()
    return _kg_builder

