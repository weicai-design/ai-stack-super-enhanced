# 证据归档说明

此目录用于保存“功能 × 需求 × 证据”矩阵对应的佐证材料，建议按以下结构维护：

- `screenshots/`：界面、流程或监控图（命名示例：`2025-11-20-super-agent-dashboard.png`）
- `logs/`：任务执行、API 调用、SLO/混沌测试日志（建议压缩存档）
- `reports/`：PDF/HTML 报告、白皮书、SLO JSON 等

每新增一条证据时：
1. 将原始文件放入上述子目录并添加简短说明（可用 `README.md` 或 `index.json` 维护索引）。
2. 在 `docs/compliance/function_requirement_evidence_matrix.md` 对应行更新“所需证据”列，引用该文件路径或外链。
3. 若证据来自脚本运行（性能测试、API 验证等），尽量保留执行命令与输出摘要，便于复现。

> 建议在 CI/CD 中自动上传关键日志/截图到对象存储，再同步记录到矩阵，形成闭环。

