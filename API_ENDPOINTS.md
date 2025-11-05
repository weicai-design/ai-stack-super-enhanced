# 📡 AI Stack Super Enhanced - API端点文档

**最后更新**: 2025-11-02  
**API版本**: 1.0.0  
**基础URL**: `http://localhost:8011`

---

## 🔍 目录

- [健康检查](#健康检查)
- [RAG端点](#rag端点)
- [索引管理](#索引管理)
- [知识图谱](#知识图谱)

---

## 🏥 健康检查

### GET `/readyz`
健康检查端点，验证服务状态。

**认证**: 不需要

**响应示例**:
```json
{
  "model_ok": true,
  "dim_ok": true,
  "index_docs": 10,
  "index_matrix_ok": true,
  "kg_file_exists": true,
  "ts": 1704067200.0
}
```

---

## 📚 RAG端点

### POST `/rag/ingest`
摄入文本或文件到RAG索引。

**认证**: 需要（如果设置了RAG_API_KEY）

**请求体**:
```json
{
  "path": "/path/to/file.txt",  // 可选：文件路径
  "text": "文档内容",              // 可选：直接文本
  "doc_id": "custom-id",          // 可选：文档ID
  "save_index": true,             // 可选：是否保存索引
  "chunk_size": 1000,             // 可选：分块大小
  "chunk_overlap": 200,           // 可选：分块重叠
  "upsert": false                 // 可选：是否更新已存在文档
}
```

**响应**:
```json
{
  "success": true,
  "inserted": 1,
  "ids": ["doc-id-123"],
  "size": 10
}
```

---

### POST `/rag/ingest_file`
上传文件并摄入到RAG索引。

**认证**: 需要（如果设置了RAG_API_KEY）

**参数**:
- `file`: 上传的文件（multipart/form-data）
- `save_index`: bool（默认: true）
- `doc_id`: string（可选）
- `chunk_size`: int（可选）
- `chunk_overlap`: int（默认: 0）
- `upsert`: bool（默认: false）

---

### POST `/rag/ingest_dir`
批量摄入目录中的文件到RAG索引。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `dir_path`: string（必需）
- `glob`: string（默认: "**/*.txt"）
- `save_index`: bool（默认: true）
- `limit`: int（可选）
- `chunk_size`: int（可选）
- `chunk_overlap`: int（默认: 0）

---

### GET `/rag/search`
语义搜索RAG索引中的文档。

**认证**: 不需要

**查询参数**:
- `query`: string（必需，最小长度: 1）
- `top_k`: int（默认: 5，范围: 1-50）

**响应示例**:
```json
{
  "items": [
    {
      "id": "doc-id-1",
      "score": 0.95,
      "snippet": "文档片段...",
      "path": "/path/to/file.txt"
    }
  ]
}
```

---

### GET `/rag/groups`
对索引中的文档进行语义分组。

**认证**: 不需要

**查询参数**:
- `k`: int（默认: 3，范围: 1-50）- 分组数量
- `max_items`: int（默认: 100，范围: 1-1000）- 最大处理文档数

---

## 📇 索引管理

### GET `/index/info`
获取索引信息。

**认证**: 不需要

**响应**:
```json
{
  "size": 10,
  "dimension": 384,
  "backend": "InMemory"
}
```

---

### GET `/index/ids`
获取所有文档ID列表。

**认证**: 不需要

**响应**:
```json
{
  "ids": ["doc-1", "doc-2", "doc-3"]
}
```

---

### DELETE `/index/clear`
清空索引和可选的知识图谱。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `remove_file`: bool（默认: true）- 是否删除磁盘文件
- `clear_kg`: bool（默认: true）- 是否同时清空知识图谱

---

### POST `/index/save`
保存索引到磁盘。

**认证**: 需要（如果设置了RAG_API_KEY）

---

### POST `/index/load`
从磁盘加载索引。

**认证**: 需要（如果设置了RAG_API_KEY）

---

### DELETE `/index/delete`
根据ID删除文档。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `doc_id`: string（必需，最小长度: 1）

---

### POST `/index/rebuild`
重建索引（重新计算所有向量）。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `reload_docs`: bool（默认: true）- 是否从磁盘重新加载文档
- `batch`: int（默认: 256，范围: 1-4096）- 批处理大小
- `save_index`: bool（默认: true）- 重建后是否保存索引

---

## 🕸️ 知识图谱

### GET `/kg/snapshot`
获取知识图谱快照。

**认证**: 不需要

**响应**:
```json
{
  "success": true,
  "nodes": 50,
  "edges": 100,
  "entities": [...],
  "sample": {
    "emails": ["test@example.com"],
    "urls": ["https://example.com"]
  }
}
```

---

### POST `/kg/save`
保存知识图谱到文件。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `path`: string（可选）- 保存路径

---

### DELETE `/kg/clear`
清空知识图谱。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `remove_file`: bool（默认: true）- 是否删除磁盘文件

---

### POST `/kg/load`
从文件加载知识图谱。

**认证**: 需要（如果设置了RAG_API_KEY）

**查询参数**:
- `path`: string（可选）- 加载路径

---

### GET `/kg/stats`
获取知识图谱统计信息。

**认证**: 不需要

**响应**:
```json
{
  "nodes": 50,
  "edges": 100,
  "ok": true
}
```

---

### GET `/kg/query`
查询知识图谱中关联到特定实体的文档。

**认证**: 不需要

**查询参数**:
- `type`: string（必需，模式: `^(email|url)$`）- 实体类型
- `value`: string（必需，最小长度: 3）- 实体值

**响应**:
```json
{
  "success": true,
  "docs": ["doc-id-1", "doc-id-2"],
  "count": 2
}
```

---

## 🔐 认证

如果设置了`RAG_API_KEY`环境变量，以下端点需要认证：

- 所有`POST`端点（除了`/readyz`）
- 所有`DELETE`端点

**请求头**:
```
X-API-Key: your_secret_key_here
```

**示例**:
```bash
curl -H "X-API-Key: your_secret_key" \
  -X POST "http://localhost:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

---

## 📖 交互式文档

启动服务后，访问：

- **Swagger UI**: http://localhost:8011/docs
- **ReDoc**: http://localhost:8011/redoc

---

## 🔗 相关文档

- [README.md](README.md) - 项目概览
- [QUICKSTART.md](QUICKSTART.md) - 快速启动指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置文档

---

**API文档版本**: 1.0.0  
**最后更新**: 2025-11-02

