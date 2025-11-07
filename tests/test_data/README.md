# 测试数据目录

此目录用于存放测试数据文件。

## 文件说明

- `sample_*.json` - 示例数据文件
- `mock_*.json` - Mock数据文件
- `test_*.txt` - 测试文本文件

## 使用方法

```python
from tests.test_utils import test_helper

# 加载测试数据
data = test_helper.load_test_data("sample_data.json")

# 保存测试数据
test_helper.save_test_data("result.json", {"key": "value"})
```

