# 资源自动调节器 - AI-STACK优化版

## 概述

资源自动调节器是基于AI-STACK架构优化的智能资源监控与自动调节系统，提供完整的资源管理解决方案。

### 核心特性

- 🔍 **实时监控**: CPU、内存、磁盘使用率实时监控
- ⚡ **智能分析**: 自动检测资源问题并生成调节建议
- 🤖 **自动调节**: 支持智能自动调节和手动干预
- 📊 **可视化界面**: 现代化Web界面，实时数据展示
- 🔧 **配置管理**: 动态配置调整，支持热更新
- 📈 **统计分析**: 详细统计报告和性能指标
- 🛡️ **安全可靠**: 完善的错误处理和审计日志

## 架构设计

### 系统架构

```
资源自动调节器系统架构
├── 核心层 (Core)
│   ├── ResourceAutoAdjuster - 主调节器类
│   ├── ResourceConfig - 配置管理
│   ├── 数据模型 (ResourceIssue, AdjustmentSuggestion)
│   └── 抽象接口 (IResourceMonitor, IAdjustmentStrategy)
├── API层
│   └── RESTful API接口 (FastAPI)
├── Web层
│   └── 可视化界面 (HTML + JavaScript + Chart.js)
└── 工具层
    ├── 测试套件
    └── 部署脚本
```

### AI-STACK优化特性

1. **模块化架构**: 支持接口隔离和依赖注入
2. **配置化管理**: 统一的配置管理，支持动态调整
3. **异步处理**: 高性能异步监控和处理
4. **缓存机制**: 智能缓存减少重复计算
5. **日志系统**: 结构化日志和审计追踪
6. **错误处理**: 完善的异常处理和恢复机制

## 快速开始

### 环境要求

- Python 3.8+
- 依赖包 (见 requirements.txt)
- 支持的操作系统: Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-stack-super-enhanced/🚀 Super Agent Main Interface
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python main_resource_auto_adjuster.py
```

4. **访问界面**
- Web界面: http://localhost:8000/web
- API文档: http://localhost:8000/api/docs
- 健康检查: http://localhost:8000/health

### Docker部署

```bash
# 构建镜像
docker build -t resource-auto-adjuster .

# 运行容器
docker run -d -p 8000:8000 resource-auto-adjuster
```

## 功能详解

### 1. 资源监控

#### 监控指标
- **CPU使用率**: 实时监控CPU负载
- **内存使用率**: 监控内存使用情况
- **磁盘使用率**: 磁盘空间监控
- **进程监控**: 高资源占用进程检测

#### 监控配置
```python
# 默认配置
config = ResourceConfig()
config.set("monitoring.interval", 5)  # 监控间隔(秒)
config.set("thresholds.cpu.warning", 80)  # CPU警告阈值
config.set("thresholds.cpu.critical", 90)  # CPU危险阈值
```

### 2. 问题分析

#### 问题类型
- **CPU问题**: 高CPU使用率、进程占用过高
- **内存问题**: 内存不足、内存泄漏
- **磁盘问题**: 磁盘空间不足、IO瓶颈

#### 分析算法
```python
# 智能分析流程
1. 问题检测 → 2. 原因分析 → 3. 建议生成 → 4. 影响评估
```

### 3. 自动调节

#### 调节动作
- **清理缓存**: 释放内存缓存
- **降低优先级**: 调整进程优先级
- **终止进程**: 强制终止问题进程
- **重启服务**: 重启问题服务
- **资源重分配**: 动态资源分配

#### 调节策略
```python
# 自动调节条件
if issue.severity == "critical" and auto_adjust_enabled:
    execute_adjustment(suggestion)
```

## API接口

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/resource-adjuster/status` | GET | 获取调节器状态 |
| `/api/resource-adjuster/monitor` | POST | 执行资源监控 |
| `/api/resource-adjuster/issues` | GET | 获取问题列表 |
| `/api/resource-adjuster/issues/{id}/analyze` | POST | 分析特定问题 |
| `/api/resource-adjuster/suggestions/{id}/execute` | POST | 执行调节建议 |
| `/api/resource-adjuster/configuration` | PUT | 更新配置 |
| `/api/resource-adjuster/statistics` | GET | 获取统计信息 |

