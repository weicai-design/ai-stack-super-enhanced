/ai-stack-super-enhanced/
│
├── /data/                     # 数据存储
│   ├── index.json            # 索引文件
│   └── kg_snapshot.json       # 知识图谱快照
│
├── /pipelines/                # 管道实现
│   ├── hybrid_search.py       # 混合搜索实现
│   └── smart_ingestion_pipeline.py  # 智能采集管道
│
├── /preprocessors/            # 预处理器
│   └── kg_simple.py           # 简单知识图谱写入器
│
├── /core/                     # 核心功能
│   ├── semantic_grouping.py    # 语义分组
│   └── utils.py               # 工具函数
│
├── /api/                      # API 实现
│   └── app.py                 # FastAPI 应用
│
├── /tests/                    # 测试
│   └── test_app.py            # API 测试
│
├── requirements.txt           # 依赖文件
└── README.md                  # 项目说明