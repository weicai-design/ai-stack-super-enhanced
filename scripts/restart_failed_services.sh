#!/bin/bash

echo "🔄 重启失败的服务..."
echo ""

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
VENV="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 激活虚拟环境
source "$VENV/bin/activate"

# 启动函数
restart_service() {
    local name=$1
    local port=$2
    local dir=$3
    local module=$4
    
    echo -e "${BLUE}➤ 重启 $name (端口 $port)...${NC}"
    
    # 停止旧进程
    lsof -ti:$port | xargs kill -9 2>/dev/null
    sleep 1
    
    # 启动服务
    cd "$dir"
    nohup $VENV/bin/python3 -m uvicorn $module --host 0.0.0.0 --port $port > "$LOG_DIR/${name}.log" 2>&1 &
    PID=$!
    
    echo "  PID: $PID"
    
    # 等待服务启动
    sleep 5
    
    # 检查服务
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1 || curl -s "http://localhost:$port" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ 启动成功${NC}"
        return 0
    else
        echo -e "  ✗ 启动失败，查看日志: tail $LOG_DIR/${name}.log"
        return 1
    fi
}

echo "1️⃣  重启RAG系统"
echo "--------------------------------"
restart_service "RAG" 8011 \
    "$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph" \
    "api.app:app"
echo ""

echo "2️⃣  重启趋势分析系统"
echo "--------------------------------"
restart_service "Trend" 8015 \
    "$PROJECT_ROOT/🔍 Intelligent Trend Analysis" \
    "api.main:app"
echo ""

echo "3️⃣  重启内容创作系统"
echo "--------------------------------"
restart_service "Content" 8016 \
    "$PROJECT_ROOT/🎨 Intelligent Content Creation" \
    "api.main:app"
echo ""

echo "================================"
echo -e "${GREEN}✅ 重启完成！${NC}"
echo "================================"


