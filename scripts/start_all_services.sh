#!/bin/bash

# AI-STACK 所有服务启动脚本
# 一键启动所有主要服务

echo "🚀 AI-STACK 服务启动工具"
echo "════════════════════════════════════════"
echo ""

BASE_DIR="/Users/ywc/ai-stack-super-enhanced"
PIDS_FILE="/tmp/ai-stack-pids.txt"

# 清理旧进程
cleanup_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  端口 $port 已被占用，正在清理..."
        lsof -ti :$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 启动服务并记录PID
start_service() {
    local name=$1
    local port=$2
    local cmd=$3
    local dir=$4
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 启动 $name (端口 $port)..."
    
    cleanup_port $port
    
    if [ -n "$dir" ]; then
        cd "$BASE_DIR/$dir" || return 1
    fi
    
    # 执行启动命令
    eval "$cmd" > /tmp/${name// /_}.log 2>&1 &
    local pid=$!
    
    echo "$name|$port|$pid" >> "$PIDS_FILE"
    echo "✅ $name 已启动 (PID: $pid, 端口: $port)"
    
    sleep 2
}

# 检查服务健康状态
check_service() {
    local name=$1
    local port=$2
    local endpoint=${3:-/health}
    
    sleep 3
    if curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo "✅ $name 健康检查通过"
        return 0
    else
        echo "⚠️  $name 健康检查失败（可能正在启动中）"
        return 1
    fi
}

# 清空PID文件
> "$PIDS_FILE"

echo "📍 清理旧进程..."
cleanup_port 8011
cleanup_port 8012
cleanup_port 8013
cleanup_port 8014
cleanup_port 8015
cleanup_port 8016
cleanup_port 8017
cleanup_port 8018
cleanup_port 8019
cleanup_port 8020
cleanup_port 8021
cleanup_port 8022
cleanup_port 8023

echo ""
echo "🚀 开始启动服务..."
echo ""

# 1. 启动RAG系统 (8011)
start_service "RAG系统" 8011 \
    "source venv_311/bin/activate && python -m uvicorn api.app:app --host 0.0.0.0 --port 8011" \
    "📚 Enhanced RAG & Knowledge Graph"

# 2. 启动ERP后端 (8013)
start_service "ERP后端" 8013 \
    "source venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8013 --reload" \
    "💼 Intelligent ERP & Business Management"

# 3. 启动ERP前端 (8012)
start_service "ERP前端" 8012 \
    "cd web/frontend && npm run dev" \
    "💼 Intelligent ERP & Business Management"

# 4. 启动超级Agent主界面 (8020)
start_service "超级Agent主界面" 8020 \
    "python3 -m http.server 8020" \
    "🚀 Super Agent Main Interface/web"

# 5. 启动任务系统 (8017)
if [ -f "$BASE_DIR/🤖 Intelligent Task Agent/api/main.py" ]; then
    start_service "任务系统" 8017 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8017" \
        "🤖 Intelligent Task Agent"
fi

# 6. 启动自我学习系统 (8019)
if [ -f "$BASE_DIR/🧠 Self Learning System/api/main.py" ]; then
    start_service "自我学习系统" 8019 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8019" \
        "🧠 Self Learning System"
fi

# 7. 启动资源管理系统 (8018)
if [ -f "$BASE_DIR/🛠️ Intelligent System Resource Management/api/main.py" ]; then
    start_service "资源管理系统" 8018 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8018" \
        "🛠️ Intelligent System Resource Management"
fi

# 8. 启动趋势分析系统 (8015)
if [ -f "$BASE_DIR/🔍 Intelligent Trend Analysis/api/main.py" ]; then
    start_service "趋势分析系统" 8015 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8015" \
        "🔍 Intelligent Trend Analysis"
fi

# 9. 启动股票系统 (8014)
if [ -f "$BASE_DIR/📈 Intelligent Stock Trading/api/main.py" ]; then
    start_service "股票系统" 8014 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8014" \
        "📈 Intelligent Stock Trading"
fi

# 10. 启动内容创作系统 (8016)
if [ -f "$BASE_DIR/🎨 Intelligent Content Creation/api/main.py" ]; then
    start_service "内容创作系统" 8016 \
        "source venv/bin/activate 2>/dev/null || true && python -m uvicorn api.main:app --host 0.0.0.0 --port 8016" \
        "🎨 Intelligent Content Creation"
fi

echo ""
echo "⏳ 等待服务启动..."
sleep 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 服务健康检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service "RAG系统" 8011
check_service "ERP后端" 8013
check_service "ERP前端" 8012 "/"
check_service "超级Agent" 8020 "/"

echo ""
echo "════════════════════════════════════════"
echo "✅ 服务启动完成！"
echo "════════════════════════════════════════"
echo ""
echo "📍 访问地址："
echo "   🤖 超级Agent主界面: http://localhost:8020"
echo "   💬 OpenWebUI:        http://localhost:3000"
echo "   📚 RAG知识库:        http://localhost:8011/rag-management"
echo "   💼 ERP前端:          http://localhost:8012"
echo "   📖 ERP API文档:      http://localhost:8013/docs"
echo ""
echo "📝 服务PID记录在: $PIDS_FILE"
echo ""
echo "🛑 停止所有服务:"
echo "   ./scripts/stop_all_services.sh"
echo ""
echo "🌐 正在打开主要界面..."
sleep 2
open http://localhost:8020
open http://localhost:8012
open http://localhost:8011/rag-management 2>/dev/null || true

echo ""
echo "✅ 完成！"


