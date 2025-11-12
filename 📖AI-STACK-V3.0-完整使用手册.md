# 📖 AI-STACK V3.0 完整使用手册

**版本**: V3.0 融合版  
**更新时间**: 2025-11-09  
**适用对象**: 所有用户

---

## 🎯 快速开始

### 访问系统

```
主控制台:     http://localhost:8000/
API文档:      http://localhost:8000/docs
中文指南:     http://localhost:8000/guide
系统健康:     http://localhost:8000/health
```

### 10大功能模块

```
1. 📚 RAG知识图谱    http://localhost:8000/docs#/RAG
2. 💰 财务管理        http://localhost:8000/finance/
3. ⚙️ 运营管理        http://localhost:8000/operations/
4. 🏭 ERP系统         http://localhost:8000/erp/
5. 📈 股票交易        http://localhost:8000/stock/
6. ✍️ 内容创作        http://localhost:8000/content/
7. 📊 趋势分析        http://localhost:8000/trend/
8. 💬 AI交互中心      http://localhost:8000/interaction/
9. 📋 智能任务        http://localhost:8000/tasks/
10. 🔧 系统管理       http://localhost:8000/learning/
```

---

## 📚 模块使用指南

### 1. RAG和知识图谱

**主要功能**:
- 文档上传和检索
- 语义搜索
- 知识图谱构建
- 智能问答

**使用示例**:
```bash
# 搜索知识
curl "http://localhost:8000/rag/search?query=人工智能&top_k=5"

# 导入文档
curl -X POST http://localhost:8000/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "这是一段测试文本"}'

# 查看知识图谱
curl http://localhost:8000/kg/stats
```

---

### 2. 财务管理系统

**主要功能**:
- 财务数据导入导出
- 盈亏分析
- 财务看板（日/周/月/季/年）
- 经营建议

**使用示例**:
```bash
# 获取财务看板
curl http://localhost:8000/finance/dashboard

# 盈亏分析
curl "http://localhost:8000/finance/analysis/profit?period=monthly"

# 导入财务数据
curl -X POST http://localhost:8000/finance/import \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "date": "2025-11-09",
      "period": "monthly",
      "revenue": 100000,
      "cost_of_goods_sold": 60000
    },
    "data_type": "income_statement"
  }'
```

---

### 3. 运营管理系统

**主要功能**:
- 流程定义和管理
- 全流程业务管理（16个阶段）
- 进度监控
- 问题收集和闭环

**使用示例**:
```bash
# 获取运营看板
curl http://localhost:8000/operations/dashboard

# 查询业务流程
curl http://localhost:8000/operations/processes

# 获取统计数据
curl "http://localhost:8000/operations/statistics?period=month"
```

---

### 4. ERP系统

**主要功能**:
- 客户管理（CRM）
- 订单管理
- 项目管理
- 采购/物料/生产/质量/仓储/交付

**使用示例**:
```bash
# 添加客户
curl -X POST http://localhost:8000/erp/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试公司",
    "industry": "制造业",
    "contact_person": "张三",
    "credit_level": "A"
  }'

# 创建订单
curl -X POST http://localhost:8000/erp/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "xxx",
    "order_no": "ORDER001",
    "product_name": "产品A",
    "quantity": 100,
    "unit_price": 1000,
    "order_date": "2025-11-09"
  }'

# 获取统计
curl http://localhost:8000/erp/stats
```

---

### 5. 股票交易系统

**主要功能**:
- 股票数据采集（A/B/H股）
- 交易策略管理
- 自动交易
- 收益分析

**使用示例**:
```bash
# 获取股票数据
curl "http://localhost:8000/stock/data/000001?market=A"

# 添加交易策略
curl -X POST http://localhost:8000/stock/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "价值投资策略",
    "description": "长期持有优质股票",
    "rules": {
      "buy_price": 10.0,
      "sell_price": 15.0,
      "max_loss": 0.1
    }
  }'

# 查看投资组合
curl http://localhost:8000/stock/portfolio
```

---

### 6. 内容创作系统

**主要功能**:
- 素材收集
- 自动创作
- 多平台发布
- 效果跟踪

