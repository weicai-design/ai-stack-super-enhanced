# Super Agent 前端路由规范

该文件记录 P0-020 之后的关键三级页面抽离及路由映射，所有入口统一由 `web/js/routes.js` 维护，左侧导航根据 `data-module` 与该表匹配。

| Module ID | 页面说明 | 访问方式 |
|-----------|----------|----------|
| `chat` | 智能聊天（主页面内嵌） | 内置 |
| `rag` | RAG 知识库管理控制台 | `http://localhost:8011/rag-management` |
| `rag-preprocess` | RAG 预处理中心（清洗/标准化/去重/验证） | `rag_preprocess.html` |
| `rag-tools` | RAG 工具集 | `rag_tools.html` |
| `rag-ingest` | 老版流水线面板（保留） | `rag_ingest.html` |
| `knowledge` | 知识沉淀中心（模板 + 入库队列） | `knowledge_center.html` |
| `erp` | ERP 管理工作台（外部服务） | `http://localhost:8012` |
| `erp-key` | ERP 流程中心（11环节+时间线） | `erp_core.html` |
| `erp-orders` | 订单看板 | `erp_orders.html` |
| `erp-production` | 生产工单看板 | `erp_production.html` |
| `erp-procurements` | 采购预警 | `erp_procurements.html` |
| `erp-inventory` | 库存可视化 | `erp_inventory.html` |
| `bpm-hub` | BPM 控制台（设计器+追踪） | `erp_bpmn.html` |
| `bpmn-runtime` | BPM 流程运行中心 | `bpmn_runtime.html` |
| `bpmn-designer` | BPM 流程设计器 | `bpmn_designer.html` |
| `content` | 内容创作平台（抖音 API 控制台） | `content_douyin.html` |
| `trend` | 趋势分析指标库与模板 | `trend_insights.html` |
| `stock` | 股票模拟盘与风控 | `stock_simulator.html` |
| `operations` | 运营财务指标看板 | `operations_finance.html` |
| `stock-backtest` | 策略回测面板 | `stock_backtest.html` |

### ERP 11 环节独立三级页

全部复用 `erp_stage.html`，通过 `stage` 查询参数区分，例如：

```
erp_stage.html?stage=market_research
erp_stage.html?stage=customer_development
erp_stage.html?stage=project_development
erp_stage.html?stage=production_planning
erp_stage.html?stage=order_management
erp_stage.html?stage=procurement
erp_stage.html?stage=material_receipt
erp_stage.html?stage=production
erp_stage.html?stage=quality_check
erp_stage.html?stage=warehousing
erp_stage.html?stage=delivery
```

> 若新增模块，请同步更新 `routes.js` 和此文档，确保左侧导航、快捷入口与统一路由保持一致。制作三级页时，建议将页面放在 `web/` 根目录或 `web/<module>/` 子目录，静态资源继续复用现有 CSS/JS。 *** End Patch*** End Patch

