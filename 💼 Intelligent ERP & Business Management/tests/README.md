# ERP模块测试文档

## 测试文件结构

```
tests/
├── __init__.py
├── conftest.py                    # Pytest配置和公共fixtures
├── test_database_models.py        # 数据库模型测试
├── test_finance_api.py            # 财务API测试
├── test_analytics_api.py          # 经营分析API测试
├── test_process_api.py            # 流程管理API测试
├── run_tests.sh                   # 测试运行脚本
└── README.md                      # 本文件
```

## 运行测试

### 方式1: 使用测试脚本

```bash
cd "💼 Intelligent ERP & Business Management"
bash tests/run_tests.sh
```

### 方式2: 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_database_models.py -v

# 运行特定测试函数
pytest tests/test_finance_api.py::test_create_financial_data -v
```

### 方式3: 使用Python直接运行

```bash
# 运行特定测试文件
python tests/test_database_models.py
```

## 测试覆盖

### 数据库模型测试 (`test_database_models.py`)

- ✅ `test_financial_data_model` - 财务数据模型
- ✅ `test_customer_model` - 客户模型
- ✅ `test_order_model` - 订单模型
- ✅ `test_order_item_model` - 订单明细模型
- ✅ `test_business_process_model` - 业务流程模型
- ✅ `test_process_instance_model` - 流程实例模型
- ✅ `test_process_tracking_model` - 流程跟踪模型
- ✅ `test_relationships` - 模型关系测试

### 财务API测试 (`test_finance_api.py`)

- ✅ `test_create_financial_data` - 创建财务数据
- ✅ `test_get_finance_dashboard` - 获取财务看板
- ✅ `test_get_financial_data` - 查询财务数据
- ✅ `test_get_finance_dashboard_monthly` - 月度财务看板

### 经营分析API测试 (`test_analytics_api.py`)

- ✅ `test_revenue_analysis` - 开源分析
- ✅ `test_cost_analysis` - 成本分析
- ✅ `test_efficiency_analysis` - 产出效益分析

### 流程管理API测试 (`test_process_api.py`)

- ✅ `test_define_process` - 定义流程
- ✅ `test_create_process_instance` - 创建流程实例
- ✅ `test_track_process` - 流程跟踪
- ✅ `test_get_process_progress` - 获取流程进度
- ✅ `test_get_full_process_flow` - 全流程视图
- ✅ `test_create_exception` - 创建流程异常
- ✅ `test_get_exceptions` - 获取流程异常
- ✅ `test_get_improvements` - 获取改进计划

## 测试数据库

测试使用SQLite内存数据库 (`sqlite:///:memory:`)，每次测试后自动清理。

## 依赖

确保安装以下依赖：

```bash
pip install pytest
pip install fastapi
pip install httpx  # FastAPI TestClient需要
pip install sqlalchemy
```

## 注意事项

1. 测试使用内存数据库，不会影响实际数据
2. 每个测试文件都会独立设置和清理数据库
3. 使用FastAPI TestClient进行API测试
4. 所有测试都应该能独立运行

## 添加新测试

1. 在相应的测试文件中添加测试函数
2. 使用`@pytest.fixture`创建必要的测试数据
3. 确保测试可以独立运行
4. 遵循命名约定：`test_功能名称`

