#!/bin/bash

echo "🚀 一键启动所有AI Stack服务..."
echo "================================"
echo ""

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 启动函数
start_service() {
    local name=$1
    local port=$2
    local cmd=$3
    
    echo -e "${BLUE}启动 $name (端口 $port)...${NC}"
    
    # 停止旧进程
    lsof -ti:$port | xargs kill -9 2>/dev/null
    sleep 1
    
    # 启动服务
    eval "$cmd" > "$LOG_DIR/${name}.log" 2>&1 &
    PID=$!
    
    echo "  PID: $PID"
    sleep 2
}

# 1. 启动ERP系统
echo "1️⃣  ERP系统"
start_service "ERP-Backend" 8013 \
    "cd '$PROJECT_ROOT/💼 Intelligent ERP & Business Management' && source venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8013"

start_service "ERP-Frontend" 8012 \
    "cd '$PROJECT_ROOT/💼 Intelligent ERP & Business Management/web/frontend' && npm run dev"

# 2. 启动RAG系统 (Python 3.11)
echo ""
echo "2️⃣  RAG系统 (Python 3.11)"
start_service "RAG" 8011 \
    "cd '$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph' && source venv_311/bin/activate && python -m uvicorn api.app:app --host 0.0.0.0 --port 8011"

# 3. 启动其他服务
echo ""
echo "3️⃣  其他业务服务"
start_service "Stock" 8014 \
    "cd '$PROJECT_ROOT/📈 Intelligent Stock Trading' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8014"

start_service "Trend" 8015 \
    "cd '$PROJECT_ROOT/🔍 Intelligent Trend Analysis' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8015"

start_service "Content" 8016 \
    "cd '$PROJECT_ROOT/🎨 Intelligent Content Creation' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8016"

start_service "Task" 8017 \
    "cd '$PROJECT_ROOT/🤖 Intelligent Task Agent' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn web.api.main:app --host 0.0.0.0 --port 8017"

start_service "Resource" 8018 \
    "cd '$PROJECT_ROOT/🛠️ Resource Management' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8018"

start_service "Learning" 8019 \
    "cd '$PROJECT_ROOT/🧠 Self Learning System' && source $PROJECT_ROOT/venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8019"

echo ""
echo "================================"
echo -e "${GREEN}✅ 所有服务启动完成！${NC}"
echo "================================"
echo ""
echo "等待服务启动..."
sleep 8

echo ""
echo "📋 服务状态检查:"
echo "================================"

# 检查服务
check_service() {
    local name=$1
    local port=$2
    local url=$3
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name (端口 $port)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name (端口 $port) - 可能正在启动"
        return 1
    fi
}

check_service "OpenWebUI" 3000 "http://localhost:3000"
check_service "RAG系统" 8011 "http://localhost:8011/health"
check_service "ERP前端" 8012 "http://localhost:8012"
check_service "ERP后端" 8013 "http://localhost:8013/health"
check_service "股票交易" 8014 "http://localhost:8014/health"
check_service "趋势分析" 8015 "http://localhost:8015/health"
check_service "内容创作" 8016 "http://localhost:8016/health"
check_service "任务代理" 8017 "http://localhost:8017/health"
check_service "资源管理" 8018 "http://localhost:8018/health"
check_service "自我学习" 8019 "http://localhost:8019/health"

echo ""
echo "📝 查看日志: tail -f $LOG_DIR/<service>.log"
echo "🧪 运行健康检查: python3 scripts/system_health_check.py"
echo ""

