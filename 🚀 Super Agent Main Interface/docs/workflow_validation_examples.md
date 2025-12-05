# 工作流验证器使用示例和集成指南

## 快速开始示例

### 基础验证示例

```python
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def basic_validation_example():
    """基础验证示例"""
    # 创建验证器实例
    validator = WorkflowEnhancedValidator()
    
    # 开始验证
    validation_id = await validator.start_workflow_validation(
        workflow_id="simple_chat_workflow",
        workflow_type="direct",
        user_input="你好，请帮我查询天气",
        context={"user_id": "12345", "location": "北京"}
    )
    
    # 等待验证完成
    await asyncio.sleep(1)
    
    # 获取验证报告
    report = await validator.get_validation_report(validation_id)
    
    # 输出验证结果
    print(f"工作流ID: {report.workflow_id}")
    print(f"验证状态: {report.overall_status}")
    print(f"验证耗时: {report.total_duration:.2f}秒")
    
    # 显示详细验证结果
    for result in report.validation_results:
        print(f"  - {result.validation_type}: {result.status} ({result.level})")

if __name__ == "__main__":
    asyncio.run(basic_validation_example())
```

### 智能工作流验证示例

```python
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def intelligent_workflow_validation():
    """智能工作流验证示例"""
    validator = WorkflowEnhancedValidator()
    
    validation_id = await validator.start_workflow_validation(
        workflow_id="ai_analysis_workflow",
        workflow_type="intelligent",
        user_input="请分析这份销售数据并给出优化建议",
        context={
            "data_type": "sales_data",
            "time_range": "2024-01-01 to 2024-12-31",
            "analysis_depth": "detailed"
        }
    )
    
    # 智能工作流验证时间较长
    await asyncio.sleep(3)
    
    report = await validator.get_validation_report(validation_id)
    
    print("智能工作流验证结果:")
    print(f"双线闭环完整性: {report.summary.get('dual_loop_integrity', 'N/A')}")
    print(f"RAG步骤完成率: {report.summary.get('rag_completion_rate', 0):.1%}")
    print(f"专家模块调用次数: {report.summary.get('expert_calls', 0)}")

if __name__ == "__main__":
    asyncio.run(intelligent_workflow_validation())
```

## 高级功能示例

### 监控和告警集成

```python
import asyncio
from datetime import datetime
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

class MonitoringSystem:
    """模拟监控系统"""
    
    def __init__(self):
        self.events = []
    
    def log_event(self, event_type: str, data: dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.events.append(event)
        print(f"[监控系统] {event_type}: {data}")
    
    def send_alert(self, alert: dict):
        print(f"[告警系统] {alert['severity']}告警: {alert['message']}")

async def monitoring_integration_example():
    """监控系统集成示例"""
    monitoring_system = MonitoringSystem()
    validator = WorkflowEnhancedValidator()
    
    # 添加监控回调
    def monitoring_callback(event_type: str, data: dict):
        monitoring_system.log_event(event_type, data)
    
    # 添加告警回调
    def alert_callback(alert: dict):
        monitoring_system.send_alert(alert)
    
    validator.add_monitoring_callback(monitoring_callback)
    validator.add_alert_callback(alert_callback)
    
    # 开始多个验证任务以触发监控
    validation_ids = []
    for i in range(3):
        vid = await validator.start_workflow_validation(
            workflow_id=f"monitored_workflow_{i}",
            workflow_type="direct",
            user_input=f"测试输入 {i}",
            context={"test": True}
        )
        validation_ids.append(vid)
    
    # 等待验证完成
    await asyncio.sleep(2)
    
    # 检查健康状态
    health_status = await validator.get_health_status()
    print(f"验证器健康状态: {health_status['status']}")
    
    # 获取告警信息
    alerts = validator.get_alerts(hours=1)
    print(f"最近1小时告警数: {len(alerts)}")

if __name__ == "__main__":
    asyncio.run(monitoring_integration_example())
```

### 错误处理和重试机制

