#!/bin/bash

echo "🚀 启动AI Stack核心服务..."
echo ""

# 项目根目录
PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 启动函数
start_service() {
    local name=$1
    local port=$2
    local dir=$3
    local command=$4
    
    echo -e "${BLUE}➤ 启动 $name (端口 $port)...${NC}"
    
    # 检查端口是否被占用
    if lsof -i:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}  ⚠ 端口 $port 已被占用，跳过${NC}"
        return
    fi
    
    # 切换到服务目录
    cd "$dir"
    
    # 在后台执行命令
    nohup bash -c "$command" > "$LOG_DIR/${name}.log" 2>&1 &
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
    "python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8011"

echo "2️⃣  启动资源管理系统"
echo "--------------------------------"
start_service "Resource" 8018 \
    "$PROJECT_ROOT/🛠️ Resource Management" \
    "python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8018"

echo "3️⃣  启动任务代理系统"
echo "--------------------------------"
start_service "Task" 8017 \
    "$PROJECT_ROOT/🤖 Intelligent Task Agent" \
    "python3 -m uvicorn web.api.main:app --host 0.0.0.0 --port 8017"

echo "4️⃣  启动自我学习系统"
echo "--------------------------------"
start_service "Learning" 8019 \
    "$PROJECT_ROOT/🧠 Self Learning System" \
    "python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8019"

echo "================================"
echo -e "${GREEN}✅ 核心服务启动完成！${NC}"
echo "================================"
echo ""
echo "📋 已启动的服务："
echo "  - RAG系统:    http://localhost:8011"
echo "  - 资源管理:   http://localhost:8018"
echo "  - 任务代理:   http://localhost:8017"
echo "  - 自我学习:   http://localhost:8019"
echo "  - ERP后端:    http://localhost:8013"
echo "  - ERP前端:    http://localhost:8012"
echo "  - OpenWebUI:  http://localhost:3000"
echo ""
echo "📝 查看所有日志:"
echo "  ls -lh $LOG_DIR/"
echo ""
echo "🧪 运行健康检查:"
echo "  python3 scripts/system_health_check.py"
echo ""


