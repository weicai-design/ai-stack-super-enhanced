# 快速启动指南

## 🚀 5分钟快速上手

### 1. 环境准备

```bash
# 确保Python 3.11+已安装
python3 --version

# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

**方式1: 使用开发脚本（推荐）**

```bash
bash scripts/dev.sh
```

**方式2: 使用 Makefile**

```bash
make dev        # 启动在8011端口
make api-8011   # 明确指定8011端口
make api-8001   # 或使用8001端口
make api        # 或使用8000端口
```

**方式3: 直接使用 uvicorn**

```bash
cd "📚 Enhanced RAG & Knowledge Graph"
uvicorn api.app:app --host 127.0.0.1 --port 8011 --reload
```

### 3. 验证服务

服务启动后，在浏览器访问：

- 健康检查: http://127.0.0.1:8011/readyz
- API文档: http://127.0.0.1:8011/docs
- 交互式文档: http://127.0.0.1:8011/redoc

### 4. 运行测试

```bash
# 运行冒烟测试
bash scripts/smoke.sh

# 运行单元测试
make test
```

## 📝 常用操作

### 摄取文档

```bash
# 创建一个测试文件
echo "Hello World! Contact: test@example.com" > /tmp/test.txt

# 摄取文档
curl -X POST "http://127.0.0.1:8011/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{"path":"/tmp/test.txt","save_index":true}'
```

### 搜索

```bash
# 语义搜索
curl "http://127.0.0.1:8011/rag/search?query=example&top_k=3"
```

### 查看知识图谱

```bash
# 获取知识图谱快照
curl "http://127.0.0.1:8011/kg/snapshot"
```

## 🐳 Docker 部署

### 构建和运行

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run

# 或使用 docker-compose
docker-compose -f docker-compose.rag.yml up -d
```

### 查看日志

```bash
docker-compose -f docker-compose.rag.yml logs -f
```

## 🔐 安全配置

如果需要启用API密钥认证：

```bash
export RAG_API_KEY=your_secret_key
```

然后在请求时添加头部：

```bash
curl -H "X-API-Key: your_secret_key" \
  http://127.0.0.1:8011/rag/search?query=test
```

## 📚 更多信息

查看主 README.md 了解更多详细信息。


