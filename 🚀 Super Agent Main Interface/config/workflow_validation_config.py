#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证配置文件

功能：
1. 配置验证参数和阈值
2. 定义验证规则
3. 配置监控设置
4. 管理测试场景
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum


class ValidationRuleType(Enum):
    """验证规则类型"""
    PERFORMANCE = "performance"
    FUNCTIONAL = "functional"
    SECURITY = "security"
    RELIABILITY = "reliability"


@dataclass
class ValidationRule:
    """验证规则配置"""
    name: str
    rule_type: ValidationRuleType
    description: str
    threshold: float
    severity: str  # "critical", "warning", "info"
    enabled: bool = True


@dataclass
class PerformanceThreshold:
    """性能阈值配置"""
    max_response_time: float  # 最大响应时间（秒）
    max_memory_usage: float  # 最大内存使用（MB）
    max_cpu_usage: float  # 最大CPU使用率（%）
    concurrent_users: int  # 并发用户数


@dataclass
class ValidationScenario:
    """验证场景配置"""
    name: str
    description: str
    workflow_type: str  # "intelligent", "direct"
    input_template: Dict[str, Any]
    expected_output: Dict[str, Any]
    enabled: bool = True


class WorkflowValidationConfig:
    """工作流验证配置类"""
    
    def __init__(self):
        # 性能阈值配置
        self.performance_thresholds = PerformanceThreshold(
            max_response_time=2.0,  # 2秒SLO
            max_memory_usage=512.0,  # 512MB
            max_cpu_usage=80.0,  # 80%
            concurrent_users=10  # 10个并发用户
        )
        
        # 验证规则配置
        self.validation_rules = self._setup_validation_rules()
        
        # 验证场景配置
        self.validation_scenarios = self._setup_validation_scenarios()
        
        # 监控配置
        self.monitoring_config = {
            "update_interval": 5,  # 监控更新间隔（秒）
            "retention_period": 24,  # 数据保留时间（小时）
            "alert_channels": ["console", "file", "email"],  # 告警通道
            "log_level": "INFO",  # 日志级别
        }
        
        # 报告配置
        self.reporting_config = {
            "auto_generate": True,  # 自动生成报告
            "report_format": "markdown",  # 报告格式
            "save_directory": "validation_reports",  # 保存目录
            "max_reports": 100,  # 最大报告数量
        }
    
    def _setup_validation_rules(self) -> List[ValidationRule]:
        """设置验证规则"""
        return [
            ValidationRule(
                name="response_time_slo",
                rule_type=ValidationRuleType.PERFORMANCE,
                description="响应时间SLO验证（<2秒）",
                threshold=2.0,
                severity="critical",
            ),
            ValidationRule(
                name="workflow_completion",
                rule_type=ValidationRuleType.FUNCTIONAL,
                description="工作流完成率验证（>95%）",
                threshold=0.95,
                severity="critical",
            ),
            ValidationRule(
                name="rag_retrieval_accuracy",
                rule_type=ValidationRuleType.FUNCTIONAL,
                description="RAG检索准确率验证（>90%）",
                threshold=0.90,
                severity="warning",
            ),
            ValidationRule(
                name="expert_routing_success",
                rule_type=ValidationRuleType.FUNCTIONAL,
                description="专家路由成功率验证（>98%）",
                threshold=0.98,
                severity="warning",
            ),
            ValidationRule(
                name="module_execution_success",
                rule_type=ValidationRuleType.FUNCTIONAL,
                description="模块执行成功率验证（>99%）",
                threshold=0.99,
                severity="critical",
            ),
            ValidationRule(
                name="dual_loop_integrity",
                rule_type=ValidationRuleType.RELIABILITY,
                description="双线闭环完整性验证（100%）",
                threshold=1.0,
                severity="critical",
            ),
            ValidationRule(
                name="error_handling_effectiveness",
                rule_type=ValidationRuleType.RELIABILITY,
                description="错误处理有效性验证（>95%）",
                threshold=0.95,
                severity="warning",
            ),
        ]
    
    def _setup_validation_scenarios(self) -> List[ValidationScenario]:
        """设置验证场景"""
        return [
            ValidationScenario(
                name="erp_order_query",
                description="ERP订单查询工作流验证",
                workflow_type="intelligent",
                input_template={
                    "query": "查询最近3天的订单状态",
                    "domain": "erp",
                    "priority": "normal",
                },
                expected_output={
                    "status": "completed",
                    "steps": ["RAG检索", "专家路由", "模块执行", "专家整合", "RAG存储"],
                    "min_steps": 4,
                    "max_duration": 2.0,
                },
            ),
            ValidationScenario(
                name="content_creation_suggestion",
                description="内容创作建议工作流验证",
                workflow_type="intelligent",
                input_template={
                    "query": "为新产品生成营销内容建议",
                    "domain": "content_creation",
                    "priority": "normal",
                },
                expected_output={
                    "status": "completed",
                    "steps": ["RAG检索", "策划专家", "生成专家", "去AI化专家", "RAG存储"],
                    "min_steps": 4,
                    "max_duration": 2.0,
                },
            ),
            ValidationScenario(
                name="stock_trend_analysis",
                description="股票趋势分析工作流验证",
                workflow_type="intelligent",
                input_template={
                    "query": "分析AAPL股票最近一周的趋势",
                    "domain": "stock_quant",
                    "priority": "normal",
                },
                expected_output={
                    "status": "completed",
                    "steps": ["RAG检索", "技术分析专家", "基本面专家", "风险分析专家", "RAG存储"],
                    "min_steps": 4,
                    "max_duration": 2.0,
                },
            ),
            ValidationScenario(
                name="direct_operation_workflow",
                description="直接操作工作流验证",
                workflow_type="direct",
                input_template={
                    "query": "执行系统状态检查",
                    "domain": "system",
                    "priority": "high",
                },
                expected_output={
                    "status": "completed",
                    "steps": ["模块执行", "结果返回"],
                    "min_steps": 2,
                    "max_duration": 1.0,
                },
            ),
            ValidationScenario(
                name="error_handling_workflow",
                description="错误处理工作流验证",
                workflow_type="intelligent",
                input_template={
                    "query": "执行无效操作",
                    "domain": "error_test",
                    "priority": "normal",
                },
                expected_output={
                    "status": "failed",
                    "steps": ["RAG检索", "错误处理"],
                    "min_steps": 1,
                    "max_duration": 1.5,
                },
            ),
            ValidationScenario(
                name="concurrent_workflow_test",
                description="并发工作流验证",
                workflow_type="intelligent",
                input_template={
                    "query": "并发测试查询",
                    "domain": "concurrent_test",
                    "priority": "normal",
                },
                expected_output={
                    "status": "completed",
                    "steps": ["RAG检索", "专家路由", "模块执行"],
                    "min_steps": 3,
                    "max_duration": 3.0,
                },
            ),
        ]
    
    def get_enabled_rules(self) -> List[ValidationRule]:
        """获取启用的验证规则"""
        return [rule for rule in self.validation_rules if rule.enabled]
    
    def get_enabled_scenarios(self) -> List[ValidationScenario]:
        """获取启用的验证场景"""
        return [scenario for scenario in self.validation_scenarios if scenario.enabled]
    
    def get_rule_by_name(self, name: str) -> Optional[ValidationRule]:
        """根据名称获取验证规则"""
        for rule in self.validation_rules:
            if rule.name == name:
                return rule
        return None
    
    def get_scenario_by_name(self, name: str) -> Optional[ValidationScenario]:
        """根据名称获取验证场景"""
        for scenario in self.validation_scenarios:
            if scenario.name == name:
                return scenario
        return None
    
    def update_performance_thresholds(self, **kwargs):
        """更新性能阈值"""
        for key, value in kwargs.items():
            if hasattr(self.performance_thresholds, key):
                setattr(self.performance_thresholds, key, value)
    
    def enable_rule(self, rule_name: str):
        """启用验证规则"""
        rule = self.get_rule_by_name(rule_name)
        if rule:
            rule.enabled = True
    
    def disable_rule(self, rule_name: str):
        """禁用验证规则"""
        rule = self.get_rule_by_name(rule_name)
        if rule:
            rule.enabled = False
    
    def enable_scenario(self, scenario_name: str):
        """启用验证场景"""
        scenario = self.get_scenario_by_name(scenario_name)
        if scenario:
            scenario.enabled = True
    
    def disable_scenario(self, scenario_name: str):
        """禁用验证场景"""
        scenario = self.get_scenario_by_name(scenario_name)
        if scenario:
            scenario.enabled = False


# 全局配置实例
workflow_validation_config = WorkflowValidationConfig()


def get_workflow_validation_config() -> WorkflowValidationConfig:
    """获取工作流验证配置实例"""
    return workflow_validation_config


if __name__ == "__main__":
    # 测试配置
    config = get_workflow_validation_config()
    
    print("🚀 工作流验证配置测试")
    print("=" * 50)
    
    print("\n📊 性能阈值:")
    print(f"   最大响应时间: {config.performance_thresholds.max_response_time}秒")
    print(f"   最大内存使用: {config.performance_thresholds.max_memory_usage}MB")
    print(f"   最大CPU使用率: {config.performance_thresholds.max_cpu_usage}%")
    print(f"   并发用户数: {config.performance_thresholds.concurrent_users}")
    
    print("\n🔧 验证规则:")
    for rule in config.get_enabled_rules():
        print(f"   {rule.name}: {rule.description} (阈值: {rule.threshold})")
    
    print("\n🎯 验证场景:")
    for scenario in config.get_enabled_scenarios():
        print(f"   {scenario.name}: {scenario.description}")
    
    print("\n✅ 配置加载完成")