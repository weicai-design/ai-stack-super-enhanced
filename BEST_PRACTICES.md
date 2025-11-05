# 🏆 AI Stack Super Enhanced - 最佳实践指南

**版本**: v2.0.0  
**更新时间**: 2025-11-03  

---

## 📋 目录

1. [开发最佳实践](#开发最佳实践)
2. [部署最佳实践](#部署最佳实践)
3. [安全最佳实践](#安全最佳实践)
4. [性能最佳实践](#性能最佳实践)
5. [数据管理最佳实践](#数据管理最佳实践)
6. [API设计最佳实践](#api设计最佳实践)
7. [前端开发最佳实践](#前端开发最佳实践)
8. [AI模型使用最佳实践](#ai模型使用最佳实践)

---

## 🔧 开发最佳实践

### 1. 使用虚拟环境

**✅ 推荐做法**:
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

**❌ 不推荐**:
```bash
# 直接在系统Python安装（可能冲突）
sudo pip install -r requirements.txt
```

---

### 2. 遵循代码规范

**✅ 推荐做法**:
```bash
# 使用格式化工具
pip install black flake8 isort

# 格式化代码
black .
isort .

# 检查代码质量
flake8 .
```

**代码风格**:
```python
# ✅ 好的做法
def get_customer_by_id(customer_id: int) -> Optional[Customer]:
    """
    根据ID获取客户信息
    
    Args:
        customer_id: 客户ID
        
    Returns:
        客户对象，如果不存在则返回None
    """
    return db.query(Customer).filter(Customer.id == customer_id).first()

# ❌ 避免
def get_cust(id):
    return db.query(Customer).filter(Customer.id==id).first()
```

---

### 3. 编写测试

**✅ 推荐做法**:
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

def test_get_customers():
    response = client.get("/api/business/customers")
    assert response.status_code == 200
    assert "customers" in response.json()
```

**运行测试**:
```bash
# 安装pytest
pip install pytest pytest-cov

# 运行测试
pytest

# 查看覆盖率
pytest --cov=.
```

---

### 4. 使用Git版本控制

**✅ 推荐做法**:
```bash
# 提交前检查
git status
git diff

# 有意义的提交信息
git commit -m "feat: 添加工艺管理模块API接口"
git commit -m "fix: 修复财务看板数据计算错误"
git commit -m "docs: 更新API文档"

# 使用分支
git checkout -b feature/new-module
```

**提交信息规范**:
- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

---

## 🚀 部署最佳实践

### 1. 环境分离

**✅ 推荐做法**:
```bash
# 开发环境
export ENV=development
python api/main.py

# 生产环境
export ENV=production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app
```

**配置文件**:
```python
# config.py
import os

class Config:
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    
class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URL = "postgresql://user:pass@localhost/prod_db"
```

---

### 2. 使用进程管理器

**✅ 推荐做法**:
```bash
# 使用systemd (Linux)
sudo systemctl start erp-api
sudo systemctl enable erp-api

# 使用PM2 (跨平台)
pm2 start api/main.py --name erp-api
pm2 startup
pm2 save
```

---

### 3. 配置反向代理

**✅ 推荐做法** (Nginx):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8013;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/static;
    }
}
```

---

## 🔐 安全最佳实践

### 1. 环境变量管理

**✅ 推荐做法**:
```bash
# .env 文件 (不要提交到Git)
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key

# 在代码中使用
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
```

**.gitignore**:
```
.env
*.key
secrets/
```

---

### 2. API认证

**✅ 推荐做法**:
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

@app.get("/api/protected")
async def protected_route(token: str = Depends(verify_token)):
    return {"message": "Access granted"}
```

---

### 3. 输入验证

**✅ 推荐做法**:
```python
from pydantic import BaseModel, validator, Field

class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str
    phone: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v
```

---

## ⚡ 性能最佳实践

### 1. 数据库优化

**✅ 推荐做法**:
```python
# 使用索引
from sqlalchemy import Index

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)  # 添加索引
    email = Column(String(100), unique=True, index=True)
    
    __table_args__ = (
        Index('idx_customer_name_email', 'name', 'email'),  # 复合索引
    )
```

**使用分页**:
```python
@app.get("/api/customers")
async def get_customers(skip: int = 0, limit: int = 50):
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return {"customers": customers}
```

---

### 2. 缓存策略

**✅ 推荐做法**:
```python
from functools import lru_cache
import redis

# 内存缓存（简单数据）
@lru_cache(maxsize=128)
def get_config():
    return load_config()

# Redis缓存（分布式）
redis_client = redis.Redis(host='localhost', port=6379)

def get_customer_cached(customer_id: int):
    cache_key = f"customer:{customer_id}"
    
    # 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 从数据库获取
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    # 存入缓存
    redis_client.setex(cache_key, 3600, json.dumps(customer))
    
    return customer
```

---

### 3. 异步操作

**✅ 推荐做法**:
```python
import asyncio
import httpx

# 使用async/await
@app.get("/api/combined-data")
async def get_combined_data():
    async with httpx.AsyncClient() as client:
        # 并发请求
        finance, customers, orders = await asyncio.gather(
            client.get("http://localhost:8013/api/finance/dashboard"),
            client.get("http://localhost:8013/api/business/customers"),
            client.get("http://localhost:8013/api/business/orders")
        )
    
    return {
        "finance": finance.json(),
        "customers": customers.json(),
        "orders": orders.json()
    }
```

---

## 💾 数据管理最佳实践

### 1. 数据备份

**✅ 推荐做法**:
```bash
# 每日自动备份
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="/path/to/backups/$DATE"

mkdir -p "$BACKUP_DIR"

# 备份SQLite
cp erp.db "$BACKUP_DIR/erp_$DATE.db"

# 备份PostgreSQL
pg_dump -U user database_name > "$BACKUP_DIR/db_$DATE.sql"

# 压缩
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"

# 删除30天前的备份
find /path/to/backups -mtime +30 -delete
```

**设置crontab**:
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

---

### 2. 数据迁移

**✅ 推荐做法**:
```bash
# 使用Alembic管理数据库迁移
pip install alembic

# 初始化
alembic init alembic

# 创建迁移
alembic revision -m "add new column"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

### 3. 数据验证

**✅ 推荐做法**:
```python
from pydantic import BaseModel, validator

class FinancialData(BaseModel):
    income: float
    expense: float
    
    @validator('income', 'expense')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('金额必须为正数')
        return v
    
    @property
    def profit(self):
        return self.income - self.expense
```

---

## 🎨 API设计最佳实践

### 1. RESTful设计

**✅ 推荐做法**:
```python
# 使用标准HTTP方法
@app.get("/api/customers")           # 获取列表
@app.get("/api/customers/{id}")      # 获取单个
@app.post("/api/customers")          # 创建
@app.put("/api/customers/{id}")      # 更新
@app.delete("/api/customers/{id}")   # 删除

# 使用复数形式
# ✅ /api/customers
# ❌ /api/customer

# 使用嵌套资源
# ✅ /api/customers/{id}/orders
# ❌ /api/customer-orders?customer_id={id}
```

---

### 2. 统一响应格式

**✅ 推荐做法**:
```python
# 成功响应
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}

# 错误响应
{
    "success": false,
    "error": {
        "code": "INVALID_INPUT",
        "message": "输入数据无效",
        "details": {...}
    }
}

# 实现
from fastapi import HTTPException

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""

@app.get("/api/customers")
async def get_customers():
    customers = get_all_customers()
    return APIResponse(
        success=True,
        data=customers,
        message="查询成功"
    )
```

---

### 3. 版本控制

**✅ 推荐做法**:
```python
# URL版本控制
@app.get("/api/v1/customers")
@app.get("/api/v2/customers")  # 新版本

# 或使用Header
from fastapi import Header

@app.get("/api/customers")
async def get_customers(api_version: str = Header("1.0")):
    if api_version == "2.0":
        return new_format_customers()
    return old_format_customers()
```

---

## 🎯 前端开发最佳实践

### 1. 组件化

**✅ 推荐做法**:
```vue
<!-- CustomerCard.vue -->
<template>
  <div class="customer-card">
    <h3>{{ customer.name }}</h3>
    <p>{{ customer.email }}</p>
  </div>
</template>

<script>
export default {
  name: 'CustomerCard',
  props: {
    customer: {
      type: Object,
      required: true
    }
  }
}
</script>
```

---

### 2. 状态管理

**✅ 推荐做法** (使用Pinia):
```javascript
// stores/customer.js
import { defineStore } from 'pinia'
import axios from 'axios'

export const useCustomerStore = defineStore('customer', {
  state: () => ({
    customers: [],
    loading: false
  }),
  
  actions: {
    async fetchCustomers() {
      this.loading = true
      try {
        const response = await axios.get('/api/customers')
        this.customers = response.data.customers
      } finally {
        this.loading = false
      }
    }
  }
})
```

---

### 3. 错误处理

**✅ 推荐做法**:
```javascript
// api/axios.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8013'
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 添加token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 跳转登录
      router.push('/login')
    }
    // 显示错误消息
    ElMessage.error(error.message)
    return Promise.reject(error)
  }
)

export default api
```

---

## 🤖 AI模型使用最佳实践

### 1. 提示词工程

**✅ 推荐做法**:
```python
def create_finance_expert_prompt(question: str, context: dict) -> str:
    """创建财务专家提示词"""
    return f"""你是一位资深的企业财务专家。

背景信息：
- 本月收入：{context['income']}
- 本月支出：{context['expense']}
- 利润率：{context['profit_margin']}

用户问题：{question}

请基于以上数据提供专业的财务分析和建议。
"""
```

---

### 2. 温度参数调整

**✅ 推荐做法**:
```python
# 精确任务（如数据分析）使用低温度
response = ollama.generate(
    model="qwen2.5:7b",
    prompt=prompt,
    options={"temperature": 0.3}  # 更确定的输出
)

# 创意任务（如内容创作）使用高温度
response = ollama.generate(
    model="qwen2.5:7b",
    prompt=prompt,
    options={"temperature": 0.9}  # 更有创意
)
```

---

### 3. 上下文管理

**✅ 推荐做法**:
```python
# 保持对话上下文
class ConversationManager:
    def __init__(self):
        self.history = []
    
    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
    
    def get_prompt(self, new_question: str) -> str:
        self.add_message("user", new_question)
        
        # 构建包含历史的提示
        full_prompt = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.history[-10:]  # 只保留最近10条
        ])
        
        return full_prompt
```

---

## 📝 文档最佳实践

### 1. API文档

**✅ 推荐做法**:
```python
@app.get(
    "/api/customers",
    response_model=CustomerListResponse,
    summary="获取客户列表",
    description="返回所有客户的列表，支持分页和筛选",
    response_description="客户列表和分页信息"
)
async def get_customers(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(50, description="返回记录数", le=100),
    category: Optional[str] = Query(None, description="客户类别筛选")
):
    """
    获取客户列表API
    
    - **skip**: 从第几条记录开始
    - **limit**: 返回多少条记录
    - **category**: 按类别筛选（可选）
    """
    ...
```

---

### 2. 代码注释

**✅ 推荐做法**:
```python
def calculate_mrp(
    material_code: str,
    period_start: date,
    period_end: date
) -> Dict:
    """
    计算物料需求计划（MRP）
    
    MRP计算公式：
    净需求 = 毛需求 - 现有库存 - 预计到货 + 安全库存
    
    Args:
        material_code: 物料编码
        period_start: 计划开始日期
        period_end: 计划结束日期
        
    Returns:
        Dict: 包含每日需求、库存和建议订单的字典
        
    Raises:
        ValueError: 当物料编码不存在时
        
    Example:
        >>> calculate_mrp("MAT001", date(2025,11,1), date(2025,11,30))
        {'requirements': [...], 'suggestions': [...]}
    """
    ...
```

---

## 🎉 总结

遵循这些最佳实践将帮助您：

✅ **提高代码质量** - 更易维护和扩展  
✅ **提升系统性能** - 更快的响应速度  
✅ **增强系统安全** - 更好的数据保护  
✅ **改善用户体验** - 更稳定可靠  

**记住**: 最佳实践不是一成不变的，要根据实际情况灵活运用！

---

**更新时间**: 2025-11-03  
**版本**: v2.0.0  
**维护者**: AI Stack Team

