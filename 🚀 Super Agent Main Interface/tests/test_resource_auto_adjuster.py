"""
资源自动调节器单元测试 - AI-STACK优化：支持完整的测试覆盖

测试目标：
1. 验证资源监控功能
2. 测试问题分析和建议生成
3. 验证调节动作执行
4. 测试配置管理和异常处理
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.resource_auto_adjuster import (
    ResourceAutoAdjuster, ResourceConfig, ResourceIssueType, 
    ResourceIssue, AdjustmentAction, AdjustmentSuggestion
)


class TestResourceConfig(unittest.TestCase):
    """资源配置管理测试"""
    
    def setUp(self):
        self.config = ResourceConfig()
    
    def test_default_config(self):
        """测试默认配置"""
        self.assertEqual(self.config.get("monitoring.interval"), 5)
        self.assertEqual(self.config.get("thresholds.cpu.warning"), 70)
        self.assertEqual(self.config.get("security.require_approval_for_critical"), True)
    
    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = {
            "monitoring": {"interval": 10},
            "thresholds": {"cpu": {"warning": 80}}
        }
        config = ResourceConfig(custom_config)
        
        self.assertEqual(config.get("monitoring.interval"), 10)
        self.assertEqual(config.get("thresholds.cpu.warning"), 80)
    
    def test_set_config(self):
        """测试设置配置"""
        self.config.set("monitoring.interval", 15)
        self.assertEqual(self.config.get("monitoring.interval"), 15)
        
        self.config.set("thresholds.memory.critical", 95)
        self.assertEqual(self.config.get("thresholds.memory.critical"), 95)


class TestResourceAutoAdjuster(unittest.TestCase):
    """资源自动调节器测试"""
    
    def setUp(self):
        """测试初始化"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 创建模拟配置
        self.mock_config = Mock()
        self.mock_config.get = Mock(side_effect=self._mock_config_get)
        
        # 创建调节器实例
        self.adjuster = ResourceAutoAdjuster(config=self.mock_config)
        
        # 模拟统计信息
        self.adjuster.statistics = {
            "total_issues_detected": 0,
            "total_suggestions_generated": 0,
            "total_adjustments_executed": 0,
            "successful_adjustments": 0,
            "failed_adjustments": 0,
            "last_operation_time": None
        }
    
    def tearDown(self):
        """测试清理"""
        self.loop.close()
    
    def _mock_config_get(self, key, default=None):
        """模拟配置获取"""
        config_map = {
            "monitoring.interval": 5,
            "monitoring.enable_auto_adjust": False,
            "thresholds.cpu.warning": 70,
            "thresholds.cpu.critical": 90,
            "thresholds.memory.warning": 75,
            "thresholds.memory.critical": 90,
            "thresholds.disk.warning": 80,
            "thresholds.disk.critical": 95,
            "thresholds.network.warning": 50,
            "thresholds.network.critical": 80,
            "security.require_approval_for_critical": True,
            "security.max_auto_adjustments_per_hour": 10,
            "security.enable_audit_log": True,
            "performance.cache_ttl": 300,
            "performance.max_concurrent_operations": 5,
            "performance.enable_async_processing": True
        }
        return config_map.get(key, default)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.adjuster.config)
        self.assertEqual(len(self.adjuster.issues), 0)
        self.assertEqual(len(self.adjuster.suggestions), 0)
        self.assertEqual(len(self.adjuster.approved_adjustments), 0)
    
    @patch('core.resource_auto_adjuster.psutil.cpu_percent')
    @patch('core.resource_auto_adjuster.psutil.virtual_memory')
    @patch('core.resource_auto_adjuster.psutil.disk_usage')
    @patch('core.resource_auto_adjuster.psutil.net_io_counters')
    def test_monitor_resources_normal(self, mock_net, mock_disk, mock_memory, mock_cpu):
        """测试正常资源监控"""
        # 模拟正常资源使用率
        mock_cpu.return_value = 50.0
        
        memory_mock = Mock()
        memory_mock.percent = 60.0
        memory_mock.available = 8 * 1024**3  # 8GB
        memory_mock.total = 16 * 1024**3     # 16GB
        mock_memory.return_value = memory_mock
        
        disk_mock = Mock()
        disk_mock.percent = 70.0
        disk_mock.free = 50 * 1024**3        # 50GB
        disk_mock.total = 200 * 1024**3      # 200GB
        mock_disk.return_value = disk_mock
        
        net_mock = Mock()
        net_mock.bytes_sent = 100 * 1024**2  # 100MB
        net_mock.bytes_recv = 150 * 1024**2  # 150MB
        mock_net.return_value = net_mock
        
        # 执行监控
        result = self.loop.run_until_complete(self.adjuster.monitor_resources())
        
        # 验证结果
        self.assertEqual(len(result), 0)  # 应该没有检测到问题
        self.assertEqual(self.adjuster.statistics["total_issues_detected"], 0)
    
    @patch('core.resource_auto_adjuster.psutil.cpu_percent')
    def test_monitor_resources_cpu_critical(self, mock_cpu):
        """测试CPU临界问题检测"""
        # 模拟CPU使用率过高
        mock_cpu.return_value = 95.0
        
        # 执行监控
        result = self.loop.run_until_complete(self.adjuster.monitor_resources())
        
        # 验证结果
        self.assertEqual(len(result), 1)
        issue = result[0]
        self.assertEqual(issue.issue_type, ResourceIssueType.CPU_HIGH)
        self.assertEqual(issue.severity, "critical")
        self.assertIn("CPU使用率过高", issue.description)
    
    def test_analyze_issue_cpu(self):
        """测试CPU问题分析"""
        # 创建CPU问题
        issue = ResourceIssue(
            issue_type=ResourceIssueType.CPU_HIGH,
            severity="critical",
            description="CPU使用率过高: 95%",
            current_value=95.0,
            threshold=90.0,
            affected_modules=["python3", "chrome"],
            detected_at=datetime.now(),
            metadata={"cpu_percent": 95.0}
        )
        
        # 执行分析
        result = self.loop.run_until_complete(self.adjuster.analyze_issue(issue))
        
        # 验证结果
        self.assertGreater(len(result), 0)
        suggestion = result[0]
        self.assertIn(suggestion.action, [
            AdjustmentAction.REDUCE_PRIORITY,
            AdjustmentAction.TERMINATE_PROCESS,
            AdjustmentAction.REALLOCATE_RESOURCES
        ])
    
    def test_execute_adjustment_clear_cache(self):
        """测试清理缓存调节动作"""
        # 创建调节建议
        issue = ResourceIssue(
            issue_type=ResourceIssueType.MEMORY_HIGH,
            severity="warning",
            description="内存使用率较高: 80%",
            current_value=80.0,
            threshold=75.0,
            affected_modules=[],
            detected_at=datetime.now(),
            metadata={"memory_percent": 80.0}
        )
        
        suggestion = AdjustmentSuggestion(
            issue=issue,
            action=AdjustmentAction.CLEAR_CACHE,
            description="清理系统缓存",
            estimated_improvement=15.0,
            requires_approval=False
        )
        
        # 执行调节
        result = self.loop.run_until_complete(
            self.adjuster.execute_adjustment(suggestion, approved=True)
        )
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.adjuster.statistics["total_adjustments_executed"], 1)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加一些测试数据
        self.adjuster.issues.append(ResourceIssue(
            issue_type=ResourceIssueType.CPU_HIGH,
            severity="critical",
            description="测试问题",
            current_value=95.0,
            threshold=90.0,
            affected_modules=[],
            detected_at=datetime.now(),
            metadata={}
        ))
        
        # 获取统计信息
        stats = self.adjuster.get_statistics()
        
        # 验证结果
        self.assertIn("monitoring", stats)
        self.assertIn("distribution", stats)
        self.assertIn("configuration", stats)
        self.assertEqual(stats["monitoring"]["total_issues_detected"], 0)  # 统计信息独立计数
    
    def test_rate_limit_check(self):
        """测试频率限制检查"""
        # 添加一些调节记录
        for i in range(5):
            self.adjuster.approved_adjustments.append({
                "executed_at": (datetime.now() - timedelta(minutes=i*10)).isoformat()
            })
        
        # 检查频率限制
        result = self.adjuster._check_rate_limit()
        self.assertTrue(result)  # 5 < 10，应该通过
        
        # 添加更多记录
        for i in range(6):
            self.adjuster.approved_adjustments.append({
                "executed_at": (datetime.now() - timedelta(minutes=i*5)).isoformat()
            })
        
        # 再次检查
        result = self.adjuster._check_rate_limit()
        self.assertFalse(result)  # 11 > 10，应该被限制


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 使用真实配置创建调节器
        self.adjuster = ResourceAutoAdjuster()
    
    def tearDown(self):
        self.loop.close()
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 监控资源
        issues = self.loop.run_until_complete(self.adjuster.monitor_resources())
        
        # 2. 分析问题
        suggestions = []
        for issue in issues:
            issue_suggestions = self.loop.run_until_complete(
                self.adjuster.analyze_issue(issue)
            )
            suggestions.extend(issue_suggestions)
        
        # 3. 执行调节（如果有建议）
        if suggestions:
            result = self.loop.run_until_complete(
                self.adjuster.execute_adjustment(suggestions[0], approved=True)
            )
            self.assertIn(result["status"], ["success", "failed", "pending_approval"])
        
        # 4. 验证统计信息
        stats = self.adjuster.get_statistics()
        self.assertIsInstance(stats, dict)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)