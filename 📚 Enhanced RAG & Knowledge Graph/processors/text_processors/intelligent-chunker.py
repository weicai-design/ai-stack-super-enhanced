"""
Intelligent Text Chunker
版本: 1.0.0
功能: 智能文本分块处理器
描述: 基于语义和上下文的自适应文本分块，支持多种分块策略
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import (
    ChunkingStrategy,
    ProcessedTextChunk,
    TextProcessingConfig,
    TextProcessorBase,
    register_processor,
)

logger = logging.getLogger("text_processor.intelligent_chunker")


@dataclass
class ChunkBoundary:
    """分块边界数据类"""

    start: int
    end: int
    boundary_type: str  # sentence, paragraph, semantic, fixed
    confidence: float


class IntelligentChunker(TextProcessorBase):
    """智能文本分块器"""

    def __init__(self, config: TextProcessingConfig):
        super().__init__(config)
        self.vectorizer = None
        self.sentence_detector = None
        self._semantic_threshold = 0.7
        self._context_window = 3

    async def _initialize_components(self):
        """初始化分块组件"""
        try:
            # 初始化TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(
                max_features=1000, stop_words=None, ngram_range=(1, 2)
            )

            # 初始化句子检测器（简化版，实际应使用更复杂的NLP库）
            self._init_sentence_detector()

            logger.info("智能分块器组件初始化完成")

        except Exception as e:
            logger.error(f"分块器组件初始化失败: {str(e)}")
            raise

    def _init_sentence_detector(self):
        """初始化句子检测器"""
        # 简化的句子边界正则（支持中文和英文）
        self.sentence_pattern = re.compile(
            r"[.!?。！？]+[\s]*|[\n\r]+|[:：][\s]*$", re.MULTILINE | re.UNICODE
        )

    async def _process_impl(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[ProcessedTextChunk]:
        """执行智能文本分块"""
        try:
            # 根据配置选择分块策略
            if self.config.chunking_strategy == ChunkingStrategy.SEMANTIC:
                chunks = await self._semantic_chunking(text)
            elif self.config.chunking_strategy == ChunkingStrategy.FIXED:
                chunks = await self._fixed_size_chunking(text)
            elif self.config.chunking_strategy == ChunkingStrategy.DYNAMIC:
                chunks = await self._dynamic_chunking(text)
            else:  # ADAPTIVE
                chunks = await self._adaptive_chunking(text)

            # 验证分块质量
            validated_chunks = await self._validate_chunks(chunks, text)

            logger.info(f"文本分块完成: {len(validated_chunks)} 个分块")
            return validated_chunks

        except Exception as e:
            logger.error(f"文本分块处理失败: {str(e)}")
            raise

    async def _semantic_chunking(self, text: str) -> List[ProcessedTextChunk]:
        """基于语义相似度的分块"""
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return await self._fixed_size_chunking(text)

        # 计算句子间的语义相似度
        similarity_matrix = await self._compute_semantic_similarity(sentences)

        # 基于相似度寻找分块边界
        boundaries = self._find_semantic_boundaries(sentences, similarity_matrix)

        return await self._create_chunks_from_boundaries(
            text, sentences, boundaries, "semantic"
        )

    async def _fixed_size_chunking(self, text: str) -> List[ProcessedTextChunk]:
        """固定大小的分块"""
        chunks = []
        text_length = len(text)
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        start = 0
        chunk_id = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # 尝试在句子边界处结束
            if end < text_length:
                adjusted_end = self._find_safe_boundary(text, start, end)
                end = adjusted_end if adjusted_end > start + chunk_size // 2 else end

            chunk_text = text[start:end]

            chunks.append(
                ProcessedTextChunk(
                    content=chunk_text,
                    chunk_id=f"fixed_{chunk_id}",
                    start_position=start,
                    end_position=end,
                    semantic_score=0.8,  # 固定分块的默认分数
                    quality_score=0.9,
                    entities=[],
                    metadata={
                        "chunking_strategy": "fixed",
                        "original_length": len(chunk_text),
                        "overlap_with_previous": overlap if chunk_id > 0 else 0,
                    },
                )
            )

            start = end - overlap
            chunk_id += 1

            # 防止无限循环
            if start >= text_length or chunk_id > 1000:
                break

        return chunks

    async def _dynamic_chunking(self, text: str) -> List[ProcessedTextChunk]:
        """动态内容分块"""
        # 识别文本结构（段落、标题等）
        structure_units = self._analyze_text_structure(text)

        chunks = []
        chunk_id = 0
        current_chunk = ""
        current_start = 0

        for unit in structure_units:
            unit_text = text[unit.start : unit.end]

            # 如果当前块加上新单元不超过最大大小，则合并
            if len(current_chunk) + len(unit_text) <= self.config.max_chunk_size:
                if not current_chunk:
                    current_start = unit.start
                current_chunk += unit_text
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(
                        await self._create_chunk(
                            current_chunk,
                            current_start,
                            unit.start,
                            chunk_id,
                            "dynamic",
                        )
                    )
                    chunk_id += 1

                # 开始新块
                current_chunk = unit_text
                current_start = unit.start

        # 添加最后一个块
        if current_chunk:
            chunks.append(
                await self._create_chunk(
                    current_chunk, current_start, len(text), chunk_id, "dynamic"
                )
            )

        return chunks

    async def _adaptive_chunking(self, text: str) -> List[ProcessedTextChunk]:
        """自适应分块策略"""
        # 结合多种分块策略
        semantic_chunks = await self._semantic_chunking(text)
        fixed_chunks = await self._fixed_size_chunking(text)

        # 选择最优分块方案
        semantic_score = await self._evaluate_chunk_quality(semantic_chunks)
        fixed_score = await self._evaluate_chunk_quality(fixed_chunks)

        if semantic_score >= fixed_score:
            logger.info("选择语义分块策略")
            return semantic_chunks
        else:
            logger.info("选择固定分块策略")
            return fixed_chunks

    def _split_into_sentences(self, text: str) -> List[Tuple[int, int, str]]:
        """将文本分割成句子"""
        sentences = []
        start = 0

        for match in self.sentence_pattern.finditer(text):
            end = match.end()
            sentence_text = text[start:end].strip()

            if sentence_text and len(sentence_text) >= 5:  # 最小句子长度
                sentences.append((start, end, sentence_text))

            start = end

        # 添加最后一个句子
        if start < len(text):
            remaining_text = text[start:].strip()
            if remaining_text and len(remaining_text) >= 5:
                sentences.append((start, len(text), remaining_text))

        return sentences

    async def _compute_semantic_similarity(
        self, sentences: List[Tuple[int, int, str]]
    ) -> np.ndarray:
        """计算句子间的语义相似度"""
        try:
            sentence_texts = [s[2] for s in sentences]

            if len(sentence_texts) <= 1:
                return np.ones((1, 1))

            # 使用TF-IDF计算相似度
            tfidf_matrix = self.vectorizer.fit_transform(sentence_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            return similarity_matrix

        except Exception as e:
            logger.warning(f"语义相似度计算失败，使用默认相似度: {str(e)}")
            return np.ones((len(sentences), len(sentences)))

    def _find_semantic_boundaries(
        self, sentences: List[Tuple[int, int, str]], similarity_matrix: np.ndarray
    ) -> List[ChunkBoundary]:
        """寻找语义分块边界"""
        boundaries = []
        n_sentences = len(sentences)

        if n_sentences <= 1:
            return boundaries

        # 检测相似度显著下降的位置作为边界
        for i in range(1, n_sentences):
            # 计算移动平均相似度
            prev_similarities = []
            next_similarities = []

            for j in range(max(0, i - self._context_window), i):
                prev_similarities.extend(
                    similarity_matrix[j, max(0, j - 1) : j + 1].flatten()
                )

            for j in range(i, min(n_sentences, i + self._context_window)):
                next_similarities.extend(
                    similarity_matrix[j, j : min(n_sentences, j + 1)].flatten()
                )

            if prev_similarities and next_similarities:
                prev_avg = np.mean(prev_similarities)
                next_avg = np.mean(next_similarities)

                # 如果相似度下降超过阈值，则认为是边界
                if prev_avg - next_avg > self._semantic_threshold:
                    boundaries.append(
                        ChunkBoundary(
                            start=sentences[i][0],
                            end=sentences[i][0],
                            boundary_type="semantic",
                            confidence=abs(prev_avg - next_avg),
                        )
                    )

        return boundaries

    def _analyze_text_structure(self, text: str) -> List[Any]:
        """分析文本结构"""

        # 简化的结构分析（实际应使用更复杂的NLP技术）
        class StructureUnit:
            def __init__(self, start, end, unit_type):
                self.start = start
                self.end = end
                self.unit_type = unit_type

        units = []

        # 检测段落（空行分隔）
        paragraph_pattern = re.compile(r"\n\s*\n")
        last_end = 0

        for match in paragraph_pattern.finditer(text):
            if match.start() > last_end:
                units.append(StructureUnit(last_end, match.start(), "paragraph"))
            last_end = match.end()

        if last_end < len(text):
            units.append(StructureUnit(last_end, len(text), "paragraph"))

        return units

    def _find_safe_boundary(self, text: str, start: int, proposed_end: int) -> int:
        """在句子或单词边界处寻找安全的分块结束位置"""
        # 首先尝试在句子边界处结束
        sentence_end = proposed_end
        while sentence_end > start and sentence_end < len(text):
            if text[sentence_end] in ".!?。！？\n":
                return sentence_end + 1
            sentence_end -= 1

        # 其次尝试在单词边界处结束（空格）
        word_end = proposed_end
        while word_end > start and word_end < len(text):
            if text[word_end].isspace():
                return word_end + 1
            word_end -= 1

        return proposed_end

    async def _create_chunks_from_boundaries(
        self,
        text: str,
        sentences: List[Tuple[int, int, str]],
        boundaries: List[ChunkBoundary],
        strategy: str,
    ) -> List[ProcessedTextChunk]:
        """从边界创建分块"""
        chunks = []
        chunk_id = 0
        start_idx = 0

        boundary_positions = [b.start for b in boundaries] + [len(text)]

        for boundary in boundary_positions:
            if boundary <= start_idx:
                continue

            chunk_text = text[start_idx:boundary].strip()
            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                chunks.append(
                    await self._create_chunk(
                        chunk_text, start_idx, boundary, chunk_id, strategy
                    )
                )
                chunk_id += 1

            start_idx = boundary

        return chunks

    async def _create_chunk(
        self, text: str, start: int, end: int, chunk_id: int, strategy: str
    ) -> ProcessedTextChunk:
        """创建分块对象"""
        return ProcessedTextChunk(
            content=text,
            chunk_id=f"{strategy}_{chunk_id}",
            start_position=start,
            end_position=end,
            semantic_score=await self._calculate_semantic_score(text),
            quality_score=await self._calculate_quality_score(text),
            entities=[],  # 由实体提取器后续填充
            metadata={
                "chunking_strategy": strategy,
                "original_length": len(text),
                "word_count": len(text.split()),
            },
        )

    async def _calculate_semantic_score(self, text: str) -> float:
        """计算分块的语义连贯性分数"""
        # 简化实现 - 实际应使用更复杂的语义分析
        words = text.split()
        if len(words) < 5:
            return 0.6

        # 基于句子结构和词汇多样性评分
        sentence_count = len(re.findall(r"[.!?。！？]", text))
        unique_words = len(set(words))
        lexical_diversity = unique_words / len(words) if words else 0

        score = 0.3 * min(sentence_count / 3, 1.0) + 0.7 * lexical_diversity
        return min(score, 1.0)

    async def _calculate_quality_score(self, text: str) -> float:
        """计算分块质量分数"""
        # 基于文本长度、完整性和可读性评分
        length_score = min(len(text) / self.config.chunk_size, 1.0)

        # 检查文本完整性（是否在句子中间被切断）
        completeness_score = 1.0
        if text and text[-1] not in ".!?。！？\n":
            completeness_score = 0.7

        # 基本可读性检查
        readability_score = 1.0
        if len(text.split()) < 3:
            readability_score = 0.5

        final_score = (
            0.4 * length_score + 0.4 * completeness_score + 0.2 * readability_score
        )
        return final_score

    async def _validate_chunks(
        self, chunks: List[ProcessedTextChunk], original_text: str
    ) -> List[ProcessedTextChunk]:
        """验证分块质量并过滤不合格的分块"""
        valid_chunks = []

        for chunk in chunks:
            # 检查分块长度
            if len(chunk.content) < self.config.min_chunk_size:
                logger.warning(f"分块 {chunk.chunk_id} 过短，已跳过")
                continue

            if len(chunk.content) > self.config.max_chunk_size:
                logger.warning(f"分块 {chunk.chunk_id} 过长，已跳过")
                continue

            # 检查内容质量
            if chunk.quality_score < 0.3:
                logger.warning(f"分块 {chunk.chunk_id} 质量过低，已跳过")
                continue

            # 验证文本内容匹配
            original_segment = original_text[chunk.start_position : chunk.end_position]
            if chunk.content != original_segment:
                logger.warning(f"分块 {chunk.chunk_id} 内容不匹配，已校正")
                chunk.content = original_segment

            valid_chunks.append(chunk)

        logger.info(f"分块验证完成: {len(valid_chunks)}/{len(chunks)} 个分块有效")
        return valid_chunks

    async def _evaluate_chunk_quality(self, chunks: List[ProcessedTextChunk]) -> float:
        """评估分块方案的整体质量"""
        if not chunks:
            return 0.0

        total_score = 0.0
        for chunk in chunks:
            total_score += chunk.quality_score * chunk.semantic_score

        return total_score / len(chunks)


# 注册处理器
register_processor("intelligent_chunker", IntelligentChunker)
logger.info("智能分块器注册完成")
