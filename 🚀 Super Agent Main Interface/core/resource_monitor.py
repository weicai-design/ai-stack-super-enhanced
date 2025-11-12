"""
资源监控系统
整合自🛠️ Intelligent System Resource Management/，融合到超级Agent
"""

import psutil
import platform
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

class ResourceMonitor:
    """
    资源监控系统
    
    功能：
    1. 监控CPU/内存/磁盘/网络
    2. 监控外接硬盘连接状态
    3. 分析资源问题
    4. 提供资源调节建议
    """
    
    def __init__(self):
        self.monitoring = False
        self.resource_history = []
        self.alerts = []
        
    async def start_monitoring(self, interval: int = 5):
        """开始监控"""
        self.monitoring = True
        while self.monitoring:
            await self._collect_resource_data()
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
    
    async def _collect_resource_data(self):
        """收集资源数据"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self._get_cpu_info(),
            "memory": self._get_memory_info(),
            "disk": self._get_disk_info(),
            "network": self._get_network_info(),
            "external_drives": self._get_external_drives()
        }
        
        self.resource_history.append(data)
        
        # 只保留最近100条记录
        if len(self.resource_history) > 100:
            self.resource_history = self.resource_history[-100:]
        
        # 检查资源问题
        await self._check_resource_issues(data)
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息"""
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "per_cpu": psutil.cpu_percent(interval=1, percpu=True)
        }
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free
        }
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """获取磁盘信息"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    
    def _get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    
    def _get_external_drives(self) -> List[Dict[str, Any]]:
        """获取外接硬盘信息"""
        external_drives = []
        
        # 获取所有磁盘分区
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            # 检查是否是外接设备（macOS/Linux）
            if platform.system() == "Darwin":  # macOS
                if "/Volumes" in partition.mountpoint:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        external_drives.append({
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                            "connected": True
                        })
                    except PermissionError:
                        pass
        
        return external_drives
    
    async def _check_resource_issues(self, data: Dict):
        """检查资源问题"""
        issues = []
        
        # CPU使用率过高
        if data["cpu"]["percent"] > 80:
            issues.append({
                "type": "cpu_high",
                "severity": "high",
                "value": data["cpu"]["percent"],
                "threshold": 80,
                "suggestion": "CPU使用率过高，建议关闭不必要的进程"
            })
        
        # 内存使用率过高
        if data["memory"]["percent"] > 85:
            issues.append({
                "type": "memory_high",
                "severity": "high",
                "value": data["memory"]["percent"],
                "threshold": 85,
                "suggestion": "内存使用率过高，建议清理缓存或关闭应用"
            })
        
        # 磁盘空间不足
        if data["disk"]["percent"] > 90:
            issues.append({
                "type": "disk_full",
                "severity": "high",
                "value": data["disk"]["percent"],
                "threshold": 90,
                "suggestion": "磁盘空间不足，建议清理文件或扩展存储"
            })
        
        # 外接硬盘连接状态
        if data["external_drives"]:
            for drive in data["external_drives"]:
                if drive.get("percent", 0) > 90:
                    issues.append({
                        "type": "external_drive_full",
                        "severity": "medium",
                        "drive": drive["mountpoint"],
                        "value": drive["percent"],
                        "suggestion": f"外接硬盘 {drive['mountpoint']} 空间不足"
                    })
        
        if issues:
            self.alerts.extend(issues)
            # 只保留最近50条告警
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前资源状态⭐增强版（包含外接硬盘）"""
        if not self.resource_history:
            return {
                "cpu": {"percent": 0},
                "memory": {"percent": 0},
                "disk": {"percent": 0},
                "network": {},
                "external_drives": []
            }
        
        latest = self.resource_history[-1]
        
        # 确保包含外接硬盘信息
        if "external_drives" not in latest:
            latest["external_drives"] = self._get_external_drives()
        
        return latest
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """获取告警"""
        if severity:
            return [alert for alert in self.alerts if alert.get("severity") == severity]
        return self.alerts
    
    def get_resource_trends(self, hours: int = 1) -> Dict[str, List]:
        """获取资源趋势"""
        # 获取最近N小时的数据
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        trends = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "timestamps": []
        }
        
        for data in self.resource_history:
            timestamp = datetime.fromisoformat(data["timestamp"]).timestamp()
            if timestamp >= cutoff_time:
                trends["cpu"].append(data["cpu"]["percent"])
                trends["memory"].append(data["memory"]["percent"])
                trends["disk"].append(data["disk"]["percent"])
                trends["timestamps"].append(data["timestamp"])
        
        return trends

