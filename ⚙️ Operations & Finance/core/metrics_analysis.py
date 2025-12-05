"""
指标分析监控系统 - 生产级实现
提供专家性能指标分析、对比和历史数据功能
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json

# 导入结构化日志模块
try:
    from .structured_logging import get_logger, trace_operation, get_performance_monitor
except ImportError:
    # 回退到本地实现
    import logging
    from datetime import datetime
    from typing import Dict, Any
    
    class PerformanceMonitor:
        def __init__(self):
            self.total_calls = 0
            
        def record_performance(self, name: str, value: float, tags: Dict[str, str] = None):
            self.total_calls += 1
            
        def get_stats(self):
            return {"total_calls": self.total_calls}
    
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_performance_monitor():
        return PerformanceMonitor()
    
    def trace_operation(name: str):
        class DummyTrace:
            def __init__(self, name):
                self.name = name
                self.request_id = "dummy_request_id"
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return DummyTrace(name)
    


# 导入监控系统模块
from monitoring_system import ExpertMonitor, ExpertMetric, ExpertStatus, MetricType, AlertSeverity


class AnalysisPeriod(Enum):
    """分析周期枚举"""
    REAL_TIME = "real_time"  # 实时分析
    HOUR = "hour"           # 小时分析
    DAY = "day"             # 日分析
    WEEK = "week"           # 周分析
    MONTH = "month"         # 月分析


class TrendDirection(Enum):
    """趋势方向枚举"""
    IMPROVING = "improving"      # 改善
    STABLE = "stable"           # 稳定
    DEGRADING = "degrading"     # 恶化
    UNKNOWN = "unknown"         # 未知


@dataclass
class PerformanceAnalysis:
    """性能分析结果"""
    expert_name: str
    period: AnalysisPeriod
    timestamp: datetime
    
    # 基础指标
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    success_rate: float
    throughput: float
    error_rate: float
    
    # 分析指标
    health_score: float
    performance_score: float
    trend: TrendDirection
    
    # 对比分析
    baseline_comparison: Dict[str, Any] = field(default_factory=dict)
    peer_comparison: Dict[str, Any] = field(default_factory=dict)
    
    # 异常检测
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    # 优化建议
    recommendations: List[str] = field(default_factory=list)
    
    # 统计信息
    metrics_count: int = 0
    requests_count: int = 0
    errors_count: int = 0


@dataclass
class ComparativeAnalysis:
    """对比分析结果"""
    expert_name: str
    comparison_type: str  # "baseline", "peer", "historical"
    timestamp: datetime
    
    # 对比指标
    metrics_comparison: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 性能差异
    performance_delta: Dict[str, float] = field(default_factory=dict)
    
    # 排名信息
    ranking: Dict[str, Any] = field(default_factory=dict)
    
    # 分析结论
    insights: List[str] = field(default_factory=list)


class MetricsAnalyzer:
    """指标分析器 - 生产级实现"""
    
    def __init__(self, monitor: ExpertMonitor):
        self.monitor = monitor
        self.logger = get_logger("metrics_analyzer")
        self.performance_monitor = get_performance_monitor()
        
        # 分析配置
        self.analysis_cache: Dict[str, Tuple[PerformanceAnalysis, float]] = {}
        self.cache_ttl = 300  # 5分钟缓存
        
        # 基准线配置
        self.baselines: Dict[str, Dict[str, float]] = {
            "response_time": {"good": 0.1, "warning": 0.3, "critical": 0.5},
            "success_rate": {"good": 0.95, "warning": 0.85, "critical": 0.7},
            "throughput": {"good": 50, "warning": 20, "critical": 10},
            "error_rate": {"good": 0.05, "warning": 0.15, "critical": 0.3}
        }
        
        # 分析任务
        self.analysis_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        self.logger.info("指标分析器初始化完成")
    
    def analyze_performance(self, expert_name: str, period: AnalysisPeriod = AnalysisPeriod.HOUR) -> PerformanceAnalysis:
        """分析专家性能 - 生产级增强"""
        with trace_operation("analyze_performance") as trace:
            # 检查缓存
            cache_key = f"{expert_name}:{period.value}"
            if cache_key in self.analysis_cache:
                cached_analysis, timestamp = self.analysis_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    self.logger.debug(f"使用缓存的分析结果 - 专家: {expert_name}, 周期: {period.value}")
                    return cached_analysis
            
            # 获取专家状态和指标
            status = self.monitor.get_expert_status(expert_name)
            if not status:
                raise ValueError(f"专家 {expert_name} 不存在")
            
            # 获取相关指标
            metrics = self._get_metrics_for_period(expert_name, period)
            
            # 执行分析
            analysis = self._perform_analysis(expert_name, status, metrics, period)
            
            # 更新缓存
            self.analysis_cache[cache_key] = (analysis, time.time())
            
            self.logger.info(f"性能分析完成 - 专家: {expert_name}, 周期: {period.value}, 健康评分: {analysis.health_score}, 性能评分: {analysis.performance_score}, 趋势: {analysis.trend.value}")
            
            return analysis
    
    def _get_metrics_for_period(self, expert_name: str, period: AnalysisPeriod) -> Dict[str, List[ExpertMetric]]:
        """获取指定周期的指标数据"""
        metrics = {}
        
        # 根据周期确定时间范围
        end_time = datetime.now()
        if period == AnalysisPeriod.HOUR:
            start_time = end_time - timedelta(hours=1)
            limit = 360  # 每分钟6个点，1小时
        elif period == AnalysisPeriod.DAY:
            start_time = end_time - timedelta(days=1)
            limit = 1440  # 每小时60个点，24小时
        elif period == AnalysisPeriod.WEEK:
            start_time = end_time - timedelta(weeks=1)
            limit = 10080  # 每分钟1个点，7天
        elif period == AnalysisPeriod.MONTH:
            start_time = end_time - timedelta(days=30)
            limit = 43200  # 每小时60个点，30天
        else:  # REAL_TIME
            start_time = end_time - timedelta(minutes=5)
            limit = 300  # 每秒1个点，5分钟
        
        # 获取各种类型的指标
        for metric_type in MetricType:
            metrics_data = self.monitor.get_metrics(
                expert_name, 
                metric_type=metric_type, 
                limit=limit
            )
            
            # 过滤时间范围
            filtered_metrics = [
                m for m in metrics_data 
                if m.timestamp >= start_time
            ]
            
            metrics[metric_type.value] = filtered_metrics
        
        return metrics
    
    def _perform_analysis(self, expert_name: str, status: ExpertStatus, 
                         metrics: Dict[str, List[ExpertMetric]], period: AnalysisPeriod) -> PerformanceAnalysis:
        """执行性能分析"""
        # 基础指标计算
        response_time_metrics = metrics.get(MetricType.RESPONSE_TIME.value, [])
        throughput_metrics = metrics.get(MetricType.THROUGHPUT.value, [])
        
        # 响应时间分析
        response_times = [m.value for m in response_time_metrics]
        response_time_avg = statistics.mean(response_times) if response_times else 0
        response_time_p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else response_time_avg
        response_time_p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else response_time_avg
        
        # 吞吐量分析
        throughput_values = [m.value for m in throughput_metrics]
        throughput_avg = statistics.mean(throughput_values) if throughput_values else 0
        
        # 错误率分析
        error_rate = 1 - status.success_rate if hasattr(status, 'success_rate') else 0
        
        # 健康评分和性能评分
        health_score = self._calculate_health_score(status, metrics)
        performance_score = self._calculate_performance_score(status, metrics)
        
        # 趋势分析
        trend = self._analyze_trend(metrics, period)
        
        # 对比分析
        baseline_comparison = self._compare_with_baseline(status, metrics)
        peer_comparison = self._compare_with_peers(expert_name, status)
        
        # 异常检测
        anomalies = self._detect_anomalies(metrics, status)
        
        # 优化建议
        recommendations = self._generate_recommendations(status, metrics, anomalies)
        
        return PerformanceAnalysis(
            expert_name=expert_name,
            period=period,
            timestamp=datetime.now(),
            response_time_avg=response_time_avg,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p99,
            success_rate=status.success_rate,
            throughput=throughput_avg,
            error_rate=error_rate,
            health_score=health_score,
            performance_score=performance_score,
            trend=trend,
            baseline_comparison=baseline_comparison,
            peer_comparison=peer_comparison,
            anomalies=anomalies,
            recommendations=recommendations,
            metrics_count=sum(len(m) for m in metrics.values()),
            requests_count=status.total_requests if hasattr(status, 'total_requests') else 0,
            errors_count=status.error_count
        )
    
    def _calculate_health_score(self, status: ExpertStatus, metrics: Dict[str, List[ExpertMetric]]) -> float:
        """计算健康评分"""
        score = 100.0
        
        # 响应时间权重 (30%)
        if hasattr(status, 'response_time_avg'):
            rt_score = max(0, 100 - (status.response_time_avg * 1000) / 10)  # 每10ms扣1分
            score = score * 0.7 + rt_score * 0.3
        
        # 成功率权重 (40%)
        if hasattr(status, 'success_rate'):
            sr_score = status.success_rate * 100
            score = score * 0.6 + sr_score * 0.4
        
        # 吞吐量权重 (30%)
        if hasattr(status, 'throughput'):
            tp_score = min(100, status.throughput * 2)  # 每0.5个请求得1分
            score = score * 0.7 + tp_score * 0.3
        
        return round(score, 2)
    
    def _calculate_performance_score(self, status: ExpertStatus, metrics: Dict[str, List[ExpertMetric]]) -> float:
        """计算性能评分"""
        # 基于多个指标的综合评分
        factors = []
        
        if hasattr(status, 'response_time_avg') and status.response_time_avg > 0:
            # 响应时间因子 (越低越好)
            rt_factor = 1.0 / max(0.1, status.response_time_avg)
            factors.append(rt_factor)
        
        if hasattr(status, 'success_rate'):
            # 成功率因子
            sr_factor = status.success_rate
            factors.append(sr_factor)
        
        if hasattr(status, 'throughput'):
            # 吞吐量因子
            tp_factor = min(1.0, status.throughput / 100.0)
            factors.append(tp_factor)
        
        if factors:
            avg_factor = sum(factors) / len(factors)
            return round(avg_factor * 100, 2)
        
        return 0.0
    
    def _analyze_trend(self, metrics: Dict[str, List[ExpertMetric]], period: AnalysisPeriod) -> TrendDirection:
        """分析趋势"""
        # 简化的趋势分析实现
        # 在实际生产环境中，这里应该使用更复杂的算法
        return TrendDirection.STABLE
    
    def _compare_with_baseline(self, status: ExpertStatus, metrics: Dict[str, List[ExpertMetric]]) -> Dict[str, Any]:
        """与基准线对比"""
        comparison = {}
        
        for metric_name, thresholds in self.baselines.items():
            if hasattr(status, metric_name):
                value = getattr(status, metric_name)
                good_threshold = thresholds["good"]
                warning_threshold = thresholds["warning"]
                critical_threshold = thresholds["critical"]
                
                if value <= good_threshold:
                    level = "good"
                elif value <= warning_threshold:
                    level = "warning"
                else:
                    level = "critical"
                
                comparison[metric_name] = {
                    "value": value,
                    "baseline": good_threshold,
                    "level": level,
                    "delta": value - good_threshold
                }
        
        return comparison
    
    def _compare_with_peers(self, expert_name: str, status: ExpertStatus) -> Dict[str, Any]:
        """与同类专家对比"""
        # 简化的同行对比实现
        # 在实际生产环境中，这里应该获取所有同类专家的数据进行对比
        return {
            "peer_count": 0,  # 暂时返回0，需要实际实现
            "ranking": "N/A",
            "percentile": "N/A"
        }
    
    def _detect_anomalies(self, metrics: Dict[str, List[ExpertMetric]], status: ExpertStatus) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []
        
        # 检测响应时间异常
        response_times = [m.value for m in metrics.get(MetricType.RESPONSE_TIME.value, [])]
        if response_times:
            avg_rt = statistics.mean(response_times)
            std_rt = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            # 检测异常高的响应时间
            for rt in response_times:
                if rt > avg_rt + 3 * std_rt and std_rt > 0:
                    anomalies.append({
                        "type": "high_response_time",
                        "value": rt,
                        "threshold": avg_rt + 3 * std_rt,
                        "timestamp": datetime.now()
                    })
        
        return anomalies
    
    def _generate_recommendations(self, status: ExpertStatus, metrics: Dict[str, List[ExpertMetric]], 
                                 anomalies: List[Dict[str, Any]]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于响应时间的建议
        if hasattr(status, 'response_time_avg') and status.response_time_avg > 0.3:
            recommendations.append("响应时间较高，建议优化处理逻辑或增加资源")
        
        # 基于成功率的建议
        if hasattr(status, 'success_rate') and status.success_rate < 0.9:
            recommendations.append("成功率较低，建议检查错误处理和资源分配")
        
        # 基于异常的建议
        if anomalies:
            recommendations.append(f"检测到{len(anomalies)}个异常，建议进行详细分析")
        
        return recommendations
    
    def get_comparative_analysis(self, expert_name: str, comparison_type: str) -> ComparativeAnalysis:
        """获取对比分析"""
        with trace_operation("get_comparative_analysis") as trace:
            # 实现对比分析逻辑
            # 这里简化实现，实际应该包含更复杂的对比算法
            
            return ComparativeAnalysis(
                expert_name=expert_name,
                comparison_type=comparison_type,
                timestamp=datetime.now(),
                insights=["对比分析功能待完善"]
            )
    
    async def start_periodic_analysis(self):
        """启动定期分析任务"""
        if self.is_running:
            self.logger.warning("定期分析任务已在运行中")
            return
        
        self.is_running = True
        self.logger.info("启动定期分析任务")
        
        async def analysis_loop():
            while self.is_running:
                try:
                    # 对所有专家进行小时分析
                    statuses = self.monitor.get_all_status()
                    
                    for expert_name in statuses.keys():
                        try:
                            analysis = self.analyze_performance(expert_name, AnalysisPeriod.HOUR)
                            self.logger.debug(
                                f"定期性能分析 - 专家: {expert_name}, 健康评分: {analysis.health_score}, 性能评分: {analysis.performance_score}"
                            )
                        except Exception as e:
                            self.logger.error(f"专家分析失败 - 专家: {expert_name}, 错误: {e}")
                    
                    # 每小时执行一次
                    await asyncio.sleep(3600)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"定期分析任务异常 - 错误: {e}")
                    await asyncio.sleep(60)  # 异常后等待1分钟
        
        self.analysis_task = asyncio.create_task(analysis_loop())
    
    async def stop_periodic_analysis(self):
        """停止定期分析任务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("停止定期分析任务")


