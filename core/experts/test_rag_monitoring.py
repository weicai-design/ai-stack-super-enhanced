#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG监控系统测试
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from .rag_monitoring import (
    RAGMetricsCollector, RAGHealthChecker, RAGMonitoringSystem,
    get_monitoring_system
)
from .rag_config import RAGSystemConfig


def test_metrics_collector_basic_operations():
    """测试指标收集器基本操作"""
    collector = RAGMetricsCollector()
    
    # 测试计数器
    collector.increment_counter("test_counter", labels={"type": "test"})
    collector.increment_counter("test_counter", labels={"type": "test"}, value=2)
    
    metrics = collector.get_metrics()
    assert "test_counter" in metrics["counters"]
    assert metrics["counters"]["test_counter"]["type=test"] == 3
    
    # 测试仪表盘
    collector.set_gauge("test_gauge", 42.5, labels={"status": "active"})
    collector.set_gauge("test_gauge", 43.0, labels={"status": "active"})
    
    metrics = collector.get_metrics()
    assert "test_gauge" in metrics["gauges"]
    assert metrics["gauges"]["test_gauge"]["status=active"] == 43.0
    
    # 测试直方图
    collector.record_histogram("test_histogram", 0.5, labels={"operation": "test"})
    collector.record_histogram("test_histogram", 0.7, labels={"operation": "test"})
    collector.record_histogram("test_histogram", 0.9, labels={"operation": "test"})
    
    metrics = collector.get_metrics()
    assert "test_histogram" in metrics["histograms"]
    histogram_data = metrics["histograms"]["test_histogram"]["operation=test"]
    assert histogram_data["count"] == 3
    assert histogram_data["sum"] == 2.1
    assert histogram_data["avg"] == 0.7


def test_metrics_collector_reset():
    """测试指标收集器重置"""
    collector = RAGMetricsCollector()
    
    collector.increment_counter("test_counter")
    collector.set_gauge("test_gauge", 10.0)
    
    metrics = collector.get_metrics()
    assert len(metrics["counters"]) > 0
    assert len(metrics["gauges"]) > 0
    
    collector.reset()
    
    metrics = collector.get_metrics()
    assert len(metrics["counters"]) == 0
    assert len(metrics["gauges"]) == 0


def test_health_checker_system_health():
    """测试健康检查器系统健康检查"""
    health_checker = RAGHealthChecker()
    
    # 测试系统健康检查
    health_status = health_checker.check_system_health()
    
    assert "status" in health_status
    assert "timestamp" in health_status
    assert "cpu_usage" in health_status
    assert "memory_usage" in health_status
    assert "disk_usage" in health_status
    
    # 验证状态值在合理范围内
    assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
    assert 0 <= health_status["cpu_usage"] <= 100
    assert 0 <= health_status["memory_usage"] <= 100
    assert 0 <= health_status["disk_usage"] <= 100


def test_health_checker_performance_metrics():
    """测试健康检查器性能指标"""
    health_checker = RAGHealthChecker()
    
    # 记录一些性能数据
    health_checker.record_request_latency(0.1)
    health_checker.record_request_latency(0.2)
    health_checker.record_request_latency(0.3)
    
    health_checker.record_error_rate(0.05)
    
    # 获取性能指标
    performance_metrics = health_checker.get_performance_metrics()
    
    assert "request_count" in performance_metrics
    assert "avg_latency" in performance_metrics
    assert "error_rate" in performance_metrics
    assert "throughput" in performance_metrics
    
    assert performance_metrics["request_count"] == 3
    assert performance_metrics["avg_latency"] == 0.2
    assert performance_metrics["error_rate"] == 0.05


def test_health_checker_memory_usage():
    """测试健康检查器内存使用情况"""
    health_checker = RAGHealthChecker()
    
    memory_usage = health_checker.get_memory_usage()
    
    assert "total" in memory_usage
    assert "used" in memory_usage
    assert "free" in memory_usage
    assert "percentage" in memory_usage
    
    # 验证内存使用率在合理范围内
    assert 0 <= memory_usage["percentage"] <= 100
    assert memory_usage["used"] <= memory_usage["total"]
    assert memory_usage["free"] == memory_usage["total"] - memory_usage["used"]


