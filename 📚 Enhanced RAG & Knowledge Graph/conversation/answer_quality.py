"""
答案质量评分
Answer Quality Scoring

功能：
1. 多维度质量评估
2. 实时评分反馈
3. 低分答案告警
4. 质量改进建议

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityScore:
    """质量评分结果"""
    
    def __init__(
        self,
        relevance: float,
        completeness: float,
        confidence: float,
        clarity: float,
        overall: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化质量评分
        
        Args:
            relevance: 相关性（0-1）
            completeness: 完整性（0-1）
            confidence: 置信度（0-1）
            clarity: 清晰度（0-1）
            overall: 总体得分（0-1）
            details: 详细信息
        """
        self.relevance = relevance
        self.completeness = completeness
        self.confidence = confidence
        self.clarity = clarity
        self.overall = overall
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "relevance": self.relevance,
            "completeness": self.completeness,
            "confidence": self.confidence,
            "clarity": self.clarity,
            "overall": self.overall,
            "grade": self.get_grade(),
            "details": self.details
        }
    
    def get_grade(self) -> str:
        """获取等级评价"""
        if self.overall >= 0.9:
            return "优秀"
        elif self.overall >= 0.8:
            return "良好"
        elif self.overall >= 0.7:
            return "中等"
        elif self.overall >= 0.6:
            return "及格"
        else:
            return "待改进"
    
    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """是否高质量"""
        return self.overall >= threshold
    
    def get_warnings(self) -> List[str]:
        """获取质量警告"""
        warnings = []
        
        if self.relevance < 0.7:
            warnings.append("相关性较低，可能答非所问")
        if self.completeness < 0.7:
            warnings.append("回答不够完整，建议补充信息")
        if self.confidence < 0.7:
            warnings.append("置信度较低，建议核实答案")
        if self.clarity < 0.7:
            warnings.append("表达不够清晰，建议重新组织")
        
        return warnings


