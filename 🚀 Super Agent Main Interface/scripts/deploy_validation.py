#!/usr/bin/env python3
"""
AI Stack Super Enhanced 部署验证脚本
用于验证部署是否成功，检查各项功能是否正常
"""

import asyncio
import sys
import time
import json
from typing import Dict, List, Any, Optional
from enum import Enum
import httpx
import psutil
from datetime import datetime, timedelta

class ValidationStatus(Enum):
    """验证状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

class ValidationResult:
    """验证结果"""
    
    def __init__(self, test_name: str, status: ValidationStatus, 
                 duration: float = 0.0, details: str = None,
                 error: str = None):
        self.test_name = test_name
        self.status = status
        self.duration = duration
        self.details = details
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "test_name": self.test_name,
            "status": self.status.value,
            "duration": self.duration,
            "details": self.details,
            "error": self.error,
            "timestamp": self.timestamp.isoformat()
        }

class DeploymentValidator:
    """部署验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 api_key: str = None, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.results: List[ValidationResult] = []
        self.http_client = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.http_client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.http_client:
            await self.http_client.aclose()
    
    async def validate_service_availability(self) -> ValidationResult:
        """验证服务可用性"""
        start_time = time.time()
        
        try:
            # 检查健康端点
            response = await self.http_client.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                return ValidationResult(
                    "service_availability", 
                    ValidationStatus.PASSED,
                    duration,
                    f"服务健康状态: {health_data.get('status', 'unknown')}"
                )
            else:
                return ValidationResult(
                    "service_availability",
                    ValidationStatus.FAILED,
                    duration,
                    f"健康端点返回状态码: {response.status_code}"
                )
        
        except Exception as e:
            return ValidationResult(
                "service_availability",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"服务可用性检查失败: {str(e)}"
            )
    
    async def validate_api_endpoints(self) -> ValidationResult:
        """验证API端点"""
        start_time = time.time()
        endpoints_checked = 0
        endpoints_failed = 0
        
        try:
            # 需要验证的API端点列表
            endpoints = [
                "/api/v1/auth/login",
                "/api/v1/tenants",
                "/api/v1/audit/logs",
                "/api/v1/security/policies",
                "/api/v1/monitoring/metrics"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await self.http_client.get(f"{self.base_url}{endpoint}")
                    endpoints_checked += 1
                    
                    # 允许401/403（需要认证），但其他错误视为失败
                    if response.status_code not in [200, 401, 403]:
                        endpoints_failed += 1
                
                except Exception:
                    endpoints_failed += 1
            
            duration = time.time() - start_time
            
            if endpoints_failed == 0:
                return ValidationResult(
                    "api_endpoints",
                    ValidationStatus.PASSED,
                    duration,
                    f"成功检查 {endpoints_checked} 个API端点"
                )
            else:
                return ValidationResult(
                    "api_endpoints",
                    ValidationStatus.WARNING,
                    duration,
                    f"{endpoints_failed}/{endpoints_checked} 个API端点检查失败"
                )
        
        except Exception as e:
            return ValidationResult(
                "api_endpoints",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"API端点验证失败: {str(e)}"
            )
    
    async def validate_database_connectivity(self) -> ValidationResult:
        """验证数据库连接"""
        start_time = time.time()
        
        try:
            # 通过API测试数据库连接
            response = await self.http_client.get(f"{self.base_url}/api/v1/system/db-check")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return ValidationResult(
                    "database_connectivity",
                    ValidationStatus.PASSED,
                    duration,
                    "数据库连接正常"
                )
            else:
                return ValidationResult(
                    "database_connectivity",
                    ValidationStatus.FAILED,
                    duration,
                    f"数据库检查返回状态码: {response.status_code}"
                )
        
        except Exception as e:
            return ValidationResult(
                "database_connectivity",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"数据库连接验证失败: {str(e)}"
            )
    
    async def validate_cache_functionality(self) -> ValidationResult:
        """验证缓存功能"""
        start_time = time.time()
        
        try:
            # 测试缓存设置和获取
            test_key = f"deploy_test_{int(time.time())}"
            test_value = "deploy_validation"
            
            # 设置缓存
            set_response = await self.http_client.post(
                f"{self.base_url}/api/v1/cache/set",
                json={"key": test_key, "value": test_value, "expire": 60}
            )
            
            if set_response.status_code != 200:
                return ValidationResult(
                    "cache_functionality",
                    ValidationStatus.FAILED,
                    time.time() - start_time,
                    "缓存设置失败"
                )
            
            # 获取缓存
            get_response = await self.http_client.get(
                f"{self.base_url}/api/v1/cache/get",
                params={"key": test_key}
            )
            
            duration = time.time() - start_time
            
            if get_response.status_code == 200:
                cached_value = get_response.json().get("value")
                if cached_value == test_value:
                    return ValidationResult(
                        "cache_functionality",
                        ValidationStatus.PASSED,
                        duration,
                        "缓存功能正常"
                    )
                else:
                    return ValidationResult(
                        "cache_functionality",
                        ValidationStatus.FAILED,
                        duration,
                        "缓存值不匹配"
                    )
            else:
                return ValidationResult(
                    "cache_functionality",
                    ValidationStatus.FAILED,
                    duration,
                    "缓存获取失败"
                )
        
        except Exception as e:
            return ValidationResult(
                "cache_functionality",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"缓存功能验证失败: {str(e)}"
            )
    
    async def validate_authentication(self) -> ValidationResult:
        """验证认证功能"""
        start_time = time.time()
        
        try:
            # 测试认证端点
            auth_response = await self.http_client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123",
                    "tenant_id": "default"
                }
            )
            
            duration = time.time() - start_time
            
            if auth_response.status_code == 200:
                return ValidationResult(
                    "authentication",
                    ValidationStatus.PASSED,
                    duration,
                    "认证功能正常"
                )
            elif auth_response.status_code == 401:
                return ValidationResult(
                    "authentication",
                    ValidationStatus.WARNING,
                    duration,
                    "认证失败（可能为预期行为）"
                )
            else:
                return ValidationResult(
                    "authentication",
                    ValidationStatus.FAILED,
                    duration,
                    f"认证端点返回异常状态码: {auth_response.status_code}"
                )
        
        except Exception as e:
            return ValidationResult(
                "authentication",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"认证功能验证失败: {str(e)}"
            )
    
    async def validate_monitoring(self) -> ValidationResult:
        """验证监控功能"""
        start_time = time.time()
        
        try:
            # 检查监控指标端点
            metrics_response = await self.http_client.get(
                f"{self.base_url}/api/v1/monitoring/metrics"
            )
            
            duration = time.time() - start_time
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                return ValidationResult(
                    "monitoring",
                    ValidationStatus.PASSED,
                    duration,
                    "监控功能正常"
                )
            else:
                return ValidationResult(
                    "monitoring",
                    ValidationStatus.WARNING,
                    duration,
                    f"监控端点返回状态码: {metrics_response.status_code}"
                )
        
        except Exception as e:
            return ValidationResult(
                "monitoring",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"监控功能验证失败: {str(e)}"
            )
    
    async def validate_performance(self) -> ValidationResult:
        """验证性能"""
        start_time = time.time()
        response_times = []
        
        try:
            # 执行多次请求测试性能
            for i in range(5):
                request_start = time.time()
                response = await self.http_client.get(f"{self.base_url}/health")
                request_duration = time.time() - request_start
                response_times.append(request_duration)
            
            duration = time.time() - start_time
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            if avg_response_time < 1.0:  # 平均响应时间小于1秒
                status = ValidationStatus.PASSED
                details = f"平均响应时间: {avg_response_time:.3f}s, 最大响应时间: {max_response_time:.3f}s"
            elif avg_response_time < 3.0:
                status = ValidationStatus.WARNING
                details = f"响应时间较慢: {avg_response_time:.3f}s, 最大响应时间: {max_response_time:.3f}s"
            else:
                status = ValidationStatus.FAILED
                details = f"响应时间过长: {avg_response_time:.3f}s, 最大响应时间: {max_response_time:.3f}s"
            
            return ValidationResult("performance", status, duration, details)
        
        except Exception as e:
            return ValidationResult(
                "performance",
                ValidationStatus.FAILED,
                time.time() - start_time,
                error=f"性能验证失败: {str(e)}"
            )
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证"""
        validation_methods = [
            self.validate_service_availability,
            self.validate_api_endpoints,
            self.validate_database_connectivity,
            self.validate_cache_functionality,
            self.validate_authentication,
            self.validate_monitoring,
            self.validate_performance
        ]
        
        # 执行所有验证
        for method in validation_methods:
            result = await method()
            self.results.append(result)
        
        # 计算总体验证结果
        overall_status = self._calculate_overall_status()
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "validations": [result.to_dict() for result in self.results]
        }
    
    def _calculate_overall_status(self) -> ValidationStatus:
        """计算总体验证状态"""
        if not self.results:
            return ValidationStatus.FAILED
        
        status_counts = {
            ValidationStatus.PASSED: 0,
            ValidationStatus.FAILED: 0,
            ValidationStatus.WARNING: 0,
            ValidationStatus.SKIPPED: 0
        }
        
        for result in self.results:
            status_counts[result.status] += 1
        
        if status_counts[ValidationStatus.FAILED] > 0:
            return ValidationStatus.FAILED
        elif status_counts[ValidationStatus.WARNING] > 0:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASSED
    
    def generate_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 70)
        report.append("AI Stack Super Enhanced 部署验证报告")
        report.append("=" * 70)
        report.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"目标地址: {self.base_url}")
        report.append("")
        
        # 总体状态
        overall_status = self._calculate_overall_status()
        status_emoji = {
            ValidationStatus.PASSED: "✅",
            ValidationStatus.WARNING: "⚠️",
            ValidationStatus.FAILED: "❌",
            ValidationStatus.SKIPPED: "⏭️"
        }
        
        report.append(f"总体状态: {status_emoji[overall_status]} {overall_status.value.upper()}")
        report.append("")
        
        # 详细验证结果
        report.append("详细验证结果:")
        report.append("-" * 70)
        
        for result in self.results:
            emoji = status_emoji[result.status]
            report.append(f"{emoji} {result.test_name:<25} {result.status.value:<8} {result.duration:.3f}s")
            if result.details:
                report.append(f"   详情: {result.details}")
            if result.error:
                report.append(f"   错误: {result.error}")
        
        report.append("")
        report.append("验证统计:")
        report.append("-" * 70)
        
        passed_count = len([r for r in self.results if r.status == ValidationStatus.PASSED])
        warning_count = len([r for r in self.results if r.status == ValidationStatus.WARNING])
        failed_count = len([r for r in self.results if r.status == ValidationStatus.FAILED])
        total_count = len(self.results)
        
        report.append(f"通过: {passed_count}/{total_count}")
        report.append(f"警告: {warning_count}/{total_count}")
        report.append(f"失败: {failed_count}/{total_count}")
        
        report.append("")
        report.append("状态说明:")
        report.append("✅ PASSED  - 验证通过")
        report.append("⚠️ WARNING - 验证警告（需要关注）")
        report.append("❌ FAILED  - 验证失败（需要修复）")
        report.append("=" * 70)
        
        return "\n".join(report)

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Stack Super Enhanced 部署验证')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='目标服务地址 (默认: http://localhost:8000)')
    parser.add_argument('--api-key', help='API密钥')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时时间 (默认: 30秒)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='输出格式 (默认: text)')
    
    args = parser.parse_args()
    
    # 创建验证器
    async with DeploymentValidator(args.url, args.api_key, args.timeout) as validator:
        # 运行验证
        print("开始部署验证...")
        results = await validator.run_all_validations()
        
        # 输出结果
        if args.output == 'json':
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            report = validator.generate_report()
            print(report)
        
        # 根据总体状态设置退出码
        overall_status = validator._calculate_overall_status()
        if overall_status == ValidationStatus.FAILED:
            sys.exit(1)
        elif overall_status == ValidationStatus.WARNING:
            sys.exit(2)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())