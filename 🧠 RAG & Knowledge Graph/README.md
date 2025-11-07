# 🧠 RAG & Knowledge Graph - 智能知识管理系统

**版本**: v1.0.0  
**开始日期**: 2025-11-06  
**优先级**: P0（核心基础设施）

---

## 📋 系统概述

RAG（Retrieval-Augmented Generation）和知识图谱是AI-Stack的**核心知识基座**，为所有其他功能模块提供智能知识支持。

### 核心功能

1. **全格式文件处理** ✅
   - 办公文件：Word、Excel、PPT、PDF
   - 电子书：EPUB、MOBI、TXT
   - 编程文件：Python、Java、C++、JavaScript等
   - 图片：JPG、PNG、GIF、WebP
   - 音视频：MP3、MP4、WAV、AVI
   - 思维导图：XMind、FreeMind
   - 数据库文件：SQL、CSV、JSON
   - 其他：Markdown、HTML、XML

2. **四项预处理** ✅
   - 数据清洗
   - 标准化处理
   - 去重验证
   - 真实性验证

3. **多源信息收集** ✅
   - 网络搜索信息
   - 人机交互信息
   - 业务系统数据
   - 智能体产生的信息

4. **智能检索利用** ✅
   - 语义检索
   - 向量检索
   - 混合检索
   - 上下文感知

5. **自主分组** ✅
   - 词义分析
   - 自动分类
   - 标签生成
   - 关系识别

