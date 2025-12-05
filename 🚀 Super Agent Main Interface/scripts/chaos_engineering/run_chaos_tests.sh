#!/bin/bash
# Chaos工程测试脚本
# 7.3: 运行Chaos测试，产出日志、报告存储于evidence/

set -e  # 任何命令失败时立即退出

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVIDENCE_DIR="$PROJECT_ROOT/evidence/chaos"

# 创建必要的目录
mkdir -p "$EVIDENCE_DIR"

# 时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$EVIDENCE_DIR/chaos_test_${TIMESTAMP}.log"
REPORT_FILE="$EVIDENCE_DIR/chaos_test_report_${TIMESTAMP}.json"

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
log_info "🚀 启动Chaos工程测试..."

# 1. 依赖检查
log_info "1. 检查必要依赖..."
check_dependency "Python3" "python3" || exit 1
check_dependency "Pip" "pip3" || exit 1
log_success "所有依赖检查通过。"

# 2. 切换到项目根目录
cd "$PROJECT_ROOT"
log_info "已切换到项目根目录: $PROJECT_ROOT"

# 3. 检查测试文件
log_info "2. 检查测试文件..."
CHAOS_RUNNER="$PROJECT_ROOT/🚀 Super Agent Main Interface/scripts/chaos_engineering/chaos_test_runner.py"
if [ ! -f "$CHAOS_RUNNER" ]; then
    log_error "Chaos测试运行器不存在: $CHAOS_RUNNER"
    exit 1
fi
log_success "测试文件检查通过。"

# 4. 运行Chaos测试
log_info "3. 运行Chaos测试..."
log_info "证据目录: $EVIDENCE_DIR"
log_info "日志文件: $LOG_FILE"

# 运行Chaos测试（使用Python脚本）
if python3 "$CHAOS_RUNNER" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "Chaos测试执行完成。"
else
    log_error "Chaos测试执行失败。"
    exit 1
fi

# 5. 检查测试结果
log_info "4. 检查测试结果..."
if [ -d "$EVIDENCE_DIR" ] && [ "$(ls -A $EVIDENCE_DIR/*.json 2>/dev/null)" ]; then
    log_success "测试报告已生成在: $EVIDENCE_DIR"
    
    # 统计测试结果
    TOTAL_TESTS=$(find "$EVIDENCE_DIR" -name "chaos_test_*.json" -type f | wc -l)
    log_info "测试报告数量: $TOTAL_TESTS"
else
    log_error "测试报告未生成。"
    exit 1
fi

# 6. 生成摘要报告
log_info "5. 生成摘要报告..."
SUMMARY_FILE="$EVIDENCE_DIR/chaos_test_summary_${TIMESTAMP}.txt"

cat > "$SUMMARY_FILE" << EOF
Chaos工程测试摘要报告
====================
测试时间: $(date '+%Y-%m-%d %H:%M:%S')
证据目录: $EVIDENCE_DIR
日志文件: $LOG_FILE

测试结果:
EOF

if [ -d "$EVIDENCE_DIR" ]; then
    echo "测试报告文件:" >> "$SUMMARY_FILE"
    find "$EVIDENCE_DIR" -name "chaos_test_*.json" -type f -exec basename {} \; >> "$SUMMARY_FILE" 2>/dev/null || true
    echo "" >> "$SUMMARY_FILE"
    echo "日志文件:" >> "$SUMMARY_FILE"
    find "$EVIDENCE_DIR" -name "chaos_test_*.log" -type f -exec basename {} \; >> "$SUMMARY_FILE" 2>/dev/null || true
fi

log_success "摘要报告已生成: $SUMMARY_FILE"

# 7. 输出结果路径
log_info "6. 测试结果文件:"
log_info "  证据目录: $EVIDENCE_DIR"
log_info "  摘要报告: $SUMMARY_FILE"
log_info "  日志文件: $LOG_FILE"

log_success "🎉 Chaos工程测试执行完成！"

# 显示摘要
echo ""
echo "=========================================="
cat "$SUMMARY_FILE"
echo "=========================================="

