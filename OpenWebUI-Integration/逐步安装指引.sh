#!/bin/bash

# OpenWebUI Functions 逐步安装引导脚本

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

FUNCTIONS_DIR="/Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/openwebui-functions"

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🚀 OpenWebUI Functions 逐步安装引导${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Functions列表
declare -a FUNCTIONS=(
    "rag_integration.py:RAG Knowledge Integration:http://host.docker.internal:8011"
    "erp_query.py:ERP Business Query:http://host.docker.internal:8013"
    "stock_analysis.py:Stock Trading & Analysis:http://host.docker.internal:8014"
    "unified_aistack.py:AI Stack Unified Interface:auto"
    "content_creation.py:Content Creation:http://host.docker.internal:8016"
    "system_monitor.py:System Monitor:auto"
    "terminal_exec.py:Terminal Executor:manual"
)

total=${#FUNCTIONS[@]}
current=1

for func_info in "${FUNCTIONS[@]}"; do
    IFS=':' read -r filename title endpoint <<< "$func_info"
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Function ${current}/${total}: ${title}${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 复制到剪贴板
    cat "$FUNCTIONS_DIR/$filename" | pbcopy
    echo -e "${GREEN}✅ 已复制到剪贴板: ${filename}${NC}"
    echo ""
    
    echo -e "${CYAN}📋 在OpenWebUI中操作：${NC}"
    echo "  1. 点击 '+' 或 'Create Function'"
    echo "  2. 粘贴代码 (Command+V)"
    echo "  3. 点击 'Save'"
    
    # 显示配置说明
    if [ "$endpoint" != "auto" ] && [ "$endpoint" != "manual" ]; then
        echo ""
        echo -e "${CYAN}⚙️  配置 (点击⚙️图标)：${NC}"
        if [ "$filename" == "rag_integration.py" ]; then
            echo "  rag_api_endpoint: $endpoint"
            echo "  search_top_k: 5"
            echo "  enable_kg_query: true"
        elif [ "$filename" == "erp_query.py" ]; then
            echo "  erp_api_endpoint: $endpoint"
            echo "  enable_write: false"
        elif [ "$filename" == "stock_analysis.py" ]; then
            echo "  stock_api_endpoint: $endpoint"
            echo "  enable_trading: false"
            echo "  max_trade_amount: 10000.0"
        elif [ "$filename" == "content_creation.py" ]; then
            echo "  content_api_endpoint: $endpoint"
            echo "  enable_auto_publish: false"
        fi
    elif [ "$endpoint" == "manual" ]; then
        echo ""
        echo -e "${CYAN}⚙️  配置：${NC}"
        echo "  enable_terminal: false  # ⚠️ 测试后再启用"
        echo "  working_directory: /Users/ywc/ai-stack-super-enhanced"
    fi
    
    echo ""
    echo -e "${CYAN}🔘 确保Function已启用${NC}"
    echo "  开关应该是绿色的"
    echo ""
    
    if [ $current -lt $total ]; then
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        read -p "完成后按Enter继续下一个... "
        echo ""
    fi
    
    ((current++))
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   🎉 所有Functions准备完毕！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}🧪 测试集成功能：${NC}"
echo ""
echo "在OpenWebUI聊天框输入："
echo "  ${BLUE}/aistack status${NC}     - 查看所有系统"
echo "  ${BLUE}/rag search AI${NC}      - RAG搜索"
echo "  ${BLUE}/erp financial${NC}      - ERP财务"
echo "  ${BLUE}/stock price 600519${NC} - 股票价格"
echo ""
echo "或直接提问（智能路由）："
echo "  ${BLUE}什么是机器学习？${NC}   → 自动RAG搜索"
echo "  ${BLUE}今天的财务数据${NC}     → 自动ERP查询"
echo ""
echo -e "${GREEN}✅ 安装完成后，OpenWebUI将深度集成所有AI Stack功能！${NC}"
echo ""



