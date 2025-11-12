# 🚀 AI Stack 部署指南 v2.1

**版本**: v2.1.0  
**更新时间**: 2025-11-07  
**适用环境**: 开发/测试/生产

---

## 📋 目录

- [系统要求](#系统要求)
- [部署架构](#部署架构)
- [快速开始](#快速开始)
- [Docker部署](#docker部署)
- [Kubernetes部署](#kubernetes部署)
- [生产环境配置](#生产环境配置)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排查](#故障排查)
- [性能优化](#性能优化)

---

## 💻 系统要求

### 最小配置（开发环境）

| 组件 | 要求 |
|------|------|
| CPU | 4核 |
| 内存 | 8GB |
| 磁盘 | 50GB可用空间 |
| 操作系统 | Ubuntu 20.04+ / macOS 11+ / Windows 10+ |
| Python | 3.11+ |
| Docker | 20.10+ |
| Docker Compose | 2.0+ |

### 推荐配置（生产环境）

| 组件 | 要求 |
|------|------|
| CPU | 16核 |
| 内存 | 32GB |
| 磁盘 | 500GB SSD |
| 操作系统 | Ubuntu 22.04 LTS |
| Python | 3.11 |
| Docker | 24.0+ |
| Kubernetes | 1.28+ (可选) |

### 依赖服务

- PostgreSQL 15+ (可选，用于持久化)
- Redis 7+ (可选，用于缓存)
- Elasticsearch 8+ (可选，用于全文搜索)

---

## 🏗️ 部署架构

### 单机部署架构

```
┌─────────────────────────────────────┐
│       Nginx反向代理 (80/443)         │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│          Docker容器集群              │
│  ┌─────────┐  ┌─────────┐           │
│  │RAG系统  │  │ERP系统  │  ...      │
│  └─────────┘  └─────────┘           │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│        数据持久化层                  │
│  SQLite / PostgreSQL / ChromaDB     │
└─────────────────────────────────────┘
```

### 分布式部署架构

```
┌─────────────────────────────────────┐
│          负载均衡器 (Nginx)          │
└─────────────────────────────────────┘
         ↓         ↓         ↓
┌────────┐  ┌────────┐  ┌────────┐
│ 节点1   │  │ 节点2   │  │ 节点3   │
│ 应用层  │  │ 应用层  │  │ 应用层  │
└────────┘  └────────┘  └────────┘
         ↓         ↓         ↓
┌─────────────────────────────────────┐
│           共享存储层                  │
│  PostgreSQL + Redis + MinIO         │
└─────────────────────────────────────┘
```

---

## 🚀 快速开始

### 方法1: 一键部署脚本

```bash
# 克隆项目
git clone https://github.com/your-org/ai-stack-super-enhanced.git
cd ai-stack-super-enhanced

# 执行一键部署
./scripts/quick_deploy.sh

# 等待服务启动（约2-3分钟）
# 访问: http://localhost
```

### 方法2: Docker Compose

```bash
# 1. 配置环境变量
cp .env.example .env
vim .env  # 填入必要的API密钥

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 方法3: 本地开发部署

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
export OPENAI_API_KEY=your_key
export OLLAMA_BASE_URL=http://localhost:11434

# 4. 初始化数据库
python scripts/init_database.py

# 5. 启动服务
./scripts/start_all_services.sh
```

---

## 🐳 Docker部署

### 完整部署流程

#### 1. 环境准备

```bash
# 创建必要的目录
mkdir -p data logs backups

# 创建Docker网络
docker network create ai-stack-network

# 配置环境变量
cat > .env << EOF
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Ollama配置（本地模型）
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b

# 数据库配置
DATABASE_URL=sqlite:///data/aistack.db

# Redis配置（可选）
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=/app/logs
EOF
```

#### 2. 启动核心服务

```bash
# 启动核心服务
docker-compose up -d

# 等待服务启动
sleep 30

# 验证服务健康
./scripts/health_check.sh
```

#### 3. 启动监控服务

```bash
# 启动Prometheus和Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 访问Grafana: http://localhost:3000
# 默认账号: admin / admin123
```

#### 4. 数据初始化

```bash
# 初始化测试数据（开发环境）
docker exec ai-stack-rag python scripts/init_sample_data.py

# 导入知识库（生产环境）
docker exec ai-stack-rag python scripts/import_knowledge_base.py
```

### Docker Compose配置详解

**主配置文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # RAG知识检索系统
  rag-api:
    build:
      context: ./📚 Enhanced RAG & Knowledge Graph
      dockerfile: Dockerfile
    container_name: ai-stack-rag
    restart: unless-stopped
    ports:
      - "8011:8011"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./data/rag:/app/data
      - ./logs:/app/logs
    networks:
      - ai-stack-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8011/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ERP企业管理系统
  erp-api:
    build:
      context: ./💼 Intelligent ERP & Business Management
      dockerfile: Dockerfile
    container_name: ai-stack-erp
    restart: unless-stopped
    ports:
      - "8013:8013"
    volumes:
      - ./data/erp:/app/data
      - ./logs:/app/logs
    networks:
      - ai-stack-network

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: ai-stack-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    networks:
      - ai-stack-network
    depends_on:
      - rag-api
      - erp-api

networks:
  ai-stack-network:
    driver: bridge

volumes:
  rag_data:
  erp_data:
  logs:
```

### 常用Docker命令

```bash
# 查看运行中的容器
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart [service_name]

# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v

# 更新服务
docker-compose pull
docker-compose up -d

# 进入容器
docker exec -it ai-stack-rag /bin/bash

# 查看资源使用
docker stats
```

---

## ☸️ Kubernetes部署

### 前置要求

- Kubernetes集群 (v1.28+)
- kubectl已配置
- Helm 3+

### 快速部署

```bash
# 1. 添加Helm仓库
helm repo add ai-stack https://charts.aistack.com
helm repo update

# 2. 创建命名空间
kubectl create namespace ai-stack

# 3. 配置values.yaml
cat > values.yaml << EOF
global:
  domain: aistack.example.com
  
rag:
  replicas: 3
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 2000m
      memory: 4Gi

erp:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 1000m
      memory: 2Gi
EOF

# 4. 安装
helm install ai-stack ai-stack/ai-stack \
  --namespace ai-stack \
  --values values.yaml

# 5. 查看部署状态
kubectl get pods -n ai-stack
kubectl get svc -n ai-stack
```

### Kubernetes资源配置

**Deployment示例**: `infra/k8s/rag-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
  namespace: ai-stack
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
      - name: rag-api
        image: aistack/rag-api:v2.1.0
        ports:
        - containerPort: 8011
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-stack-secrets
              key: openai-api-key
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8011
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8011
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rag-api
  namespace: ai-stack
spec:
  selector:
    app: rag-api
  ports:
  - protocol: TCP
    port: 8011
    targetPort: 8011
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-api
  namespace: ai-stack
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.aistack.example.com
    secretName: aistack-tls
  rules:
  - host: api.aistack.example.com
    http:
      paths:
      - path: /rag
        pathType: Prefix
        backend:
          service:
            name: rag-api
            port:
              number: 8011
```

### 配置管理

```bash
# 创建ConfigMap
kubectl create configmap ai-stack-config \
  --from-file=config.yaml \
  --namespace=ai-stack

# 创建Secret
kubectl create secret generic ai-stack-secrets \
  --from-literal=openai-api-key=your_key \
  --from-literal=jwt-secret=your_secret \
  --namespace=ai-stack

# 查看配置
kubectl get configmap -n ai-stack
kubectl get secret -n ai-stack
```

### 自动扩缩容

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-api-hpa
  namespace: ai-stack
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 🔒 生产环境配置

### 1. 安全加固

#### SSL/TLS配置

```bash
# 生成自签名证书（测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/aistack.key \
  -out nginx/ssl/aistack.crt \
  -subj "/CN=aistack.local"

# 使用Let's Encrypt（生产）
certbot certonly --standalone -d api.aistack.com
```

#### Nginx SSL配置

```nginx
server {
    listen 443 ssl http2;
    server_name api.aistack.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://rag-api:8011;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 数据库优化

#### PostgreSQL配置

```bash
# docker-compose.yml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: aistack
    POSTGRES_USER: aistack
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
```

### 3. 缓存配置

#### Redis配置

```bash
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"
```

### 4. 日志管理

#### 集中式日志

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 📊 监控和日志

### Prometheus监控

```bash
# 启动监控栈
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# 访问Prometheus
open http://localhost:9090

# 访问Grafana
open http://localhost:3000
```

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f rag-api

# 导出日志
docker-compose logs --no-color > logs/$(date +%Y%m%d).log
```

---

## 💾 备份和恢复

### 数据备份

```bash
# 备份脚本
./scripts/backup.sh

# 手动备份
docker exec ai-stack-rag tar -czf /tmp/rag-backup.tar.gz /app/data
docker cp ai-stack-rag:/tmp/rag-backup.tar.gz ./backups/
```

### 数据恢复

```bash
# 恢复脚本
./scripts/restore.sh ./backups/rag-backup.tar.gz

# 手动恢复
docker cp ./backups/rag-backup.tar.gz ai-stack-rag:/tmp/
docker exec ai-stack-rag tar -xzf /tmp/rag-backup.tar.gz -C /app/
```

---

## 🐛 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
lsof -i :8011

# 查看容器日志
docker logs ai-stack-rag

# 检查环境变量
docker exec ai-stack-rag printenv
```

#### 2. 内存不足

```bash
# 增加Docker内存限制
docker-compose up -d --scale rag-api=1 --memory="4g"
```

#### 3. 数据库连接失败

```bash
# 测试数据库连接
docker exec ai-stack-rag python -c "from sqlalchemy import create_engine; engine = create_engine('sqlite:///data/aistack.db'); print(engine.connect())"
```

---

## ⚡ 性能优化

### 1. 并发配置

```python
# uvicorn配置
uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 2. 缓存优化

```python
# Redis缓存
CACHE_TTL = 3600
redis_client.setex(key, CACHE_TTL, value)
```

### 3. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_vectors_embedding ON vectors USING ivfflat(embedding);
```

---

## 📚 参考资料

- [Docker文档](https://docs.docker.com/)
- [Kubernetes文档](https://kubernetes.io/docs/)
- [Nginx文档](https://nginx.org/en/docs/)

---

**文档版本**: v2.1.0  
**最后更新**: 2025-11-07  
**维护团队**: AI Stack Team



















