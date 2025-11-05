"""
API集成示例
演示如何集成各种第三方API

注意：这些是示例代码，实际使用需要申请相应的API密钥
"""

import requests
from typing import Optional
import json


# ==================== 股票API集成示例 ====================

class StockAPIIntegration:
    """股票API集成示例（使用Alpha Vantage）"""
    
    def __init__(self, api_key: str = "YOUR_API_KEY"):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_price(self, symbol: str) -> dict:
        """
        获取实时股票价格
        
        使用方法:
        stock_api = StockAPIIntegration(api_key="your_key")
        price = stock_api.get_stock_price("AAPL")
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                return {
                    "symbol": symbol,
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0"),
                    "volume": int(quote.get("06. volume", 0)),
                    "timestamp": quote.get("07. latest trading day", "")
                }
            else:
                return {"error": "API调用失败或超过限额"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_intraday_data(self, symbol: str, interval: str = "5min") -> dict:
        """获取日内数据"""
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ==================== 社交媒体API集成示例 ====================

class SocialMediaAPIIntegration:
    """社交媒体API集成示例"""
    
    @staticmethod
    def xiaohongshu_api_example():
        """
        小红书API集成示例（概念性）
        
        注意：小红书没有官方API，这里仅展示集成思路
        实际使用可能需要：
        1. 使用第三方服务
        2. 爬虫技术（需遵守robots.txt）
        3. 官方合作
        """
        # 示例数据结构
        post_data = {
            "title": "我的产品分享",
            "content": "这是一款很棒的产品...",
            "images": ["image1.jpg", "image2.jpg"],
            "tags": ["好物分享", "生活日常"],
            "location": "上海"
        }
        
        # 实际实现需要：
        # 1. 获取access_token
        # 2. 调用发布接口
        # 3. 处理回调和状态
        
        return {
            "message": "这是概念性示例，实际需要申请API权限",
            "data_structure": post_data
        }
    
    @staticmethod
    def douyin_api_example():
        """
        抖音API集成示例
        
        抖音开放平台: https://open.douyin.com/
        需要：
        1. 注册开发者账号
        2. 创建应用
        3. 获取access_token
        """
        # 示例配置
        config = {
            "client_key": "YOUR_CLIENT_KEY",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "YOUR_REDIRECT_URI"
        }
        
        # 发布视频示例数据
        video_data = {
            "video_url": "https://...",
            "title": "我的视频标题",
            "description": "视频描述",
            "tags": ["科技", "AI"],
            "cover_url": "https://..."
        }
        
        return {
            "message": "需要在抖音开放平台申请API权限",
            "config": config,
            "data_structure": video_data
        }


# ==================== 新闻API集成示例 ====================

class NewsAPIIntegration:
    """新闻API集成示例（使用NewsAPI.org）"""
    
    def __init__(self, api_key: str = "YOUR_API_KEY"):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
    
    def get_top_headlines(self, country: str = "cn", category: Optional[str] = None) -> dict:
        """
        获取头条新闻
        
        使用方法:
        news_api = NewsAPIIntegration(api_key="your_key")
        headlines = news_api.get_top_headlines(country="cn", category="technology")
        """
        params = {
            "country": country,
            "apiKey": self.api_key
        }
        
        if category:
            params["category"] = category
        
        try:
            response = requests.get(f"{self.base_url}/top-headlines", params=params)
            data = response.json()
            
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                return {
                    "total": len(articles),
                    "articles": [
                        {
                            "title": article.get("title"),
                            "description": article.get("description"),
                            "url": article.get("url"),
                            "source": article.get("source", {}).get("name"),
                            "publishedAt": article.get("publishedAt")
                        }
                        for article in articles
                    ]
                }
            else:
                return {"error": data.get("message", "API调用失败")}
                
        except Exception as e:
            return {"error": str(e)}
    
    def search_news(self, query: str, language: str = "zh") -> dict:
        """搜索新闻"""
        params = {
            "q": query,
            "language": language,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(f"{self.base_url}/everything", params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ==================== AI模型API集成示例 ====================

class AIModelAPIIntegration:
    """AI模型API集成示例"""
    
    @staticmethod
    def openai_example(api_key: str = "YOUR_API_KEY"):
        """
        OpenAI API集成示例
        
        使用方法:
        response = AIModelAPIIntegration.openai_example(api_key="sk-...")
        """
        import openai
        
        openai.api_key = api_key
        
        try:
            # GPT-4 调用示例
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个有帮助的财务分析助手"},
                    {"role": "user", "content": "分析一下这个月的财务数据"}
                ]
            )
            
            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def ollama_local_example():
        """
        Ollama本地模型调用示例
        
        使用方法:
        response = AIModelAPIIntegration.ollama_local_example()
        """
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": "请分析ERP系统的业务流程",
                    "stream": False
                }
            )
            
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ==================== 使用示例 ====================

def main():
    """主函数 - 演示如何使用这些集成"""
    
    print("=== API集成示例 ===\n")
    
    # 1. 股票API示例
    print("1. 股票API集成:")
    print("   stock_api = StockAPIIntegration(api_key='your_key')")
    print("   price = stock_api.get_stock_price('AAPL')")
    print("   说明: 需要在 https://www.alphavantage.co/ 申请免费API密钥\n")
    
    # 2. 新闻API示例
    print("2. 新闻API集成:")
    print("   news_api = NewsAPIIntegration(api_key='your_key')")
    print("   headlines = news_api.get_top_headlines(country='cn')")
    print("   说明: 需要在 https://newsapi.org/ 申请免费API密钥\n")
    
    # 3. 社交媒体示例
    print("3. 社交媒体集成:")
    print("   - 小红书: 需要官方合作或第三方服务")
    print("   - 抖音: 在 https://open.douyin.com/ 申请开发者权限\n")
    
    # 4. AI模型示例
    print("4. AI模型集成:")
    print("   - OpenAI: 需要在 https://platform.openai.com/ 申请API密钥")
    print("   - Ollama: 本地运行，无需API密钥")
    print("   response = AIModelAPIIntegration.ollama_local_example()\n")
    
    print("=== 注意事项 ===")
    print("1. 所有API都需要遵守相应的服务条款")
    print("2. 注意API调用频率限制")
    print("3. 妥善保管API密钥，不要提交到代码库")
    print("4. 建议使用环境变量存储敏感信息")
    print("5. 生产环境使用时要做好错误处理和重试机制")


if __name__ == "__main__":
    main()


# ==================== 配置示例 ====================

"""
环境变量配置示例（.env文件）:

# 股票API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# 新闻API
NEWS_API_KEY=your_news_api_key

# OpenAI
OPENAI_API_KEY=sk-your_openai_key

# 抖音
DOUYIN_CLIENT_KEY=your_douyin_key
DOUYIN_CLIENT_SECRET=your_douyin_secret

使用方法:
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
"""

