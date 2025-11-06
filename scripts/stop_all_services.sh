#!/bin/bash

# AI Stack 停止所有服务脚本
# 版本: v3.0

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ⏹️  AI Stack 停止所有服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# 服务端口列表
PORTS=(8020 8011 8013 8014 8015 8016 8017 8018 8019)

STOPPED_COUNT=0

echo -e "${YELLOW}正在停止服务...${NC}"
echo ""

for port in "${PORTS[@]}"; do
    # 查找端口上的进程
    PID=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$PID" ]; then
        # 获取进程名
        PROCESS_NAME=$(ps -p $PID -o comm= 2>/dev/null)
        
        echo -e "${BLUE}➤${NC} 停止端口 $port 上的服务 (PID: $PID, 进程: $PROCESS_NAME)"
        
        # 尝试优雅关闭
        kill -15 $PID 2>/dev/null
        
        # 等待2秒
        sleep 2
        
        # 检查是否还在运行
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}  • 优雅关闭失败，强制终止...${NC}"
            kill -9 $PID 2>/dev/null
        fi
        
        # 验证是否关闭
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ 服务已停止${NC}"
            STOPPED_COUNT=$((STOPPED_COUNT + 1))
        else
            echo -e "${RED}  ✗ 停止失败${NC}"
        fi
    else
        echo -e "${BLUE}➤${NC} 端口 $port: ${YELLOW}无服务运行${NC}"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ 成功停止 $STOPPED_COUNT 个服务${NC}"
else
    echo -e "${YELLOW}⚠️  没有发现运行中的服务${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
