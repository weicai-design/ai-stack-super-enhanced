#!/bin/bash

echo "🚀 启动RAG系统 (Python 3.11)..."

RAG_DIR="/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph"

# 停止旧进程
lsof -ti:8011 | xargs kill -9 2>/dev/null
sleep 2

# 激活Python 3.11环境
cd "$RAG_DIR"
source venv_311/bin/activate

# 启动服务
nohup python -m uvicorn api.app:app --host 0.0.0.0 --port 8011 > /tmp/rag-system.log 2>&1 &
PID=$!

echo "   PID: $PID"
echo "   日志: /tmp/rag-system.log"

# 等待启动
sleep 5

# 测试服务
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "   ✅ RAG系统启动成功！"
    echo ""
    echo "   访问地址: http://localhost:8011"
    echo "   API文档: http://localhost:8011/docs"
else
    echo "   ❌ RAG系统启动失败"
    echo "   查看日志: tail -f /tmp/rag-system.log"
fi


