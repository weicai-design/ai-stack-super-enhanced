#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2 秒 SLO 性能实测报告生成器
P3-015 开发任务：向量索引优化、流式/SSR、上下文压缩实测
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import time
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    target: Optional[float] = None
    status: str = "unknown"  # pass, fail, warning


@dataclass
class VectorIndexBenchmark:
    """向量索引性能基准测试"""
    index_type: str  # FastVectorIndex, OptimizedFaissVectorStore, HybridVectorStore
    document_count: int
    query_count: int
    avg_query_time_ms: float
    p50_query_time_ms: float
    p95_query_time_ms: float
    p99_query_time_ms: float
    throughput_qps: float
    memory_usage_mb: float
    cache_hit_rate: Optional[float] = None


@dataclass
class StreamingBenchmark:
    """流式响应性能基准测试"""
    response_type: str  # SSE, chunked, websocket
    message_length: int
    chunk_size: int
    time_to_first_byte_ms: float
    total_response_time_ms: float
    throughput_mbps: float
    client_perceived_latency_ms: float


@dataclass
class ContextCompressionBenchmark:
    """上下文压缩性能基准测试"""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    compression_time_ms: float
    quality_score: float  # 0-1, 压缩后质量评分
    method: str  # summarization, truncation, extraction


class SLOPerformanceReporter:
    """
    2 秒 SLO 性能实测报告生成器
    """
    
    def __init__(self):
        """初始化性能报告器"""
        self.vector_index_benchmarks: List[VectorIndexBenchmark] = []
        self.streaming_benchmarks: List[StreamingBenchmark] = []
        self.context_compression_benchmarks: List[ContextCompressionBenchmark] = []
        self.slo_target_ms = 2000  # 2秒SLO目标
    
    def record_vector_index_benchmark(self, benchmark: VectorIndexBenchmark):
        """记录向量索引性能基准测试"""
        self.vector_index_benchmarks.append(benchmark)
        logger.info(f"向量索引基准测试已记录: {benchmark.index_type}, 平均查询时间: {benchmark.avg_query_time_ms}ms")
    
    def record_streaming_benchmark(self, benchmark: StreamingBenchmark):
        """记录流式响应性能基准测试"""
        self.streaming_benchmarks.append(benchmark)
        logger.info(f"流式响应基准测试已记录: {benchmark.response_type}, TTFB: {benchmark.time_to_first_byte_ms}ms")
    
    def record_context_compression_benchmark(self, benchmark: ContextCompressionBenchmark):
        """记录上下文压缩性能基准测试"""
        self.context_compression_benchmarks.append(benchmark)
        logger.info(f"上下文压缩基准测试已记录: {benchmark.method}, 压缩比: {benchmark.compression_ratio:.2f}")
    
    def generate_vector_index_report(self) -> Dict[str, Any]:
        """生成向量索引优化报告"""
        if not self.vector_index_benchmarks:
            return {
                "status": "no_data",
                "message": "暂无向量索引基准测试数据"
            }
        
        # 按索引类型分组
        by_type: Dict[str, List[VectorIndexBenchmark]] = {}
        for bench in self.vector_index_benchmarks:
            by_type.setdefault(bench.index_type, []).append(bench)
        
        # 计算统计信息
        reports = {}
        for index_type, benches in by_type.items():
            avg_query_times = [b.avg_query_time_ms for b in benches]
            avg_avg = sum(avg_query_times) / len(avg_query_times) if avg_query_times else 0
            
            reports[index_type] = {
                "avg_query_time_ms": avg_avg,
                "min_query_time_ms": min(avg_query_times) if avg_query_times else 0,
                "max_query_time_ms": max(avg_query_times) if avg_query_times else 0,
                "p95_query_time_ms": sorted(avg_query_times)[int(len(avg_query_times) * 0.95)] if avg_query_times else 0,
                "avg_throughput_qps": sum(b.throughput_qps for b in benches) / len(benches) if benches else 0,
                "avg_memory_usage_mb": sum(b.memory_usage_mb for b in benches) / len(benches) if benches else 0,
                "test_count": len(benches)
            }
        
        # 找出最优索引类型
        best_type = min(
            reports.items(),
            key=lambda x: x[1]["avg_query_time_ms"]
        )[0] if reports else None
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.vector_index_benchmarks),
                "index_types_tested": list(by_type.keys()),
                "best_index_type": best_type,
                "best_avg_query_time_ms": reports[best_type]["avg_query_time_ms"] if best_type and best_type in reports else None
            },
            "detailed_results": reports,
            "recommendations": self._generate_vector_index_recommendations(reports, best_type)
        }
    
    def generate_streaming_report(self) -> Dict[str, Any]:
        """生成流式/SSR性能报告"""
        if not self.streaming_benchmarks:
            return {
                "status": "no_data",
                "message": "暂无流式响应基准测试数据"
            }
        
        # 按响应类型分组
        by_type: Dict[str, List[StreamingBenchmark]] = {}
        for bench in self.streaming_benchmarks:
            by_type.setdefault(bench.response_type, []).append(bench)
        
        reports = {}
        for response_type, benches in by_type.items():
            ttfb_times = [b.time_to_first_byte_ms for b in benches]
            total_times = [b.total_response_time_ms for b in benches]
            
            reports[response_type] = {
                "avg_ttfb_ms": sum(ttfb_times) / len(ttfb_times) if ttfb_times else 0,
                "min_ttfb_ms": min(ttfb_times) if ttfb_times else 0,
                "max_ttfb_ms": max(ttfb_times) if ttfb_times else 0,
                "avg_total_time_ms": sum(total_times) / len(total_times) if total_times else 0,
                "avg_throughput_mbps": sum(b.throughput_mbps for b in benches) / len(benches) if benches else 0,
                "avg_client_perceived_latency_ms": sum(b.client_perceived_latency_ms for b in benches) / len(benches) if benches else 0,
                "test_count": len(benches)
            }
        
        # 找出最优响应类型
        best_type = min(
            reports.items(),
            key=lambda x: x[1]["avg_ttfb_ms"]
        )[0] if reports else None
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.streaming_benchmarks),
                "response_types_tested": list(by_type.keys()),
                "best_response_type": best_type,
                "best_ttfb_ms": reports[best_type]["avg_ttfb_ms"] if best_type and best_type in reports else None
            },
            "detailed_results": reports,
            "slo_compliance": {
                "target_ttfb_ms": 500,  # 目标：500ms内首字节
                "target_total_ms": self.slo_target_ms,
                "compliance_rate": self._calculate_slo_compliance(reports)
            },
            "recommendations": self._generate_streaming_recommendations(reports, best_type)
        }
    
    def generate_context_compression_report(self) -> Dict[str, Any]:
        """生成上下文压缩性能报告"""
        if not self.context_compression_benchmarks:
            return {
                "status": "no_data",
                "message": "暂无上下文压缩基准测试数据"
            }
        
        # 按压缩方法分组
        by_method: Dict[str, List[ContextCompressionBenchmark]] = {}
        for bench in self.context_compression_benchmarks:
            by_method.setdefault(bench.method, []).append(bench)
        
        reports = {}
        for method, benches in by_method.items():
            compression_ratios = [b.compression_ratio for b in benches]
            quality_scores = [b.quality_score for b in benches]
            compression_times = [b.compression_time_ms for b in benches]
            
            reports[method] = {
                "avg_compression_ratio": sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0,
                "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "avg_compression_time_ms": sum(compression_times) / len(compression_times) if compression_times else 0,
                "avg_token_reduction": sum(b.original_tokens - b.compressed_tokens for b in benches) / len(benches) if benches else 0,
                "test_count": len(benches)
            }
        
        # 找出最优压缩方法（平衡压缩比和质量）
        best_method = max(
            reports.items(),
            key=lambda x: x[1]["avg_compression_ratio"] * x[1]["avg_quality_score"]
        )[0] if reports else None
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.context_compression_benchmarks),
                "methods_tested": list(by_method.keys()),
                "best_method": best_method,
                "best_compression_ratio": reports[best_method]["avg_compression_ratio"] if best_method and best_method in reports else None,
                "best_quality_score": reports[best_method]["avg_quality_score"] if best_method and best_method in reports else None
            },
            "detailed_results": reports,
            "recommendations": self._generate_compression_recommendations(reports, best_method)
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合性能报告"""
        vector_report = self.generate_vector_index_report()
        streaming_report = self.generate_streaming_report()
        compression_report = self.generate_context_compression_report()
        
        # 计算总体SLO达成率
        slo_metrics = []
        
        if vector_report.get("status") == "success":
            best_vector_time = vector_report["summary"].get("best_avg_query_time_ms", 0)
            if best_vector_time > 0:
                slo_metrics.append({
                    "name": "向量索引查询",
                    "value_ms": best_vector_time,
                    "target_ms": 100,  # 目标：100ms内
                    "status": "pass" if best_vector_time <= 100 else "fail"
                })
        
        if streaming_report.get("status") == "success":
            best_ttfb = streaming_report["summary"].get("best_ttfb_ms", 0)
            if best_ttfb > 0:
                slo_metrics.append({
                    "name": "流式响应首字节",
                    "value_ms": best_ttfb,
                    "target_ms": 500,  # 目标：500ms内
                    "status": "pass" if best_ttfb <= 500 else "fail"
                })
        
        if compression_report.get("status") == "success":
            best_compression_time = compression_report["detailed_results"].get(
                compression_report["summary"].get("best_method", ""),
                {}
            ).get("avg_compression_time_ms", 0)
            if best_compression_time > 0:
                slo_metrics.append({
                    "name": "上下文压缩",
                    "value_ms": best_compression_time,
                    "target_ms": 200,  # 目标：200ms内
                    "status": "pass" if best_compression_time <= 200 else "fail"
                })
        
        overall_slo_rate = sum(1 for m in slo_metrics if m["status"] == "pass") / len(slo_metrics) * 100 if slo_metrics else 0
        
        return {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "slo_target_ms": self.slo_target_ms,
            "overall_slo_compliance_rate": overall_slo_rate,
            "slo_metrics": slo_metrics,
            "vector_index_report": vector_report,
            "streaming_report": streaming_report,
            "context_compression_report": compression_report,
            "recommendations": {
                "priority": "high" if overall_slo_rate < 80 else "medium" if overall_slo_rate < 95 else "low",
                "actions": self._generate_overall_recommendations(slo_metrics, overall_slo_rate)
            }
        }
    
    def _generate_vector_index_recommendations(self, reports: Dict[str, Any], best_type: Optional[str]) -> List[str]:
        """生成向量索引优化建议"""
        recommendations = []
        
        if best_type:
            recommendations.append(f"推荐使用 {best_type} 作为主要向量索引实现")
        
        # 检查是否需要优化
        if reports:
            avg_times = [r["avg_query_time_ms"] for r in reports.values()]
            if max(avg_times) > 100:
                recommendations.append("考虑启用查询缓存以提升性能")
            if max(avg_times) > 200:
                recommendations.append("考虑使用HNSW索引替代Flat索引以提升大规模数据查询性能")
        
        return recommendations
    
    def _generate_streaming_recommendations(self, reports: Dict[str, Any], best_type: Optional[str]) -> List[str]:
        """生成流式响应优化建议"""
        recommendations = []
        
        if best_type:
            recommendations.append(f"推荐使用 {best_type} 作为主要流式响应方式")
        
        if reports:
            for response_type, data in reports.items():
                if data["avg_ttfb_ms"] > 500:
                    recommendations.append(f"{response_type} 的首字节时间超过目标，建议优化")
        
        return recommendations
    
    def _generate_compression_recommendations(self, reports: Dict[str, Any], best_method: Optional[str]) -> List[str]:
        """生成上下文压缩优化建议"""
        recommendations = []
        
        if best_method:
            recommendations.append(f"推荐使用 {best_method} 作为主要上下文压缩方法")
        
        if reports:
            for method, data in reports.items():
                if data["avg_quality_score"] < 0.8:
                    recommendations.append(f"{method} 的压缩质量较低，建议调整压缩策略")
        
        return recommendations
    
    def _calculate_slo_compliance(self, reports: Dict[str, Any]) -> float:
        """计算SLO达成率"""
        if not reports:
            return 0.0
        
        total_tests = sum(r["test_count"] for r in reports.values())
        if total_tests == 0:
            return 0.0
        
        # 简化计算：基于TTFB和总响应时间
        compliant_tests = 0
        for data in reports.values():
            if data["avg_ttfb_ms"] <= 500 and data["avg_total_time_ms"] <= self.slo_target_ms:
                compliant_tests += data["test_count"]
        
        return (compliant_tests / total_tests * 100) if total_tests > 0 else 0.0
    
    def _generate_overall_recommendations(self, slo_metrics: List[Dict[str, Any]], overall_rate: float) -> List[str]:
        """生成总体优化建议"""
        recommendations = []
        
        if overall_rate < 80:
            recommendations.append("⚠️ SLO达成率低于80%，需要立即优化")
        elif overall_rate < 95:
            recommendations.append("⚠️ SLO达成率低于95%，建议优化")
        else:
            recommendations.append("✅ SLO达成率良好，继续保持")
        
        # 针对失败的指标给出具体建议
        for metric in slo_metrics:
            if metric["status"] == "fail":
                recommendations.append(f"需要优化 {metric['name']}，当前 {metric['value_ms']}ms 超过目标 {metric['target_ms']}ms")
        
        return recommendations


# 全局实例
slo_performance_reporter = SLOPerformanceReporter()

