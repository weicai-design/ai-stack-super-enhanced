"""
Semantic Text Cleaner
版本: 1.0.0
功能: 语义文本清洗器
描述: 基于语义理解的智能文本清洗和标准化处理
"""

import html
import logging
import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List

from . import TextProcessingConfig, TextProcessorBase, register_processor

logger = logging.getLogger("text_processor.semantic_cleaner")


class SemanticCleaner(TextProcessorBase):
    """语义文本清洗器"""

    def __init__(self, config: TextProcessingConfig):
        super().__init__(config)
        self.noise_patterns = []
        self.replacement_rules = []
        self._quality_threshold = 0.6

    async def _initialize_components(self):
        """初始化清洗组件"""
        try:
            self._compile_noise_patterns()
            self._compile_replacement_rules()
            self._load_quality_metrics()

            logger.info("语义清洗器组件初始化完成")

        except Exception as e:
            logger.error(f"清洗器组件初始化失败: {str(e)}")
            raise

    def _compile_noise_patterns(self):
        """编译噪声模式"""
        self.noise_patterns = [
            # HTML标签
            (re.compile(r"<[^>]+>"), ""),
            # 特殊字符和表情符号
            (
                re.compile(r"[^\w\s\u4e00-\u9fff\u3400-\u4dbf\.,!?;:()\-—–@#%&*+/=]"),
                " ",
            ),
            # 多个连续空格
            (re.compile(r"\s+"), " "),
            # 多个连续标点
            (re.compile(r"([.,!?;:])\1+"), r"\1"),
            # URL链接
            (re.compile(r"https?://\S+|www\.\S+"), "[URL]"),
            # 邮箱地址
            (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "[EMAIL]",
            ),
            # 电话号码
            (re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]"), "[PHONE]"),
            # 数字编号（保留有意义的数字）
            (re.compile(r"\b\d{1,2}[\.\)]"), ""),  # 列表编号
        ]

    def _compile_replacement_rules(self):
        """编译替换规则"""
        self.replacement_rules = [
            # 全角转半角
            (
                re.compile(r'[，。！？；："（）【】《》]'),
                lambda m: self._full_to_half(m.group()),
            ),
            # 英文标点标准化
            (re.compile(r"[`´‘’]"), "'"),
            (re.compile(r'[«»"＂]'), '"'),
            # 破折号标准化
            (re.compile(r"[—–−-]{2,}"), "—"),
            # 省略号标准化
            (re.compile(r"\.{3,}"), "..."),
        ]

    def _load_quality_metrics(self):
        """加载质量评估指标"""
        self.quality_indicators = {
            "min_length": 10,
            "max_noise_ratio": 0.3,
            "min_content_ratio": 0.5,
            "max_repetition_ratio": 0.2,
        }

    async def _process_impl(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行语义文本清洗"""
        try:
            original_text = text
            cleaning_report = {
                "original_length": len(text),
                "cleaning_steps": [],
                "removed_content": [],
                "quality_metrics": {},
            }

            # 执行多阶段清洗
            text = await self._basic_cleaning(text, cleaning_report)
            text = await self._semantic_cleaning(text, cleaning_report)
            text = await self._structural_cleaning(text, cleaning_report)

            # 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(
                original_text, text, cleaning_report
            )
            cleaning_report["quality_metrics"] = quality_metrics

            # 生成最终报告
            result = {
                "cleaned_text": text,
                "cleaning_report": cleaning_report,
                "is_high_quality": quality_metrics["overall_score"]
                >= self._quality_threshold,
            }

            logger.info(
                f"文本清洗完成: 质量分数 {quality_metrics['overall_score']:.3f}"
            )
            return result

        except Exception as e:
            logger.error(f"文本清洗失败: {str(e)}")
            raise

    async def _basic_cleaning(self, text: str, report: Dict[str, Any]) -> str:
        """基础文本清洗"""
        original_text = text

        # HTML转义解码
        text = html.unescape(text)

        # Unicode标准化
        text = unicodedata.normalize("NFKC", text)

        # 应用噪声模式
        for pattern, replacement in self.noise_patterns:
            original_segment = text
            text = pattern.sub(replacement, text)

            # 记录被移除的内容
            if text != original_segment:
                removed = self._find_removed_content(original_segment, text, pattern)
                if removed:
                    report["removed_content"].extend(removed)

        # 应用替换规则
        for pattern, replacement in self.replacement_rules:
            if callable(replacement):
                text = pattern.sub(replacement, text)
            else:
                text = pattern.sub(replacement, text)

        # 去除首尾空格
        text = text.strip()

        report["cleaning_steps"].append(
            {
                "step": "basic_cleaning",
                "original_length": len(original_text),
                "cleaned_length": len(text),
                "removed_chars": len(original_text) - len(text),
            }
        )

        return text

    async def _semantic_cleaning(self, text: str, report: Dict[str, Any]) -> str:
        """语义级清洗"""
        original_text = text

        # 句子级别清洗
        sentences = self._split_into_sentences(text)
        cleaned_sentences = []

        for sentence in sentences:
            cleaned_sentence = await self._clean_sentence(sentence)
            if cleaned_sentence and await self._is_meaningful_sentence(
                cleaned_sentence
            ):
                cleaned_sentences.append(cleaned_sentence)

        text = " ".join(cleaned_sentences)

        report["cleaning_steps"].append(
            {
                "step": "semantic_cleaning",
                "original_sentences": len(sentences),
                "cleaned_sentences": len(cleaned_sentences),
                "removed_sentences": len(sentences) - len(cleaned_sentences),
            }
        )

        return text

    async def _structural_cleaning(self, text: str, report: Dict[str, Any]) -> str:
        """结构级清洗"""
        original_text = text

        # 段落重组
        paragraphs = self._split_into_paragraphs(text)
        cleaned_paragraphs = []

        for paragraph in paragraphs:
            cleaned_paragraph = await self._clean_paragraph(paragraph)
            if cleaned_paragraph and await self._is_meaningful_paragraph(
                cleaned_paragraph
            ):
                cleaned_paragraphs.append(cleaned_paragraph)

        text = "\n\n".join(cleaned_paragraphs)

        report["cleaning_steps"].append(
            {
                "step": "structural_cleaning",
                "original_paragraphs": len(paragraphs),
                "cleaned_paragraphs": len(cleaned_paragraphs),
                "removed_paragraphs": len(paragraphs) - len(cleaned_paragraphs),
            }
        )

        return text

    def _split_into_sentences(self, text: str) -> List[str]:
        """分割文本为句子"""
        # 简化的句子分割（实际应使用更复杂的NLP技术）
        sentence_endings = re.compile(r"[.!?。！？]+[\s]*|[\n\r]+")
        sentences = []
        start = 0

        for match in sentence_endings.finditer(text):
            end = match.end()
            sentence = text[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end

        # 添加最后一句
        if start < len(text):
            remaining = text[start:].strip()
            if remaining:
                sentences.append(remaining)

        return sentences

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """分割文本为段落"""
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    async def _clean_sentence(self, sentence: str) -> str:
        """清洗单个句子"""
        # 去除句子级别的噪声
        cleaned = sentence

        # 修复常见的拼写错误（简化版）
        spelling_fixes = [
            (r"\bteh\b", "the"),
            (r"\badn\b", "and"),
            (r"\brecieve\b", "receive"),
        ]

        for pattern, replacement in spelling_fixes:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # 标准化空格
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    async def _clean_paragraph(self, paragraph: str) -> str:
        """清洗单个段落"""
        # 检查段落连贯性
        sentences = self._split_into_sentences(paragraph)
        if len(sentences) < 1:
            return ""

        # 如果段落过短，尝试与上下文合并（在更高层次处理）
        if len(paragraph) < 50 and len(sentences) == 1:
            # 标记为需要进一步处理的短段落
            return paragraph

        return paragraph

    async def _is_meaningful_sentence(self, sentence: str) -> bool:
        """判断句子是否有意义"""
        if len(sentence) < 5:
            return False

        # 检查是否主要是标点或特殊字符
        alpha_count = sum(1 for c in sentence if c.isalnum() or c in "\u4e00-\u9fff")
        if alpha_count / len(sentence) < 0.3:
            return False

        # 检查重复内容
        words = sentence.split()
        if len(words) > 3:
            word_freq = Counter(words)
            most_common_ratio = word_freq.most_common(1)[0][1] / len(words)
            if most_common_ratio > 0.5:
                return False

        return True

    async def _is_meaningful_paragraph(self, paragraph: str) -> bool:
        """判断段落是否有意义"""
        if len(paragraph) < 20:
            return False

        sentences = self._split_into_sentences(paragraph)
        meaningful_sentences = sum(
            1 for s in sentences if await self._is_meaningful_sentence(s)
        )

        # 至少要有一定比例的句子是有意义的
        return meaningful_sentences / len(sentences) >= 0.5 if sentences else False

    async def _calculate_quality_metrics(
        self, original: str, cleaned: str, report: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算清洗质量指标"""
        metrics = {}

        # 内容保留率
        original_content = self._extract_content_text(original)
        cleaned_content = self._extract_content_text(cleaned)
        metrics["content_preservation"] = (
            len(cleaned_content) / len(original_content) if original_content else 1.0
        )

        # 噪声去除率
        original_noise = len(original) - len(original_content)
        cleaned_noise = len(cleaned) - len(cleaned_content)
        metrics["noise_reduction"] = (
            1.0 - (cleaned_noise / len(cleaned)) if cleaned else 1.0
        )

        # 可读性评分（简化）
        metrics["readability_score"] = await self._calculate_readability(cleaned)

        # 连贯性评分
        metrics["coherence_score"] = await self._calculate_coherence(cleaned)

        # 综合评分
        metrics["overall_score"] = (
            metrics["content_preservation"] * 0.3
            + metrics["noise_reduction"] * 0.3
            + metrics["readability_score"] * 0.2
            + metrics["coherence_score"] * 0.2
        )

        return metrics

    def _extract_content_text(self, text: str) -> str:
        """提取内容文本（去除噪声）"""
        # 移除明显的噪声字符
        content_chars = []
        for char in text:
            if char.isalnum() or char in " .,!?;:\u4e00-\u9fff\u3400-\u4dbf":
                content_chars.append(char)
        return "".join(content_chars)

    async def _calculate_readability(self, text: str) -> float:
        """计算可读性评分（简化版）"""
        sentences = self._split_into_sentences(text)
        words = text.split()

        if not sentences or not words:
            return 0.0

        # 平均句子长度
        avg_sentence_length = len(words) / len(sentences)

        # 句子长度多样性
        sentence_lengths = [len(s.split()) for s in sentences]
        length_variance = np.var(sentence_lengths) if len(sentence_lengths) > 1 else 0

        # 基于平均句子长度和多样性评分
        ideal_length = 15  # 理想平均句子长度
        length_score = 1.0 - min(
            abs(avg_sentence_length - ideal_length) / ideal_length, 1.0
        )
        diversity_score = 1.0 - min(length_variance / 100, 1.0)  # 控制方差影响

        return 0.7 * length_score + 0.3 * diversity_score

    async def _calculate_coherence(self, text: str) -> float:
        """计算文本连贯性评分"""
        sentences = self._split_into_sentences(text)
        if len(sentences) < 2:
            return 0.8  # 单句文本的默认分数

        # 简化的连贯性评估（实际应使用更复杂的NLP技术）
        # 检查句子间的过渡和主题一致性
        transition_words = [
            "然而",
            "而且",
            "另外",
            "因此",
            "所以",
            "同时",
            "例如",
            "总之",
        ]
        transition_count = 0

        for sentence in sentences:
            if any(transition in sentence for transition in transition_words):
                transition_count += 1

        transition_score = transition_count / len(sentences)

        # 基于重复关键词的连贯性
        all_words = " ".join(sentences).split()
        unique_words = set(all_words)
        repetition_ratio = 1 - len(unique_words) / len(all_words) if all_words else 0

        coherence_score = 0.6 * transition_score + 0.4 * (
            1 - min(repetition_ratio, 0.5)
        )
        return coherence_score

    def _find_removed_content(
        self, original: str, cleaned: str, pattern: re.Pattern
    ) -> List[Dict[str, Any]]:
        """查找被移除的内容"""
        removed = []

        for match in pattern.finditer(original):
            removed_text = match.group()
            if removed_text not in cleaned:
                removed.append(
                    {
                        "content": removed_text,
                        "position": match.start(),
                        "type": "noise",
                        "pattern": pattern.pattern,
                    }
                )

        return removed

    def _full_to_half(self, char: str) -> str:
        """全角字符转半角"""
        full_to_half_map = {
            "，": ",",
            "。": ".",
            "！": "!",
            "？": "?",
            "；": ";",
            "：": ":",
            "（": "(",
            "）": ")",
            "【": "[",
            "】": "]",
            "《": "<",
            "》": ">",
        }
        return full_to_half_map.get(char, char)


# 注册处理器
register_processor("semantic_cleaner", SemanticCleaner)
logger.info("语义清洗器注册完成")
