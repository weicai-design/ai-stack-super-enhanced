# 工作流验证器 API 参考

## 概述

本文档详细说明工作流验证器（WorkflowEnhancedValidator）的所有公共API接口、参数、返回值和用法示例。

## 类定义

### WorkflowEnhancedValidator

工作流验证器主类，负责管理验证任务、监控状态和生成报告。

```python
class WorkflowEnhancedValidator:
    def __init__(self, validation_config: Optional[Dict[str, Any]] = None):
        """
        初始化工作流验证器
        
        Args:
            validation_config: 验证配置字典，可选
        """
```

## 核心方法

### start_workflow_validation

开始一个新的工作流验证任务。

```python
async def start_workflow_validation(
    self,
    workflow_id: str,
    workflow_type: str,
    user_input: str,
    context: Dict[str, Any]
) -> str
```

**参数：**
- `workflow_id` (str): 工作流的唯一标识符
- `workflow_type` (str): 工作流类型，支持 "intelligent" 或 "direct"
- `user_input` (str): 用户输入内容
- `context` (dict): 工作流上下文信息

**返回值：**
- `str`: 验证任务的唯一ID

**示例：**
```python
validation_id = await validator.start_workflow_validation(
    workflow_id="chat_workflow_001",
    workflow_type="intelligent",
    user_input="你好，请帮我分析这个数据",
    context={"user_id": "12345", "session_id": "abc123"}
)
```

### get_validation_report

获取指定验证任务的详细报告。

```python
async def get_validation_report(self, validation_id: str) -> WorkflowValidationReport
```

**参数：**
- `validation_id` (str): 验证任务ID

**返回值：**
- `WorkflowValidationReport`: 验证报告对象

**示例：**
```python
report = await validator.get_validation_report(validation_id)
print(f"验证状态: {report.overall_status}")
print(f"验证耗时: {report.total_duration}秒")
```

### get_validation_stats

获取验证器的全局统计信息。

```python
def get_validation_stats(self) -> Dict[str, Any]
```

**返回值：**
- `dict`: 包含验证统计信息的字典

**统计字段：**
- `total_validations`: 总验证次数
- `passed_validations`: 通过验证次数
- `failed_validations`: 失败验证次数
- `warning_validations`: 警告验证次数
- `concurrent_validations`: 当前并发验证数
- `avg_validation_time`: 平均验证时间（秒）

**示例：**
```python
stats = validator.get_validation_stats()
print(f"总验证数: {stats['total_validations']}")
print(f"成功率: {stats['passed_validations'] / stats['total_validations'] * 100:.2f}%")
```

### get_health_status

获取验证器的健康状态。

```python
async def get_health_status(self) -> Dict[str, Any]
```

**返回值：**
- `dict`: 健康状态信息字典

**健康状态字段：**
- `status`: 整体状态（"healthy", "degraded", "unhealthy"）
- `concurrent_validations`: 当前并发验证数
- `active_validations`: 活跃验证任务数
- `last_health_check`: 最后健康检查时间
- `performance_metrics`: 性能指标

**示例：**
```python
health = await validator.get_health_status()
if health['status'] == 'healthy':
    print("验证器运行正常")
else:
    print(f"验证器状态异常: {health['status']}")
```

### get_alerts

获取指定时间范围内的告警信息。

```python
def get_alerts(self, hours: int = 24) -> List[Dict[str, Any]]
```

**参数：**
- `hours` (int): 时间范围（小时），默认24小时

**返回值：**
- `list`: 告警信息列表

**告警字段：**
- `timestamp`: 告警时间
- `type`: 告警类型
- `severity`: 严重程度（"critical", "warning"）
- `message`: 告警消息
- `validation_id`: 相关验证ID（可选）

**示例：**
```python
alerts = validator.get_alerts(hours=48)
for alert in alerts:
    print(f"[{alert['timestamp']}] {alert['type']}: {alert['message']}")
```

### stop_validation

停止指定验证任务。

