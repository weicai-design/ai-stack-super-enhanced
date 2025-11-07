/enhanced_rag_kg
│
├── /api                  # FastAPI 相关代码
│   ├── app.py            # 主应用程序
│   ├── routes.py         # 路由定义
│   ├── models.py         # Pydantic 模型
│   ├── dependencies.py    # 依赖项和中间件
│   └── metrics.py        # 指标相关代码
│
├── /pipelines            # 数据处理和管道
│   ├── ingestion.py      # 数据摄取管道
│   ├── search.py         # 搜索管道
│   └── embedding.py      # 嵌入处理
│
├── /preprocessors        # 数据预处理
│   ├── text_preprocessor.py  # 文本预处理
│   └── kg_preprocessor.py     # 知识图谱预处理
│
├── /models               # 机器学习模型
│   ├── semantic_model.py  # 语义模型
│   └── vector_store.py    # 向量存储
│
├── /tests                # 测试代码
│   ├── test_api.py       # API 测试
│   ├── test_pipelines.py  # 管道测试
│   └── test_models.py     # 模型测试
│
├── requirements.txt      # 依赖包
└── README.md             # 项目说明