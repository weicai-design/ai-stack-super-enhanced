# OpenWebUI RAG集成 - 前端组件

根据需求1.7：将RAG前端功能迁移到OpenWebUI界面

## 📦 组件列表

### 1. RAGSearchPanel.vue
**位置**: 聊天侧边栏  
**功能**: 
- 实时搜索RAG知识库
- 展示搜索结果
- 插入知识到聊天
- 结果高亮显示

### 2. RAGFileManager.vue
**位置**: 设置页面  
**功能**:
- 文件上传到RAG库
- 文件列表管理
- 文件删除
- 上传进度显示

### 3. RAGKnowledgeGraph.vue (待开发)
**位置**: 聊天侧边栏  
**功能**:
- 知识图谱可视化
- 节点交互
- 实体查询

### 4. RAGStatusIndicator.vue (待开发)
**位置**: 状态栏  
**功能**:
- 索引状态显示
- 文档数量统计
- 系统健康检查

---

## 🔧 集成方式

### OpenWebUI插件集成

1. **将组件文件放入OpenWebUI插件目录**
   ```
   openwebui-plugins/
   └── rag-integration/
       └── frontend/
           ├── RAGSearchPanel.vue
           ├── RAGFileManager.vue
           └── ...
   ```

2. **在插件配置中注册组件**
   ```python
   # openwebui_plugin.py
   PLUGIN_CONFIG = {
       "frontend_components": {
           "RAGSearchPanel": {
               "component": "frontend/RAGSearchPanel.vue",
               "location": "chat-sidebar",
               "priority": 100
           },
           "RAGFileManager": {
               "component": "frontend/RAGFileManager.vue",
               "location": "settings-page",
               "priority": 50
           }
       }
   }
   ```

3. **配置API连接**
   组件需要知道RAG API的地址和API Key（如果有）
   - 默认API URL: `http://127.0.0.1:8011`
   - 可通过OpenWebUI设置配置

---

## 📝 使用说明

### RAGSearchPanel组件

**Props**:
- `apiUrl`: RAG API地址（默认: `http://127.0.0.1:8011`）
- `apiKey`: API密钥（可选）
- `maxResults`: 最大结果数（默认: 10）
- `similarityThreshold`: 相似度阈值（默认: 0.5）

**Events**:
- `result-selected`: 选择结果时触发
- `insert-to-chat`: 插入到聊天时触发

**示例**:
```vue
<RAGSearchPanel
  :api-url="ragApiUrl"
  :api-key="ragApiKey"
  :max-results="10"
  @result-selected="handleResultSelected"
  @insert-to-chat="handleInsertToChat"
/>
```

### RAGFileManager组件

**Props**:
- `apiUrl`: RAG API地址
- `apiKey`: API密钥（可选）

**功能**:
- 支持拖拽上传
- 支持批量上传
- 显示上传进度
- 文件列表管理

---

## 🎨 样式定制

组件使用CSS变量，可以通过OpenWebUI的主题系统定制：

```css
:root {
  --primary-color: #3b82f6;
  --bg-secondary: #f5f5f5;
  --border-color: #ddd;
  --text-primary: #333;
  --text-secondary: #666;
}
```

---

## 🚀 后续开发

1. **RAGKnowledgeGraph组件** - 知识图谱可视化
2. **RAGStatusIndicator组件** - 状态指示器
3. **移动端适配** - 响应式设计
4. **国际化** - 多语言支持
5. **高级搜索** - 筛选、排序等功能

---

**状态**: ✅ RAGSearchPanel和RAGFileManager已完成，待集成到OpenWebUI

