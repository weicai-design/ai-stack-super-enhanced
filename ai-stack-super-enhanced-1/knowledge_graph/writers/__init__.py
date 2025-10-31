/ai-stack-super-enhanced
│
├── /data                  # 数据存储目录
│   ├── index.json        # 索引文件
│   └── kg_snapshot.json   # 知识图谱快照
│
├── /pipelines             # 管道实现
│   ├── hybrid_search.py   # 混合搜索实现
│   └── smart_ingestion_pipeline.py  # 智能采集管道
│
├── /preprocessors         # 数据预处理
│   └── kg_simple.py       # 简单知识图谱写入器
│
├── /core                  # 核心功能
│   ├── semantic_grouping.py # 语义分组
│   └── utils.py           # 工具函数
│
├── /api                   # API 实现
│   └── app.py             # FastAPI 应用
│
├── /models                # 机器学习模型
│   └── embedding_model.py  # 嵌入模型
│
├── requirements.txt       # 依赖包
└── README.md              # 项目说明