"""
Text Quality Validator
版本: 1.0.0
功能: 文本质量验证器
描述: 综合评估文本质量，包括可读性、连贯性、信息密度等多维度指标
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import TextProcessingConfig, TextProcessorBase, register_processor

logger = logging.getLogger("text_processor.quality_validator")


@dataclass
class QualityScore:
    """质量评分数据类"""

    overall: float
    readability: float
    coherence: float
    informativeness: float
    grammaticality: float
    relevance: float


@dataclass
class ValidationResult:
    """验证结果数据类"""

    is_valid: bool
    quality_score: QualityScore
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    metrics: Dict[str, float]


class QualityValidator(TextProcessorBase):
    """文本质量验证器"""

    def __init__(self, config: TextProcessingConfig):
        super().__init__(config)
        self.quality_threshold = 0.6
        self.vectorizer = None
        self.grammar_patterns = []
        self.quality_rules = []

    async def _initialize_components(self):
        """初始化质量验证组件"""
        try:
            # 初始化TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(
                max_features=1000, stop_words=None, ngram_range=(1, 2)
            )

            # 编译语法检查模式
            await self._compile_grammar_patterns()

            # 加载质量规则
            await self._load_quality_rules()

            logger.info("质量验证器组件初始化完成")

        except Exception as e:
            logger.error(f"质量验证器初始化失败: {str(e)}")
            raise

    async def _compile_grammar_patterns(self):
        """编译语法检查模式"""
        self.grammar_patterns = [
            # 连续重复词
            (re.compile(r"\b(\w+)\s+\1\b"), "连续重复词"),
            # 缺少标点
            (re.compile(r"[^.!?。！？]\n"), "可能缺少结束标点"),
            # 空格问题
            (
                re.compile(r"[,.!?;:，。！？；：][A-Za-z\u4e00-\u9fff]"),
                "标点后缺少空格",
            ),
            # 中英文混排空格
            (re.compile(r"[a-zA-Z][\u4e00-\u9fff]"), "英文后缺少空格"),
            (re.compile(r"[\u4e00-\u9fff][a-zA-Z]"), "中文后缺少空格"),
        ]

    async def _load_quality_rules(self):
        """加载质量规则"""
        self.quality_rules = [
            {
                "name": "minimum_length",
                "check": self._check_minimum_length,
                "weight": 0.1,
            },
            {
                "name": "readability_score",
                "check": self._check_readability,
                "weight": 0.2,
            },
            {
                "name": "coherence_consistency",
                "check": self._check_coherence,
                "weight": 0.25,
            },
            {
                "name": "information_density",
                "check": self._check_information_density,
                "weight": 0.2,
            },
            {
                "name": "grammatical_quality",
                "check": self._check_grammatical_quality,
                "weight": 0.15,
            },
            {"name": "relevance_focus", "check": self._check_relevance, "weight": 0.1},
        ]

    async def _process_impl(
        self, text: str, metadata: Dict[str, Any]
    ) -> ValidationResult:
        """执行文本质量验证"""
        try:
            validation_metrics = {}
            issues = []
            suggestions = []

            # 执行各项质量检查
            for rule in self.quality_rules:
                rule_result = await rule["check"](text, metadata)

                validation_metrics[rule["name"]] = rule_result["score"]
                issues.extend(rule_result.get("issues", []))
                suggestions.extend(rule_result.get("suggestions", []))

            # 计算综合质量分数
            overall_score = await self._calculate_overall_score(validation_metrics)

            # 创建质量评分对象
            quality_score = QualityScore(
                overall=overall_score,
                readability=validation_metrics.get("readability_score", 0),
                coherence=validation_metrics.get("coherence_consistency", 0),
                informativeness=validation_metrics.get("information_density", 0),
                grammaticality=validation_metrics.get("grammatical_quality", 0),
                relevance=validation_metrics.get("relevance_focus", 0),
            )

            # 确定验证结果
            is_valid = overall_score >= self.quality_threshold

            # 生成验证报告
            result = ValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                issues=issues,
                suggestions=suggestions,
                metrics=validation_metrics,
            )

            logger.info(f"质量验证完成: 综合分数 {overall_score:.3f}, 有效: {is_valid}")
            return result

        except Exception as e:
            logger.error(f"质量验证失败: {str(e)}")
            raise

    async def _check_minimum_length(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查最小长度要求"""
        score = 1.0
        issues = []
        suggestions = []

        text_length = len(text)
        word_count = len(text.split())

        # 基于文本类型设置不同的长度要求
        min_acceptable_length = 10
        ideal_length = 50

        if text_length < min_acceptable_length:
            score = 0.2
            issues.append(
                {
                    "type": "length_insufficient",
                    "severity": "high",
                    "message": f"文本长度过短 ({text_length} 字符)",
                    "position": "global",
                }
            )
            suggestions.append("增加更多内容以提高信息量")
        elif text_length < ideal_length:
            score = 0.7
            issues.append(
                {
                    "type": "length_suboptimal",
                    "severity": "low",
                    "message": f"文本长度较短 ({text_length} 字符)",
                    "position": "global",
                }
            )
            suggestions.append("考虑扩展内容以提供更完整的信息")

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {"text_length": text_length, "word_count": word_count},
        }

    async def _check_readability(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查可读性"""
        score = 1.0
        issues = []
        suggestions = []

        try:
            # 计算多种可读性指标
            flesch_score = await self._calculate_flesch_reading_ease(text)
            avg_sentence_length = await self._calculate_avg_sentence_length(text)
            lexical_diversity = await self._calculate_lexical_diversity(text)

            # 综合可读性评分
            readability_components = []

            # Flesch可读性评分 (0-100, 越高越易读)
            if flesch_score >= 60:  # 标准水平
                readability_components.append(1.0)
            elif flesch_score >= 30:  # 中等水平
                readability_components.append(0.7)
            else:  # 较难阅读
                readability_components.append(0.3)
                issues.append(
                    {
                        "type": "low_readability",
                        "severity": "medium",
                        "message": f"文本可读性较低 (Flesch指数: {flesch_score:.1f})",
                        "position": "global",
                    }
                )
                suggestions.append("简化句子结构，使用更常见的词汇")

            # 句子长度评分
            if avg_sentence_length <= 20:  # 理想长度
                readability_components.append(1.0)
            elif avg_sentence_length <= 35:  # 可接受长度
                readability_components.append(0.8)
            else:  # 过长句子
                readability_components.append(0.4)
                issues.append(
                    {
                        "type": "long_sentences",
                        "severity": "medium",
                        "message": f"平均句子长度较长 ({avg_sentence_length:.1f} 词)",
                        "position": "global",
                    }
                )
                suggestions.append("将长句子拆分为多个短句")

            # 词汇多样性评分
            if lexical_diversity >= 0.6:  # 良好的多样性
                readability_components.append(1.0)
            elif lexical_diversity >= 0.4:  # 中等多样性
                readability_components.append(0.7)
            else:  # 词汇重复较多
                readability_components.append(0.3)
                issues.append(
                    {
                        "type": "low_lexical_diversity",
                        "severity": "low",
                        "message": f"词汇多样性较低 ({lexical_diversity:.3f})",
                        "position": "global",
                    }
                )
                suggestions.append("使用更丰富的词汇表达")

            score = sum(readability_components) / len(readability_components)

        except Exception as e:
            logger.warning(f"可读性检查失败: {str(e)}")
            score = 0.5

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "flesch_reading_ease": flesch_score,
                "avg_sentence_length": avg_sentence_length,
                "lexical_diversity": lexical_diversity,
            },
        }

    async def _check_coherence(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查连贯性和一致性"""
        score = 1.0
        issues = []
        suggestions = []

        try:
            coherence_components = []

            # 句子间连贯性
            sentence_coherence = await self._calculate_sentence_coherence(text)
            coherence_components.append(sentence_coherence)

            if sentence_coherence < 0.6:
                issues.append(
                    {
                        "type": "low_coherence",
                        "severity": "medium",
                        "message": "句子间连贯性有待提高",
                        "position": "global",
                    }
                )
                suggestions.append("使用过渡词改善句子间的逻辑连接")

            # 主题一致性
            topic_consistency = await self._calculate_topic_consistency(text)
            coherence_components.append(topic_consistency)

            if topic_consistency < 0.7:
                issues.append(
                    {
                        "type": "topic_drift",
                        "severity": "medium",
                        "message": "文本主题一致性不足",
                        "position": "global",
                    }
                )
                suggestions.append("保持主题聚焦，避免频繁切换话题")

            # 逻辑结构
            logical_structure = await self._analyze_logical_structure(text)
            coherence_components.append(logical_structure)

            if logical_structure < 0.6:
                issues.append(
                    {
                        "type": "weak_structure",
                        "severity": "low",
                        "message": "文本逻辑结构可以优化",
                        "position": "global",
                    }
                )
                suggestions.append("使用清晰的段落结构组织内容")

            score = sum(coherence_components) / len(coherence_components)

        except Exception as e:
            logger.warning(f"连贯性检查失败: {str(e)}")
            score = 0.5

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "sentence_coherence": sentence_coherence,
                "topic_consistency": topic_consistency,
                "logical_structure": logical_structure,
            },
        }

    async def _check_information_density(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查信息密度"""
        score = 1.0
        issues = []
        suggestions = []

        try:
            density_components = []

            # 实体密度
            entity_density = await self._calculate_entity_density(text)
            density_components.append(entity_density)

            if entity_density < 0.1:
                issues.append(
                    {
                        "type": "low_entity_density",
                        "severity": "medium",
                        "message": "实体信息密度较低",
                        "position": "global",
                    }
                )
                suggestions.append("增加具体的人物、地点、组织等实体信息")

            # 关键词密度
            keyword_density = await self._calculate_keyword_density(text)
            density_components.append(keyword_density)

            # 重复内容检测
            repetition_score = await self._calculate_repetition_score(text)
            density_components.append(repetition_score)

            if repetition_score < 0.7:
                issues.append(
                    {
                        "type": "high_repetition",
                        "severity": "low",
                        "message": "文本中存在较多重复内容",
                        "position": "global",
                    }
                )
                suggestions.append("减少重复表达，提高信息效率")

            score = sum(density_components) / len(density_components)

        except Exception as e:
            logger.warning(f"信息密度检查失败: {str(e)}")
            score = 0.5

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "entity_density": entity_density,
                "keyword_density": keyword_density,
                "repetition_score": repetition_score,
            },
        }

    async def _check_grammatical_quality(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查语法质量"""
        score = 1.0
        issues = []
        suggestions = []

        try:
            grammar_issues = await self._detect_grammar_issues(text)
            issue_count = len(grammar_issues)

            # 基于语法问题数量评分
            if issue_count == 0:
                score = 1.0
            elif issue_count <= 2:
                score = 0.8
            elif issue_count <= 5:
                score = 0.6
            else:
                score = 0.3

            # 添加检测到的问题
            for issue in grammar_issues:
                issues.append(
                    {
                        "type": "grammar_issue",
                        "severity": "low",
                        "message": issue["description"],
                        "position": issue["position"],
                        "context": issue.get("context", ""),
                    }
                )

            if grammar_issues:
                suggestions.append("检查并修正语法问题")

        except Exception as e:
            logger.warning(f"语法质量检查失败: {str(e)}")
            score = 0.5

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {"grammar_issue_count": issue_count},
        }

    async def _check_relevance(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查相关性和聚焦度"""
        score = 1.0
        issues = []
        suggestions = []

        try:
            # 主题聚焦度
            focus_score = await self._calculate_topic_focus(text)

            # 上下文相关性（如果有元数据）
            context_relevance = await self._calculate_context_relevance(text, metadata)

            relevance_components = [focus_score]
            if context_relevance is not None:
                relevance_components.append(context_relevance)

            score = sum(relevance_components) / len(relevance_components)

            if focus_score < 0.7:
                issues.append(
                    {
                        "type": "low_focus",
                        "severity": "medium",
                        "message": "文本主题聚焦度不足",
                        "position": "global",
                    }
                )
                suggestions.append("保持内容与核心主题的相关性")

        except Exception as e:
            logger.warning(f"相关性检查失败: {str(e)}")
            score = 0.5

        return {
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "metrics": {
                "topic_focus": focus_score,
                "context_relevance": context_relevance or 0.0,
            },
        }

    async def _calculate_flesch_reading_ease(self, text: str) -> float:
        """计算Flesch阅读易度指数"""
        try:
            sentences = await self._split_into_sentences(text)
            words = text.split()

            if not sentences or not words:
                return 60.0  # 默认中等可读性

            total_sentences = len(sentences)
            total_words = len(words)
            total_syllables = sum(self._count_syllables(word) for word in words)

            # Flesch公式: 206.835 - 1.015 * (总词数/总句数) - 84.6 * (总音节数/总词数)
            avg_sentence_length = total_words / total_sentences
            avg_syllables_per_word = total_syllables / total_words

            score = (
                206.835
                - (1.015 * avg_sentence_length)
                - (84.6 * avg_syllables_per_word)
            )
            return max(0, min(100, score))

        except Exception:
            return 60.0

    async def _calculate_avg_sentence_length(self, text: str) -> float:
        """计算平均句子长度"""
        sentences = await self._split_into_sentences(text)
        if not sentences:
            return 0.0

        word_counts = [len(sentence.split()) for sentence in sentences]
        return sum(word_counts) / len(word_counts)

    async def _calculate_lexical_diversity(self, text: str) -> float:
        """计算词汇多样性"""
        words = text.lower().split()
        if not words:
            return 0.0

        unique_words = set(words)
        return len(unique_words) / len(words)

    async def _calculate_sentence_coherence(self, text: str) -> float:
        """计算句子间连贯性"""
        sentences = await self._split_into_sentences(text)
        if len(sentences) < 2:
            return 0.8  # 单句文本的默认分数

        try:
            # 使用TF-IDF计算句子相似度
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 计算相邻句子的平均相似度
            adjacent_similarities = []
            for i in range(len(sentences) - 1):
                adjacent_similarities.append(similarity_matrix[i, i + 1])

            return (
                sum(adjacent_similarities) / len(adjacent_similarities)
                if adjacent_similarities
                else 0.5
            )

        except Exception:
            return 0.5

    async def _calculate_topic_consistency(self, text: str) -> float:
        """计算主题一致性"""
        sentences = await self._split_into_sentences(text)
        if len(sentences) < 3:
            return 0.8

        try:
            # 计算首句与后续句子的平均相似度
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            first_sentence_similarities = similarity_matrix[0, 1:]
            return (
                np.mean(first_sentence_similarities)
                if first_sentence_similarities.size > 0
                else 0.5
            )

        except Exception:
            return 0.5

    async def _analyze_logical_structure(self, text: str) -> float:
        """分析逻辑结构"""
        # 简化的逻辑结构分析
        paragraphs = await self._split_into_paragraphs(text)

        if len(paragraphs) < 2:
            return 0.7

        # 检查段落长度分布
        paragraph_lengths = [len(p.split()) for p in paragraphs]
        length_variance = np.var(paragraph_lengths)

        # 较低的方差通常表示更好的结构平衡
        structure_score = 1.0 - min(length_variance / 100, 1.0)

        return structure_score

    async def _calculate_entity_density(self, text: str) -> float:
        """计算实体密度"""
        # 简化的实体识别（基于大写词和特定模式）
        words = text.split()
        if not words:
            return 0.0

        # 识别可能的实体（大写词、特定名词等）
        entity_candidates = []
        for word in words:
            # 英文大写词（排除句首词）
            if word.istitle() and len(word) > 1:
                entity_candidates.append(word)
            # 中文特定模式（简化）
            elif re.search(r"[公司|大学|医院|政府]", word):
                entity_candidates.append(word)

        entity_density = len(entity_candidates) / len(words)
        return min(entity_density * 10, 1.0)  # 归一化到0-1

    async def _calculate_keyword_density(self, text: str) -> float:
        """计算关键词密度"""
        words = text.lower().split()
        if not words:
            return 0.0

        # 计算词频分布
        word_freq = Counter(words)

        # 关键词密度基于高频词的比例
        top_words = word_freq.most_common(5)
        keyword_density = sum(count for _, count in top_words) / len(words)

        # 适中的关键词密度最好
        ideal_density = 0.3
        density_score = 1.0 - min(
            abs(keyword_density - ideal_density) / ideal_density, 1.0
        )

        return density_score

    async def _calculate_repetition_score(self, text: str) -> float:
        """计算重复内容评分"""
        sentences = await self._split_into_sentences(text)
        if len(sentences) < 2:
            return 1.0

        try:
            # 计算句子间的相似度
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 排除对角线，计算平均相似度
            np.fill_diagonal(similarity_matrix, 0)
            avg_similarity = np.sum(similarity_matrix) / (
                len(sentences) * (len(sentences) - 1)
            )

            # 相似度越低，重复越少，分数越高
            return 1.0 - min(avg_similarity, 0.5)

        except Exception:
            return 0.7

    async def _detect_grammar_issues(self, text: str) -> List[Dict[str, Any]]:
        """检测语法问题"""
        issues = []

        for pattern, description in self.grammar_patterns:
            for match in pattern.finditer(text):
                issues.append(
                    {
                        "description": description,
                        "position": match.start(),
                        "context": text[max(0, match.start() - 20) : match.end() + 20],
                    }
                )

        return issues

    async def _calculate_topic_focus(self, text: str) -> float:
        """计算主题聚焦度"""
        sentences = await self._split_into_sentences(text)
        if len(sentences) < 2:
            return 0.8

        try:
            # 使用TF-IDF计算主题一致性
            tfidf_matrix = self.vectorizer.fit_transform(sentences)

            # 计算所有句子的主题向量平均值
            topic_vectors = tfidf_matrix.toarray()
            mean_topic_vector = np.mean(topic_vectors, axis=0)

            # 计算每个句子与平均主题的相似度
            similarities = []
            for i in range(len(sentences)):
                similarity = cosine_similarity(
                    topic_vectors[i].reshape(1, -1), mean_topic_vector.reshape(1, -1)
                )[0][0]
                similarities.append(similarity)

            # 返回平均相似度作为聚焦度指标
            return np.mean(similarities) if similarities else 0.5

        except Exception:
            return 0.5

    async def _calculate_context_relevance(
        self, text: str, metadata: Dict[str, Any]
    ) -> Optional[float]:
        """计算上下文相关性"""
        # 如果有主题或上下文信息，可以计算相关性
        if not metadata or "context" not in metadata:
            return None

        try:
            context = metadata.get("context", "")
            if not context:
                return None

            # 计算文本与上下文的相似度
            tfidf_matrix = self.vectorizer.fit_transform([text, context])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return similarity

        except Exception:
            return None

    async def _split_into_sentences(self, text: str) -> List[str]:
        """分割文本为句子"""
        # 简化的句子分割
        sentence_endings = re.compile(r"[.!?。！？]+[\s]*|[\n\r]+")
        sentences = []
        start = 0

        for match in sentence_endings.finditer(text):
            end = match.end()
            sentence = text[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end

        if start < len(text):
            remaining = text[start:].strip()
            if remaining:
                sentences.append(remaining)

        return sentences

    async def _split_into_paragraphs(self, text: str) -> List[str]:
        """分割文本为段落"""
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _count_syllables(self, word: str) -> int:
        """计算单词音节数（英文）"""
        # 简化的音节计数
        word = word.lower()
        count = 0
        vowels = "aeiouy"

        if word[0] in vowels:
            count += 1

        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1

        if word.endswith("e"):
            count -= 1

        return max(count, 1)

    async def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """计算综合质量分数"""
        total_score = 0.0
        total_weight = 0.0

        for rule in self.quality_rules:
            rule_name = rule["name"]
            rule_weight = rule["weight"]

            if rule_name in metrics:
                total_score += metrics[rule_name] * rule_weight
                total_weight += rule_weight

        return total_score / total_weight if total_weight > 0 else 0.0


# 注册处理器
register_processor("quality_validator", QualityValidator)
logger.info("质量验证器注册完成")
