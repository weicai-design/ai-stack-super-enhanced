#!/bin/bash

# 一键准备所有OpenWebUI Functions
# 会逐个复制Functions到剪贴板，并打开安装页面

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FUNCTIONS_DIR="/Users/ywc/ai-stack-super-enhanced/OpenWebUI-Integration/openwebui-functions"

echo -e "${CYAN}"
echo "═══════════════════════════════════════════════════════════"
echo "   🚀 一键准备OpenWebUI Functions安装"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

# 打开Functions页面
echo -e "${BLUE}📂 打开OpenWebUI Functions管理页面...${NC}"
open "http://localhost:3000/workspace/functions"
sleep 2

echo ""
echo -e "${GREEN}✅ 已在浏览器打开：http://localhost:3000/workspace/functions${NC}"
echo ""

# Functions列表
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 1/7: RAG Knowledge Integration${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/rag_integration.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}在OpenWebUI中操作：${NC}"
echo "  1. 点击 '+' 创建Function"
echo "  2. 粘贴代码 (Command+V)"
echo "  3. 点击 'Save'"
echo "  4. 点击 ⚙️ 配置："
echo "     ${BLUE}rag_api_endpoint: http://host.docker.internal:8011${NC}"
echo "     ${BLUE}search_top_k: 5${NC}"
echo "     ${BLUE}enable_kg_query: true${NC}"
echo "  5. 保存并启用Function"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 2/7: ERP Business Query${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/erp_query.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}erp_api_endpoint: http://host.docker.internal:8013${NC}"
echo "  ${BLUE}enable_write: false${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 3/7: Stock Trading & Analysis${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/stock_analysis.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}stock_api_endpoint: http://host.docker.internal:8014${NC}"
echo "  ${BLUE}enable_trading: false${NC}  ${RED}# ⚠️ 谨慎开启${NC}"
echo "  ${BLUE}max_trade_amount: 10000.0${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 4/7: AI Stack Unified Interface${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/unified_aistack.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}auto_routing: true${NC}  ${GREEN}# 启用智能路由${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 5/7: Content Creation & Publishing${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/content_creation.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}content_api_endpoint: http://host.docker.internal:8016${NC}"
echo "  ${BLUE}enable_auto_publish: false${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 6/7: System Monitor${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/system_monitor.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：默认即可${NC}"
echo ""
read -p "完成后按Enter继续... "

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📦 Function 7/7: Terminal Command Executor${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$FUNCTIONS_DIR/terminal_exec.py" | pbcopy
echo -e "${GREEN}✅ 已复制到剪贴板${NC}"
echo ""
echo -e "${CYAN}配置：${NC}"
echo "  ${BLUE}enable_terminal: false${NC}  ${RED}# ⚠️ 谨慎开启${NC}"
echo "  ${BLUE}working_directory: /Users/ywc/ai-stack-super-enhanced${NC}"
echo ""
read -p "完成后按Enter... "

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   🎊 所有Functions已准备完毕！${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}🧪 测试命令：${NC}"
echo ""
echo "在OpenWebUI聊天框输入以下命令测试："
echo ""
echo -e "  ${BLUE}/aistack status${NC}        - 查看所有系统状态"
echo -e "  ${BLUE}/rag search AI技术${NC}     - 搜索知识库"
echo -e "  ${BLUE}/erp financial${NC}         - 查询财务数据"
echo -e "  ${BLUE}/stock price 600519${NC}    - 查询贵州茅台"
echo -e "  ${BLUE}/system status${NC}         - 系统监控"
echo ""
echo "或直接提问（智能路由）："
echo ""
echo -e "  ${BLUE}什么是深度学习？${NC}      → 自动RAG搜索"
echo -e "  ${BLUE}今天的订单情况${NC}        → 自动ERP查询"
echo -e "  ${BLUE}贵州茅台多少钱${NC}        → 自动股票查询"
echo ""
echo -e "${GREEN}🎉 集成成功后，你就可以通过OpenWebUI统一管理所有AI Stack功能！${NC}"
echo ""



