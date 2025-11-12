"""
性能监控工具
用于监控API响应时间和性能指标
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = []
        self.max_metrics = 1000  # 最多保存1000条指标
    
    def record(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录性能指标
        
        Args:
            operation: 操作名称
            duration: 耗时（秒）
            success: 是否成功
            metadata: 额外元数据
        """
        metric = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.metrics.append(metric)
        
        # 限制指标数量
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
        
        # 如果耗时过长，记录警告
        if duration > 5.0:
            logger.warning(f"操作 {operation} 耗时过长: {duration:.2f}秒")
    
    def get_statistics(
        self,
        operation: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            operation: 操作名称（可选）
            hours: 时间范围（小时）
            
        Returns:
            统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
            and (operation is None or m["operation"] == operation)
        ]
        
        if not filtered_metrics:
            return {
                "count": 0,
                "avg_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "success_rate": 0
            }
        
        durations = [m["duration"] for m in filtered_metrics]
        successes = [m["success"] for m in filtered_metrics]
        
        return {
            "count": len(filtered_metrics),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "success_rate": sum(successes) / len(successes) if successes else 0
        }
    
    def get_slow_operations(
        self,
        threshold: float = 3.0,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        获取慢操作列表
        
        Args:
            threshold: 阈值（秒）
            hours: 时间范围（小时）
            
        Returns:
            慢操作列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        slow_ops = [
            m for m in self.metrics
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
            and m["duration"] >= threshold
        ]
        
        return sorted(slow_ops, key=lambda x: x["duration"], reverse=True)


# 全局性能监控器
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: Optional[str] = None):
    """
    性能监控装饰器
    
    Args:
        operation_name: 操作名称（如果不提供，使用函数名）
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record(
                    operation=op_name,
                    duration=duration,
                    success=success
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record(
                    operation=op_name,
                    duration=duration,
                    success=success
                )
        
        # 根据函数是否为协程选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

