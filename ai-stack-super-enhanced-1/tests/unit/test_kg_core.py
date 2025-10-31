/ai-stack-super-enhanced
│
├── /data                   # 数据存储目录
│   ├── index.json         # 索引文件
│   └── kg_snapshot.json    # 知识图谱快照
│
├── /models                 # 模型存储目录
│   └── all-MiniLM-L6-v2    # 预训练模型
│
├── /pipelines              # 数据处理管道
│   ├── hybrid_search.py    # 混合搜索实现
│   └── smart_ingestion_pipeline.py  # 智能数据采集管道
│
├── /preprocessors          # 数据预处理模块
│   └── kg_simple.py        # 简单知识图谱写入器
│
├── /core                   # 核心功能模块
│   ├── semantic_grouping.py # 语义分组实现
│   └── utils.py            # 工具函数
│
├── /api                    # API 接口
│   └── app.py              # FastAPI 应用
│
├── /tests                  # 测试用例
│   └── test_app.py         # API 测试
│
├── requirements.txt        # 项目依赖
└── README.md               # 项目说明文档