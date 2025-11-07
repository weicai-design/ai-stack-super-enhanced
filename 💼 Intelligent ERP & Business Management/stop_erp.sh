#!/bin/bash

################################################################################
# AI-Stack ERP 停止脚本
# 
# 功能：
# - 优雅停止服务
# - 清理资源
# - 保存日志
################################################################################

# 配置
API_PORT=8013
PID_FILE="/tmp/erp-api.pid"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "ℹ️  $1"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo "🛑 停止ERP系统..."
echo ""

# 方式1: 从PID文件停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log_info "终止进程 (PID: $PID)..."
        kill -15 "$PID" 2>/dev/null || true
        sleep 2
        
        # 检查是否还在运行
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "进程未响应，强制终止..."
            kill -9 "$PID" 2>/dev/null || true
        fi
        
        log_success "进程已终止"
    else
        log_warning "PID文件存在但进程不存在"
    fi
    
    rm -f "$PID_FILE"
else
    log_info "PID文件不存在，尝试通过端口查找..."
fi

# 方式2: 通过端口停止
if lsof -ti :$API_PORT > /dev/null 2>&1; then
    log_info "清理端口${API_PORT}上的进程..."
    lsof -ti :$API_PORT | xargs kill -15 2>/dev/null || true
    sleep 2
    
    # 强制清理
    if lsof -ti :$API_PORT > /dev/null 2>&1; then
        lsof -ti :$API_PORT | xargs kill -9 2>/dev/null || true
    fi
    
    log_success "端口已清理"
fi

# 验证
if lsof -ti :$API_PORT > /dev/null 2>&1; then
    log_warning "端口仍被占用，请手动检查"
else
    log_success "ERP系统已完全停止"
fi

echo ""
