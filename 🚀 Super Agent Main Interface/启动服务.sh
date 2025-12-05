#!/bin/bash

# 超级Agent主界面启动脚本

echo "🚀 正在启动AI-STACK超级Agent主界面..."
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ -f "requirements.txt" ]; then
    echo "📦 安装依赖..."
    pip install -q -r requirements.txt
fi

# 检查端口占用
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用，正在清理..."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动服务
echo "🔧 启动服务（端口 $PORT）..."
echo ""

uvicorn api.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --reload \
    --log-level info

echo ""
echo "✅ 服务已启动"
echo "📍 访问地址: http://localhost:$PORT"
echo "📚 API文档: http://localhost:$PORT/docs"

