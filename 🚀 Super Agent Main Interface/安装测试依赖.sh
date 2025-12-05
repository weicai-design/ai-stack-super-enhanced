#!/bin/bash
# 安装测试依赖脚本

echo "=========================================="
echo "安装测试依赖（pytest, httpx）"
echo "=========================================="

# 检查Python版本
python3 --version

# 安装pytest（使用--user标志避免系统包管理冲突）
echo "安装 pytest..."
python3 -m pip install pytest>=7.0.0 pytest-asyncio>=0.21.0 --user --quiet

# 安装httpx（使用--user标志）
echo "安装 httpx..."
python3 -m pip install httpx>=0.24.0 --user --quiet

# 验证安装
echo ""
echo "验证安装:"
python3 -m pytest --version || echo "警告: pytest可能未正确安装"
python3 -c "import httpx; print(f'httpx版本: {httpx.__version__}')" || echo "警告: httpx可能未正确安装"

echo ""
echo "=========================================="
echo "依赖安装完成"
echo "=========================================="
echo ""
echo "如果安装失败，可以尝试:"
echo "  python3 -m pip install pytest httpx --user"
echo "或者使用虚拟环境:"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"