6. **知识图谱** ✅
   - 实体识别
   - 关系抽取
   - 图谱构建
   - 图谱查询

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────┐
│              RAG Web界面                         │
│         (http://localhost:8014)                 │
├─────────────────────────────────────────────────┤
│              RAG API层                           │
│    上传 | 查询 | 分析 | 可视化                    │
├─────────────────────────────────────────────────┤
│           核心处理层                             │
│  ┌──────────┬──────────┬──────────┐            │
│  │文件处理器│预处理引擎│知识抽取器│            │
│  └──────────┴──────────┴──────────┘            │
├─────────────────────────────────────────────────┤
│           存储层                                 │
│  ┌──────────┬──────────┬──────────┐            │
│  │向量数据库│关系数据库│文件存储  │            │
│  │ Chroma   │ SQLite   │ MinIO    │            │
│  └──────────┴──────────┴──────────┘            │
└─────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
🧠 RAG & Knowledge Graph/
├── README.md                    # 本文档
├── requirements.txt             # Python依赖
├── config.yaml                  # 配置文件
│
├── core/                        # 核心模块
│   ├── __init__.py
│   ├── rag_engine.py           # RAG引擎
│   ├── vector_store.py         # 向量存储
│   ├── knowledge_graph.py      # 知识图谱
│   └── retriever.py            # 检索器
│
├── processors/                  # 处理器
│   ├── __init__.py
│   ├── file_processor.py       # 文件处理
│   ├── text_processor.py       # 文本处理
│   ├── image_processor.py      # 图片处理
│   ├── audio_processor.py      # 音频处理
│   ├── video_processor.py      # 视频处理
│   └── preprocessor.py         # 预处理器
│
├── storage/                     # 存储层
│   ├── __init__.py
│   ├── chroma_store.py         # Chroma向量库
│   ├── sqlite_store.py         # SQLite数据库
│   └── file_store.py           # 文件存储
│
├── api/                         # API接口
│   ├── __init__.py
│   ├── main.py                 # FastAPI主程序
│   ├── routes/
│   │   ├── upload.py          # 上传接口
│   │   ├── query.py           # 查询接口
│   │   ├── knowledge.py       # 知识管理
│   │   └── graph.py           # 图谱接口
│
├── web/                         # Web界面
│   ├── index.html              # 主页
│   ├── upload.html             # 上传页面
│   ├── query.html              # 查询页面
│   ├── knowledge.html          # 知识库管理
│   ├── graph.html              # 知识图谱
│   └── static/
│       ├── css/
│       └── js/
│
├── utils/                       # 工具函数
│   ├── __init__.py
│   ├── text_utils.py
│   ├── file_utils.py
│   └── embedding_utils.py
│
├── tests/                       # 测试
│   ├── test_processor.py
│   ├── test_retriever.py
│   └── test_api.py
│
└── scripts/                     # 脚本
    ├── start_rag.sh            # 启动脚本
    ├── init_db.py              # 初始化数据库
    └── import_data.py          # 导入数据
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd "🧠 RAG & Knowledge Graph"
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python scripts/init_db.py
```

### 3. 启动服务

```bash
./scripts/start_rag.sh
```

### 4. 访问界面

- Web界面: http://localhost:8014
- API文档: http://localhost:8014/docs
- 知识图谱: http://localhost:8014/graph

---

## 📖 核心功能说明

### 1. 文件上传与处理

**支持的文件格式**:
- 文档：PDF, DOCX, XLSX, PPTX, TXT, MD
- 代码：PY, JS, JAVA, CPP, GO, RS
- 图片：JPG, PNG, GIF, WEBP
- 音频：MP3, WAV, M4A
- 视频：MP4, AVI, MKV
- 其他：JSON, XML, CSV, SQL

**处理流程**:
```
上传文件 → 格式识别 → 内容提取 → 分块处理 
  ↓
预处理（清洗、标准化、去重、验证）
  ↓
向量化 → 存储到向量库 → 建立索引
```

### 2. 知识检索

**检索方式**:
- **语义检索**: 基于语义相似度
- **向量检索**: 基于向量距离
- **混合检索**: 结合BM25和向量检索
- **图谱检索**: 基于知识图谱关系

**检索API**:
```python
# 简单检索
POST /api/query
{
  "query": "如何提高企业利润？",
  "top_k": 5
}

# 高级检索
POST /api/query/advanced
{
  "query": "客户管理最佳实践",
  "filters": {"source": "ERP"},
  "include_metadata": true,
  "rerank": true
}
```

### 3. 知识图谱

**图谱构建**:
- 实体识别（NER）
- 关系抽取（RE）
- 属性提取
- 图谱存储

**图谱查询**:
```python
# 查询实体
GET /api/graph/entity/{name}

# 查询关系
GET /api/graph/relation?from=A&to=B

# 路径查询
POST /api/graph/path
{
  "start": "客户A",
  "end": "订单123",
  "max_depth": 3
}
```

### 4. 智能问答

**RAG增强的问答**:
```python
POST /api/chat
{
  "question": "如何优化库存管理？",
  "context_sources": ["ERP", "文档库", "知识库"],
  "use_knowledge_graph": true
}
```

**响应**:
```json
{
  "answer": "基于您的ERP数据和最佳实践...",
  "sources": [
    {
      "content": "库存优化建议...",
      "source": "ERP-仓储管理",
      "relevance": 0.95
    }
  ],
  "knowledge_graph_path": ["库存管理", "ABC分析", "安全库存"]
}
```

---

## 🔧 配置说明

### config.yaml

```yaml
# RAG配置
rag:
  embedding_model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  chunk_size: 512
  chunk_overlap: 50
  top_k: 5
  
# 向量数据库
vector_store:
  type: "chroma"
  persist_directory: "./data/chroma"
  collection_name: "ai_stack_knowledge"
  
# 知识图谱
knowledge_graph:
  neo4j_uri: "bolt://localhost:7687"
  neo4j_user: "neo4j"
  neo4j_password: "password"
  
# 预处理
preprocessing:
  enable_deduplication: true
  enable_validation: true
  enable_cleaning: true
  enable_normalization: true
  
# API
api:
  host: "0.0.0.0"
  port: 8014
  cors_origins: ["*"]
```

---

## 🔌 与其他模块集成

### 1. 与ERP集成

```python
# ERP数据自动进入RAG
from rag_engine import RAGEngine

rag = RAGEngine()

# 订单数据
order_data = erp.get_order("ORD001")
rag.add_document(
    content=order_data,
    metadata={
        "source": "ERP",
        "module": "订单管理",
        "type": "业务数据"
    }
)

# ERP查询RAG获取建议
suggestions = rag.query(
    "如何提高该订单的利润率？",
    filters={"module": "订单管理"}
)
```

### 2. 与交互中心集成

```python
# 聊天时自动检索RAG
def chat_with_rag(user_message):
    # 检索相关知识
    context = rag.retrieve(user_message)
    
    # 生成回答
    response = llm.generate(
        prompt=user_message,
        context=context
    )
    
    return response
```

### 3. 与其他功能集成

- **股票功能**: 存储股票分析结果，检索历史策略
- **内容创作**: 存储创作素材，检索热点话题
- **趋势分析**: 存储爬取信息，检索行业报告

---

## 📊 性能指标

### 目标性能

| 指标 | 目标值 |
|------|--------|
| 文件上传速度 | >10MB/s |
| 检索响应时间 | <500ms |
| 向量化速度 | >1000条/秒 |
| 并发查询 | >100 QPS |
| 准确率 | >90% |

### 容量规划

- 向量数据库: 支持100万+文档
- 知识图谱: 支持10万+实体
- 文件存储: 支持1TB+数据

---

## 🔐 安全与隐私

1. **数据加密**: 静态数据加密存储
2. **访问控制**: 基于角色的权限管理
3. **审计日志**: 完整的操作日志
4. **数据隔离**: 多租户数据隔离
5. **去伪验证**: 信息真实性验证

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/integration/

# 性能测试
python tests/performance_test.py
```

---

## 📈 开发路线图

### 阶段1: 基础功能（第1周）✅
- [x] 项目架构搭建
- [ ] 文件处理器实现
- [ ] 向量数据库集成
- [ ] 基础API开发

### 阶段2: 核心功能（第2周）
- [ ] 四项预处理实现
- [ ] 知识检索优化
- [ ] Web界面开发
- [ ] 与ERP集成

### 阶段3: 高级功能（第3周）
- [ ] 知识图谱构建
- [ ] 智能问答
- [ ] 多源信息收集
- [ ] 自主分组

### 阶段4: 优化完善（第4周）
- [ ] 性能优化
- [ ] 安全加固
- [ ] 文档完善
- [ ] 全面测试

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

---

## 📞 技术支持

- 文档: 本README
- API文档: http://localhost:8014/docs
- Issue: GitHub Issues

---

**开发团队**: AI-Stack  
**版本**: v1.0.0  
**最后更新**: 2025-11-06












