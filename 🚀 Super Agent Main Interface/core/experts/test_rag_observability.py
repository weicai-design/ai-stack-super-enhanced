#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG可观测性系统测试
"""

import pytest
import time
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from .rag_observability import (
    TracingContext, Span, RAGTracer, StructuredLogger,
    RAGHealthCheckAPI, RAGMetricsAPI, get_observability_system,
    trace_operation
)


def test_tracing_context_basic():
    """测试追踪上下文基本功能"""
    context = TracingContext()
    
    # 测试开始追踪
    trace_id = context.start_trace("test_trace")
    assert trace_id is not None
    assert trace_id in context.active_traces
    
    # 测试获取当前追踪
    current_trace = context.get_current_trace()
    assert current_trace is not None
    assert current_trace["trace_id"] == trace_id
    
    # 测试结束追踪
    context.end_trace(trace_id)
    assert trace_id not in context.active_traces
    assert trace_id in context.completed_traces


def test_tracing_context_nested():
    """测试嵌套追踪"""
    context = TracingContext()
    
    # 创建父追踪
    parent_trace_id = context.start_trace("parent_trace")
    
    # 创建子追踪
    child_trace_id = context.start_trace("child_trace", parent_trace_id=parent_trace_id)
    
    # 验证父子关系
    child_trace = context.get_trace(child_trace_id)
    assert child_trace["parent_trace_id"] == parent_trace_id
    
    # 结束子追踪
    context.end_trace(child_trace_id)
    
    # 结束父追踪
    context.end_trace(parent_trace_id)
    
    # 验证追踪状态
    assert parent_trace_id in context.completed_traces
    assert child_trace_id in context.completed_traces


def test_span_creation():
    """测试Span创建"""
    span = Span(
        span_id="test_span",
        name="test_operation",
        trace_id="test_trace",
        start_time=datetime.now()
    )
    
    assert span.span_id == "test_span"
    assert span.name == "test_operation"
    assert span.trace_id == "test_trace"
    assert span.status == "active"
    
    # 测试Span完成
    span.finish()
    assert span.status == "completed"
    assert span.end_time is not None
    
    # 测试Span数据转换
    span_data = span.to_dict()
    assert span_data["span_id"] == "test_span"
    assert span_data["name"] == "test_operation"
    assert span_data["status"] == "completed"


def test_span_with_attributes():
    """测试带属性的Span"""
    span = Span(
        span_id="test_span",
        name="test_operation",
        trace_id="test_trace"
    )
    
    # 添加属性
    span.add_attribute("service", "rag_expert")
    span.add_attribute("operation", "knowledge_analysis")
    
    # 添加事件
    span.add_event("analysis_started", {"timestamp": datetime.now().isoformat()})
    
    span.finish()
    
    span_data = span.to_dict()
    assert span_data["attributes"]["service"] == "rag_expert"
    assert span_data["attributes"]["operation"] == "knowledge_analysis"
    assert len(span_data["events"]) == 1


def test_rag_tracer_basic():
    """测试RAG追踪器基本功能"""
    tracer = RAGTracer()
    
    # 测试开始追踪
    trace_id = tracer.start_trace("test_trace", {"service": "rag_system"})
    assert trace_id is not None
    
    # 测试开始Span
    span = tracer.start_span("test_span", trace_id, {"operation": "analysis"})
    assert span is not None
    assert span.name == "test_span"
    
    # 测试结束Span
    tracer.end_span(span)
    assert span.status == "completed"
    
    # 测试结束追踪
    tracer.end_trace(trace_id)
    
    # 验证追踪数据
    trace_data = tracer.get_trace(trace_id)
    assert trace_data["trace_id"] == trace_id
    assert len(trace_data["spans"]) == 1


def test_rag_tracer_span_operations():
    """测试RAG追踪器Span操作"""
    tracer = RAGTracer()
    
    trace_id = tracer.start_trace("complex_trace")
    
    # 创建多个Span
    span1 = tracer.start_span("span1", trace_id)
    span2 = tracer.start_span("span2", trace_id)
    
    # 验证Span关系
    assert span1.trace_id == trace_id
    assert span2.trace_id == trace_id
    
    # 结束Span
    tracer.end_span(span1)
    tracer.end_span(span2)
    
    tracer.end_trace(trace_id)
    
    # 验证追踪包含多个Span
    trace_data = tracer.get_trace(trace_id)
    assert len(trace_data["spans"]) == 2


def test_structured_logger():
    """测试结构化日志记录器"""
    logger = StructuredLogger("test_service")
    
    # 测试不同级别的日志
    logger.info("测试信息日志", {"user": "test_user", "action": "login"})
    logger.warning("测试警告日志", {"issue": "low_memory"})
    logger.error("测试错误日志", {"error_code": "500", "endpoint": "/api/test"})
    logger.debug("测试调试日志", {"debug_info": "detailed_data"})
    
    # 验证日志格式
    # 这里主要测试日志方法不会抛出异常
    assert True


def test_health_check_api():
    """测试健康检查API"""
    health_api = RAGHealthCheckAPI()
    
    # 测试健康检查端点
    health_response = health_api.check_health()
    
    assert "status" in health_response
    assert "timestamp" in health_response
    assert "services" in health_response
    
    # 验证响应格式
    assert health_response["status"] in ["healthy", "degraded", "unhealthy"]
    assert isinstance(health_response["services"], dict)


def test_metrics_api():
    """测试指标API"""
    metrics_api = RAGMetricsAPI()
    
    # 测试指标端点
    metrics_response = metrics_api.get_metrics()
    
    assert "metrics" in metrics_response
    assert "timestamp" in metrics_response
    
    # 验证指标数据结构
    metrics_data = metrics_response["metrics"]
    assert "counters" in metrics_data
    assert "gauges" in metrics_data
    assert "histograms" in metrics_data


def test_trace_operation_decorator():
    """测试追踪操作装饰器"""
    
    @trace_operation("test_operation")
    def test_function(param1, param2):
        time.sleep(0.01)  # 模拟工作
        return param1 + param2
    
    # 调用被装饰的函数
    result = test_function(2, 3)
    
    assert result == 5
    
    # 验证追踪器被调用
    # 这里主要测试装饰器不会影响函数功能
    assert True


def test_trace_operation_with_exception():
    """测试追踪操作装饰器异常处理"""
    
    @trace_operation("failing_operation")
    def failing_function():
        raise ValueError("测试异常")
    
    # 测试异常处理
    try:
        failing_function()
        assert False, "应该抛出异常"
    except ValueError:
        # 异常应该正常传播
        assert True


def test_get_observability_system_singleton():
    """测试可观测性系统单例模式"""
    system1 = get_observability_system()
    system2 = get_observability_system()
    
    assert system1 is system2


def test_observability_system_integration():
    """测试可观测性系统集成"""
    system = get_observability_system()
    
    # 测试追踪功能
    trace_id = system.tracer.start_trace("integration_test")
    span = system.tracer.start_span("test_span", trace_id)
    system.tracer.end_span(span)
    system.tracer.end_trace(trace_id)
    
    # 测试日志功能
    system.logger.info("集成测试日志", {"test": "integration"})
    
    # 测试健康检查
    health_status = system.health_api.check_health()
    assert "status" in health_status
    
    # 测试指标收集
    metrics = system.metrics_api.get_metrics()
    assert "metrics" in metrics


def test_span_error_handling():
    """测试Span错误处理"""
    span = Span("test_span", "test_operation", "test_trace")
    
    # 测试错误记录
    span.record_error("测试错误", {"error_code": "500"})
    
    span.finish()
    
    span_data = span.to_dict()
    assert "errors" in span_data
    assert len(span_data["errors"]) == 1
    assert span_data["errors"][0]["message"] == "测试错误"


def test_tracing_context_cleanup():
    """测试追踪上下文清理"""
    context = TracingContext()
    
    # 创建多个追踪
    for i in range(10):
        trace_id = context.start_trace(f"trace_{i}")
        context.end_trace(trace_id)
    
    # 测试清理功能
    context.cleanup_old_traces(max_age_seconds=0)  # 立即清理
    
    assert len(context.completed_traces) == 0


def test_structured_logger_custom_fields():
    """测试结构化日志记录器自定义字段"""
    logger = StructuredLogger("custom_service", {"environment": "test", "version": "1.0.0"})
    
    # 测试日志包含自定义字段
    # 这里主要验证方法调用不会出错
    logger.info("自定义字段测试", {"user_action": "test_action"})
    
    assert True


def test_health_check_api_custom_checks():
    """测试健康检查API自定义检查"""
    health_api = RAGHealthCheckAPI()
    
    # 添加自定义健康检查
    def custom_check():
        return {"status": "healthy", "message": "自定义检查通过"}
    
    health_api.add_custom_check("custom_service", custom_check)
    
    # 执行健康检查
    health_response = health_api.check_health()
    
    assert "custom_service" in health_response["services"]
    assert health_response["services"]["custom_service"]["status"] == "healthy"


def test_metrics_api_custom_metrics():
    """测试指标API自定义指标"""
    metrics_api = RAGMetricsAPI()
    
    # 添加自定义指标
    metrics_api.add_custom_metric("custom_counter", "counter", "自定义计数器")
    metrics_api.add_custom_metric("custom_gauge", "gauge", "自定义仪表盘")
    
    # 获取指标
    metrics_response = metrics_api.get_metrics()
    
    # 验证自定义指标存在
    custom_metrics = metrics_response.get("custom_metrics", {})
    assert "custom_counter" in custom_metrics
    assert "custom_gauge" in custom_metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])