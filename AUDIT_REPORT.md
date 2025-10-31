# 仓库审计报告（自动生成）
- 时间: 2025-10-27T20:26:52
- 根目录: /Users/ywc/ai-stack-super-enhanced

## 顶层模块覆盖
- 🚀 Core System & Entry Points: ✓
- ⚙️ Configuration Center: ✓
- 🔧 Core Engine: ✓
- 📚 Enhanced RAG & Knowledge Graph: ✓
- 💼 Intelligent ERP & Business Management: ✓
- 📈 Intelligent Stock Trading: ✓
- 🎨 Intelligent Content Creation: ✓
- 🔍 Intelligent Trend Analysis: ✓
- 🤖 Intelligent Task Agent: ✓
- 💬 Intelligent OpenWebUI Interaction Center: ✓
- 🛠️ Intelligent System Resource Management: ✓
- 🐳 Intelligent Docker Containerization: ✓
- 📖 Intelligent Documentation & Testing: ✓
- extensions: ✓
- plugins: ✓
- scripts: ✓
- models: ✓
- .vscode: ✓

## 关键路径检查
- 📚 Enhanced RAG & Knowledge Graph: ✓
  - 📚 Enhanced RAG & Knowledge Graph/api/app.py: ✓
  - 📚 Enhanced RAG & Knowledge Graph/core: ✓
  - 📚 Enhanced RAG & Knowledge Graph/pipelines: ✓
  - 📚 Enhanced RAG & Knowledge Graph/knowledge_graph: ✓
- .vscode: ✓
  - .vscode/settings.json: ✓
- models: ✓
  - models/all-MiniLM-L6-v2: ✓
  - models/all-MiniLM-L6-v2/modules.json: ✓
  - models/all-MiniLM-L6-v2/1_Pooling: ✓
  - models/all-MiniLM-L6-v2/0_Transformer: ✗
- scripts: ✓
  - scripts/dev.sh: ✗
  - scripts/smoke.sh: ✗
  - scripts/scaffold_minimal.py: ✓
  - scripts/audit_repo.py: ✓

## 服务探测
- 8011 端口: 离线
  - /readyz: {}
  - /index/info: {}
  - /kg/stats: {}

## 差距与优先级
- [ ] 缺少脚本: scripts/dev.sh
- [ ] 缺少脚本: scripts/smoke.sh
- [ ] uvicorn 未监听 8011 端口
