# 工作流验证器文档

## 概述

工作流验证器（WorkflowEnhancedValidator）是一个生产级的验证框架，用于实时验证AI工作流的执行状态、检测双线闭环完整性、监控性能指标、检测错误并自动生成验证报告。

## 核心功能

### 1. 多维度验证
- **输入验证**：验证用户输入和上下文数据的有效性
- **性能验证**：监控响应时间、内存使用、CPU使用率
- **功能验证**：验证工作流功能完整性
- **双线闭环验证**：检查智能工作流的RAG→专家→模块→专家→RAG闭环流程
- **安全验证**：验证输入验证、输出清理、访问控制
- **可靠性验证**：检查重试机制、熔断器、优雅降级
- **可观测性验证**：验证监控和日志记录功能

### 2. 实时监控和告警
- **健康监控**：60秒间隔的健康检查
- **性能告警**：并发数、成功率告警
- **错误告警**：验证错误自动告警
- **监控回调**：支持自定义监控回调函数

### 3. 统计和报告
- **实时统计**：验证总数、通过数、失败数、警告数
- **性能统计**：平均验证时间、并发验证数
- **自动报告**：JSON格式验证报告自动生成
- **告警历史**：保留最近100条告警记录

## 快速开始

### 基本使用

```python
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

# 创建验证器实例
validator = WorkflowEnhancedValidator()

# 开始工作流验证
validation_id = await validator.start_workflow_validation(
    workflow_id="test_workflow_001",
    workflow_type="intelligent",
    user_input="测试输入",
    context={"test": True}
)

# 获取验证报告
report = await validator.get_validation_report(validation_id)
print(f"验证状态: {report.overall_status}")
```

### 配置验证器

```python
# 自定义配置
config = {
    "performance_validation": {
        "max_response_time": 2.0,  # 2秒SLO
        "max_memory_usage": 512.0,  # 512MB
        "max_cpu_usage": 80.0,  # 80%
        "concurrent_workflows": 10,
    },
    "functional_validation": {
        "min_step_completion_rate": 0.95,  # 95%步骤完成率
        "max_error_rate": 0.05,  # 5%错误率
        "dual_loop_integrity_required": True,
    }
}

validator = WorkflowEnhancedValidator(validation_config=config)
```

## API参考

### 核心方法

#### `start_workflow_validation(workflow_id, workflow_type, user_input, context)`
开始工作流验证。

**参数：**
- `workflow_id` (str): 工作流ID
- `workflow_type` (str): 工作流类型（"intelligent" 或 "direct"）
- `user_input` (str): 用户输入
- `context` (dict): 上下文信息

**返回：**
- `str`: 验证ID

#### `get_validation_report(validation_id)`
获取验证报告。

**参数：**
- `validation_id` (str): 验证ID

**返回：**
- `WorkflowValidationReport`: 验证报告对象

#### `get_validation_stats()`
获取验证统计信息。

**返回：**
- `dict`: 统计信息字典

#### `get_health_status()`
获取验证器健康状态。

**返回：**
- `dict`: 健康状态信息

#### `get_alerts(hours=24)`
获取指定时间范围内的告警。

**参数：**
- `hours` (int): 时间范围（小时）

**返回：**
- `list`: 告警列表

### 回调函数

#### 添加监控回调
```python
def monitoring_callback(event_type: str, data: dict):
    print(f"监控事件: {event_type}, 数据: {data}")

validator.add_monitoring_callback(monitoring_callback)
```

#### 添加错误处理器
```python
def error_handler(validation_id: str, error: Exception):
    print(f"验证错误: {validation_id}, {error}")

validator.add_error_handler(error_handler)
```

#### 添加告警回调
```python
def alert_callback(alert: dict):
    print(f"告警: {alert}")

validator.add_alert_callback(alert_callback)
```

## 验证报告结构

验证报告包含以下字段：

```python
@dataclass
class WorkflowValidationReport:
    workflow_id: str           # 工作流ID
    workflow_type: str         # 工作流类型
    start_time: str           # 开始时间
    end_time: str             # 结束时间
    total_duration: float     # 总耗时
    validation_results: List[ValidationResult]  # 验证结果列表
    overall_status: ValidationStatus  # 整体状态
    summary: Dict[str, Any]    # 验证摘要
```

