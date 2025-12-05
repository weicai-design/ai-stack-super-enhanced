#!/bin/bash

echo "🚀 启动RAG系统 (Python 3.11)..."

RAG_DIR="/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph"

# 停止旧进程
lsof -ti:8011 | xargs kill -9 2>/dev/null
sleep 2

# 激活Python 3.11环境（使用新环境）
cd "$RAG_DIR"
if [ -d "venv_311_new" ]; then
    source venv_311_new/bin/activate
else
    # 如果新环境不存在，尝试创建
    python3.11 -m venv venv_311_new
    source venv_311_new/bin/activate
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    pip install fastapi uvicorn[standard] httpx pydantic > /dev/null 2>&1
fi

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


