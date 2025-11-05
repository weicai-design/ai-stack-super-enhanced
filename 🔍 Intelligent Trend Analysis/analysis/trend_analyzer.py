"""
Trend Analyzer
趋势分析器

根据需求6.3: 信息分类、比较、汇总、总结
根据需求6.4: 输出报告
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter
import re


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self):
        """初始化趋势分析器"""
        self.analyzed_data = []
    
    def classify_content(
        self, 
        data: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        分类信息
        
        根据需求6.3: 信息分类
        
        Args:
            data: 爬取的数据
            
        Returns:
            分类后的数据
        """
        classified = {}
        
        for item in data:
            category = item.get("category", "其他")
            if category not in classified:
                classified[category] = []
            classified[category].append(item)
        
        return classified
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            top_k: 返回数量
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（实际可使用jieba等库）
        # 去除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 分词（简化版）
        words = text.split()
        
        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '了', '和', '与', '等', '及', '为'}
        words = [w for w in words if len(w) > 1 and w not in stop_words]
        
        # 统计词频
        word_counts = Counter(words)
        
        # 返回TOP K
        return [word for word, count in word_counts.most_common(top_k)]
    
    def summarize_content(
        self, 
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        汇总分析内容
        
        根据需求6.3: 汇总、总结
        
        Args:
            data: 数据列表
            
        Returns:
            汇总结果
        """
        if not data:
            return {"total": 0}
        
        # 按类别统计
        categories = Counter(item.get("category") for item in data)
        
        # 按来源统计
        sources = Counter(item.get("source") for item in data)
        
        # 提取所有内容的关键词
        all_content = " ".join(item.get("content", "") for item in data)
        keywords = self.extract_keywords(all_content, 20)
        
        # 时间分布
        dates = [item.get("publish_date", "")[:10] for item in data if item.get("publish_date")]
        date_distribution = Counter(dates)
        
        return {
            "total": len(data),
            "categories": dict(categories),
            "sources": dict(sources),
            "keywords": keywords,
            "date_distribution": dict(date_distribution),
            "latest_items": data[-10:] if len(data) > 10 else data,
        }
    
    def compare_trends(
        self,
        current_data: List[Dict[str, Any]],
        previous_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        趋势对比分析
        
        根据需求6.3: 比较
        
        Args:
            current_data: 当前数据
            previous_data: 历史数据
            
        Returns:
            对比结果
        """
        current_summary = self.summarize_content(current_data)
        previous_summary = self.summarize_content(previous_data)
        
        # 数量变化
        volume_change = current_summary["total"] - previous_summary["total"]
        volume_change_percent = (
            volume_change / previous_summary["total"] * 100 
            if previous_summary["total"] > 0 else 0
        )
        
        # 关键词变化
        current_keywords = set(current_summary.get("keywords", []))
        previous_keywords = set(previous_summary.get("keywords", []))
        
        new_keywords = current_keywords - previous_keywords
        disappeared_keywords = previous_keywords - current_keywords
        
        return {
            "volume_change": volume_change,
            "volume_change_percent": round(volume_change_percent, 2),
            "new_keywords": list(new_keywords),
            "disappeared_keywords": list(disappeared_keywords),
            "trending_up": list(new_keywords)[:5],  # 热度上升
            "current_summary": current_summary,
            "previous_summary": previous_summary,
        }
    
    def detect_hot_topics(
        self,
        data: List[Dict[str, Any]],
        threshold: int = 3
    ) -> List[Dict[str, Any]]:
        """
        检测热点话题
        
        Args:
            data: 数据列表
            threshold: 热度阈值
            
        Returns:
            热点话题列表
        """
        # 提取所有标题的关键词
        all_keywords = []
        for item in data:
            title = item.get("title", "")
            keywords = self.extract_keywords(title, 5)
            all_keywords.extend(keywords)
        
        # 统计词频
        keyword_counts = Counter(all_keywords)
        
        # 筛选热点
        hot_topics = []
        for keyword, count in keyword_counts.most_common(20):
            if count >= threshold:
                # 找到包含该关键词的文章
                related_articles = [
                    item for item in data
                    if keyword in item.get("title", "") or keyword in item.get("content", "")
                ]
                
                hot_topics.append({
                    "keyword": keyword,
                    "frequency": count,
                    "hotness": min(count * 10, 100),
                    "related_count": len(related_articles),
                    "sample_articles": related_articles[:3],
                })
        
        return hot_topics


class ReportGenerator:
    """
    报告生成器
    
    根据需求6.4: 输出报告
    """
    
    def __init__(self, llm_url: str = "http://localhost:11434"):
        """
        初始化报告生成器
        
        Args:
            llm_url: LLM服务地址
        """
        self.llm_url = llm_url
        self.analyzer = TrendAnalyzer()
    
    def generate_industry_report(
        self,
        industry: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成行业报告
        
        根据需求6.4: 产业报告、行业报告
        
        Args:
            industry: 行业名称
            data: 行业相关数据
            
        Returns:
            行业报告
        """
        # 汇总分析
        summary = self.analyzer.summarize_content(data)
        
        # 检测热点
        hot_topics = self.analyzer.detect_hot_topics(data)
        
        # 生成报告
        report = {
            "report_type": "industry_report",
            "industry": industry,
            "generated_at": datetime.now().isoformat(),
            "executive_summary": f"{industry}行业趋势分析报告",
            "data_summary": summary,
            "hot_topics": hot_topics[:10],
            "key_insights": self._generate_insights(summary, hot_topics),
            "recommendations": self._generate_recommendations(summary),
            "total_articles": len(data),
        }
        
        return report
    
    def generate_investment_report(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成投资报告
        
        根据需求6.4: 投资报告
        
        Args:
            data: 投资相关数据
            
        Returns:
            投资报告
        """
        summary = self.analyzer.summarize_content(data)
        hot_topics = self.analyzer.detect_hot_topics(data)
        
        report = {
            "report_type": "investment_report",
            "generated_at": datetime.now().isoformat(),
            "executive_summary": "投资趋势分析报告",
            "market_overview": summary,
            "hot_sectors": hot_topics[:5],
            "investment_opportunities": self._identify_opportunities(data),
            "risk_factors": self._identify_risks(data),
            "recommendations": self._generate_investment_recommendations(data),
        }
        
        return report
    
    def _generate_insights(
        self,
        summary: Dict[str, Any],
        hot_topics: List[Dict[str, Any]]
    ) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 基于数据生成洞察
        if summary.get("total", 0) > 100:
            insights.append("信息量充足，趋势明显")
        
        if hot_topics:
            top_topic = hot_topics[0]
            insights.append(f"热点话题：{top_topic['keyword']}（热度{top_topic['hotness']}）")
        
        # TODO: 使用LLM生成更深入的洞察
        
        return insights
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = [
            "持续关注行业动态",
            "重点关注热点话题",
            "建议进行深度研究",
        ]
        
        # TODO: 基于数据生成个性化建议
        
        return recommendations
    
    def _identify_opportunities(self, data: List[Dict[str, Any]]) -> List[str]:
        """识别投资机会"""
        return [
            "新兴科技领域",
            "政策支持行业",
            "市场需求增长领域",
        ]
    
    def _identify_risks(self, data: List[Dict[str, Any]]) -> List[str]:
        """识别风险因素"""
        return [
            "市场波动风险",
            "政策变化风险",
            "行业竞争加剧",
        ]
    
    def _generate_investment_recommendations(self, data: List[Dict[str, Any]]) -> List[str]:
        """生成投资建议"""
        return [
            "建议关注科技创新领域",
            "适度分散投资",
            "长期价值投资",
        ]

