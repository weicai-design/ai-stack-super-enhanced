"""
引用溯源功能
Source Tracking & Citation

功能：
1. 追踪答案来源
2. 生成引用标注
3. 源文档链接管理
4. 可信度评分

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SourceReference:
    """源引用"""
    
    def __init__(
        self,
        doc_id: str,
        title: str,
        snippet: str,
        relevance: float = 0.0,
        page: Optional[int] = None,
        url: Optional[str] = None
    ):
        """
        初始化源引用
        
        Args:
            doc_id: 文档ID
            title: 文档标题
            snippet: 文本片段
            relevance: 相关度得分
            page: 页码（如适用）
            url: 文档URL（如有）
        """
        self.doc_id = doc_id
        self.title = title
        self.snippet = snippet
        self.relevance = relevance
        self.page = page
        self.url = url
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "doc_id": self.doc_id,
            "title": self.title,
            "snippet": self.snippet,
            "relevance": self.relevance
        }
        if self.page is not None:
            result["page"] = self.page
        if self.url:
            result["url"] = self.url
        return result
    
    def to_citation(self, index: int) -> str:
        """生成引用格式"""
        citation = f"[{index}] {self.title}"
        if self.page:
            citation += f", 第{self.page}页"
        if self.url:
            citation += f" ({self.url})"
        return citation


class SourceTracker:
    """
    引用溯源追踪器
    
    功能：
    - 追踪答案与源文档的关联
    - 生成标准引用格式
    - 计算源可信度
    - 支持多种引用风格
    """
    
    def __init__(self, citation_style: str = "numeric"):
        """
        初始化溯源追踪器
        
        Args:
            citation_style: 引用风格（'numeric', 'author-year', 'footnote'）
        """
        self.citation_style = citation_style
        self.sources: List[SourceReference] = []
    
    def add_source(
        self,
        doc_id: str,
        title: str,
        snippet: str,
        relevance: float = 0.0,
        page: Optional[int] = None,
        url: Optional[str] = None
    ) -> SourceReference:
        """
        添加源文档
        
        Args:
            doc_id: 文档ID
            title: 文档标题
            snippet: 相关文本片段
            relevance: 相关度得分
            page: 页码
            url: 文档URL
            
        Returns:
            源引用对象
        """
        source = SourceReference(
            doc_id=doc_id,
            title=title,
            snippet=snippet,
            relevance=relevance,
            page=page,
            url=url
        )
        self.sources.append(source)
        logger.debug(f"添加源引用: {doc_id}, 相关度: {relevance:.2f}")
        return source
    
    def add_sources_batch(self, sources: List[Dict[str, Any]]):
        """
        批量添加源文档
        
        Args:
            sources: 源文档列表
        """
        for source in sources:
            self.add_source(
                doc_id=source.get("doc_id", ""),
                title=source.get("title", "未知文档"),
                snippet=source.get("snippet", ""),
                relevance=source.get("relevance", 0.0),
                page=source.get("page"),
                url=source.get("url")
            )
    
    def get_sources(
        self,
        min_relevance: float = 0.0,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取源文档列表
        
        Args:
            min_relevance: 最小相关度阈值
            limit: 最大返回数量
            
        Returns:
            源文档列表
        """
        # 过滤和排序
        filtered = [s for s in self.sources if s.relevance >= min_relevance]
        filtered.sort(key=lambda x: x.relevance, reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return [s.to_dict() for s in filtered]
    
    def generate_citations(
        self,
        format_type: str = "list"
    ) -> str:
        """
        生成引用列表
        
        Args:
            format_type: 格式类型（'list', 'inline', 'footnote'）
            
        Returns:
            格式化的引用文本
        """
        if not self.sources:
            return ""
        
        if format_type == "list":
            return self._generate_list_citations()
        elif format_type == "inline":
            return self._generate_inline_citations()
        elif format_type == "footnote":
            return self._generate_footnote_citations()
        else:
            return self._generate_list_citations()
    
    def _generate_list_citations(self) -> str:
        """生成列表式引用"""
        citations = []
        for i, source in enumerate(self.sources, 1):
            citations.append(source.to_citation(i))
        
        return "\n".join([
            "",
            "参考来源:",
            "-" * 50,
            *citations
        ])
    
    def _generate_inline_citations(self) -> str:
        """生成行内引用"""
        citations = []
        for i, source in enumerate(self.sources, 1):
            citations.append(f"[{i}]")
        return " ".join(citations)
    
    def _generate_footnote_citations(self) -> str:
        """生成脚注式引用"""
        footnotes = []
        for i, source in enumerate(self.sources, 1):
            footnotes.append(f"[{i}]: {source.title}")
            if source.page:
                footnotes[-1] += f", 第{source.page}页"
        
        return "\n".join(footnotes)
    
    def annotate_answer(
        self,
        answer: str,
        add_citations: bool = True
    ) -> str:
        """
        为答案添加引用标注
        
        Args:
            answer: 原始答案
            add_citations: 是否在末尾添加引用列表
            
        Returns:
            标注后的答案
        """
        if not self.sources:
            return answer
        
        # 为答案添加引用编号（简单实现）
        # TODO: 在v2.6.1中实现智能片段匹配
        annotated = answer
        
        # 在末尾添加引用列表
        if add_citations and self.sources:
            annotated += "\n" + self.generate_citations("list")
        
        return annotated
    
    def calculate_confidence(self) -> float:
        """
        计算整体置信度
        
        基于源文档数量和相关度
        
        Returns:
            置信度得分（0-1）
        """
        if not self.sources:
            return 0.0
        
        # 考虑源数量和平均相关度
        avg_relevance = sum(s.relevance for s in self.sources) / len(self.sources)
        source_count_factor = min(len(self.sources) / 3, 1.0)  # 3个源达到满分
        
        confidence = (avg_relevance * 0.7) + (source_count_factor * 0.3)
        
        return round(confidence, 3)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.sources:
            return {
                "source_count": 0,
                "avg_relevance": 0.0,
                "confidence": 0.0
            }
        
        return {
            "source_count": len(self.sources),
            "avg_relevance": round(
                sum(s.relevance for s in self.sources) / len(self.sources), 3
            ),
            "max_relevance": max(s.relevance for s in self.sources),
            "min_relevance": min(s.relevance for s in self.sources),
            "confidence": self.calculate_confidence(),
            "with_url": sum(1 for s in self.sources if s.url),
            "with_page": sum(1 for s in self.sources if s.page)
        }
    
    def clear(self):
        """清空所有源"""
        self.sources.clear()
        logger.debug("清空源引用")


# ==================== 便捷函数 ====================

def track_sources(sources: List[Dict[str, Any]]) -> SourceTracker:
    """
    便捷函数：创建SourceTracker并添加源
    
    Args:
        sources: 源文档列表
        
    Returns:
        SourceTracker对象
    """
    tracker = SourceTracker()
    tracker.add_sources_batch(sources)
    return tracker


def annotate_with_sources(answer: str, sources: List[Dict[str, Any]]) -> str:
    """
    便捷函数：为答案添加引用
    
    Args:
        answer: 原始答案
        sources: 源文档列表
        
    Returns:
        标注后的答案
    """
    tracker = track_sources(sources)
    return tracker.annotate_answer(answer, add_citations=True)

