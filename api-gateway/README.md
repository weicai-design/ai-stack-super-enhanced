# 🌉 AI Stack API Gateway

**端口**: 9000  
**功能**: 统一API网关，连接所有AI Stack服务

---

## 🚀 快速启动

```bash
cd api-gateway

# 安装依赖
pip install -r requirements.txt

# 启动网关
python main.py
```

访问: http://localhost:9000

API文档: http://localhost:9000/docs

---

## 🔌 API端点

### 系统管理

- `GET /` - 网关信息
- `GET /health` - 健康检查
- `GET /gateway/services` - 服务列表
- `GET /gateway/status` - 所有服务状态
- `GET /gateway/stats` - 网关统计

### RAG系统

- `GET /gateway/rag/search?query=<query>&top_k=5` - 知识搜索
- `POST /gateway/rag/ingest` - 文档摄入
- `GET /gateway/kg/snapshot` - 知识图谱快照
- `GET /gateway/kg/query?query=<query>` - 图谱查询

### ERP系统

- `GET /gateway/erp/financial?period=month` - 财务数据
- `GET /gateway/erp/orders?status=<status>` - 订单查询
- `GET /gateway/erp/customers` - 客户查询
- `GET /gateway/erp/production` - 生产状态

### 股票系统

- `GET /gateway/stock/price/{code}` - 股票价格
- `GET /gateway/stock/analyze/{code}` - 策略分析
- `GET /gateway/stock/sentiment` - 市场情绪

### 内容创作

- `POST /gateway/content/generate` - 生成内容

### 任务管理

- `GET /gateway/task/list` - 任务列表

### 资源监控

- `GET /gateway/resource/stats` - 资源统计

---

## 💡 使用示例

### 搜索RAG

```bash
curl "http://localhost:9000/gateway/rag/search?query=AI技术&top_k=3"
```

### 查询ERP财务

```bash
curl "http://localhost:9000/gateway/erp/financial?period=month"
```

### 查询股票价格

```bash
curl "http://localhost:9000/gateway/stock/price/600519"
```

### 检查系统状态

```bash
curl "http://localhost:9000/gateway/status"
```

---

## 🌐 集成方式

### 方式1: OpenWebUI Functions调用

Functions可以通过API Gateway统一调用：

```python
# 在Function中
gateway_url = "http://host.docker.internal:9000"
response = await client.get(f"{gateway_url}/gateway/rag/search")
```

### 方式2: 直接API调用

任何应用都可以通过API Gateway访问AI Stack：

```javascript
// JavaScript
fetch('http://localhost:9000/gateway/rag/search?query=test')
  .then(res => res.json())
  .then(data => console.log(data));
```

```python
# Python
import requests
result = requests.get('http://localhost:9000/gateway/rag/search?query=test')
print(result.json())
```

---

## 📊 监控

### 网关统计

```bash
curl "http://localhost:9000/gateway/stats"
```

返回：
```json
{
  "requests_total": 150,
  "errors_total": 2,
  "services_count": 8,
  "uptime": "运行中"
}
```

### 服务状态

```bash
curl "http://localhost:9000/gateway/status"
```

---

## 🔧 配置

修改 `main.py` 中的服务地址：

```python
SERVICES = {
    "rag": "http://localhost:8011",
    "erp": "http://localhost:8013",
    # ...
}
```

---

## 🚀 启动网关

```bash
cd /Users/ywc/ai-stack-super-enhanced/api-gateway
python main.py
```

或使用uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

---

**创建时间**: 2025-11-04  
**端口**: 9000  
**状态**: ✅ 已完成



