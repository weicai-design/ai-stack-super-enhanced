# 端到端真实性验证脚本使用说明

## 概述

本目录包含 P0-105 端到端真实性验证的测试脚本和报告生成器。

## 文件说明

- `e2e_validation.py`: 端到端测试脚本，测试两个代表性流程
- `generate_e2e_report.py`: 报告生成器，从测试结果生成Markdown报告
- `README_E2E.md`: 本文件，使用说明

## 前置条件

1. **API服务运行**: 确保AI-STACK API服务正在运行
   ```bash
   # 在项目根目录运行
   python -m uvicorn "🚀 Super Agent Main Interface.api.main:app" --host 0.0.0.0 --port 8000
   ```

2. **依赖安装**: 确保已安装所需依赖
   ```bash
   pip install httpx
   ```

3. **数据库初始化**: 确保数据库已初始化（如果使用数据库）

## 使用方法

### 1. 运行端到端测试

```bash
cd /Users/ywc/ai-stack-super-enhanced
python scripts/e2e_validation.py
```

**输出**:
- `artifacts/e2e_validation_report.json`: 测试结果JSON
- `e2e_validation.log`: 测试执行日志

### 2. 生成验证报告

```bash
python scripts/generate_e2e_report.py
```

**输出**:
- `P0-105-端到端流程验证报告.md`: Markdown格式的验证报告

### 3. 查看测试结果

```bash
# 查看测试日志
tail -f e2e_validation.log

# 查看测试结果JSON（需要jq）
cat artifacts/e2e_validation_report.json | jq

# 查看验证报告
cat P0-105-端到端流程验证报告.md
```

## 测试流程

### 流程1: 抖音内容生成发布

1. 生成故事板/脚本
2. 构建发布内容
3. 发布到抖音（包含合规检测、去AI化、风控评估）
4. 查询运营分析

### 流程2: ERP订单→生产→财务

1. 创建订单（模拟）
2. 运营试算（根据目标周营收）
3. 8D分析（质量/成本/交期等）
4. ERP数据同步到运营财务
5. 查询同步状态
6. 查询运营财务KPI

## 配置

### API基础URL

默认: `http://localhost:8000/api`

如需修改，编辑 `e2e_validation.py`:
```python
BASE_URL = "http://your-api-host:port/api"
```

### 超时时间

默认: 30秒

如需修改，编辑 `e2e_validation.py`:
```python
self.client = httpx.AsyncClient(timeout=60.0)  # 60秒
```

## 故障排查

### 1. 连接错误

**错误**: `Connection refused` 或 `Connection timeout`

**解决**:
- 检查API服务是否运行
- 检查API基础URL是否正确
- 检查防火墙设置

### 2. API调用失败

**错误**: `HTTP 404` 或 `HTTP 500`

**解决**:
- 检查API端点路径是否正确
- 检查请求参数格式是否正确
- 查看API服务日志

### 3. 测试失败

**错误**: 某个步骤测试失败

**解决**:
- 查看 `e2e_validation.log` 获取详细错误信息
- 检查测试数据是否正确
- 检查相关模块是否已加载

## 扩展

### 添加新流程测试

1. 在 `E2EValidator` 类中添加新的测试方法:
```python
async def test_new_flow(self) -> Dict[str, Any]:
    """测试新流程"""
    flow_name = "新流程名称"
    # ... 实现测试逻辑
    return flow_results
```

2. 在 `run_all_tests()` 中调用新方法:
```python
flow3_result = await self.test_new_flow()
report["flows"].append(flow3_result)
```

### 添加截图功能

1. 安装截图库（如 `selenium` 或 `playwright`）
2. 在测试步骤中添加截图代码:
```python
screenshot_path = self.screenshots_dir / f"{flow_name}_{step_name}.png"
# ... 截图代码
```

## 注意事项

1. **测试数据**: 测试使用的是模拟数据，不会影响生产环境
2. **并发测试**: 当前脚本是顺序执行，如需并发测试需要修改
3. **资源清理**: 测试完成后不会自动清理测试数据，需要手动清理（如需要）

## 相关文档

- `P0-105-端到端真实性验证交付文档.md`: 详细交付文档
- `P0-105-完整验证总结.md`: 验证总结
- `P0-105-端到端流程验证报告.md`: 生成的验证报告

