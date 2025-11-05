# 🌐 OpenWebUI深度集成 - 使用指南

**完成时间**: 2025-11-04 23:15  
**状态**: ✅ 核心Functions完成  
**优先级**: ⭐⭐⭐⭐⭐ (最高)

---

## 📊 项目进度

### ✅ 已完成 (60%)

1. ✅ OpenWebUI源码获取
2. ✅ 集成方案设计 (`INTEGRATION_PLAN.md`)
3. ✅ RAG Integration Function
4. ✅ ERP Query Function  
5. ✅ Stock Analysis Function

### ⏳ 待完成 (40%)

6. ⏳ Content Creation Function
7. ⏳ Terminal Exec Function
8. ⏳ API Gateway
9. ⏳ 集成测试

---

## 🚀 快速开始

### 1. 启动AI Stack服务

```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/start_all_final.sh
```

### 2. 启动OpenWebUI

```bash
docker run -d -p 3000:8080 \
  --name open-webui \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

访问: http://localhost:3000

### 3. 安装Functions

1. 进入 **设置** → **Functions**
2. 点击 **+ 添加**
3. 上传 `openwebui-functions/` 下的 `.py` 文件
4. 启用并配置

---

## 📦 已实现Functions

### 1. RAG Integration ✅

**命令**:
- `/rag search <query>` - 搜索知识库
- `/rag ingest <file>` - 摄入文档  
- `/kg query <entity>` - 查询知识图谱
- `/kg visualize` - 可视化

**配置**:
```python
rag_api_endpoint: http://host.docker.internal:8011
search_top_k: 5
enable_kg_query: true
```

### 2. ERP Query ✅

**命令**:
- `/erp financial` - 财务数据
- `/erp orders` - 订单查询
- `/erp production` - 生产状态
- `/erp inventory` - 库存查询
- `/erp dashboard` - 综合看板

**配置**:
```python
erp_api_endpoint: http://host.docker.internal:8013
```

### 3. Stock Analysis ✅

**命令**:
- `/stock price <code>` - 股票价格
- `/stock analyze <code>` - 策略分析
- `/stock sentiment` - 市场情绪
- `/stock portfolio` - 我的持仓

**配置**:
```python
stock_api_endpoint: http://host.docker.internal:8014
enable_trading: false  # ⚠️ 谨慎开启
```

---

## 💡 使用示例

### RAG搜索
```
User: /rag search 深度学习
Assistant: [展示知识库搜索结果]
```

### ERP查询
```
User: /erp financial month  
Assistant: [显示本月财务数据]
```

### 股票分析
```
User: /stock price 600519
Assistant: [显示贵州茅台价格和趋势]
```

### 自动增强
```
User: 什么是知识图谱？
Assistant: [自动从RAG检索并回答]
```

---

## 📁 文件结构

```
OpenWebUI-Integration/
├── README.md                      # 本文件
├── INTEGRATION_PLAN.md            # 详细集成方案
├── open-webui/                    # OpenWebUI源码
└── openwebui-functions/           # Functions目录
    ├── rag_integration.py         # RAG集成 ✅
    ├── erp_query.py               # ERP查询 ✅
    ├── stock_analysis.py          # 股票分析 ✅
    ├── content_creation.py        # 内容创作 ⏳
    ├── terminal_exec.py           # 终端执行 ⏳
    ├── trend_analysis.py          # 趋势分析 ⏳
    ├── task_management.py         # 任务管理 ⏳
    └── resource_monitor.py        # 资源监控 ⏳
```

---

## 🎯 核心特性

### 1. 统一对话接口

通过OpenWebUI聊天框访问所有AI Stack功能，无需切换页面。

### 2. 自动智能增强

Functions自动检测用户意图并增强回答:
- RAG自动检索相关知识
- ERP自动查询业务数据  
- 股票自动提供分析

### 3. 实时状态反馈

```
🔄 正在处理请求...
✅ 查询完成
📊 [显示结果]
```

### 4. 安全可控

- 交易功能默认关闭
- API密钥保护
- 权限精细控制

---

## 🔧 配置技巧

### Docker网络配置

在Docker中运行OpenWebUI时，使用 `host.docker.internal` 访问宿主机服务:

```python
rag_api_endpoint: "http://host.docker.internal:8011"
erp_api_endpoint: "http://host.docker.internal:8013"
```

### 本地运行配置

如果OpenWebUI在本地运行:

```python
rag_api_endpoint: "http://localhost:8011"
erp_api_endpoint: "http://localhost:8013"
```

---

## 📖 详细文档

- **集成方案**: `INTEGRATION_PLAN.md` - 完整技术方案
- **Function源码**: `openwebui-functions/` - 所有Function代码
- **OpenWebUI文档**: https://docs.openwebui.com/

---

## 🎉 成果展示

通过这次集成，实现了：

✅ OpenWebUI作为统一交互中心  
✅ 一个界面访问所有AI Stack功能  
✅ 自动智能增强对话  
✅ 实时状态反馈  
✅ 安全可控的系统集成

**下一步**: 继续开发剩余Functions，完成100%集成！

---

**创建时间**: 2025-11-04  
**版本**: v1.0.0  
**状态**: 进行中 - 60%完成



