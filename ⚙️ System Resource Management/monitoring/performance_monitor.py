"""
性能监控系统
实时监控系统性能指标并提供优化建议
"""
import psutil
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import deque
import asyncio


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, history_size: int = 1000):
        """
        初始化性能监控器
        
        Args:
            history_size: 历史数据保存数量
        """
        self.history_size = history_size
        
        # 历史数据（使用deque实现固定大小的队列）
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        
        # 性能阈值
        self.thresholds = {
            "cpu": 80.0,
            "memory": 85.0,
            "disk": 90.0,
            "network_io": 100 * 1024 * 1024  # 100MB/s
        }
        
        # 告警记录
        self.alerts = []
        
        # 监控状态
        self.is_monitoring = False
    
    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集当前性能指标
        
        Returns:
            性能指标数据
        """
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存指标
        memory = psutil.virtual_memory()
        
        # 磁盘指标
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # 网络指标
        network_io = psutil.net_io_counters()
        
        # 进程信息
        process_count = len(psutil.pids())
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            },
            "process": {
                "count": process_count
            }
        }
        
        # 保存到历史
        self.cpu_history.append({
            "timestamp": metrics["timestamp"],
            "value": cpu_percent
        })
        
        self.memory_history.append({
            "timestamp": metrics["timestamp"],
            "value": memory.percent
        })
        
        self.disk_history.append({
            "timestamp": metrics["timestamp"],
            "value": disk.percent
        })
        
        return metrics
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        检查性能告警
        
        Args:
            metrics: 当前性能指标
        
        Returns:
            告警列表
        """
        alerts = []
        
        # CPU告警
        if metrics["cpu"]["percent"] > self.thresholds["cpu"]:
            alerts.append({
                "level": "warning" if metrics["cpu"]["percent"] < 90 else "critical",
                "type": "cpu",
                "message": f"CPU使用率过高: {metrics['cpu']['percent']:.1f}%",
                "value": metrics["cpu"]["percent"],
                "threshold": self.thresholds["cpu"],
                "timestamp": metrics["timestamp"]
            })
        
        # 内存告警
        if metrics["memory"]["percent"] > self.thresholds["memory"]:
            alerts.append({
                "level": "warning" if metrics["memory"]["percent"] < 95 else "critical",
                "type": "memory",
                "message": f"内存使用率过高: {metrics['memory']['percent']:.1f}%",
                "value": metrics["memory"]["percent"],
                "threshold": self.thresholds["memory"],
                "timestamp": metrics["timestamp"]
            })
        
        # 磁盘告警
        if metrics["disk"]["percent"] > self.thresholds["disk"]:
            alerts.append({
                "level": "warning" if metrics["disk"]["percent"] < 95 else "critical",
                "type": "disk",
                "message": f"磁盘使用率过高: {metrics['disk']['percent']:.1f}%",
                "value": metrics["disk"]["percent"],
                "threshold": self.thresholds["disk"],
                "timestamp": metrics["timestamp"]
            })
        
        # 保存告警
        self.alerts.extend(alerts)
        
        return alerts
    
    def get_statistics(self, metric_type: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        获取指定时间段的统计数据
        
        Args:
            metric_type: 指标类型 (cpu/memory/disk)
            duration_minutes: 时间段（分钟）
        
        Returns:
            统计数据
        """
        # 选择数据源
        if metric_type == "cpu":
            history = list(self.cpu_history)
        elif metric_type == "memory":
            history = list(self.memory_history)
        elif metric_type == "disk":
            history = list(self.disk_history)
        else:
            return {"error": "无效的指标类型"}
        
        if not history:
            return {"error": "暂无历史数据"}
        
        # 过滤指定时间段的数据
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_data = [
            item for item in history
            if datetime.fromisoformat(item["timestamp"]) > cutoff_time
        ]
        
        if not recent_data:
            recent_data = history
        
        values = [item["value"] for item in recent_data]
        
        return {
            "metric_type": metric_type,
            "duration_minutes": duration_minutes,
            "count": len(values),
            "current": values[-1] if values else 0,
            "average": sum(values) / len(values) if values else 0,
            "max": max(values) if values else 0,
            "min": min(values) if values else 0,
            "latest_timestamp": recent_data[-1]["timestamp"] if recent_data else None
        }
    
    def generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        生成性能优化建议
        
        Args:
            metrics: 当前性能指标
        
        Returns:
            优化建议列表
        """
        recommendations = []
        
        # CPU优化建议
        if metrics["cpu"]["percent"] > 70:
            recommendations.append(
                "💡 CPU使用率较高，建议：\n"
                "  • 检查并关闭不必要的后台进程\n"
                "  • 优化频繁执行的代码逻辑\n"
                "  • 考虑使用异步处理或多进程"
            )
        
        # 内存优化建议
        if metrics["memory"]["percent"] > 75:
            recommendations.append(
                "💡 内存使用率较高，建议：\n"
                "  • 检查内存泄漏\n"
                "  • 优化数据缓存策略\n"
                "  • 及时释放不需要的对象\n"
                "  • 考虑增加物理内存"
            )
        
        # 磁盘优化建议
        if metrics["disk"]["percent"] > 80:
            recommendations.append(
                "💡 磁盘空间不足，建议：\n"
                "  • 清理日志文件\n"
                "  • 删除临时文件\n"
                "  • 压缩或归档旧数据\n"
                "  • 考虑扩展磁盘空间"
            )
        
        # 进程数量建议
        if metrics["process"]["count"] > 300:
            recommendations.append(
                "💡 进程数量较多，建议：\n"
                "  • 检查是否有进程泄漏\n"
                "  • 合并相似功能的服务\n"
                "  • 优化服务启动策略"
            )
        
        return recommendations if recommendations else ["✅ 系统性能良好，暂无优化建议"]
    
    async def start_monitoring(self, interval: int = 60):
        """
        启动持续监控
        
        Args:
            interval: 监控间隔（秒）
        """
        self.is_monitoring = True
        print(f"🔍 开始性能监控（间隔：{interval}秒）...")
        
        while self.is_monitoring:
            metrics = self.collect_metrics()
            alerts = self.check_alerts(metrics)
            
            # 输出告警
            if alerts:
                for alert in alerts:
                    icon = "⚠️" if alert["level"] == "warning" else "🚨"
                    print(f"{icon} {alert['message']}")
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        print("⏹️ 性能监控已停止")
    
    def get_report(self) -> Dict[str, Any]:
        """
        生成性能报告
        
        Returns:
            性能报告
        """
        current_metrics = self.collect_metrics()
        
        cpu_stats = self.get_statistics("cpu", 60)
        memory_stats = self.get_statistics("memory", 60)
        disk_stats = self.get_statistics("disk", 60)
        
        recommendations = self.generate_recommendations(current_metrics)
        
        # 最近的告警
        recent_alerts = [
            alert for alert in self.alerts[-10:]
        ]
        
        return {
            "generated_at": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "statistics": {
                "cpu": cpu_stats,
                "memory": memory_stats,
                "disk": disk_stats
            },
            "recommendations": recommendations,
            "recent_alerts": recent_alerts,
            "alert_count": len(self.alerts)
        }


# 全局实例
performance_monitor = PerformanceMonitor()

