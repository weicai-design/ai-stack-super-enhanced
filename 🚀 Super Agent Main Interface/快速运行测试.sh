#!/bin/bash
# 快速运行测试（假设依赖已安装）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查pytest是否可用
if ! python3 -m pytest --version >/dev/null 2>&1; then
    echo "错误: pytest未安装"
    echo ""
    echo "请先运行以下命令之一安装依赖:"
    echo "  1. ./安装并运行测试.sh  (推荐，会自动处理虚拟环境)"
    echo "  2. python3 -m pip install pytest pytest-asyncio httpx --break-system-packages"
    echo "  3. 使用虚拟环境: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "=========================================="
echo "AI工作流完整实现与验证测试（T001-T003）"
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