### 响应格式

```json
{
    "status": "success",
    "message": "操作成功",
    "data": {},
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## 配置说明

### 主要配置项

```yaml
# 监控配置
monitoring:
  interval: 5                    # 监控间隔(秒)
  enable_auto_adjust: true       # 启用自动调节
  auto_adjust_threshold: medium  # 自动调节阈值

# 阈值配置
thresholds:
  cpu:
    warning: 80                  # CPU警告阈值(%)
    critical: 90                 # CPU危险阈值(%)
  memory:
    warning: 85
    critical: 95
  disk:
    warning: 80
    critical: 90

# 安全配置
security:
  require_approval_for_critical: true    # 关键操作需要授权
  max_auto_adjustments_per_hour: 10      # 每小时最大自动调节次数
```

### 配置更新

通过API动态更新配置:
```bash
curl -X PUT http://localhost:8000/api/resource-adjuster/configuration \
  -H "Content-Type: application/json" \
  -d '{"monitoring.interval": 10}'
```

## 监控指标

### 性能指标
- 监控响应时间
- 缓存命中率
- 问题检测准确率
- 调节成功率

### 业务指标
- 系统可用性
- 资源利用率
- 问题解决时间
- 用户满意度

## 故障排除

### 常见问题

1. **监控数据不更新**
   - 检查psutil权限
   - 验证配置是否正确
   - 查看日志文件

2. **自动调节不生效**
   - 检查自动调节开关
   - 验证阈值配置
   - 查看审计日志

3. **API访问失败**
   - 检查端口占用
   - 验证依赖安装
   - 查看错误日志

### 日志分析

日志文件位置: `resource_auto_adjuster.log`

```bash
# 查看实时日志
tail -f resource_auto_adjuster.log

# 搜索错误日志
grep "ERROR" resource_auto_adjuster.log

# 统计监控次数
grep "监控完成" resource_auto_adjuster.log | wc -l
```

## 扩展开发

### 添加新监控指标

1. 扩展`ResourceIssueType`枚举
2. 实现新的问题检测方法
3. 添加对应的分析逻辑
4. 更新Web界面显示

### 自定义调节策略

1. 实现`IAdjustmentStrategy`接口
2. 注册到调节器中
3. 配置策略触发条件
4. 测试策略效果

### 集成外部系统

```python
# 示例: 集成告警系统
class AlertSystemIntegration:
    def send_alert(self, issue: ResourceIssue):
        # 发送告警到外部系统
        pass
```

## 性能优化

### 监控优化
- 调整监控间隔
- 启用缓存机制
- 优化数据采集

### 内存优化
- 限制历史数据存储
- 启用数据压缩
- 定期清理缓存

### 网络优化
- 启用HTTP压缩
- 优化API响应
- 减少不必要的数据传输

## 安全考虑

### 访问控制
- API访问权限控制
- 敏感操作授权
- 操作审计日志

### 数据安全
- 配置数据加密
- 敏感信息保护
- 安全传输协议

### 系统安全
- 进程权限控制
- 资源访问限制
- 安全更新机制

## 版本历史

### v1.0.0 (当前版本)
- 基础资源监控功能
- 智能问题分析
- 自动调节机制
- Web可视化界面
- RESTful API接口

### 未来规划
- 机器学习优化
- 多云资源管理
- 移动端应用
- 高级分析功能

## 贡献指南

### 代码规范
- 遵循PEP8规范
- 添加类型注解
- 编写单元测试
- 更新文档说明

### 提交流程
1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 技术支持

- 文档: 本项目README
- 问题: GitHub Issues
- 邮件: support@example.com
- 社区: 官方论坛

---

**AI-STACK资源自动调节器** - 让资源管理更智能、更高效！