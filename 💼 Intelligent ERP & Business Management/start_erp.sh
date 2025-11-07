#!/bin/bash

################################################################################
# AI-Stack ERP 启动脚本（优化版）
# 版本: v2.5.0
# 
# 功能：
# - 环境检查
# - 服务清理
# - 后端启动
# - 健康检查
# - 日志管理
################################################################################

set -e

# 配置
ERP_DIR="$(cd "$(dirname "$0")" && pwd)"
API_PORT=8013
LOG_DIR="$ERP_DIR/logs"
PID_FILE="/tmp/erp-api.pid"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# 打印Logo
print_logo() {
    echo ""
    echo -e "${BOLD}${BLUE}"
    echo "╔════════════════════════════════════════════════════╗"
    echo "║                                                    ║"
    echo "║         AI-Stack ERP System v2.5.0                 ║"
    echo "║         智能企业资源计划系统                        ║"
    echo "║                                                    ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 环境检查
check_environment() {
    log_info "检查运行环境..."
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python版本: $PYTHON_VERSION"
    else
        log_error "Python3未安装，请先安装Python 3.8+"
        exit 1
    fi
    
    # 检查uvicorn
    if python3 -c "import uvicorn" 2>/dev/null; then
        log_success "Uvicorn已安装"
    else
        log_warning "Uvicorn未安装，尝试安装依赖..."
        pip install -r requirements.txt
    fi
    
    # 检查FastAPI
    if python3 -c "import fastapi" 2>/dev/null; then
        log_success "FastAPI已安装"
    else
        log_warning "FastAPI未安装，尝试安装依赖..."
        pip install -r requirements.txt
    fi
    
    # 创建必要目录
    mkdir -p "$LOG_DIR"
    mkdir -p backups
    
    log_success "环境检查完成"
}

# 2. 清理旧服务
clean_old_service() {
    log_info "清理旧服务..."
    
    # 清理端口占用
    if lsof -ti :$API_PORT > /dev/null 2>&1; then
        log_warning "端口$API_PORT被占用，正在清理..."
        lsof -ti :$API_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
        log_success "端口已清理"
    else
        log_success "端口$API_PORT空闲"
    fi
    
    # 清理PID文件
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log_warning "发现旧进程(PID: $OLD_PID)，正在终止..."
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

# 3. 启动后端服务
start_backend() {
    log_info "启动ERP API服务..."
    
    cd "$ERP_DIR"
    
    # 启动uvicorn
    nohup python3 -m uvicorn api.main:app \
        --host 0.0.0.0 \
        --port $API_PORT \
        --log-level info \
        > "$LOG_DIR/erp-api.log" 2>&1 &
    
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$PID_FILE"
    
    log_success "后端服务已启动 (PID: $BACKEND_PID)"
    log_info "等待服务就绪..."
    sleep 3
}

# 4. 健康检查
health_check() {
    log_info "执行健康检查..."
    
    MAX_RETRIES=10
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s -f "http://localhost:$API_PORT/health" > /dev/null 2>&1; then
            log_success "服务健康检查通过！"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -n "."
        sleep 1
    done
    
    log_error "服务启动失败，请查看日志: $LOG_DIR/erp-api.log"
    return 1
}

# 5. 显示服务信息
show_info() {
    # 获取系统信息
    API_INFO=$(curl -s "http://localhost:$API_PORT/api/info" 2>/dev/null)
    
    echo ""
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ ERP系统启动成功！${NC}"
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}📊 系统信息:${NC}"
    echo "   版本: v2.5.0"
    echo "   完成度: 97%"
    echo "   模块数: 16个"
    echo "   高级功能: 39个"
    echo "   API端点: 120+"
    echo ""
    echo -e "${BOLD}🌐 访问地址:${NC}"
    echo "   API服务:    http://localhost:$API_PORT"
    echo "   API文档:    http://localhost:$API_PORT/docs"
    echo "   健康检查:   http://localhost:$API_PORT/health"
    echo "   系统信息:   http://localhost:$API_PORT/api/info"
    echo ""
    echo -e "${BOLD}📋 控制台:${NC}"
    echo "   ERP主控台:  http://localhost:8000/erp-dashboard.html"
    echo "   高级分析:   http://localhost:8000/advanced-analytics.html"
    echo "   (需单独启动: cd ../unified-dashboard && python3 server.py)"
    echo ""
    echo -e "${BOLD}📝 日志文件:${NC}"
    echo "   API日志:    $LOG_DIR/erp-api.log"
    echo "   查看日志:   tail -f $LOG_DIR/erp-api.log"
    echo ""
    echo -e "${BOLD}🛑 停止服务:${NC}"
    echo "   方式1: ./stop_erp.sh"
    echo "   方式2: kill \$(cat $PID_FILE)"
    echo "   方式3: lsof -ti :$API_PORT | xargs kill"
    echo ""
    echo -e "${BOLD}🔧 实用工具:${NC}"
    echo "   性能测试:   python3 '🔧 性能优化工具.py'"
    echo "   功能测试:   python3 '🧪 综合功能测试.py'"
    echo "   系统监控:   ./📊\ 系统监控脚本.sh"
    echo "   自动备份:   ./🔄\ 自动备份脚本.sh"
    echo ""
    echo -e "${BOLD}════════════════════════════════════════════════════${NC}"
    echo ""
}

# 6. 打开浏览器（可选）
open_browser() {
    if [ "$1" = "--no-browser" ]; then
        log_info "跳过打开浏览器"
        return
    fi
    
    log_info "正在打开API文档..."
    sleep 1
    
    # 检测操作系统
    if command -v open &> /dev/null; then
        # macOS
        open "http://localhost:$API_PORT/docs"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "http://localhost:$API_PORT/docs"
    elif command -v start &> /dev/null; then
        # Windows
        start "http://localhost:$API_PORT/docs"
    else
        log_info "请手动打开浏览器访问: http://localhost:$API_PORT/docs"
    fi
}

# 主函数
main() {
    # 解析参数
    NO_BROWSER=false
    SKIP_CHECK=false
    
    for arg in "$@"; do
        case $arg in
            --no-browser)
                NO_BROWSER=true
                ;;
            --skip-check)
                SKIP_CHECK=true
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --no-browser    不自动打开浏览器"
                echo "  --skip-check    跳过环境检查"
                echo "  --help, -h      显示帮助信息"
                exit 0
                ;;
        esac
    done
    
    # 显示Logo
    print_logo
    
    # 执行启动流程
    if [ "$SKIP_CHECK" = false ]; then
        check_environment
    fi
    
    clean_old_service
    start_backend
    
    if health_check; then
        show_info
        
        if [ "$NO_BROWSER" = false ]; then
            open_browser
        fi
        
        echo -e "${GREEN}✨ 享受使用AI-Stack ERP系统吧！${NC}"
        echo ""
        
        exit 0
    else
        log_error "启动失败，请检查日志"
        exit 1
    fi
}

# 执行主函数
main "$@"
