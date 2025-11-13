"""
新闻数据API适配器
对接新闻API获取真实新闻数据
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class NewsAdapter:
    """
    新闻数据API适配器
    
    功能:
    1. 获取最新新闻
    2. 搜索新闻
    3. 按类别获取新闻
    4. 趋势分析
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化新闻适配器"""
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "")
        self.base_url = "https://newsapi.org/v2"  # NewsAPI示例
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "X-Api-Key": self.api_key
            })
        
        logger.info("✅ 新闻API适配器初始化完成")
    
    def get_top_headlines(
        self,
        category: str = "technology",
        country: str = "cn",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取头条新闻
        
        Args:
            category: 新闻类别
            country: 国家代码
            limit: 数量限制
            
        Returns:
            新闻列表
        """
        if not self.api_key:
            logger.warning("未配置新闻API密钥，使用模拟数据")
            return self._mock_news(category, limit)
        
        try:
            response = self.session.get(
                f"{self.base_url}/top-headlines",
                params={
                    "category": category,
                    "country": country,
                    "pageSize": limit
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [{
                "title": article["title"],
                "description": article.get("description", ""),
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"],
                "category": category,
                "data_source": "NewsAPI"
            } for article in data.get("articles", [])]
        
        except Exception as e:
            logger.error(f"获取头条新闻失败: {e}")
            return self._mock_news(category, limit)
    
    def search_news(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索新闻
        
        Args:
            query: 搜索关键词
            from_date: 开始日期
            to_date: 结束日期
            limit: 数量限制
            
        Returns:
            新闻列表
        """
        if not self.api_key:
            return self._mock_search_news(query, limit)
        
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(
                f"{self.base_url}/everything",
                params={
                    "q": query,
                    "from": from_date,
                    "to": to_date,
                    "pageSize": limit,
                    "sortBy": "publishedAt"
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [{
                "title": article["title"],
                "description": article.get("description", ""),
                "url": article["url"],
                "source": article["source"]["name"],
                "published_at": article["publishedAt"],
                "query": query,
                "data_source": "NewsAPI"
            } for article in data.get("articles", [])]
        
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            return self._mock_search_news(query, limit)
    
    def _mock_news(self, category: str, limit: int) -> List[Dict[str, Any]]:
        """模拟新闻数据"""
        import random
        
        news = []
        for i in range(limit):
            news.append({
                "title": f"[模拟] {category}类新闻标题{i+1}",
                "description": f"这是一条关于{category}的模拟新闻描述",
                "url": f"https://example.com/news/{i+1}",
                "source": "模拟数据源",
                "published_at": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                "category": category,
                "data_source": "模拟数据"
            })
        
        return news
    
    def _mock_search_news(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """模拟搜索结果"""
        return self._mock_news(query, limit)


# 创建全局实例
news_adapter = NewsAdapter()

















