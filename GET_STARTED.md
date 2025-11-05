# 🚀 AI Stack Super Enhanced - 立即开始使用

**最后更新**: 2025-11-02

---

## ⚡ 快速启动（30秒）

### 1. 启动服务

```bash
make dev
```

或

```bash
bash scripts/dev.sh
```

### 2. 验证服务

服务启动后（约10-20秒），访问：

- **健康检查**: http://127.0.0.1:8011/readyz
- **API文档**: http://127.0.0.1:8011/docs
- **交互式文档**: http://127.0.0.1:8011/redoc

---

## 📋 首次使用步骤

### 步骤1: 检查服务状态

```bash
curl http://127.0.0.1:8011/readyz
```

预期响应：
```json
{
  "model_ok": true,
  "dim_ok": true,
  "index_docs": 0,
  "index_matrix_ok": true,
  "kg_file_exists": false,
  "ts": 1704067200.0
}
```

### 步骤2: 创建测试文档

```bash
echo "这是一个测试文档。联系邮箱: test@example.com 网址: https://example.com" > /tmp/test.txt
```

### 步骤3: 摄入文档

```bash
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/tmp/test.txt",
    "save_index": true
  }'
```

预期响应：
```json
{
  "success": true,
  "inserted": 1,
  "ids": ["doc-id-xxx"],
  "size": 1
}
```

### 步骤4: 搜索文档

```bash
curl "http://127.0.0.1:8011/rag/search?query=测试&top_k=3"
```

预期响应：
```json
{
  "items": [
    {
      "id": "doc-id-xxx",
      "score": 0.95,
      "snippet": "这是一个测试文档...",
      "path": "/tmp/test.txt"
    }
  ]
}
```

### 步骤5: 查看知识图谱

```bash
curl "http://127.0.0.1:8011/kg/snapshot"
```

预期响应包含提取的邮箱和URL信息。

---

## 🎯 常用操作

### 查看索引信息

```bash
curl http://127.0.0.1:8011/index/info
```

### 查看所有文档ID

```bash
curl http://127.0.0.1:8011/index/ids
```

### 批量摄入目录

```bash
curl -X POST "http://127.0.0.1:8011/rag/ingest_dir?dir_path=/path/to/docs&glob=**/*.txt&limit=10"
```

### 文档分组

```bash
curl "http://127.0.0.1:8011/rag/groups?k=5&max_items=100"
```

---

## 🔐 使用API密钥（可选）

如果需要启用API密钥验证：

```bash
export RAG_API_KEY=your_secret_key
make dev
```

然后在请求中添加头部：

```bash
curl -H "X-API-Key: your_secret_key" \
  -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

---

## 🐳 使用Docker启动

```bash
# 构建镜像
make docker-build

# 运行容器
docker-compose -f docker-compose.rag.yml up
```

---

## 🧪 运行测试

```bash
# 冒烟测试（需要服务运行）
make smoke

# 单元测试
make test

# 代码审计
make audit
```

---

## 📚 更多信息

- **API端点详细文档**: 查看 [API_ENDPOINTS.md](API_ENDPOINTS.md)
- **配置说明**: 查看 [CONFIGURATION.md](CONFIGURATION.md)
- **快速启动指南**: 查看 [QUICKSTART.md](QUICKSTART.md)
- **项目概览**: 查看 [README.md](README.md)

---

## ❓ 常见问题

### Q: 服务启动失败？
A: 检查：
1. Python 3.11+ 已安装
2. 依赖已安装: `pip install -r requirements.txt`
3. 端口8011未被占用: `lsof -nP -iTCP:8011`

### Q: 模型加载失败？
A: 模型会在首次使用时自动下载，确保网络连接正常。

### Q: 如何停止服务？
A: 按 `Ctrl+C` 或运行：
```bash
lsof -nP -iTCP:8011 -sTCP:LISTEN -t | xargs kill
```

---

**准备好了吗？运行 `make dev` 开始吧！** 🚀

