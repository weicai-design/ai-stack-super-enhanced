# 📚 AI Stack API文档 v2.1

**版本**: v2.1.0  
**更新时间**: 2025-11-07  
**状态**: 生产就绪

---

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [通用规范](#通用规范)
- [RAG知识检索系统](#rag知识检索系统)
- [ERP企业管理系统](#erp企业管理系统)
- [OpenWebUI交互中心](#openwebui交互中心)
- [股票交易系统](#股票交易系统)
- [趋势分析系统](#趋势分析系统)
- [内容创作系统](#内容创作系统)
- [智能任务代理](#智能任务代理)
- [资源管理系统](#资源管理系统)
- [自我学习系统](#自我学习系统)
- [错误码](#错误码)
- [最佳实践](#最佳实践)

---

## 🎯 概述

AI Stack提供了9个核心系统的RESTful API，所有API遵循统一的设计规范。

### 基础URL

```
开发环境: http://localhost:{port}
生产环境: https://api.aistack.com
```

### 服务端口

| 服务 | 端口 | 文档URL |
|------|------|---------|
| RAG系统 | 8011 | http://localhost:8011/docs |
| ERP系统 | 8013 | http://localhost:8013/docs |
| OpenWebUI | 8020 | http://localhost:8020/docs |
| 股票交易 | 8015 | http://localhost:8015/docs |
| 趋势分析 | 8014 | http://localhost:8014/docs |
| 内容创作 | 8016 | http://localhost:8016/docs |
| 任务代理 | 8017 | http://localhost:8017/docs |
| 资源管理 | 8018 | http://localhost:8018/docs |
| 学习系统 | 8019 | http://localhost:8019/docs |

---

## 🔐 认证

### API Key认证

在请求头中包含API Key：

```http
Authorization: Bearer YOUR_API_KEY
```

### 获取API Key

```bash
POST /api/auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### OAuth2认证 (v2.1新增)

支持标准OAuth2授权码流程。

---

## 📝 通用规范

### 请求格式

- Content-Type: `application/json`
- 字符编码: `UTF-8`
- 日期格式: ISO 8601 (`2025-11-07T10:30:00Z`)

### 响应格式

成功响应：
```json
{
  "status": "success",
  "data": { },
  "timestamp": "2025-11-07T10:30:00Z"
}
```

错误响应：
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "错误描述",
    "details": {}
  },
  "timestamp": "2025-11-07T10:30:00Z"
}
```

### 分页

使用标准分页参数：

```
GET /api/resource?page=1&page_size=20
```

响应包含分页信息：
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 100,
    "total_pages": 5
  }
}
```

### 排序

```
GET /api/resource?sort=created_at&order=desc
```

### 过滤

```
GET /api/resource?filter[status]=active&filter[date_from]=2025-01-01
```

---

## 📚 RAG知识检索系统

### 基础URL
```
http://localhost:8011/api
```

### 文档摄入

#### 上传文档

```http
POST /documents/ingest
Content-Type: multipart/form-data

file: <file>
metadata: {
  "title": "文档标题",
  "category": "技术文档",
  "tags": ["AI", "机器学习"]
}
```

**响应**:
```json
{
  "document_id": "doc_12345",
  "status": "processing",
  "chunks_created": 15,
  "vectors_generated": 15
}
```

#### 批量上传

```http
POST /documents/batch-ingest
Content-Type: multipart/form-data

files: [<file1>, <file2>, ...]
```

### 知识检索

#### 语义检索

```http
POST /search/semantic
Content-Type: application/json

{
  "query": "什么是机器学习？",
  "top_k": 5,
  "filters": {
    "category": "技术文档"
  }
}
```

**响应**:
```json
{
  "results": [
    {
      "document_id": "doc_12345",
      "chunk_id": "chunk_001",
      "content": "机器学习是...",
      "score": 0.95,
      "metadata": {}
    }
  ],
  "query_time_ms": 45
}
```

#### 混合检索

```http
POST /search/hybrid
Content-Type: application/json

{
  "query": "搜索查询",
  "semantic_weight": 0.7,
  "keyword_weight": 0.3,
  "top_k": 10
}
```

### 知识图谱

#### 构建知识图谱

```http
POST /knowledge-graph/build
Content-Type: application/json

{
  "document_ids": ["doc_001", "doc_002"],
  "extract_entities": true,
  "extract_relationships": true
}
```

#### 查询知识图谱

```http
POST /knowledge-graph/query
Content-Type: application/json

{
  "query": "MATCH (n:Person)-[r:WORKS_AT]->(c:Company) RETURN n, r, c",
  "limit": 10
}
```

### 真实性验证

```http
POST /verification/verify
Content-Type: application/json

{
  "content": "待验证的内容",
  "sources": ["source1", "source2"]
}
```

**响应**:
```json
{
  "verified": true,
  "confidence": 0.92,
  "sources": [
    {
      "source": "source1",
      "support_score": 0.95
    }
  ]
}
```

---

## 💼 ERP企业管理系统

### 基础URL
```
http://localhost:8013/api
```

### 客户管理

#### 创建客户

```http
POST /customers
Content-Type: application/json

{
  "name": "客户名称",
  "contact": "联系人",
  "phone": "13800138000",
  "email": "customer@example.com",
  "address": "详细地址",
  "level": "VIP"
}
```

**响应**:
```json
{
  "customer_id": 1,
  "name": "客户名称",
  "created_at": "2025-11-07T10:30:00Z"
}
```

#### 获取客户列表

```http
GET /customers?page=1&page_size=20&level=VIP
```

#### 更新客户

```http
PUT /customers/{customer_id}
Content-Type: application/json

{
  "level": "SVIP",
  "notes": "重要客户"
}
```

### 订单管理

#### 创建订单

```http
POST /orders
Content-Type: application/json

{
  "customer_id": 1,
  "items": [
    {
      "product_id": 1,
      "quantity": 10,
      "unit_price": 99.99
    }
  ],
  "delivery_date": "2025-11-15",
  "notes": "备注"
}
```

#### 更新订单状态

```http
PUT /orders/{order_id}/status
Content-Type: application/json

{
  "status": "processing"
}
```

**订单状态**:
- `pending`: 待处理
- `processing`: 处理中
- `shipped`: 已发货
- `delivered`: 已送达
- `cancelled`: 已取消

### 生产管理

#### 创建生产计划

```http
POST /production/plans
Content-Type: application/json

{
  "order_id": 1,
  "product": "产品名称",
  "quantity": 100,
  "start_date": "2025-11-08",
  "end_date": "2025-11-15"
}
```

#### 更新生产进度

```http
PUT /production/plans/{plan_id}/progress
Content-Type: application/json

{
  "completed_quantity": 50,
  "current_stage": "加工生产"
}
```

### 库存管理

#### 获取库存概览

```http
GET /inventory/summary
```

#### 入库操作

```http
POST /inventory/stock-in
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 100,
  "warehouse": "主仓库",
  "batch_number": "BATCH20251107"
}
```

#### 出库操作

```http
POST /inventory/stock-out
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 50,
  "reason": "销售订单",
  "order_id": 1
}
```

### 财务管理

#### 获取财务概览

```http
GET /finance/overview?period=month
```

**响应**:
```json
{
  "revenue": 1000000,
  "cost": 600000,
  "profit": 400000,
  "profit_margin": 0.40,
  "period": "2025-11"
}
```

#### 生成财务报表

```http
POST /finance/reports
Content-Type: application/json

{
  "type": "monthly",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30"
}
```

---

## 💬 OpenWebUI交互中心

### 基础URL
```
http://localhost:8020/api
```

### 智能对话

#### 发送消息

```http
POST /chat/message
Content-Type: application/json

{
  "message": "你好，请帮我分析这个问题",
  "context": {
    "session_id": "session_123",
    "user_id": "user_001"
  }
}
```

**响应**:
```json
{
  "response": "AI回复内容",
  "context": {},
  "timestamp": "2025-11-07T10:30:00Z"
}
```

#### 流式响应

```http
POST /chat/stream
Content-Type: application/json

{
  "message": "生成一篇长文章",
  "stream": true
}
```

返回Server-Sent Events流。

### 上下文记忆

#### 保存上下文

```http
POST /context/save
Content-Type: application/json

{
  "session_id": "session_123",
  "context": {
    "topic": "机器学习",
    "previous_queries": []
  }
}
```

#### 获取上下文

```http
GET /context/{session_id}
```

### 智能提醒

#### 创建提醒

```http
POST /reminders
Content-Type: application/json

{
  "title": "会议提醒",
  "content": "下午3点开会",
  "remind_at": "2025-11-07T15:00:00Z"
}
```

### 对话导出

```http
GET /chat/export?session_id=session_123&format=json
```

**支持格式**: json, markdown, pdf, html

---

## 📈 股票交易系统

### 基础URL
```
http://localhost:8015/api
```

### 行情数据

#### 获取实时报价

```http
GET /stocks/{symbol}/quote
```

**响应**:
```json
{
  "symbol": "000001",
  "current_price": 15.50,
  "change": 0.50,
  "change_percent": 3.33,
  "volume": 1000000,
  "timestamp": "2025-11-07T10:30:00Z"
}
```

#### 获取历史数据

```http
GET /stocks/{symbol}/history?start=2025-01-01&end=2025-11-07
```

### 交易操作

#### 下单

```http
POST /orders
Content-Type: application/json

{
  "symbol": "000001",
  "action": "buy",
  "quantity": 100,
  "price": 15.50,
  "order_type": "limit"
}
```

**订单类型**:
- `market`: 市价单
- `limit`: 限价单
- `stop`: 止损单

#### 撤单

```http
DELETE /orders/{order_id}
```

### 投资组合

#### 获取持仓

```http
GET /portfolio/positions
```

#### 获取绩效

```http
GET /portfolio/performance?period=ytd
```

### 策略回测

```http
POST /strategies/backtest
Content-Type: application/json

{
  "strategy_id": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-10-31",
  "initial_capital": 100000
}
```

---

## 🔍 趋势分析系统

### 基础URL
```
http://localhost:8014/api
```

### 热点追踪

#### 获取热门话题

```http
GET /trends/hot-topics?platform=weibo&limit=20
```

#### 搜索趋势

```http
POST /trends/search
Content-Type: application/json

{
  "keyword": "人工智能",
  "platforms": ["weibo", "zhihu"],
  "date_range": "last_7_days"
}
```

### 情感分析

```http
POST /trends/sentiment
Content-Type: application/json

{
  "text": "这个产品非常好用"
}
```

**响应**:
```json
{
  "sentiment": "positive",
  "score": 0.92,
  "confidence": 0.95
}
```

### 报告生成

```http
POST /trends/reports
Content-Type: application/json

{
  "topic": "人工智能",
  "date_range": "last_30_days",
  "include_charts": true
}
```

---

## 🎨 内容创作系统

### 基础URL
```
http://localhost:8016/api
```

### 内容生成

#### AI生成内容

```http
POST /content/generate
Content-Type: application/json

{
  "topic": "人工智能的未来",
  "style": "professional",
  "length": "medium",
  "platform": "xiaohongshu"
}
```

#### 优化内容

```http
POST /content/optimize
Content-Type: application/json

{
  "content": "原始内容",
  "platform": "xiaohongshu",
  "target_audience": "年轻人"
}
```

### 发布管理

#### 发布内容

```http
POST /content/publish
Content-Type: application/json

{
  "content": "发布内容",
  "platform": "weibo",
  "images": ["url1", "url2"],
  "scheduled_time": "2025-11-08T10:00:00Z"
}
```

#### 获取发布统计

```http
GET /content/analytics?period=last_7_days
```

---

## 🤖 智能任务代理

### 基础URL
```
http://localhost:8017/api
```

### 任务管理

#### 创建任务

```http
POST /tasks
Content-Type: application/json

{
  "name": "任务名称",
  "description": "任务描述",
  "priority": "high",
  "deadline": "2025-11-15"
}
```

#### 任务分解

```http
POST /tasks/decompose
Content-Type: application/json

{
  "task": "开发一个Web应用"
}
```

**响应**:
```json
{
  "subtasks": [
    {
      "name": "需求分析",
      "estimated_hours": 8
    },
    {
      "name": "设计数据库",
      "estimated_hours": 4
    }
  ]
}
```

#### 执行任务

```http
POST /tasks/{task_id}/execute
```

### 任务监控

```http
GET /tasks/{task_id}/monitor
```

---

## 🛠️ 资源管理系统

### 基础URL
```
http://localhost:8018/api
```

### 资源监控

#### 获取系统指标

```http
GET /resources/metrics
```

**响应**:
```json
{
  "cpu": {
    "usage_percent": 45.5,
    "cores": 8
  },
  "memory": {
    "used": 8589934592,
    "total": 17179869184,
    "usage_percent": 50.0
  },
  "disk": {
    "used": 107374182400,
    "total": 536870912000,
    "usage_percent": 20.0
  }
}
```

### 资源分配

```http
POST /resources/allocate
Content-Type: application/json

{
  "service": "rag_system",
  "cpu": 2,
  "memory": 4096
}
```

### 性能监控

```http
GET /resources/performance?period=1h
```

---

## 🧠 自我学习系统

### 基础URL
```
http://localhost:8019/api
```

### 学习反馈

#### 记录交互

```http
POST /learning/interactions
Content-Type: application/json

{
  "user_input": "用户输入",
  "system_response": "系统响应",
  "feedback": "positive"
}
```

### 模式分析

```http
GET /learning/patterns
```

### 改进建议

```http
GET /learning/improvements
```

### 模型重训练

```http
POST /learning/retrain
Content-Type: application/json

{
  "model_type": "response_generator"
}
```

---

## ⚠️ 错误码

### HTTP状态码

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### 业务错误码

| 错误码 | 说明 |
|-------|------|
| INVALID_INPUT | 输入参数无效 |
| UNAUTHORIZED | 未授权访问 |
| RESOURCE_NOT_FOUND | 资源未找到 |
| QUOTA_EXCEEDED | 配额超限 |
| INTERNAL_ERROR | 内部错误 |
| SERVICE_UNAVAILABLE | 服务不可用 |
| RATE_LIMIT_EXCEEDED | 超过速率限制 |

---

## 💡 最佳实践

### 1. API密钥安全

- 不要在代码中硬编码API密钥
- 使用环境变量存储密钥
- 定期轮换API密钥
- 使用HTTPS传输

### 2. 错误处理

```python
import requests

try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    # 处理HTTP错误
    print(f"HTTP错误: {e}")
except requests.exceptions.RequestException as e:
    # 处理其他请求错误
    print(f"请求错误: {e}")
```

### 3. 速率限制

遵守API速率限制：
- 默认: 100请求/分钟
- 使用指数退避重试策略
- 检查响应头中的速率限制信息

### 4. 批量操作

对于大量数据，使用批量API：

```python
# 好的做法
POST /documents/batch-ingest

# 避免
for doc in docs:
    POST /documents/ingest
```

### 5. 缓存

合理使用缓存减少API调用：

```python
import requests_cache

# 启用缓存
requests_cache.install_cache('api_cache', expire_after=300)
```

### 6. 超时设置

设置合理的超时时间：

```python
response = requests.get(url, timeout=10)
```

### 7. 分页处理

```python
def get_all_items(url):
    items = []
    page = 1
    while True:
        response = requests.get(f"{url}?page={page}")
        data = response.json()
        items.extend(data['items'])
        if page >= data['pagination']['total_pages']:
            break
        page += 1
    return items
```

---

## 📞 技术支持

- 文档问题: docs@aistack.com
- API问题: api-support@aistack.com
- 技术讨论: https://github.com/aistack/issues

---

**文档版本**: v2.1.0  
**最后更新**: 2025-11-07  
**维护团队**: AI Stack Team



















