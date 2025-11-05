# 🚀 OpenWebUI Functions 快速部署指南

**目标**: 在OpenWebUI中启用AI Stack所有功能  
**时间**: 5分钟  
**难度**: ⭐ 简单

---

## 📋 部署步骤

### 步骤1: 确保所有服务运行 ✅

```bash
cd /Users/ywc/ai-stack-super-enhanced
source venv/bin/activate
python3 scripts/system_health_check.py
```

**期望结果**: 10/10服务运行中

---

### 步骤2: 访问OpenWebUI

```bash
open http://localhost:3000
```

---

### 步骤3: 进入Functions管理

1. 在OpenWebUI左侧菜单找到 **"Functions"** 或 **"工具"** 图标
2. 点击进入Functions管理页面
3. 点击右上角的 **"+"** 或 **"Add Function"**

---

### 步骤4: 导入AI Stack工具集

1. **打开Functions代码文件**:
   ```bash
   cat "/Users/ywc/ai-stack-super-enhanced/💬 Intelligent OpenWebUI Interaction Center/openwebui_functions/all_systems_tools.py"
   ```

2. **复制全部内容** (Cmd+A, Cmd+C)

3. **粘贴到OpenWebUI**:
   - 在Functions编辑器中粘贴
   - 点击 "Save" 保存

4. **启用Function**:
   - 确保Function状态为"Enabled"

---

### 步骤5: 测试Functions

在OpenWebUI聊天框中输入：

```
查看本月财务情况
```

或

```
搜索知识库中关于Python的内容
```

**期望**: OpenWebUI自动调用相应的Function并返回结果

---

## 🎯 可用的Functions

### 1. RAG知识库相关

```
"搜索知识库..."
"上传文档到知识库"
"查看知识库统计"
```

### 2. ERP企业管理相关

```
"查看本月财务情况"
"查看财务看板"
"查询客户信息"
"查看订单状态"
```

### 3. 股票交易相关

```
"查看股票列表"
"查询AAPL股票行情"
"分析股票走势"
```

### 4. 任务管理相关

```
"创建一个数据分析任务"
"查看任务列表"
"查看任务状态"
```

### 5. 资源监控相关

```
"查看系统资源状态"
"查看服务列表"
```

---

## 🔧 配置说明

### Docker网络配置

如果OpenWebUI在Docker中运行，使用 `host.docker.internal` 访问本地服务：

```
http://host.docker.internal:8011  # 代替 localhost:8011
http://host.docker.internal:8013  # 代替 localhost:8013
```

这已经在Functions代码中默认配置好了。

---

## 🎨 自定义Functions

### 修改API地址

在Functions代码中修改Valves部分：

```python
class Valves(BaseModel):
    RAG_API: str = Field(
        default="http://your-custom-url:8011",
        description="RAG API地址"
    )
```

### 添加新Function

```python
async def your_custom_function(
    self,
    parameter: str,
    __user__: dict = {}
) -> str:
    """
    你的自定义功能
    
    示例: "执行自定义操作"
    """
    # 你的代码
    return "结果"
```

---

## ✅ 验证清单

### Functions部署成功的标志

- [ ] Functions在管理页面显示
- [ ] Functions状态为"Enabled"
- [ ] 聊天框输入指令有响应
- [ ] 返回的数据正确

---

## 💡 使用技巧

### 1. 自然语言调用

**不需要记忆命令**，直接说：
```
"帮我查一下本月的财务数据"
"搜索一下关于AI的文档"
"看看今天的股票行情"
```

OpenWebUI会自动识别意图并调用相应Function。

---

### 2. 组合使用

可以在一次对话中使用多个系统：

```
"帮我分析一下：
1. 查看本月财务情况
2. 搜索历史数据对比
3. 给出改进建议"
```

OpenWebUI会依次调用：
- ERP API → 财务数据
- RAG API → 历史记录
- 自学习API → 优化建议

---

### 3. 上下文记忆

OpenWebUI会记住对话上下文，可以连续提问：

```
用户: "查看本月财务"
AI: [显示财务数据]

用户: "和上个月比怎么样？"
AI: [自动对比数据]
```

---

## 🎊 快速演示脚本

### 演示1: ERP查询

```
你: "查看本月的财务看板"
AI: → 调用ERP API
    → 返回收入、支出、利润等数据
    
你: "客户管理里有多少客户？"
AI: → 调用ERP客户API
    → 返回客户统计
```

### 演示2: 知识库

```
你: "上传一份文档到知识库"
AI: → 调用RAG上传API
    → 返回上传结果

你: "搜索刚才上传的文档"
AI: → 调用RAG搜索API
    → 返回搜索结果
```

### 演示3: 股票分析

```
你: "查看苹果股票的行情"
AI: → 调用股票API
    → 返回AAPL实时数据
    
你: "分析一下走势"
AI: → 调用策略分析API
    → 返回分析结果
```

---

## 🔍 故障排除

### Functions不工作？

**检查1**: 所有服务是否运行
```bash
python3 scripts/system_health_check.py
```

**检查2**: API地址是否正确
- Docker中使用 `host.docker.internal`
- 本地使用 `localhost`

**检查3**: Functions是否启用
- 在Functions管理页面确认状态

---

## 📚 相关文档

- `OpenWebUI完整集成指南.md` - 详细集成文档
- `API使用示例.md` - API调用示例
- `终极使用手册.md` - 完整使用手册

---

## 🎉 完成！

按照以上步骤，你就可以在OpenWebUI中使用所有AI Stack功能了！

**开始体验吧！** ✨

---

**更新时间**: 2025-11-04  
**部署难度**: ⭐ 简单  
**预计时间**: 5分钟

