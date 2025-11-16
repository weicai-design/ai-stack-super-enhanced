"""
响应时间监控和性能优化模块
实现2秒响应时间保证
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    性能监控器
    监控响应时间，确保2秒内响应
    """
    
    def __init__(self, target_response_time: float = 2.0):
        """
        初始化性能监控器
        
        Args:
            target_response_time: 目标响应时间（秒），默认2秒
        """
        self.target_response_time = target_response_time
        self.response_times = deque(maxlen=1000)  # 保留最近1000次响应时间
        self.step_times = {}  # 各步骤耗时统计
        self.slow_queries = deque(maxlen=100)  # 慢查询记录
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "p50_response_time": 0.0,
            "p95_response_time": 0.0,
            "p99_response_time": 0.0,
            "timeout_count": 0,
            "cache_hit_rate": 0.0
        }
        self.cache_hits = 0
        self.cache_misses = 0
        
    def record_response_time(self, response_time: float, from_cache: bool = False):
        """
        记录响应时间
        
        Args:
            response_time: 响应时间（秒）
            from_cache: 是否来自缓存
        """
        self.response_times.append(response_time)
        self.performance_stats["total_requests"] += 1
        
        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        # 更新缓存命中率
        total = self.cache_hits + self.cache_misses
        if total > 0:
            self.performance_stats["cache_hit_rate"] = self.cache_hits / total
        
        # 检查是否超时
        if response_time > self.target_response_time:
            self.performance_stats["timeout_count"] += 1
            self.slow_queries.append({
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            })
            logger.warning(f"响应时间超时: {response_time:.2f}秒 > {self.target_response_time}秒")
        
        # 更新统计信息
        self._update_stats()
    
    def record_step_time(self, step_name: str, step_time: float):
        """
        记录步骤耗时
        
        Args:
            step_name: 步骤名称
            step_time: 步骤耗时（秒）
        """
        if step_name not in self.step_times:
            self.step_times[step_name] = deque(maxlen=100)
        
        self.step_times[step_name].append(step_time)
    
    def _update_stats(self):
        """更新性能统计"""
        if not self.response_times:
            return
        
        sorted_times = sorted(self.response_times)
        n = len(sorted_times)
        
        self.performance_stats["avg_response_time"] = sum(sorted_times) / n
        self.performance_stats["p50_response_time"] = sorted_times[n // 2]
        self.performance_stats["p95_response_time"] = sorted_times[int(n * 0.95)]
        self.performance_stats["p99_response_time"] = sorted_times[int(n * 0.99)]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self.performance_stats,
            "target_response_time": self.target_response_time,
            "current_response_rate": self._calculate_response_rate(),
            "step_times": {
                step: {
                    "avg": sum(times) / len(times) if times else 0,
                    "max": max(times) if times else 0,
                    "min": min(times) if times else 0,
                    "count": len(times)
                }
                for step, times in self.step_times.items()
            },
            "slow_queries_count": len(self.slow_queries)
        }
    
    def _calculate_response_rate(self) -> float:
        """计算响应率（2秒内响应占比）"""
        if not self.response_times:
            return 0.0
        
        within_target = sum(1 for rt in self.response_times if rt <= self.target_response_time)
        return within_target / len(self.response_times)
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """获取慢查询列表"""
        return list(self.slow_queries)[-limit:]
    
    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        for step_name, times in self.step_times.items():
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                
                # 如果平均时间超过目标时间的20%，或最大时间超过目标时间，认为是瓶颈
                if avg_time > self.target_response_time * 0.2 or max_time > self.target_response_time:
                    bottlenecks.append({
                        "step": step_name,
                        "avg_time": avg_time,
                        "max_time": max_time,
                        "count": len(times),
                        "severity": "high" if max_time > self.target_response_time else "medium"
                    })
        
        return sorted(bottlenecks, key=lambda x: x["max_time"], reverse=True)


class ResponseTimeOptimizer:
    """
    响应时间优化器
    通过缓存、异步、超时等策略优化响应时间
    """
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
        self.cache = {}
        self.cache_ttl = {}
        self.max_cache_size = 1000
        
    async def optimize_with_timeout(
        self,
        func: Callable,
        timeout: float,
        default_value: Any = None,
        cache_key: Optional[str] = None
    ) -> Any:
        """
        带超时的优化执行
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒）
            default_value: 超时时的默认返回值
            cache_key: 缓存键（可选）
            
        Returns:
            函数执行结果
        """
        # 检查缓存
        if cache_key and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl.get(cache_key, 300):
                self.performance_monitor.record_response_time(0.001, from_cache=True)
                return cached_data
        
        start_time = time.time()
        
        try:
            # 执行函数（带超时）
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(), timeout=timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func),
                    timeout=timeout
                )
            
            elapsed_time = time.time() - start_time
            
            # 记录响应时间
            self.performance_monitor.record_response_time(elapsed_time, from_cache=False)
            
            # 缓存结果
            if cache_key and elapsed_time < timeout * 0.8:  # 只缓存快速响应的结果
                self._set_cache(cache_key, result)
            
            return result
            
        except asyncio.TimeoutError:
            elapsed_time = time.time() - start_time
            self.performance_monitor.record_response_time(elapsed_time, from_cache=False)
            logger.warning(f"函数执行超时: {timeout}秒")
            return default_value
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.performance_monitor.record_response_time(elapsed_time, from_cache=False)
            logger.error(f"函数执行错误: {e}")
            raise
    
    def _set_cache(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        # 限制缓存大小
        if len(self.cache) >= self.max_cache_size:
            # 删除最旧的缓存
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
            del self.cache_ttl[oldest_key]
        
        self.cache[key] = (value, datetime.now())
        self.cache_ttl[key] = ttl
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_ttl.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "cache_keys": list(self.cache.keys())[:10]  # 只返回前10个键
        }


# 全局性能监控器实例
performance_monitor = PerformanceMonitor(target_response_time=2.0)
response_time_optimizer = ResponseTimeOptimizer(performance_monitor)









