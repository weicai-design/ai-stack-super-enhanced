#!/usr/bin/env bash
# AI Stack Super Enhanced - 配置国内镜像（无VPN环境）
# 自动配置HuggingFace、PyPI等国内镜像源

set -euo pipefail
cd "$(dirname "$0")/.."

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      🇨🇳 配置国内镜像源（无VPN环境）                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 创建配置目录
mkdir -p .config
CONFIG_FILE=".config/china_mirrors.env"

# HuggingFace镜像配置
HF_MIRROR="https://hf-mirror.com"

# PyPI镜像配置（多个选项）
PYPI_MIRRORS=(
    "https://pypi.tuna.tsinghua.edu.cn/simple"  # 清华大学镜像（推荐）
    "https://mirrors.aliyun.com/pypi/simple"    # 阿里云镜像
    "https://pypi.douban.com/simple"            # 豆瓣镜像
    "https://mirrors.bfsu.edu.cn/pypi/web/simple" # 北京外国语大学镜像
)

# 选择第一个可用的PyPI镜像
PYPI_MIRROR="${PYPI_MIRRORS[0]}"

echo "📋 配置镜像源:"
echo ""
echo "  HuggingFace镜像: $HF_MIRROR"
echo "  PyPI镜像: $PYPI_MIRROR"
echo ""

# 生成环境变量配置文件
cat > "$CONFIG_FILE" <<EOF
# 国内镜像配置（无VPN环境）
# 生成时间: $(date +"%Y-%m-%d %H:%M:%S")

# HuggingFace镜像
export HF_ENDPOINT="$HF_MIRROR"
export HF_HOME="\${HF_HOME:-\$HOME/.cache/huggingface}"

# PyPI镜像
export PIP_INDEX_URL="$PYPI_MIRROR"
export PIP_TRUSTED_HOST=\$(echo "$PYPI_MIRROR" | sed 's|https\?://||' | cut -d/ -f1)

# 禁用自动更新（避免网络问题）
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export TRANSFORMERS_OFFLINE=0
EOF

echo "✅ 配置文件已生成: $CONFIG_FILE"
echo ""

# 配置pip镜像
echo "📦 配置pip镜像..."
if [ -f "$HOME/.pip/pip.conf" ]; then
    echo "⚠️  $HOME/.pip/pip.conf 已存在，备份为 .pip/pip.conf.bak"
    mkdir -p "$HOME/.pip"
    cp "$HOME/.pip/pip.conf" "$HOME/.pip/pip.conf.bak" 2>/dev/null || true
fi

mkdir -p "$HOME/.pip"
cat > "$HOME/.pip/pip.conf" <<EOF
[global]
index-url = $PYPI_MIRROR
trusted-host = $(echo "$PYPI_MIRROR" | sed 's|https\?://||' | cut -d/ -f1)

[install]
trusted-host = $(echo "$PYPI_MIRROR" | sed 's|https\?://||' | cut -d/ -f1)
EOF

echo "✅ pip配置已更新: $HOME/.pip/pip.conf"
echo ""

# 配置git（如果需要克隆HuggingFace仓库）
echo "🔧 配置git镜像（可选）..."
if command -v git >/dev/null 2>&1; then
    git config --global url."https://hf-mirror.com".insteadOf "https://huggingface.co" 2>/dev/null || true
    echo "✅ git镜像已配置"
fi
echo ""

# 创建加载脚本
LOAD_SCRIPT="scripts/load_china_mirrors.sh"
cat > "$LOAD_SCRIPT" <<'LOADEOF'
#!/usr/bin/env bash
# 加载国内镜像配置

if [ -f ".config/china_mirrors.env" ]; then
    source .config/china_mirrors.env
    echo "✅ 国内镜像配置已加载"
else
    echo "⚠️  配置文件不存在，运行 'bash scripts/setup_china_mirrors.sh' 生成"
fi
LOADEOF

chmod +x "$LOAD_SCRIPT"
echo "✅ 加载脚本已创建: $LOAD_SCRIPT"
echo ""

# 更新download_model.sh使其自动使用镜像
echo "🔄 更新模型下载脚本..."
if [ -f "scripts/download_model.sh" ]; then
    # 确保脚本使用镜像
    sed -i.bak 's|HF_ENDPOINT=.*|HF_ENDPOINT=https://hf-mirror.com|g' "scripts/download_model.sh" 2>/dev/null || \
    sed -i '' 's|HF_ENDPOINT=.*|HF_ENDPOINT=https://hf-mirror.com|g' "scripts/download_model.sh" 2>/dev/null || true
    echo "✅ 模型下载脚本已更新"
fi
echo ""

# 显示使用说明
cat <<EOF
╔══════════════════════════════════════════════════════════════╗
║      ✅ 国内镜像配置完成                                      ║
╚══════════════════════════════════════════════════════════════╝

📋 使用方法:

1. 手动加载配置:
   source .config/china_mirrors.env
   或
   source scripts/load_china_mirrors.sh

2. 在脚本中使用:
   source .config/china_mirrors.env && python your_script.py

3. 自动加载（添加到 ~/.bashrc 或 ~/.zshrc）:
   echo 'source $(pwd)/.config/china_mirrors.env' >> ~/.bashrc

4. 下载模型:
   bash scripts/download_model.sh

5. 安装依赖（已自动配置pip镜像）:
   pip install -r requirements.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 提示:

• HuggingFace模型会自动从 $HF_MIRROR 下载
• pip安装会自动使用 $PYPI_MIRROR
• 所有配置已持久化，无需每次手动设置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

echo "🎉 配置完成！现在可以在无VPN环境下使用系统。"

