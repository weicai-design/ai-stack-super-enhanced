# 🌐 OpenWebUI 深度集成方案

**创建时间**: 2025-11-04 23:05  
**优先级**: ⭐⭐⭐⭐⭐ (最高)  
**目标**: 实现OpenWebUI作为AI Stack统一交互中心

---

## 🎯 集成目标

根据用户需求5.1-5.9，OpenWebUI需要成为：

1. **统一交互窗口** - 所有AI Stack功能的中央控制台
2. **多格式文件处理** - 支持上传/生成所有格式文件
3. **系统互联枢纽** - 连接RAG、ERP、股票、内容创作等所有模块
4. **智能助手** - 提供查询、操作、监控、分析等功能
5. **终端和编程集成** - 支持终端调用和编程功能

---

## 📊 OpenWebUI 源码分析

### 核心架构

```
open-webui/
├── backend/          # Python后端 (FastAPI)
│   ├── apps/         # 核心应用模块
│   │   ├── webui/    # WebUI核心
│   │   ├── ollama/   # Ollama集成
│   │   └── rag/      # RAG功能
│   ├── main.py       # 主入口
│   └── config.py     # 配置
├── src/              # Svelte前端
│   ├── lib/          # 核心库
│   │   ├── components/  # UI组件
│   │   ├── stores/      # 状态管理
│   │   └── apis/        # API客户端
│   └── routes/       # 路由页面
└── docker/           # Docker配置
```

### 关键文件

