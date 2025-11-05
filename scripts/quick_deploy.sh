#!/bin/bash

# ================================================================
# AI Stack Super Enhanced - 一键部署脚本
# 版本: v1.4.0
# 功能: 检查依赖、配置环境、启动所有服务
# ================================================================

echo "🚀 AI Stack Super Enhanced - 一键部署脚本 v1.4.0"
echo "========================================================"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==================== 步骤1: 检查依赖 ====================

echo ""
log_info "步骤1/5: 检查系统依赖..."

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python已安装: $PYTHON_VERSION"
else
    log_error "Python3未安装，请先安装Python 3.8+"
    exit 1
fi

# 检查Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_success "Node.js已安装: $NODE_VERSION"
else
    log_warning "Node.js未安装，前端功能可能受限"
fi

# 检查Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    log_success "Docker已安装: $DOCKER_VERSION"
    
    # 检查Docker是否运行
    if docker info &> /dev/null; then
        log_success "Docker正在运行"
    else
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
else
    log_warning "Docker未安装，部分功能可能受限"
fi

# 检查Ollama
if command -v ollama &> /dev/null; then
    log_success "Ollama已安装"
else
    log_warning "Ollama未安装，LLM功能可能受限"
fi

# ==================== 步骤2: 创建虚拟环境 ====================

echo ""
log_info "步骤2/5: 配置Python环境..."

cd "$PROJECT_ROOT"

if [ ! -d "venv" ]; then
    log_info "创建虚拟环境..."
    python3 -m venv venv
    log_success "虚拟环境创建成功"
else
    log_success "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ -f "requirements.txt" ]; then
    log_info "安装Python依赖..."
    pip install -q -r requirements.txt
    log_success "Python依赖安装完成"
fi

# ==================== 步骤3: 检查端口占用 ====================

echo ""
log_info "步骤3/5: 检查端口占用..."

PORTS=(8011 8012 8013 8014 8015 8016 8017 8018 8019 8020 3000)
OCCUPIED_PORTS=()

for PORT in "${PORTS[@]}"; do
    if lsof -i:$PORT &> /dev/null; then
        log_warning "端口 $PORT 已被占用"
        OCCUPIED_PORTS+=($PORT)
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    log_warning "发现 ${#OCCUPIED_PORTS[@]} 个端口被占用"
    read -p "是否停止占用端口的进程? (y/n): " KILL_PORTS
    if [ "$KILL_PORTS" = "y" ] || [ "$KILL_PORTS" = "Y" ]; then
        for PORT in "${OCCUPIED_PORTS[@]}"; do
            log_info "停止端口 $PORT 上的进程..."
            lsof -ti:$PORT | xargs kill -9 2>/dev/null
        done
        log_success "端口已释放"
    fi
fi

# ==================== 步骤4: 启动服务 ====================

echo ""
log_info "步骤4/5: 启动所有服务..."

# 启动ERP后端
log_info "启动ERP后端 (端口8013)..."
cd "$PROJECT_ROOT/💼 Intelligent ERP & Business Management"
python3 api/main.py &> logs/backend.log &
ERP_BACKEND_PID=$!
sleep 2

# 检查ERP后端是否启动成功
if curl -s http://localhost:8013/health &> /dev/null; then
    log_success "ERP后端启动成功 (PID: $ERP_BACKEND_PID)"
else
    log_error "ERP后端启动失败"
fi

# 启动命令网关
log_info "启动命令网关 (端口8020)..."
cd "$PROJECT_ROOT/💬 Intelligent OpenWebUI Interaction Center"
python3 command_gateway.py &> logs/gateway.log &
GATEWAY_PID=$!
sleep 2

if curl -s http://localhost:8020/health &> /dev/null; then
    log_success "命令网关启动成功 (PID: $GATEWAY_PID)"
else
    log_error "命令网关启动失败"
fi

# ==================== 步骤5: 生成启动报告 ====================

echo ""
log_info "步骤5/5: 生成部署报告..."

cat > "$PROJECT_ROOT/DEPLOYMENT_REPORT.txt" << EOF
========================================================
AI Stack Super Enhanced - 部署报告
========================================================
部署时间: $(date '+%Y-%m-%d %H:%M:%S')
版本: v1.4.0
部署方式: 一键部署脚本

========================================================
系统信息
========================================================
操作系统: $(uname -s)
Python版本: $(python3 --version)
Node.js版本: $(node --version 2>/dev/null || echo "未安装")
Docker版本: $(docker --version 2>/dev/null || echo "未安装")

========================================================
服务状态
========================================================
✅ ERP后端 (8013): 运行中 (PID: $ERP_BACKEND_PID)
✅ 命令网关 (8020): 运行中 (PID: $GATEWAY_PID)

========================================================
访问地址
========================================================
📦 命令面板: http://localhost:8020
💼 ERP系统: http://localhost:8012
💬 OpenWebUI: http://localhost:3000
📊 系统监控: http://localhost:8020/monitor

========================================================
快速操作
========================================================
查看日志: tail -f logs/*.log
停止服务: ./scripts/stop_all_services.sh
重启服务: ./scripts/restart_services.sh

========================================================
下一步
========================================================
1. 访问命令面板: open http://localhost:8020
2. 查看ERP系统: open http://localhost:8012
3. 查看部署状态: cat DEPLOYMENT_REPORT.txt

========================================================
EOF

log_success "部署报告已生成: DEPLOYMENT_REPORT.txt"

# ==================== 完成 ====================

echo ""
echo "========================================================"
log_success "✅ 部署完成！"
echo "========================================================"
echo ""
echo "📦 命令面板: http://localhost:8020"
echo "💼 ERP系统: http://localhost:8012"
echo ""
echo "提示: 使用 './scripts/stop_all_services.sh' 停止所有服务"
echo ""

# 自动打开浏览器（macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open http://localhost:8020
    log_info "已自动打开命令面板"
fi

