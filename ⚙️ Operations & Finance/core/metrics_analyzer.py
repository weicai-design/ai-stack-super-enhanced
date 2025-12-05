"""
指标分析监控系统
提供专家性能指标分析和可视化
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
from collections import defaultdict
import json

from core.structured_logging import get_logger, trace_operation
from core.monitoring_system import ExpertMonitor, ExpertMetric


@dataclass
class PerformanceAnalysis:
    """性能分析结果"""
    expert_name: str
    period: str  # "1h", "24h", "7d"
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    error_rate: float
    throughput: float
    trend: str  # "improving", "stable", "degrading"
    recommendations: List[str]


@dataclass
class ComparativeAnalysis:
    """对比分析结果"""
    experts: List[str]
    comparison_period: str
    metrics_comparison: Dict[str, Dict[str, float]]
    rankings: Dict[str, List[str]]
    insights: List[str]


class MetricsAnalyzer:
    """指标分析器"""
    
    def __init__(self, monitor: ExpertMonitor):
        self.monitor = monitor
        self.logger = get_logger("metrics_analyzer")
    
    def filter_metrics_by_time(self, metrics: List[ExpertMetric], hours: int) -> List[ExpertMetric]:
        """按时间过滤指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in metrics if m.timestamp >= cutoff_time]
    
    def analyze_performance(self, expert_name: str, period_hours: int = 24) -> PerformanceAnalysis:
        """分析专家性能"""
        with trace_operation("analyze_performance") as trace:
            try:
                self.logger.info(
                    "开始性能分析",
                    expert_name=expert_name,
                    period_hours=period_hours
                )
                
                # 获取相关指标
                response_times = []
                success_counts = 0
                error_counts = 0
                request_counts = 0
                
                # 响应时间指标
                response_metrics = self.monitor.metrics.get(f"{expert_name}:response_time", [])
                filtered_response = self.filter_metrics_by_time(response_metrics, period_hours)
                response_times = [m.value for m in filtered_response]
                
                # 成功/失败指标
                success_metrics = self.monitor.metrics.get(f"{expert_name}:success_count", [])
                filtered_success = self.filter_metrics_by_time(success_metrics, period_hours)
                success_counts = len(filtered_success)
                
                error_metrics = self.monitor.metrics.get(f"{expert_name}:error_count", [])
                filtered_errors = self.filter_metrics_by_time(error_metrics, period_hours)
                error_counts = len(filtered_errors)
                
                request_metrics = self.monitor.metrics.get(f"{expert_name}:request_count", [])
                filtered_requests = self.filter_metrics_by_time(request_metrics, period_hours)
                request_counts = len(filtered_requests)
                
                # 计算性能指标
                avg_response_time = statistics.mean(response_times) if response_times else 0
                p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else avg_response_time
                p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else avg_response_time
                
                total_requests = success_counts + error_counts
                success_rate = success_counts / total_requests if total_requests > 0 else 1.0
                error_rate = 1 - success_rate
                
                throughput = request_counts / (period_hours * 60)  # 请求/分钟
                
                # 分析趋势
                trend = self._analyze_trend(expert_name, period_hours)
                
                # 生成建议
                recommendations = self._generate_recommendations(
                    expert_name, avg_response_time, success_rate, throughput
                )
                
                # 确定时间段标签
                period_map = {1: "1h", 24: "24h", 168: "7d"}
                period_label = period_map.get(period_hours, f"{period_hours}h")
                
                analysis = PerformanceAnalysis(
                    expert_name=expert_name,
                    period=period_label,
                    avg_response_time=avg_response_time,
                    p95_response_time=p95_response_time,
                    p99_response_time=p99_response_time,
                    success_rate=success_rate,
                    error_rate=error_rate,
                    throughput=throughput,
                    trend=trend,
                    recommendations=recommendations
                )
                
                self.logger.info("性能分析完成", expert_name=expert_name)
                
                return analysis
                
            except Exception as e:
                self.logger.error("性能分析失败", expert_name=expert_name, error=str(e))
                raise
    
    def _analyze_trend(self, expert_name: str, period_hours: int) -> str:
        """分析性能趋势"""
        # 简化的趋势分析：比较前半段和后半段的性能
        if period_hours < 2:
            return "stable"  # 时间段太短，无法分析趋势
        
        # 获取前半段和后半段的响应时间
        response_metrics = self.monitor.metrics.get(f"{expert_name}:response_time", [])
        
        if len(response_metrics) < 10:
            return "stable"  # 数据不足
        
        # 分割时间段
        midpoint_time = datetime.now() - timedelta(hours=period_hours / 2)
        
        first_half = [m.value for m in response_metrics if m.timestamp < midpoint_time]
        second_half = [m.value for m in response_metrics if m.timestamp >= midpoint_time]
        
        if not first_half or not second_half:
            return "stable"
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        # 判断趋势
        if avg_second < avg_first * 0.9:  # 改善超过10%
            return "improving"
        elif avg_second > avg_first * 1.1:  # 恶化超过10%
            return "degrading"
        else:
            return "stable"
    
    def _generate_recommendations(self, expert_name: str, response_time: float, 
                                success_rate: float, throughput: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 响应时间建议
        if response_time > 3.0:
            recommendations.append(f"专家 {expert_name} 响应时间较长({response_time:.2f}s)，建议优化算法或增加缓存")
        elif response_time > 1.0:
            recommendations.append(f"专家 {expert_name} 响应时间适中({response_time:.2f}s)，可考虑进一步优化")
        
        # 成功率建议
        if success_rate < 0.95:
            recommendations.append(f"专家 {expert_name} 成功率较低({success_rate:.1%})，建议检查错误处理和稳定性")
        
        # 吞吐量建议
        if throughput < 0.1:
            recommendations.append(f"专家 {expert_name} 使用率较低({throughput:.2f} req/min)，可考虑推广使用")
        elif throughput > 10.0:
            recommendations.append(f"专家 {expert_name} 使用率较高({throughput:.2f} req/min)，建议优化性能或增加资源")
        
        if not recommendations:
            recommendations.append(f"专家 {expert_name} 性能良好，继续保持")
        
        return recommendations
    
    def compare_experts(self, expert_names: List[str], period_hours: int = 24) -> ComparativeAnalysis:
        """对比多个专家的性能"""
        with trace_operation("compare_experts") as trace:
            try:
                self.logger.info(
                    "开始专家对比分析",
                    expert_count=len(expert_names),
                    period_hours=period_hours
                )
                
                metrics_comparison = {}
                rankings = {
                    "response_time": [],
                    "success_rate": [],
                    "throughput": []
                }
                
                # 分析每个专家的性能
                expert_performances = {}
                for expert_name in expert_names:
                    performance = self.analyze_performance(expert_name, period_hours)
                    expert_performances[expert_name] = performance
                    
                    metrics_comparison[expert_name] = {
                        "avg_response_time": performance.avg_response_time,
                        "success_rate": performance.success_rate,
                        "throughput": performance.throughput
                    }
                
                # 生成排名
                # 响应时间排名（越低越好）
                response_times = [(name, perf.avg_response_time) for name, perf in expert_performances.items()]
                response_times.sort(key=lambda x: x[1])
                rankings["response_time"] = [name for name, _ in response_times]
                
                # 成功率排名（越高越好）
                success_rates = [(name, perf.success_rate) for name, perf in expert_performances.items()]
                success_rates.sort(key=lambda x: x[1], reverse=True)
                rankings["success_rate"] = [name for name, _ in success_rates]
                
                # 吞吐量排名（越高越好）
                throughputs = [(name, perf.throughput) for name, perf in expert_performances.items()]
                throughputs.sort(key=lambda x: x[1], reverse=True)
                rankings["throughput"] = [name for name, _ in throughputs]
                
                # 生成洞察
                insights = self._generate_insights(expert_performances, rankings)
                
                # 确定时间段标签
                period_map = {1: "1h", 24: "24h", 168: "7d"}
                period_label = period_map.get(period_hours, f"{period_hours}h")
                
                analysis = ComparativeAnalysis(
                    experts=expert_names,
                    comparison_period=period_label,
                    metrics_comparison=metrics_comparison,
                    rankings=rankings,
                    insights=insights
                )
                
                self.logger.info("专家对比分析完成", expert_count=len(expert_names))
                
                return analysis
                
            except Exception as e:
                self.logger.error("专家对比分析失败", error=str(e))
                raise
    
    def _generate_insights(self, expert_performances: Dict[str, PerformanceAnalysis], 
                          rankings: Dict[str, List[str]]) -> List[str]:
        """生成洞察信息"""
        insights = []
        
        # 找出性能最好的专家
        best_response = rankings["response_time"][0] if rankings["response_time"] else None
        best_success = rankings["success_rate"][0] if rankings["success_rate"] else None
        best_throughput = rankings["throughput"][0] if rankings["throughput"] else None
        
        if best_response:
            insights.append(f"专家 {best_response} 响应时间最快")
        
        if best_success:
            insights.append(f"专家 {best_success} 成功率最高")
        
        if best_throughput:
            insights.append(f"专家 {best_throughput} 使用率最高")
        
        # 找出需要关注的专家
        for expert_name, performance in expert_performances.items():
            if performance.success_rate < 0.9:
                insights.append(f"专家 {expert_name} 成功率较低({performance.success_rate:.1%})，需要关注")
            
            if performance.avg_response_time > 2.0:
                insights.append(f"专家 {expert_name} 响应时间较慢({performance.avg_response_time:.2f}s)，建议优化")
        
        return insights
    
    def get_performance_history(self, expert_name: str, metric_type: str, 
                              hours: int = 24, interval_minutes: int = 30) -> Dict[str, Any]:
        """获取性能历史数据"""
        with trace_operation("get_performance_history") as trace:
            try:
                self.logger.info(
                    "获取性能历史数据",
                    expert_name=expert_name,
                    metric_type=metric_type,
                    hours=hours
                )
                
                key = f"{expert_name}:{metric_type}"
                metrics = self.monitor.metrics.get(key, [])
                
                # 按时间间隔聚合数据
                interval_seconds = interval_minutes * 60
                now = datetime.now()
                start_time = now - timedelta(hours=hours)
                
                # 创建时间桶
                time_buckets = {}
                current_time = start_time.replace(second=0, microsecond=0)
                while current_time <= now:
                    time_buckets[current_time] = []
                    current_time += timedelta(minutes=interval_minutes)
                
                # 分配指标到时间桶
                for metric in metrics:
                    if metric.timestamp < start_time:
                        continue
                    
                    # 找到对应的时间桶
                    bucket_time = metric.timestamp.replace(second=0, microsecond=0)
                    bucket_time = bucket_time - timedelta(minutes=bucket_time.minute % interval_minutes)
                    
                    if bucket_time in time_buckets:
                        time_buckets[bucket_time].append(metric.value)
                
                # 计算每个时间桶的统计值
                history_data = []
                for bucket_time, values in sorted(time_buckets.items()):
                    if values:
                        avg_value = statistics.mean(values)
                        min_value = min(values)
                        max_value = max(values)
                    else:
                        avg_value = min_value = max_value = 0
                    
                    history_data.append({
                        "timestamp": bucket_time.isoformat(),
                        "avg": avg_value,
                        "min": min_value,
                        "max": max_value,
                        "count": len(values)
                    })
                
                result = {
                    "success": True,
                    "expert_name": expert_name,
                    "metric_type": metric_type,
                    "history": history_data,
                    "trace_id": trace.request_id
                }
                
                self.logger.info("性能历史数据获取完成", data_points=len(history_data))
                
                return result
                
            except Exception as e:
                self.logger.error("获取性能历史数据失败", error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "trace_id": trace.request_id
                }


class MetricsAPI:
    """指标分析API"""
    
    def __init__(self, analyzer: MetricsAnalyzer):
        self.analyzer = analyzer
        self.logger = get_logger("metrics_api")
    
    def analyze_expert_performance(self, expert_name: str, period: str = "24h") -> Dict[str, Any]:
        """分析专家性能"""
        period_map = {"1h": 1, "24h": 24, "7d": 168}
        period_hours = period_map.get(period, 24)
        
        try:
            analysis = self.analyzer.analyze_performance(expert_name, period_hours)
            
            return {
                "success": True,
                "analysis": {
                    "expert_name": analysis.expert_name,
                    "period": analysis.period,
                    "avg_response_time": analysis.avg_response_time,
                    "p95_response_time": analysis.p95_response_time,
                    "p99_response_time": analysis.p99_response_time,
                    "success_rate": analysis.success_rate,
                    "error_rate": analysis.error_rate,
                    "throughput": analysis.throughput,
                    "trend": analysis.trend,
                    "recommendations": analysis.recommendations
                }
            }
        except Exception as e:
            self.logger.error("分析专家性能失败", expert_name=expert_name, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_experts_performance(self, expert_names: List[str], period: str = "24h") -> Dict[str, Any]:
        """对比专家性能"""
        period_map = {"1h": 1, "24h": 24, "7d": 168}
        period_hours = period_map.get(period, 24)
        
        try:
            analysis = self.analyzer.compare_experts(expert_names, period_hours)
            
            return {
                "success": True,
                "comparison": {
                    "experts": analysis.experts,
                    "comparison_period": analysis.comparison_period,
                    "metrics_comparison": analysis.metrics_comparison,
                    "rankings": analysis.rankings,
                    "insights": analysis.insights
                }
            }
        except Exception as e:
            self.logger.error("对比专家性能失败", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_performance_history(self, expert_name: str, metric_type: str, 
                              period: str = "24h", interval: str = "30m") -> Dict[str, Any]:
        """获取性能历史数据"""
        period_map = {"1h": 1, "24h": 24, "7d": 168}
        interval_map = {"5m": 5, "30m": 30, "1h": 60}
        
        period_hours = period_map.get(period, 24)
        interval_minutes = interval_map.get(interval, 30)
        
        return self.analyzer.get_performance_history(expert_name, metric_type, period_hours, interval_minutes)


# 全局分析器实例
def get_global_monitor():
    """获取全局监控器实例"""
    from core.monitoring_system import ExpertMonitor
    return ExpertMonitor()

global_analyzer = MetricsAnalyzer(get_global_monitor())
metrics_api = MetricsAPI(global_analyzer)


def get_global_analyzer() -> MetricsAnalyzer:
    """获取全局分析器实例"""
    return global_analyzer


def get_metrics_api() -> MetricsAPI:
    """获取指标API实例"""
    return metrics_api


if __name__ == "__main__":
    # 测试指标分析系统
    from core.monitoring_system import ExpertMonitor
    
    async def test_metrics_analyzer():
        monitor = ExpertMonitor()
        analyzer = MetricsAnalyzer(monitor)
        
        # 添加一些测试数据
        for i in range(100):
            monitor.record_request("data_analyzer", 0.5 + i * 0.01, True)
            monitor.record_request("price_analyzer", 1.0 + i * 0.02, i % 10 != 0)  # 10%错误率
        
        # 分析性能
        analysis = analyzer.analyze_performance("data_analyzer", 24)
        print(f"Data Analyzer Performance: {analysis}")
        
        # 对比专家
        comparison = analyzer.compare_experts(["data_analyzer", "price_analyzer"], 24)
        print(f"Expert Comparison: {comparison}")
        
        # 获取历史数据
        history = analyzer.get_performance_history("data_analyzer", "response_time", 24, 60)
        print(f"Performance History: {len(history['history'])} data points")
    
    asyncio.run(test_metrics_analyzer())