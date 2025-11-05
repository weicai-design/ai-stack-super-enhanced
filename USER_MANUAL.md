# 📖 AI Stack Super Enhanced 用户手册

**版本**: v1.1.0  
**最后更新**: 2025-11-03  

---

## 📋 目录

1. [快速开始](#快速开始)
2. [系统概览](#系统概览)
3. [详细使用指南](#详细使用指南)
4. [API使用](#api使用)
5. [常见问题](#常见问题)
6. [故障排除](#故障排除)

---

## 🚀 快速开始

### 第一步：启动系统

```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/start_all_services.sh
```

等待30秒让所有服务启动。

### 第二步：测试服务

```bash
./scripts/test_all_systems.sh
```

应该看到大部分服务显示"✓ 通过"。

### 第三步：访问系统

```bash
# 访问ERP系统（推荐从这里开始）
open http://localhost:8012

# 或访问OpenWebUI
open http://localhost:3000

# 或查看监控面板
open monitoring/dashboard.html
```

---

## 🌐 系统概览

### 10个服务端口

| 端口 | 系统 | 用途 | 推荐访问 |
|------|------|------|---------|
| 3000 | OpenWebUI | AI聊天 | ⭐⭐⭐ |
| 8011 | RAG API | 知识检索 | ⭐⭐ |
| 8012 | ERP 前端 | 企业管理 | ⭐⭐⭐⭐⭐ |
| 8013 | ERP 后端 | API服务 | ⭐⭐⭐⭐ |
| 8014 | 股票服务 | 交易系统 | ⭐⭐⭐ |
| 8015 | 趋势分析 | 数据分析 | ⭐⭐⭐ |
| 8016 | 内容创作 | 内容生成 | ⭐⭐⭐ |
| 8017 | 任务代理 | 任务管理 | ⭐⭐⭐⭐ |
| 8018 | 资源管理 | 资源监控 | ⭐⭐⭐⭐ |
| 8019 | 自我学习 | 系统优化 | ⭐⭐⭐ |

---

## 📚 详细使用指南

### 1. ERP企业管理系统 ⭐⭐⭐⭐⭐

**推荐理由**: 功能最完整，界面最美观，数据最丰富

#### 访问地址
```
http://localhost:8012
```

#### 主要功能

**A. 财务看板**
- 📊 多时间维度（日/周/月/季/年）
- 💰 收入、支出、利润趋势
- 📈 专业图表可视化
- 🎯 自动数据汇总

**使用步骤**:
1. 点击左侧"财务看板"
2. 选择时间范围（月度/季度/年度）
3. 查看财务数据和趋势图表

**B. 经营分析**
- 📊 开源分析（客户类别、订单统计）
- 💵 成本分析（费用明细、合理性分析）
- 📈 效益分析（投入产出、ROI）

**使用步骤**:
1. 点击"经营分析" → "开源分析"
2. 查看客户分类和订单趋势
3. 查看产品订单明细

**C. 流程管理**
- 🔄 16阶段全流程可视化
- 📋 流程实例追踪
- ⚠️ 异常监控和改进

**使用步骤**:
1. 点击"流程管理" → "流程列表"
2. 查看已定义的业务流程
3. 点击"流程跟踪"查看执行情况

**D. 业务管理**
- 👥 客户管理（CRUD操作）
- 📦 订单管理（状态追踪）
- 🎯 项目管理（进度监控）

**使用步骤**:
1. 点击"业务管理" → "客户管理"
2. 查看客户列表
3. 可以添加、编辑、删除客户

---

### 2. OpenWebUI 统一交互中心 ⭐⭐⭐⭐

#### 访问地址
```
http://localhost:3000
```

#### 主要功能

**A. AI聊天**
- 💬 与Qwen2.5-7B对话
- 📚 集成RAG知识检索
- 💼 查询ERP数据

**使用示例**:
```
用户: "帮我分析一下本月的财务情况"
AI: [调用ERP API，返回财务分析]

用户: "上传一份PDF文件"
AI: [使用RAG处理文件]
```

**B. 文件处理**
- 📄 上传各种格式文件
- 🔍 自动解析和索引
- 💡 智能问答

---

### 3. 任务代理系统 ⭐⭐⭐⭐

#### 访问地址
```
http://localhost:8017
```

#### API使用示例

**创建数据采集任务**:
```bash
curl -X POST http://localhost:8017/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "每日新闻采集",
    "description": "从科技网站采集最新新闻",
    "task_type": "data_collection",
    "priority": 7
  }'
```

**查看任务列表**:
```bash
curl http://localhost:8017/api/tasks/list
```

**执行任务**:
```bash
curl -X POST http://localhost:8017/api/tasks/1/execute
```

---

### 4. 资源管理系统 ⭐⭐⭐⭐

#### 访问地址
```
http://localhost:8018/docs
```

#### API使用示例

**查看系统资源**:
```bash
curl http://localhost:8018/api/resources/system
```

**检测资源冲突**:
```bash
curl "http://localhost:8018/api/resources/conflicts/detect?services=ollama&services=rag-service"
```

**获取启动顺序**:
```bash
curl http://localhost:8018/api/resources/startup/status
```

---

### 5. 股票交易系统 ⭐⭐⭐

#### 访问地址
```
http://localhost:8014/docs
```

#### API使用示例

**获取股票数据**:
```bash
curl http://localhost:8014/api/stock/quote/AAPL
```

**运行策略分析**:
```bash
curl -X POST http://localhost:8014/api/strategy/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "strategy": "trend_following"
  }'
```

---

### 6. 趋势分析系统 ⭐⭐⭐

#### 访问地址
```
http://localhost:8015/docs
```

#### API使用示例

**启动新闻爬取**:
```bash
curl -X POST http://localhost:8015/api/crawl/news \
  -H "Content-Type: application/json" \
  -d '{
    "source": "tech_news",
    "category": "AI",
    "max_items": 50
  }'
```

**获取趋势报告**:
```bash
curl http://localhost:8015/api/reports/latest
```

---

### 7. 内容创作系统 ⭐⭐⭐

#### 访问地址
```
http://localhost:8016/docs
```

#### API使用示例

**收集素材**:
```bash
curl -X POST http://localhost:8016/api/materials/collect \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["xiaohongshu", "douyin"],
    "topic": "AI技术",
    "count": 20
  }'
```

**生成内容**:
```bash
curl -X POST http://localhost:8016/api/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "type": "article",
    "topic": "人工智能发展趋势",
    "length": 1500
  }'
```

---

## 🔧 常见问题

### Q1: 如何停止所有服务？

```bash
./scripts/stop_all_services.sh
```

### Q2: 如何查看服务日志？

```bash
# 查看所有日志
ls -la logs/

# 查看特定服务日志
tail -f logs/ERP-Backend.log
```

### Q3: 如何重启单个服务？

```bash
# 1. 找到服务进程
lsof -i :8013

# 2. 停止进程
kill -9 <PID>

# 3. 重新启动
cd "💼 Intelligent ERP & Business Management"
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8013
```

### Q4: ERP页面打不开怎么办？

```bash
# 方法1: 强制刷新浏览器
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# 方法2: 使用无痕模式
# Mac: Cmd + Shift + N
# Windows: Ctrl + Shift + N

# 方法3: 重启服务
./scripts/stop_all_services.sh
./scripts/start_all_services.sh
```

### Q5: 如何添加测试数据？

```bash
cd "💼 Intelligent ERP & Business Management"
source venv/bin/activate

# 添加财务数据
python scripts/add_test_data.py

# 添加业务数据
python scripts/add_business_test_data.py

# 添加流程数据
python scripts/add_process_data.py
```

---

## 🛠️ 故障排除

### 问题1: 端口被占用

**现象**: 服务启动失败，提示端口已被使用

**解决**:
```bash
# 查找占用进程
lsof -i :8013

# 终止进程
kill -9 <PID>

# 重新启动
./scripts/start_all_services.sh
```

### 问题2: 数据库连接失败

**现象**: ERP后端报错"数据库连接失败"

**解决**:
```bash
# 检查数据库文件
ls -la "💼 Intelligent ERP & Business Management/erp.db"

# 如果不存在，运行测试数据脚本会自动创建
cd "💼 Intelligent ERP & Business Management"
python scripts/add_test_data.py
```

### 问题3: npm install失败

**现象**: ERP前端启动失败

**解决**:
```bash
cd "💼 Intelligent ERP & Business Management/web/frontend"

# 清理并重新安装
rm -rf node_modules package-lock.json
npm install
```

### 问题4: Python依赖缺失

**现象**: 服务启动报错"ModuleNotFoundError"

**解决**:
```bash
cd "💼 Intelligent ERP & Business Management"

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 📊 使用技巧

### 技巧1: 使用监控面板

```bash
# 打开监控面板
open monitoring/dashboard.html
```

实时查看：
- ✅ 所有服务运行状态
- ✅ 系统资源使用
- ✅ 请求统计
- ✅ 系统告警

### 技巧2: 查看API文档

所有服务都提供Swagger文档：
```bash
open http://localhost:8013/docs  # ERP API
open http://localhost:8017/docs  # 任务代理API
open http://localhost:8018/docs  # 资源管理API
```

### 技巧3: 批量测试API

```bash
# 测试ERP健康检查
curl http://localhost:8013/health

# 测试所有服务
for port in 8011 8013 8014 8015 8016 8017 8018 8019; do
    echo "Testing port $port:"
    curl -s "http://localhost:$port/health" | jq .
done
```

### 技巧4: 实时查看日志

```bash
# 实时查看所有错误日志
tail -f logs/*_error.log

# 实时查看特定服务日志
tail -f logs/ERP-Backend.log
```

---

## 🎯 最佳实践

### 1. 日常使用流程

**早上启动**:
```bash
./scripts/start_all_services.sh
```

**工作中**:
- 使用ERP系统管理业务
- 使用OpenWebUI进行AI对话
- 使用各API接口集成业务

**晚上停止**:
```bash
./scripts/stop_all_services.sh
```

### 2. 数据管理

**备份数据**:
```bash
# 备份ERP数据库
cp "💼 Intelligent ERP & Business Management/erp.db" \
   "backups/erp_$(date +%Y%m%d).db"
```

**恢复数据**:
```bash
# 恢复ERP数据库
cp "backups/erp_20251103.db" \
   "💼 Intelligent ERP & Business Management/erp.db"
```

### 3. 性能优化

**如果系统运行慢**:
1. 查看资源使用: http://localhost:8018/api/resources/system
2. 检测资源冲突: http://localhost:8018/api/resources/conflicts/detect
3. 应用优化建议

**如果特定功能慢**:
1. 查看日志找出慢查询
2. 添加缓存
3. 优化数据库查询

---

## 💡 高级功能

### 1. 自定义任务

创建自定义任务脚本：

```python
import requests

# 创建任务
task = {
    "name": "我的定时任务",
    "description": "每天定时执行的数据处理",
    "task_type": "data_processing",
    "priority": 8,
    "config": {
        "schedule": "daily",
        "time": "09:00"
    }
}

response = requests.post(
    "http://localhost:8017/api/tasks/create",
    json=task
)

print(response.json())
```

### 2. 集成外部API

在任意服务中集成外部API：

```python
from common.error_handler import retry_on_error
import aiohttp

@retry_on_error(max_retries=3)
async def call_external_api():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as response:
            return await response.json()
```

### 3. 自定义监控

添加自定义监控指标：

```python
from common.performance_config import global_monitor

# 记录业务指标
global_monitor.record_metric(
    "order_count",
    order_count,
    {"type": "business"}
)

# 查看指标统计
stats = global_monitor.get_metric_stats("order_count")
```

---

## 📞 获取帮助

### 文档资源
- [项目README](./README.md)
- [快速开始](./QUICK_START.md)
- [优化指南](./OPTIMIZATION_PLAN.md)
- [完成报告](./🏆 PROJECT_FINALE.md)

### 日志文件
- 主日志: `logs/<service>.log`
- 错误日志: `logs/<service>_error.log`

### API文档
- 各服务的 `/docs` 端点

---

## 🎉 开始你的AI Stack之旅吧！

```bash
# 一键启动
./scripts/start_all_services.sh

# 访问ERP系统
open http://localhost:8012

# 祝你使用愉快！🚀
```

---

**项目路径**: `/Users/ywc/ai-stack-super-enhanced`  
**用户手册版本**: v1.1.0  
**最后更新**: 2025-11-03  

---

**💡 提示**: 从ERP系统开始是最好的选择，功能最完整！


