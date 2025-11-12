"""
智能摘要器
支持抽取式摘要、生成式摘要、多文档摘要等功能
"""
from typing import List, Dict, Optional
import re
from collections import Counter


class IntelligentSummarizer:
    """智能摘要生成器"""
    
    def __init__(self, language: str = "zh"):
        """
        初始化摘要器
        
        Args:
            language: 语言（zh, en）
        """
        self.language = language
        
        # 中文停用词
        self.stop_words_zh = {
            '的', '了', '在', '是', '和', '有', '与', '等', '为', '这', '将', '可以',
            '能够', '进行', '通过', '使用', '我们', '他们', '其中', '因此', '如果',
            '但是', '所以', '然而', '并且', '或者', '虽然', '不过', '而且'
        }
    
    def summarize(
        self,
        text: str,
        method: str = "extractive",
        max_length: int = 200,
        num_sentences: int = 3
    ) -> Dict:
        """
        生成摘要
        
        Args:
            text: 输入文本
            method: 摘要方法（extractive, abstractive, hybrid）
            max_length: 最大长度
            num_sentences: 提取的句子数（抽取式）
            
        Returns:
            摘要结果
        """
        if method == "extractive":
            summary = self._extractive_summary(text, num_sentences)
        elif method == "abstractive":
            summary = self._abstractive_summary(text, max_length)
        elif method == "hybrid":
            # 混合：先抽取再生成
            extracted = self._extractive_summary(text, num_sentences)
            summary = self._abstractive_summary(extracted, max_length)
        else:
            summary = text[:max_length]
        
        return {
            "success": True,
            "original_length": len(text),
            "summary": summary,
            "summary_length": len(summary),
            "compression_ratio": f"{(1 - len(summary)/len(text))*100:.1f}%",
            "method": method
        }
    
    def _extractive_summary(self, text: str, num_sentences: int) -> str:
        """
        抽取式摘要
        
        从原文中抽取最重要的句子
        
        使用TextRank算法或基于TF-IDF
        """
        # 分句
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return text
        
        # 计算句子重要性得分
        sentence_scores = self._score_sentences(sentences, text)
        
        # 排序并选择top k句子
        sorted_sentences = sorted(
            enumerate(sentences),
            key=lambda x: sentence_scores[x[0]],
            reverse=True
        )
        
        # 选择top k，但按原文顺序排列
        selected_indices = sorted([idx for idx, _ in sorted_sentences[:num_sentences]])
        selected_sentences = [sentences[i] for i in selected_indices]
        
        return ''.join(selected_sentences)
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        # 按句号、问号、感叹号分割
        sentences = re.split(r'([。！？.!?]+)', text)
        
        # 重新组合（保留标点）
        result = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                sent = sentences[i] + sentences[i+1]
                if sent.strip():
                    result.append(sent)
        
        return result
    
    def _score_sentences(self, sentences: List[str], full_text: str) -> List[float]:
        """
        计算句子重要性得分
        
        基于：
        - 关键词频率
        - 句子位置
        - 句子长度
        """
        scores = []
        
        # 提取关键词
        keywords = self._extract_keywords(full_text, top_k=20)
        keyword_set = set(kw["word"] for kw in keywords)
        
        for i, sent in enumerate(sentences):
            score = 0.0
            
            # 1. 关键词得分
            words = re.findall(r'[\u4e00-\u9fa5]+', sent)
            keyword_count = sum(1 for w in words if w in keyword_set)
            score += keyword_count * 2
            
            # 2. 位置得分（首尾句子更重要）
            position_score = 0
            if i < 2:  # 开头
                position_score = 2
            elif i >= len(sentences) - 2:  # 结尾
                position_score = 1.5
            score += position_score
            
            # 3. 长度得分（避免太短的句子）
            if len(sent) > 20:
                score += 1
            
            scores.append(score)
        
        return scores
    
    def _abstractive_summary(self, text: str, max_length: int) -> str:
        """
        生成式摘要
        
        使用AI模型生成新的摘要文本
        
        实际实现需要使用：
        - GPT-3/GPT-4
        - BART
        - T5
        - 或中文模型（如CPM、ChatGLM）
        """
        # 模拟生成式摘要
        # 实际应调用LLM API
        
        if len(text) <= max_length:
            return text
        
        # 简化版：提取关键信息
        summary = f"本文主要讨论了...（实际使用中会调用GPT-4或其他LLM生成流畅的摘要）"
        
        return summary[:max_length]
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[Dict]:
        """提取关键词（用于重要性评分）"""
        words = re.findall(r'[\u4e00-\u9fa5]+', text)
        words = [w for w in words if len(w) >= 2 and w not in self.stop_words_zh]
        
        word_freq = Counter(words)
        
        keywords = []
        for word, freq in word_freq.most_common(top_k):
            keywords.append({
                "word": word,
                "frequency": freq,
                "score": freq / len(words) if words else 0
            })
        
        return keywords
    
    def multi_document_summary(
        self,
        documents: List[str],
        max_length: int = 500
    ) -> Dict:
        """
        多文档摘要
        
        对多个文档生成统一的摘要
        
        Args:
            documents: 文档列表
            max_length: 最大长度
            
        Returns:
            多文档摘要
        """
        # 合并文档
        combined_text = "\n\n".join(documents)
        
        # 生成摘要
        summary_result = self.summarize(combined_text, method="extractive", max_length=max_length)
        
        return {
            "success": True,
            "document_count": len(documents),
            "total_length": len(combined_text),
            "summary": summary_result["summary"],
            "compression_ratio": summary_result["compression_ratio"]
        }
    
    def query_focused_summary(
        self,
        text: str,
        query: str,
        max_length: int = 200
    ) -> Dict:
        """
        问题导向摘要
        
        生成针对特定问题的摘要
        
        Args:
            text: 文本
            query: 问题/查询
            max_length: 最大长度
            
        Returns:
            针对问题的摘要
        """
        # 提取查询关键词
        query_keywords = set(re.findall(r'[\u4e00-\u9fa5]+', query))
        query_keywords = {w for w in query_keywords if len(w) >= 2}
        
        # 找到与查询最相关的句子
        sentences = self._split_sentences(text)
        
        # 计算相关性得分
        relevant_sentences = []
        for sent in sentences:
            sent_words = set(re.findall(r'[\u4e00-\u9fa5]+', sent))
            overlap = query_keywords & sent_words
            if overlap:
                relevant_sentences.append((sent, len(overlap)))
        
        # 排序并选择
        relevant_sentences.sort(key=lambda x: x[1], reverse=True)
        
        summary = ''.join(s[0] for s in relevant_sentences[:3])
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return {
            "success": True,
            "query": query,
            "summary": summary,
            "relevance_score": len(relevant_sentences)
        }
    
    def bullet_point_summary(self, text: str, num_points: int = 5) -> List[str]:
        """
        要点式摘要
        
        生成bullet point格式的摘要
        
        Args:
            text: 输入文本
            num_points: 要点数量
            
        Returns:
            要点列表
        """
        sentences = self._split_sentences(text)
        scores = self._score_sentences(sentences, text)
        
        # 选择重要句子
        sorted_sentences = sorted(
            zip(sentences, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 提取要点（简化版）
        bullet_points = []
        for sent, score in sorted_sentences[:num_points]:
            # 简化句子，移除从句
            point = sent.strip()
            if len(point) > 50:
                point = point[:50] + "..."
            bullet_points.append(point)
        
        return bullet_points


# 使用示例
if __name__ == "__main__":
    summarizer = IntelligentSummarizer()
    
    test_text = """
人工智能技术在过去十年取得了巨大进展。深度学习的突破使得计算机在图像识别、语音识别等任务上达到甚至超过人类水平。
大语言模型的出现更是开启了AI的新时代。GPT、BERT等模型展示了强大的语言理解和生成能力。
在企业应用方面，AI已经深入到客户服务、数据分析、流程优化等多个领域。许多企业通过部署AI系统，实现了效率提升和成本降低。
未来，AI将继续快速发展，与更多传统行业深度融合，为社会带来深刻变革。
    """
    
    print("✅ 智能摘要器已加载\n")
    
    # 抽取式摘要
    result1 = summarizer.summarize(test_text, method="extractive", num_sentences=2)
    print(f"📊 抽取式摘要 ({result1['compression_ratio']}压缩):")
    print(f"  {result1['summary']}\n")
    
    # 要点式摘要
    bullets = summarizer.bullet_point_summary(test_text, num_points=3)
    print(f"📋 要点式摘要:")
    for i, point in enumerate(bullets, 1):
        print(f"  {i}. {point}")
    
    print("\n💡 实际部署建议:")
    print("  • 使用transformers加载BART或T5模型")
    print("  • 或调用GPT-4 API生成高质量摘要")
    print("  • 或使用中文模型（如ChatGLM）")


