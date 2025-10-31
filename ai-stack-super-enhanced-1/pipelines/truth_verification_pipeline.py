/ai-stack-super-enhanced
│
├── /data                  # 数据存储
│   ├── index.json
│   └── kg_snapshot.json
│
├── /pipelines             # 管道实现
│   ├── hybrid_search.py
│   └── smart_ingestion_pipeline.py
│
├── /preprocessors         # 数据预处理
│   └── kg_simple.py
│
├── /core                  # 核心功能
│   ├── semantic_grouping.py
│   └── utils.py           # 工具函数
│
├── /api                   # API 实现
│   └── app.py
│
├── /models                # 模型存储
│   └── embedding_model    # 嵌入模型
│
└── requirements.txt       # 依赖文件