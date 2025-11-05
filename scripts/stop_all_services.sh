#!/bin/bash

# AI Stack Super Enhanced - 统一停止脚本
# 停止所有运行的服务

echo "🛑 开始停止所有服务..."
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 停止端口上的进程
stop_port() {
    local port=$1
    local name=$2
    
    echo -n "停止 $name (端口 $port)... "
    
    # 查找占用端口的进程
    local pid=$(lsof -ti:$port)
    
    if [ -n "$pid" ]; then
        kill -9 $pid 2>/dev/null
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo "未运行"
        return 1
    fi
}

# 停止所有服务
stop_port 3000 "OpenWebUI"
stop_port 8011 "RAG API"
stop_port 8012 "ERP 前端"
stop_port 8013 "ERP 后端"
stop_port 8014 "股票服务"
stop_port 8015 "趋势分析"
stop_port 8016 "内容创作"
stop_port 8017 "任务代理"
stop_port 8018 "资源管理"
stop_port 8019 "自我学习"

echo ""
echo "================================"
echo "✅ 所有服务已停止！"
echo "================================"

