#!/bin/bash

echo "🔧 为RAG系统配置Python 3.11环境..."
echo ""

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
RAG_DIR="$PROJECT_ROOT/📚 Enhanced RAG & Knowledge Graph"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查Python 3.11
echo -e "${BLUE}1️⃣  检查Python 3.11...${NC}"
if command -v python3.11 &> /dev/null; then
    PYTHON311=$(which python3.11)
    echo -e "${GREEN}✓ Python 3.11已安装: $PYTHON311${NC}"
    $PYTHON311 --version
else
    echo -e "${YELLOW}⚠️  Python 3.11未安装${NC}"
    echo "   安装命令: brew install python@3.11"
    exit 1
fi

echo ""

# 创建独立虚拟环境
echo -e "${BLUE}2️⃣  创建Python 3.11虚拟环境...${NC}"
cd "$RAG_DIR"

if [ -d "venv_311" ]; then
    echo -e "${YELLOW}   虚拟环境已存在，删除旧环境...${NC}"
    rm -rf venv_311
fi

$PYTHON311 -m venv venv_311
echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"

echo ""

# 激活虚拟环境并安装依赖
echo -e "${BLUE}3️⃣  安装RAG系统依赖...${NC}"
source venv_311/bin/activate

# 升级pip
echo "   升级pip..."
pip install --quiet --upgrade pip

# 安装基础依赖
echo "   安装基础依赖..."
pip install --quiet fastapi uvicorn pydantic requests numpy

# 尝试安装torch和sentence-transformers
echo "   安装PyTorch (这可能需要几分钟)..."
pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu

echo "   安装sentence-transformers..."
pip install --quiet sentence-transformers

echo "   安装FAISS..."
pip install --quiet faiss-cpu

echo "   安装其他依赖..."
pip install --quiet beautifulsoup4 lxml python-multipart aiofiles

echo -e "${GREEN}✓ 所有依赖安装完成${NC}"

echo ""

# 测试导入
echo -e "${BLUE}4️⃣  测试依赖导入...${NC}"
python -c "
import torch
import sentence_transformers
import faiss
import numpy as np
print('✓ 所有关键包导入成功')
print(f'  - PyTorch: {torch.__version__}')
print(f'  - Sentence Transformers: {sentence_transformers.__version__}')
print(f'  - NumPy: {np.__version__}')
" && echo -e "${GREEN}✓ 依赖测试通过${NC}" || echo -e "${RED}✗ 依赖测试失败${NC}"

echo ""

# 创建启动脚本
echo -e "${BLUE}5️⃣  创建RAG启动脚本...${NC}"
cat > "$RAG_DIR/start_rag.sh" << 'EOF'
#!/bin/bash

echo "🚀 启动RAG系统 (Python 3.11)..."

RAG_DIR="/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph"

# 停止旧进程
lsof -ti:8011 | xargs kill -9 2>/dev/null
sleep 2

# 激活Python 3.11环境
cd "$RAG_DIR"
source venv_311/bin/activate

# 启动服务
nohup python -m uvicorn api.app:app --host 0.0.0.0 --port 8011 > /tmp/rag-system.log 2>&1 &
PID=$!

echo "   PID: $PID"
echo "   日志: /tmp/rag-system.log"

# 等待启动
sleep 5

# 测试服务
if curl -s http://localhost:8011/health > /dev/null 2>&1; then
    echo "   ✅ RAG系统启动成功！"
    echo ""
    echo "   访问地址: http://localhost:8011"
    echo "   API文档: http://localhost:8011/docs"
else
    echo "   ❌ RAG系统启动失败"
    echo "   查看日志: tail -f /tmp/rag-system.log"
fi
EOF

chmod +x "$RAG_DIR/start_rag.sh"
echo -e "${GREEN}✓ 启动脚本创建成功: $RAG_DIR/start_rag.sh${NC}"

echo ""
echo "================================"
echo -e "${GREEN}✅ RAG环境配置完成！${NC}"
echo "================================"
echo ""
echo "📋 下一步："
echo "   1. 启动RAG系统: cd '$RAG_DIR' && ./start_rag.sh"
echo "   2. 测试服务: curl http://localhost:8011/health"
echo "   3. 查看文档: open http://localhost:8011/docs"
echo ""
echo "💡 提示："
echo "   RAG系统使用独立的Python 3.11环境"
echo "   虚拟环境位置: $RAG_DIR/venv_311"
echo ""


