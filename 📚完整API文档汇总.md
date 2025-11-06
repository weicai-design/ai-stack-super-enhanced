# AI Stack 完整API文档汇总

> 生成时间：2025-01-06  
> 版本：v2.0  
> 总完成度：90%

---

## 目录

1. [RAG知识检索系统 API](#1-rag知识检索系统-api)
2. [ERP企业管理系统 API](#2-erp企业管理系统-api)
3. [股票智能交易系统 API](#3-股票智能交易系统-api)
4. [趋势分析系统 API](#4-趋势分析系统-api)
5. [内容创作系统 API](#5-内容创作系统-api)
6. [智能任务代理 API](#6-智能任务代理-api)
7. [资源管理系统 API](#7-资源管理系统-api)
8. [自我学习系统 API](#8-自我学习系统-api)
9. [AI交互中心 API](#9-ai交互中心-api)

---

## 1. RAG知识检索系统 API

**基础URL**: `http://localhost:8011`  
**Swagger文档**: `http://localhost:8011/docs`

### 1.1 文档管理

#### 上传文档
```http
POST /api/documents/upload
Content-Type: multipart/form-data

参数:
- file: 文档文件（支持60+种格式）
- metadata: JSON格式元数据

返回:
{
  "document_id": "DOC001",
  "status": "success",
  "chunks": 120
}
```

#### 获取文档列表
```http
GET /api/documents/list?category=技术&limit=20

返回:
{
  "documents": [...],
  "total": 50
}
```

### 1.2 知识检索

#### RAG检索
```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "如何使用RAG系统？",
  "top_k": 5,
  "rerank": true
}

返回:
{
  "results": [
    {
      "content": "...",
      "score": 0.95,
      "source": "doc1.pdf",
      "page": 3
    }
  ]
}
```

### 1.3 知识图谱

#### 查询实体关系
```http
GET /api/knowledge-graph/relations?entity=RAG&max_depth=2

返回:
{
  "entity": "RAG",
  "relations": [
    {"type": "belongs_to", "target": "NLP"},
    {"type": "uses", "target": "向量数据库"}
  ]
}
```

---

## 2. ERP企业管理系统 API

**基础URL**: `http://localhost:8013`  
**Swagger文档**: `http://localhost:8013/docs`

### 2.1 客户管理

#### 创建客户
```http
POST /api/customers/create
Content-Type: application/json

{
  "name": "示例公司",
  "contact": "张经理",
  "phone": "13800138000",
  "category": "重点客户"
}
```

#### 客户价值分析
```http
GET /api/customers/{customer_id}/analysis

返回:
{
  "customer_id": 1,
  "value_score": 85,
  "total_orders": 50,
  "total_amount": 500000,
  "category": "重点客户"
}
```

### 2.2 订单管理

#### 创建订单
```http
POST /api/orders/create

{
  "customer_id": 1,
  "products": [
    {"product_id": 1, "quantity": 100, "price": 50}
  ],
  "total_amount": 5000
}
```

#### 订单趋势分析
```http
GET /api/orders/trend?period=month

返回:
{
  "trend": "上升",
  "growth_rate": 15.5,
  "period_data": [...]
}
```

### 2.3 生产管理

#### 创建生产计划
```http
POST /api/production/plans/create

{
  "order_id": "ORD001",
  "product_id": 1,
  "quantity": 1000,
  "start_date": "2025-01-10",
  "end_date": "2025-01-20"
}
```

### 2.4 财务管理

#### 生成财务报表
```http
POST /api/finance/reports/generate

{
  "report_type": "profit_loss",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}

返回:
{
  "report_id": "FIN001",
  "revenue": 1000000,
  "cost": 600000,
  "profit": 400000,
  "profit_margin": 40.0
}
```

---

## 3. 股票智能交易系统 API

**基础URL**: `http://localhost:8014`

### 3.1 市场数据

#### 获取实时行情
```http
GET /api/market/quote/{symbol}

返回:
{
  "symbol": "000001.SZ",
  "price": 12.50,
  "change": 2.3,
  "volume": 1000000
}
```

### 3.2 策略分析

#### 策略回测
```http
POST /api/strategy/backtest

{
  "strategy_name": "trend_following",
  "symbol": "000001.SZ",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000
}

返回:
{
  "total_return": 25.5,
  "sharpe_ratio": 1.8,
  "max_drawdown": -8.5
}
```

### 3.3 交易执行

#### 下单
```http
POST /api/trade/order

{
  "symbol": "000001.SZ",
  "action": "buy",
  "quantity": 1000,
  "price": 12.50,
  "order_type": "limit"
}
```

---

## 4. 趋势分析系统 API

**基础URL**: `http://localhost:8015`

### 4.1 热点追踪

#### 获取实时热点
```http
GET /api/trends/hotspots?platform=微博&limit=10

返回:
{
  "hotspots": [
    {
      "keyword": "AI芯片",
      "heat": 95,
      "trend": "上升",
      "related_topics": [...]
    }
  ]
}
```

### 4.2 报告生成

#### 生成行业报告
```http
POST /api/reports/industry

{
  "industry": "AI芯片",
  "companies": ["英伟达", "AMD"],
  "period": "month"
}

返回:
{
  "report_id": "REP001",
  "file_path": "reports/AI芯片行业报告.md"
}
```

---

## 5. 内容创作系统 API

**基础URL**: `http://localhost:8016`

### 5.1 内容生成

#### AI创作内容
```http
POST /api/content/create

{
  "topic": "AI技术应用",
  "platform": "小红书",
  "style": "干货分享",
  "length": 500
}

返回:
{
  "content_id": "CNT001",
  "title": "3分钟了解AI如何改变生活",
  "content": "...",
  "tags": ["AI", "科技"]
}
```

### 5.2 平台发布

#### 发布到平台
```http
POST /api/publish/xiaohongshu

{
  "content_id": "CNT001",
  "schedule_time": "2025-01-06 20:00:00"
}
```

### 5.3 效果追踪

#### 追踪内容效果
```http
GET /api/analytics/effect/{content_id}

返回:
{
  "views": 1250,
  "likes": 89,
  "comments": 23,
  "engagement_rate": 8.9
}
```

---

## 6. 智能任务代理 API

**基础URL**: `http://localhost:8017`

### 6.1 任务管理

#### 创建任务
```http
POST /api/tasks/create

{
  "name": "自动化营销任务",
  "steps": [
    {"action": "trend_analysis", "params": {...}},
    {"action": "content_create", "params": {...}},
    {"action": "publish", "params": {...}}
  ],
  "auto_execute": true
}
```

#### 监控任务执行
```http
GET /api/tasks/{task_id}/status

返回:
{
  "task_id": "TASK001",
  "status": "executing",
  "progress": 60,
  "current_step": 2,
  "total_steps": 3
}
```

---

## 7. 资源管理系统 API

**基础URL**: `http://localhost:8018`

### 7.1 系统监控

#### 获取系统状态
```http
GET /api/system/status

返回:
{
  "cpu_usage": 45.2,
  "memory_usage": 68.5,
  "disk_usage": 55.0,
  "network_io": {...}
}
```

### 7.2 性能优化

#### 触发优化
```http
POST /api/optimize/performance

{
  "target": "database",
  "auto_apply": false
}
```

---

## 8. 自我学习系统 API

**基础URL**: `http://localhost:8019`

### 8.1 问题诊断

#### 诊断问题
```http
POST /api/auto-fix/diagnose

{
  "error_type": "PerformanceIssue",
  "message": "API响应时间超过阈值",
  "stack_trace": "..."
}

返回:
{
  "problem_id": "PROB001",
  "root_cause": "数据库查询未优化",
  "solutions": [...]
}
```

### 8.2 代码修复

#### 生成修复代码
```http
POST /api/auto-fix/generate

{
  "problem_id": "PROB001"
}

返回:
{
  "fix_id": "FIX001",
  "code": "...",
  "description": "添加数据库索引",
  "impact": "响应时间减少90%"
}
```

#### 执行修复
```http
POST /api/auto-fix/execute

{
  "fix_id": "FIX001",
  "user_approved": true
}
```

---

## 9. AI交互中心 API

**基础URL**: `http://localhost:8020`

### 9.1 对话管理

#### 发送消息
```http
POST /api/chat

{
  "message": "帮我分析一下市场趋势",
  "context_id": "CTX001"
}

返回:
{
  "response": "...",
  "context_id": "CTX001",
  "actions": [...]
}
```

### 9.2 语音功能

#### TTS文本转语音
```http
POST /api/voice/tts

{
  "text": "你好，这是测试",
  "voice": "zh-CN-tingting"
}
```

---

## API使用示例

### Python示例

```python
import httpx
import asyncio

async def example():
    # RAG检索
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8011/api/rag/search",
            json={"query": "如何使用RAG？", "top_k": 5}
        )
        print(response.json())

asyncio.run(example())
```

### cURL示例

```bash
# 获取股票行情
curl http://localhost:8014/api/market/quote/000001.SZ

# 创建ERP客户
curl -X POST http://localhost:8013/api/customers/create \
  -H "Content-Type: application/json" \
  -d '{"name":"测试公司","contact":"张三"}'
```

---

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 速率限制

- 默认：每分钟60次请求
- VIP用户：每分钟300次请求
- 批量操作：每分钟10次请求

---

## 联系方式

- **项目地址**: `/Users/ywc/ai-stack-super-enhanced`
- **统一控制台**: `file:///.../unified-dashboard/index.html`
- **技术支持**: 查看各模块README.md

---

**更新日志**:
- 2025-01-06: v2.0版本发布，新增50+个API
- 2024-12-30: v1.5版本发布，优化响应速度
- 2024-12-20: v1.0初始版本

