#!/bin/bash

# AI Stack Super Enhanced - 统一启动脚本
# 按照正确顺序启动所有服务

echo "🚀 开始启动 AI Stack 所有服务..."
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 启动函数
start_service() {
    local name=$1
    local command=$2
    local log_file="$LOG_DIR/${name}.log"
    
    echo -e "${BLUE}➤ 启动 $name...${NC}"
    
    # 在后台执行命令
    eval "$command" > "$log_file" 2>&1 &
    
    echo "  PID: $!"
    echo "  日志: $log_file"
}

echo ""
echo "1️⃣  启动基础服务"
echo "--------------------------------"

# 检查 Docker
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker 已运行${NC}"
else
    echo -e "${YELLOW}⚠ 正在启动 Docker...${NC}"
    open -a Docker
    sleep 15
fi

# 检查 Ollama
if ollama list > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama 已运行${NC}"
else
    echo -e "${YELLOW}⚠ 正在启动 Ollama...${NC}"
    ollama serve &
    sleep 5
fi

echo ""
echo "2️⃣  启动核心服务"
echo "--------------------------------"

# 启动 RAG 服务
start_service "RAG" \
    "cd '$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph' && python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8011"

sleep 3

# 启动 ERP 后端
start_service "ERP-Backend" \
    "cd '$PROJECT_ROOT/💼 Intelligent ERP & Business Management' && source venv/bin/activate && python -m uvicorn api.main:app --host 0.0.0.0 --port 8013"

sleep 3

# 启动 ERP 前端
start_service "ERP-Frontend" \
    "cd '$PROJECT_ROOT/💼 Intelligent ERP & Business Management/web/frontend' && npm run dev"

sleep 5

echo ""
echo "3️⃣  启动业务服务"
echo "--------------------------------"

# 启动股票服务
start_service "Stock" \
    "cd '$PROJECT_ROOT/📈 Intelligent Stock Trading' && python -m uvicorn api.main:app --host 0.0.0.0 --port 8014"

sleep 2

# 启动趋势分析
start_service "Trend" \
    "cd '$PROJECT_ROOT/🔍 Intelligent Trend Analysis' && python -m uvicorn api.main:app --host 0.0.0.0 --port 8015"

sleep 2

# 启动内容创作
start_service "Content" \
    "cd '$PROJECT_ROOT/🎨 Intelligent Content Creation' && python -m uvicorn api.main:app --host 0.0.0.0 --port 8016"

sleep 2

echo ""
echo "4️⃣  启动管理服务"
echo "--------------------------------"

# 启动任务代理
start_service "Task-Agent" \
    "cd '$PROJECT_ROOT/🤖 Intelligent Task Agent' && python -m uvicorn web.api.main:app --host 0.0.0.0 --port 8017"

sleep 2

# 启动资源管理
start_service "Resource-Manager" \
    "cd '$PROJECT_ROOT/🛠️ Resource Management' && python -m uvicorn api.main:app --host 0.0.0.0 --port 8018"

sleep 2

# 启动自我学习
start_service "Self-Learning" \
    "cd '$PROJECT_ROOT/🧠 Self Learning System' && python -m uvicorn api.main:app --host 0.0.0.0 --port 8019"

sleep 2

echo ""
echo "================================"
echo "✅ 所有服务已启动！"
echo "================================"
echo ""
echo "📋 服务列表："
echo "  - OpenWebUI:    http://localhost:3000"
echo "  - RAG API:      http://localhost:8011"
echo "  - ERP 前端:     http://localhost:8012"
echo "  - ERP 后端:     http://localhost:8013"
echo "  - 股票服务:     http://localhost:8014"
echo "  - 趋势分析:     http://localhost:8015"
echo "  - 内容创作:     http://localhost:8016"
echo "  - 任务代理:     http://localhost:8017"
echo "  - 资源管理:     http://localhost:8018"
echo "  - 自我学习:     http://localhost:8019"
echo ""
echo "📝 日志目录: $LOG_DIR"
echo ""
echo "💡 提示:"
echo "  - 运行 './test_all_systems.sh' 测试所有服务"
echo "  - 运行 './stop_all_services.sh' 停止所有服务"
echo "  - 查看日志: tail -f $LOG_DIR/<service>.log"
echo ""

