# 📋 AI Stack Super Enhanced - 快速参考卡片

**版本**: v2.0.0  
**更新时间**: 2025-11-03  

---

## ⚡ 快速启动

### 一键部署
```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/quick_deploy.sh
```

### 手动启动
```bash
# ERP后端
cd "💼 Intelligent ERP & Business Management"
python3 api/main.py &

# 命令网关
cd "💬 Intelligent OpenWebUI Interaction Center"
python3 command_gateway.py &
```

---

## 🌐 访问地址

| 服务 | 地址 | 用途 |
|------|------|------|
| **命令面板** | http://localhost:8020 | 统一操作入口 |
| **ERP系统** | http://localhost:8012 | 完整ERP功能 |
| **ERP API** | http://localhost:8013 | ERP后端API |
| **API文档** | http://localhost:8013/docs | Swagger文档 |
| **OpenWebUI** | http://localhost:3000 | AI对话界面 |
| **RAG API** | http://localhost:8011 | 知识库API |
| **股票API** | http://localhost:8014 | 股票分析 |
| **趋势API** | http://localhost:8015 | 趋势分析 |
| **任务API** | http://localhost:8017 | 任务管理 |
| **资源API** | http://localhost:8018 | 资源监控 |

---

## 🎯 常用命令

### 系统管理

```bash
# 启动所有服务
./scripts/start_all_services.sh

# 停止所有服务
./scripts/stop_all_services.sh

# 检查服务状态
lsof -i :8012
lsof -i :8013
lsof -i :8020

# 查看日志
tail -f logs/*.log
```

### 数据管理

```bash
# 添加测试数据
cd "💼 Intelligent ERP & Business Management"
python3 scripts/add_test_data.py
python3 scripts/add_business_test_data.py
python3 scripts/add_process_data.py
```

---

## 📊 ERP模块速查

### 13个完整模块

