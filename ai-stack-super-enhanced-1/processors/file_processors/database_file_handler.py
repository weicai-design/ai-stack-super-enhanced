/ai-stack-super-enhanced
│
├── /data                  # 存储数据和索引
│   ├── index.json
│   └── kg_snapshot.json
│
├── /models                # 存储模型文件
│   └── ...
│
├── /pipelines             # 存储数据处理和检索管道
│   ├── hybrid_search.py
│   └── smart_ingestion_pipeline.py
│
├── /preprocessors         # 存储数据预处理模块
│   └── kg_simple.py
│
├── /core                  # 核心功能模块
│   ├── semantic_grouping.py
│   └── ...
│
├── /api                   # API 相关代码
│   ├── app.py             # FastAPI 应用
│   └── routes.py          # 路由定义
│
├── /tests                 # 测试代码
│   └── ...
│
├── requirements.txt       # 依赖包
└── README.md              # 项目说明文档