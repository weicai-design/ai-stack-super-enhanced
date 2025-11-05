#!/bin/bash

# AI Stack Super Enhanced - 统一测试脚本
# 测试所有系统是否正常运行

echo "🧪 开始测试所有系统..."
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_service() {
    local name=$1
    local url=$2
    local port=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "测试 $name (端口 $port)... "
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local name=$1
    local url=$2
    local max_wait=30
    local wait_time=0
    
    echo -n "等待 $name 启动"
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        wait_time=$((wait_time + 2))
    done
    
    echo -e " ${RED}✗ 超时${NC}"
    return 1
}

echo ""
echo "1️⃣  测试核心服务"
echo "--------------------------------"

# 测试 OpenWebUI
test_service "OpenWebUI" "http://localhost:3000" "3000"

# 测试 RAG API
test_service "RAG API" "http://localhost:8011/health" "8011"

# 测试 ERP 后端
test_service "ERP 后端" "http://localhost:8013/health" "8013"

# 测试 ERP 前端
test_service "ERP 前端" "http://localhost:8012" "8012"

echo ""
echo "2️⃣  测试业务服务"
echo "--------------------------------"

# 测试股票服务
test_service "股票交易" "http://localhost:8014/health" "8014"

# 测试趋势分析
test_service "趋势分析" "http://localhost:8015/health" "8015"

# 测试内容创作
test_service "内容创作" "http://localhost:8016/health" "8016"

echo ""
echo "3️⃣  测试管理服务"
echo "--------------------------------"

# 测试任务代理
test_service "任务代理" "http://localhost:8017/health" "8017"

# 测试资源管理
test_service "资源管理" "http://localhost:8018/health" "8018"

# 测试自我学习
test_service "自我学习" "http://localhost:8019/health" "8019"

echo ""
echo "================================"
echo "📊 测试结果汇总"
echo "================================"
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"

# 计算成功率
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "成功率: ${SUCCESS_RATE}%"
    
    if [ $SUCCESS_RATE -eq 100 ]; then
        echo -e "${GREEN}✅ 所有系统运行正常！${NC}"
        exit 0
    elif [ $SUCCESS_RATE -ge 70 ]; then
        echo -e "${YELLOW}⚠️  部分系统需要启动${NC}"
        exit 1
    else
        echo -e "${RED}❌ 多个系统未运行${NC}"
        exit 2
    fi
else
    echo -e "${RED}❌ 没有执行任何测试${NC}"
    exit 3
fi

