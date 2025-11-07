"""
文本处理器 - 文本分块和预处理
"""

import re
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """
    文本处理器
    
    负责：
    1. 文本分块（Chunking）
    2. 文本清洗
    3. 文本标准化
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化文本处理器"""
        self.config = config or self._get_default_config()
        logger.info("📝 文本处理器初始化完成")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "chunk_size": 512,
            "chunk_overlap": 50,
            "chunk_method": "semantic",  # fixed, sentence, semantic
            "min_chunk_size": 10,
            "max_chunk_size": 2000
        }
    
    def split_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        分割文本为块
        
        Args:
            text: 输入文本
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            method: 分块方法（fixed, sentence, semantic）
            
        Returns:
            文本块列表
        """
        chunk_size = chunk_size or self.config["chunk_size"]
        chunk_overlap = chunk_overlap or self.config["chunk_overlap"]
        method = method or self.config["chunk_method"]
        
        logger.info(f"📄 分割文本: {len(text)}字符 → {chunk_size}字符/块")
        
        if method == "fixed":
            chunks = self._split_fixed(text, chunk_size, chunk_overlap)
        elif method == "sentence":
            chunks = self._split_by_sentence(text, chunk_size, chunk_overlap)
        elif method == "semantic":
            chunks = self._split_semantic(text, chunk_size, chunk_overlap)
        else:
            chunks = self._split_fixed(text, chunk_size, chunk_overlap)
        
        # 添加元数据
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "chunk_id": i,
                "content": chunk,
                "length": len(chunk),
                "start_pos": text.find(chunk),
                "method": method
            })
        
        logger.info(f"✅ 分割完成: {len(result)}个块")
        return result
    
    def _split_fixed(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """固定大小分块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def _split_by_sentence(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """按句子分块"""
        # 分句（支持中英文）
        sentences = re.split(r'([。！？.!?]\s*)', text)
        sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2] + [''])]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_semantic(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """语义分块（基于段落和句子）"""
        # 先按段落分
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前块+段落不超过大小，直接添加
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                # 保存当前块
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                # 如果段落本身很长，需要进一步分句
                if len(para) > chunk_size:
                    sub_chunks = self._split_by_sentence(para, chunk_size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def clean_text(self, text: str) -> str:
        """
        清洗文本
        
        - 删除多余空白
        - 删除特殊字符
        - 标准化换行符
        """
        # 标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 删除多余空白
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 删除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def normalize_text(self, text: str) -> str:
        """
        标准化文本
        
        - 统一标点符号
        - 删除URL
        - 删除邮箱
        """
        # 删除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 删除邮箱
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        return text
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取关键词（简单实现）
        
        Args:
            text: 输入文本
            top_k: 返回前K个关键词
            
        Returns:
            关键词列表
        """
        # 简单实现：基于词频
        # TODO: 可以使用jieba、TF-IDF等更高级的方法
        
        # 分词（简单的基于空格）
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) > 2:  # 只统计长度>2的词
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 排序并返回
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]


def test_text_processor():
    """测试文本处理器"""
    print("="*70)
    print("  文本处理器测试")
    print("="*70)
    
    processor = TextProcessor()
    
    # 测试文本
    test_text = """
    这是第一段文本。它包含多个句子。用于测试分块功能。
    
    这是第二段文本！它也包含多个句子？测试不同的分块方法。
    
    This is the third paragraph. It contains English sentences. For testing purposes.
    """
    
    print(f"\n原始文本长度: {len(test_text)}字符\n")
    
    # 测试固定分块
    print("1. 固定大小分块:")
    chunks = processor.split_text(test_text, chunk_size=50, method="fixed")
    for chunk in chunks[:3]:
        print(f"   块{chunk['chunk_id']}: {chunk['length']}字符")
    
    # 测试句子分块
    print("\n2. 按句子分块:")
    chunks = processor.split_text(test_text, chunk_size=100, method="sentence")
    for chunk in chunks:
        print(f"   块{chunk['chunk_id']}: {chunk['length']}字符")
    
    # 测试文本清洗
    print("\n3. 文本清洗:")
    dirty_text = "这是    多余空白\n\n\n\n的文本"
    clean = processor.clean_text(dirty_text)
    print(f"   原文: '{dirty_text}'")
    print(f"   清洗后: '{clean}'")
    
    # 测试关键词提取
    print("\n4. 关键词提取:")
    keywords = processor.extract_keywords(test_text, top_k=5)
    print(f"   关键词: {keywords}")
    
    print("\n✅ 文本处理器测试完成！")


if __name__ == "__main__":
    test_text_processor()






