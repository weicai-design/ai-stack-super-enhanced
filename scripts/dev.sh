#!/usr/bin/env bash
# AI Stack Super Enhanced - 开发环境启动脚本
set -euo pipefail
cd "$(dirname "$0")/.."

# 加载国内镜像配置（如果存在，无VPN环境）
if [ -f ".config/china_mirrors.env" ]; then
    source .config/china_mirrors.env
    echo "✅ 已加载国内镜像配置（无VPN环境）"
fi

# 设置环境变量
PYTHONPATH="${PYTHONPATH:-}"
export PYTHONPATH="$PWD/📚 Enhanced RAG & Knowledge Graph:$PYTHONPATH"
export LOCAL_ST_MODEL_PATH="$PWD/models/all-MiniLM-L6-v2"

# 确保HuggingFace镜像与本地缓存已设置（无VPN环境）
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-$PWD/models}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$PWD/models}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$PWD/models}"
export SENTENCE_TRANSFORMERS_HOME="${SENTENCE_TRANSFORMERS_HOME:-$PWD/models}"
echo "🌐 使用HF镜像: $HF_ENDPOINT"
echo "💾 模型缓存目录: $HF_HOME"

# 检查Python环境
if [ -d "$PWD/.venv" ]; then
    PYTHON="$PWD/.venv/bin/python"
elif [ -d "$PWD/venv" ]; then
    PYTHON="$PWD/venv/bin/python"
else
    PYTHON="python3"
    echo "警告: 未找到虚拟环境，使用系统Python: $PYTHON"
fi

# 清理已占用的端口
if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:8011 -sTCP:LISTEN -t | xargs -r kill || true
fi

# 启动服务
exec "$PYTHON" -m uvicorn "api.app:app" \
  --app-dir "📚 Enhanced RAG & Knowledge Graph" \
  --host 127.0.0.1 --port 8011 --reload
