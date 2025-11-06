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


    # ============ 封号检测和处理 ============
    
    def detect_blocking(
        self,
        response_content: str,
        status_code: int,
        response_time: float
    ) -> Dict[str, Any]:
        """
        检测是否被封禁
        
        Args:
            response_content: 响应内容
            status_code: 状态码
            response_time: 响应时间
        
        Returns:
            检测结果
        """
        blocking_detected = False
        blocking_type = None
        confidence = 0
        
        # 检测1: 状态码
        if status_code in [403, 429, 503]:
            blocking_detected = True
            blocking_type = "status_code_blocking"
            confidence = 90
        
        # 检测2: 响应内容特征
        blocking_keywords = [
            "验证码", "captcha", "人机验证", "Access Denied",
            "Too Many Requests", "blocked", "IP被禁止",
            "请稍后再试", "访问频繁"
        ]
        
        for keyword in blocking_keywords:
            if keyword in response_content:
                blocking_detected = True
                blocking_type = "content_blocking"
                confidence = 95
                break
        
        # 检测3: 响应时间异常
        if response_time > 10:  # 超过10秒
            blocking_detected = True
            blocking_type = "slow_response"
            confidence = 60
        
        # 检测4: 空响应或重定向
        if len(response_content) < 100:
            blocking_detected = True
            blocking_type = "empty_response"
            confidence = 70
        
        return {
            "blocking_detected": blocking_detected,
            "blocking_type": blocking_type,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    
    def handle_blocking(
        self,
        domain: str,
        blocking_type: str
    ) -> Dict[str, Any]:
        """
        处理封禁
        
        Args:
            domain: 域名
            blocking_type: 封禁类型
        
        Returns:
            处理策略
        """
        strategies = []
        
        if blocking_type in ["status_code_blocking", "content_blocking"]:
            # 严重封禁，需要切换IP和增加延迟
            strategies.append("switch_proxy")
            strategies.append("increase_delay")
            strategies.append("clear_cookies")
            
            # 暂停该域名的爬取
            self._pause_domain(domain, minutes=30)
        
        elif blocking_type == "slow_response":
            # 响应慢，可能是频率过高
            strategies.append("increase_delay")
            strategies.append("reduce_frequency")
        
        elif blocking_type == "empty_response":
            # 空响应，尝试换UA和代理
            strategies.append("switch_user_agent")
            strategies.append("switch_proxy")
        
        return {
            "domain": domain,
            "blocking_type": blocking_type,
            "strategies": strategies,
            "recommended_action": "暂停爬取30分钟后重试"
        }
    
    def _pause_domain(self, domain: str, minutes: int):
        """
        暂停域名爬取
        
        Args:
            domain: 域名
            minutes: 暂停分钟数
        """
        if not hasattr(self, 'paused_domains'):
            self.paused_domains = {}
        
        resume_time = datetime.now() + timedelta(minutes=minutes)
        self.paused_domains[domain] = resume_time.isoformat()
    
    def is_domain_paused(self, domain: str) -> bool:
        """
        检查域名是否被暂停
        
        Args:
            domain: 域名
        
        Returns:
            是否暂停
        """
        if not hasattr(self, 'paused_domains'):
            return False
        
        if domain not in self.paused_domains:
            return False
        
        resume_time = datetime.fromisoformat(self.paused_domains[domain])
        if datetime.now() >= resume_time:
            del self.paused_domains[domain]
            return False
        
        return True
    
    # ============ 高级反爬功能 ============
    
    def simulate_browser_behavior(self) -> Dict[str, Any]:
        """
        模拟浏览器行为
        
        Returns:
            模拟参数
        """
        # 模拟浏览器指纹
        fingerprint = {
            "screen": {
                "width": random.choice([1920, 2560, 1440]),
                "height": random.choice([1080, 1440, 900]),
                "colorDepth": 24
            },
            "timezone": random.choice([-480, -420, -360]),  # 中国时区
            "language": random.choice(["zh-CN", "zh-CN,zh;q=0.9"]),
            "platform": random.choice(["MacIntel", "Win32", "Linux x86_64"]),
            "cookieEnabled": True,
            "doNotTrack": random.choice(["1", None])
        }
        
        # 模拟鼠标移动和滚动
        behavior = {
            "mouse_movements": random.randint(5, 20),
            "scroll_depth": random.uniform(0.3, 0.95),
            "time_on_page": random.uniform(2, 10),
            "clicks": random.randint(0, 3)
        }
        
        return {
            "fingerprint": fingerprint,
            "behavior": behavior
        }
    
    def get_session_cookies(self, domain: str) -> Dict[str, str]:
        """
        获取会话Cookie
        
        Args:
            domain: 域名
        
        Returns:
            Cookie字典
        """
        if not hasattr(self, 'session_cookies'):
            self.session_cookies = {}
        
        if domain not in self.session_cookies:
            # 创建新会话Cookie
            self.session_cookies[domain] = {
                "session_id": f"sess_{random.randint(100000, 999999)}",
                "created_at": datetime.now().isoformat(),
                "request_count": 0
            }
        
        session = self.session_cookies[domain]
        session["request_count"] += 1
        
        # 如果会话请求过多，刷新会话
        if session["request_count"] > 50:
            self.session_cookies[domain] = {
                "session_id": f"sess_{random.randint(100000, 999999)}",
                "created_at": datetime.now().isoformat(),
                "request_count": 1
            }
        
        return {
            "session_id": self.session_cookies[domain]["session_id"]
        }
    
    def configure_advanced_settings(
        self,
        min_delay: int = 2,
        max_delay: int = 5,
        max_requests_per_minute: int = 10,
        retry_times: int = 3,
        auto_switch_proxy: bool = True,
        auto_pause_on_blocking: bool = True,
        pause_duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        配置高级设置
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            max_requests_per_minute: 每分钟最大请求数
            retry_times: 重试次数
            auto_switch_proxy: 自动切换代理
            auto_pause_on_blocking: 检测到封禁时自动暂停
            pause_duration_minutes: 暂停时长（分钟）
        
        Returns:
            配置结果
        """
        self.config.update({
            "min_delay": min_delay,
            "max_delay": max_delay,
            "max_requests_per_minute": max_requests_per_minute,
            "retry_times": retry_times,
            "auto_switch_proxy": auto_switch_proxy,
            "auto_pause_on_blocking": auto_pause_on_blocking,
            "pause_duration_minutes": pause_duration_minutes
        })
        
        return {
            "success": True,
            "message": "反爬虫配置已更新",
            "config": self.config
        }
    
    def get_crawl_health_report(self) -> Dict[str, Any]:
        """
        获取爬虫健康度报告
        
        Returns:
            健康度报告
        """
        # 统计请求
        total_requests = sum(len(v) for v in self.request_history.values())
        
        # 统计暂停的域名
        paused_domains = 0
        if hasattr(self, 'paused_domains'):
            paused_domains = len([
                d for d, resume_time in self.paused_domains.items()
                if datetime.fromisoformat(resume_time) > datetime.now()
            ])
        
        # 资源状态
        proxy_available = len(self.proxy_pool)
        ua_available = len(self.user_agents)
        
        # 健康评分
        health_score = 100
        
        # 如果有域名被暂停，扣分
        health_score -= paused_domains * 10
        
        # 如果代理池少，扣分
        if proxy_available < 5:
            health_score -= 20
        
        # 如果UA少，扣分
        if ua_available < 5:
            health_score -= 10
        
        health_score = max(0, health_score)
        
        # 健康等级
        if health_score >= 80:
            health_level = "健康"
        elif health_score >= 60:
            health_level = "一般"
        else:
            health_level = "需关注"
        
        return {
            "health_score": health_score,
            "health_level": health_level,
            "statistics": {
                "total_requests": total_requests,
                "active_domains": len(self.request_history),
                "paused_domains": paused_domains,
                "proxy_pool_size": proxy_available,
                "user_agent_pool_size": ua_available
            },
            "recommendations": self._get_health_recommendations(health_score, proxy_available, ua_available)
        }
    
    def _get_health_recommendations(
        self,
        health_score: int,
        proxy_count: int,
        ua_count: int
    ) -> List[str]:
        """
        获取健康建议
        
        Args:
            health_score: 健康分数
            proxy_count: 代理数量
            ua_count: UA数量
        
        Returns:
            建议列表
        """
        recommendations = []
        
        if health_score < 60:
            recommendations.append("整体健康度较低，建议暂停爬取并检查配置")
        
        if proxy_count < 5:
            recommendations.append(f"代理池过小（{proxy_count}个），建议增加到10个以上")
        
        if ua_count < 5:
            recommendations.append(f"User-Agent池过小（{ua_count}个），建议增加到10个以上")
        
        if hasattr(self, 'paused_domains') and self.paused_domains:
            recommendations.append(f"有{len(self.paused_domains)}个域名被暂停，请检查原因")
        
        if not recommendations:
            recommendations.append("爬虫运行正常，无需特别关注")
        
        return recommendations


# 全局实例
anti_crawler = AntiCrawlerSystem()







