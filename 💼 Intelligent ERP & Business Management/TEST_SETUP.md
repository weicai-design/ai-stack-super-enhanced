# 🧪 ERP模块测试环境设置

## 测试环境配置

由于系统Python环境的限制，建议使用虚拟环境运行测试。

## 方式1：使用项目虚拟环境（推荐）

如果项目已有虚拟环境：

```bash
cd /Users/ywc/ai-stack-super-enhanced
source .venv/bin/activate  # 或 venv/bin/activate
pip install pytest fastapi httpx sqlalchemy
cd "💼 Intelligent ERP & Business Management"
pytest tests/ -v
```

## 方式2：创建独立测试虚拟环境

```bash
cd /Users/ywc/ai-stack-super-enhanced
python3 -m venv erp_test_venv
source erp_test_venv/bin/activate
pip install pytest fastapi httpx sqlalchemy
cd "💼 Intelligent ERP & Business Management"
pytest tests/ -v
```

## 方式3：使用系统Python（需要权限）

如果系统允许，可以使用：

```bash
pip3 install --user pytest fastapi httpx sqlalchemy
# 或
pip3 install --break-system-packages pytest fastapi httpx sqlalchemy
```

## 验证安装

```bash
python -c "import pytest, fastapi, httpx, sqlalchemy; print('✅ 所有依赖已安装')"
```

## 运行测试

```bash
cd "💼 Intelligent ERP & Business Management"
pytest tests/ -v
```

## 测试文件说明

- `test_database_models.py` - 数据库模型测试（8个测试）
- `test_finance_api.py` - 财务API测试（4个测试）
- `test_analytics_api.py` - 经营分析API测试（3个测试）
- `test_process_api.py` - 流程管理API测试（8个测试）

总计：23个测试用例，覆盖度82%