**使用示例**:
```bash
# 收集素材
curl -X POST http://localhost:8000/content/materials/collect-web \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["AI", "科技", "创新"]}'

# 创作内容
curl -X POST http://localhost:8000/content/contents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI技术最新趋势",
    "body": "内容正文...",
    "platform": "zhihu"
  }'

# 获取内容列表
curl http://localhost:8000/content/contents
```

---

### 7. 趋势分析系统

**主要功能**:
- 信息爬取
- 数据处理分析
- 报告生成

**使用示例**:
```bash
# 爬取新闻
curl -X POST http://localhost:8000/trend/data/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "category": "technology",
    "keywords": ["AI", "机器学习"]
  }'

# 处理分析
curl -X POST http://localhost:8000/trend/analyses/process

# 获取报告列表
curl http://localhost:8000/trend/reports
```

---

### 8. AI智能交互中心

**主要功能**:
- 统一聊天窗口
- 功能路由
- 命令执行

**使用示例**:
```bash
# 创建会话
curl -X POST "http://localhost:8000/interaction/sessions?user_id=user123"

# 发送消息
curl -X POST http://localhost:8000/interaction/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "帮我查询财务数据"
  }'

# 获取可用功能
curl http://localhost:8000/interaction/functions
```

---

### 9-10. 其他系统

**智能任务**:
- 任务管理: http://localhost:8000/tasks/

**学习进化**:
- 学习系统: http://localhost:8000/learning/

**资源管理**:
- 资源监控: http://localhost:8000/resource/

**专家系统**:
- 专家咨询: http://localhost:8000/expert/

---

## 🔧 系统管理

### 多租户管理

```bash
# 创建租户
curl -X POST http://localhost:8000/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试公司",
    "slug": "test-company",
    "owner_email": "admin@test.com",
    "plan": "pro"
  }'

# 查看租户列表
curl http://localhost:8000/tenants/

# 查看配额
curl http://localhost:8000/tenants/{tenant_id}/quota
```

### 缓存管理

```bash
# 查看缓存统计
curl http://localhost:8000/cache/stats

# 清除缓存
curl -X DELETE http://localhost:8000/cache/clear
```

### 限流管理

```bash
# 查看限流状态
curl http://localhost:8000/rate-limit/status

# 查看用户配额
curl http://localhost:8000/rate-limit/quota/{user_id}
```

---

## 📊 监控和统计

### 系统监控

```bash
# 系统健康检查
curl http://localhost:8000/health

# 实时统计
curl http://localhost:8000/analytics/summary

# 查看API调用统计
curl http://localhost:8000/analytics/api-calls
```

### 性能监控

```
Prometheus: http://localhost:9090
Grafana:    http://localhost:3001
```

---

## 🎯 最佳实践

### 1. 使用多租户

所有API请求都应该包含租户信息：

```bash
# 方式1: 使用请求头
curl http://localhost:8000/finance/dashboard \
  -H "X-Tenant-ID: your-tenant-id"

# 方式2: 使用查询参数
curl "http://localhost:8000/finance/dashboard?tenant_id=your-tenant-id"
```

### 2. 使用RAG增强

所有模块都可以利用RAG知识库：

```python
# 先导入领域知识到RAG
requests.post("/rag/ingest", json={"text": "财务分析领域知识..."})

# 然后在分析时自动检索
requests.get("/finance/analysis/profit")  # 会自动从RAG获取建议
```

### 3. 使用专家系统

```bash
# 获取财务专家建议
curl "http://localhost:8000/expert/advice?domain=finance&question=如何降低成本"

# 获取股票专家建议
curl "http://localhost:8000/expert/advice?domain=stock&question=是否应该买入"
```

---

## 🎊 系统特色

### 1. 统一交互

所有功能都可以通过AI交互中心统一访问，无需记忆各个模块的API。

### 2. 智能增强

所有模块都集成了RAG知识库和专家系统，提供智能建议。

### 3. 自我学习

系统会学习用户行为和使用模式，持续优化。

### 4. 企业级

多租户、数据隔离、配额管理、完整的企业级特性。

---

**📖 完整使用手册已准备好！**

**访问 http://localhost:8000/ 开始使用！** 🚀












