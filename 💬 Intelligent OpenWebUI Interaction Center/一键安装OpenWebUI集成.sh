#!/bin/bash

# OpenWebUI统一集成 - 一键安装脚本
# 将所有系统集成到OpenWebUI聊天界面

echo "🚀 开始安装OpenWebUI统一集成..."
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# OpenWebUI Functions目录
FUNCTIONS_DIR="$HOME/.openwebui/functions"

# 创建Functions目录
echo -e "${BLUE}1. 创建Functions目录...${NC}"
mkdir -p "$FUNCTIONS_DIR"
echo -e "${GREEN}✓ 目录已创建: $FUNCTIONS_DIR${NC}"

# 复制统一工具集
echo ""
echo -e "${BLUE}2. 复制AI Stack统一工具集...${NC}"
cp "openwebui_functions/all_systems_tools.py" "$FUNCTIONS_DIR/"
echo -e "${GREEN}✓ all_systems_tools.py 已复制${NC}"

# 复制RAG专用工具
echo ""
echo -e "${BLUE}3. 复制RAG专用工具...${NC}"
cp "openwebui_functions/rag_tools.py" "$FUNCTIONS_DIR/"
echo -e "${GREEN}✓ rag_tools.py 已复制${NC}"

# 检查OpenWebUI是否运行
echo ""
echo -e "${BLUE}4. 检查OpenWebUI状态...${NC}"
if curl -s --max-time 2 http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OpenWebUI 正在运行${NC}"
else
    echo -e "${YELLOW}⚠ OpenWebUI 未运行，正在启动...${NC}"
    
    # 尝试启动OpenWebUI
    if docker ps -a | grep -q open-webui; then
        docker start open-webui
    else
        docker run -d -p 3000:8080 \
          --add-host=host.docker.internal:host-gateway \
          -v open-webui:/app/backend/data \
          --name open-webui \
          --restart always \
          ghcr.io/open-webui/open-webui:main
    fi
    
    echo "等待OpenWebUI启动..."
    sleep 10
fi

# 重启OpenWebUI以加载新Functions
echo ""
echo -e "${BLUE}5. 重启OpenWebUI以加载Functions...${NC}"
docker restart open-webui
echo "等待重启完成..."
sleep 5

echo ""
echo "================================"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo "================================"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 访问OpenWebUI:"
echo "   open http://localhost:3000"
echo ""
echo "2. 登录后，进入 Admin Panel"
echo "   点击右上角头像 → Admin Panel"
echo ""
echo "3. 启用Functions:"
echo "   Admin Panel → Functions → 找到以下两个："
echo "   - AI Stack Tools (26个系统工具)"
echo "   - RAG Tools (7个RAG工具)"
echo "   点击启用开关 ✅"
echo ""
echo "4. 配置API地址（如需要）:"
echo "   点击Functions的配置按钮⚙️"
echo "   确认API地址为: http://host.docker.internal:80XX"
echo ""
echo "5. 开始使用:"
echo "   在聊天框中输入："
echo "   - \"查看所有系统状态\""
echo "   - \"查看本月财务情况\""
echo "   - \"帮助\""
echo ""
echo "🎉 享受统一的AI Stack体验！"
echo ""


