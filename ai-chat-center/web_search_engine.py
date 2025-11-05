"""
需求5: 外部网站内容精准搜索引擎
支持多种搜索引擎和网站爬取
"""

import httpx
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from urllib.parse import quote, urljoin
import asyncio


class WebSearchEngine:
    """外部网站精准搜索引擎"""
    
    def __init__(self):
        self.search_engines = {
            "google": "https://www.google.com/search?q={}",
            "bing": "https://www.bing.com/search?q={}",
            "baidu": "https://www.baidu.com/s?wd={}",
        }
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    
    async def search_web(self, query: str, engine: str = "bing", max_results: int = 5) -> List[Dict[str, Any]]:
        """
        精准搜索外部网站
        """
        results = []
        
        try:
            if engine == "bing":
                results = await self.search_bing(query, max_results)
            elif engine == "google":
                results = await self.search_google(query, max_results)
            elif engine == "baidu":
                results = await self.search_baidu(query, max_results)
            else:
                # 默认使用bing
                results = await self.search_bing(query, max_results)
        
        except Exception as e:
            print(f"❌ 网页搜索失败: {e}")
        
        return results
    
    async def search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Bing搜索"""
        results = []
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                url = f"https://www.bing.com/search?q={quote(query)}"
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析Bing搜索结果
                    search_results = soup.find_all('li', class_='b_algo', limit=max_results)
                    
                    for item in search_results:
                        title_elem = item.find('h2')
                        link_elem = item.find('a')
                        snippet_elem = item.find('p') or item.find('div', class_='b_caption')
                        
                        if title_elem and link_elem:
                            results.append({
                                "title": title_elem.get_text(strip=True),
                                "url": link_elem.get('href', ''),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                "source": "Bing"
                            })
        
        except Exception as e:
            print(f"❌ Bing搜索失败: {e}")
        
        return results
    
    async def search_google(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Google搜索（简化版）"""
        results = []
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                url = f"https://www.google.com/search?q={quote(query)}"
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Google搜索结果解析
                    search_results = soup.find_all('div', class_='g', limit=max_results)
                    
                    for item in search_results:
                        title_elem = item.find('h3')
                        link_elem = item.find('a')
                        snippet_elem = item.find('div', class_='VwiC3b')
                        
                        if title_elem and link_elem:
                            results.append({
                                "title": title_elem.get_text(strip=True),
                                "url": link_elem.get('href', ''),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                "source": "Google"
                            })
        
        except Exception as e:
            print(f"❌ Google搜索失败: {e}")
        
        return results
    
    async def search_baidu(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """百度搜索"""
        results = []
        
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                url = f"https://www.baidu.com/s?wd={quote(query)}"
                response = await client.get(url, headers=self.headers, timeout=10.0)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 百度搜索结果解析
                    search_results = soup.find_all('div', class_='result', limit=max_results)
                    
                    for item in search_results:
                        title_elem = item.find('h3') or item.find('a')
                        link_elem = item.find('a')
                        snippet_elem = item.find('span', class_='content-right_8Zs40')
                        
                        if title_elem and link_elem:
                            results.append({
                                "title": title_elem.get_text(strip=True),
                                "url": link_elem.get('href', ''),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                                "source": "百度"
                            })
        
        except Exception as e:
            print(f"❌ 百度搜索失败: {e}")
        
        return results
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        精准抓取特定网站内容
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers, timeout=15.0)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 提取文本
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    return {
                        "url": url,
                        "title": soup.title.string if soup.title else "无标题",
                        "content": text[:5000],  # 前5000字符
                        "success": True
                    }
        
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def search_and_scrape(self, query: str, engine: str = "bing", scrape_top: int = 3) -> str:
        """
        搜索并抓取top结果的详细内容
        """
        # 1. 搜索
        search_results = await self.search_web(query, engine, max_results=5)
        
        if not search_results:
            return "未找到相关搜索结果"
        
        # 2. 抓取top结果的详细内容
        detailed_results = []
        
        for i, result in enumerate(search_results[:scrape_top], 1):
            url = result.get("url", "")
            if url and url.startswith("http"):
                scraped = await self.scrape_website(url)
                
                if scraped.get("success"):
                    detailed_results.append({
                        "index": i,
                        "title": result.get("title"),
                        "url": url,
                        "snippet": result.get("snippet"),
                        "content": scraped.get("content", "")[:1000]  # 每个页面1000字符
                    })
        
        # 3. 格式化返回
        formatted_result = f"🔍 外部网站搜索结果（找到 {len(search_results)} 条）\n\n"
        
        for result in search_results:
            formatted_result += f"📄 {result.get('title')}\n"
            formatted_result += f"🔗 {result.get('url')}\n"
            formatted_result += f"📝 {result.get('snippet')}\n\n"
        
        if detailed_results:
            formatted_result += f"\n📖 详细内容（抓取前 {len(detailed_results)} 个）\n\n"
            
            for detail in detailed_results:
                formatted_result += f"【{detail['index']}. {detail['title']}】\n"
                formatted_result += f"{detail['content'][:500]}...\n\n"
        
        return formatted_result


