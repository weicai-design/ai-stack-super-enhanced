"""
用户行为分析中间件
Analytics Middleware

记录和分析API请求，提供使用统计和报告

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


# ==================== 数据存储 ====================

class AnalyticsStore:
    """分析数据存储（内存存储，生产环境建议使用数据库）"""
    
    def __init__(self):
        self.requests = []  # 所有请求记录
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "errors": 0,
            "success": 0
        })
        self.ip_stats = defaultdict(lambda: {
            "count": 0,
            "endpoints": defaultdict(int),
            "errors": 0
        })
        self.hourly_stats = defaultdict(int)
        self.daily_stats = defaultdict(int)
        self.status_code_stats = defaultdict(int)
        self.user_agent_stats = defaultdict(int)
        
        # 性能统计
        self.slow_requests = []  # 慢请求（>1秒）
        self.error_requests = []  # 错误请求
        
        # 统计信息
        self.start_time = datetime.now()
        self.total_requests = 0
        self.total_errors = 0
    
    def add_request(self, request_data: Dict[str, Any]):
        """添加请求记录"""
        self.requests.append(request_data)
        
        # 限制内存中的记录数（保留最近10000条）
        if len(self.requests) > 10000:
            self.requests = self.requests[-10000:]
        
        # 更新统计
        endpoint = request_data.get("endpoint", "unknown")
        ip = request_data.get("ip", "unknown")
        duration = request_data.get("duration", 0)
        status_code = request_data.get("status_code", 0)
        user_agent = request_data.get("user_agent", "unknown")
        
        # 端点统计
        self.endpoint_stats[endpoint]["count"] += 1
        self.endpoint_stats[endpoint]["total_time"] += duration
        
        if status_code >= 400:
            self.endpoint_stats[endpoint]["errors"] += 1
            self.total_errors += 1
        else:
            self.endpoint_stats[endpoint]["success"] += 1
        
        # IP统计
        self.ip_stats[ip]["count"] += 1
        self.ip_stats[ip]["endpoints"][endpoint] += 1
        if status_code >= 400:
            self.ip_stats[ip]["errors"] += 1
        
        # 时间统计
        timestamp = request_data.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                day_key = dt.strftime("%Y-%m-%d")
                self.hourly_stats[hour_key] += 1
                self.daily_stats[day_key] += 1
            except:
                pass
        
        # 状态码统计
        self.status_code_stats[status_code] += 1
        
        # User-Agent统计
        self.user_agent_stats[user_agent] += 1
        
        # 总请求数
        self.total_requests += 1
        
        # 慢请求记录（>1秒）
        if duration > 1.0:
            self.slow_requests.append(request_data)
            if len(self.slow_requests) > 100:
                self.slow_requests = self.slow_requests[-100:]
        
        # 错误请求记录
        if status_code >= 400:
            self.error_requests.append(request_data)
            if len(self.error_requests) > 100:
                self.error_requests = self.error_requests[-100:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # 计算平均响应时间
        total_time = sum(
            stats["total_time"] 
            for stats in self.endpoint_stats.values()
        )
        avg_response_time = total_time / max(self.total_requests, 1)
        
        # Top端点（按请求数排序）
        top_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        # Top IP（按请求数排序）
        top_ips = sorted(
            self.ip_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        
        # 错误率
        error_rate = (self.total_errors / max(self.total_requests, 1)) * 100
        
        return {
            "overview": {
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate": f"{error_rate:.2f}%",
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600,
                "avg_response_time": f"{avg_response_time:.3f}s",
                "requests_per_second": self.total_requests / max(uptime, 1)
            },
            "top_endpoints": [
                {
                    "endpoint": endpoint,
                    "count": stats["count"],
                    "avg_time": f"{stats['total_time'] / max(stats['count'], 1):.3f}s",
                    "errors": stats["errors"],
                    "success_rate": f"{(stats['success'] / max(stats['count'], 1)) * 100:.1f}%"
                }
                for endpoint, stats in top_endpoints
            ],
            "top_ips": [
                {
                    "ip": ip,
                    "count": stats["count"],
                    "unique_endpoints": len(stats["endpoints"]),
                    "errors": stats["errors"]
                }
                for ip, stats in top_ips
            ],
            "status_codes": dict(self.status_code_stats),
            "slow_requests_count": len(self.slow_requests),
            "error_requests_count": len(self.error_requests)
        }
    
    def get_hourly_stats(self, hours: int = 24) -> Dict[str, int]:
        """获取最近N小时的统计"""
        now = datetime.now()
        result = {}
        
        for i in range(hours):
            hour_key = (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
            result[hour_key] = self.hourly_stats.get(hour_key, 0)
        
        return dict(sorted(result.items()))
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, int]:
        """获取最近N天的统计"""
        now = datetime.now()
        result = {}
        
        for i in range(days):
            day_key = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            result[day_key] = self.daily_stats.get(day_key, 0)
        
        return dict(sorted(result.items()))
    
    def get_slow_requests(self, limit: int = 20) -> List[Dict]:
        """获取慢请求列表"""
        return sorted(
            self.slow_requests,
            key=lambda x: x.get("duration", 0),
            reverse=True
        )[:limit]
    
    def get_error_requests(self, limit: int = 20) -> List[Dict]:
        """获取错误请求列表"""
        return sorted(
            self.error_requests,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
    
    def clear_old_data(self, days: int = 7):
        """清理旧数据"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        # 清理旧请求
        self.requests = [
            req for req in self.requests
            if req.get("timestamp", "") > cutoff_str
        ]
        
        logger.info(f"清理了{days}天前的旧数据")


# ==================== 中间件 ====================

class AnalyticsMiddleware(BaseHTTPMiddleware):
    """分析中间件"""
    
    def __init__(self, app, store: AnalyticsStore = None):
        super().__init__(app)
        self.store = store or AnalyticsStore()
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 记录开始时间
        start_time = time.time()
        
        # 获取请求信息
        method = request.method
        url = str(request.url)
        endpoint = request.url.path
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            logger.error(f"请求处理异常: {e}")
            status_code = 500
            error = str(e)
            # 重新抛出异常
            raise
        finally:
            # 计算耗时
            duration = time.time() - start_time
            
            # 记录请求
            request_data = {
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "url": url,
                "endpoint": endpoint,
                "ip": ip,
                "user_agent": user_agent,
                "status_code": status_code,
                "duration": duration,
                "error": error
            }
            
            try:
                self.store.add_request(request_data)
            except Exception as e:
                logger.error(f"记录请求失败: {e}")
        
        return response


# ==================== 全局实例 ====================

# 创建全局存储实例
analytics_store = AnalyticsStore()


# ==================== 辅助函数 ====================

def get_analytics_store() -> AnalyticsStore:
    """获取分析存储实例"""
    return analytics_store


def generate_report(store: AnalyticsStore = None) -> Dict[str, Any]:
    """生成分析报告"""
    store = store or analytics_store
    
    return {
        "report_time": datetime.now().isoformat(),
        "statistics": store.get_statistics(),
        "hourly_trend": store.get_hourly_stats(24),
        "daily_trend": store.get_daily_stats(7),
        "slow_requests": store.get_slow_requests(10),
        "recent_errors": store.get_error_requests(10)
    }


# ==================== 导出 ====================

__all__ = [
    "AnalyticsMiddleware",
    "AnalyticsStore",
    "analytics_store",
    "get_analytics_store",
    "generate_report"
]












