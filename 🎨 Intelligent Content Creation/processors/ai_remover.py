"""
AI痕迹去除器
实现内容去AI化、差异化处理，使AI生成的内容更像人类创作
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import re


class AIContentRemover:
    """AI痕迹去除器"""
    
    def __init__(self):
        """初始化去AI化处理器"""
        self.removal_strategies = []
        self.processed_contents = []
    
    def remove_ai_traces(
        self,
        content: str,
        content_type: str = "article"
    ) -> Dict[str, Any]:
        """
        去除AI痕迹
        
        Args:
            content: 原始内容
            content_type: 内容类型 (article/post/comment)
        
        Returns:
            处理后的内容
        """
        processed = content
        applied_strategies = []
        
        # 策略1: 去除AI常用的正式化表达
        processed, changed = self._remove_formal_expressions(processed)
        if changed:
            applied_strategies.append("去除正式化表达")
        
        # 策略2: 添加口语化表达
        processed = self._add_colloquial_expressions(processed)
        applied_strategies.append("添加口语化")
        
        # 策略3: 调整句式结构
        processed = self._adjust_sentence_structure(processed)
        applied_strategies.append("调整句式")
        
        # 策略4: 添加个性化元素
        processed = self._add_personality(processed, content_type)
        applied_strategies.append("添加个性化")
        
        # 策略5: 去除过于完美的格式
        processed = self._add_natural_imperfections(processed)
        applied_strategies.append("自然化处理")
        
        # 策略6: 替换AI常用词汇
        processed = self._replace_ai_common_words(processed)
        applied_strategies.append("替换AI词汇")
        
        # 计算相似度（简化版）
        similarity = self._calculate_similarity(content, processed)
        
        # 记录处理
        self.processed_contents.append({
            "original_length": len(content),
            "processed_length": len(processed),
            "similarity": similarity,
            "strategies_applied": applied_strategies,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "original_content": content,
            "processed_content": processed,
            "similarity_to_original": similarity,
            "strategies_applied": applied_strategies,
            "ai_score_before": 85,  # 模拟AI检测分数
            "ai_score_after": 25    # 处理后的分数（越低越像人类）
        }
    
    def _remove_formal_expressions(self, text: str) -> tuple:
        """
        去除正式化表达
        
        Args:
            text: 文本
        
        Returns:
            (处理后文本, 是否有变化)
        """
        # AI常用的正式表达
        formal_patterns = [
            (r'综上所述', '总的来说'),
            (r'值得注意的是', '要注意'),
            (r'具体而言', '具体来说'),
            (r'此外', '另外'),
            (r'因此', '所以'),
            (r'然而', '但是'),
            (r'首先.*?其次.*?最后', lambda m: self._simplify_enumeration(m.group(0)))
        ]
        
        changed = False
        for pattern, replacement in formal_patterns:
            if isinstance(replacement, str):
                new_text = re.sub(pattern, replacement, text)
            else:
                new_text = re.sub(pattern, replacement, text)
            
            if new_text != text:
                changed = True
                text = new_text
        
        return text, changed
    
    def _add_colloquial_expressions(self, text: str) -> str:
        """
        添加口语化表达
        
        Args:
            text: 文本
        
        Returns:
            处理后文本
        """
        # 随机添加口语化元素
        colloquial_insertions = [
            "说实话，", "其实吧，", "我觉得，", "个人感觉，",
            "emmm，", "哈哈，", "啊，"
        ]
        
        sentences = text.split('。')
        for i in range(len(sentences)):
            # 随机在20%的句子前添加口语化表达
            if random.random() < 0.2 and len(sentences[i]) > 10:
                insertion = random.choice(colloquial_insertions)
                sentences[i] = insertion + sentences[i]
        
        return '。'.join(sentences)
    
    def _adjust_sentence_structure(self, text: str) -> str:
        """
        调整句式结构，打破AI的规律性
        
        Args:
            text: 文本
        
        Returns:
            处理后文本
        """
        # 随机合并或拆分句子
        sentences = [s for s in text.split('。') if s.strip()]
        
        new_sentences = []
        i = 0
        while i < len(sentences):
            if random.random() < 0.3 and i + 1 < len(sentences):
                # 30%概率合并两个短句
                if len(sentences[i]) < 30 and len(sentences[i+1]) < 30:
                    merged = sentences[i] + '，' + sentences[i+1]
                    new_sentences.append(merged)
                    i += 2
                    continue
            
            new_sentences.append(sentences[i])
            i += 1
        
        return '。'.join(new_sentences) + '。'
    
    def _add_personality(self, text: str, content_type: str) -> str:
        """
        添加个性化元素
        
        Args:
            text: 文本
            content_type: 内容类型
        
        Returns:
            处理后文本
        """
        # 根据内容类型添加个性化元素
        if content_type == "post":
            # 社交媒体风格：添加表情、语气词
            emotions = ["😊", "👍", "💪", "🎉", "✨"]
            if random.random() < 0.5:
                text += " " + random.choice(emotions)
        
        return text
    
    def _add_natural_imperfections(self, text: str) -> str:
        """
        添加自然瑕疵，使内容更真实
        
        Args:
            text: 文本
        
        Returns:
            处理后文本
        """
        # 随机添加一些"不完美"的元素
        
        # 1. 偶尔使用省略号
        sentences = text.split('。')
        for i in range(len(sentences)):
            if random.random() < 0.15:  # 15%概率
                sentences[i] = sentences[i].rstrip('，、；') + '...'
        
        # 2. 偶尔使用感叹号
        for i in range(len(sentences)):
            if random.random() < 0.1:  # 10%概率
                sentences[i] = sentences[i] + '!'
        
        return '。'.join(sentences)
    
    def _replace_ai_common_words(self, text: str) -> str:
        """
        替换AI常用词汇
        
        Args:
            text: 文本
        
        Returns:
            处理后文本
        """
        # AI容易使用的词汇替换
        replacements = {
            "优化": ["改进", "提升", "完善"],
            "提升": ["提高", "增强", "加强"],
            "有效": ["管用", "好用", "实用"],
            "显著": ["明显", "很明显", "特别"],
            "进一步": ["更", "再", "继续"],
            "相关": ["有关", "关于"],
            "重要": ["要紧", "关键", "核心"]
        }
        
        for word, alternatives in replacements.items():
            if word in text:
                # 随机替换部分出现的词汇
                count = text.count(word)
                for _ in range(count):
                    if random.random() < 0.5:  # 50%概率替换
                        text = text.replace(word, random.choice(alternatives), 1)
        
        return text
    
    def _simplify_enumeration(self, text: str) -> str:
        """简化枚举表达"""
        # 将"首先...其次...最后"简化为更自然的表达
        return text.replace('首先', '').replace('其次', '还有').replace('最后', '最后就是')
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算相似度（简化版）
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度（0-100）
        """
        # 简化的相似度计算
        common_chars = sum(1 for c1, c2 in zip(text1, text2) if c1 == c2)
        max_len = max(len(text1), len(text2))
        
        return round((common_chars / max_len * 100), 2) if max_len > 0 else 100
    
    def create_differentiated_content(
        self,
        base_content: str,
        differentiation_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        创建差异化内容
        
        Args:
            base_content: 基础内容
            differentiation_level: 差异化程度 (low/medium/high)
        
        Returns:
            差异化内容
        """
        # 根据差异化程度应用不同策略
        strategies_count = {
            "low": 2,
            "medium": 4,
            "high": 6
        }
        
        count = strategies_count.get(differentiation_level, 4)
        
        # 应用多种策略
        processed = base_content
        
        strategies = [
            self._add_personal_views,
            self._add_examples,
            self._change_perspective,
            self._add_questions,
            self._simplify_language,
            self._add_emotions
        ]
        
        selected_strategies = random.sample(strategies, min(count, len(strategies)))
        
        for strategy in selected_strategies:
            processed = strategy(processed)
        
        return {
            "success": True,
            "original_content": base_content,
            "differentiated_content": processed,
            "differentiation_level": differentiation_level,
            "strategies_count": len(selected_strategies)
        }
    
    def _add_personal_views(self, text: str) -> str:
        """添加个人观点"""
        views = ["我觉得", "在我看来", "我的经验是", "个人认为"]
        insertion = random.choice(views)
        
        # 在第一段添加个人观点
        paragraphs = text.split('\n')
        if paragraphs:
            paragraphs[0] = insertion + paragraphs[0]
        
        return '\n'.join(paragraphs)
    
    def _add_examples(self, text: str) -> str:
        """添加实例"""
        example_intro = random.choice(["举个例子", "比如说", "就拿我来说"])
        return text + f"\n\n{example_intro}，[这里可以添加具体例子]。"
    
    def _change_perspective(self, text: str) -> str:
        """改变视角"""
        # 将部分"我们"改为"你"或"大家"
        text = text.replace("我们可以", random.choice(["你可以", "大家可以"]))
        return text
    
    def _add_questions(self, text: str) -> str:
        """添加疑问句"""
        questions = ["是不是？", "对吧？", "你觉得呢？", "怎么样？"]
        sentences = text.split('。')
        
        # 随机在某个句子后添加疑问
        if len(sentences) > 2:
            idx = random.randint(1, len(sentences) - 2)
            sentences[idx] += random.choice(questions)
        
        return '。'.join(sentences)
    
    def _simplify_language(self, text: str) -> str:
        """简化语言"""
        # 将复杂词汇替换为简单词汇
        simplifications = {
            "实施": "做",
            "进行": "做",
            "开展": "搞",
            "促进": "帮助",
            "提升": "变好"
        }
        
        for complex_word, simple_word in simplifications.items():
            if random.random() < 0.3:  # 30%概率替换
                text = text.replace(complex_word, simple_word, 1)
        
        return text
    
    def _add_emotions(self, text: str) -> str:
        """添加情感元素"""
        emotions = ["真的很", "特别", "超级", "真心", "确实"]
        
        # 随机在形容词前添加情感词
        adjectives = ["好", "棒", "赞", "牛", "厉害"]
        for adj in adjectives:
            if adj in text and random.random() < 0.5:
                emotion = random.choice(emotions)
                text = text.replace(adj, emotion + adj, 1)
        
        return text
    
    def batch_process(
        self,
        contents: List[str],
        differentiation_level: str = "medium"
    ) -> Dict[str, Any]:
        """
        批量处理内容
        
        Args:
            contents: 内容列表
            differentiation_level: 差异化程度
        
        Returns:
            批量处理结果
        """
        results = []
        
        for i, content in enumerate(contents):
            # 去AI化
            removed = self.remove_ai_traces(content)
            
            # 差异化
            differentiated = self.create_differentiated_content(
                removed["processed_content"],
                differentiation_level
            )
            
            results.append({
                "index": i,
                "original": content,
                "ai_removed": removed["processed_content"],
                "differentiated": differentiated["differentiated_content"],
                "ai_score_reduction": 60  # 模拟：AI分数降低60分
            })
        
        # 确保所有结果都不相同
        results = self._ensure_uniqueness(results)
        
        return {
            "success": True,
            "total_processed": len(results),
            "results": results,
            "average_ai_score_reduction": 60
        }
    
    def _ensure_uniqueness(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        确保每个结果都有差异
        
        Args:
            results: 结果列表
        
        Returns:
            差异化后的结果
        """
        # 为每个结果添加独特元素
        for i, result in enumerate(results):
            # 添加序号相关的个性化
            unique_elements = [
                f"\n\n第{i+1}个观察：",
                f"\n\n更新{i+1}：",
                f"\n\nTip {i+1}："
            ]
            
            if random.random() < 0.3:
                result["differentiated"] += random.choice(unique_elements) + "[个性化内容]"
        
        return results
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计
        
        Returns:
            统计数据
        """
        if not self.processed_contents:
            return {
                "total_processed": 0,
                "message": "暂无处理记录"
            }
        
        total = len(self.processed_contents)
        
        avg_similarity = statistics.mean([
            p["similarity"] for p in self.processed_contents
        ])
        
        avg_length_change = statistics.mean([
            ((p["processed_length"] - p["original_length"]) / p["original_length"] * 100)
            for p in self.processed_contents
            if p["original_length"] > 0
        ])
        
        return {
            "total_processed": total,
            "average_similarity": round(avg_similarity, 2),
            "average_length_change_percent": round(avg_length_change, 2),
            "estimated_ai_detection_reduction": "60-70%"
        }


# 创建默认实例
ai_content_remover = AIContentRemover()

