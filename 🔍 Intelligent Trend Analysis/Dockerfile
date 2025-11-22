# Trend Analysis Sidecar Dockerfile
# P3-401: 实现Trend Sidecar的可选独立部署

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
            pandas==2.1.3 \
            numpy==1.26.2 \
            scikit-learn==1.3.2; \
    fi

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=8014
ENV HOST=0.0.0.0

# 暴露端口
EXPOSE 8014

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8014/health || exit 1

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8014", "--workers", "2"]

