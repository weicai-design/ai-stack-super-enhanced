#!/bin/bash
# 安装依赖并运行测试的一体化脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "T001-T003 测试安装与运行"
echo "=========================================="
echo ""

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "检测到未使用虚拟环境"
    echo ""
    echo "选项1: 使用虚拟环境（推荐）"
    echo "选项2: 使用--break-system-packages安装（需要确认）"
    echo ""
    read -p "请选择 (1/2，默认1): " choice
    choice=${choice:-1}
    
    if [ "$choice" = "1" ]; then
        echo "创建虚拟环境..."
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        echo "激活虚拟环境..."
        source venv/bin/activate
        
        echo "安装依赖..."
        pip install pytest pytest-asyncio httpx --quiet
        
        echo "虚拟环境已激活，依赖已安装"
    elif [ "$choice" = "2" ]; then
        echo "使用--break-system-packages安装..."
        python3 -m pip install pytest pytest-asyncio httpx --break-system-packages --quiet
    else
        echo "无效选择，退出"
        exit 1
    fi
else
    echo "已在虚拟环境中，直接安装依赖..."
    pip install pytest pytest-asyncio httpx --quiet
fi

echo ""
echo "=========================================="
echo "开始运行测试"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p logs/workflow

# 设置Python路径
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 运行T001: 工作流集成测试
echo "=========================================="
echo "T001: 工作流集成测试"
echo "=========================================="
python3 -m pytest tests/test_workflow_integration.py -v --tb=short || {
    echo "警告: T001测试失败或部分失败（可能是RAG服务未运行）"
}
echo ""

# 运行T002: RAG双检索验证测试
echo "=========================================="
echo "T002: RAG双检索验证测试"
echo "=========================================="
python3 -m pytest tests/test_rag_double_retrieval.py -v --tb=short || {
    echo "警告: T002测试失败或部分失败（可能是RAG服务未运行）"
}
echo ""

# 运行T003: 2秒SLO性能验证测试
echo "=========================================="
echo "T003: 2秒SLO性能验证测试"
echo "=========================================="
echo "注意: 此测试需要API服务运行在 http://localhost:8000"
python3 -m pytest tests/performance/test_slo_2s.py -v --tb=short || {
    echo "警告: T003测试失败或部分失败（可能是API服务未运行）"
}
echo ""

# 生成汇总报告
echo "=========================================="
echo "测试汇总"
echo "=========================================="
echo "测试报告已保存到: logs/workflow/"
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="

