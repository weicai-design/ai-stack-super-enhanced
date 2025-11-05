# 🚀 AI Stack Super Enhanced - 服务状态指南

**最后更新**: 2025-11-02

---

## 📊 服务启动状态

### ✅ 服务已启动

开发服务器已在后台启动。

---

## ⏳ 启动时间说明

### 首次启动
- **预计时间**: 60-90秒
- **原因**: 需要从HuggingFace下载句子嵌入模型（all-MiniLM-L6-v2）
- **模型大小**: 约80MB

### 后续启动
- **预计时间**: 10-20秒
- **原因**: 模型已缓存，只需加载

---

## 🔍 验证服务是否就绪

### 方法1: 检查健康端点

```bash
curl http://127.0.0.1:8011/readyz
```

**预期响应**（服务就绪时）:
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

### 方法2: 检查端口占用

```bash
lsof -nP -iTCP:8011 -sTCP:LISTEN
```

**预期输出**: 显示uvicorn进程占用8011端口

### 方法3: 访问API文档

直接在浏览器打开：
```
http://127.0.0.1:8011/docs
```

如果页面能正常加载，说明服务已就绪。

---

## 📝 服务启动后的操作

### 1. 验证服务 ✅

```bash
curl http://127.0.0.1:8011/readyz
```

### 2. 查看索引信息

```bash
curl http://127.0.0.1:8011/index/info
```

### 3. 运行快速测试 ⭐ 推荐

```bash
bash QUICK_TEST.sh
```

这个脚本会自动测试：
- 服务健康检查
- 文档摄入
- 搜索功能
- 知识图谱

### 4. 访问API文档

在浏览器打开：
- **Swagger UI**: http://127.0.0.1:8011/docs
- **ReDoc**: http://127.0.0.1:8011/redoc

---

## 🐛 常见问题

### Q: 服务启动失败？

**检查清单**:
1. Python 3.11+ 已安装
2. 依赖已安装: `pip install -r requirements.txt`
3. 端口8011未被占用: `lsof -nP -iTCP:8011`
4. 虚拟环境已激活（如果使用）

**解决方案**:
```bash
# 停止可能占用端口的进程
lsof -nP -iTCP:8011 -sTCP:LISTEN -t | xargs kill

# 重新启动
make dev
```

### Q: 模型下载失败？

**原因**: 网络连接问题或HuggingFace访问限制

**解决方案**:
1. 检查网络连接
2. 尝试使用代理
3. 手动下载模型到 `models/all-MiniLM-L6-v2/`

### Q: 服务启动很慢？

**正常情况**:
- 首次启动需要下载模型（60-90秒）
- 这是正常现象，请耐心等待

**加速方法**:
- 使用已下载的本地模型
- 确保 `models/all-MiniLM-L6-v2/` 目录存在

---

## 🛑 停止服务

### 方法1: 在启动终端按 Ctrl+C

### 方法2: 使用kill命令

```bash
# 查找进程
lsof -nP -iTCP:8011 -sTCP:LISTEN

# 停止进程
lsof -nP -iTCP:8011 -sTCP:LISTEN -t | xargs kill
```

---

## 📊 服务日志

服务日志会显示在启动终端，包含：
- 启动信息
- 模型加载状态
- 请求日志
- 错误信息（如有）

---

## ✅ 就绪检查清单

- [ ] 服务已启动（`make dev`）
- [ ] 等待30-90秒（首次启动）
- [ ] 健康检查返回JSON（`curl http://127.0.0.1:8011/readyz`）
- [ ] API文档可访问（http://127.0.0.1:8011/docs）
- [ ] 运行快速测试通过（`bash QUICK_TEST.sh`）

---

**服务启动完成后，即可开始使用！** 🎉

