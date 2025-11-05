# 💬 OpenWebUI 统一交互中心

**版本**: v1.1.0  
**核心理念**: 在OpenWebUI聊天框中操作AI Stack的所有功能  

---

## 🎯 核心功能

### 统一交互入口
**访问**: http://localhost:3000

在OpenWebUI聊天中可以：
- 📚 操作RAG知识库
- 💼 管理ERP企业系统
- 📈 查看股票交易
- 🔍 启动趋势分析
- ✍️ 创建内容
- 🤖 管理任务
- ⚙️ 监控资源
- 🧠 查看系统分析

**全部通过自然语言在聊天中完成！**

---

## 🚀 快速开始

### 一键安装

```bash
cd "/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center"

# 运行安装脚本
./一键安装OpenWebUI集成.sh
```

### 手动安装

```bash
# 1. 复制Functions
mkdir -p ~/.openwebui/functions
cp openwebui_functions/all_systems_tools.py ~/.openwebui/functions/
cp openwebui_functions/rag_tools.py ~/.openwebui/functions/

# 2. 重启OpenWebUI
docker restart open-webui

# 3. 在OpenWebUI中启用（见下文）
```

### 在OpenWebUI中启用

1. 访问 http://localhost:3000
2. 点击右上角头像 → **Admin Panel**
3. 点击左侧 **Functions**
4. 找到 **AI Stack Tools** 和 **RAG Tools**
5. 点击启用开关 ✅
6. 保存配置

---

## 💬 使用示例

### 在聊天中直接说：

#### 查看系统状态
```
"查看所有系统状态"
→ 返回所有9个系统的运行状态
```

#### ERP管理
```
"查看本月财务情况"
→ 返回财务看板数据

"查看客户列表"
→ 返回客户信息

"查看订单ORD001"
→ 返回订单详情
```

#### 股票分析
```
"查看AAPL股票价格"
→ 返回实时行情

"用趋势策略分析TSLA"
→ 返回策略建议
```

#### RAG知识库
```
"搜索知识库中的Python内容"
→ 返回相关知识

"将这段文本保存到知识库"
→ 保存成功确认
```

#### 趋势分析
```
"爬取最新科技新闻"
→ 启动爬虫任务

"生成AI行业趋势报告"
→ 返回分析报告
```

#### 内容创作
```
"生成一篇关于AI的小红书文章"
→ 返回生成的内容

"从抖音收集旅游素材"
→ 返回素材列表
```

#### 任务管理
```
"创建每日数据采集任务"
→ 任务创建成功

"查看运行中的任务"
→ 返回任务列表
```

#### 资源监控
```
"查看系统资源"
→ 返回CPU/内存/磁盘

"检测资源冲突"
→ 返回冲突检测结果
```

#### 获取帮助
```
"有哪些功能"
"帮助"
→ 返回完整功能清单
```

---

## 📊 集成架构

### 三层架构

**1. 用户层（OpenWebUI界面）**
- 聊天框输入
- 自然语言理解
- 结果展示

**2. 功能层（Functions）**
- 26个统一工具
- API调用封装
- 结果格式化

**3. 服务层（各系统API）**
- 9大系统后端
- 132+个API接口
- 实际业务逻辑

---

## 🌟 核心优势

### ✅ 统一体验
- 只需一个OpenWebUI界面
- 所有功能聊天框操作
- 无需切换页面

### ✅ 自然交互
- 说出你的需求
- AI自动理解
- 自动调用正确的API

### ✅ 智能增强
- RAG自动增强回答
- 历史对话自动保存
- 知识不断积累

### ✅ 完全集成
- 9大系统全覆盖
- 132+个API可调用
- 所有功能可用

---

## 📁 文件结构

```
💬 Intelligent OpenWebUI Interaction Center/
├── openwebui_functions/
│   ├── all_systems_tools.py    # 26个统一工具（主要）
│   └── rag_tools.py             # 7个RAG工具
│
├── plugins/
│   ├── rag_integration_plugin.py   # RAG后台集成
│   └── erp_integration_plugin.py   # ERP后台集成
│
├── web/
│   └── rag-frontend/
│       └── index.html           # RAG辅助管理页面（可选）
│
├── 一键安装OpenWebUI集成.sh     # 安装脚本
├── OpenWebUI统一操作指南.md      # 操作指南
├── OPENWEBUI_RAG_INTEGRATION.md  # RAG集成说明
├── 如何使用RAG功能.md           # RAG使用说明
└── README.md                     # 本文件
```

---

## 🔧 配置说明

### API地址配置

在OpenWebUI Functions配置中：

**Docker环境**（默认）:
```
RAG_API:      http://host.docker.internal:8011
ERP_API:      http://host.docker.internal:8013
STOCK_API:    http://host.docker.internal:8014
TREND_API:    http://host.docker.internal:8015
CONTENT_API:  http://host.docker.internal:8016
TASK_API:     http://host.docker.internal:8017
RESOURCE_API: http://host.docker.internal:8018
LEARNING_API: http://host.docker.internal:8019
```

**本地环境**:
```
将 host.docker.internal 替换为 localhost
```

---

## 📖 详细文档

- [OpenWebUI统一操作指南](./OpenWebUI统一操作指南.md)
- [如何使用RAG功能](./如何使用RAG功能.md)
- [OpenWebUI RAG集成](./OPENWEBUI_RAG_INTEGRATION.md)

---

## 🎉 开始使用

```bash
# 安装
./一键安装OpenWebUI集成.sh

# 访问
open http://localhost:3000

# 在聊天中说：
"查看所有系统状态"
"查看本月财务"
"查看AAPL股票"
"帮助"
```

---

**主入口**: http://localhost:3000  
**功能数**: 26个统一工具  
**覆盖**: 所有9大系统  

**🎉 所有功能都在聊天框中！**


