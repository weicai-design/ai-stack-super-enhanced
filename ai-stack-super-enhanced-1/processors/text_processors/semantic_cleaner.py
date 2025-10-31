/ai-stack-super-enhanced
│
├── /data                  # 数据存储目录
│   ├── index.json        # 索引文件
│   └── kg_snapshot.json   # 知识图谱快照
│
├── /models                # 模型存储目录
│   └── ...                # 其他模型文件
│
├── /pipelines             # 管道实现
│   ├── hybrid_search.py   # 混合搜索实现
│   └── smart_ingestion_pipeline.py  # 智能采集管道
│
├── /preprocessors         # 数据预处理
│   └── kg_simple.py       # 简单知识图谱写入器
│
├── /core                  # 核心功能
│   ├── semantic_grouping.py # 语义分组实现
│   └── ...                # 其他核心功能
│
├── /api                   # API 实现
│   ├── app.py            # FastAPI 应用
│   └── ...                # 其他 API 相关文件
│
├── /tests                 # 测试用例
│   └── ...                # 测试文件
│
├── requirements.txt       # 依赖包
└── README.md              # 项目说明