# AI-STACK 部署与运行基线

> 目标：在不破坏现有多模块架构的前提下，为所有后续开发提供可复现、可审计的运行环境。

---

## 1. 目录结构总览

| 层级 | 说明 | 关键路径 |
| --- | --- | --- |
| 主控 | 超级 Agent / Chat UI / API 网关 | `🚀 Super Agent Main Interface/`、`api-gateway/` |
| 模块域 | RAG、ERP、内容、趋势、股票、任务、自我学习、资源等 | `📚 Enhanced RAG & Knowledge Graph/`、`💼 Intelligent ERP & Business Management/` 等 |
| 前端子项目 | Vite/Vue 控制台、静态 HTML | `💼 Intelligent ERP & Business Management/web/frontend/`、`🚀 Super Agent Main Interface/web/` |
| 运维脚本 | 一键启动、诊断、日志 | `scripts/`、`*.sh` |

---

## 2. Python 依赖安装

1. 创建虚拟环境（示例）  
   ```bash
   cd /Users/ywc/ai-stack-super-enhanced
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安装锁定依赖  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.lock
   ```
3. 模块私有依赖  
   - 若需启用单独模块（如 `📚 Enhanced RAG & Knowledge Graph`），在对应目录下执行各自 `requirements.txt`。
   - 避免 `pip install -r requirements.txt` 与 `requirements.lock` 混用，可使用 `pip install -r requirements.lock` 后按需补充模块独占包。

---

## 3. 前端依赖安装（Vite/Vue 控制台）

1. 安装 Node 18+ / npm 10+。
2. 在 ERP 前端目录生成锁文件（已完成，可复用）：  
   ```bash
   cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management/web/frontend"
   npm ci   # 使用 package-lock.json 复现依赖
   ```
3. 运行开发/构建脚本：  
   ```bash
   npm run dev        # 默认 8012 端口
   npm run build      # 产出 dist
   npm run preview    # 预览构建结果
   ```
4. 其他静态页面位于 `🚀 Super Agent Main Interface/web/` 等目录，无需额外打包，只需通过后端 static route 暴露。

---

## 4. 环境变量管理

1. 复制 `env.example` → `.env`，并根据章节补齐密钥（OpenAI、Ollama、Douyin、THS、数据库等）。  
2. 若运行特定模块，请同步设置模块级变量（例如 `RAG_API_URL`、`ERP_EXPORT_DIR`）。  
3. 推荐使用 direnv / dotenv CLI 管理多套环境；生产环境统一注入到进程管理器（systemd、Supervisor、Docker Compose）。
4. 安全相关变量：
   - `API_TOKEN` / `SUPER_AGENT_API_TOKEN`：全局 API 访问令牌（对应 `X-API-KEY` header）。
   - `SECURITY_AUDIT_LOG` / `SECURITY_LOG_DIR`：安全审计 JSONL 输出位置。
   - `SENSITIVE_KEYWORDS`：逗号分隔的敏感词列表，用于输入过滤。
   - `TERMINAL_WHITELIST_PATH`：终端命令白名单配置文件，可随自定义而扩展。

---

## 5. 启动顺序建议

1. **核心数据服务**：数据库（SQLite / PostgreSQL / Redis）、本地向量库（FAISS / Chroma）。  
2. **后端 API**：  
   - `uvicorn 🚀 Super Agent Main Interface.api.super_agent_api:app --host 0.0.0.0 --port 8000`  
   - 其他模块（RAG、ERP、内容等）按需启动。  
3. **前端 / 静态站点**：  
   - `npm run dev` 或提供构建后的 `dist` 给 Nginx。  
   - 纯 HTML 页可由主 API 的 `StaticFiles` 直接服务。  
4. **辅助服务**：任务调度、资源监控、审计/日志收集。

---

## 6. 依赖一致性与冲突检测

- 运行 `python scripts/check_dependencies.py`：  
  - 第一步执行 `pip check`，确保 Python 依赖图无冲突；  
  - 第二步对比 `requirements.txt` 与 `requirements.lock`，提示遗漏/新增；  
  - 第三步在 ERP 前端目录执行 `npm ls --depth=0`，确保 Node 依赖可解析。  
- 若需扩展其它前端子项目，请在对应目录运行 `npm install --package-lock-only` 并纳入版本控制。

---

## 7. 日志与可观测性

- 后端：默认输出到 stdout，可通过 `LOG_LEVEL` 控制。建议在 `logs/` 下集中存档，并配置 Prometheus/Alertmanager（已有 `prometheus-client` 依赖）。  
- 前端：Vite Dev Server 自带日志；生产模式建议通过 Nginx access/error log 统一收集。  
- 运行闭环：结合 `artifacts/evidence/`（建议目录）记录端到端执行录像、脚本、指标快照。

---

## 8. 常见问题

| 场景 | 处理建议 |
| --- | --- |
| Python 依赖冲突 | 运行 `python scripts/check_dependencies.py`，根据输出调整 `requirements.lock`；必要时使用 `pip install --force-reinstall 包名==版本`。 |
| npm 包版本不一致 | 执行 `npm ci` 而非 `npm install`；若需新增依赖，`npm install 包名 --save` 后同步提交 `package-lock.json`。 |
| 无法访问外部 API | 检查 `.env` 或部署平台的密钥注入；必要时配置代理。 |
| 模块端口冲突 | 通过 `HOST` / `PORT` 环境变量重载默认值；保持 API Gateway 统一入口。 |

---

此指南随代码库版本更新而演化，所有新增模块/服务请补充各自的依赖说明，并保持与主锁文件一致。欢迎在共建过程中提出改进建议。***

