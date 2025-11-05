#!/bin/bash
# 简化版RAG启动脚本 - 避免后台进程阻塞

cd "/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph"

# 停止旧进程
lsof -ti:8011 | xargs kill -9 2>/dev/null
sleep 1

# 激活环境并启动（前台运行，便于调试）
source venv_311/bin/activate
python -m uvicorn api.app:app --host 0.0.0.0 --port 8011


