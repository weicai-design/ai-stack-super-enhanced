# 📍 在OpenWebUI中查看AI Stack集成

**重要**: Functions需要手动安装才能在OpenWebUI中看到！

---

## 🔍 Functions在哪里？

### 方法1: 通过设置菜单（推荐）

**步骤**:
1. 打开 http://localhost:3000
2. **登录**（首次需注册）
3. 点击**左下角的用户头像/名字**
4. 选择 **"Settings"** (设置)
5. 在左侧菜单中找到 **"Functions"**
6. 应该看到Functions列表（如果已安装）

### 方法2: 直接访问URL

在浏览器地址栏输入:
```
http://localhost:3000/workspace/functions
```

### 方法3: 通过Admin面板

```
http://localhost:3000/admin/functions
```

---

## ⚠️ 如果看不到Functions

说明Functions还未安装，需要手动上传。

### 安装步骤

#### Step 1: 进入Functions页面

访问: http://localhost:3000/workspace/functions

#### Step 2: 点击添加

点击页面右上角的 **"+"** 按钮

#### Step 3: 上传Function代码

**方式A: 复制粘贴（推荐）**

1. 在终端执行:
   ```bash
   cd /Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/openwebui-functions
   cat rag_integration.py | pbcopy
   ```

2. 在OpenWebUI中:
   - 点击代码编辑区
   - 粘贴 (Command+V)
   - 点击 **Save**

**方式B: 从URL导入**

1. 点击 **"Import from URL"** (如果有)
2. 输入本地文件路径或URL

**方式C: 拖放文件**

1. 直接拖动 `.py` 文件到上传区域

#### Step 4: 配置Function

1. 找到刚添加的Function
2. 点击 **⚙️** (设置图标)
3. 配置API端点:
   ```
   rag_api_endpoint: http://host.docker.internal:8011
   ```
4. 保存

#### Step 5: 启用Function

确保Function右侧的开关是**绿色**（开启状态）

---

## 🎨 OpenWebUI界面说明

### 主界面结构

```
┌─────────────────────────────────────────┐
│  Open WebUI                             │
├─────────────────────────────────────────┤
│                                         │
│  左侧边栏:                               │
│  - 新建聊天                              │
│  - 聊天历史                              │
│  - ...                                  │
│                                         │
│  左下角:                                 │
│  👤 用户头像/名字  ← 点击这里            │
│     └→ Settings                         │
│        └→ Functions  ← 在这里！          │
│                                         │
└─────────────────────────────────────────┘
```

### Functions页面应该看到什么

如果Functions已安装，你会看到：

```
Functions 列表
┌────────────────────────────────────┐
│ + (添加按钮)                        │
├────────────────────────────────────┤
│ 📚 RAG Knowledge Integration       │
│    [开关] ⚙️ 🗑️                   │
├────────────────────────────────────┤
│ 💼 ERP Business Query              │
│    [开关] ⚙️ 🗑️                   │
├────────────────────────────────────┤
│ ... (其他Functions)                │
└────────────────────────────────────┘
```

---

## 🧪 如何知道集成成功？

### 测试1: 查看Functions列表

进入 Functions 页面，应该看到7个Functions

### 测试2: 在聊天中使用

创建新聊天，输入:
```
/aistack
```

如果集成成功，会看到命令提示

### 测试3: 智能路由

直接提问:
```
什么是机器学习？
```

如果集成成功，RAG会自动检索知识库

---

## ❌ 如果完全看不到Functions菜单

可能原因：
1. **未登录** - 需要先注册/登录
2. **不是管理员** - 首个注册用户自动成为管理员
3. **版本不支持** - 需要较新版本的OpenWebUI

**解决**:
- 确保已登录
- 使用首个注册的账号
- 更新OpenWebUI版本

---

## 💡 当前情况说明

### 已完成

- ✅ OpenWebUI运行正常
- ✅ 7个Functions代码已开发
- ✅ API Gateway已启动

### 待完成

- ⏳ Functions需要在OpenWebUI界面中手动上传
- ⏳ 每个Function约1分钟，共7分钟

### 为什么需要手动？

因为是新启动的OpenWebUI容器，数据库是空的。Functions需要通过UI界面上传到OpenWebUI的数据库中。

---

## 🚀 快速安装

**现在RAG Integration已在剪贴板**

在OpenWebUI中：
1. Settings → Functions
2. 点击 +
3. 粘贴 (Command+V)
4. Save

重复7次即可！

---

**创建时间**: 2025-11-04
**文件位置**: OpenWebUI-Integration/📍 在OpenWebUI中查看集成.md



