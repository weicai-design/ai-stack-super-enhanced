#!/bin/bash

echo "🛑 正在停止ERP系统..."
echo ""

# 方法1：使用保存的PID
if [ -f /tmp/erp-backend.pid ]; then
    BACKEND_PID=$(cat /tmp/erp-backend.pid)
    echo "停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm /tmp/erp-backend.pid
fi

if [ -f /tmp/erp-frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/erp-frontend.pid)
    echo "停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm /tmp/erp-frontend.pid
fi

# 方法2：通过端口查找并停止
echo "清理端口占用..."
lsof -ti :8012 | xargs kill -9 2>/dev/null
lsof -ti :8013 | xargs kill -9 2>/dev/null

sleep 1

# 验证
if lsof -i :8012 > /dev/null 2>&1; then
    echo "❌ 端口8012仍被占用"
else
    echo "✅ 前端服务已停止（端口8012）"
fi

if lsof -i :8013 > /dev/null 2>&1; then
    echo "❌ 端口8013仍被占用"
else
    echo "✅ 后端服务已停止（端口8013）"
fi

echo ""
echo "🎉 ERP系统已停止！"