class MetricsAnalysisAPI:
    """指标分析API - 生产级实现"""
    
    def __init__(self, analyzer: MetricsAnalyzer):
        self.analyzer = analyzer
        self.logger = get_logger("metrics_analysis_api")
    
    def get_performance_analysis(self, expert_name: str, period: str = "hour") -> Dict[str, Any]:
        """获取性能分析"""
        with trace_operation("api_get_performance_analysis") as trace:
            try:
                analysis_period = AnalysisPeriod(period)
                analysis = self.analyzer.analyze_performance(expert_name, analysis_period)
                
                result = {
                    "success": True,
                    "analysis": analysis.__dict__,
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": trace.request_id
                }
                
                self.logger.debug(f"API获取性能分析 - 专家: {expert_name}, 周期: {period}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"API获取性能分析异常 - 专家: {expert_name}, 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trace_id": trace.request_id
                }
    
    def get_comparative_analysis(self, expert_name: str, comparison_type: str) -> Dict[str, Any]:
        """获取对比分析"""
        with trace_operation("api_get_comparative_analysis") as trace:
            try:
                analysis = self.analyzer.get_comparative_analysis(expert_name, comparison_type)
                
                result = {
                    "success": True,
                    "analysis": analysis.__dict__,
                    "timestamp": datetime.now().isoformat(),
                    "trace_id": trace.request_id
                }
                
                self.logger.debug(f"API获取对比分析 - 专家: {expert_name}, 对比类型: {comparison_type}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"API获取对比分析异常 - 专家: {expert_name}, 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trace_id": trace.request_id
                }
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        with trace_operation("api_get_analysis_summary") as trace:
            try:
                # 获取所有专家状态
                statuses = self.analyzer.monitor.get_all_status()
                
                # 计算总体统计
                total_experts = len(statuses)
                healthy_experts = sum(1 for s in statuses.values() if s.is_healthy)
                
                # 计算平均评分
                avg_health_score = 0
                avg_performance_score = 0
                if statuses:
                    avg_health_score = sum(s.health_score for s in statuses.values()) / total_experts
                    avg_performance_score = sum(s.performance_score for s in statuses.values()) / total_experts
                
                result = {
                    "success": True,
                    "summary": {
                        "total_experts": total_experts,
                        "healthy_experts": healthy_experts,
                        "unhealthy_experts": total_experts - healthy_experts,
                        "avg_health_score": round(avg_health_score, 2),
                        "avg_performance_score": round(avg_performance_score, 2),
                        "analysis_timestamp": datetime.now().isoformat()
                    },
                    "trace_id": trace.request_id
                }
                
                self.logger.debug(f"API获取分析摘要 - 总专家数: {total_experts}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"API获取分析摘要异常 - 错误: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "trace_id": trace.request_id
                }


