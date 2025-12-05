#!/bin/bash
# 运行 pytest 测试的便捷脚本
# 自动设置 PYTHONPATH 并运行核心测试

cd "$(dirname "$0")"

PYTHONPATH="/Users/ywc/ai-stack-super-enhanced/🚀 Super Agent Main Interface:/Users/ywc/ai-stack-super-enhanced/super_agent_main_interface" \
.venv/bin/pytest ai_stack/tests "🚀 Super Agent Main Interface/tests" "📚 Enhanced RAG & Knowledge Graph/tests" "$@"





