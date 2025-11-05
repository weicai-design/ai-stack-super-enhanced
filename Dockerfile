# AI Stack Super Enhanced - Dockerfile
ARG PY_BASE=python:3.11-slim

FROM ${PY_BASE} AS base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖（无VPN环境优化：预设国内镜像）
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app/📚\ Enhanced\ RAG\ \&\ Knowledge\ Graph:$PYTHONPATH
ENV LOCAL_ST_MODEL_PATH=/app/models/all-MiniLM-L6-v2

# 配置HuggingFace国内镜像与本地缓存（无VPN环境）
ENV HF_ENDPOINT=https://hf-mirror.com \
    HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1 \
    HF_HOME=/app/models \
    HUGGINGFACE_HUB_CACHE=/app/models \
    TRANSFORMERS_CACHE=/app/models \
    SENTENCE_TRANSFORMERS_HOME=/app/models

# 暴露端口
EXPOSE 8011

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8011/readyz || exit 1

# 启动命令
CMD ["uvicorn", "api.app:app", \
     "--app-dir", "📚 Enhanced RAG & Knowledge Graph", \
     "--host", "0.0.0.0", \
     "--port", "8011"]
