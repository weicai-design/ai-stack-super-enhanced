#!/bin/bash

# ERP系统服务启动脚本
# 一键启动前后端服务

echo "🚀 正在启动ERP系统服务..."
echo ""

# 进入ERP目录
cd "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"

# 检查端口占用
echo "📍 检查端口占用..."
if lsof -Pi :8012 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8012已被占用，正在清理..."
    lsof -ti :8012 | xargs kill -9
    sleep 1
fi

if lsof -Pi :8013 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8013已被占用，正在清理..."
    lsof -ti :8013 | xargs kill -9
    sleep 1
fi

echo "✅ 端口清理完成"
echo ""

# 启动后端服务
echo "🔧 启动后端服务（端口8013）..."
source venv/bin/activate
nohup uvicorn api.main:app --host 0.0.0.0 --port 8013 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo ""

# 等待后端启动
echo "⏳ 等待后端服务就绪..."
sleep 3

# 检查后端健康状态
if curl -s http://localhost:8013/health > /dev/null; then
    echo "✅ 后端服务健康检查通过"
else
    echo "❌ 后端服务启动失败，请查看 logs/backend.log"
    exit 1
fi
echo ""

# 启动前端服务
echo "🎨 启动前端服务（端口8012）..."
cd web/frontend
nohup npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
echo ""

# 等待前端启动
echo "⏳ 等待前端服务就绪..."
sleep 3

# 检查前端状态
if curl -s http://localhost:8012 > /dev/null; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败，请查看 logs/frontend.log"
    exit 1
fi
echo ""

# 打印服务信息
echo "════════════════════════════════════════"
echo "🎉 ERP系统服务已全部启动！"
echo "════════════════════════════════════════"
echo ""
echo "📍 访问地址："
echo "   前端系统: http://localhost:8012"
echo "   后端API:  http://localhost:8013"
echo "   API文档:  http://localhost:8013/docs"
echo ""
echo "📊 服务状态："
echo "   前端 PID: $FRONTEND_PID"
echo "   后端 PID: $BACKEND_PID"
echo ""
echo "📝 日志文件："
echo "   前端日志: logs/frontend.log"
echo "   后端日志: logs/backend.log"
echo ""
echo "🛑 停止服务："
echo "   kill $FRONTEND_PID $BACKEND_PID"
echo ""

# 打开浏览器
echo "🌐 正在打开浏览器..."
sleep 2
open http://localhost:8012

echo ""
echo "✅ 完成！请在浏览器中查看效果"
echo ""
echo "💡 提示："
echo "   - 如果页面空白，请按 Cmd+Shift+R 强制刷新"
echo "   - 如果还是不行，按 F12 打开开发者工具查看错误"
echo ""

