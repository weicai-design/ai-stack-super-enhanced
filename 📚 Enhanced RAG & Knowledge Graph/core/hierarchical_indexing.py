"""
Hierarchical Indexing
层次化索引

实现自适应分块和层次化索引（差距6）：
1. 多粒度分块（句子、段落、章节）
2. 层次化索引构建
3. 根据查询复杂度选择检索粒度
4. 自适应分块策略
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class GranularityLevel(Enum):
    """粒度级别"""
    SENTENCE = "sentence"  # 句子级
    PARAGRAPH = "paragraph"  # 段落级
    SECTION = "section"  # 章节级
    DOCUMENT = "document"  # 文档级


@dataclass
class HierarchicalChunk:
    """层次化分块"""
    id: str
    content: str
    level: GranularityLevel
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    start_pos: int = 0
    end_pos: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class HierarchicalIndex:
    """
    层次化索引
    
    支持多粒度分块和检索
    """

    def __init__(
        self,
        min_sentence_length: int = 50,
        min_paragraph_length: int = 200,
        min_section_length: int = 500,
    ):
        """
        初始化层次化索引
        
        Args:
            min_sentence_length: 最小句子长度
            min_paragraph_length: 最小段落长度
            min_section_length: 最小章节长度
        """
        self.min_sentence_length = min_sentence_length
        self.min_paragraph_length = min_paragraph_length
        self.min_section_length = min_section_length
        
        # 索引存储：{level: {chunk_id: HierarchicalChunk}}
        self.index: Dict[GranularityLevel, Dict[str, HierarchicalChunk]] = {
            level: {} for level in GranularityLevel
        }
        
        # 文档ID映射：{doc_id: {level: [chunk_ids]}}
        self.doc_index: Dict[str, Dict[GranularityLevel, List[str]]] = {}

    def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[str]]:
        """
        索引文档（多粒度分块）
        
        Args:
            doc_id: 文档ID
            text: 文档文本
            metadata: 文档元数据
            
        Returns:
            每个粒度级别的分块ID列表
        """
        metadata = metadata or {}
        
        # 1. 句子级分块
        sentence_chunks = self._split_sentences(text, doc_id)
        
        # 2. 段落级分块（基于句子）
        paragraph_chunks = self._split_paragraphs(text, sentence_chunks, doc_id)
        
        # 3. 章节级分块（基于段落）
        section_chunks = self._split_sections(text, paragraph_chunks, doc_id)
        
        # 4. 文档级（整个文档作为一个分块）
        doc_chunk = self._create_document_chunk(text, doc_id, metadata)
        
        # 5. 构建层次关系
        self._build_hierarchy(
            sentence_chunks, paragraph_chunks, section_chunks, doc_chunk
        )
        
        # 6. 存储到索引
        chunk_ids = {
            GranularityLevel.SENTENCE: [c.id for c in sentence_chunks],
            GranularityLevel.PARAGRAPH: [c.id for c in paragraph_chunks],
            GranularityLevel.SECTION: [c.id for c in section_chunks],
            GranularityLevel.DOCUMENT: [doc_chunk.id],
        }
        
        self.doc_index[doc_id] = chunk_ids
        
        # 存储所有分块
        for chunk in sentence_chunks:
            self.index[GranularityLevel.SENTENCE][chunk.id] = chunk
        for chunk in paragraph_chunks:
            self.index[GranularityLevel.PARAGRAPH][chunk.id] = chunk
        for chunk in section_chunks:
            self.index[GranularityLevel.SECTION][chunk.id] = chunk
        self.index[GranularityLevel.DOCUMENT][doc_chunk.id] = doc_chunk
        
        logger.debug(
            f"文档 {doc_id} 索引完成: "
            f"句子={len(sentence_chunks)}, "
            f"段落={len(paragraph_chunks)}, "
            f"章节={len(section_chunks)}"
        )
        
        return chunk_ids

    def _split_sentences(self, text: str, doc_id: str) -> List[HierarchicalChunk]:
        """
        分割为句子级分块
        """
        import re
        
        # 句子分隔符（中英文）
        sentence_pattern = re.compile(r'([。！？.!?]\s*)')
        sentences = sentence_pattern.split(text)
        
        chunks = []
        current_pos = 0
        
        i = 0
        while i < len(sentences):
            if i % 2 == 0:  # 句子内容
                sentence_text = sentences[i].strip()
                if len(sentence_text) >= self.min_sentence_length:
                    chunk_id = f"{doc_id}-sent-{len(chunks)}"
                    chunk = HierarchicalChunk(
                        id=chunk_id,
                        content=sentence_text,
                        level=GranularityLevel.SENTENCE,
                        start_pos=current_pos,
                        end_pos=current_pos + len(sentence_text),
                    )
                    chunks.append(chunk)
                    current_pos += len(sentences[i])
                    if i + 1 < len(sentences):
                        current_pos += len(sentences[i + 1])  # 分隔符
                else:
                    current_pos += len(sentences[i])
                    if i + 1 < len(sentences):
                        current_pos += len(sentences[i + 1])
            i += 1
        
        return chunks

    def _split_paragraphs(
        self,
        text: str,
        sentence_chunks: List[HierarchicalChunk],
        doc_id: str,
    ) -> List[HierarchicalChunk]:
        """
        分割为段落级分块
        """
        # 段落分隔符（双换行）
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_pos = 0
        sentence_idx = 0
        
        for para_idx, para_text in enumerate(paragraphs):
            para_text = para_text.strip()
            if len(para_text) >= self.min_paragraph_length:
                # 找到属于这个段落的句子
                para_sentence_ids = []
                for sent_chunk in sentence_chunks:
                    if (sent_chunk.start_pos >= current_pos and
                        sent_chunk.start_pos < current_pos + len(para_text)):
                        para_sentence_ids.append(sent_chunk.id)
                
                chunk_id = f"{doc_id}-para-{para_idx}"
                chunk = HierarchicalChunk(
                    id=chunk_id,
                    content=para_text,
                    level=GranularityLevel.PARAGRAPH,
                    start_pos=current_pos,
                    end_pos=current_pos + len(para_text),
                    children_ids=para_sentence_ids,
                )
                chunks.append(chunk)
            
            current_pos += len(para_text) + 2  # +2 for \n\n
        
        return chunks

    def _split_sections(
        self,
        text: str,
        paragraph_chunks: List[HierarchicalChunk],
        doc_id: str,
    ) -> List[HierarchicalChunk]:
        """
        分割为章节级分块
        """
        import re
        
        # 章节标记（标题）
        section_pattern = re.compile(r'^#{1,6}\s+.*$', re.MULTILINE)
        section_markers = list(section_pattern.finditer(text))
        
        chunks = []
        current_pos = 0
        
        for i, marker in enumerate(section_markers):
            section_start = marker.start()
            
            # 找到属于这个章节的段落
            section_para_ids = []
            for para_chunk in paragraph_chunks:
                if (para_chunk.start_pos >= section_start and
                    (i + 1 >= len(section_markers) or
                     para_chunk.end_pos <= section_markers[i + 1].start())):
                    section_para_ids.append(para_chunk.id)
            
            # 提取章节内容
            section_end = section_markers[i + 1].start() if i + 1 < len(section_markers) else len(text)
            section_text = text[section_start:section_end].strip()
            
            if len(section_text) >= self.min_section_length:
                chunk_id = f"{doc_id}-sect-{i}"
                chunk = HierarchicalChunk(
                    id=chunk_id,
                    content=section_text,
                    level=GranularityLevel.SECTION,
                    start_pos=section_start,
                    end_pos=section_end,
                    children_ids=section_para_ids,
                )
                chunks.append(chunk)
        
        # 如果没有章节标记，将整个文档作为一个章节
        if not chunks and paragraph_chunks:
            chunk_id = f"{doc_id}-sect-0"
            chunk = HierarchicalChunk(
                id=chunk_id,
                content=text,
                level=GranularityLevel.SECTION,
                start_pos=0,
                end_pos=len(text),
                children_ids=[p.id for p in paragraph_chunks],
            )
            chunks.append(chunk)
        
        return chunks

    def _create_document_chunk(
        self,
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
    ) -> HierarchicalChunk:
        """
        创建文档级分块
        """
        chunk_id = f"{doc_id}-doc"
        return HierarchicalChunk(
            id=chunk_id,
            content=text,
            level=GranularityLevel.DOCUMENT,
            metadata=metadata,
            start_pos=0,
            end_pos=len(text),
        )

    def _build_hierarchy(
        self,
        sentence_chunks: List[HierarchicalChunk],
        paragraph_chunks: List[HierarchicalChunk],
        section_chunks: List[HierarchicalChunk],
        doc_chunk: HierarchicalChunk,
    ) -> None:
        """
        构建层次关系
        """
        # 文档级 -> 章节级
        doc_chunk.children_ids = [s.id for s in section_chunks]
        for section_chunk in section_chunks:
            section_chunk.parent_id = doc_chunk.id
        
        # 章节级 -> 段落级（已在_split_sections中设置）
        # 段落级 -> 句子级（已在_split_paragraphs中设置）
        for para_chunk in paragraph_chunks:
            for sent_id in para_chunk.children_ids:
                # 找到对应的句子chunk
                for sent_chunk in sentence_chunks:
                    if sent_chunk.id == sent_id:
                        sent_chunk.parent_id = para_chunk.id
                        break

    def select_granularity(
        self,
        query: str,
        query_complexity: Optional[str] = None,
    ) -> GranularityLevel:
        """
        根据查询复杂度选择检索粒度
        
        Args:
            query: 查询文本
            query_complexity: 查询复杂度（simple, medium, complex）
            
        Returns:
            推荐的粒度级别
        """
        if query_complexity is None:
            # 简单启发式：根据查询长度和关键词数量
            query_words = len(query.split())
            if query_words <= 3:
                query_complexity = "simple"
            elif query_words <= 8:
                query_complexity = "medium"
            else:
                query_complexity = "complex"
        
        if query_complexity == "simple":
            # 简单查询：使用句子级或段落级
            return GranularityLevel.SENTENCE
        elif query_complexity == "medium":
            # 中等查询：使用段落级或章节级
            return GranularityLevel.PARAGRAPH
        else:
            # 复杂查询：使用章节级或文档级
            return GranularityLevel.SECTION

    def retrieve(
        self,
        query_embedding: Any,
        top_k: int = 5,
        granularity: Optional[GranularityLevel] = None,
        doc_ids: Optional[List[str]] = None,
    ) -> List[HierarchicalChunk]:
        """
        从层次化索引检索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            granularity: 检索粒度（如果None则自动选择）
            doc_ids: 限制检索的文档ID列表（可选）
            
        Returns:
            检索到的分块列表
        """
        # 如果没有指定粒度，使用文档级作为默认
        if granularity is None:
            granularity = GranularityLevel.DOCUMENT
        
        # 获取对应粒度的索引
        level_index = self.index.get(granularity, {})
        
        # 如果没有对应粒度的索引，使用最接近的粒度
        if not level_index:
            for level in [GranularityLevel.SECTION, GranularityLevel.PARAGRAPH, GranularityLevel.SENTENCE]:
                if self.index[level]:
                    granularity = level
                    level_index = self.index[granularity]
                    break
        
        # 简化实现：返回所有分块（实际应该使用向量相似度）
        # TODO: 集成向量相似度计算
        chunks = list(level_index.values())
        
        # 如果指定了文档ID，过滤分块
        if doc_ids:
            filtered_chunks = []
            for chunk in chunks:
                # 从chunk ID提取doc_id
                chunk_doc_id = chunk.id.split('-')[0]
                if chunk_doc_id in doc_ids:
                    filtered_chunks.append(chunk)
            chunks = filtered_chunks
        
        return chunks[:top_k]


# 全局层次化索引实例
_global_hierarchical_index: Optional[HierarchicalIndex] = None


def get_hierarchical_index() -> HierarchicalIndex:
    """
    获取层次化索引实例（单例模式）
    
    Returns:
        HierarchicalIndex实例
    """
    global _global_hierarchical_index
    
    if _global_hierarchical_index is None:
        _global_hierarchical_index = HierarchicalIndex()
    
    return _global_hierarchical_index

