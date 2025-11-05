#!/bin/bash

echo "🚀 正在启动ERP系统..."
echo ""

# 定义项目路径
ERP_DIR="/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management"

# 检查并停止已有服务
echo "🧹 清理旧服务..."
lsof -ti :8012 | xargs kill -9 2>/dev/null
lsof -ti :8013 | xargs kill -9 2>/dev/null
sleep 1

# 启动后端服务
echo "📡 启动后端服务..."
cd "$ERP_DIR"
source venv/bin/activate
nohup uvicorn api.main:app --host 0.0.0.0 --port 8013 --reload > /tmp/erp-backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端PID: $BACKEND_PID"

# 等待后端启动
echo "   等待后端启动..."
sleep 3

# 测试后端
if curl -s http://localhost:8013/health > /dev/null 2>&1; then
    echo "   ✅ 后端服务启动成功！"
else
    echo "   ❌ 后端服务启动失败，请查看日志: tail /tmp/erp-backend.log"
    exit 1
fi

# 启动前端服务
echo ""
echo "🎨 启动前端服务..."
cd "$ERP_DIR/web/frontend"
nohup npm run dev > /tmp/erp-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端PID: $FRONTEND_PID"

# 等待前端启动
echo "   等待前端启动..."
sleep 5

# 测试前端
if curl -s http://localhost:8012 > /dev/null 2>&1; then
    echo "   ✅ 前端服务启动成功！"
else
    echo "   ❌ 前端服务启动失败，请查看日志: tail /tmp/erp-frontend.log"
    exit 1
fi

# 显示信息
echo ""
echo "=" | awk '{for(i=0;i<50;i++)printf"=";printf"\n"}'
echo "✅ ERP系统启动完成！"
echo "=" | awk '{for(i=0;i<50;i++)printf"=";printf"\n"}'
echo ""
echo "🌐 访问地址:"
echo "   前端首页: http://localhost:8012"
echo "   财务看板: http://localhost:8012/finance/dashboard"
echo "   API文档:  http://localhost:8013/docs"
echo ""
echo "📝 查看日志:"
echo "   前端: tail -f /tmp/erp-frontend.log"
echo "   后端: tail -f /tmp/erp-backend.log"
echo ""
echo "🛑 停止服务:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   或运行: ./stop_erp.sh"
echo ""
echo "🎉 保存PID到文件..."
echo "$BACKEND_PID" > /tmp/erp-backend.pid
echo "$FRONTEND_PID" > /tmp/erp-frontend.pid

# 自动打开浏览器
echo "🌐 正在打开浏览器..."
sleep 2
open http://localhost:8012

echo ""
echo "✨ 享受使用ERP系统吧！"