### 验证状态

- `ValidationStatus.PASSED`: 验证通过
- `ValidationStatus.FAILED`: 验证失败
- `ValidationStatus.WARNING`: 验证警告
- `ValidationStatus.PENDING`: 验证待处理

### 验证级别

- `ValidationLevel.CRITICAL`: 关键级别
- `ValidationLevel.HIGH`: 高优先级
- `ValidationLevel.MEDIUM`: 中优先级
- `ValidationLevel.LOW`: 低优先级

## 配置选项

### 性能验证配置
- `max_response_time`: 最大响应时间（秒）
- `max_memory_usage`: 最大内存使用（MB）
- `max_cpu_usage`: 最大CPU使用率（%）
- `concurrent_workflows`: 并发工作流数

### 功能验证配置
- `min_step_completion_rate`: 最小步骤完成率
- `max_error_rate`: 最大错误率
- `dual_loop_integrity_required`: 是否要求双线闭环完整性

### 安全验证配置
- `input_validation_required`: 是否要求输入验证
- `output_sanitization_required`: 是否要求输出清理
- `access_control_enforced`: 是否强制执行访问控制

### 可靠性验证配置
- `retry_mechanism_enabled`: 是否启用重试机制
- `circuit_breaker_enabled`: 是否启用熔断器
- `graceful_degradation_enabled`: 是否启用优雅降级

### 报告配置
- `auto_generate_reports`: 是否自动生成报告
- `report_format`: 报告格式（"markdown" 或 "json"）
- `save_directory`: 报告保存目录

## 测试覆盖

工作流验证器包含完整的测试套件，覆盖以下功能：

1. **基础验证功能测试**：验证基本工作流验证功能
2. **双线闭环验证测试**：测试智能工作流闭环完整性
3. **错误处理机制测试**：验证错误处理和告警功能
4. **性能监控测试**：测试健康状态和性能监控
5. **报告生成测试**：验证自动报告生成功能
6. **并发验证测试**：测试并发验证和统计功能

测试通过率：100%

## 生产就绪特性

### 1. 高可用性
- 自动健康检查
- 优雅的错误处理
- 资源限制管理

### 2. 可观测性
- 实时监控指标
- 详细的日志记录
- 告警系统

### 3. 可扩展性
- 模块化验证架构
- 自定义回调支持
- 灵活的配置系统

### 4. 安全性
- 输入验证和清理
- 访问控制验证
- 安全配置检查

## 最佳实践

### 1. 配置优化
```python
# 生产环境推荐配置
config = {
    "performance_validation": {
        "max_response_time": 3.0,  # 适当放宽响应时间
        "max_memory_usage": 1024.0,  # 1GB内存限制
        "concurrent_workflows": 20,  # 根据服务器配置调整
    },
    "functional_validation": {
        "min_step_completion_rate": 0.90,  # 90%完成率阈值
    }
}
```

### 2. 监控集成
```python
# 集成到现有监控系统
async def integration_callback(event_type: str, data: dict):
    # 发送到监控系统
    await send_to_monitoring_system({
        "type": "workflow_validation",
        "event": event_type,
        "data": data
    })

validator.add_monitoring_callback(integration_callback)
```

### 3. 告警处理
```python
# 告警集成到通知系统
async def alert_handler(alert: dict):
    if alert["severity"] == "critical":
        # 发送紧急通知
        await send_critical_alert(alert)
    elif alert["severity"] == "warning":
        # 发送警告通知
        await send_warning_alert(alert)

validator.add_alert_callback(alert_handler)
```

## 故障排除

### 常见问题

1. **验证超时**：检查性能配置中的`max_response_time`
2. **内存不足**：调整`max_memory_usage`配置
3. **并发限制**：增加`concurrent_workflows`配置
4. **验证失败**：检查工作流实现和输入数据

### 日志分析

验证器提供详细的日志信息，可通过以下方式启用：

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 版本历史

- **v1.0.0**：初始版本，基础验证功能
- **v1.1.0**：添加双线闭环验证和告警系统
- **v1.2.0**：完善监控和统计功能，达到生产水平

## 支持

如有问题或建议，请联系开发团队或查看项目文档。