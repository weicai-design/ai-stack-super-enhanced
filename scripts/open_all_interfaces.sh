#!/bin/bash

# AI-STACK 所有界面打开脚本
# 自动检测服务状态并打开可用界面

echo "🌐 AI-STACK 界面访问工具"
echo "════════════════════════════════════════"
echo ""

# 检查端口是否在监听
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
}

# 打开URL（如果服务运行）
open_if_running() {
    local port=$1
    local url=$2
    local name=$3
    
    if check_port $port; then
        echo "✅ $name (端口 $port) - 正在打开..."
        open "$url" 2>/dev/null
        sleep 1
    else
        echo "⚠️  $name (端口 $port) - 服务未运行"
    fi
}

echo "📊 检查服务状态..."
echo ""

# 一级界面
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 一级界面（主界面）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
open_if_running 8020 "http://localhost:8020" "超级Agent主界面"
open_if_running 3000 "http://localhost:3000" "OpenWebUI交互中心"
echo ""

# 二级界面
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 二级界面（独立系统）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
open_if_running 8011 "http://localhost:8011/rag-management" "RAG知识库管理"
open_if_running 8012 "http://localhost:8012" "ERP前端系统"
open_if_running 8013 "http://localhost:8013/docs" "ERP API文档"
open_if_running 8017 "http://localhost:8017/dashboard" "智能任务系统"
open_if_running 8019 "http://localhost:8019/dashboard" "自我学习系统"
open_if_running 8018 "http://localhost:8018/dashboard" "资源管理系统"
open_if_running 8015 "http://localhost:8015/dashboard" "趋势分析系统"
open_if_running 8014 "http://localhost:8014/dashboard" "股票量化系统"
open_if_running 8016 "http://localhost:8016/dashboard" "内容创作系统"
open_if_running 8021 "http://localhost:8021" "运营管理界面"
open_if_running 8022 "http://localhost:8022" "财务管理界面"
open_if_running 8023 "http://localhost:8023" "AI编程助手"
echo ""

# ERP三级界面
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 ERP三级界面（子系统）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if check_port 8012; then
    echo "✅ ERP前端运行中，打开三级界面..."
    open "http://localhost:8012/interfaces/order-management.html" 2>/dev/null
    sleep 0.5
    open "http://localhost:8012/interfaces/project-management.html" 2>/dev/null
    sleep 0.5
    open "http://localhost:8012/interfaces/procurement-management.html" 2>/dev/null
    sleep 0.5
    open "http://localhost:8012/interfaces/production-management.html" 2>/dev/null
    sleep 0.5
    open "http://localhost:8012/interfaces/quality-management.html" 2>/dev/null
    echo "✅ 已打开5个主要三级界面"
else
    echo "⚠️  ERP前端未运行，无法打开三级界面"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 完成！"
echo ""
echo "💡 提示："
echo "   - 如果某些界面无法打开，请先启动对应的服务"
echo "   - 查看完整访问指南：🌐AI-STACK所有界面访问指南.md"
echo ""


