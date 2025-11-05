# 📋 AI Stack Super Enhanced - 配置文档

**最后更新**: 2025-11-02

---

## 🔧 环境变量配置

### 必需配置

无（所有配置都有默认值）

### 可选配置（含无VPN环境）

#### `RAG_API_KEY`
- **类型**: String
- **默认值**: 空（不使用API Key验证）
- **说明**: 如果设置，所有API请求需要携带匹配的`X-API-Key`请求头
- **示例**: `export RAG_API_KEY=secret123`

#### `VECTOR_BACKEND`
- **类型**: String
- **默认值**: `faiss`
- **说明**: 向量数据库后端选择
- **可选值**: `faiss`, `inmemory`

#### `LOCAL_ST_MODEL_PATH`
- **类型**: String (路径)
- **默认值**: `models/all-MiniLM-L6-v2`
- **说明**: 本地句子嵌入模型路径
- **示例**: `/app/models/all-MiniLM-L6-v2`

#### `HF_ENDPOINT`
- **类型**: String (URL)
- **默认值**: `https://hf-mirror.com`
- **说明**: 无VPN环境下使用的HuggingFace镜像端点

#### 模型缓存（无VPN推荐）
- `HF_HOME` / `HUGGINGFACE_HUB_CACHE` / `TRANSFORMERS_CACHE` / `SENTENCE_TRANSFORMERS_HOME`
- **默认值**: `models/`
- **说明**: 统一配置为本地`models/`目录，避免联网下载

#### `PYTHONPATH`
- **类型**: String (路径)
- **默认值**: 自动设置
- **说明**: Python模块搜索路径
- **示例**: `/app/📚 Enhanced RAG & Knowledge Graph`

---

## 🐳 Docker 配置

### docker-compose.rag.yml

标准开发环境配置（已包含无VPN镜像与本地缓存环境变量）：

```yaml
version: "3.9"
services:
  api:
    build:
      context: .
      args:
        PY_BASE: python:3.11-slim
    environment:
      - RAG_API_KEY=${RAG_API_KEY:-secret123}
      - VECTOR_BACKEND=faiss
      - LOCAL_ST_MODEL_PATH=/app/models/all-MiniLM-L6-v2
      - HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
      - HF_HOME=/app/models
      - HUGGINGFACE_HUB_CACHE=/app/models
      - TRANSFORMERS_CACHE=/app/models
      - SENTENCE_TRANSFORMERS_HOME=/app/models
    ports:
      - "8011:8011"
    volumes:
      - ./:/app
      - ./models:/app/models
      - ./data:/app/data
    working_dir: /app
    command: >
      uvicorn "api.app:app" --app-dir "📚 Enhanced RAG & Knowledge Graph"
      --host 0.0.0.0 --port 8011 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8011/readyz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 启动命令

```bash
# 使用docker-compose启动
docker-compose -f docker-compose.rag.yml up

# 后台运行
docker-compose -f docker-compose.rag.yml up -d

# 查看日志
docker-compose -f docker-compose.rag.yml logs -f

# 停止服务
docker-compose -f docker-compose.rag.yml down
```

---

## 🔨 Makefile 命令

### 开发命令

```bash
# 启动开发服务器（端口8011）
make dev

# 或使用api-8011
make api-8011

# 启动开发服务器（端口8000）
make api

# 启动开发服务器（端口8001）
make api-8001
```

### 测试命令

```bash
# 运行测试
make test

# 运行冒烟测试
make smoke

# 运行代码审计
make audit
```

### Docker命令

```bash
# 构建Docker镜像
make docker-build

# 运行Docker容器
make docker-run

# 在Docker中运行测试
make docker-test
```

---

## 📦 依赖管理

### requirements.txt

主要依赖：

- **Web框架**: `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`
- **向量处理**: `numpy>=2.1.3`, `sentence-transformers>=3.0.0`
- **文件处理**: `pymupdf>=1.24.0`, `pdfplumber>=0.11.0`, `python-docx>=1.1.0`
- **向量数据库**: `faiss-cpu>=1.7.4`
- **监控**: `prometheus-client>=0.20.0`

### 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## 🔐 API 密钥配置

### 启用API密钥验证

1. **设置环境变量**:
   ```bash
   export RAG_API_KEY=your_secret_key_here
   ```

2. **在Docker中设置**:
   ```bash
   docker-compose -f docker-compose.rag.yml up -e RAG_API_KEY=your_secret_key
   ```

3. **在请求中使用**:
   ```bash
   curl -H "X-API-Key: your_secret_key_here" http://localhost:8011/rag/search?query=test
   ```

### 禁用API密钥验证

不设置`RAG_API_KEY`环境变量即可。

---

## 📁 目录结构

### 数据目录

- `data/` - 索引数据和知识图谱文件
  - `docs.json` - 文档索引
  - `vectors.npy` - 向量索引
  - `kg.json` - 知识图谱数据

### 模型目录

- `models/` - 本地模型文件
  - `all-MiniLM-L6-v2/` - 句子嵌入模型

### 日志目录

- `logs/` - 应用日志文件

---

## ⚙️ 开发环境配置

### Python版本

- **最低版本**: Python 3.11
- **推荐版本**: Python 3.11+

### 开发脚本

`scripts/dev.sh` - 自动开发环境启动脚本

功能：
- 自动检测虚拟环境
- 清理占用端口
- 设置环境变量
- 启动开发服务器

---

## 🌐 API端点配置

### 默认端口

- **开发环境**: 8011
- **生产环境**: 8011（可配置）

### 健康检查

```bash
curl http://localhost:8011/readyz
```

### API文档

- **Swagger UI**: http://localhost:8011/docs
- **ReDoc**: http://localhost:8011/redoc

---

## 📝 配置文件位置

- **环境变量示例**: `.env.example`
- **Docker Compose**: `docker-compose.rag.yml`
- **Dockerfile**: `Dockerfile`
- **Makefile**: `Makefile`
- **依赖文件**: `requirements.txt`

---

## 🔍 故障排查

### 端口已被占用

```bash
# 查找占用端口的进程
lsof -nP -iTCP:8011 -sTCP:LISTEN

# 或使用脚本自动清理
bash scripts/dev.sh
```

### 模型加载失败

检查`LOCAL_ST_MODEL_PATH`环境变量和模型文件是否存在。

### API密钥验证失败

确认请求头`X-API-Key`与`RAG_API_KEY`环境变量匹配。

---

**更多信息请参考**: [README.md](README.md) 和 [QUICKSTART.md](QUICKSTART.md)

