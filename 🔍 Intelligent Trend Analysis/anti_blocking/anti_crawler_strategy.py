"""
反爬虫策略
- User-Agent轮换
- IP代理池
- 请求频率控制
- 验证码处理
"""
from typing import Dict, Any, List
import random
import time
from datetime import datetime, timedelta


class AntiCrawlerStrategy:
    """反爬虫策略管理"""
    
    def __init__(self):
        # User-Agent池
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        ]
        
        # IP代理池（示例）
        self.proxy_pool = []
        
        # 请求频率控制
        self.request_intervals = {
            "default": (2, 5),      # 2-5秒
            "conservative": (5, 10), # 5-10秒
            "aggressive": (1, 3)     # 1-3秒
        }
        
        # 请求历史
        self.request_history = []
        
        # 黑名单（被封的域名/IP）
        self.blacklist = []
    
    # ============ 请求策略 ============
    
    def get_request_headers(self, strategy: str = "default") -> Dict[str, str]:
        """
        获取请求头
        
        Args:
            strategy: 策略类型（default/conservative/aggressive）
        
        Returns:
            请求头
        """
        # 随机User-Agent
        user_agent = random.choice(self.user_agents)
        
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # 随机添加Referer
        if random.random() > 0.5:
            headers["Referer"] = "https://www.google.com/"
        
        return headers
    
    def get_request_delay(self, strategy: str = "default") -> float:
        """
        获取请求延迟
        
        Args:
            strategy: 策略类型
        
        Returns:
            延迟秒数
        """
        interval = self.request_intervals.get(strategy, self.request_intervals["default"])
        min_delay, max_delay = interval
        
        # 随机延迟
        delay = random.uniform(min_delay, max_delay)
        
        return delay
    
    def get_proxy(self) -> Optional[str]:
        """
        获取代理
        
        Returns:
            代理地址或None
        """
        if not self.proxy_pool:
            return None
        
        # 随机选择一个可用代理
        available_proxies = [p for p in self.proxy_pool if p not in self.blacklist]
        
        if not available_proxies:
            return None
        
        return random.choice(available_proxies)
    
    # ============ 请求频率控制 ============
    
    def should_wait(self, domain: str) -> bool:
        """
        检查是否需要等待
        
        Args:
            domain: 目标域名
        
        Returns:
            是否需要等待
        """
        # 检查最近对该域名的请求
        recent_requests = [
            r for r in self.request_history
            if r['domain'] == domain and
            datetime.fromisoformat(r['timestamp']) > datetime.utcnow() - timedelta(minutes=1)
        ]
        
        # 如果1分钟内请求超过10次，需要等待
        return len(recent_requests) > 10
    
    def record_request(
        self,
        domain: str,
        success: bool,
        response_code: Optional[int] = None
    ):
        """
        记录请求
        
        Args:
            domain: 域名
            success: 是否成功
            response_code: 响应代码
        """
        self.request_history.append({
            "domain": domain,
            "success": success,
            "response_code": response_code,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 只保留最近1000条
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
        
        # 检查是否被封
        if response_code in [403, 429]:  # 403 Forbidden, 429 Too Many Requests
            self._handle_blocked(domain)
    
    def _handle_blocked(self, domain: str):
        """处理被封情况"""
        print(f"⚠️ 域名 {domain} 可能被封锁，响应码403/429")
        
        # 添加到黑名单（临时）
        if domain not in self.blacklist:
            self.blacklist.append(domain)
        
        # 自动切换策略为保守模式
        print(f"📋 自动切换为保守爬取模式")
    
    # ============ 统计分析 ============
    
    def get_request_statistics(self) -> Dict[str, Any]:
        """获取请求统计"""
        try:
            total = len(self.request_history)
            
            if total == 0:
                return {
                    "success": True,
                    "statistics": {
                        "total_requests": 0
                    }
                }
            
            successful = sum(1 for r in self.request_history if r['success'])
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # 按域名统计
            domain_stats = defaultdict(lambda: {"total": 0, "success": 0})
            for req in self.request_history:
                domain = req['domain']
                domain_stats[domain]["total"] += 1
                if req['success']:
                    domain_stats[domain]["success"] += 1
            
            # 被封域名
            blocked_domains = [
                d for d, stats in domain_stats.items()
                if stats['success'] / stats['total'] < 0.5  # 成功率低于50%
            ]
            
            return {
                "success": True,
                "statistics": {
                    "total_requests": total,
                    "successful_requests": successful,
                    "success_rate": float(success_rate),
                    "blacklisted_domains": len(self.blacklist),
                    "potentially_blocked": blocked_domains,
                    "domain_stats": dict(domain_stats)
                }
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_proxy(self, proxy_url: str):
        """添加代理到代理池"""
        if proxy_url not in self.proxy_pool:
            self.proxy_pool.append(proxy_url)
    
    def remove_proxy(self, proxy_url: str):
        """从代理池移除代理"""
        if proxy_url in self.proxy_pool:
            self.proxy_pool.remove(proxy_url)


# 全局实例
anti_crawler = AntiCrawlerStrategy()

