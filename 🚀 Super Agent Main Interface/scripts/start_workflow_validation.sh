#!/bin/bash

# AI-STACK 工作流验证系统启动脚本
# 功能：一键启动工作流验证系统，包括测试、监控和仪表板

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$PROJECT_ROOT/tools"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# 日志文件
LOG_FILE="$PROJECT_ROOT/logs/workflow_validation.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查Python环境
check_python_environment() {
    print_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "未找到python3命令，请安装Python 3.7+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    print_info "Python版本: $PYTHON_VERSION"
    
    # 检查Python版本是否 >= 3.7
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)"; then
        print_success "Python版本检查通过"
    else
        print_error "需要Python 3.7或更高版本"
        exit 1
    fi
}

# 函数：检查依赖
check_dependencies() {
    print_info "检查项目依赖..."
    
    # 检查项目根目录是否存在
    if [ ! -d "$PROJECT_ROOT" ]; then
        print_error "项目根目录不存在: $PROJECT_ROOT"
        exit 1
    fi
    
    # 检查核心文件是否存在
    local core_files=(
        "$PROJECT_ROOT/core/workflow_orchestrator.py"
        "$PROJECT_ROOT/core/workflow_validation_monitor.py"
        "$PROJECT_ROOT/tools/workflow_validation_dashboard.py"
        "$PROJECT_ROOT/tools/run_workflow_validation.py"
        "$PROJECT_ROOT/config/workflow_validation_config.py"
    )
    
    for file in "${core_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_warning "文件不存在: $file"
        fi
    done
    
    print_success "依赖检查完成"
}

# 函数：运行工作流验证测试
run_validation_tests() {
    print_info "运行工作流验证测试..."
    
    cd "$PROJECT_ROOT"
    
    # 运行测试脚本
    if python3 "$TOOLS_DIR/run_workflow_validation.py" 2>&1 | tee -a "$LOG_FILE"; then
        print_success "工作流验证测试完成"
    else
        print_error "工作流验证测试失败"
        return 1
    fi
}

# 函数：启动验证仪表板
start_validation_dashboard() {
    print_info "启动工作流验证仪表板..."
    
    cd "$PROJECT_ROOT"
    
    # 后台启动仪表板
    nohup python3 "$TOOLS_DIR/workflow_validation_dashboard.py" >> "$LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    
    # 保存PID到文件
    echo "$DASHBOARD_PID" > "$PROJECT_ROOT/.dashboard.pid"
    
    # 等待仪表板启动
    sleep 3
    
    if kill -0 "$DASHBOARD_PID" 2>/dev/null; then
        print_success "工作流验证仪表板已启动 (PID: $DASHBOARD_PID)"
        print_info "仪表板日志: $LOG_FILE"
        print_info "按 Ctrl+C 停止仪表板"
    else
        print_error "工作流验证仪表板启动失败"
        return 1
    fi
}

# 函数：停止验证仪表板
stop_validation_dashboard() {
    print_info "停止工作流验证仪表板..."
    
    local pid_file="$PROJECT_ROOT/.dashboard.pid"
    
    if [ -f "$pid_file" ]; then
        local dashboard_pid=$(cat "$pid_file")
        
        if kill -0 "$dashboard_pid" 2>/dev/null; then
            kill "$dashboard_pid"
            print_success "工作流验证仪表板已停止 (PID: $dashboard_pid)"
        else
            print_warning "工作流验证仪表板进程不存在"
        fi
        
        rm -f "$pid_file"
    else
        print_warning "未找到仪表板PID文件"
    fi
}

# 函数：显示使用帮助
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  test        运行工作流验证测试"
    echo "  dashboard   启动工作流验证仪表板"
    echo "  stop        停止工作流验证仪表板"
    echo "  full        运行完整验证流程（测试 + 仪表板）"
    echo "  status      显示验证系统状态"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 test        # 仅运行测试"
    echo "  $0 dashboard   # 仅启动仪表板"
    echo "  $0 full        # 完整验证流程"
    echo "  $0 status      # 查看系统状态"
}

# 函数：显示系统状态
show_status() {
    print_info "工作流验证系统状态检查..."
    
    local pid_file="$PROJECT_ROOT/.dashboard.pid"
    
    # 检查仪表板进程
    if [ -f "$pid_file" ]; then
        local dashboard_pid=$(cat "$pid_file")
        
        if kill -0 "$dashboard_pid" 2>/dev/null; then
            print_success "工作流验证仪表板正在运行 (PID: $dashboard_pid)"
        else
            print_warning "工作流验证仪表板进程文件存在但进程未运行"
            rm -f "$pid_file"
        fi
    else
        print_info "工作流验证仪表板未运行"
    fi
    
    # 检查日志文件
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(du -h "$LOG_FILE" | cut -f1)
        print_info "日志文件: $LOG_FILE ($log_size)"
    else
        print_info "日志文件: 未创建"
    fi
    
    # 检查验证报告目录
    local report_dir="$PROJECT_ROOT/validation_reports"
    if [ -d "$report_dir" ]; then
        local report_count=$(find "$report_dir" -name "*.md" | wc -l)
        print_info "验证报告数量: $report_count"
    else
        print_info "验证报告目录: 未创建"
    fi
    
    print_success "状态检查完成"
}

# 函数：清理临时文件
cleanup() {
    print_info "清理临时文件..."
    
    rm -f "$PROJECT_ROOT/.dashboard.pid"
    
    print_success "清理完成"
}

# 主函数
main() {
    local action="${1:-help}"
    
    case "$action" in
        test)
            check_python_environment
            check_dependencies
            run_validation_tests
            ;;
        dashboard)
            check_python_environment
            check_dependencies
            start_validation_dashboard
            
            # 等待用户中断
            trap 'stop_validation_dashboard; cleanup; exit 0' INT
            while true; do
                sleep 1
            done
            ;;
        stop)
            stop_validation_dashboard
            cleanup
            ;;
        full)
            check_python_environment
            check_dependencies
            run_validation_tests
            start_validation_dashboard
            
            # 等待用户中断
            trap 'stop_validation_dashboard; cleanup; exit 0' INT
            while true; do
                sleep 1
            done
            ;;
        status)
            show_status
            ;;
        help)
            show_usage
            ;;
        *)
            print_error "未知选项: $action"
            show_usage
            exit 1
            ;;
    esac
}

# 设置信号处理
trap 'cleanup; exit 0' EXIT

# 运行主函数
main "$@"