# 全局分析器实例
_global_analyzer: Optional[MetricsAnalyzer] = None


def get_metrics_analyzer(monitor: Optional[ExpertMonitor] = None) -> MetricsAnalyzer:
    """获取全局指标分析器"""
    global _global_analyzer
    
    if _global_analyzer is None:
        if monitor is None:
            from .monitoring_system import get_expert_monitor
            monitor = get_expert_monitor()
        _global_analyzer = MetricsAnalyzer(monitor)
    
    return _global_analyzer


def get_metrics_analysis_api() -> MetricsAnalysisAPI:
    """获取指标分析API"""
    analyzer = get_metrics_analyzer()
    return MetricsAnalysisAPI(analyzer)


# 测试代码
if __name__ == "__main__":
    import asyncio
    
    async def test_metrics_analysis():
        """测试指标分析系统"""
        print("=== 指标分析系统测试 ===")
        
        # 获取分析器
        analyzer = get_metrics_analyzer()
        
        # 测试性能分析
        try:
            analysis = analyzer.analyze_performance("test_expert", AnalysisPeriod.HOUR)
            print(f"性能分析结果: {analysis}")
        except Exception as e:
            print(f"性能分析测试失败: {e}")
        
        # 测试API
        api = get_metrics_analysis_api()
        result = api.get_analysis_summary()
        print(f"分析摘要: {result}")
        
        print("=== 指标分析系统测试完成 ===")
    
    asyncio.run(test_metrics_analysis())