```python
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def error_handling_example():
    """错误处理示例"""
    validator = WorkflowEnhancedValidator()
    
    # 添加错误处理器
    def error_handler(validation_id: str, error: Exception):
        print(f"验证 {validation_id} 发生错误: {error}")
        # 可以在这里实现重试逻辑
        # 或者发送错误通知
    
    validator.add_error_handler(error_handler)
    
    try:
        # 尝试使用无效的工作流类型
        validation_id = await validator.start_workflow_validation(
            workflow_id="error_test",
            workflow_type="invalid_type",  # 无效类型
            user_input="test",
            context={}
        )
    except Exception as e:
        print(f"验证启动失败: {e}")
        # 实现重试逻辑
        print("尝试使用有效的工作流类型...")
        
        # 重试使用有效类型
        validation_id = await validator.start_workflow_validation(
            workflow_id="error_test",
            workflow_type="direct",
            user_input="test",
            context={}
        )
    
    # 正常处理验证结果
    await asyncio.sleep(1)
    report = await validator.get_validation_report(validation_id)
    print(f"最终验证状态: {report.overall_status}")

if __name__ == "__main__":
    asyncio.run(error_handling_example())
```

## 生产环境集成示例

### 与现有系统集成

```python
import asyncio
import logging
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ProductionIntegration:
    """生产环境集成类"""
    
    def __init__(self):
        self.validator = WorkflowEnhancedValidator()
        self.setup_callbacks()
    
    def setup_callbacks(self):
        """设置生产环境回调"""
        
        # 监控回调
        def production_monitoring_callback(event_type: str, data: dict):
            logger.info(f"监控事件: {event_type}")
            
            if event_type == "validation_started":
                self.on_validation_started(data)
            elif event_type == "validation_completed":
                self.on_validation_completed(data)
            elif event_type == "performance_alert":
                self.on_performance_alert(data)
        
        # 告警回调
        def production_alert_callback(alert: dict):
            logger.warning(f"告警: {alert['message']}")
            self.send_production_alert(alert)
        
        self.validator.add_monitoring_callback(production_monitoring_callback)
        self.validator.add_alert_callback(production_alert_callback)
    
    def on_validation_started(self, data: dict):
        """验证开始处理"""
        logger.info(f"验证开始: {data['validation_id']}")
        # 可以记录到数据库或发送到监控系统
    
    def on_validation_completed(self, data: dict):
        """验证完成处理"""
        logger.info(f"验证完成: {data['validation_id']}")
        # 更新数据库状态或触发后续操作
    
    def on_performance_alert(self, data: dict):
        """性能告警处理"""
        logger.error(f"性能告警: {data}")
        # 触发自动扩容或通知运维团队
    
    def send_production_alert(self, alert: dict):
        """发送生产告警"""
        # 集成到现有的告警系统（如PagerDuty、Slack等）
        severity = alert['severity']
        message = alert['message']
        
        if severity == 'critical':
            # 发送紧急告警
            self.send_critical_alert(message)
        else:
            # 发送普通告警
            self.send_warning_alert(message)
    
    def send_critical_alert(self, message: str):
        """发送紧急告警"""
        # 实现紧急告警逻辑
        logger.critical(f"紧急告警: {message}")
    
    def send_warning_alert(self, message: str):
        """发送警告告警"""
        # 实现警告告警逻辑
        logger.warning(f"警告告警: {message}")
    
    async def validate_workflow(self, workflow_id: str, user_input: str, context: dict) -> dict:
        """验证工作流并返回结果"""
        try:
            validation_id = await self.validator.start_workflow_validation(
                workflow_id=workflow_id,
                workflow_type="intelligent",
                user_input=user_input,
                context=context
            )
            
            # 等待验证完成
            await asyncio.sleep(2)
            
            report = await self.validator.get_validation_report(validation_id)
            
            return {
                "success": True,
                "validation_id": validation_id,
                "status": report.overall_status.value,
                "duration": report.total_duration,
                "summary": report.summary
            }
            
        except Exception as e:
            logger.error(f"工作流验证失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def production_integration_example():
    """生产环境集成示例"""
    integration = ProductionIntegration()
    
    # 模拟生产环境工作流验证
    result = await integration.validate_workflow(
        workflow_id="production_chat_workflow",
        user_input="用户的生产环境查询",
        context={
            "environment": "production",
            "user_tier": "premium",
            "request_source": "web_app"
        }
    )
    
    if result["success"]:
        print(f"验证成功 - 状态: {result['status']}, 耗时: {result['duration']:.2f}秒")
        
        # 检查验证器健康状态
        health = await integration.validator.get_health_status()
        print(f"验证器健康状态: {health['status']}")
        
        # 检查统计信息
        stats = integration.validator.get_validation_stats()
        print(f"验证统计: {stats['passed_validations']}/{stats['total_validations']} 通过")
    else:
        print(f"验证失败: {result['error']}")

if __name__ == "__main__":
    asyncio.run(production_integration_example())
```

