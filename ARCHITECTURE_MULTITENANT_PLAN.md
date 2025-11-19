# AI-STACK 多租户 / 微服务演进计划

> 目标：在**保持单体仓库与运行时**的前提下，逐步建立**模块化边界 + 多租户上下文**，为未来拆分为微服务做准备。

---

## 1. 现状盘点

| 层级 | 现状 | 风险/缺口 |
| --- | --- | --- |
| API 层 | FastAPI 路由统一，由 `super_agent_api.py` 暴露；部分接口（如 RAG/Trend）已经接入 `require_tenant` | ERP/Content/资源治理等模块存在匿名调用；租户上下文与资源监控尚未完全贯通 |
| Service 层 | 单体模块（chat orchestration、expert router、resource monitor、RAG、ERP、Content、Trend、Stock 等）以类/函数形式注入 | 模块边界隐式，缺少契约/指标；模块状态共享同一进程缓存 |
| 数据层 | 以内存结构 + 文件模拟数据为主；向量存储/日志/配置分散 | 无租户隔离策略；未来迁移到外部服务将面临 schema/命名冲突 |
| Observability & Resource | `observability_system`、`resource_monitor`、`expert_router` 等已具备标签化能力 | 需要扩展 tenant 标签、SLO 指标，以及 per-module 审计 |

---

## 2. 分层与能力矩阵

| 层 | 目标 | 关键任务 |
| --- | --- | --- |
| Request Context | 所有入口必须携带 tenant/slo_context | 统一中间件、补充匿名接口校验、接入活动审计 |
| Module Contract | 每个模块暴露 facade（OpenAPI/ServiceAdapter） | `chat_orchestrator`, `rag_hub`, `content_ops`, `trend_ops`, `resource_ops` 等完成接口注册 |
| Data Access | tenant-aware data access（前缀/Schema/命名空间） | 落地租户配置中心、开始为模拟数据打 tenant 标签 |
| Observability & Resource | 以租户/模块为维度观测 | Trace/Metric/Resource monitor 增加 `tenant_id`、`module` 维度；导出 SLO |
| Deployment Readiness | 逐步抽象 service slice | Service Registry、Health Contract、Sidecar 适配、事件总线 |

---

## 3. 演进阶段

### Phase 0 · Context Isolation（Week 0-1）
- 扩散 `require_tenant`，并补齐资源/任务/内容等接口的租户参数
- super_agent.expert_router / resource_monitor 的缓存 key 加入 tenant
- 终端审计/WorkFlow monitor 写入 `tenant_id`
- Acceptance：tenancy_smoke_suite 通过；租户泄露=0

### Phase 1 · Module Contracts（Week 1-3）
- 为 chat / rag / trend / content / stock 模块声明内部 OpenAPI（或 Service Facade）
- observability_system 记录 module latency；expert_router 暴露 per-module 成功率
- Acceptance：module_contract_snapshot 覆盖 ≥80%

### Phase 2 · Service Slice（Week 3-6）
- 抽象 rag_hub、content_ops 为 ServiceAdapter，可配置为“本地函数 or Sidecar”
- 引入事件总线，将租户生命周期/配置变化广播给模块
- 准备 API Gateway/Ingress 配置清单
- Acceptance：service_slice_replay 通过；sidecar 启停<5分钟

### Phase 3 · Poly-Service Ready（Week 6+）
- 建立 Service Registry、Health contract；允许以进程/容器方式部署
- 数据访问层接入真实数据源（Postgres/Vector/Redis），能力 adapter tenant-aware
- 演练 Chaos/Fault/Upgrade
- Acceptance：observability trace 覆盖 ≥95%；tenancy regression=0

---

## 4. Guardrails
1. **单体优先**：所有新模块先以内嵌 adapter 形式提供服务，保持开发与部署简单。
2. **Tenant Everywhere**：从 API → Service → Data 的每一跳都必须携带 `tenant_id`，禁止在模块内部重新解码 JWT。
3. **Observability 第一**：拆分前必须具备模块级监控、日志、trace，以及标准 health contract。
4. **Shared Infra**：Resource monitor / expert router / observability 保持集中式，避免重复造轮子。
5. **渐进拆分**：优先拆分对外依赖强的模块（内容、RAG、资源执行），ERP/任务在完成持久化前保留在单体。

---

## 5. 配套交付
- API 端 `/api/super-agent/architecture/multitenant-plan` 返回上述 JSON 计划，给前端或脚本读取。
- 专家中枢/资源面板已支持 per-module 能力和路由，后续可展示多租户视角。
- TODO（下一阶段）：
  - 落地租户配置中心（文件 + 内存 + future DB）
  - 在 Resource/Expert/Task 等共享组件中使用 tenant-aware cache 接口
  - 编写 module runbook（拆分指南、回滚策略）

---

## 6. 参考接口
```bash
# 获取计划
curl http://localhost:8000/api/super-agent/architecture/multitenant-plan

# 触发 tenancy smoke / future
pytest tests/tenancy_smoke_suite.py
```

---

如需扩展：可在各模块 facade 中加入 `@tenant_required` 装饰器，与 `ResourceAuthorizationManager` / `ExpertRouter` 的租户上下文打通，并在事件总线中同步 tenant config。_READY_

