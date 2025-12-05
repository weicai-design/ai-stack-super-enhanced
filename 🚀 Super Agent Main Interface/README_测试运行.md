# T001-T003 测试运行说明

## ⚠️ 重要提示

由于您的系统Python环境受保护（externally-managed-environment），需要特殊方式安装依赖。

## 🚀 推荐方法：使用虚拟环境

### 步骤1: 创建并激活虚拟环境

```bash
cd ~/ai-stack-super-enhanced/super_agent_main_interface

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 步骤2: 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或只安装测试依赖
pip install pytest pytest-asyncio httpx
```

### 步骤3: 运行测试

```bash
# 方法1: 使用脚本
./快速运行测试.sh

# 方法2: 直接运行
python3 -m pytest tests/test_workflow_integration.py -v
python3 -m pytest tests/test_rag_double_retrieval.py -v
python3 -m pytest tests/performance/test_slo_2s.py -v
```

### 步骤4: 退出虚拟环境（测试完成后）

```bash
deactivate
```

## 🔧 方法2: 使用--break-system-packages

如果不想使用虚拟环境，可以使用以下命令：

```bash
cd ~/ai-stack-super-enhanced/super_agent_main_interface

# 安装依赖
python3 -m pip install pytest pytest-asyncio httpx --break-system-packages

# 运行测试
./快速运行测试.sh
```

## 🎯 方法3: 使用一体化脚本

最简单的方式，脚本会自动处理虚拟环境：

```bash
cd ~/ai-stack-super-enhanced/super_agent_main_interface
./安装并运行测试.sh
```

脚本会：
1. 检测是否在虚拟环境中
2. 如果不在，询问是否创建虚拟环境
3. 自动安装依赖
4. 运行所有测试

## 📋 完整命令示例

```bash
# 进入目录
cd ~/ai-stack-super-enhanced/super_agent_main_interface

# 创建虚拟环境（如果还没有）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install pytest pytest-asyncio httpx

# 运行测试
python3 -m pytest tests/test_workflow_integration.py -v
python3 -m pytest tests/test_rag_double_retrieval.py -v
python3 -m pytest tests/performance/test_slo_2s.py -v

# 退出虚拟环境
deactivate
```

## 🔍 验证安装

运行以下命令验证pytest是否已安装：

```bash
python3 -m pytest --version
```

如果显示版本号，说明安装成功。

## 📊 查看测试报告

测试报告保存在 `logs/workflow/` 目录：

```bash
ls -lt logs/workflow/*.json
```

## ❓ 常见问题

### Q: 为什么需要虚拟环境？

A: macOS的Python环境受系统保护，直接安装包可能会失败。虚拟环境可以避免这个问题。

### Q: 虚拟环境会影响其他项目吗？

A: 不会。虚拟环境是独立的，只影响当前项目。

### Q: 每次都需要激活虚拟环境吗？

A: 是的。每次运行测试前需要 `source venv/bin/activate`。

### Q: 可以永久激活虚拟环境吗？

A: 可以在 `.zshrc` 或 `.bashrc` 中添加自动激活脚本，但不推荐。

## 🎉 快速开始

最简单的运行方式：

```bash
cd ~/ai-stack-super-enhanced/super_agent_main_interface
./安装并运行测试.sh
```

脚本会自动处理所有步骤！

