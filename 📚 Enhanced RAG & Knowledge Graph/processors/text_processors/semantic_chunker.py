"""
语义分块器
基于语义边界智能分割文本，保持上下文完整性
"""
from typing import List, Dict, Optional
import re


class SemanticChunker:
    """语义分块器"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        初始化语义分块器
        
        Args:
            chunk_size: 目标块大小（字符数）
            chunk_overlap: 块之间的重叠（字符数）
            min_chunk_size: 最小块大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str, strategy: str = "semantic") -> List[Dict]:
        """
        分块文本
        
        Args:
            text: 要分块的文本
            strategy: 分块策略（semantic, paragraph, sentence, fixed）
            
        Returns:
            分块结果列表
        """
        if strategy == "semantic":
            return self._semantic_chunk(text)
        elif strategy == "paragraph":
            return self._paragraph_chunk(text)
        elif strategy == "sentence":
            return self._sentence_chunk(text)
        elif strategy == "fixed":
            return self._fixed_chunk(text)
        else:
            return self._semantic_chunk(text)
    
    def _semantic_chunk(self, text: str) -> List[Dict]:
        """
        语义分块
        
        基于语义边界识别（段落、标题、列表等）
        """
        chunks = []
        
        # 1. 首先按段落分割
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = ""
        chunk_id = 0
        
        for para in paragraphs:
            # 如果当前块加上新段落不超过限制，合并
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                # 保存当前块
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": current_chunk.strip(),
                        "size": len(current_chunk),
                        "type": "semantic"
                    })
                    chunk_id += 1
                
                # 开始新块（保留重叠）
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + para + "\n\n"
        
        # 保存最后一块
        if current_chunk.strip():
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "size": len(current_chunk),
                "type": "semantic"
            })
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        # 按双换行符分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _paragraph_chunk(self, text: str) -> List[Dict]:
        """按段落分块"""
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        for i, para in enumerate(paragraphs):
            chunks.append({
                "chunk_id": i,
                "text": para,
                "size": len(para),
                "type": "paragraph"
            })
        
        return chunks
    
    def _sentence_chunk(self, text: str) -> List[Dict]:
        """按句子分块"""
        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for sent in sentences:
            if len(current_chunk) + len(sent) <= self.chunk_size:
                current_chunk += sent + "。"
            else:
                if current_chunk:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": current_chunk.strip(),
                        "size": len(current_chunk),
                        "type": "sentence"
                    })
                    chunk_id += 1
                current_chunk = sent + "。"
        
        if current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "text": current_chunk.strip(),
                "size": len(current_chunk),
                "type": "sentence"
            })
        
        return chunks
    
    def _fixed_chunk(self, text: str) -> List[Dict]:
        """固定大小分块"""
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            
            if chunk_text:
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "size": len(chunk_text),
                    "type": "fixed"
                })
                chunk_id += 1
        
        return chunks
    
    def identify_semantic_boundaries(self, text: str) -> List[int]:
        """
        识别语义边界位置
        
        识别段落、标题、列表等结构
        
        Returns:
            边界位置列表
        """
        boundaries = []
        
        # 段落边界
        for match in re.finditer(r'\n\s*\n', text):
            boundaries.append(match.start())
        
        # 标题边界（Markdown格式）
        for match in re.finditer(r'^#+\s+', text, re.MULTILINE):
            boundaries.append(match.start())
        
        # 列表边界
        for match in re.finditer(r'^\s*[-*•]\s+', text, re.MULTILINE):
            boundaries.append(match.start())
        
        return sorted(set(boundaries))
    
    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        """获取分块统计信息"""
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0
            }
        
        sizes = [c["size"] for c in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(sizes),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "chunk_types": list(set(c["type"] for c in chunks))
        }


# 使用示例
if __name__ == "__main__":
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
    
    test_text = """
# AI技术发展报告

## 引言
人工智能技术在过去十年取得了巨大进展。深度学习、大语言模型等技术的突破，使得AI在各个领域都有了广泛应用。

## 技术趋势
1. 大语言模型持续发展
2. 多模态AI成为热点
3. AI与传统行业深度融合

## 应用案例
在企业管理中，AI已经可以帮助进行数据分析、决策支持、流程优化等工作。

## 总结
AI技术将继续快速发展，为人类社会带来深刻变革。
    """
    
    print("✅ 语义分块器已加载\n")
    
    # 测试不同策略
    for strategy in ["semantic", "paragraph", "sentence"]:
        chunks = chunker.chunk(test_text, strategy=strategy)
        stats = chunker.get_chunk_statistics(chunks)
        
        print(f"📊 {strategy}策略:")
        print(f"  分块数: {stats['total_chunks']}")
        print(f"  平均大小: {stats['avg_chunk_size']:.0f}字符")
        print()


