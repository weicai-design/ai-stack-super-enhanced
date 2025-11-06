#!/bin/bash

##############################################################################
# AI Stack 快速启动脚本
# 一键启动所有服务
##############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 AI Stack 快速启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# 检查虚拟环境
echo -e "${YELLOW}📦 检查Python虚拟环境...${NC}"
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，正在创建...${NC}"
    cd "$PROJECT_ROOT"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo -e "${GREEN}✓ 虚拟环境已就绪${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# 创建必要的目录
echo -e "\n${YELLOW}📁 创建必要目录...${NC}"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/backups"
mkdir -p "$PROJECT_ROOT/rag/chroma_db"
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 启动服务函数
start_service() {
    local name=$1
    local port=$2
    local dir=$3
    local module=$4
    
    echo -e "\n${BLUE}🔄 启动 $name (端口:$port)...${NC}"
    
    # 检查端口是否被占用
    if lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用，尝试停止旧进程...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 2
    fi
    
    # 启动服务
    cd "$PROJECT_ROOT/$dir"
    nohup python3 -m uvicorn $module:app --host 0.0.0.0 --port $port >> "$PROJECT_ROOT/logs/${name}.log" 2>&1 &
    
    sleep 2
    
    # 检查是否启动成功
    if lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name 启动成功${NC}"
        return 0
    else
        echo -e "${RED}❌ $name 启动失败，请查看日志${NC}"
        return 1
    fi
}

# 启动所有服务
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 开始启动所有服务...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 核心服务
start_service "AI交互中心" 8020 "ai-chat-center" "chat_server"
start_service "RAG系统" 8011 "rag" "rag_server"
start_service "ERP-API" 8013 "💼 Intelligent ERP & Business Management/api" "business_api"
start_service "股票交易" 8014 "📈 Intelligent Stock Trading" "stock_server"
start_service "趋势分析" 8015 "🔍 Intelligent Trend Analysis" "trend_server"
start_service "内容创作" 8016 "🎨 Intelligent Content Creation" "content_server"
start_service "任务代理" 8017 "🤖 Intelligent Task Agent" "agent_server"
start_service "资源管理" 8018 "⚙️ System Resource Management" "resource_server"
start_service "自我学习" 8019 "🧠 Self Learning System" "learning_server"

# 等待所有服务启动
echo -e "\n${YELLOW}⏳ 等待服务完全启动...${NC}"
sleep 5

# 健康检查
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏥 执行健康检查...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# 检查各个服务
check_service() {
    local name=$1
    local port=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name (端口:$port) - 运行正常${NC}"
        return 0
    else
        echo -e "${RED}❌ $name (端口:$port) - 不可用${NC}"
        return 1
    fi
}

# 执行检查
total=0
success=0

services=(
    "AI交互中心:8020"
    "RAG系统:8011"
    "ERP-API:8013"
    "股票交易:8014"
    "趋势分析:8015"
    "内容创作:8016"
    "任务代理:8017"
    "资源管理:8018"
    "自我学习:8019"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    total=$((total + 1))
    if check_service "$name" "$port"; then
        success=$((success + 1))
    fi
done

# 总结
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 启动总结${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "总服务数: ${total}"
echo -e "${GREEN}成功启动: ${success}${NC}"
echo -e "${RED}启动失败: $((total - success))${NC}"

if [ $success -eq $total ]; then
    echo -e "\n${GREEN}✅ 所有服务启动成功！${NC}"
else
    echo -e "\n${YELLOW}⚠️  部分服务启动失败，请检查日志文件${NC}"
    echo -e "日志目录: $PROJECT_ROOT/logs/"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 AI Stack 已启动！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo "📌 访问地址:"
echo "   • 统一控制台: file://$PROJECT_ROOT/unified-dashboard/index.html"
echo "   • AI交互中心: http://localhost:8020"
echo "   • RAG系统: http://localhost:8011/docs"
echo "   • ERP系统: http://localhost:8012"
echo ""
echo "📋 管理命令:"
echo "   • 查看日志: tail -f $PROJECT_ROOT/logs/*.log"
echo "   • 健康检查: python3 $PROJECT_ROOT/scripts/health_check.py"
echo "   • 停止服务: $PROJECT_ROOT/scripts/stop_all.sh"
echo ""







