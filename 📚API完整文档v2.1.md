# 📚 AI Stack API完整文档 v2.1

**版本**: 2.1.0  
**更新时间**: 2025-11-07  
**API总数**: 225+

---

## 📑 目录

- [快速开始](#快速开始)
- [认证授权](#认证授权)
- [RAG系统API](#rag系统api)
- [ERP系统API](#erp系统api)
- [OpenWebUI API](#openwebui-api)
- [其他系统API](#其他系统api)
- [错误码](#错误码)

---

## 🚀 快速开始

### 基础信息

| 项目 | 值 |
|------|-----|
| **基础URL** | `http://localhost` |
| **API版本** | v2.1 |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |
| **认证方式** | API Key / JWT |

### 通用响应格式

**成功响应**:
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "错误信息",
  "error_code": "ERR_CODE",
  "details": {}
}
```

---

## 🔐 认证授权

### API Key认证

**请求头**:
```http
X-API-Key: your_api_key_here
```

### JWT Token认证

**请求头**:
```http
Authorization: Bearer your_jwt_token_here
```

### 获取Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 📚 RAG系统API

**服务地址**: `http://localhost:8011`  
**接口数**: 15+

### 1. 文档摄入

#### 摄入文本文档
```http
POST /rag/ingest/text
Content-Type: application/json

{
  "text": "文档内容",
  "metadata": {
    "source": "来源",
    "author": "作者"
  },
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**响应**:
```json
{
  "success": true,
  "chunks_created": 10,
  "document_id": "doc_123"
}
```

#### 上传文件
```http
POST /rag/ingest/file
Content-Type: multipart/form-data

file: <binary>
metadata: {"source": "upload"}
```

#### 批量摄入
```http
POST /rag/ingest/batch
Content-Type: application/json

{
  "documents": [
    {"text": "文档1", "metadata": {}},
    {"text": "文档2", "metadata": {}}
  ]
}
```

---

### 2. 文档检索

#### 检索查询
```http
GET /rag/search?query=查询词&mode=hybrid&top_k=10&alpha=0.5
```

**参数**:
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | ✅ | - | 查询词 |
| mode | string | ❌ | hybrid | 检索模式: vector/keyword/hybrid |
| top_k | int | ❌ | 5 | 返回结果数 |
| alpha | float | ❌ | 0.5 | 混合检索权重(0-1) |
| highlight | bool | ❌ | false | 是否高亮 |

**响应**:
```json
[
  {
    "id": "chunk_123",
    "text": "相关内容...",
    "score": 0.95,
    "metadata": {
      "source": "document.pdf",
      "page": 1
    }
  }
]
```

---

### 3. 知识图谱

#### 构建知识图谱
```http
POST /kg/build
Content-Type: application/json

{
  "text": "文本内容",
  "extract_entities": true,
  "extract_relations": true
}
```

**响应**:
```json
{
  "entities": [
    {"name": "实体1", "type": "人物"},
    {"name": "实体2", "type": "组织"}
  ],
  "relations": [
    {"from": "实体1", "to": "实体2", "type": "属于"}
  ]
}
```

#### 查询知识图谱
```http
POST /kg/query
Content-Type: application/json

{
  "query": "查询内容",
  "depth": 2
}
```

#### 获取图谱快照
```http
GET /kg/snapshot
```

#### 导出知识图谱
```http
GET /kg/export?format=json
```

**格式**: json | graphml | cypher

---

## 💼 ERP系统API

**服务地址**: `http://localhost:8013`  
**接口数**: 60+

### 1. 客户管理

#### 创建客户
```http
POST /api/customers
Content-Type: application/json

{
  "name": "客户名称",
  "contact": "联系人",
  "phone": "13800138000",
  "email": "customer@example.com",
  "address": "地址",
  "level": "VIP"
}
```

#### 获取客户列表
```http
GET /api/customers?page=1&size=20&level=VIP
```

#### 获取客户详情
```http
GET /api/customers/{customer_id}
```

#### 更新客户
```http
PUT /api/customers/{customer_id}
Content-Type: application/json

{
  "phone": "新电话",
  "level": "SVIP"
}
```

#### 删除客户
```http
DELETE /api/customers/{customer_id}
```

---

### 2. 订单管理

#### 创建订单
```http
POST /api/orders
Content-Type: application/json

{
  "customer_id": 1,
  "product": "产品名称",
  "quantity": 100,
  "unit_price": 99.99,
  "delivery_date": "2025-11-15"
}
```

#### 获取订单列表
```http
GET /api/orders?status=pending&customer_id=1
```

#### 更新订单状态
```http
PUT /api/orders/{order_id}/status
Content-Type: application/json

{
  "status": "confirmed"
}
```

**状态枚举**: 
- `pending` - 待审核
- `confirmed` - 已确认
- `in_production` - 生产中
- `shipped` - 已发货
- `completed` - 已完成
- `cancelled` - 已取消

---

### 3. 财务管理

#### 获取财务概览
```http
GET /api/finance/summary
```

**响应**:
```json
{
  "revenue": 1000000,
  "expenses": 600000,
  "profit": 400000,
  "profit_margin": 0.40
}
```

#### 获取财务报表
```http
GET /api/finance/report?period=month&date=2025-11
```

**Period类型**: day | week | month | quarter | year

#### 收入分析
```http
GET /api/finance/analysis/revenue?start_date=2025-11-01&end_date=2025-11-07
```

#### 成本分析
```http
GET /api/finance/analysis/cost
```

#### 利润趋势
```http
GET /api/finance/trends/profit?days=30
```

---

### 4. 生产管理

#### 创建生产计划
```http
POST /api/production/plans
Content-Type: application/json

{
  "order_id": 1,
  "product": "产品",
  "quantity": 100,
  "start_date": "2025-11-08",
  "end_date": "2025-11-15"
}
```

#### 更新生产进度
```http
PUT /api/production/plans/{plan_id}/progress
Content-Type: application/json

{
  "completed_quantity": 50,
  "current_stage": "质量检验",
  "notes": "进展顺利"
}
```

#### 获取生产状态
```http
GET /api/production/status
```

---

### 5. 库存管理

#### 库存概览
```http
GET /api/inventory/summary
```

#### 入库操作
```http
POST /api/inventory/stock-in
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
POST /api/inventory/stock-out
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 50,
  "reason": "销售订单",
  "order_id": 1
}
```

#### 库存预警
```http
GET /api/inventory/alerts
```

---

## 💬 OpenWebUI API

**服务地址**: `http://localhost:3000`  
**接口数**: 40+

### 1. 上下文记忆

#### 获取会话历史
```http
GET /api/context/history/{session_id}?limit=50&offset=0
```

#### 获取会话摘要
```http
GET /api/context/summary/{session_id}
```

#### 搜索历史对话
```http
GET /api/context/search/{session_id}?query=搜索词&top_k=5
```

---

### 2. 智能提醒

#### 检测提醒
```http
POST /api/reminder/detect
Content-Type: application/json

{
  "message": "明天下午3点提醒我开会",
  "user_id": "user_001",
  "session_id": "session_001"
}
```

#### 获取活跃提醒
```http
GET /api/reminder/active/{user_id}?limit=20
```

#### 获取到期提醒
```http
GET /api/reminder/due/{user_id}
```

#### 完成提醒
```http
POST /api/reminder/{reminder_id}/complete
```

---

### 3. 对话导出

#### 导出为Markdown
```http
GET /api/export/{session_id}/markdown?include_metadata=false
```

#### 导出为JSON
```http
GET /api/export/{session_id}/json?pretty=true
```

#### 导出为HTML
```http
GET /api/export/{session_id}/html
```

#### 导出为TXT
```http
GET /api/export/{session_id}/txt
```

---

## 📈 股票交易API

**服务地址**: `http://localhost:8014`  
**接口数**: 8+

### 1. 行情查询

#### 获取股票价格
```http
GET /api/stock/price/{stock_code}
```

**示例**: `/api/stock/price/600519` (茅台)

**响应**:
```json
{
  "code": "600519",
  "name": "贵州茅台",
  "price": 1650.50,
  "change": 15.30,
  "change_percent": 0.94,
  "volume": 123456,
  "market_cap": 2070000000000
}
```

---

## 🔍 趋势分析API

**服务地址**: `http://localhost:8015`  
**接口数**: 6+

### 1. 热点追踪

#### 获取热点列表
```http
GET /api/trends/hotspots?platform=weibo&limit=20
```

**Platform**: weibo | zhihu | baidu | news

---

## 🎨 内容创作API

**服务地址**: `http://localhost:8016`  
**接口数**: 8+

### 1. 内容生成

#### 生成文章
```http
POST /api/content/generate
Content-Type: application/json

{
  "topic": "主题",
  "style": "专业",
  "length": "中等"
}
```

---

## 🤖 任务代理API

**服务地址**: `http://localhost:8017`  
**接口数**: 16+

### 1. 任务管理

#### 创建任务
```http
POST /api/tasks
Content-Type: application/json

{
  "title": "任务标题",
  "description": "任务描述",
  "priority": "high"
}
```

---

## 🛠️ 资源管理API

**服务地址**: `http://localhost:8018`  
**接口数**: 23+

### 1. 系统监控

#### 获取系统状态
```http
GET /api/system/status
```

**响应**:
```json
{
  "cpu_percent": 45.5,
  "memory_percent": 60.2,
  "disk_percent": 35.8,
  "services": {
    "rag": "running",
    "erp": "running"
  }
}
```

---

## 🧠 学习系统API

**服务地址**: `http://localhost:8019`  
**接口数**: 20+

### 1. 自动修复

#### 诊断问题
```http
POST /api/auto-fix/diagnose
Content-Type: application/json

{
  "error_message": "错误信息",
  "stack_trace": "堆栈跟踪",
  "context": {}
}
```

---

## ❌ 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| ERR_AUTH_001 | 401 | 未授权访问 |
| ERR_AUTH_002 | 403 | 权限不足 |
| ERR_VALID_001 | 422 | 参数验证失败 |
| ERR_NOT_FOUND | 404 | 资源不存在 |
| ERR_SERVER_001 | 500 | 服务器内部错误 |
| ERR_DB_001 | 500 | 数据库错误 |
| ERR_AI_001 | 503 | AI服务不可用 |

---

## 📊 API使用统计

### 请求限制

| 级别 | 限制 |
|------|------|
| 免费用户 | 100次/小时 |
| 标准用户 | 1000次/小时 |
| 企业用户 | 无限制 |

### 响应时间SLA

| API类型 | 目标 |
|---------|------|
| 查询类 | < 100ms |
| 搜索类 | < 500ms |
| AI类 | < 5s |
| 批量类 | < 10s |

---

**文档版本**: v2.1.0  
**最后更新**: 2025-11-07

