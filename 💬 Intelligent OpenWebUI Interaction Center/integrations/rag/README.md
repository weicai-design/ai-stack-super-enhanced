# OpenWebUI RAG 集成模块

OpenWebUI与RAG系统的深度集成，实现聊天内容自动保存、知识检索增强、文件自动处理等功能。

## 🎯 功能特性

### 1. 聊天内容自动保存 ⭐⭐⭐⭐⭐
- 自动保存用户消息到RAG库
- 可选保存助手回答
- 支持会话关联
- 自动生成文档ID

### 2. 知识检索增强回答 ⭐⭐⭐⭐⭐
- 从RAG库检索相关知识
- 自动增强AI回答
- 提供相关上下文
- 相似度过滤

### 3. 文件上传自动处理 ⭐⭐⭐⭐
- 自动处理上传的文件
- 支持多种文件格式
- 批量处理支持
- 自动摄入RAG库

### 4. 知识图谱查询 ⭐⭐⭐
- 查询知识图谱实体
- 获取相关实体信息
- 支持email、url等类型

## 📦 模块结构

```
integrations/rag/
├── __init__.py                 # 模块导出
├── rag_integration.py          # RAG集成服务（核心）
├── chat_handler.py             # 聊天消息处理器
├── file_upload_handler.py      # 文件上传处理器
├── knowledge_enhancer.py       # 知识增强器
├── openwebui_plugin.py         # OpenWebUI插件入口
└── README.md                   # 本文档
```

## 🚀 快速开始

### 安装依赖

```bash
pip install httpx
```

### 基本使用

```python
from integrations.rag import (
    RAGIntegrationService,
    ChatMessageHandler,
    FileUploadHandler,
    KnowledgeEnhancer,
)

# 初始化服务
rag_service = RAGIntegrationService(
    rag_api_url="http://127.0.0.1:8011",
    api_key=None,  # 如果设置了RAG_API_KEY
)

# 处理聊天消息
chat_handler = ChatMessageHandler(auto_save=True)
await chat_handler.process_user_message(
    message="用户的问题",
    user_id="user123",
    session_id="session456",
)

# 增强回答
enhancer = KnowledgeEnhancer(enable_enhancement=True)
result = await enhancer.enhance_response(
    user_query="用户的问题",
    original_response="原始AI回答",
)
```

### OpenWebUI集成

1. 将插件放入OpenWebUI插件目录
2. 在OpenWebUI配置中启用插件
3. 设置环境变量：
   ```bash
   export RAG_API_URL=http://127.0.0.1:8011
   export RAG_API_KEY=your_key  # 可选
   ```

## 📋 API参考

### RAGIntegrationService

核心RAG集成服务，提供与RAG API的所有交互。

#### 方法

- `health_check()` - 检查RAG服务健康状态
- `ingest_text(text, doc_id, metadata, save_index)` - 摄入文本
- `ingest_file(file_path, doc_id, save_index)` - 摄入文件
- `search(query, top_k)` - 搜索文档
- `get_kg_snapshot()` - 获取知识图谱快照
- `query_kg(entity_type, entity_value)` - 查询知识图谱
- `get_index_info()` - 获取索引信息

### ChatMessageHandler

处理OpenWebUI聊天消息。

#### 方法

- `process_user_message(message, user_id, session_id, metadata)` - 处理用户消息
- `process_assistant_message(message, user_message, user_id, session_id, metadata)` - 处理助手消息
- `search_relevant_context(query, top_k)` - 搜索相关上下文

### FileUploadHandler

处理文件上传。

#### 方法

- `process_uploaded_file(file_path, filename, user_id, session_id, metadata)` - 处理单个文件
- `process_uploaded_files(file_paths, user_id, session_id)` - 批量处理文件
- `is_supported_file(filename)` - 检查文件是否支持

### KnowledgeEnhancer

使用RAG知识增强AI回答。

#### 方法

- `enhance_response(user_query, original_response, use_context)` - 增强回答
- `get_related_entities(query)` - 获取相关实体

## 🔧 配置

### 环境变量

- `RAG_API_URL`: RAG API地址（默认: http://127.0.0.1:8011）
- `RAG_API_KEY`: RAG API密钥（可选）

### 初始化参数

```python
# ChatMessageHandler
handler = ChatMessageHandler(
    auto_save=True,      # 自动保存
    min_length=10,       # 最小消息长度
)

# KnowledgeEnhancer
enhancer = KnowledgeEnhancer(
    enable_enhancement=True,     # 启用增强
    top_k=3,                     # 检索数量
    similarity_threshold=0.5,    # 相似度阈值
)

# FileUploadHandler
handler = FileUploadHandler(
    auto_process=True,   # 自动处理
    temp_dir=None,       # 临时目录
)
```

## 📝 使用示例

### 示例1: 自动保存聊天内容

```python
from integrations.rag import ChatMessageHandler

handler = ChatMessageHandler()

# 用户发送消息时
result = await handler.process_user_message(
    message="这是一个重要的问题",
    user_id="user123",
    session_id="session456",
)

if result.get("saved"):
    print(f"已保存，文档ID: {result['doc_id']}")
```

### 示例2: 知识增强回答

```python
from integrations.rag import KnowledgeEnhancer

enhancer = KnowledgeEnhancer()

# 增强AI回答
result = await enhancer.enhance_response(
    user_query="什么是RAG？",
    original_response="RAG是检索增强生成...",
)

if result.get("has_knowledge"):
    print("找到了相关知识！")
    print(f"增强后的回答: {result['enhanced_response']}")
```

### 示例3: 处理文件上传

```python
from integrations.rag import FileUploadHandler

handler = FileUploadHandler()

# 处理上传的文件
result = await handler.process_uploaded_file(
    file_path="/path/to/file.pdf",
    filename="document.pdf",
    user_id="user123",
)

if result.get("processed"):
    print(f"文件已处理，文档ID: {result['doc_id']}")
```

## 🐛 故障排除

### RAG服务连接失败

1. 检查RAG服务是否运行：`curl http://127.0.0.1:8011/readyz`
2. 检查环境变量`RAG_API_URL`是否正确
3. 检查网络连接

### 文件上传失败

1. 检查文件是否存在
2. 检查文件格式是否支持
3. 查看日志获取详细错误信息

### 知识增强无效果

1. 检查RAG库中是否有相关文档
2. 调整`similarity_threshold`参数
3. 增加`top_k`值以检索更多结果

## 📚 相关文档

- [RAG API文档](../api/README.md)
- [OpenWebUI插件开发文档](https://github.com/open-webui/open-webui)
- [项目主文档](../../../README.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

与主项目保持一致。

---

**版本**: 1.0.0  
**更新时间**: 2025-11-02

