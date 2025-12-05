#!/bin/bash
# 性能测试运行脚本
# 7.1: 运行性能测试套件，记录2秒SLO、专家协同案例等数据

set -e  # 任何命令失败时立即退出

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TESTS_DIR="$PROJECT_ROOT/tests/performance"
RESULTS_DIR="$PROJECT_ROOT/performance_results"
LOG_DIR="$PROJECT_ROOT/logs/performance"
SLO_REPORT_DIR="$PROJECT_ROOT/logs/workflow"
TEST_FILE="$TESTS_DIR/test_slo_2s.py"

# 创建必要的目录
mkdir -p "$RESULTS_DIR" "$LOG_DIR"

# 时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/performance_test_${TIMESTAMP}.log"
REPORT_FILE="$RESULTS_DIR/slo_2s_report_${TIMESTAMP}.json"

# ==================== 函数定义 ====================
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_dependency() {
    local dep_name=$1
    local command_to_check=$2
    if ! command -v "$command_to_check" &> /dev/null; then
        log_error "$dep_name ($command_to_check) 未安装，请先安装。"
        return 1
    fi
    return 0
}

# ==================== 主流程 ====================
log_info "🚀 启动性能测试套件..."

# 1. 依赖检查
log_info "1. 检查必要依赖..."
check_dependency "Python3" "python3" || exit 1
check_dependency "Pip" "pip3" || exit 1
check_dependency "Pytest" "pytest" || exit 1
log_success "所有依赖检查通过。"

# 2. 切换到项目根目录
cd "$PROJECT_ROOT"
log_info "已切换到项目根目录: $PROJECT_ROOT"

# 3. 检查测试文件
log_info "2. 检查测试文件..."
if [ ! -f "$TEST_FILE" ]; then
    log_error "测试文件不存在: $TEST_FILE"
    exit 1
fi
log_success "测试文件检查通过。"

# 4. 运行性能测试
log_info "3. 运行性能测试套件..."
log_info "测试文件: $TEST_FILE"
log_info "结果目录: $RESULTS_DIR"
log_info "日志文件: $LOG_FILE"
log_info "目标基准地址: ${SLO_BASE_URL:-http://localhost:8000}"

# 运行pytest测试
# 注意：如果安装了pytest-json-report，可以使用--json-report选项
# 否则使用标准pytest输出
export SLO_BASE_URL="${SLO_BASE_URL:-http://localhost:8000}"
export SLO_TEST_ITERATIONS="${SLO_TEST_ITERATIONS:-10}"

if command -v pytest-json-report &> /dev/null || python3 -c "import pytest_jsonreport" 2>/dev/null; then
    # 使用pytest-json-report插件
    if python3 -m pytest "$TEST_FILE" \
        -v \
        --tb=short \
        --json-report \
        --json-report-file="$RESULTS_DIR/pytest_report_${TIMESTAMP}.json" \
        --log-cli-level=INFO \
        2>&1 | tee -a "$LOG_FILE"; then
        log_success "性能测试执行完成。"
    else
        log_error "性能测试执行失败。"
        exit 1
    fi
else
    # 使用标准pytest输出，手动生成JSON报告
    log_info "pytest-json-report未安装，使用标准pytest输出"
    if python3 -m pytest "$TEST_FILE" \
        -v \
        --tb=short \
        --log-cli-level=INFO \
        2>&1 | tee -a "$LOG_FILE"; then
        log_success "性能测试执行完成。"
    else
        log_error "性能测试执行失败。"
        exit 1
    fi
fi

# 5. 收集SLO测试报告
log_info "4. 汇总SLO测试报告..."
LATEST_SLO_REPORT=$(ls -t "$SLO_REPORT_DIR"/slo_2s_test_report_*.json 2>/dev/null | head -n 1 || true)
if [ -z "$LATEST_SLO_REPORT" ]; then
    log_error "未找到SLO测试报告，请确认pytest是否成功生成。"
    exit 1
fi
cp "$LATEST_SLO_REPORT" "$REPORT_FILE"
log_success "SLO测试报告已复制到: $REPORT_FILE"

# 6. 生成摘要报告
log_info "5. 生成摘要报告..."
SUMMARY_FILE="$RESULTS_DIR/performance_summary_${TIMESTAMP}.txt"

python3 <<EOF > "$SUMMARY_FILE"
import json
from datetime import datetime
report_path = "$REPORT_FILE"
log_path = "$LOG_FILE"
test_file = "$TEST_FILE"
report = json.loads(open(report_path, encoding="utf-8").read())
summary = report.get("summary", {})

print("SLO性能测试摘要报告")
print("====================")
print(f"测试时间: {datetime.now():%Y-%m-%d %H:%M:%S}")
print(f"测试文件: {test_file}")
print(f"日志文件: {log_path}")
print(f"SLO报告: {report_path}")
print("")
print("关键指标:")
print(f"  API总数: {summary.get('total_apis', 0)}")
print(f"  API级合规率: {summary.get('overall_api_compliance_rate', 0)*100:.2f}%")
print(f"  请求级合规率: {summary.get('overall_request_compliance_rate', 0)*100:.2f}%")
print(f"  平均响应时间: {summary.get('avg_response_time_ms', 0):.2f} ms")
print(f"  P95响应时间: {summary.get('p95_response_time_ms', 0):.2f} ms")
print(f"  P99响应时间: {summary.get('p99_response_time_ms', 0):.2f} ms")
print("")
service_down = summary.get("service_unavailable_endpoints") or []
if service_down:
    print("警告: 以下端点未能成功访问，可能需要检查服务状态：")
    for ep in service_down:
        print(f"  - {ep}")
    print("")
print("详细结果请查看完整JSON报告。")
EOF

log_success "摘要报告已生成: $SUMMARY_FILE"

# 7. 输出结果路径
log_info "6. 测试结果文件:"
log_info "  详细报告: $REPORT_FILE"
log_info "  摘要报告: $SUMMARY_FILE"
log_info "  日志文件: $LOG_FILE"

log_success "🎉 性能测试套件执行完成！"

# 显示摘要
echo ""
echo "=========================================="
cat "$SUMMARY_FILE"
echo "=========================================="

