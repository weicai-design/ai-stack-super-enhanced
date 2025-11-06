"""
反爬虫机制
- User-Agent轮换
- IP代理池
- 请求频率控制
- Cookie管理
"""
import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio


class AntiCrawlerSystem:
    """反爬虫系统"""
    
    def __init__(self):
        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # IP代理池（示例）
        self.proxy_pool = []
        
        # 请求记录（用于频率控制）
        self.request_history = {}
        
        # 配置
        self.config = {
            "min_delay": 2,      # 最小延迟（秒）
            "max_delay": 5,      # 最大延迟（秒）
            "max_requests_per_minute": 10,  # 每分钟最大请求数
            "retry_times": 3,    # 重试次数
            "retry_delay": 5     # 重试延迟（秒）
        }
    
    # ============ User-Agent管理 ============
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def add_user_agent(self, ua: str):
        """添加User-Agent到池中"""
        if ua not in self.user_agents:
            self.user_agents.append(ua)
    
    # ============ 代理管理 ============
    
    def add_proxy(self, proxy: str):
        """添加代理"""
        if proxy not in self.proxy_pool:
            self.proxy_pool.append(proxy)
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if self.proxy_pool:
            return random.choice(self.proxy_pool)
        return None
    
    # ============ 频率控制 ============
    
    def can_request(self, domain: str) -> bool:
        """检查是否可以请求"""
        now = datetime.now()
        
        # 获取该域名的请求历史
        if domain not in self.request_history:
            self.request_history[domain] = []
        
        # 清理1分钟前的记录
        one_minute_ago = now - timedelta(minutes=1)
        self.request_history[domain] = [
            t for t in self.request_history[domain]
            if t > one_minute_ago
        ]
        
        # 检查是否超过限制
        if len(self.request_history[domain]) >= self.config['max_requests_per_minute']:
            return False
        
        return True
    
    def record_request(self, domain: str):
        """记录请求"""
        if domain not in self.request_history:
            self.request_history[domain] = []
        
        self.request_history[domain].append(datetime.now())
    
    def get_delay(self) -> float:
        """获取随机延迟时间"""
        return random.uniform(
            self.config['min_delay'],
            self.config['max_delay']
        )
    
    # ============ 请求头生成 ============
    
    def get_request_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """生成请求头"""
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if referer:
            headers['Referer'] = referer
        
        return headers
    
    # ============ 智能重试 ============
    
    async def smart_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """
        智能请求（自动重试、延迟、换代理）
        
        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 其他参数
        
        Returns:
            请求结果
        """
        import httpx
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        for attempt in range(self.config['retry_times']):
            try:
                # 频率控制
                if not self.can_request(domain):
                    wait_time = 60 - (datetime.now().second)
                    await asyncio.sleep(wait_time)
                
                # 延迟
                if attempt > 0:
                    await asyncio.sleep(self.config['retry_delay'])
                else:
                    await asyncio.sleep(self.get_delay())
                
                # 准备请求
                headers = self.get_request_headers(kwargs.get('referer'))
                proxy = self.get_random_proxy()
                
                # 发送请求
                async with httpx.AsyncClient(
                    headers=headers,
                    proxies=proxy,
                    timeout=30.0
                ) as client:
                    if method == "GET":
                        response = await client.get(url, **kwargs)
                    elif method == "POST":
                        response = await client.post(url, **kwargs)
                    else:
                        raise ValueError(f"不支持的方法: {method}")
                    
                    # 记录请求
                    self.record_request(domain)
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "content": response.text,
                        "headers": dict(response.headers)
                    }
            
            except Exception as e:
                if attempt == self.config['retry_times'] - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": attempt + 1
                    }
                
                # 继续重试
                continue
        
        return {
            "success": False,
            "error": "所有重试均失败"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = sum(len(v) for v in self.request_history.values())
        
        return {
            "total_requests": total_requests,
            "domains_count": len(self.request_history),
            "user_agents_count": len(self.user_agents),
            "proxies_count": len(self.proxy_pool),
            "domain_stats": {
                domain: len(requests)
                for domain, requests in self.request_history.items()
            }
        }


# 全局实例
anti_crawler = AntiCrawlerSystem()








