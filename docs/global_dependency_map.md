# 全局依赖映射（Global Dependency Map）

> 来源：`🚀 Super Agent Main Interface/core/configurable_api_connector.py`、`🚀 Super Agent Main Interface/core/api_credential_manager.py`、`api-gateway/gateway.py`

## 1. 外部 API 依赖

| 平台 | 基础域名 / 默认端点 | 端口 | 关键环境变量 / 凭证键 | 主要用途 |
|------|---------------------|------|------------------------|----------|
| 抖音开放平台 | `https://open.douyin.com` | 443 (HTTPS) | `DOUYIN_APP_ID`, `DOUYIN_APP_SECRET`, `DOUYIN_ACCESS_TOKEN`, `DOUYIN_CLIENT_KEY`, `DOUYIN_CLIENT_SECRET` | 视频发布、统计查询、Token 刷新 (`DouyinAPIConnector`) |
| 同花顺（10jqka） | `https://api.10jqka.com.cn` | 443 | `TONGHUASHUN_API_KEY`, `TONGHUASHUN_API_SECRET`, `THS_APP_KEY`, `THS_APP_SECRET` | 行情获取、账户查询、委托下单 (`Ths123APIConnector`) |
| ERP 平台 | `ERP_API_URL`（默认 `http://localhost:8013`） | `8013` | `ERP_API_KEY`, `ERP_USERNAME`, `ERP_PASSWORD` | 财务看板、订单管理、下单接口 (`ERPAPIConnector`) |
| 内容平台（通用） | `CONTENT_API_URL`（默认 `http://localhost:8016`） | `8016` | `CONTENT_ACCESS_TOKEN`, `CONTENT_API_KEY`（或自定义 `${PLATFORM}_ACCESS_TOKEN` / `${PLATFORM}_API_KEY`） | 内容发布、统计 (`ContentPlatformAPIConnector`) |
| API 凭证加密 | N/A | N/A | `API_CREDENTIAL_ENCRYPTION_KEY` | `APICredentialManager` 启动时读取/生成的 Fernet 密钥，用于 `.credentials/*.json` 加密存储 |

### 说明
- 所有外部连接器都会先从 `APICredentialManager` 读取凭证：优先环境变量，其次 `.credentials/<platform>.json`。
- `ConfigurableAPIConnector` 在模块导入时自动注册 `douyin`、`ths123`、`erp`、`content` 四个平台，必要时可在 `register_connector` 里追加其他平台。
- 若无真实 API，可通过设置相同 env 变量指向 Mock 服务。

## 2. 内部微服务 / 网关端口

来源：`api-gateway/gateway.py` 中 `ServiceRegistry.services`

| 服务标识 | 默认 URL | 描述 |
|----------|----------|------|
| `rag` | `http://localhost:8011` | 增强 RAG & 知识图谱服务 |
| `erp` | `http://localhost:8013` | 企业 ERP / 业务管理 |
| `openwebui` | `http://localhost:8020` | OpenWebUI 前端入口 |
| `stock` | `http://localhost:8015` | 智能股票/同花顺侧车 |
| `trend` | `http://localhost:8014` | 趋势分析服务 |
| `content` | `http://localhost:8016` | 内容创作/发布服务 |
| `agent` | `http://localhost:8017` | Super Agent 主接口 |
| `resource` | `http://localhost:8018` | 资源调度 / 监控 |
| `learning` | `http://localhost:8019` | 自我学习 / 建议系统 |
| **API Gateway** | `http://0.0.0.0:8000`（运行时配置） | 统一入口，转发到上述服务；健康检查 `/gateway/health` |

### 说明
- `ServiceRegistry` 当前写死本地端口，若部署到不同主机/容器，需要同步更新此映射或改为动态注册。
- API 网关通过 `/{service}/{path}` 动态代理请求，要求后端服务保持 `/health` 健康检查。

## 3. 依赖维护建议

1. **环境变量清单**：建议在 `env.example` 中列出上述所有变量，并标注是否必填、默认值。
2. **端口冲突检查**：`8011~8020` 端口请在启动前确保未被占用，可通过 `lsof -i :<port>` 自查。
3. **证书/密钥管理**：`.credentials/` 目录默认 600 权限，配合 `API_CREDENTIAL_ENCRYPTION_KEY` 统一加密；生产环境应将密钥由运维注入。
4. **依赖变更**：新增外部平台时，在 `ConfigurableAPIConnector` 注册并补充本文件，以保持依赖透明。