```python
async def stop_validation(self, validation_id: str) -> bool
```

**参数：**
- `validation_id` (str): 验证任务ID

**返回值：**
- `bool`: 是否成功停止

**示例：**
```python
success = await validator.stop_validation(validation_id)
if success:
    print("验证任务已停止")
else:
    print("停止验证任务失败")
```

## 回调函数管理

### add_monitoring_callback

添加监控回调函数。

```python
def add_monitoring_callback(self, callback: Callable[[str, Dict[str, Any]], None])
```

**参数：**
- `callback`: 回调函数，接收事件类型和数据字典

**事件类型：**
- `validation_started`: 验证开始
- `validation_completed`: 验证完成
- `validation_failed`: 验证失败
- `performance_alert`: 性能告警
- `health_check`: 健康检查

**示例：**
```python
def monitoring_handler(event_type: str, data: dict):
    print(f"监控事件: {event_type}")
    print(f"事件数据: {data}")

validator.add_monitoring_callback(monitoring_handler)
```

### add_error_handler

添加错误处理回调函数。

```python
def add_error_handler(self, handler: Callable[[str, Exception], None])
```

**参数：**
- `handler`: 错误处理函数，接收验证ID和异常对象

**示例：**
```python
def error_handler(validation_id: str, error: Exception):
    print(f"验证 {validation_id} 发生错误: {error}")
    # 发送错误通知或记录日志

validator.add_error_handler(error_handler)
```

### add_alert_callback

添加告警回调函数。

```python
def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None])
```

**参数：**
- `callback`: 告警回调函数，接收告警字典

**示例：**
```python
def alert_handler(alert: dict):
    if alert['severity'] == 'critical':
        # 发送紧急告警
        send_critical_alert(alert)
    else:
        # 发送普通告警
        send_warning_alert(alert)

validator.add_alert_callback(alert_handler)
```

## 数据类定义

### WorkflowValidationReport

验证报告数据类。

```python
@dataclass
class WorkflowValidationReport:
    workflow_id: str
    workflow_type: str
    start_time: str
    end_time: str
    total_duration: float
    validation_results: List[ValidationResult]
    overall_status: ValidationStatus
    summary: Dict[str, Any]
```

**字段说明：**
- `workflow_id`: 工作流ID
- `workflow_type`: 工作流类型
- `start_time`: 验证开始时间（ISO格式）
- `end_time`: 验证结束时间（ISO格式）
- `total_duration`: 总验证耗时（秒）
- `validation_results`: 验证结果列表
- `overall_status`: 整体验证状态
- `summary`: 验证摘要信息

### ValidationResult

单个验证结果数据类。

```python
@dataclass
class ValidationResult:
    validation_type: str
    status: ValidationStatus
    level: ValidationLevel
    message: str
    details: Dict[str, Any]
    timestamp: str
```

**字段说明：**
- `validation_type`: 验证类型
- `status`: 验证状态
- `level`: 验证级别
- `message`: 验证消息
- `details`: 详细验证信息
- `timestamp`: 验证时间戳

### 枚举类型

#### ValidationStatus

验证状态枚举。

```python
class ValidationStatus(Enum):
    PASSED = "passed"      # 验证通过
    FAILED = "failed"      # 验证失败
    WARNING = "warning"    # 验证警告
    PENDING = "pending"    # 验证待处理
```

#### ValidationLevel

验证级别枚举。

```python
class ValidationLevel(Enum):
    CRITICAL = "critical"  # 关键级别
    HIGH = "high"          # 高优先级
    MEDIUM = "medium"      # 中优先级
    LOW = "low"            # 低优先级
```

## 配置选项

### 默认配置

