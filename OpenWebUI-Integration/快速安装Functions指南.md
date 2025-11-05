# 🚀 OpenWebUI Functions 快速安装指南

**重要**: Functions需要手动安装到OpenWebUI中才能使用！

---

## 📋 安装步骤

### Step 1: 确保OpenWebUI运行

访问: http://localhost:3000

如果未运行，执行：
```bash
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  --name open-webui \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### Step 2: 登录OpenWebUI

1. 打开 http://localhost:3000
2. 首次访问需要**注册账号**（本地账号，无需联网）
3. 填写：
   - 姓名：任意
   - 邮箱：任意（如 admin@local.com）
   - 密码：设置密码
4. 点击注册并登录

### Step 3: 进入Functions管理

1. 点击左下角 **头像/用户名**
2. 选择 **设置** (Settings)
3. 点击左侧菜单 **Functions**
4. 或直接访问: http://localhost:3000/admin/functions

### Step 4: 安装RAG Integration Function

#### 方法A: 复制粘贴（推荐）

1. 点击 **+** 或 **Import Functions**
2. 选择 **From Python Code**
3. 打开文件：
   ```bash
   cat /Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/openwebui-functions/rag_integration.py
   ```
4. 复制全部内容
5. 粘贴到OpenWebUI
6. 点击 **Save**

#### 方法B: 直接导入（如支持）

1. 点击 **Import Functions**
2. 选择文件 `rag_integration.py`
3. 点击 **Import**

### Step 5: 配置RAG Integration

1. 找到刚安装的 **RAG Knowledge Integration**
2. 点击 **⚙️** (设置图标)
3. 配置Valves：
   ```
   rag_api_endpoint: http://host.docker.internal:8011
   search_top_k: 5
   enable_kg_query: true
   ```
4. 点击 **Save**

### Step 6: 启用Function

1. 确保Function的开关是 **开启** 状态（绿色）
2. 如果是关闭的，点击开关启用

### Step 7: 重复安装其他Functions

重复Step 4-6，安装：
- ✅ `erp_query.py` (ERP查询)
- ✅ `stock_analysis.py` (股票分析)

**ERP Query配置**:
```
erp_api_endpoint: http://host.docker.internal:8013
enable_write: false
```

**Stock Analysis配置**:
```
stock_api_endpoint: http://localhost:8014
enable_trading: false
max_trade_amount: 10000.0
```

**注意**: 
- 如果OpenWebUI在Docker中，用 `host.docker.internal`
- 如果本地运行，用 `localhost`

---

## 🧪 测试Functions

### 1. 测试RAG Integration

在OpenWebUI聊天框输入：

```
/rag search AI技术
```

应该看到：
```
🔄 正在处理RAG请求...
✅ RAG搜索完成
🔍 RAG搜索结果
[显示搜索结果]
```

### 2. 测试ERP Query

```
/erp financial
```

应该看到：
```
🔄 正在查询ERP系统...
✅ 财务数据查询完成
💰 财务数据 (month)
[显示财务数据]
```

### 3. 测试Stock Analysis

```
/stock price 600519
```

应该看到：
```
🔄 正在处理股票请求...
✅ 价格查询完成
📈 贵州茅台 (600519)
当前价格: ¥1,850.00
[显示详细数据]
```

### 4. 测试自动增强

```
什么是深度学习？
```

应该看到RAG自动检索知识库并增强回答。

---

## 🔍 故障排查

### 问题1: Function无法调用API

**原因**: API端点配置错误或服务未运行

**解决**:
```bash
# 检查服务状态
python3 scripts/system_health_check.py

# 确保服务运行
./scripts/start_all_final.sh
```

### 问题2: Docker网络无法访问

**原因**: Docker容器无法访问宿主机

**解决**:
1. 使用 `host.docker.internal` 替代 `localhost`
2. 或使用 `--network host` 启动OpenWebUI

### 问题3: Function报错

**原因**: 依赖缺失或配置错误

**解决**:
1. 检查API端点配置
2. 查看OpenWebUI日志：
   ```bash
   docker logs open-webui
   ```

### 问题4: 找不到Functions菜单

**原因**: 可能需要管理员权限

**解决**:
1. 确保使用首个注册的账号（自动为管理员）
2. 或访问: http://localhost:3000/admin/functions

---

## 📊 当前集成状态

### ✅ 已集成 (3个)

- ✅ RAG系统 - 知识库搜索、文档摄入、知识图谱
- ✅ ERP系统 - 财务、订单、生产、库存查询
- ✅ 股票系统 - 价格、分析、情绪、交易

### ⏳ 待集成 (6个)

- ⏳ 内容创作系统
- ⏳ 趋势分析系统
- ⏳ 任务代理系统
- ⏳ 资源管理系统
- ⏳ 自我学习系统
- ⏳ 终端执行功能

---

## 💡 使用建议

### 1. 先测试基础功能

从简单命令开始：
```
/rag search test
/erp dashboard
/stock sentiment
```

### 2. 尝试自动增强

直接提问：
```
什么是机器学习？
今天的财务数据
贵州茅台价格
```

### 3. 组合使用

一次对话使用多个系统：
```
帮我查询今天的财务数据，然后从知识库搜索同行业的对比数据
```

---

## 🎯 集成效果

**之前**: 需要分别访问多个系统
- ERP: http://localhost:8012
- RAG: http://localhost:8011
- 股票: http://localhost:8014

**现在**: 一个界面统一访问
- 全部通过 http://localhost:3000
- 对话式交互
- 自动智能增强

---

## 🎉 下一步

1. ✅ 测试已安装的3个Functions
2. ⏳ 继续开发剩余Functions
3. ⏳ 开发API Gateway
4. ⏳ 完整集成测试

---

**创建时间**: 2025-11-04  
**文件位置**: OpenWebUI-Integration/快速安装Functions指南.md  
**下一步**: 在OpenWebUI中安装并测试Functions



