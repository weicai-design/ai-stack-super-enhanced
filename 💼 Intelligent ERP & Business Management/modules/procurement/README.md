# 采购管理模块

## 模块概述

采购管理模块是企业资源规划(ERP)系统的核心组件之一，负责管理企业采购全流程，包括采购申请、审批、订单管理、供应商管理、收货管理等环节。

## 功能特性

### 核心功能
- **采购申请管理**: 创建、审批、跟踪采购申请
- **采购订单管理**: 订单创建、发送、状态跟踪
- **供应商管理**: 供应商信息维护、绩效评估
- **库存管理**: 收货、质检、入库管理
- **采购分析**: 采购数据统计、成本分析

### 高级特性
- **限流熔断**: 防止系统过载，保障服务稳定性
- **缓存机制**: 提升数据访问性能
- **健康检查**: 系统状态监控
- **配置管理**: 支持环境隔离和动态配置
- **监控告警**: 实时监控和异常告警

## 架构设计

### 三层架构
```
表示层 (API) → 业务逻辑层 → 数据访问层
```

### 核心组件
- **ProcurementManager**: 采购管理核心业务逻辑
- **RateLimiter**: 令牌桶限流器
- **CircuitBreaker**: 熔断器
- **ConfigManager**: 配置管理器
- **HealthChecker**: 健康检查器

## API接口

### 采购申请接口
- `POST /api/procurement/requests` - 创建采购申请
- `PUT /api/procurement/requests/{id}/approve` - 审批采购申请
- `GET /api/procurement/requests` - 获取采购申请列表

### 采购订单接口
- `POST /api/procurement/orders` - 创建采购订单
- `PUT /api/procurement/orders/{id}/send` - 发送订单给供应商
- `PUT /api/procurement/orders/{id}/receive` - 记录收货

### 供应商接口
- `POST /api/procurement/suppliers` - 添加供应商
- `GET /api/procurement/suppliers/{id}/performance` - 获取供应商绩效

### 系统接口
- `GET /api/procurement/health` - 健康检查
- `GET /api/procurement/config` - 获取配置

## 配置说明

### 配置文件位置
- `config/procurement.json` - 主配置文件

### 主要配置项
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "procurement_db"
  },
  "api": {
    "port": 8000,
    "rate_limit": 100,
    "circuit_breaker": {
      "failure_threshold": 5,
      "timeout": 30
    }
  },
  "cache": {
    "ttl": 300,
    "max_size": 1000
  }
}
```

## 部署说明

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (可选，用于缓存)

### 安装步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 配置数据库: 创建数据库并导入schema
3. 修改配置文件: 更新数据库连接信息
4. 启动服务: `python procurement_api.py`

### 健康检查
访问 `/api/procurement/health` 检查服务状态

## 测试说明

### 运行测试
```bash
# 运行所有测试
pytest tests/test_procurement.py -v

# 运行特定测试类
pytest tests/test_procurement.py::TestProcurementManager -v

# 运行性能测试
pytest tests/test_procurement.py::TestProcurementPerformance -v
```

### 测试覆盖
- 单元测试: 核心组件功能验证
- 集成测试: 端到端流程验证
- 性能测试: 并发和压力测试

## 监控告警

### 监控指标
- API请求成功率
- 响应时间
- 系统资源使用率
- 数据库连接状态

### 告警规则
- API错误率 > 5%
- 平均响应时间 > 2秒
- 内存使用率 > 80%
- 数据库连接失败

## 故障排除

### 常见问题
1. **数据库连接失败**: 检查配置文件中的数据库连接信息
2. **限流触发**: 检查请求频率是否超过限制
3. **熔断器开启**: 检查下游服务是否正常
4. **缓存失效**: 检查Redis连接状态

### 日志查看
日志文件位置: `logs/procurement.log`

## 版本历史

### v1.0.0 (2025-11-12)
- 基础采购管理功能
- 限流熔断机制
- 健康检查接口
- 完整测试套件

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License