| 模块 | API路径 | 主要功能 |
|------|---------|---------|
| 财务管理 | /api/finance/* | 看板、数据录入 |
| 经营分析 | /api/analytics/* | 开源、成本、效益 |
| 流程管理 | /api/process/* | 定义、追踪、异常 |
| 采购管理 | /api/procurement/* | 供应商、订单 |
| 仓储管理 | /api/warehouse/* | 库存、预警 |
| 质量管理 | /api/quality/* | 质检、缺陷 |
| 物料管理 | /api/material/* | MRP、ABC |
| 生产管理 | /api/production/* | 排程、OEE |
| 设备管理 | /api/equipment/* | 台账、MTBF |
| 工艺管理 | /api/engineering/* | 路线、参数 |
| 客户管理 | /api/business/customers | CRM |
| 订单管理 | /api/business/orders | OMS |
| 项目管理 | /api/business/projects | PM |

---

## 🔧 API快速调用

### 财务看板
```bash
# 本月财务
curl http://localhost:8013/api/finance/dashboard?period_type=monthly

# 本周财务
curl http://localhost:8013/api/finance/dashboard?period_type=weekly
```

### 客户列表
```bash
curl http://localhost:8013/api/business/customers
```

### 库存查询
```bash
curl http://localhost:8013/api/warehouse/inventory
```

### 生产订单
```bash
curl http://localhost:8013/api/production/orders
```

### 设备列表
```bash
curl http://localhost:8013/api/equipment/equipment
```

---

## 💡 命令面板常用指令

在 http://localhost:8020 中可直接输入：

```
系统类:
- 查看所有系统状态
- 查看系统资源
- 查看服务状态

财务类:
- 查看本月财务
- 查看本周财务
- 查看今日财务

业务类:
- 查看客户列表
- 查看订单列表
- 查看库存情况

其他:
- 查看AAPL股票
- 查看知识库统计
- 帮助
```

---

## 🗄️ 数据库位置

### SQLite数据库
```bash
# ERP数据库
💼 Intelligent ERP & Business Management/erp.db

# 其他系统数据库
各系统目录下的 *.db 文件
```

### 数据备份
```bash
# 备份ERP数据
cp "💼 Intelligent ERP & Business Management/erp.db" backups/erp_$(date +%Y%m%d).db
```

---

## 🔍 故障排除速查

### 端口被占用
```bash
# 查看占用
lsof -i :8013

# 释放端口
lsof -ti :8013 | xargs kill -9
```

### 服务无法启动
```bash
# 检查Python版本
python3 --version

# 检查依赖
pip list | grep fastapi

# 重新安装依赖
pip install -r requirements.txt
```

### 页面无法访问
```bash
# 硬刷新浏览器
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows)

# 清除缓存后重试
使用无痕模式访问
```

---

## 📦 专家模型使用

### 下载模型
```bash
# 基础模型
ollama pull qwen2.5:7b

# 创建专家模型（示例）
ollama create finance-expert -f expert_models/finance_expert.modelfile
```

### 调用专家
```python
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": "如何优化现金流？",
        "stream": False
    }
)
print(response.json()["response"])
```

---

## 🎨 前端开发

### ERP前端
```bash
cd "💼 Intelligent ERP & Business Management/web/frontend"

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build
```

---

## 📝 日志查看

### 后端日志
```bash
# ERP后端
tail -f "💼 Intelligent ERP & Business Management/logs/backend.log"

# 命令网关
tail -f "💬 Intelligent OpenWebUI Interaction Center/logs/gateway.log"
```

### 实时监控
```bash
# 查看所有日志
tail -f logs/*.log

# 过滤错误
tail -f logs/*.log | grep ERROR
```

---

## 🚀 性能优化

### Python优化
```bash
# 使用uvloop（更快的事件循环）
pip install uvloop

# 启用多worker
uvicorn main:app --workers 4
```

### 数据库优化
```sql
-- 添加索引
CREATE INDEX idx_customer_name ON customers(name);
CREATE INDEX idx_order_date ON orders(order_date);
```

---

## 🔐 环境变量

### 配置文件 (.env)
```bash
# API密钥
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key
OPENAI_API_KEY=your_key

# 数据库
DATABASE_URL=sqlite:///./erp.db

# 服务配置
ERP_API_PORT=8013
COMMAND_GATEWAY_PORT=8020
```

---

## 📊 监控指标

### 系统健康检查
```bash
# ERP健康检查
curl http://localhost:8013/health

# 所有服务状态
curl http://localhost:8020/execute?command=查看所有系统状态
```

### 性能指标
```bash
# CPU和内存
top -l 1 | grep "CPU usage"
top -l 1 | grep "PhysMem"

# 磁盘空间
df -h
```

---

## 🎯 快捷键

### 浏览器
- `Cmd/Ctrl + R` - 刷新页面
- `Cmd/Ctrl + Shift + R` - 硬刷新
- `Cmd/Ctrl + T` - 新标签页
- `Cmd/Ctrl + W` - 关闭标签页

### 终端
- `Ctrl + C` - 停止进程
- `Ctrl + Z` - 暂停进程
- `Cmd + K` - 清屏 (Mac)
- `clear` - 清屏 (通用)

---

## 📞 支持资源

### 文档
- `README.md` - 项目概览
- `🎯终极使用指南.md` - 详细指南
- `🏆100%完成度达成-v2.0.0.md` - 完成报告

### API文档
- http://localhost:8013/docs - Swagger UI
- http://localhost:8013/redoc - ReDoc

### 在线资源
- FastAPI: https://fastapi.tiangolo.com/
- Vue.js: https://vuejs.org/
- Ollama: https://ollama.ai/

---

## 💡 最佳实践

### 开发流程
1. 启动开发服务器
2. 修改代码
3. 浏览器自动刷新
4. 查看效果
5. 提交代码

### 生产部署
1. 运行测试
2. 构建前端
3. 配置环境变量
4. 启动服务
5. 监控运行状态

---

## 🎉 快速成功案例

### 场景1：查看财务
```
1. 打开 http://localhost:8020
2. 点击"查看本月财务"
3. 立即看到结果
```

### 场景2：管理客户
```
1. 打开 http://localhost:8012
2. 点击"业务管理" → "客户管理"
3. 查看、添加、编辑客户
```

### 场景3：生产监控
```
1. 访问 http://localhost:8013/docs
2. 找到 /api/production/orders
3. 点击 "Try it out"
4. 执行查询
```

---

**更新时间**: 2025-11-03  
**版本**: v2.0.0  
**状态**: 完整版  

**🚀 祝使用愉快！**