def test_monitoring_system_integration():
    """测试监控系统集成"""
    system_config = RAGSystemConfig(monitoring_enabled=True)
    monitoring_system = RAGMonitoringSystem(system_config)
    
    # 测试专家分析跟踪
    monitoring_system.track_expert_analysis(
        expert_id="test_expert",
        analysis_type="knowledge",
        duration=0.5,
        success=True
    )
    
    # 测试请求跟踪
    monitoring_system.track_request(
        request_id="test_request",
        endpoint="/api/analyze",
        duration=1.2,
        status_code=200
    )
    
    # 获取监控数据
    metrics = monitoring_system.metrics_collector.get_metrics()
    health_status = monitoring_system.health_checker.check_system_health()
    
    assert "rag_expert_analysis_total" in metrics["counters"]
    assert "rag_request_duration_seconds" in metrics["histograms"]
    assert health_status["status"] in ["healthy", "degraded", "unhealthy"]


def test_monitoring_system_disabled():
    """测试监控系统禁用状态"""
    system_config = RAGSystemConfig(monitoring_enabled=False)
    monitoring_system = RAGMonitoringSystem(system_config)
    
    # 在禁用状态下，跟踪操作应该不会记录数据
    monitoring_system.track_expert_analysis(
        expert_id="test_expert",
        analysis_type="knowledge",
        duration=0.5,
        success=True
    )
    
    metrics = monitoring_system.metrics_collector.get_metrics()
    
    # 计数器应该为空，因为监控被禁用
    assert len(metrics["counters"]) == 0


def test_monitoring_system_error_handling():
    """测试监控系统错误处理"""
    system_config = RAGSystemConfig()
    monitoring_system = RAGMonitoringSystem(system_config)
    
    # 测试无效的指标名称
    monitoring_system.metrics_collector.increment_counter("", labels={"test": "value"})
    monitoring_system.metrics_collector.set_gauge("invalid*name", 10.0)
    
    # 应该正常处理，不会抛出异常
    metrics = monitoring_system.metrics_collector.get_metrics()
    assert metrics is not None


def test_monitoring_system_export_metrics():
    """测试监控系统指标导出"""
    system_config = RAGSystemConfig()
    monitoring_system = RAGMonitoringSystem(system_config)
    
    # 添加一些测试数据
    monitoring_system.track_expert_analysis(
        expert_id="test_expert",
        analysis_type="knowledge",
        duration=0.3,
        success=True
    )
    
    # 导出指标
    exported_metrics = monitoring_system.export_metrics()
    
    assert "metrics" in exported_metrics
    assert "health_status" in exported_metrics
    assert "performance_metrics" in exported_metrics
    assert "timestamp" in exported_metrics
    
    # 验证导出的数据结构
    assert isinstance(exported_metrics["metrics"], dict)
    assert isinstance(exported_metrics["health_status"], dict)
    assert isinstance(exported_metrics["performance_metrics"], dict)


def test_get_monitoring_system_singleton():
    """测试监控系统单例模式"""
    system1 = get_monitoring_system()
    system2 = get_monitoring_system()
    
    assert system1 is system2


def test_monitoring_system_thread_safety():
    """测试监控系统线程安全"""
    import threading
    
    system_config = RAGSystemConfig()
    monitoring_system = RAGMonitoringSystem(system_config)
    
    results = []
    
    def worker(worker_id):
        for i in range(100):
            monitoring_system.track_expert_analysis(
                expert_id=f"expert_{worker_id}",
                analysis_type="test",
                duration=0.1 * (i + 1),
                success=True
            )
        results.append(f"worker_{worker_id}_done")
    
    # 创建多个线程并发操作
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 验证数据一致性
    metrics = monitoring_system.metrics_collector.get_metrics()
    analysis_counter = metrics["counters"].get("rag_expert_analysis_total", {})
    
    # 总分析次数应该是500次（5个线程 * 100次）
    total_analyses = sum(analysis_counter.values())
    assert total_analyses == 500


def test_health_checker_thresholds():
    """测试健康检查器阈值设置"""
    health_checker = RAGHealthChecker()
    
    # 设置自定义阈值
    health_checker.set_health_thresholds(
        cpu_threshold=80.0,
        memory_threshold=85.0,
        disk_threshold=90.0
    )
    
    # 模拟高CPU使用率
    with patch('psutil.cpu_percent') as mock_cpu:
        mock_cpu.return_value = 85.0  # 超过阈值
        
        health_status = health_checker.check_system_health()
        
        # 当CPU使用率超过阈值时，状态应为degraded
        if health_status["cpu_usage"] > 80.0:
            assert health_status["status"] == "degraded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])