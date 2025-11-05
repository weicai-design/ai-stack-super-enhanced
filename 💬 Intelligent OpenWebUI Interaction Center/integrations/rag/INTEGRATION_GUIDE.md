# OpenWebUI集成指南

本指南说明如何将RAG集成模块集成到OpenWebUI中。

## 📋 前置要求

1. **RAG服务运行中**
   ```bash
   # 启动RAG服务
   make dev
   # 或
   bash scripts/dev.sh
   ```

2. **OpenWebUI已安装**
   - 参考 [OpenWebUI安装文档](https://github.com/open-webui/open-webui)

3. **Python依赖**
   ```bash
   pip install httpx
   ```

## 🔧 集成步骤

### 方法1: 作为OpenWebUI插件集成（推荐）

#### 步骤1: 复制插件文件

```bash
# 将集成模块复制到OpenWebUI插件目录
cp -r "💬 Intelligent OpenWebUI Interaction Center/integrations/rag" \
      /path/to/open-webui/.plugins/
```

#### 步骤2: 配置OpenWebUI

在OpenWebUI配置文件中添加：

```yaml
# .env 或配置文件
RAG_API_URL=http://127.0.0.1:8011
RAG_API_KEY=your_secret_key  # 可选
```

#### 步骤3: 启用插件

在OpenWebUI管理界面中启用RAG集成插件。

---

### 方法2: 自定义集成（高级）

#### 在OpenWebUI中添加钩子

```python
# 在OpenWebUI的custom_auth.py或类似文件中

from integrations.rag import (
    get_chat_handler,
    get_file_handler,
    get_knowledge_enhancer,
)

# 用户消息钩子
async def on_user_message(message, user_id=None, session_id=None, **kwargs):
    handler = get_chat_handler()
    result = await handler.process_user_message(
        message=message,
        user_id=user_id,
        session_id=session_id,
    )
    return result

# 文件上传钩子
async def on_file_upload(file_path, filename=None, user_id=None, **kwargs):
    handler = get_file_handler()
    result = await handler.process_uploaded_file(
        file_path=file_path,
        filename=filename,
        user_id=user_id,
    )
    return result

# 回答增强钩子
async def enhance_response(user_query, original_response, **kwargs):
    enhancer = get_knowledge_enhancer()
    result = await enhancer.enhance_response(
        user_query=user_query,
        original_response=original_response,
    )
    return result.get("enhanced_response", original_response)
```

---

## 📝 使用示例

### 示例1: 在OpenWebUI中自动保存聊天内容

```python
# 在OpenWebUI的聊天处理逻辑中

from integrations.rag import ChatMessageHandler

async def handle_chat_message(message, user_id, session_id):
    handler = ChatMessageHandler(auto_save=True)
    
    # 自动保存用户消息
    result = await handler.process_user_message(
        message=message,
        user_id=user_id,
        session_id=session_id,
    )
    
    if result.get("saved"):
        print(f"消息已保存到RAG库: {result['doc_id']}")
```

### 示例2: 增强AI回答

```python
from integrations.rag import KnowledgeEnhancer

async def generate_response(user_query):
    # 1. 生成原始回答（使用LLM）
    original_response = await llm.generate(user_query)
    
    # 2. 使用RAG知识增强回答
    enhancer = KnowledgeEnhancer()
    enhanced = await enhancer.enhance_response(
        user_query=user_query,
        original_response=original_response,
    )
    
    # 3. 返回增强后的回答
    return enhanced.get("enhanced_response", original_response)
```

### 示例3: 处理文件上传

```python
from integrations.rag import FileUploadHandler

async def handle_file_upload(file_path, filename, user_id):
    handler = FileUploadHandler(auto_process=True)
    
    result = await handler.process_uploaded_file(
        file_path=file_path,
        filename=filename,
        user_id=user_id,
    )
    
    if result.get("processed"):
        return f"文件已处理并添加到知识库: {result['doc_id']}"
    else:
        return f"处理失败: {result.get('error')}"
```

---

## ⚙️ 配置选项

### 环境变量

```bash
# RAG API地址（必需）
export RAG_API_URL=http://127.0.0.1:8011

# RAG API密钥（可选，如果RAG服务启用了API Key）
export RAG_API_KEY=your_secret_key

# 自动保存聊天内容（默认：true）
export RAG_AUTO_SAVE_CHAT=true

# 最小消息长度（默认：10）
export RAG_MIN_MESSAGE_LENGTH=10

# 启用知识增强（默认：true）
export RAG_ENABLE_ENHANCEMENT=true

# 检索知识数量（默认：3）
export RAG_TOP_K=3

# 相似度阈值（默认：0.5）
export RAG_SIMILARITY_THRESHOLD=0.5
```

### 代码配置

```python
from integrations.rag import (
    ChatMessageHandler,
    KnowledgeEnhancer,
    FileUploadHandler,
)

# 自定义配置
chat_handler = ChatMessageHandler(
    auto_save=True,      # 自动保存
    min_length=20,       # 最小消息长度
)

knowledge_enhancer = KnowledgeEnhancer(
    enable_enhancement=True,
    top_k=5,             # 检索5个知识片段
    similarity_threshold=0.6,  # 更高相似度阈值
)

file_handler = FileUploadHandler(
    auto_process=True,
    temp_dir="/custom/temp/dir",
)
```

---

## 🧪 测试集成

### 运行示例代码

```bash
cd "💬 Intelligent OpenWebUI Interaction Center/integrations/rag"
python example_usage.py
```

### 手动测试

1. **测试聊天保存**
   ```bash
   # 在OpenWebUI中发送一条消息
   # 检查是否保存到RAG库
   curl http://127.0.0.1:8011/index/info
   ```

2. **测试文件上传**
   ```bash
   # 在OpenWebUI中上传一个文件
   # 检查是否处理
   curl http://127.0.0.1:8011/index/info
   ```

3. **测试知识增强**
   ```bash
   # 在OpenWebUI中提问
   # 检查回答是否包含RAG知识
   ```

---

## 🐛 故障排除

### 问题1: RAG服务连接失败

**症状**: 无法连接到RAG API

**解决**:
```bash
# 1. 检查RAG服务是否运行
curl http://127.0.0.1:8011/readyz

# 2. 检查环境变量
echo $RAG_API_URL

# 3. 检查网络连接
```

### 问题2: 聊天内容未保存

**症状**: 消息发送后未保存到RAG库

**解决**:
```python
# 检查auto_save配置
handler = ChatMessageHandler(auto_save=True)  # 确保为True

# 检查消息长度
# 确保消息长度 >= min_length (默认10)
```

### 问题3: 知识增强无效果

**症状**: 回答未包含RAG知识

**解决**:
```python
# 1. 检查RAG库是否有内容
# 2. 降低相似度阈值
enhancer = KnowledgeEnhancer(similarity_threshold=0.3)

# 3. 增加检索数量
enhancer = KnowledgeEnhancer(top_k=5)
```

---

## 📚 下一步

1. **完善集成**: 根据实际需求调整配置
2. **扩展功能**: 添加更多自定义功能
3. **性能优化**: 优化检索和增强速度
4. **监控日志**: 设置日志监控和告警

---

## 🤝 获取帮助

- 查看 [README.md](README.md) 获取API参考
- 查看 [example_usage.py](example_usage.py) 获取更多示例
- 提交Issue获取支持

---

**版本**: 1.0.0  
**更新时间**: 2025-11-02

