#!/bin/bash

# AI-STACK V5.8 Ollama启用脚本

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║         🚀 AI-STACK V5.8 Ollama启用脚本                   ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 1. 检查Ollama安装
echo "【步骤1】检查Ollama安装..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama已安装"
    ollama --version
else
    echo "❌ Ollama未安装"
    echo "安装命令: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# 2. 检查Ollama服务
echo ""
echo "【步骤2】检查Ollama服务..."
if curl -s http://localhost:11434/api/version &> /dev/null; then
    echo "✅ Ollama服务运行中"
else
    echo "⚠️ Ollama服务未运行，正在启动..."
    ollama serve &
    sleep 5
fi

# 3. 检查可用模型
echo ""
echo "【步骤3】检查可用模型..."
ollama list

# 4. 推荐模型
echo ""
echo "【步骤4】推荐模型（如未安装）..."
if ! ollama list | grep -q "qwen:7b"; then
    echo "⚠️ 推荐模型qwen:7b未安装"
    echo "下载命令: ollama pull qwen:7b"
    echo "或使用其他模型: llama2:7b, mistral:7b"
else
    echo "✅ 推荐模型qwen:7b已安装"
fi

# 5. 设置环境变量
echo ""
echo "【步骤5】配置环境变量..."
export USE_OLLAMA=true
export OLLAMA_BASE_URL=http://localhost:11434
export DEFAULT_OLLAMA_MODEL=qwen:7b
export ENABLE_SELF_LEARNING=true

echo "✅ 环境变量已设置:"
echo "   USE_OLLAMA=true"
echo "   OLLAMA_BASE_URL=http://localhost:11434"
echo "   DEFAULT_OLLAMA_MODEL=qwen:7b"
echo "   ENABLE_SELF_LEARNING=true"

# 6. 测试Ollama
echo ""
echo "【步骤6】测试Ollama对话..."
curl -s -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen:7b",
    "messages": [{"role":"user","content":"你好"}],
    "stream": false
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    msg = d.get('message', {}).get('content', '')
    print(f'✅ Ollama对话测试通过: {msg[:50]}...')
except:
    print('⚠️ Ollama对话测试失败')
"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║         ✅ Ollama已就绪！                                 ║"
echo "║                                                           ║"
echo "║   启动AI-STACK命令:                                       ║"
echo "║   cd '📚 Enhanced RAG & Knowledge Graph'                  ║"
echo "║   USE_OLLAMA=true python -m uvicorn api.app:app --reload ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"


