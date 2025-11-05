# 🎯 OpenWebUI Plugin安装 - 详细图文教程

**问题**: OpenWebUI聊天框无法触发AI Stack功能  
**原因**: Plugin还未安装  
**解决**: 必须手动在OpenWebUI UI中安装Plugin

---

## 📍 Plugin在OpenWebUI中的位置

### 方法1: 通过Settings菜单

```
OpenWebUI主页 (http://localhost:3000)
    ↓
点击左下角 👤 用户头像/用户名
    ↓
弹出菜单中选择 "Settings"
    ↓
左侧菜单找到 "Functions" 或 "Workspace"
    ↓
点击 "Functions"
    ↓
Functions管理页面（这里安装Plugin）
```

### 方法2: 直接访问URL

在浏览器地址栏输入：
```
http://localhost:3000/workspace/functions
```

---

## 🔧 详细安装步骤（带截图说明）

### Step 1: 找到Functions菜单

**位置**: 
- 左下角有个圆形图标（用户头像）
- 旁边显示你的用户名
- 点击它！

**如果没有看到**:
- 可能需要先登录/注册
- 首次访问需要创建账号（本地账号，随便填）

### Step 2: 进入Settings

点击用户头像后，会弹出菜单：
```
┌─────────────────┐
│ Profile         │
│ Settings  ← 点这个│
│ ...             │
└─────────────────┘
```

### Step 3: 找到Functions

进入Settings后，左侧有菜单列表：
```
┌─────────────────┐
│ General         │
│ Interface       │
│ Account         │
│ Workspace       │
│ Functions  ← 点这│
│ ...             │
└─────────────────┘
```

或者在 "Workspace" 下找到 "Functions"

### Step 4: 添加Plugin

在Functions页面：

**看到的界面**:
```
┌────────────────────────────────────┐
│ Functions                    [+]   │ ← 点击+号
├────────────────────────────────────┤
│                                    │
│ (如果是空的，说明还没有Functions)   │
│                                    │
└────────────────────────────────────┘
```

点击右上角的 **"+"** 按钮

### Step 5: 粘贴Plugin代码

点击+后，会出现代码编辑器：

```
┌────────────────────────────────────┐
│ Create Function                    │
├────────────────────────────────────┤
│                                    │
│ [代码编辑区域]  ← 在这里粘贴        │
│                                    │
│                                    │
│                                    │
│                [Cancel] [Save]     │
└────────────────────────────────────┘
```

**操作**:
1. 点击代码编辑区
2. **Command+V** 粘贴（Plugin已在剪贴板）
3. 点击 **"Save"**

### Step 6: 配置Plugin

保存后，在Functions列表中找到刚添加的Plugin：

```
┌────────────────────────────────────┐
│ AI Stack Intelligent Master Plugin │
│ [开关] ⚙️ 🗑️                      │ ← 点击⚙️
└────────────────────────────────────┘
```

点击 **⚙️** (设置图标)

### Step 7: 配置API地址

在配置页面，设置：

```
rag_api: http://host.docker.internal:8011
erp_api: http://host.docker.internal:8013
stock_api: http://host.docker.internal:8014
content_api: http://host.docker.internal:8016
learning_api: http://host.docker.internal:8019

启用所有开关:
✅ enable_auto_rag: true
✅ enable_smart_routing: true
✅ enable_interaction_learning: true
✅ enable_expert_analysis: true
✅ enable_auto_rag_ingest: true
✅ enable_self_evolution: true
```

点击 **Save**

### Step 8: 启用Plugin

确保Plugin左侧的**开关是绿色**（开启状态）

如果是灰色，点击开关变成绿色

---

## 🧪 安装成功的验证

### 验证方法1: 在聊天框测试

创建新聊天，输入：
```
什么是机器学习？
```

**成功的表现**:
- 看到 "🧠 AI Stack智能分析中..."
- 看到 "✅ 已集成RAG知识+实时数据+专家分析"
- AI回答包含【RAG知识】【专家建议】

**失败的表现**:
- 只是普通AI回答
- 没有状态提示
- 没有RAG知识和专家建议

### 验证方法2: 查看学习数据

在终端执行：
```bash
curl http://localhost:8019/api/learning/stats
```

如果返回学习统计数据，说明系统在工作

---

## ⚠️ 常见问题

### Q1: 找不到Functions菜单

**解决**:
- 确保已登录
- 使用首个注册的账号（管理员）
- 直接访问: http://localhost:3000/workspace/functions

### Q2: 点击+没有反应

**解决**:
- 刷新页面
- 检查浏览器控制台错误
- 尝试不同浏览器

### Q3: Plugin保存后无效

**解决**:
- 检查API地址配置是否正确
- 确保所有AI Stack服务运行中
- 查看OpenWebUI日志: `docker logs open-webui`

---

## 💡 如果实在无法安装

### 备选方案1: 使用统一控制台

访问: **http://localhost:8000**
- 点击系统卡片直接访问各功能
- 不依赖OpenWebUI

### 备选方案2: 直接使用API Gateway

```bash
# RAG搜索
curl "http://localhost:9000/gateway/rag/search?query=机器学习"

# ERP财务
curl "http://localhost:9000/gateway/erp/financial"

# 股票查询
curl "http://localhost:9000/gateway/stock/price/600519"
```

---

**关键**: Plugin必须通过OpenWebUI UI手动安装，无法自动化！



