# 贡献指南

感谢您对 AI Stack 项目感兴趣！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告Bug

如果您发现了bug，请：

1. 检查 [Issues](issues) 确保问题尚未被报告
2. 创建新的 Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 预期行为和实际行为
   - 系统环境信息
   - 截图或日志（如适用）

### 提出新功能

如果您有新功能建议：

1. 先在 Issues 中讨论您的想法
2. 等待维护者反馈
3. 获得批准后开始实现

### 提交代码

#### 1. Fork 仓库

```bash
# Fork到您的账户
# 克隆您的Fork
git clone https://github.com/your-username/ai-stack-super-enhanced.git
cd ai-stack-super-enhanced
```

#### 2. 创建分支

```bash
# 基于develop分支创建功能分支
git checkout -b feature/your-feature-name develop
```

分支命名规范：
- `feature/功能名` - 新功能
- `bugfix/问题描述` - Bug修复
- `hotfix/紧急修复` - 紧急修复
- `docs/文档更新` - 文档更新

#### 3. 开发

```bash
# 设置开发环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 进行开发
# ...

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8 .
```

#### 4. 提交

```bash
# 添加修改
git add .

# 提交（使用有意义的提交信息）
git commit -m "feat: 添加新功能描述"
```

提交信息格式：
- `feat: 功能描述` - 新功能
- `fix: 问题描述` - Bug修复
- `docs: 文档描述` - 文档更新
- `style: 样式调整` - 代码格式（不影响功能）
- `refactor: 重构描述` - 代码重构
- `test: 测试相关` - 添加或修改测试
- `chore: 杂项` - 构建过程或辅助工具的变动

#### 5. 推送

```bash
# 推送到您的Fork
git push origin feature/your-feature-name
```

#### 6. 创建Pull Request

1. 访问原仓库
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写PR描述：
   - 修改内容
   - 相关Issue
   - 测试情况
   - 截图（如适用）

## 📝 代码规范

### Python代码

遵循 PEP 8：

```python
# 好的示例
def calculate_total(items: List[Item]) -> float:
    """
    计算总价
    
    Args:
        items: 商品列表
    
    Returns:
        总价
    """
    return sum(item.price for item in items)
```

### 文档字符串

使用Google风格：

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述
    
    详细描述（如需要）
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
    
    Returns:
        返回值描述
    
    Raises:
        ValueError: 异常描述
    """
    pass
```

### 测试

- 为新功能编写测试
- 确保所有测试通过
- 保持测试覆盖率 >80%

```python
import pytest

def test_calculate_total():
    """测试计算总价功能"""
    items = [Item(price=10), Item(price=20)]
    assert calculate_total(items) == 30
```

## 🔍 代码审查

所有PR都需要经过代码审查：

- 至少一位维护者批准
- 所有CI检查通过
- 无merge冲突

## 📋 清单

提交PR前确保：

- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交信息清晰
- [ ] 没有不必要的文件

## 🏷️ Issue和PR标签

- `bug` - Bug报告
- `enhancement` - 功能增强
- `documentation` - 文档相关
- `good first issue` - 适合新手
- `help wanted` - 需要帮助
- `priority: high` - 高优先级
- `wip` - 进行中

## 💬 交流

- GitHub Issues - Bug报告和功能建议
- GitHub Discussions - 一般讨论
- Email - support@example.com

## 📜 许可证

提交代码即表示您同意按照项目的 MIT 许可证授权您的贡献。

## 🙏 感谢

感谢您的贡献！每一个贡献都让 AI Stack 变得更好。




