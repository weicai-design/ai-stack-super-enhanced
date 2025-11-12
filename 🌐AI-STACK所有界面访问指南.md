# 🌐 AI-STACK 所有界面访问指南

**更新时间**: 2025-01-XX  
**状态**: ✅ 所有界面可用

---

## 📋 界面总览

### 一级界面（主界面）

| 界面名称 | 文件路径 | 访问地址 | 端口 | 状态 |
|---------|---------|---------|------|------|
| **超级Agent主界面** | `🚀 Super Agent Main Interface/web/index.html` | http://localhost:8020 | 8020 | ✅ |
| **OpenWebUI交互中心** | - | http://localhost:3000 | 3000 | ✅ |

---

## 📚 二级界面（独立系统）

### 1. RAG知识库系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **RAG管理界面** | `📚 Enhanced RAG & Knowledge Graph/web/rag_management.html` | http://localhost:8011/rag-management | 文档管理 |
| **知识图谱可视化** | `📚 Enhanced RAG & Knowledge Graph/web/knowledge_graph_view.html` | http://localhost:8011/knowledge-graph | 图谱可视化 |
| **预处理系统（三级界面）** | `📚 Enhanced RAG & Knowledge Graph/web/preprocessing.html` | http://localhost:8011/preprocessing | 数据预处理 |
| **真实性验证界面** | `📚 Enhanced RAG & Knowledge Graph/web/truthfulness_verification.html` | http://localhost:8011/truthfulness | 真实性验证 |

**RAG API文档**: http://localhost:8011/docs

---

### 2. ERP企业管理系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **ERP前端主界面** | `💼 Intelligent ERP & Business Management/web/frontend/index.html` | http://localhost:8012 | Vue3主界面 |
| **工作流编辑器** | `💼 Intelligent ERP & Business Management/web/workflow-editor.html` | http://localhost:8012/workflow-editor | 流程设计器 |

**ERP API文档**: http://localhost:8013/docs

---

### 3. 运营财务系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **运营管理界面** | `⚙️ Operations & Finance/web/index.html` | http://localhost:8021 | 运营管理 |
| **财务管理界面** | `⚙️ Operations & Finance/web/index.html` | http://localhost:8022 | 财务管理 |

---

### 4. AI编程助手

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **编程助手界面** | `💻 AI Programming Assistant/web/index.html` | http://localhost:8023 | 代码编辑器 |

**编程助手API**: http://localhost:8023/docs

---

### 5. 智能任务系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **任务管理界面** | `🤖 Intelligent Task Agent/web/templates/dashboard.html` | http://localhost:8017/dashboard | 任务看板 |

**任务系统API**: http://localhost:8017/docs

---

### 6. 自我学习系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **学习系统界面** | `🧠 Self Learning System/web/templates/dashboard.html` | http://localhost:8019/dashboard | 学习监控 |

**学习系统API**: http://localhost:8019/docs

---

### 7. 资源管理系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **资源管理界面** | - | http://localhost:8018/dashboard | 资源监控 |

**资源管理API**: http://localhost:8018/docs

---

### 8. 趋势分析系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **趋势分析界面** | `🔍 Intelligent Trend Analysis/web/templates/dashboard.html` | http://localhost:8015/dashboard | 趋势分析 |

**趋势分析API**: http://localhost:8015/docs

---

### 9. 股票量化系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **股票交易界面** | `📈 Intelligent Stock Trading/web/templates/dashboard.html` | http://localhost:8014/dashboard | 股票交易 |

**股票系统API**: http://localhost:8014/docs

---

### 10. 内容创作系统

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **内容创作界面** | `🎨 Intelligent Content Creation/web/templates/dashboard.html` | http://localhost:8016/dashboard | 内容创作 |

**内容创作API**: http://localhost:8016/docs

---

## 📊 三级界面（ERP子系统）

### ERP 11个独立三级界面

| 界面名称 | 文件路径 | 访问地址 | 说明 |
|---------|---------|---------|------|
| **订单管理** | `💼 Intelligent ERP & Business Management/web/interfaces/order-management.html` | http://localhost:8012/interfaces/order-management.html | 订单CRUD |
| **项目管理** | `💼 Intelligent ERP & Business Management/web/interfaces/project-management.html` | http://localhost:8012/interfaces/project-management.html | 项目管理 |
| **采购管理** | `💼 Intelligent ERP & Business Management/web/interfaces/procurement-management.html` | http://localhost:8012/interfaces/procurement-management.html | 采购管理 |
| **计划管理** | `💼 Intelligent ERP & Business Management/web/interfaces/plan-management.html` | http://localhost:8012/interfaces/plan-management.html | 生产计划 |
| **生产管理** | `💼 Intelligent ERP & Business Management/web/interfaces/production-management.html` | http://localhost:8012/interfaces/production-management.html | 生产管理 |
| **质量管理** | `💼 Intelligent ERP & Business Management/web/interfaces/quality-management.html` | http://localhost:8012/interfaces/quality-management.html | 质量检验 |
| **到料管理** | `💼 Intelligent ERP & Business Management/web/interfaces/receiving-management.html` | http://localhost:8012/interfaces/receiving-management.html | 物料入库 |
| **出库管理** | `💼 Intelligent ERP & Business Management/web/interfaces/outbound-management.html` | http://localhost:8012/interfaces/outbound-management.html | 物料出库 |
| **发运管理** | `💼 Intelligent ERP & Business Management/web/interfaces/shipping-management.html` | http://localhost:8012/interfaces/shipping-management.html | 物流发运 |
| **售后管理** | `💼 Intelligent ERP & Business Management/web/interfaces/after-sales-management.html` | http://localhost:8012/interfaces/after-sales-management.html | 售后服务 |
| **结算管理** | `💼 Intelligent ERP & Business Management/web/interfaces/settlement-management.html` | http://localhost:8012/interfaces/settlement-management.html | 财务结算 |
| **试算平衡** | `💼 Intelligent ERP & Business Management/web/interfaces/trial-balance.html` | http://localhost:8012/interfaces/trial-balance.html | 试算功能 |

