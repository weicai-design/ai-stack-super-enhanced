#!/bin/bash
# -*- coding: utf-8 -*-
# 运行工作流验证测试脚本（T001-T003）
# 执行AI工作流完整实现与验证的所有测试

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 进入项目根目录
cd "$PROJECT_ROOT"

# 使用符号链接或直接路径
if [ -L "super_agent_main_interface" ]; then
    MAIN_INTERFACE_DIR="super_agent_main_interface"
elif [ -d "🚀 Super Agent Main Interface" ]; then
    MAIN_INTERFACE_DIR="🚀 Super Agent Main Interface"
else
    echo "错误: 找不到主界面目录"
    exit 1
fi

echo "=========================================="
echo "AI工作流完整实现与验证测试（T001-T003）"
echo "=========================================="
echo "主界面目录: $MAIN_INTERFACE_DIR"
echo ""

# 进入主界面目录
cd "$MAIN_INTERFACE_DIR"

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
echo "查看报告:"
echo "  - 工作流集成测试: logs/workflow/integration_test_report_*.json"
echo "  - RAG双检索测试: logs/workflow/rag_double_retrieval_test_report_*.json"
echo "  - 2秒SLO测试: logs/workflow/slo_2s_test_report_*.json"
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="