### 性能优化配置

```python
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

# 高性能配置
high_performance_config = {
    "performance_validation": {
        "max_response_time": 1.0,  # 严格的响应时间要求
        "max_memory_usage": 1024.0,  # 1GB内存限制
        "max_cpu_usage": 90.0,  # 90% CPU使用率
        "concurrent_workflows": 50,  # 高并发支持
    },
    "functional_validation": {
        "min_step_completion_rate": 0.98,  # 高完成率要求
        "max_error_rate": 0.02,  # 低错误率容忍
        "dual_loop_integrity_required": True,
    }
}

# 创建高性能验证器
high_perf_validator = WorkflowEnhancedValidator(validation_config=high_performance_config)

# 宽松配置（开发环境）
development_config = {
    "performance_validation": {
        "max_response_time": 5.0,  # 宽松的响应时间
        "max_memory_usage": 2048.0,  # 2GB内存限制
        "concurrent_workflows": 10,  # 低并发
    },
    "functional_validation": {
        "min_step_completion_rate": 0.80,  # 较低的完成率要求
        "dual_loop_integrity_required": False,  # 不要求双线闭环
    }
}

# 创建开发环境验证器
dev_validator = WorkflowEnhancedValidator(validation_config=development_config)
```

## 测试和调试

### 单元测试示例

```python
import unittest
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

class TestWorkflowValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = WorkflowEnhancedValidator()
    
    def test_basic_validation(self):
        """测试基础验证功能"""
        async def test():
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_workflow",
                workflow_type="direct",
                user_input="test",
                context={}
            )
            
            self.assertIsNotNone(validation_id)
            self.assertIsInstance(validation_id, str)
            
            # 等待验证完成
            await asyncio.sleep(1)
            
            report = await self.validator.get_validation_report(validation_id)
            self.assertIsNotNone(report)
            self.assertEqual(report.workflow_id, "test_workflow")
        
        asyncio.run(test())
    
    def test_concurrent_validations(self):
        """测试并发验证"""
        async def test():
            # 创建多个并发验证任务
            tasks = []
            for i in range(5):
                task = self.validator.start_workflow_validation(
                    workflow_id=f"concurrent_{i}",
                    workflow_type="direct",
                    user_input=f"test_{i}",
                    context={"index": i}
                )
                tasks.append(task)
            
            validation_ids = await asyncio.gather(*tasks)
            
            # 验证所有任务都成功创建
            for vid in validation_ids:
                self.assertIsNotNone(vid)
            
            # 检查并发统计
            stats = self.validator.get_validation_stats()
            self.assertGreaterEqual(stats["concurrent_validations"], 5)
        
        asyncio.run(test())
    
    def test_error_handling(self):
        """测试错误处理"""
        async def test():
            # 测试无效的工作流类型
            with self.assertRaises(Exception):
                await self.validator.start_workflow_validation(
                    workflow_id="error_test",
                    workflow_type="invalid_type",
                    user_input="test",
                    context={}
                )
        
        asyncio.run(test())

if __name__ == "__main__":
    unittest.main()
```

### 调试技巧

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 调试回调函数
def debug_callback(event_type: str, data: dict):
    print(f"[DEBUG] {event_type}: {data}")

# 在验证器中添加调试回调
validator.add_monitoring_callback(debug_callback)

# 检查内部状态
print("验证器统计:", validator.get_validation_stats())
print("健康状态:", asyncio.run(validator.get_health_status()))
print("最近告警:", validator.get_alerts(hours=1))
```

## 最佳实践

1. **合理配置参数**：根据实际业务需求调整验证参数
2. **使用异步操作**：避免阻塞主线程
3. **实现错误处理**：确保系统稳定性
4. **集成监控系统**：实时掌握验证状态
5. **定期检查健康状态**：预防潜在问题
6. **优化资源使用**：根据服务器配置调整并发数

## 故障排除

### 常见问题

1. **验证超时**：检查`max_response_time`配置
2. **内存不足**：调整`max_memory_usage`配置
3. **并发限制**：增加`concurrent_workflows`配置
4. **验证失败**：检查工作流实现和输入数据

### 调试步骤

1. 启用详细日志
2. 检查验证器健康状态
3. 查看最近告警信息
4. 分析验证报告详情
5. 调整配置参数重新测试

---

这些示例展示了工作流验证器的各种使用场景，从基础验证到生产环境集成。根据实际需求选择合适的配置和集成方式。