# 验收矩阵文档

## 文件说明

- `requirements-v4.1.xlsx` - 验收矩阵Excel文件（通过API生成）

## 生成方式

### 方式1: 通过API生成

```bash
curl -X POST http://localhost:8020/api/super-agent/acceptance/matrix/generate
```

### 方式2: 通过Python脚本生成

```python
from core.acceptance_matrix_generator import acceptance_matrix_generator

# 生成Excel文件
output_file = acceptance_matrix_generator.generate_excel()
print(f"验收矩阵已生成: {output_file}")
```

## 验收矩阵结构

| 列名 | 说明 |
|------|------|
| 任务ID | 需求/任务唯一标识（如P0-001） |
| 类别 | 任务类别（基础设施/核心功能/RAG/ERP等） |
| 任务名称 | 任务名称 |
| 描述 | 任务描述 |
| 交付物 | 交付物列表（逗号分隔） |
| 状态 | 状态（completed/in_progress/pending） |
| 验收标准 | 验收标准描述 |
| 证据 | 证据文件路径或说明 |
| 测试结果 | 测试结果（pass/fail/pending） |
| 备注 | 备注信息 |
| 完成时间 | 完成时间戳 |

## 更新需求状态

```bash
curl -X PUT http://localhost:8020/api/super-agent/acceptance/matrix/requirement/P0-001 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "test_result": "pass",
    "evidence": "DEPLOYMENT_GUIDE.md",
    "notes": "已完成"
  }'
```

## 查看摘要

```bash
curl http://localhost:8020/api/super-agent/acceptance/matrix/summary
```

