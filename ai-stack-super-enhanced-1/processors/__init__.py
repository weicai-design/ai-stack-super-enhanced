/ai-stack-super-enhanced
│
├── /data                   # 存储数据和索引
│   ├── index.json
│   └── kg_snapshot.json
│
├── /models                 # 存储模型
│   └── sentence_transformer
│
├── /pipelines              # 管道实现
│   ├── hybrid_search.py
│   └── smart_ingestion_pipeline.py
│
├── /preprocessors          # 数据预处理
│   └── kg_simple.py
│
├── /core                   # 核心功能
│   ├── semantic_grouping.py
│   └── utils.py
│
├── /api                    # API 实现
│   ├── app.py              # FastAPI 应用
│   └── routes.py           # 路由定义
│
├── /tests                  # 测试用例
│   └── test_app.py
│
├── requirements.txt        # 依赖文件
└── README.md               # 项目说明