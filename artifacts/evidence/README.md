# Evidence & Closure Logs

本目录用于沉淀端到端闭环的“证据”：

- `closure_events.jsonl`：由 `ClosureRecorder` 自动生成的 JSON Lines，记录统一的 “接受 → 执行 → 检查 → 反馈 → 再执行” 事件。
- `closure_events.summary.json`：简要统计（总数 / 各阶段计次）。
- `sample_closure_event.jsonl`：示例文件，展示单个任务从接受到再执行的典型结构。

> 若需扩展其它模块的证据，请保持 JSONL 单行 JSON 的格式，便于机器解析；人类可通过 Markdown/截图等补充说明。***


