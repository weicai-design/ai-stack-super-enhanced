# AI Stack 安装指南

## Python 版本要求

**重要：必须使用 Python 3.12.x**

- ✅ **推荐：Python 3.12.x**（PyTorch 官方支持）
- ❌ **不支持：Python 3.13**（PyTorch 暂不支持，会导致 `sentence-transformers` 无法安装）

### 检查 Python 版本

```bash
python3.12 --version
# 应显示：Python 3.12.x
```

如果没有 Python 3.12，请先安装：
- macOS: `brew install python@3.12`
- 或使用 pyenv: `pyenv install 3.12.11`

## 安装步骤

### 1. 创建虚拟环境

```bash
cd /path/to/ai-stack-super-enhanced
python3.12 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows
```

### 2. 升级 pip

```bash
pip install --upgrade pip
```

### 3. 安装 PyTorch（必需）

由于 `sentence-transformers` 依赖 PyTorch，需要先安装：

```bash
# 使用清华镜像（推荐）
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用官方源（CPU 版本）
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

### 5. 生成锁定文件（可选）

```bash
pip freeze > requirements-locked.txt
```

### 6. 验证安装

运行依赖检查脚本：

```bash
python scripts/check_dependencies.py
```

应该看到：
- ✅ requirements.txt 与 requirements-locked.txt 无缺包或版本冲突
- ✅ 当前 Python 依赖无冲突
- ✅ npm 依赖解析成功

## 环境配置

1. 复制环境变量模板：
   ```bash
   cp env.example .env
   ```

2. 编辑 `.env` 文件，填入你的 API 密钥和配置。

3. 详细配置说明请参考 `env.example` 中的注释。

## 常见问题

### Q: 安装时提示 "No matching distribution found for torch"

**A:** 这通常是因为使用了 Python 3.13。请切换到 Python 3.12：
```bash
# 删除旧虚拟环境
rm -rf .venv

# 使用 Python 3.12 创建新环境
python3.12 -m venv .venv
source .venv/bin/activate
pip install torch
pip install -r requirements.txt
```

### Q: 安装 sentence-transformers 时提示需要 torch

**A:** 这是正常的。请先安装 torch（见步骤 3），然后再安装 requirements.txt。

### Q: 依赖冲突怎么办？

**A:** 运行 `python scripts/check_dependencies.py` 查看详细报告，或运行 `pip check` 检查冲突。

## 下一步

安装完成后，请参考：
- `README.md` - 项目概述
- `docs/global_dependency_map.md` - 依赖关系图
- `env.example` - 环境变量配置说明