class AnswerQualityScorer:
    """
    答案质量评分器
    
    评估维度：
    1. 相关性 - 答案与问题的相关程度
    2. 完整性 - 答案的完整程度
    3. 置信度 - 基于源文档的可信度
    4. 清晰度 - 答案的表达清晰度
    """
    
    def __init__(self):
        """初始化评分器"""
        self.weights = {
            "relevance": 0.35,      # 相关性权重
            "completeness": 0.25,   # 完整性权重
            "confidence": 0.25,     # 置信度权重
            "clarity": 0.15         # 清晰度权重
        }
    
    def score_answer(
        self,
        question: str,
        answer: str,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> QualityScore:
        """
        评估答案质量
        
        Args:
            question: 用户问题
            answer: 生成的答案
            sources: 源文档列表
            
        Returns:
            质量评分对象
        """
        sources = sources or []
        
        # 1. 计算相关性
        relevance = self._calculate_relevance(question, answer)
        
        # 2. 计算完整性
        completeness = self._calculate_completeness(question, answer)
        
        # 3. 计算置信度
        confidence = self._calculate_confidence(sources)
        
        # 4. 计算清晰度
        clarity = self._calculate_clarity(answer)
        
        # 5. 计算总分
        overall = (
            relevance * self.weights["relevance"] +
            completeness * self.weights["completeness"] +
            confidence * self.weights["confidence"] +
            clarity * self.weights["clarity"]
        )
        
        details = {
            "question_length": len(question),
            "answer_length": len(answer),
            "source_count": len(sources),
            "has_citations": self._has_citations(answer)
        }
        
        return QualityScore(
            relevance=relevance,
            completeness=completeness,
            confidence=confidence,
            clarity=clarity,
            overall=overall,
            details=details
        )
    
    def _calculate_relevance(self, question: str, answer: str) -> float:
        """
        计算相关性（基于关键词重叠）
        
        Args:
            question: 问题
            answer: 答案
            
        Returns:
            相关性得分（0-1）
        """
        # 提取关键词
        question_words = set(self._extract_keywords(question))
        answer_words = set(self._extract_keywords(answer))
        
        if not question_words:
            return 0.5  # 无法判断
        
        # 计算Jaccard相似度
        intersection = len(question_words & answer_words)
        union = len(question_words | answer_words)
        
        if union == 0:
            return 0.0
        
        base_score = intersection / len(question_words)
        
        # 奖励：答案包含问题的核心词
        question_core = question_words - {"的", "了", "是", "在", "有", "和", "与"}
        if question_core:
            core_match = len(question_core & answer_words) / len(question_core)
            base_score = (base_score * 0.6) + (core_match * 0.4)
        
        return min(base_score, 1.0)
    
    def _calculate_completeness(self, question: str, answer: str) -> float:
        """
        计算完整性
        
        基于答案长度、结构等判断
        
        Args:
            question: 问题
            answer: 答案
            
        Returns:
            完整性得分（0-1）
        """
        # 基于长度
        answer_length = len(answer)
        if answer_length < 20:
            length_score = 0.3
        elif answer_length < 50:
            length_score = 0.5
        elif answer_length < 100:
            length_score = 0.7
        elif answer_length < 200:
            length_score = 0.85
        else:
            length_score = 1.0
        
        # 结构完整性
        has_intro = any(word in answer[:50] for word in ["是", "指", "表示", "意思"])
        has_details = len(answer) > 100
        has_conclusion = any(word in answer[-50:] for word in ["因此", "所以", "总之", "综上"])
        
        structure_score = (
            (0.3 if has_intro else 0) +
            (0.4 if has_details else 0) +
            (0.3 if has_conclusion else 0)
        )
        
        # 综合评分
        completeness = (length_score * 0.6) + (structure_score * 0.4)
        
        return round(completeness, 3)
    
    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """
        计算置信度
        
        基于源文档数量和相关度
        
        Args:
            sources: 源文档列表
            
        Returns:
            置信度得分（0-1）
        """
        if not sources:
            return 0.3  # 无源文档，低置信度
        
        # 源数量因子（1-3个源最佳）
        source_count = len(sources)
        if source_count == 0:
            count_factor = 0.0
        elif source_count == 1:
            count_factor = 0.7
        elif source_count == 2:
            count_factor = 0.9
        elif source_count >= 3:
            count_factor = 1.0
        else:
            count_factor = 0.5
        
        # 相关度因子
        avg_relevance = sum(s.get("relevance", 0) for s in sources) / len(sources)
        
        # 综合置信度
        confidence = (count_factor * 0.4) + (avg_relevance * 0.6)
        
        return round(confidence, 3)
    
    def _calculate_clarity(self, answer: str) -> float:
        """
        计算清晰度
        
        基于句子结构、标点使用等
        
        Args:
            answer: 答案
            
        Returns:
            清晰度得分（0-1）
        """
        # 句子数量
        sentences = re.split(r'[。！？\n]', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # 平均句长
        if sentence_count > 0:
            avg_sentence_length = len(answer) / sentence_count
        else:
            avg_sentence_length = len(answer)
        
        # 理想句长：30-80字
        if 30 <= avg_sentence_length <= 80:
            length_score = 1.0
        elif 20 <= avg_sentence_length <= 100:
            length_score = 0.8
        else:
            length_score = 0.6
        
        # 标点使用
        punctuation_count = sum(answer.count(p) for p in "，。！？；：")
        punctuation_ratio = punctuation_count / len(answer) if answer else 0
        
        # 理想标点比例：0.05-0.15
        if 0.05 <= punctuation_ratio <= 0.15:
            punct_score = 1.0
        else:
            punct_score = 0.7
        
        # 段落结构
        paragraphs = answer.split('\n\n')
        has_paragraphs = len(paragraphs) > 1
        structure_score = 1.0 if has_paragraphs else 0.8
        
        # 综合清晰度
        clarity = (length_score * 0.4) + (punct_score * 0.3) + (structure_score * 0.3)
        
        return round(clarity, 3)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单分词（移除停用词）
        stopwords = {
            "的", "了", "是", "在", "有", "和", "与", "或", "而", "等",
            "个", "这", "那", "我", "你", "他", "她", "它", "们"
        }
        
        words = re.findall(r'[\u4e00-\u9fa5]+', text)
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        
        return keywords
    
    def _has_citations(self, answer: str) -> bool:
        """检查是否包含引用"""
        return bool(re.search(r'\[\d+\]|参考来源', answer))


# 默认评分器实例
default_scorer = AnswerQualityScorer()


# ==================== 便捷函数 ====================

def score_answer(
    question: str,
    answer: str,
    sources: Optional[List[Dict[str, Any]]] = None
) -> QualityScore:
    """
    便捷函数：评估答案质量
    
    Args:
        question: 问题
        answer: 答案
        sources: 源文档列表
        
    Returns:
        质量评分对象
    """
    return default_scorer.score_answer(question, answer, sources)

