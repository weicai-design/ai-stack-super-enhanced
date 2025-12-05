#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2秒SLO性能验证脚本
验证所有API响应时间是否满足<2秒的服务水平目标
"""

from __future__ import annotations

import asyncio
import time
import statistics
import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import httpx

logger = logging.getLogger(__name__)


@dataclass
class SLOValidationResult:
    """SLO验证结果"""
    endpoint: str
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time: float  # 毫秒
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    slo_target: float = 2000.0  # 2秒目标
    slo_status: str = "unknown"  # pass, warning, fail
    slo_violations: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SLOValidator:
    """
    2秒SLO性能验证器
    
    功能：
    1. 验证单个API端点的2秒SLO
    2. 批量验证所有关键API端点
    3. 生成SLO验证报告
    4. 识别性能瓶颈
    """
    
    def __init__(self):
        """
        初始化SLO验证器
        """
        self.client = httpx.AsyncClient(timeout=10.0)  # 10秒超时
        self.results: List[SLOValidationResult] = []
        
        # 关键服务和端口映射
        self.services = {
            "超级Agent主界面": {
                "base_url": "http://localhost:8020",
                "endpoints": ["/", "/js/main.js", "/css/main.css", "/favicon.ico"]
            },
            "自我学习系统": {
                "base_url": "http://localhost:8019", 
                "endpoints": ["/health", "/api/health", "/api/status"]
            },
            "ERP前端": {
                "base_url": "http://localhost:8012",
                "endpoints": ["/", "/static/js/app.js", "/static/css/style.css"]
            }
        }
        
        # 构建完整的端点列表
        self.critical_endpoints = []
        for service_name, service_config in self.services.items():
            for endpoint in service_config["endpoints"]:
                self.critical_endpoints.append({
                    "service": service_name,
                    "base_url": service_config["base_url"],
                    "endpoint": endpoint
                })
        
        logger.info(f"SLO验证器初始化完成")
        logger.info(f"将验证 {len(self.critical_endpoints)} 个关键端点的2秒SLO")
        logger.info(f"服务列表: {list(self.services.keys())}")
    
    async def validate_endpoint_slo(
        self,
        endpoint_config: dict,
        test_iterations: int = 10,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
    ) -> SLOValidationResult:
        """
        验证单个API端点的2秒SLO
        
        Args:
            endpoint_config: 端点配置字典
            test_iterations: 测试迭代次数
            method: HTTP方法
            payload: 请求体
            
        Returns:
            SLO验证结果
        """
        service_name = endpoint_config["service"]
        base_url = endpoint_config["base_url"]
        endpoint = endpoint_config["endpoint"]
        
        test_name = f"slo_validation_{service_name}_{endpoint.replace('/', '_')}"
        logger.info(f"开始验证服务 {service_name} 端点SLO: {endpoint}")
        
        start_time = time.time()
        response_times: List[float] = []
        success_count = 0
        failure_count = 0
        slo_violations = 0
        errors: List[str] = []
        
        # 执行测试迭代
        for i in range(test_iterations):
            try:
                req_start = time.time()
                
                if method.upper() == "GET":
                    response = await self.client.get(f"{base_url}{endpoint}")
                elif method.upper() == "POST":
                    response = await self.client.post(f"{base_url}{endpoint}", json=payload)
                elif method.upper() == "PUT":
                    response = await self.client.put(f"{base_url}{endpoint}", json=payload)
                else:
                    response = await self.client.request(method, f"{base_url}{endpoint}", json=payload)
                
                req_time = (time.time() - req_start) * 1000  # 转换为毫秒
                response_times.append(req_time)
                
                # 检查是否违反SLO
                if req_time > 2000:  # 2秒SLO
                    slo_violations += 1
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"HTTP {response.status_code}: {response.text[:100]}")
                
                logger.debug(f"请求 {i+1}/{test_iterations}: {req_time:.2f}ms")
                
            except Exception as e:
                failure_count += 1
                errors.append(str(e)[:100])
                logger.warning(f"请求 {i+1}/{test_iterations} 失败: {e}")
            
            # 短暂延迟，避免服务器过载
            await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        total_requests = test_iterations
        
        # 计算SLO状态
        slo_status = self._calculate_slo_status(
            response_times=response_times,
            success_rate=success_count / total_requests if total_requests > 0 else 0.0,
            slo_violations=slo_violations,
            total_requests=total_requests,
        )
        
        # 计算性能指标
        metrics = self._calculate_metrics(
            endpoint=f"{service_name}:{endpoint}",
            test_name=test_name,
            response_times=response_times,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            slo_violations=slo_violations,
            duration=duration,
            errors=errors,
            slo_status=slo_status,
        )
        
        self.results.append(metrics)
        
        logger.info(f"SLO验证完成: {service_name}:{endpoint} - 状态: {slo_status}, "
                   f"平均响应时间: {metrics.avg_response_time:.2f}ms, "
                   f"SLO违规: {slo_violations}/{total_requests}")
        
        return metrics
    
    async def validate_all_endpoints(
        self,
        test_iterations: int = 5,
        concurrent_validation: bool = True,
    ) -> List[SLOValidationResult]:
        """
        验证所有关键API端点的2秒SLO
        
        Args:
            test_iterations: 每个端点的测试迭代次数
            concurrent_validation: 是否并发验证
            
        Returns:
            SLO验证结果列表
        """
        logger.info(f"开始验证所有 {len(self.critical_endpoints)} 个关键API端点的2秒SLO")
        
        if concurrent_validation:
            # 并发验证所有端点
            tasks = []
            for endpoint_config in self.critical_endpoints:
                task = self.validate_endpoint_slo(
                    endpoint_config=endpoint_config,
                    test_iterations=test_iterations,
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤异常结果
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, SLOValidationResult):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    endpoint_config = self.critical_endpoints[i]
                    logger.error(f"端点 {endpoint_config['service']}:{endpoint_config['endpoint']} 验证失败: {result}")
            
            return valid_results
        else:
            # 顺序验证所有端点
            results = []
            for endpoint_config in self.critical_endpoints:
                try:
                    result = await self.validate_endpoint_slo(
                        endpoint_config=endpoint_config,
                        test_iterations=test_iterations,
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"端点 {endpoint_config['service']}:{endpoint_config['endpoint']} 验证失败: {e}")
            
            return results
    
    def _calculate_slo_status(
        self,
        response_times: List[float],
        success_rate: float,
        slo_violations: int,
        total_requests: int,
    ) -> str:
        """计算SLO状态"""
        if not response_times:
            return "fail"
        
        # 成功率必须≥95%
        if success_rate < 0.95:
            return "fail"
        
        # SLO违规率必须≤5%
        violation_rate = slo_violations / total_requests if total_requests > 0 else 1.0
        
        if violation_rate <= 0.05:  # ≤5%违规率
            return "pass"
        elif violation_rate <= 0.10:  # ≤10%违规率
            return "warning"
        else:
            return "fail"
    
    def _calculate_metrics(
        self,
        endpoint: str,
        test_name: str,
        response_times: List[float],
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        slo_violations: int,
        duration: float,
        errors: List[str],
        slo_status: str,
    ) -> SLOValidationResult:
        """计算性能指标"""
        if not response_times:
            return SLOValidationResult(
                endpoint=endpoint,
                test_name=test_name,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=0.0,
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                slo_status=slo_status,
                slo_violations=slo_violations,
                errors=errors,
            )
        
        sorted_times = sorted(response_times)
        
        return SLOValidationResult(
            endpoint=endpoint,
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=(successful_requests / total_requests * 100) if total_requests > 0 else 0.0,
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0.0,
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0.0,
            slo_status=slo_status,
            slo_violations=slo_violations,
            errors=errors[:10],  # 只保留前10个错误
        )
    
    def generate_slo_report(self) -> Dict[str, Any]:
        """生成SLO验证报告"""
        if not self.results:
            return {"error": "没有验证结果"}
        
        # 统计总体SLO状态
        total_endpoints = len(self.results)
        passed_endpoints = len([r for r in self.results if r.slo_status == "pass"])
        warning_endpoints = len([r for r in self.results if r.slo_status == "warning"])
        failed_endpoints = len([r for r in self.results if r.slo_status == "fail"])
        
        # 计算平均响应时间
        avg_response_times = [r.avg_response_time for r in self.results if r.avg_response_time > 0]
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0.0
        
        # 识别性能瓶颈
        slow_endpoints = [r for r in self.results if r.avg_response_time > 1000]  # >1秒
        critical_endpoints = [r for r in self.results if r.avg_response_time > 1500]  # >1.5秒
        
        return {
            "slo_validation_report": {
                "timestamp": datetime.utcnow().isoformat(),
                "slo_target": "2秒",
                "total_endpoints_tested": total_endpoints,
                "overall_status": "pass" if failed_endpoints == 0 else "fail",
                "endpoint_status_summary": {
                    "passed": passed_endpoints,
                    "warning": warning_endpoints,
                    "failed": failed_endpoints,
                    "pass_rate": f"{passed_endpoints/total_endpoints*100:.1f}%" if total_endpoints > 0 else "0%",
                },
                "performance_summary": {
                    "overall_avg_response_time_ms": overall_avg_response_time,
                    "slo_compliance_rate": f"{(total_endpoints - failed_endpoints)/total_endpoints*100:.1f}%" if total_endpoints > 0 else "0%",
                    "slow_endpoints_count": len(slow_endpoints),
                    "critical_endpoints_count": len(critical_endpoints),
                },
                "detailed_results": [r.to_dict() for r in self.results],
                "recommendations": self._generate_recommendations(),
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 分析失败端点
        failed_endpoints = [r for r in self.results if r.slo_status == "fail"]
        slow_endpoints = [r for r in self.results if r.avg_response_time > 1000]
        
        if failed_endpoints:
            recommendations.append(f"发现 {len(failed_endpoints)} 个端点违反2秒SLO，需要优先优化")
        
        if slow_endpoints:
            slowest = max(slow_endpoints, key=lambda x: x.avg_response_time)
            recommendations.append(f"最慢端点: {slowest.endpoint} ({slowest.avg_response_time:.2f}ms)")
        
        # 通用优化建议
        recommendations.extend([
            "建议启用缓存机制减少重复计算",
            "建议优化数据库查询性能",
            "建议使用异步处理提高并发能力",
            "建议监控API调用链识别瓶颈",
        ])
        
        return recommendations
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


async def main():
    """主函数 - 执行2秒SLO验证"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    validator = SLOValidator()
    
    try:
        # 验证所有关键API端点的2秒SLO
        results = await validator.validate_all_endpoints(test_iterations=5)
        
        # 生成SLO验证报告
        report = validator.generate_slo_report()
        
        # 输出报告
        print("\n" + "="*80)
        print("2秒SLO性能验证报告")
        print("="*80)
        
        summary = report["slo_validation_report"]
        print(f"验证时间: {summary['timestamp']}")
        print(f"SLO目标: {summary['slo_target']}")
        print(f"测试端点总数: {summary['total_endpoints_tested']}")
        print(f"总体状态: {summary['overall_status']}")
        
        status_summary = summary['endpoint_status_summary']
        print(f"通过端点: {status_summary['passed']} ({status_summary['pass_rate']})")
        print(f"警告端点: {status_summary['warning']}")
        print(f"失败端点: {status_summary['failed']}")
        
        perf_summary = summary['performance_summary']
        print(f"平均响应时间: {perf_summary['overall_avg_response_time_ms']:.2f}ms")
        print(f"SLO合规率: {perf_summary['slo_compliance_rate']}")
        
        # 输出详细结果
        print("\n详细结果:")
        for result in results:
            status_icon = "✅" if result.slo_status == "pass" else "⚠️" if result.slo_status == "warning" else "❌"
            print(f"{status_icon} {result.endpoint:<40} {result.avg_response_time:>6.1f}ms {result.slo_status}")
        
        # 输出建议
        print("\n优化建议:")
        for rec in summary['recommendations']:
            print(f"• {rec}")
        
        # 保存报告到文件
        report_file = f"slo_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        # 返回验证结果
        return summary['overall_status'] == 'pass'
        
    except Exception as e:
        logger.error(f"SLO验证失败: {e}")
        return False
    finally:
        await validator.close()


if __name__ == "__main__":
    # 运行SLO验证
    success = asyncio.run(main())
    
    # 根据验证结果退出
    exit(0 if success else 1)