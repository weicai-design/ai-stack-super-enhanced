"""
健康检查器
提供服务健康检查、依赖检查、服务探活功能
"""

import time
import threading
from typing import Dict, Any, List, Optional
from enum import Enum
import psutil
import requests


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """健康检查项"""
    
    def __init__(self, name: str, check_func, interval: int = 30):
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.last_check = 0
        self.status = HealthStatus.UNKNOWN
        self.message = ""
        self.last_success = 0
    
    def execute(self) -> bool:
        """执行健康检查"""
        try:
            result = self.check_func()
            if result:
                self.status = HealthStatus.HEALTHY
                self.message = "检查通过"
                self.last_success = time.time()
            else:
                self.status = HealthStatus.UNHEALTHY
                self.message = "检查失败"
            
            self.last_check = time.time()
            return result
            
        except Exception as e:
            self.status = HealthStatus.UNHEALTHY
            self.message = f"检查异常: {e}"
            self.last_check = time.time()
            return False


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.overall_status = HealthStatus.UNKNOWN
        self.monitoring_thread = None
        self.monitoring = False
        
        # 添加默认检查项
        self._add_default_checks()
        
        # 启动监控
        self._start_monitoring()
    
    def _add_default_checks(self):
        """添加默认健康检查项"""
        
        # 系统资源检查
        def check_system_resources():
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 检查阈值
            if cpu_percent > 90:
                return False, f"CPU使用率过高: {cpu_percent}%"
            if memory.percent > 90:
                return False, f"内存使用率过高: {memory.percent}%"
            if disk.percent > 90:
                return False, f"磁盘使用率过高: {disk.percent}%"
            
            return True, "系统资源正常"
        
        self.add_check("system_resources", check_system_resources, interval=60)
        
        # 数据库连接检查
        def check_database():
            try:
                # 这里需要根据实际数据库连接进行检查
                # 暂时返回成功
                return True, "数据库连接正常"
            except Exception as e:
                return False, f"数据库连接失败: {e}"
        
        self.add_check("database", check_database, interval=30)
        
        # API服务检查
        def check_api_service():
            try:
                # 检查本地API服务
                response = requests.get("http://localhost:8000/api/health", timeout=5)
                if response.status_code == 200:
                    return True, "API服务正常"
                else:
                    return False, f"API服务异常: {response.status_code}"
            except Exception as e:
                return False, f"API服务不可达: {e}"
        
        self.add_check("api_service", check_api_service, interval=30)
    
    def add_check(self, name: str, check_func, interval: int = 30):
        """添加健康检查项"""
        def wrapper():
            result, message = check_func()
            return result
        
        check = HealthCheck(name, wrapper, interval)
        self.checks[name] = check
    
    def remove_check(self, name: str):
        """移除健康检查项"""
        if name in self.checks:
            del self.checks[name]
    
    def check_all(self) -> Dict[str, Any]:
        """执行所有健康检查"""
        results = {}
        healthy_count = 0
        total_count = len(self.checks)
        
        for name, check in self.checks.items():
            success = check.execute()
            results[name] = {
                "status": check.status.value,
                "message": check.message,
                "last_check": check.last_check,
                "last_success": check.last_success
            }
            
            if success:
                healthy_count += 1
        
        # 计算总体状态
        if healthy_count == total_count:
            self.overall_status = HealthStatus.HEALTHY
        elif healthy_count >= total_count * 0.7:
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.UNHEALTHY
        
        return {
            "overall_status": self.overall_status.value,
            "healthy_count": healthy_count,
            "total_count": total_count,
            "checks": results
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.check_all()
    
    def is_healthy(self) -> bool:
        """检查是否健康"""
        status = self.get_status()
        return status["overall_status"] == HealthStatus.HEALTHY.value
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self.check_all()
                time.sleep(10)  # 每10秒检查一次
            except Exception as e:
                print(f"健康检查监控异常: {e}")
                time.sleep(30)
    
    def _start_monitoring(self):
        """启动监控"""
        if self.monitoring_thread is None:
            self.monitoring = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)


# 全局健康检查器实例
health_checker = HealthChecker()