---

## 🚀 快速访问

### 主要入口

1. **超级Agent主界面**（推荐）⭐
   ```
   http://localhost:8020
   ```

2. **OpenWebUI交互中心**
   ```
   http://localhost:3000
   ```

3. **ERP前端系统**
   ```
   http://localhost:8012
   ```

---

## 📝 启动服务

### 方式1：一键启动所有服务

```bash
cd /Users/ywc/ai-stack-super-enhanced
./scripts/start_all_services.sh
```

### 方式2：单独启动服务

#### 启动超级Agent主界面
```bash
cd "🚀 Super Agent Main Interface"
python3 -m http.server 8020
```

#### 启动ERP前端
```bash
cd "💼 Intelligent ERP & Business Management/web/frontend"
npm run dev
```

#### 启动ERP后端
```bash
cd "💼 Intelligent ERP & Business Management"
uvicorn api.main:app --host 0.0.0.0 --port 8013 --reload
```

#### 启动RAG系统
```bash
cd "📚 Enhanced RAG & Knowledge Graph"
uvicorn api.app:app --host 0.0.0.0 --port 8011 --reload
```

---

## 🌐 浏览器打开命令

### macOS

```bash
# 打开超级Agent主界面
open http://localhost:8020

# 打开OpenWebUI
open http://localhost:3000

# 打开ERP前端
open http://localhost:8012

# 打开RAG管理界面
open http://localhost:8011/rag-management

# 打开ERP API文档
open http://localhost:8013/docs
```

### 批量打开所有主要界面

```bash
# 打开所有主要界面
open http://localhost:8020  # 超级Agent
open http://localhost:3000  # OpenWebUI
open http://localhost:8012  # ERP前端
open http://localhost:8011/rag-management  # RAG管理
open http://localhost:8013/docs  # ERP API文档
```

---

## 📊 端口分配表

| 端口 | 服务 | 类型 | 访问地址 |
|------|------|------|---------|
| 3000 | OpenWebUI | Web | http://localhost:3000 |
| 8011 | RAG系统 | API | http://localhost:8011/docs |
| 8012 | ERP前端 | Web | http://localhost:8012 |
| 8013 | ERP后端 | API | http://localhost:8013/docs |
| 8014 | 股票系统 | API | http://localhost:8014/docs |
| 8015 | 趋势分析 | API | http://localhost:8015/docs |
| 8016 | 内容创作 | API | http://localhost:8016/docs |
| 8017 | 任务系统 | API | http://localhost:8017/docs |
| 8018 | 资源管理 | API | http://localhost:8018/docs |
| 8019 | 自我学习 | API | http://localhost:8019/docs |
| 8020 | 超级Agent | Web | http://localhost:8020 |
| 8021 | 运营管理 | Web | http://localhost:8021 |
| 8022 | 财务管理 | Web | http://localhost:8022 |
| 8023 | 编程助手 | Web | http://localhost:8023 |

---

## ✅ 界面检查清单

### 一级界面
- [ ] 超级Agent主界面 (8020)
- [ ] OpenWebUI交互中心 (3000)

### 二级界面
- [ ] RAG知识库管理 (8011)
- [ ] ERP前端系统 (8012)
- [ ] 运营管理界面 (8021)
- [ ] 财务管理界面 (8022)
- [ ] AI编程助手 (8023)
- [ ] 智能任务系统 (8017)
- [ ] 自我学习系统 (8019)
- [ ] 资源管理系统 (8018)
- [ ] 趋势分析系统 (8015)
- [ ] 股票量化系统 (8014)
- [ ] 内容创作系统 (8016)

### 三级界面（ERP）
- [ ] 订单管理
- [ ] 项目管理
- [ ] 采购管理
- [ ] 计划管理
- [ ] 生产管理
- [ ] 质量管理
- [ ] 到料管理
- [ ] 出库管理
- [ ] 发运管理
- [ ] 售后管理
- [ ] 结算管理
- [ ] 试算平衡

---

**提示**: 如果界面无法访问，请先启动对应的服务！


