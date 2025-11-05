#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🚀 OpenWebUI Functions 安装引导${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}已打开Functions管理页面...${NC}"
open "http://localhost:3000/workspace/functions"
sleep 3

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 1/7: RAG Knowledge Integration${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/rag_integration.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
echo -e "${CYAN}操作步骤：${NC}"
echo "  1. 在OpenWebUI点击 '+' 或 'Create Function'"
echo "  2. 粘贴代码 (Command+V)"
echo "  3. 点击 'Save'"
echo "  4. 点击⚙️配置："
echo "     ${BLUE}rag_api_endpoint: http://host.docker.internal:8011${NC}"
echo "  5. 启用Function（开关变绿）"
echo ""
read -p "完成后按Enter继续下一个... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 2/7: ERP Business Query${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/erp_query.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}erp_api_endpoint: http://host.docker.internal:8013${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 3/7: Stock Trading & Analysis${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/stock_analysis.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}stock_api_endpoint: http://host.docker.internal:8014${NC}"
echo "  ${BLUE}enable_trading: false${NC} ${RED}# 谨慎！${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 4/7: Unified AI Stack${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/unified_aistack.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}auto_routing: true${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 5/7: Content Creation${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/content_creation.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 6/7: System Monitor${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/system_monitor.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Function 7/7: Terminal Executor${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat openwebui-functions/terminal_exec.py | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板！${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}enable_terminal: false${NC} ${RED}# 谨慎！${NC}"
echo ""
read -p "完成后按Enter... "

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   🎉 所有7个Functions已准备完毕！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}🧪 测试集成：${NC}"
echo ""
echo "在OpenWebUI聊天框输入："
echo "  ${BLUE}/aistack status${NC}         - 系统状态"
echo "  ${BLUE}/rag search AI${NC}          - RAG搜索"
echo "  ${BLUE}/erp financial${NC}          - ERP财务"
echo "  ${BLUE}/stock price 600519${NC}     - 股票"
echo ""
echo "或直接提问："
echo "  ${BLUE}什么是深度学习？${NC}"
echo "  ${BLUE}今天的财务数据${NC}"
echo ""
echo -e "${GREEN}🎊 OpenWebUI已深度集成所有AI Stack功能！${NC}"
echo ""
