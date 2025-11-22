#!/bin/bash

# 服务检查和修复脚本

echo "🔍 AI-STACK 服务检查和修复工具"
echo "════════════════════════════════════════"
echo ""

BASE_DIR="/Users/ywc/ai-stack-super-enhanced"

# 检查端口是否在监听
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 检查服务健康状态
check_service_health() {
    local port=$1
    local name=$2
    local endpoint=${3:-/health}
    
    if check_port $port; then
        if curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo "✅ $name (端口 $port) - 运行正常"
            return 0
        else
            echo "⚠️  $name (端口 $port) - 端口监听但无响应"
            return 1
        fi
    else
        echo "❌ $name (端口 $port) - 未运行"
        return 2
    fi
}

echo "📊 检查服务状态..."
echo ""

# 检查各个服务
check_service_health 3000 "OpenWebUI" "/"
check_service_health 8011 "RAG系统" "/health"
check_service_health 8012 "ERP前端" "/"
check_service_health 8013 "ERP后端" "/health"
check_service_health 8014 "股票系统" "/health"
check_service_health 8015 "趋势分析" "/health"
check_service_health 8016 "内容创作" "/health"
check_service_health 8017 "任务系统" "/health"
check_service_health 8018 "资源管理" "/health"
check_service_health 8019 "自我学习" "/health"
check_service_health 8020 "超级Agent" "/"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 修复未运行的服务..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 启动RAG系统（如果未运行）
if ! check_port 8011; then
    echo "启动RAG系统..."
    cd "$BASE_DIR/📚 Enhanced RAG & Knowledge Graph"
    if [ -f "venv_311/bin/activate" ]; then
        source venv_311/bin/activate
        nohup python -m uvicorn api.app:app --host 0.0.0.0 --port 8011 > /tmp/rag-system.log 2>&1 &
        sleep 3
        if check_port 8011; then
            echo "✅ RAG系统已启动"
        else
            echo "❌ RAG系统启动失败，查看日志: tail -f /tmp/rag-system.log"
        fi
    else
        echo "❌ RAG虚拟环境不存在，请先创建: cd '📚 Enhanced RAG & Knowledge Graph' && python3.11 -m venv venv_311"
    fi
fi

# 启动ERP后端（如果未运行）
if ! check_port 8013; then
    echo "启动ERP后端..."
    cd "$BASE_DIR/💼 Intelligent ERP & Business Management"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        nohup uvicorn api.main:app --host 0.0.0.0 --port 8013 --reload > /tmp/erp-backend.log 2>&1 &
        sleep 3
        if check_port 8013; then
            echo "✅ ERP后端已启动"
        else
            echo "❌ ERP后端启动失败，查看日志: tail -f /tmp/erp-backend.log"
        fi
    fi
fi

# 启动ERP前端（如果未运行）
if ! check_port 8012; then
    echo "启动ERP前端..."
    cd "$BASE_DIR/💼 Intelligent ERP & Business Management/web/frontend"
    if [ -f "package.json" ]; then
        nohup npm run dev > /tmp/erp-frontend.log 2>&1 &
        sleep 5
        if check_port 8012; then
            echo "✅ ERP前端已启动"
        else
            echo "❌ ERP前端启动失败，查看日志: tail -f /tmp/erp-frontend.log"
        fi
    fi
fi

# 启动超级Agent（如果未运行）
if ! check_port 8020; then
    echo "启动超级Agent主界面..."
    cd "$BASE_DIR/🚀 Super Agent Main Interface/web"
    nohup python3 -m http.server 8020 > /tmp/super-agent.log 2>&1 &
    sleep 2
    if check_port 8020; then
        echo "✅ 超级Agent已启动"
    else
        echo "❌ 超级Agent启动失败"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 最终服务状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_service_health 3000 "OpenWebUI" "/"
check_service_health 8011 "RAG系统" "/health"
check_service_health 8012 "ERP前端" "/"
check_service_health 8013 "ERP后端" "/health"
check_service_health 8020 "超级Agent" "/"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 访问地址"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🤖 超级Agent主界面: http://localhost:8020"
echo "💬 OpenWebUI:        http://localhost:3000"
echo "📚 RAG知识库:        http://localhost:8011/rag-management"
echo "💼 ERP前端:          http://localhost:8012"
echo "📖 ERP API文档:      http://localhost:8013/docs"
echo ""























