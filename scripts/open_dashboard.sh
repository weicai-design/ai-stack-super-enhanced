#!/usr/bin/env bash
# AI Stack Super Enhanced - 打开功能界面

set -euo pipefail
cd "$(dirname "$0")/.."

API_URL="http://127.0.0.1:8011"
DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"

# 检查API服务是否运行
echo "🔍 检查API服务状态..."
if ! curl -s -f "$API_URL/readyz" >/dev/null 2>&1; then
    echo "❌ API服务未运行"
    echo "📋 请先启动API服务: make dev"
    echo ""
    read -p "是否现在启动API服务? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 正在启动API服务..."
        make dev &
        sleep 5
        echo "⏳ 等待API服务启动..."
        for i in {1..30}; do
            if curl -s -f "$API_URL/readyz" >/dev/null 2>&1; then
                echo "✅ API服务已启动"
                break
            fi
            sleep 1
        done
    else
        exit 1
    fi
fi

echo "✅ API服务正在运行"
echo ""

# 启动Web界面服务器
echo "🚀 启动功能界面服务器..."
echo "📍 访问地址: http://localhost:$DASHBOARD_PORT"
echo ""

# 使用Python内置HTTP服务器
cd "📚 Enhanced RAG & Knowledge Graph/web"

python3 -m http.server $DASHBOARD_PORT 2>/dev/null &
SERVER_PID=$!

echo "✅ 功能界面服务器已启动 (PID: $SERVER_PID)"
echo ""
echo "🌐 正在打开浏览器..."

# 根据操作系统打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:$DASHBOARD_PORT"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "http://localhost:$DASHBOARD_PORT" 2>/dev/null || echo "请手动访问: http://localhost:$DASHBOARD_PORT"
else
    echo "请手动访问: http://localhost:$DASHBOARD_PORT"
fi

echo ""
echo "按 Ctrl+C 停止服务器"

# 等待用户中断
wait $SERVER_PID
