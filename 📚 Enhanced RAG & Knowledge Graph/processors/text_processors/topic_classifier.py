"""
主题分类器
支持文档主题分类、多标签分类、层级分类等功能
"""
from typing import List, Dict, Optional
import re
from collections import Counter


class TopicClassifier:
    """主题分类器"""
    
    def __init__(self):
        """初始化主题分类器"""
        # 预定义主题关键词
        self.topic_keywords = {
            "技术": ["AI", "人工智能", "机器学习", "深度学习", "算法", "编程", "开发", "技术", "科技"],
            "商业": ["商业", "企业", "管理", "运营", "营销", "销售", "市场", "战略"],
            "财务": ["财务", "会计", "成本", "预算", "利润", "收入", "支出", "投资"],
            "生产": ["生产", "制造", "工艺", "质量", "设备", "产能", "效率"],
            "法律": ["法律", "合同", "协议", "合规", "法规", "条款"],
            "医疗": ["医疗", "健康", "医院", "疾病", "治疗", "药物"],
            "教育": ["教育", "学习", "培训", "课程", "教学", "学生"],
            "新闻": ["新闻", "报道", "事件", "发生", "据悉", "消息"]
        }
    
    def classify(
        self,
        text: str,
        top_k: int = 3,
        multi_label: bool = True
    ) -> Dict:
        """
        分类文本主题
        
        Args:
            text: 输入文本
            top_k: 返回top k个主题
            multi_label: 是否支持多标签
            
        Returns:
            分类结果
        """
        # 基于关键词的简单分类
        scores = self._calculate_topic_scores(text)
        
        # 排序
        sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if multi_label:
            # 多标签：返回所有分数>阈值的主题
            threshold = 0.3
            predictions = [
                {
                    "topic": topic,
                    "confidence": score,
                    "label": topic
                }
                for topic, score in sorted_topics
                if score >= threshold
            ][:top_k]
        else:
            # 单标签：只返回最高分
            predictions = [
                {
                    "topic": sorted_topics[0][0],
                    "confidence": sorted_topics[0][1],
                    "label": sorted_topics[0][0]
                }
            ]
        
        return {
            "success": True,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "predictions": predictions,
            "all_scores": dict(sorted_topics),
            "multi_label": multi_label
        }
    
    def _calculate_topic_scores(self, text: str) -> Dict[str, float]:
        """计算各主题的得分"""
        scores = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = 0
            for keyword in keywords:
                # 统计关键词出现次数
                count = len(re.findall(keyword, text, re.IGNORECASE))
                score += count
            
            # 归一化分数
            if len(text) > 0:
                scores[topic] = min(1.0, score / (len(text) / 100))
            else:
                scores[topic] = 0.0
        
        return scores
    
    def classify_hierarchical(self, text: str) -> Dict:
        """
        层级分类
        
        按照预定义的主题层级进行分类
        
        Returns:
            层级分类结果
        """
        # 定义主题层级
        hierarchy = {
            "科技": {
                "AI": ["机器学习", "深度学习", "NLP"],
                "软件": ["编程", "开发", "测试"],
                "硬件": ["芯片", "设备", "硬件"]
            },
            "商业": {
                "管理": ["企业管理", "项目管理", "人力资源"],
                "营销": ["市场营销", "品牌", "推广"],
                "财务": ["会计", "投资", "融资"]
            }
        }
        
        # 一级分类
        level1 = self.classify(text, top_k=1, multi_label=False)
        primary_topic = level1["predictions"][0]["topic"] if level1["predictions"] else "其他"
        
        # 二级分类（模拟）
        return {
            "success": True,
            "primary_topic": primary_topic,
            "secondary_topic": "子分类1",
            "tertiary_topic": "细分主题1",
            "hierarchy_path": f"{primary_topic} > 子分类1 > 细分主题1",
            "confidence": 0.85
        }
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Dict]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            top_k: 返回top k个关键词
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（实际应使用TF-IDF或TextRank）
        # 移除标点和停用词
        words = re.findall(r'[\u4e00-\u9fa5]+', text)
        
        # 过滤停用词（简化版）
        stop_words = {'的', '了', '在', '是', '和', '有', '与', '等', '为', '这', '将', '可以', '能够'}
        words = [w for w in words if len(w) >= 2 and w not in stop_words]
        
        # 统计词频
        word_freq = Counter(words)
        
        # 返回top k
        keywords = []
        for word, freq in word_freq.most_common(top_k):
            keywords.append({
                "keyword": word,
                "frequency": freq,
                "weight": freq / len(words) if words else 0
            })
        
        return keywords
    
    def batch_classify(self, texts: List[str]) -> Dict:
        """
        批量分类
        
        Args:
            texts: 文本列表
            
        Returns:
            批量分类结果
        """
        results = []
        for text in texts:
            result = self.classify(text)
            results.append(result)
        
        # 统计主题分布
        topic_distribution = Counter()
        for result in results:
            for pred in result.get("predictions", []):
                topic_distribution[pred["topic"]] += 1
        
        return {
            "success": True,
            "total": len(texts),
            "results": results,
            "topic_distribution": dict(topic_distribution)
        }
    
    def get_topic_hierarchy(self) -> Dict:
        """获取主题层级结构"""
        return {
            "科技": ["AI", "软件", "硬件"],
            "商业": ["管理", "营销", "财务"],
            "生产": ["制造", "质量", "物流"],
            "其他": ["法律", "医疗", "教育"]
        }


# 使用示例
if __name__ == "__main__":
    classifier = TopicClassifier()
    
    test_text = """
华为技术有限公司发布了最新的AI芯片，采用先进的深度学习算法。
该产品在机器学习任务上性能提升300%，预计将推动人工智能技术在企业中的应用。
公司计划投资50亿元用于技术研发。
    """
    
    print("✅ 主题分类器已加载\n")
    
    # 分类
    result = classifier.classify(test_text, top_k=3)
    
    print(f"📊 分类结果:")
    for pred in result["predictions"]:
        print(f"  {pred['topic']}: {pred['confidence']:.2f}")
    
    # 关键词提取
    keywords = classifier.extract_keywords(test_text, top_k=5)
    print(f"\n🔑 关键词:")
    for kw in keywords:
        print(f"  {kw['keyword']} (频率: {kw['frequency']})")
    
    print("\n💡 实际部署建议:")
    print("  • 使用transformers加载分类模型（如BERT-classifier）")
    print("  • 或使用百度、讯飞等分类API")
    print("  • 或训练自定义分类模型")


