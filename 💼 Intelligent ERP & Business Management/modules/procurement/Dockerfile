# 采购管理模块Docker镜像
# 多阶段构建，优化镜像大小

# 第一阶段：构建阶段
FROM python:3.8-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖到虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.8-slim

# 设置元数据
LABEL maintainer="devops@example.com"
LABEL version="1.0.0"
LABEL description="Procurement Management Module"

# 创建非root用户
RUN groupadd -r procurement && useradd -r -g procurement procurement

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY . .

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# 创建日志目录
RUN mkdir -p /var/log/procurement && \
    chown -R procurement:procurement /var/log/procurement && \
    chown -R procurement:procurement /app

# 切换到非root用户
USER procurement

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/procurement/health || exit 1

# 启动命令
CMD ["python", "procurement_api.py"]