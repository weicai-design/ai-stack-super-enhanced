# RAG Sidecar Dockerfile
# P3-401: 实现RAG Sidecar的可选独立部署

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt* ./
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir \
            fastapi==0.104.1 \
            uvicorn[standard]==0.24.0 \
            httpx==0.25.0 \
            pydantic==2.5.0 \
            sqlalchemy==2.0.23 \
            sentence-transformers==2.2.2 \
            chromadb==0.4.18; \
    fi

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/models

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=8011
ENV HOST=0.0.0.0

# 暴露端口
EXPOSE 8011

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8011/health || exit 1

# 启动命令
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8011", "--workers", "2"]

