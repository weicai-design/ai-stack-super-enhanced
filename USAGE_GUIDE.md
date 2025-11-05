# 📖 AI Stack Super Enhanced - 使用指南

**更新时间**: 2025-11-02

---

## 🎉 恭喜！系统已就绪

您的 AI Stack Super Enhanced 已成功运行，现在可以开始使用了！

---

## 🚀 立即可以做的事情

### 1. 📝 摄入您的文档

**方式A: 通过API摄入文件**
```bash
# 创建测试文档
echo "这是重要文档：联系邮箱 support@company.com" > /tmp/my-doc.txt

# 摄入文档
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/tmp/my-doc.txt",
    "save_index": true
  }'
```

**方式B: 直接上传文件**
```bash
curl -X POST "http://127.0.0.1:8011/rag/ingest_file" \
  -F "file=@/path/to/your/document.txt" \
  -F "save_index=true"
```

**方式C: 批量摄入目录**
```bash
curl -X POST "http://127.0.0.1:8011/rag/ingest_dir?dir_path=/path/to/docs&glob=**/*.txt"
```

---

### 2. 🔍 搜索您的知识库

```bash
# 简单搜索
curl "http://127.0.0.1:8011/rag/search?query=邮箱&top_k=5"

# 搜索特定主题
curl "http://127.0.0.1:8011/rag/search?query=技术支持&top_k=3"
```

---

### 3. 🕸️ 查看知识图谱

```bash
# 查看完整快照
curl "http://127.0.0.1:8011/kg/snapshot"

# 查询特定实体
curl "http://127.0.0.1:8011/kg/query?type=email&value=support@company.com"
```

---

### 4. 📊 管理索引

```bash
# 查看索引信息
curl "http://127.0.0.1:8011/index/info"

# 保存索引（手动保存）
curl -X POST "http://127.0.0.1:8011/index/save"

# 重建索引（从磁盘重新加载）
curl -X POST "http://127.0.0.1:8011/index/rebuild"
```

---

## 🎨 实际使用场景

### 场景1: 构建公司知识库

```bash
# 1. 摄入公司文档目录
curl -X POST "http://127.0.0.1:8011/rag/ingest_dir?dir_path=~/Documents/company&glob=**/*.md"

# 2. 搜索相关信息
curl "http://127.0.0.1:8011/rag/search?query=公司政策&top_k=5"

# 3. 提取联系信息
curl "http://127.0.0.1:8011/kg/query?type=email"
```

### 场景2: 个人文档管理

```bash
# 摄入个人笔记
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我的重要笔记：项目截止日期是2025-12-31，负责人：张三",
    "save_index": true
  }'

# 搜索笔记
curl "http://127.0.0.1:8011/rag/search?query=项目截止日期"
```

### 场景3: 代码库文档搜索

```bash
# 摄入项目README和文档
curl -X POST "http://127.0.0.1:8011/rag/ingest_dir?dir_path=./docs&glob=**/*.md"

# 搜索代码相关文档
curl "http://127.0.0.1:8011/rag/search?query=API使用示例&top_k=3"
```

---

## 🔧 高级功能

### 1. 启用API密钥保护

```bash
# 设置环境变量
export RAG_API_KEY="your-secret-key"

# 重启服务
make dev

# 使用API Key访问
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "测试文档"}'
```

### 2. 文档分块处理

```bash
# 大文档自动分块（每块500字符，重叠50字符）
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/large-doc.txt",
    "chunk_size": 500,
    "chunk_overlap": 50,
    "save_index": true
  }'
```

### 3. 更新已有文档

```bash
# 使用upsert更新文档（如果doc_id已存在）
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "更新后的内容",
    "doc_id": "existing-doc-id",
    "upsert": true,
    "save_index": true
  }'
```

---

## 🌐 Web界面

访问交互式API文档：
```
http://127.0.0.1:8011/docs
```

在浏览器中：
- ✅ 查看所有API端点
- ✅ 测试API功能
- ✅ 查看请求/响应示例

---

## 📋 常用命令速查

```bash
# 启动服务
make dev

# 停止服务（Ctrl+C 或）
pkill -f "uvicorn.*api.app"

# 快速测试
bash QUICK_TEST.sh

# 冒烟测试
make smoke

# 查看服务状态
curl http://127.0.0.1:8011/readyz
```

---

## 🎯 下一步建议

### 短期（今天）
1. ✅ 摄入一些实际文档
2. ✅ 尝试搜索功能
3. ✅ 探索API文档界面

### 中期（本周）
1. 📚 构建您的知识库
2. 🔍 测试不同搜索场景
3. 🕸️ 查看知识图谱可视化

### 长期（本月）
1. 🔒 配置API密钥保护
2. 🚀 部署到生产环境
3. 🔌 集成到其他系统

---

## 💡 技巧和最佳实践

1. **定期保存索引**
   - 使用 `save_index: true` 选项
   - 或手动调用 `/index/save`

2. **合理使用分块**
   - 大文档使用 `chunk_size` 参数
   - 建议大小：300-500字符

3. **利用知识图谱**
   - 自动提取邮箱、URL、电话等
   - 使用 `/kg/query` 查找实体

4. **性能优化**
   - 批量摄入使用 `/rag/ingest_dir`
   - 限制搜索结果数量（top_k）

---

## 🆘 遇到问题？

1. **检查服务状态**
   ```bash
   curl http://127.0.0.1:8011/readyz
   ```

2. **查看日志**
   ```bash
   tail -f /tmp/ai-stack-service-final.log
   ```

3. **重新启动服务**
   ```bash
   pkill -f uvicorn
   make dev
   ```

---

**开始探索您的AI知识库吧！** 🚀

