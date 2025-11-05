#!/bin/bash

echo "🚀 启动额外的业务服务..."
echo ""

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
VENV="$PROJECT_ROOT/venv"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 激活虚拟环境
source "$VENV/bin/activate"

# 启动函数
start_service() {
    local name=$1
    local port=$2
    local dir=$3
    local module=$4
    
    echo -e "${BLUE}➤ 启动 $name (端口 $port)...${NC}"
    
    # 检查端口是否被占用
    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}  ⚠ 端口 $port 已被占用，跳过${NC}"
        return
    fi
    
    # 切换到服务目录并启动
    cd "$dir"
    nohup $VENV/bin/python3 -m uvicorn $module --host 0.0.0.0 --port $port > "$LOG_DIR/${name}.log" 2>&1 &
    PID=$!
    
    echo "  PID: $PID"
    echo "  日志: $LOG_DIR/${name}.log"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否成功启动
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1 || curl -s "http://localhost:$port" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ 启动成功${NC}"
    else
        echo -e "${YELLOW}  ⚠ 可能未成功启动，请检查日志${NC}"
    fi
    
    echo ""
}

echo "1️⃣  启动RAG知识图谱系统"
echo "--------------------------------"
start_service "RAG" 8011 \
    "$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph" \
    "api.app:app"

echo "2️⃣  启动股票交易系统"
echo "--------------------------------"
start_service "Stock" 8014 \
    "$PROJECT_ROOT/📈 Intelligent Stock Trading" \
    "api.main:app"

echo "3️⃣  启动趋势分析系统"
echo "--------------------------------"
start_service "Trend" 8015 \
    "$PROJECT_ROOT/🔍 Intelligent Trend Analysis" \
    "api.main:app"

echo "4️⃣  启动内容创作系统"
echo "--------------------------------"
start_service "Content" 8016 \
    "$PROJECT_ROOT/🎨 Intelligent Content Creation" \
    "api.main:app"

echo "5️⃣  启动任务代理系统"
echo "--------------------------------"
start_service "Task" 8017 \
    "$PROJECT_ROOT/🤖 Intelligent Task Agent" \
    "web.api.main:app"

echo "6️⃣  启动资源管理系统"
echo "--------------------------------"
start_service "Resource" 8018 \
    "$PROJECT_ROOT/🛠️ Resource Management" \
    "api.main:app"

echo "7️⃣  启动自我学习系统"
echo "--------------------------------"
start_service "Learning" 8019 \
    "$PROJECT_ROOT/🧠 Self Learning System" \
    "api.main:app"

echo "================================"
echo -e "${GREEN}✅ 服务启动完成！${NC}"
echo "================================"
echo ""
echo "📋 所有服务列表："
echo "  ✓ OpenWebUI:  http://localhost:3000"
echo "  ✓ ERP前端:    http://localhost:8012"
echo "  ✓ ERP后端:    http://localhost:8013"
echo "  - RAG系统:    http://localhost:8011"
echo "  - 股票交易:   http://localhost:8014"
echo "  - 趋势分析:   http://localhost:8015"
echo "  - 内容创作:   http://localhost:8016"
echo "  - 任务代理:   http://localhost:8017"
echo "  - 资源管理:   http://localhost:8018"
echo "  - 自我学习:   http://localhost:8019"
echo ""
echo "📝 查看日志:"
echo "  tail -f $LOG_DIR/<service>.log"
echo ""
echo "🧪 运行健康检查:"
echo "  source venv/bin/activate && python3 scripts/system_health_check.py"
echo ""