```python
DEFAULT_CONFIG = {
    "performance_validation": {
        "max_response_time": 2.0,
        "max_memory_usage": 512.0,
        "max_cpu_usage": 80.0,
        "concurrent_workflows": 10,
    },
    "functional_validation": {
        "min_step_completion_rate": 0.95,
        "max_error_rate": 0.05,
        "dual_loop_integrity_required": True,
    },
    "security_validation": {
        "input_validation_required": True,
        "output_sanitization_required": True,
        "access_control_enforced": True,
    },
    "reliability_validation": {
        "retry_mechanism_enabled": True,
        "circuit_breaker_enabled": True,
        "graceful_degradation_enabled": True,
    },
    "observability_validation": {
        "monitoring_enabled": True,
        "logging_enabled": True,
        "metrics_collection_enabled": True,
    }
}
```

### 自定义配置示例

```python
custom_config = {
    "performance_validation": {
        "max_response_time": 5.0,  # 放宽响应时间限制
        "concurrent_workflows": 20,  # 增加并发数
    },
    "functional_validation": {
        "dual_loop_integrity_required": False,  # 不要求双线闭环
    }
}

validator = WorkflowEnhancedValidator(validation_config=custom_config)
```

## 使用示例

### 完整工作流验证示例

```python
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def main():
    # 创建验证器实例
    validator = WorkflowEnhancedValidator()
    
    # 添加监控回调
    def monitoring_callback(event_type: str, data: dict):
        print(f"监控事件: {event_type}")
        if event_type == "validation_completed":
            print(f"验证完成: {data['validation_id']}")
    
    validator.add_monitoring_callback(monitoring_callback)
    
    # 开始验证
    validation_id = await validator.start_workflow_validation(
        workflow_id="test_workflow",
        workflow_type="intelligent",
        user_input="测试输入",
        context={"test": True}
    )
    
    # 等待验证完成
    await asyncio.sleep(2)
    
    # 获取验证报告
    report = await validator.get_validation_report(validation_id)
    
    # 打印验证结果
    print(f"验证状态: {report.overall_status}")
    print(f"验证耗时: {report.total_duration}秒")
    
    # 获取统计信息
    stats = validator.get_validation_stats()
    print(f"总验证数: {stats['total_validations']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 批量验证示例

```python
import asyncio
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def batch_validation():
    validator = WorkflowEnhancedValidator()
    
    # 批量创建验证任务
    validation_tasks = []
    for i in range(5):
        task = validator.start_workflow_validation(
            workflow_id=f"batch_workflow_{i}",
            workflow_type="direct",
            user_input=f"批量测试输入 {i}",
            context={"batch": True, "index": i}
        )
        validation_tasks.append(task)
    
    # 并发执行验证
    validation_ids = await asyncio.gather(*validation_tasks)
    
    # 等待所有验证完成
    await asyncio.sleep(3)
    
    # 收集所有验证报告
    reports = []
    for vid in validation_ids:
        report = await validator.get_validation_report(vid)
        reports.append(report)
    
    # 分析验证结果
    passed_count = sum(1 for r in reports if r.overall_status == ValidationStatus.PASSED)
    print(f"批量验证通过率: {passed_count}/{len(reports)} ({passed_count/len(reports)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(batch_validation())
```

## 错误处理

### 常见异常

- `ValidationError`: 验证过程中发生的错误
- `ValidationTimeoutError`: 验证超时错误
- `ConfigurationError`: 配置错误
- `ResourceExhaustedError`: 资源耗尽错误

### 异常处理示例

```python
from core.workflow_enhanced_validator import ValidationError

try:
    validation_id = await validator.start_workflow_validation(
        workflow_id="test",
        workflow_type="invalid_type",  # 无效类型
        user_input="test",
        context={}
    )
except ValidationError as e:
    print(f"验证错误: {e}")
    # 处理验证错误
```

## 性能优化建议

1. **合理配置并发数**：根据服务器资源调整`concurrent_workflows`
2. **优化验证配置**：根据实际需求调整验证参数
3. **使用异步回调**：避免阻塞主线程
4. **定期清理资源**：及时停止不需要的验证任务

## 版本兼容性

- Python 3.8+
- 异步/等待支持
- 类型注解支持

---

**注意**：本文档基于工作流验证器 v1.2.0 版本编写，具体实现可能随版本更新而变化。