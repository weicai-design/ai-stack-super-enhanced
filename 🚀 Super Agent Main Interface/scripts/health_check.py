#!/usr/bin/env python3
"""
AI Stack Super Enhanced 健康检查脚本
用于检查系统各项服务的健康状态
"""

import asyncio
import sys
import time
from typing import Dict, List, Any
from enum import Enum
import psutil
import httpx
import redis
import asyncpg
from datetime import datetime

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthCheckResult:
    """健康检查结果"""
    
    def __init__(self, service: str, status: HealthStatus, 
                 response_time: float = 0.0, error: str = None):
        self.service = service
        self.status = status
        self.response_time = response_time
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "service": self.service,
            "status": self.status.value,
            "response_time": self.response_time,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }

class HealthChecker:
    """健康检查器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: List[HealthCheckResult] = []
    
    async def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源"""
        start_time = time.time()
        
        try:
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 检查内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 检查磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            response_time = time.time() - start_time
            
            # 判断健康状态
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                error = f"资源使用率过高: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%"
            elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
                status = HealthStatus.DEGRADED
                error = f"资源使用率较高: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%"
            else:
                status = HealthStatus.HEALTHY
                error = None
            
            return HealthCheckResult("system_resources", status, response_time, error)
            
        except Exception as e:
            return HealthCheckResult("system_resources", HealthStatus.UNHEALTHY, 
                                   time.time() - start_time, f"系统资源检查失败: {str(e)}")
    
    async def check_database(self) -> HealthCheckResult:
        """检查数据库连接"""
        start_time = time.time()
        
        try:
            # 从配置获取数据库连接信息
            db_config = self.config.get('database', {})
            
            # 测试数据库连接
            conn = await asyncpg.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                user=db_config.get('user', 'postgres'),
                password=db_config.get('password', ''),
                database=db_config.get('name', 'aistack')
            )
            
            # 执行简单查询测试
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            response_time = time.time() - start_time
            
            if result == 1:
                return HealthCheckResult("database", HealthStatus.HEALTHY, response_time)
            else:
                return HealthCheckResult("database", HealthStatus.UNHEALTHY, 
                                       response_time, "数据库查询测试失败")
            
        except Exception as e:
            return HealthCheckResult("database", HealthStatus.UNHEALTHY, 
                                   time.time() - start_time, f"数据库连接失败: {str(e)}")
    
    async def check_redis(self) -> HealthCheckResult:
        """检查Redis连接"""
        start_time = time.time()
        
        try:
            # 从配置获取Redis连接信息
            redis_config = self.config.get('redis', {})
            
            # 测试Redis连接
            r = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                password=redis_config.get('password', None),
                db=redis_config.get('db', 0),
                socket_connect_timeout=5
            )
            
            # 执行PING命令测试
            result = r.ping()
            r.close()
            
            response_time = time.time() - start_time
            
            if result:
                return HealthCheckResult("redis", HealthStatus.HEALTHY, response_time)
            else:
                return HealthCheckResult("redis", HealthStatus.UNHEALTHY, 
                                       response_time, "Redis PING测试失败")
            
        except Exception as e:
            return HealthCheckResult("redis", HealthStatus.UNHEALTHY, 
                                   time.time() - start_time, f"Redis连接失败: {str(e)}")
    
    async def check_api_endpoints(self) -> HealthCheckResult:
        """检查API端点"""
        start_time = time.time()
        
        try:
            # 从配置获取API端点信息
            api_config = self.config.get('api', {})
            base_url = api_config.get('base_url', 'http://localhost:8000')
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 检查健康端点
                health_response = await client.get(f"{base_url}/health")
                
                # 检查API文档端点
                docs_response = await client.get(f"{base_url}/docs")
                
            response_time = time.time() - start_time
            
            if health_response.status_code == 200 and docs_response.status_code == 200:
                return HealthCheckResult("api_endpoints", HealthStatus.HEALTHY, response_time)
            else:
                error = f"API端点检查失败: 健康端点={health_response.status_code}, 文档端点={docs_response.status_code}"
                return HealthCheckResult("api_endpoints", HealthStatus.DEGRADED, response_time, error)
            
        except Exception as e:
            return HealthCheckResult("api_endpoints", HealthStatus.UNHEALTHY, 
                                   time.time() - start_time, f"API端点检查失败: {str(e)}")
    
    async def check_external_services(self) -> HealthCheckResult:
        """检查外部服务"""
        start_time = time.time()
        
        try:
            # 检查网络连通性
            async with httpx.AsyncClient(timeout=5.0) as client:
                # 检查互联网连通性
                internet_response = await client.get("https://www.google.com")
                
                # 检查DNS解析
                dns_response = await client.get("https://8.8.8.8")
            
            response_time = time.time() - start_time
            
            if internet_response.status_code == 200:
                return HealthCheckResult("external_services", HealthStatus.HEALTHY, response_time)
            else:
                return HealthCheckResult("external_services", HealthStatus.DEGRADED, 
                                       response_time, "外部服务连通性检查失败")
            
        except Exception as e:
            return HealthCheckResult("external_services", HealthStatus.DEGRADED, 
                                   time.time() - start_time, f"外部服务检查失败: {str(e)}")
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        checks = [
            self.check_system_resources(),
            self.check_database(),
            self.check_redis(),
            self.check_api_endpoints(),
            self.check_external_services()
        ]
        
        # 并行执行所有检查
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # 处理结果
        self.results = []
        for result in results:
            if isinstance(result, Exception):
                self.results.append(HealthCheckResult("unknown", HealthStatus.UNKNOWN, 
                                                   0.0, f"检查执行异常: {str(result)}"))
            else:
                self.results.append(result)
        
        # 计算总体健康状态
        overall_status = self._calculate_overall_status()
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": [result.to_dict() for result in self.results]
        }
    
    def _calculate_overall_status(self) -> HealthStatus:
        """计算总体健康状态"""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for result in self.results:
            status_counts[result.status] += 1
        
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.UNKNOWN] > len(self.results) / 2:
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def generate_report(self) -> str:
        """生成健康检查报告"""
        report = []
        report.append("=" * 60)
        report.append("AI Stack Super Enhanced 健康检查报告")
        report.append("=" * 60)
        report.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 总体状态
        overall_status = self._calculate_overall_status()
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        
        report.append(f"总体状态: {status_emoji[overall_status]} {overall_status.value.upper()}")
        report.append("")
        
        # 详细检查结果
        report.append("详细检查结果:")
        report.append("-" * 40)
        
        for result in self.results:
            emoji = status_emoji[result.status]
            report.append(f"{emoji} {result.service:<20} {result.status.value:<10} {result.response_time:.3f}s")
            if result.error:
                report.append(f"   错误: {result.error}")
        
        report.append("")
        report.append("状态说明:")
        report.append("✅ HEALTHY   - 服务正常")
        report.append("⚠️ DEGRADED  - 服务降级")
        report.append("❌ UNHEALTHY - 服务异常")
        report.append("❓ UNKNOWN   - 状态未知")
        report.append("=" * 60)
        
        return "\n".join(report)

async def main():
    """主函数"""
    # 默认配置
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': '',
            'name': 'aistack'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'password': None,
            'db': 0
        },
        'api': {
            'base_url': 'http://localhost:8000'
        }
    }
    
    # 创建健康检查器
    checker = HealthChecker(config)
    
    # 运行健康检查
    print("开始运行健康检查...")
    results = await checker.run_all_checks()
    
    # 生成并显示报告
    report = checker.generate_report()
    print(report)
    
    # 根据总体状态设置退出码
    overall_status = checker._calculate_overall_status()
    if overall_status == HealthStatus.UNHEALTHY:
        sys.exit(1)
    elif overall_status == HealthStatus.DEGRADED:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())