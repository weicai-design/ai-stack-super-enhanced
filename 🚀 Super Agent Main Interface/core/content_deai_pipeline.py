#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容去AI化管线
功能：将AI生成的内容转换为更自然、更人性化的表达
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import random
import logging

logger = logging.getLogger(__name__)


class DeAIPipeline:
    """
    去AI化管线
    通过多种技术手段降低内容的AI痕迹
    """
    
    def __init__(self):
        """初始化去AI化管线"""
        self.human_patterns = [
            # 口语化表达
            ("因此", "所以"),
            ("综上所述", "总的来说"),
            ("值得注意的是", "要提醒的是"),
            ("首先", "先来说说"),
            ("其次", "然后"),
            ("最后", "最后再提一下"),
            ("此外", "另外"),
            ("然而", "不过"),
            ("例如", "比如"),
            ("具体而言", "具体来说"),
        ]
        
        self.ai_markers = [
            "作为一个AI",
            "根据我的训练",
            "基于我的知识",
            "我无法",
            "我不能",
            "请注意",
            "重要提示",
            "需要说明的是",
            "应当指出",
        ]
        
        self.sentence_variations = {
            "开头": [
                "你知道吗",
                "其实",
                "说实话",
                "讲真",
                "最近发现",
                "今天想聊聊",
            ],
            "结尾": [
                "你觉得呢",
                "你怎么看",
                "欢迎留言",
                "期待你的想法",
                "一起讨论",
            ]
        }
    
    def process(
        self,
        content: str,
        style: str = "casual",
        intensity: float = 0.5
    ) -> Dict[str, Any]:
        """
        处理内容，去除AI痕迹
        
        Args:
            content: 原始内容
            style: 风格（casual/formal/creative）
            intensity: 处理强度（0.0-1.0）
            
        Returns:
            处理结果
        """
        original = content
        processed = content
        
        changes = []
        
        # 1. 移除AI标记
        processed, removed_markers = self._remove_ai_markers(processed)
        if removed_markers:
            changes.append(f"移除AI标记: {len(removed_markers)}处")
        
        # 2. 替换正式表达为口语化
        if intensity > 0.3:
            processed, replaced = self._humanize_expressions(processed, intensity)
            if replaced:
                changes.append(f"口语化替换: {len(replaced)}处")
        
        # 3. 添加自然停顿和语气词
        if intensity > 0.5:
            processed, pauses = self._add_natural_pauses(processed, style, intensity)
            if pauses:
                changes.append(f"添加自然停顿: {len(pauses)}处")
        
        # 4. 调整句式多样性
        if intensity > 0.4:
            processed, varied = self._vary_sentence_structure(processed, intensity)
            if varied:
                changes.append(f"句式多样化: {varied}处")
        
        # 5. 添加个人化表达
        if intensity > 0.6:
            processed, personalized = self._add_personal_touch(processed, style)
            if personalized:
                changes.append(f"个人化表达: {personalized}处")
        
        # 计算去AI化得分
        ai_score = self._calculate_ai_score(processed)
        human_score = 100 - ai_score
        
        return {
            "original": original,
            "processed": processed,
            "changes": changes,
            "ai_score": round(ai_score, 2),
            "human_score": round(human_score, 2),
            "improvement": round(human_score - (100 - self._calculate_ai_score(original)), 2),
            "style": style,
            "intensity": intensity,
            "processed_at": datetime.now().isoformat(),
        }
    
    def _remove_ai_markers(self, text: str) -> tuple[str, List[str]]:
        """移除AI标记"""
        removed = []
        for marker in self.ai_markers:
            if marker in text:
                text = text.replace(marker, "")
                removed.append(marker)
        return text, removed
    
    def _humanize_expressions(self, text: str, intensity: float) -> tuple[str, List[str]]:
        """口语化表达替换"""
        replaced = []
        for formal, casual in self.human_patterns:
            if random.random() < intensity and formal in text:
                text = text.replace(formal, casual, 1)  # 只替换第一次出现
                replaced.append(f"{formal} -> {casual}")
        return text, replaced
    
    def _add_natural_pauses(self, text: str, style: str, intensity: float) -> tuple[str, List[str]]:
        """添加自然停顿"""
        pauses = []
        if style == "casual":
            pause_words = ["嗯", "啊", "那个", "其实", "就是"]
        else:
            pause_words = ["其实", "实际上", "也就是说"]
        
        # 在长句中间随机添加停顿
        sentences = re.split(r'[。！？]', text)
        result_sentences = []
        for sent in sentences:
            if len(sent) > 30 and random.random() < intensity * 0.3:
                # 在句子中间插入停顿
                mid = len(sent) // 2
                pause = random.choice(pause_words)
                sent = sent[:mid] + f"，{pause}，" + sent[mid:]
                pauses.append(pause)
            result_sentences.append(sent)
        
        return "。".join(result_sentences), pauses
    
    def _vary_sentence_structure(self, text: str, intensity: float) -> tuple[str, int]:
        """调整句式多样性"""
        sentences = re.split(r'[。！？]', text)
        varied_count = 0
        
        # 将部分陈述句改为疑问句或感叹句
        for i, sent in enumerate(sentences):
            if len(sent) > 10 and random.random() < intensity * 0.2:
                # 将陈述句改为疑问句
                if sent.endswith("。") and "吗" not in sent and "？" not in sent:
                    sent = sent.rstrip("。") + "？"
                    varied_count += 1
                sentences[i] = sent
        
        return "。".join(sentences), varied_count
    
    def _add_personal_touch(self, text: str, style: str) -> tuple[str, int]:
        """添加个人化表达"""
        personalized_count = 0
        
        # 在开头添加个人化表达
        if style == "casual" and not any(text.startswith(p) for p in self.sentence_variations["开头"]):
            opener = random.choice(self.sentence_variations["开头"])
            text = f"{opener}，{text}"
            personalized_count += 1
        
        # 在结尾添加互动表达
        if style == "casual" and not any(text.endswith(p) for p in self.sentence_variations["结尾"]):
            closer = random.choice(self.sentence_variations["结尾"])
            text = f"{text}。{closer}。"
            personalized_count += 1
        
        return text, personalized_count
    
    def _calculate_ai_score(self, text: str) -> float:
        """计算AI痕迹得分（0-100，越高越像AI）"""
        score = 0.0
        
        # 检查AI标记
        for marker in self.ai_markers:
            if marker in text:
                score += 15.0
        
        # 检查正式表达
        formal_count = sum(1 for formal, _ in self.human_patterns if formal in text)
        score += formal_count * 3.0
        
        # 检查句式重复
        sentences = re.split(r'[。！？]', text)
        if len(sentences) > 3:
            # 检查开头重复
            first_words = [s[:2] for s in sentences[:5] if len(s) > 2]
            if len(set(first_words)) < len(first_words) * 0.6:
                score += 10.0
        
        # 检查标点使用（AI倾向于过度使用某些标点）
        if text.count("：") > len(sentences) * 0.3:
            score += 5.0
        
        return min(score, 100.0)
    
    def batch_process(
        self,
        contents: List[str],
        style: str = "casual",
        intensity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """批量处理"""
        results = []
        for content in contents:
            result = self.process(content, style, intensity)
            results.append(result)
        return results


# 全局实例
deai_pipeline = DeAIPipeline()

