/enhanced_rag_kg
│
├── /api                  # FastAPI 相关代码
│   ├── app.py            # 主应用程序
│   ├── routes.py         # 路由定义
│   ├── models.py         # Pydantic 模型
│   ├── dependencies.py    # 依赖项和中间件
│   └── metrics.py        # 指标相关代码
│
├── /pipelines            # 数据处理和检索管道
│   ├── hybrid_search.py  # 混合检索逻辑
│   └── ingestion.py      # 数据摄取逻辑
│
├── /preprocessors        # 数据预处理模块
│   ├── kg_writer.py      # 知识图谱写入逻辑
│   └── text_processor.py  # 文本处理逻辑
│
├── /models               # 机器学习模型
│   ├── embedding.py      # 嵌入模型
│   └── transformer.py    # 变换器模型
│
├── /tests                # 测试代码
│   ├── test_api.py       # API 测试
│   └── test_pipeline.py   # 管道测试
│
├── requirements.txt      # 项目依赖
└── README.md             # 项目说明文档