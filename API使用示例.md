# 🚀 AI Stack Super Enhanced - API使用示例

**生成时间**: 2025-11-04

---

## 📌 ERP系统

### 财务数据查询

**描述**: 获取月度财务看板数据

**URL**: `http://localhost:8013/api/finance/dashboard`  
**方法**: `GET`

**参数**: 
```json
{
  "period_type": "monthly"
}
```

**Curl命令**:
```bash
curl "http://localhost:8013/api/finance/dashboard?period_type=monthly"
```

---

### 创建财务记录

**描述**: 创建新的财务记录

**URL**: `http://localhost:8013/api/finance/data`  
**方法**: `POST`

**请求体**: 
```json
{
  "date": "2025-11-04",
  "category": "revenue",
  "amount": 50000,
  "description": "测试收入"
}
```

**Curl命令**:
```bash
curl -X POST http://localhost:8013/api/finance/data \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-11-04",
    "category": "revenue",
    "amount": 50000,
    "description": "测试收入"
  }'

```

---

## 📌 股票系统

### 获取股票列表

**描述**: 获取所有股票列表

**URL**: `http://localhost:8014/api/stocks/list`  
**方法**: `GET`

**Curl命令**:
```bash
curl "http://localhost:8014/api/stocks/list"
```

---

### 获取实时行情

**描述**: 获取苹果股票实时行情

**URL**: `http://localhost:8014/api/stocks/realtime/AAPL`  
**方法**: `GET`

**Curl命令**:
```bash
curl "http://localhost:8014/api/stocks/realtime/AAPL"
```

---

## 📌 RAG系统

### 上传文档

**描述**: 上传文本到RAG知识库

**URL**: `http://localhost:8011/rag/ingest`  
**方法**: `POST`

**Curl命令**:
```bash
curl -X POST http://localhost:8011/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一个测试文档",
    "metadata": {"source": "test"}
  }'

```

---

### 检索文档

**描述**: 从知识库检索相关文档

**URL**: `http://localhost:8011/rag/retrieve`  
**方法**: `POST`

**请求体**: 
```json
{
  "query": "测试查询",
  "limit": 5
}
```

**Curl命令**:
```bash
curl -X POST http://localhost:8011/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试查询",
    "limit": 5
  }'

```

---

