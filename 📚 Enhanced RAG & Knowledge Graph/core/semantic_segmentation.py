"""
Semantic Segmentation Optimizer
语义分割优化器

实现SAGE风格的语义分割优化：
1. 语义边界识别
2. 语义完整性保证
3. 智能分块策略
4. 语义感知分块
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SemanticChunk:
    """语义分块"""
    id: str
    content: str
    start_pos: int
    end_pos: int
    semantic_score: float  # 语义完整性分数
    boundary_type: str  # 边界类型（sentence, paragraph, section等）
    metadata: Dict[str, Any] = None


class SemanticSegmentationOptimizer:
    """
    语义分割优化器
    
    实现SAGE风格的语义分割，提升检索相关性
    """

    def __init__(
        self,
        embedding_model: Any = None,
        min_chunk_size: int = 100,
        max_chunk_size: int = 512,
        semantic_threshold: float = 0.7,
    ):
        """
        初始化语义分割优化器
        
        Args:
            embedding_model: 嵌入模型（用于语义分析）
            min_chunk_size: 最小分块大小
            max_chunk_size: 最大分块大小
            semantic_threshold: 语义完整性阈值
        """
        self.embedding_model = embedding_model
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.semantic_threshold = semantic_threshold
        
        # 句子分割模式
        self.sentence_patterns = [
            re.compile(r'[。！？]'),  # 中文句子
            re.compile(r'[.!?]\s+'),  # 英文句子
            re.compile(r'\n\n+'),  # 段落分隔
        ]
        
        # 结构标记
        self.structure_markers = [
            r'^#{1,6}\s',  # Markdown标题
            r'^\d+\.',  # 编号列表
            r'^[-*]\s',  # 列表项
            r'^```',  # 代码块
        ]

    async def segment_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
    ) -> List[SemanticChunk]:
        """
        语义分割文本
        
        Args:
            text: 文本内容
            doc_id: 文档ID（可选）
            
        Returns:
            语义分块列表
        """
        if not text:
            return []
        
        # 第一步：识别语义边界
        boundaries = self._identify_semantic_boundaries(text)
        
        # 第二步：基于边界创建初始分块
        initial_chunks = self._create_chunks_from_boundaries(text, boundaries)
        
        # 第三步：评估和优化分块
        optimized_chunks = await self._optimize_chunks(initial_chunks, text)
        
        # 第四步：合并小分块
        final_chunks = self._merge_small_chunks(optimized_chunks)
        
        logger.debug(f"语义分割完成：{len(final_chunks)} 个分块")
        return final_chunks

    def _identify_semantic_boundaries(self, text: str) -> List[int]:
        """
        识别语义边界
        
        返回边界位置列表（字符索引）
        """
        boundaries = [0]  # 文档开始
        
        # 1. 识别句子边界
        for pattern in self.sentence_patterns:
            for match in pattern.finditer(text):
                boundaries.append(match.end())
        
        # 2. 识别结构边界（段落、标题等）
        lines = text.split('\n')
        current_pos = 0
        for line in lines:
            # 检查是否是结构标记
            is_structure = any(
                re.match(marker, line) for marker in self.structure_markers
            )
            
            if is_structure:
                boundaries.append(current_pos)
            
            current_pos += len(line) + 1  # +1 for newline
        
        # 3. 添加文档结束
        boundaries.append(len(text))
        
        # 去重并排序
        boundaries = sorted(list(set(boundaries)))
        
        return boundaries

    def _create_chunks_from_boundaries(
        self,
        text: str,
        boundaries: List[int],
    ) -> List[SemanticChunk]:
        """
        基于边界创建初始分块
        """
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_pos = boundaries[i]
            end_pos = boundaries[i + 1]
            content = text[start_pos:end_pos].strip()
            
            if len(content) < self.min_chunk_size:
                continue  # 跳过太小的分块
            
            # 确定边界类型
            boundary_type = self._determine_boundary_type(content, start_pos, text)
            
            chunk = SemanticChunk(
                id=f"chunk_{start_pos}_{end_pos}",
                content=content,
                start_pos=start_pos,
                end_pos=end_pos,
                semantic_score=0.5,  # 初始分数
                boundary_type=boundary_type,
            )
            chunks.append(chunk)
        
        return chunks

    def _determine_boundary_type(
        self,
        content: str,
        start_pos: int,
        full_text: str,
    ) -> str:
        """
        确定边界类型
        """
        # 检查是否是标题
        if re.match(r'^#{1,6}\s', content):
            return "heading"
        
        # 检查是否是代码块
        if content.startswith('```'):
            return "code_block"
        
        # 检查是否是列表
        if re.match(r'^\d+\.|^[-*]', content):
            return "list"
        
        # 检查段落分隔
        if '\n\n' in full_text[max(0, start_pos-10):start_pos+10]:
            return "paragraph"
        
        # 检查句子
        if any(marker in content for marker in ['。', '！', '？', '.', '!', '?']):
            return "sentence"
        
        return "text"

    async def _optimize_chunks(
        self,
        chunks: List[SemanticChunk],
        full_text: str,
    ) -> List[SemanticChunk]:
        """
        优化分块的语义完整性
        
        使用嵌入模型评估语义完整性
        """
        if not chunks:
            return []
        
        # 如果没有嵌入模型，使用简单规则
        if not self.embedding_model:
            return self._optimize_chunks_without_model(chunks)
        
        try:
            # 计算每个分块的语义完整性分数
            for chunk in chunks:
                # 计算分块内语义一致性
                semantic_score = await self._calculate_semantic_score(chunk, full_text)
                chunk.semantic_score = semantic_score
                
                # 如果分数太低，尝试扩展边界
                if semantic_score < self.semantic_threshold:
                    self._expand_chunk_boundary(chunk, full_text)
                    # 重新计算分数
                    chunk.semantic_score = await self._calculate_semantic_score(chunk, full_text)
            
            return chunks
        except Exception as e:
            logger.warning(f"语义优化失败，使用简单规则: {e}")
            return self._optimize_chunks_without_model(chunks)

    async def _calculate_semantic_score(
        self,
        chunk: SemanticChunk,
        full_text: str,
    ) -> float:
        """
        计算分块的语义完整性分数
        
        Returns:
            语义完整性分数（0-1）
        """
        # 简化实现：基于多个因素计算
        
        score = 0.5  # 基础分数
        
        content = chunk.content
        
        # 1. 长度因子（偏好中等长度）
        length_factor = self._calculate_length_factor(len(content))
        score += length_factor * 0.2
        
        # 2. 结构完整性（有明确的开始和结束）
        has_start = bool(re.match(r'^#{1,6}|^\d+\.|^[-*]', content))
        has_end = bool(content.rstrip().endswith(('.', '。', '!', '！', '?', '？')))
        if has_start and has_end:
            score += 0.2
        elif has_start or has_end:
            score += 0.1
        
        # 3. 句子完整性（包含完整句子）
        sentence_count = len(re.findall(r'[。！？.!?]', content))
        if sentence_count >= 2:
            score += 0.1
        
        # 4. 如果使用嵌入模型，可以计算语义一致性
        # （这里简化处理）
        
        return min(1.0, score)

    def _calculate_length_factor(self, length: int) -> float:
        """计算长度因子"""
        if length < self.min_chunk_size:
            return 0.5
        elif length <= self.max_chunk_size:
            return 1.0
        else:
            # 超长分块，根据超出程度降低分数
            excess = length - self.max_chunk_size
            return max(0.5, 1.0 - (excess / self.max_chunk_size))

    def _expand_chunk_boundary(
        self,
        chunk: SemanticChunk,
        full_text: str,
    ) -> None:
        """
        扩展分块边界以提升语义完整性
        """
        # 向前扩展（最多50个字符）
        expand_forward = min(50, chunk.start_pos)
        if expand_forward > 0:
            # 查找最近的句子边界
            search_text = full_text[max(0, chunk.start_pos - 100):chunk.start_pos]
            for pattern in self.sentence_patterns:
                matches = list(pattern.finditer(search_text))
                if matches:
                    last_match = matches[-1]
                    expand_pos = last_match.end()
                    chunk.start_pos = max(0, chunk.start_pos - expand_pos)
                    chunk.content = full_text[chunk.start_pos:chunk.end_pos]
                    break
        
        # 向后扩展（最多50个字符）
        expand_backward = min(50, len(full_text) - chunk.end_pos)
        if expand_backward > 0:
            # 查找最近的句子边界
            search_text = full_text[chunk.end_pos:chunk.end_pos + 100]
            for pattern in self.sentence_patterns:
                matches = list(pattern.finditer(search_text))
                if matches:
                    first_match = matches[0]
                    expand_pos = first_match.end()
                    chunk.end_pos = min(len(full_text), chunk.end_pos + expand_pos)
                    chunk.content = full_text[chunk.start_pos:chunk.end_pos]
                    break

    def _optimize_chunks_without_model(
        self,
        chunks: List[SemanticChunk],
    ) -> List[SemanticChunk]:
        """
        不使用模型的简单优化
        """
        for chunk in chunks:
            # 基于规则的语义分数
            score = 0.5
            
            # 长度因子
            length_factor = self._calculate_length_factor(len(chunk.content))
            score += length_factor * 0.3
            
            # 结构完整性
            if chunk.boundary_type in ["heading", "paragraph", "sentence"]:
                score += 0.2
            
            chunk.semantic_score = min(1.0, score)
        
        return chunks

    def _merge_small_chunks(
        self,
        chunks: List[SemanticChunk],
    ) -> List[SemanticChunk]:
        """
        合并过小的分块
        """
        if not chunks:
            return []
        
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
                continue
            
            # 如果当前分块太小，尝试合并
            if len(current_chunk.content) < self.min_chunk_size:
                # 合并到下一个分块
                merged_content = current_chunk.content + "\n\n" + chunk.content
                if len(merged_content) <= self.max_chunk_size:
                    current_chunk.content = merged_content
                    current_chunk.end_pos = chunk.end_pos
                    current_chunk.semantic_score = (
                        current_chunk.semantic_score + chunk.semantic_score
                    ) / 2
                    continue
            
            # 保存当前分块，开始新分块
            merged_chunks.append(current_chunk)
            current_chunk = chunk
        
        # 添加最后一个分块
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        return merged_chunks


# 全局语义分割优化器实例
_global_segmentation_optimizer: Optional[SemanticSegmentationOptimizer] = None


def get_semantic_segmentation_optimizer(
    embedding_model: Any = None,
) -> SemanticSegmentationOptimizer:
    """
    获取语义分割优化器实例（单例模式）
    
    Args:
        embedding_model: 嵌入模型（可选）
        
    Returns:
        SemanticSegmentationOptimizer实例
    """
    global _global_segmentation_optimizer
    
    if _global_segmentation_optimizer is None:
        _global_segmentation_optimizer = SemanticSegmentationOptimizer(
            embedding_model=embedding_model,
        )
    
    return _global_segmentation_optimizer

