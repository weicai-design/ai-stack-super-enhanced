#!/bin/bash

echo "📦 安装AI Stack所有服务的依赖..."
echo ""

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 安装全局虚拟环境依赖
echo -e "${BLUE}1️⃣  创建全局虚拟环境...${NC}"
cd "$PROJECT_ROOT"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
else
    echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装核心依赖
echo -e "${BLUE}2️⃣  安装核心Python依赖...${NC}"
pip install -q --upgrade pip
pip install -q fastapi uvicorn[standard] pydantic sqlalchemy requests psutil aiofiles python-multipart

echo -e "${GREEN}✓ 核心依赖安装完成${NC}"
echo ""

# 安装RAG系统依赖
echo -e "${BLUE}3️⃣  安装RAG系统依赖...${NC}"
cd "$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph"
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt 2>/dev/null || echo -e "${YELLOW}⚠ 部分依赖可能未成功安装${NC}"
fi
echo -e "${GREEN}✓ RAG依赖处理完成${NC}"
echo ""

# 安装ERP依赖（使用独立venv）
echo -e "${BLUE}4️⃣  检查ERP系统虚拟环境...${NC}"
cd "$PROJECT_ROOT/💼 Intelligent ERP & Business Management"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ ERP虚拟环境已存在${NC}"
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q fastapi uvicorn sqlalchemy pydantic python-multipart
    echo -e "${GREEN}✓ ERP依赖安装完成${NC}"
fi
echo ""

# 显示完成信息
echo "================================"
echo -e "${GREEN}✅ 依赖安装完成！${NC}"
echo "================================"
echo ""
echo "📋 已安装的核心依赖："
echo "  - FastAPI (Web框架)"
echo "  - Uvicorn (ASGI服务器)"
echo "  - SQLAlchemy (ORM)"
echo "  - Pydantic (数据验证)"
echo "  - Requests (HTTP客户端)"
echo "  - Psutil (系统监控)"
echo ""
echo "💡 下一步："
echo "  运行: ./scripts/start_core_services.sh"
echo ""


