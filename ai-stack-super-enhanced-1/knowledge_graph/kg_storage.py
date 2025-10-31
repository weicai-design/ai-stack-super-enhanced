/enhanced_rag_kg
│
├── /api                  # FastAPI API 相关代码
│   ├── app.py            # 主应用程序
│   ├── routes.py         # 路由定义
│   ├── models.py         # Pydantic 模型
│   └── dependencies.py    # 依赖项和中间件
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
│   ├── kg_model.py       # 知识图谱模型
│   └── embedding_model.py # 嵌入模型
│
├── /tests                # 测试代码
│   ├── test_api.py       # API 测试
│   ├── test_pipeline.py   # 管道测试
│   └── test_preprocessor.py # 预处理测试
│
├── /data                 # 数据存储
│   ├── index.json        # 索引文件
│   └── kg_snapshot.json   # 知识图谱快照
│
├── requirements.txt       # 依赖项
└── README.md              # 项目说明