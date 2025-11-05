#!/usr/bin/env bash
# AI Stack Super Enhanced - 模型下载脚本（使用镜像）
set -euo pipefail
cd "$(dirname "$0")/.."

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      📥 使用镜像站点下载模型                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

MODEL_DIR="models/all-MiniLM-L6-v2"
PYTHON="${PYTHON:-.venv/bin/python}"

# 检查虚拟环境
if [ ! -f "$PYTHON" ]; then
    if [ -d ".venv" ]; then
        PYTHON=".venv/bin/python"
    elif [ -d "venv" ]; then
        PYTHON="venv/bin/python"
    else
        PYTHON="python3"
        echo "⚠️  警告: 未找到虚拟环境，使用系统Python"
    fi
fi

echo "📋 使用Python: $PYTHON"
echo ""

# 设置镜像与本地缓存环境变量（无VPN环境）
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HOME="${HF_HOME:-$PWD/models}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$PWD/models}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$PWD/models}"
export SENTENCE_TRANSFORMERS_HOME="${SENTENCE_TRANSFORMERS_HOME:-$PWD/models}"

echo "🌐 使用HuggingFace镜像: $HF_ENDPOINT"
echo ""

# 创建模型目录
mkdir -p "$MODEL_DIR"
echo "📁 模型目录: $MODEL_DIR"
echo ""

echo "⏳ 开始下载模型（这可能需要1-3分钟）..."
echo ""

# 下载模型
$PYTHON << 'PYTHON_SCRIPT'
import os
import sys
from sentence_transformers import SentenceTransformer
from pathlib import Path

# 设置镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

model_name = 'all-MiniLM-L6-v2'
model_dir = Path('models/all-MiniLM-L6-v2')

print(f'📥 正在从镜像下载模型: {model_name}')
print(f'📂 保存到: {model_dir}')
print('')

try:
    # 下载模型
    model = SentenceTransformer(model_name)
    print(f'✅ 模型下载完成')
    
    # 保存到本地
    model.save(str(model_dir))
    print(f'✅ 模型已保存到: {model_dir}')
    print('')
    
    # 验证模型
    print('🔍 验证模型...')
    loaded_model = SentenceTransformer(str(model_dir))
    dim = loaded_model.get_sentence_embedding_dimension()
    print(f'✅ 模型验证成功，维度: {dim}')
    print('')
    print('🎉 模型下载完成！')
    
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 模型下载完成！"
    echo ""
    echo "📊 模型文件信息:"
    ls -lh "$MODEL_DIR"/*.bin "$MODEL_DIR"/*.safetensors 2>/dev/null | head -5 || echo "   检查模型目录内容..."
    echo ""
    echo "🚀 下一步: 运行 'make dev' 启动服务"
else
    echo ""
    echo "❌ 模型下载失败"
    echo ""
    echo "💡 可能的解决方案:"
    echo "   1. 检查网络连接"
    echo "   2. 确保已配置国内镜像: bash scripts/setup_china_mirrors.sh"
    echo "   3. 检查镜像配置: echo \$HF_ENDPOINT"
    echo "   4. 尝试手动设置镜像: export HF_ENDPOINT=https://hf-mirror.com"
    echo "   5. 手动下载模型文件（参考 NO_VPN_SETUP.md）"
    exit 1
fi

