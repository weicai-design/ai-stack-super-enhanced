"""
资源监控器
实时监控系统资源使用情况
"""

import psutil
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        # 系统配置（MacBook Pro 2018）
        self.system_config = {
            "cpu_cores": 6,
            "cpu_threads": 12,
            "total_memory_gb": 32,
            "internal_disk_gb": 512,
            "external_disks": ["Huawei-1", "Huawei-2"],
            "external_disk_size_gb": 1024
        }
        
        # 资源阈值配置
        self.thresholds = {
            "cpu_warning": 70,      # CPU使用率警告阈值
            "cpu_critical": 85,     # CPU使用率危险阈值
            "memory_warning": 75,   # 内存使用率警告阈值
            "memory_critical": 90,  # 内存使用率危险阈值
            "disk_warning": 80,     # 磁盘使用率警告阈值
            "disk_critical": 95     # 磁盘使用率危险阈值
        }
        
        # 服务资源使用记录
        self.service_usage = {}
        
        logger.info("资源监控器初始化完成")
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        获取系统资源使用情况
        
        Returns:
            系统资源信息
        """
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            # 内存信息
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # 磁盘信息
            disk_partitions = psutil.disk_partitions()
            disk_info = []
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": usage.total / (1024 ** 3),
                        "used_gb": usage.used / (1024 ** 3),
                        "free_gb": usage.free / (1024 ** 3),
                        "percent": usage.percent
                    })
                except Exception as e:
                    logger.warning(f"获取磁盘 {partition.device} 信息失败: {e}")
            
            # 网络信息
            net_io = psutil.net_io_counters()
            
            # 进程信息
            process_count = len(psutil.pids())
            
            resources = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "total_percent": cpu_percent,
                    "per_core_percent": cpu_per_core,
                    "cores": self.system_config["cpu_cores"],
                    "threads": self.system_config["cpu_threads"],
                    "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                    "max_frequency_mhz": cpu_freq.max if cpu_freq else 0
                },
                "memory": {
                    "total_gb": memory.total / (1024 ** 3),
                    "available_gb": memory.available / (1024 ** 3),
                    "used_gb": memory.used / (1024 ** 3),
                    "percent": memory.percent,
                    "swap_total_gb": swap.total / (1024 ** 3),
                    "swap_used_gb": swap.used / (1024 ** 3),
                    "swap_percent": swap.percent
                },
                "disk": disk_info,
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "processes": {
                    "total": process_count
                }
            }
            
            return resources
            
        except Exception as e:
            logger.error(f"获取系统资源失败: {e}")
            return {}
    
    def check_resource_status(self, resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查资源状态，判断是否超过阈值
        
        Args:
            resources: 资源信息
            
        Returns:
            资源状态评估
        """
        status = {
            "overall": "healthy",
            "warnings": [],
            "critical": [],
            "details": {}
        }
        
        # 检查CPU
        cpu_percent = resources.get("cpu", {}).get("total_percent", 0)
        if cpu_percent >= self.thresholds["cpu_critical"]:
            status["critical"].append(f"CPU使用率危险: {cpu_percent:.1f}%")
            status["details"]["cpu"] = "critical"
        elif cpu_percent >= self.thresholds["cpu_warning"]:
            status["warnings"].append(f"CPU使用率偏高: {cpu_percent:.1f}%")
            status["details"]["cpu"] = "warning"
        else:
            status["details"]["cpu"] = "healthy"
        
        # 检查内存
        memory_percent = resources.get("memory", {}).get("percent", 0)
        if memory_percent >= self.thresholds["memory_critical"]:
            status["critical"].append(f"内存使用率危险: {memory_percent:.1f}%")
            status["details"]["memory"] = "critical"
        elif memory_percent >= self.thresholds["memory_warning"]:
            status["warnings"].append(f"内存使用率偏高: {memory_percent:.1f}%")
            status["details"]["memory"] = "warning"
        else:
            status["details"]["memory"] = "healthy"
        
        # 检查磁盘
        disk_issues = []
        for disk in resources.get("disk", []):
            disk_percent = disk.get("percent", 0)
            mountpoint = disk.get("mountpoint", "未知")
            
            if disk_percent >= self.thresholds["disk_critical"]:
                disk_issues.append(f"{mountpoint} 磁盘空间危险: {disk_percent:.1f}%")
                status["details"][f"disk_{mountpoint}"] = "critical"
            elif disk_percent >= self.thresholds["disk_warning"]:
                disk_issues.append(f"{mountpoint} 磁盘空间不足: {disk_percent:.1f}%")
                status["details"][f"disk_{mountpoint}"] = "warning"
            else:
                status["details"][f"disk_{mountpoint}"] = "healthy"
        
        if disk_issues:
            if any("危险" in issue for issue in disk_issues):
                status["critical"].extend(disk_issues)
            else:
                status["warnings"].extend(disk_issues)
        
        # 设置总体状态
        if status["critical"]:
            status["overall"] = "critical"
        elif status["warnings"]:
            status["overall"] = "warning"
        
        return status
    
    def get_service_resource_usage(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        获取特定服务的资源使用情况
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务资源使用信息
        """
        try:
            # 查找服务进程
            service_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if service_name.lower() in proc.info['name'].lower():
                        service_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not service_processes:
                return None
            
            # 计算总资源使用
            total_cpu = sum(proc.cpu_percent() for proc in service_processes)
            total_memory = sum(proc.memory_percent() for proc in service_processes)
            
            usage = {
                "service_name": service_name,
                "process_count": len(service_processes),
                "cpu_percent": total_cpu,
                "memory_percent": total_memory,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存到历史记录
            self.service_usage[service_name] = usage
            
            return usage
            
        except Exception as e:
            logger.error(f"获取服务 {service_name} 资源使用失败: {e}")
            return None
    
    def get_all_services_usage(self, service_names: List[str]) -> Dict[str, Any]:
        """
        获取所有服务的资源使用情况
        
        Args:
            service_names: 服务名称列表
            
        Returns:
            所有服务的资源使用
        """
        all_usage = {}
        
        for service_name in service_names:
            usage = self.get_service_resource_usage(service_name)
            if usage:
                all_usage[service_name] = usage
        
        return all_usage
    
    def estimate_available_resources(self) -> Dict[str, Any]:
        """
        估算可用资源
        
        Returns:
            可用资源估算
        """
        resources = self.get_system_resources()
        
        available = {
            "cpu_available_percent": 100 - resources.get("cpu", {}).get("total_percent", 0),
            "memory_available_gb": resources.get("memory", {}).get("available_gb", 0),
            "can_start_new_service": True,
            "recommendations": []
        }
        
        # 判断是否可以启动新服务
        cpu_percent = resources.get("cpu", {}).get("total_percent", 0)
        memory_percent = resources.get("memory", {}).get("percent", 0)
        
        if cpu_percent > self.thresholds["cpu_warning"]:
            available["can_start_new_service"] = False
            available["recommendations"].append("CPU使用率过高，建议等待或关闭部分服务")
        
        if memory_percent > self.thresholds["memory_warning"]:
            available["can_start_new_service"] = False
            available["recommendations"].append("内存使用率过高，建议释放内存或关闭部分服务")
        
        return available
    
    def get_resource_trend(self, window_minutes: int = 5) -> Dict[str, Any]:
        """
        获取资源使用趋势
        
        Args:
            window_minutes: 时间窗口（分钟）
            
        Returns:
            资源趋势分析
        """
        # 简化版本，实际应从历史数据计算
        current = self.get_system_resources()
        
        trend = {
            "timestamp": datetime.now().isoformat(),
            "window_minutes": window_minutes,
            "cpu_trend": "stable",  # stable/increasing/decreasing
            "memory_trend": "stable",
            "current_cpu": current.get("cpu", {}).get("total_percent", 0),
            "current_memory": current.get("memory", {}).get("percent", 0)
        }
        
        return trend
    
    def suggest_resource_optimization(self, resources: Dict[str, Any]) -> List[str]:
        """
        建议资源优化措施
        
        Args:
            resources: 当前资源信息
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        cpu_percent = resources.get("cpu", {}).get("total_percent", 0)
        memory_percent = resources.get("memory", {}).get("percent", 0)
        
        if cpu_percent > 80:
            suggestions.append("建议关闭不必要的后台进程")
            suggestions.append("考虑限制部分服务的CPU使用率")
        
        if memory_percent > 85:
            suggestions.append("建议清理内存缓存")
            suggestions.append("考虑重启占用内存过多的服务")
        
        # 检查磁盘空间
        for disk in resources.get("disk", []):
            if disk.get("percent", 0) > 85:
                suggestions.append(f"建议清理 {disk['mountpoint']} 磁盘空间")
        
        if not suggestions:
            suggestions.append("系统资源使用正常，无需优化")
        
        return suggestions