1. **backend/main.py** - FastAPI应用主入口
2. **backend/apps/webui/routers/chats.py** - 聊天路由
3. **backend/apps/rag/** - RAG集成模块
4. **src/lib/apis/*** - 前端API客户端
5. **src/routes/+page.svelte** - 主界面

---

## 🔌 集成方案设计

### 方案1: Plugin/Function 扩展 ⭐⭐⭐⭐⭐ (推荐)

**原理**: 利用OpenWebUI的Functions功能注入自定义能力

**优势**:
- ✅ 无需修改OpenWebUI核心代码
- ✅ 易于维护和升级
- ✅ 模块化、可插拔
- ✅ 符合OpenWebUI设计理念

**实现**:
```python
# 创建AI Stack Functions
📁 openwebui-functions/
  ├── rag_integration.py      # RAG系统集成
  ├── erp_query.py            # ERP查询功能
  ├── stock_analysis.py       # 股票分析
  ├── content_creation.py     # 内容创作
  ├── trend_analysis.py       # 趋势分析
  ├── task_management.py      # 任务管理
  ├── resource_monitor.py     # 资源监控
  └── terminal_exec.py        # 终端执行
```

### 方案2: API Bridge 中间件

**原理**: 创建API网关，统一管理所有系统调用

**架构**:
```
OpenWebUI → API Gateway → {RAG, ERP, Stock, ...}
             ↓
          Unified API
```

**文件**:
```python
api_gateway/
├── main.py              # FastAPI网关
├── routers/
│   ├── rag_router.py    # RAG路由
│   ├── erp_router.py    # ERP路由
│   ├── stock_router.py  # 股票路由
│   └── ...
└── middleware/
    ├── auth.py          # 认证
    └── logging.py       # 日志
```

### 方案3: 源码Fork + 定制 ⚠️

**原理**: Fork OpenWebUI并深度定制

**问题**:
- ❌ 维护成本高
- ❌ 升级困难
- ❌ 不推荐

---

## 🛠️ 具体实现计划

### 第一阶段: Functions开发 (推荐方案1)

#### 1.1 RAG集成Function

**文件**: `openwebui-functions/rag_integration.py`

**功能**:
```python
class RAGIntegration:
    """RAG系统集成"""
    
    async def search_knowledge(query: str, top_k: int = 5):
        """搜索知识库"""
        # 调用RAG API
        
    async def ingest_document(file_path: str):
        """摄入文档到RAG"""
        
    async def query_knowledge_graph(entity: str):
        """查询知识图谱"""
        
    async def get_kg_visualization():
        """获取知识图谱可视化"""
```

**OpenWebUI调用**:
```python
# 在聊天中使用
User: "搜索关于AI的知识"
Assistant: [调用RAGIntegration.search_knowledge("AI")]
```

#### 1.2 ERP查询Function

**文件**: `openwebui-functions/erp_query.py`

**功能**:
```python
class ERPQuery:
    """ERP系统查询"""
    
    async def get_financial_dashboard(period: str):
        """获取财务看板"""
        
    async def query_orders(status: str = None):
        """查询订单"""
        
    async def get_production_status():
        """获取生产状态"""
        
    async def analyze_business_metrics():
        """分析经营指标"""
```

#### 1.3 股票分析Function

**文件**: `openwebui-functions/stock_analysis.py`

**功能**:
```python
class StockAnalysis:
    """股票分析"""
    
    async def get_stock_price(code: str):
        """获取股票价格"""
        
    async def analyze_strategy(code: str):
        """策略分析"""
        
    async def get_market_sentiment():
        """市场情绪"""
        
    async def execute_trade(action: str, code: str, amount: int):
        """执行交易"""
```

#### 1.4 内容创作Function

**文件**: `openwebui-functions/content_creation.py`

**功能**:
```python
class ContentCreation:
    """内容创作"""
    
    async def generate_content(topic: str, platform: str):
        """生成内容"""
        
    async def collect_materials(topic: str):
        """收集素材"""
        
    async def publish_content(content: str, platforms: list):
        """发布内容"""
```

#### 1.5 终端执行Function

**文件**: `openwebui-functions/terminal_exec.py`

**功能**:
```python
class TerminalExec:
    """终端执行"""
    
    async def execute_command(cmd: str):
        """执行终端命令"""
        # 安全检查
        # 执行命令
        # 返回结果
```

### 第二阶段: API Gateway开发

**文件**: `api_gateway/main.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="AI Stack API Gateway")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # OpenWebUI
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务配置
SERVICES = {
    "rag": "http://localhost:8011",
    "erp": "http://localhost:8013",
    "stock": "http://localhost:8014",
    "trend": "http://localhost:8015",
    "content": "http://localhost:8016",
    "task": "http://localhost:8017",
    "resource": "http://localhost:8018",
    "learning": "http://localhost:8019",
}

@app.get("/gateway/rag/search")
async def rag_search(query: str, top_k: int = 5):
    """RAG搜索"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SERVICES['rag']}/rag/search",
            params={"query": query, "top_k": top_k}
        )
        return response.json()

@app.get("/gateway/erp/financial")
async def erp_financial(period: str = "month"):
    """ERP财务数据"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SERVICES['erp']}/api/finance/dashboard",
            params={"period": period}
        )
        return response.json()

@app.get("/gateway/stock/price/{code}")
async def stock_price(code: str):
    """股票价格"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SERVICES['stock']}/api/stock/price/{code}"
        )
        return response.json()

# ... 更多路由
```

### 第三阶段: OpenWebUI配置

#### 3.1 环境变量配置

**文件**: `.env`

```bash
# AI Stack API Gateway
AI_STACK_GATEWAY=http://localhost:9000

# 各系统直连地址
RAG_API=http://localhost:8011
ERP_API=http://localhost:8013
STOCK_API=http://localhost:8014
TREND_API=http://localhost:8015
CONTENT_API=http://localhost:8016
TASK_API=http://localhost:8017
RESOURCE_API=http://localhost:8018
LEARNING_API=http://localhost:8019

# 功能开关
ENABLE_RAG_INTEGRATION=true
ENABLE_ERP_INTEGRATION=true
ENABLE_STOCK_INTEGRATION=true
ENABLE_TERMINAL=true
```

#### 3.2 Functions注册

在OpenWebUI中注册所有Functions:

1. 进入 http://localhost:3000/admin/functions
2. 上传所有Function文件
3. 启用Functions
4. 配置权限

---

## 🔧 开发步骤

### Step 1: 创建Functions目录结构

```bash
mkdir -p openwebui-functions
cd openwebui-functions

# 创建所有Function文件
touch rag_integration.py
touch erp_query.py
touch stock_analysis.py
touch content_creation.py
touch trend_analysis.py
touch task_management.py
touch resource_monitor.py
touch terminal_exec.py
```

### Step 2: 实现核心Functions

每个Function遵循OpenWebUI规范:

```python
"""
title: Function名称
author: AI Stack Team
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable
import httpx

class Action:
    class Valves(BaseModel):
        # 配置项
        api_endpoint: str = Field(
            default="http://localhost:8011",
            description="API端点"
        )
        api_key: Optional[str] = Field(
            default=None,
            description="API密钥"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        执行动作
        """
        # 实现逻辑
        pass
```

### Step 3: 开发API Gateway

```bash
mkdir -p api_gateway
cd api_gateway

# 创建文件
touch main.py
touch config.py
mkdir routers
touch routers/__init__.py
touch routers/rag_router.py
touch routers/erp_router.py
# ...
```

### Step 4: 集成测试

```bash
# 启动API Gateway
cd api_gateway
uvicorn main:app --host 0.0.0.0 --port 9000

# 启动OpenWebUI (已配置Functions)
# 测试各项功能
```

---

## 📋 功能清单

### 核心集成功能

- [ ] RAG知识搜索
- [ ] RAG文档摄入
- [ ] 知识图谱查询
- [ ] ERP财务查询
- [ ] ERP订单管理
- [ ] ERP生产监控
- [ ] 股票价格查询
- [ ] 股票策略分析
- [ ] 股票自动交易
- [ ] 内容自动创作
- [ ] 内容自动发布
- [ ] 趋势分析查询
- [ ] 任务创建和管理
- [ ] 资源监控
- [ ] 终端命令执行
- [ ] 编程代码执行

### 高级功能

- [ ] 多系统联合查询
- [ ] 跨系统数据关联
- [ ] 智能建议生成
- [ ] 异常自动检测
- [ ] 报告自动生成
- [ ] 数据可视化集成

---

## 🎨 用户界面增强

### 聊天界面增强

在OpenWebUI聊天界面添加：

1. **快捷命令菜单**
   ```
   /rag search <query>      - RAG搜索
   /erp query <type>        - ERP查询
   /stock price <code>      - 股票价格
   /content create <topic>  - 内容创作
   /task create <name>      - 创建任务
   /terminal <cmd>          - 执行命令
   ```

2. **侧边栏工具面板**
   - RAG知识库
   - ERP数据中心
   - 股票交易台
   - 内容创作室
   - 任务管理器
   - 系统监控

3. **文件上传增强**
   - 支持所有格式
   - 自动识别文件类型
   - 自动路由到相应系统
   - 进度实时显示

---

## 🔐 安全考虑

### 1. 认证和授权

```python
# API Gateway认证
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials):
    """验证Token"""
    # 实现Token验证逻辑
    pass
```

### 2. 权限控制

```python
# 不同用户不同权限
PERMISSIONS = {
    "admin": ["rag", "erp", "stock", "terminal"],
    "user": ["rag", "erp"],
    "guest": ["rag"],
}
```

### 3. 命令白名单

```python
# 终端命令白名单
ALLOWED_COMMANDS = [
    "ls", "cat", "grep", "find",
    "python", "node", "npm",
    # 危险命令禁止
    # "rm", "dd", "mkfs"
]
```

---

## 📊 监控和日志

### 1. 请求日志

```python
import logging

logger = logging.getLogger("ai_stack_gateway")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### 2. 性能监控

```python
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

---

## 🚀 部署方案

### Docker Compose集成

```yaml
version: '3.8'

services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - AI_STACK_GATEWAY=http://api-gateway:9000
    volumes:
      - ./openwebui-functions:/app/functions
    depends_on:
      - api-gateway
  
  api-gateway:
    build: ./api_gateway
    ports:
      - "9000:9000"
    environment:
      - RAG_API=http://rag-service:8011
      - ERP_API=http://erp-backend:8013
      - STOCK_API=http://stock-service:8014
    depends_on:
      - rag-service
      - erp-backend
      - stock-service
  
  rag-service:
    # RAG服务配置
    
  erp-backend:
    # ERP后端配置
    
  stock-service:
    # 股票服务配置
```

---

## 📝 开发时间表

### Week 1: Functions开发
- Day 1-2: RAG Integration
- Day 3-4: ERP Query
- Day 5: Stock Analysis
- Day 6-7: 其他Functions

### Week 2: API Gateway
- Day 1-3: Gateway核心
- Day 4-5: 路由和中间件
- Day 6-7: 测试和优化

### Week 3: 集成和测试
- Day 1-3: OpenWebUI集成
- Day 4-5: 端到端测试
- Day 6-7: 文档和部署

---

## ✅ 成功标准

### 功能标准
- ✅ 可从OpenWebUI查询所有系统数据
- ✅ 可从OpenWebUI执行所有系统操作
- ✅ 响应时间 < 500ms
- ✅ 支持所有文件格式上传

### 用户体验标准
- ✅ 界面统一、流畅
- ✅ 操作简单、直观
- ✅ 反馈及时、清晰
- ✅ 错误处理友好

---

**下一步**: 开始实现RAG Integration Function

**负责人**: AI Stack Team  
**开始时间**: 立即  
**预计完成**: 3周



