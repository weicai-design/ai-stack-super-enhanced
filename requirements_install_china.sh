#!/usr/bin/env bash
# AI Stack Super Enhanced - 使用国内镜像安装依赖
# 无VPN环境优化

set -euo pipefail
cd "$(dirname "$0")"

# 加载镜像配置（如果存在）
if [ -f ".config/china_mirrors.env" ]; then
    source .config/china_mirrors.env
fi

# 使用国内PyPI镜像
PYPI_MIRROR="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TRUSTED_HOST=$(echo "$PYPI_MIRROR" | sed 's|https\?://||' | cut -d/ -f1)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      📦 使用国内镜像安装依赖（无VPN环境）                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 PyPI镜像: $PYPI_MIRROR"
echo "📋 信任主机: $TRUSTED_HOST"
echo ""

# 检查虚拟环境
if [ -d ".venv" ]; then
    PIP=".venv/bin/pip"
    PYTHON=".venv/bin/python"
elif [ -d "venv" ]; then
    PIP="venv/bin/pip"
    PYTHON="venv/bin/python"
else
    PIP="pip3"
    PYTHON="python3"
    echo "⚠️  警告: 未找到虚拟环境，使用系统pip"
    echo "   建议先创建虚拟环境: python3 -m venv .venv"
    echo ""
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 开始安装依赖..."
echo ""

# 升级pip（使用镜像）
$PIP install --upgrade pip -i "$PYPI_MIRROR" --trusted-host "$TRUSTED_HOST"

# 安装依赖（使用镜像）
$PIP install -r requirements.txt -i "$PYPI_MIRROR" --trusted-host "$TRUSTED_HOST"

echo ""
echo "✅ 依赖安装完成！"
echo ""
echo "💡 提示:"
echo "  • 如果某些包安装失败，尝试切换镜像:"
echo "    export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple"
echo "  • 下载模型: bash scripts/download_model.sh"
echo "  • 启动服务: make dev"

