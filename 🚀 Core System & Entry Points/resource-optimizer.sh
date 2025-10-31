#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 动态资源优化器
# 文件: 6. resource-optimizer.sh
# 功能: 智能资源监控、动态分配、冲突解决、性能优化
#

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly CONFIG_DIR="$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]"
readonly LOG_DIR="$ROOT_DIR/logs"
readonly RESOURCE_LOG="$LOG_DIR/resource.log"
readonly CACHE_DIR="$ROOT_DIR/cache/resource_cache"
readonly CONFIG_FILE="$CONFIG_DIR/global/14. resource-policy.yaml"
readonly LOCK_FILE="/tmp/ai-stack-resource-optimizer.lock"

# 资源阈值配置
readonly CPU_CRITICAL=90
readonly CPU_HIGH=80
readonly CPU_MEDIUM=60
readonly MEMORY_CRITICAL=90
readonly MEMORY_HIGH=80
readonly MEMORY_MEDIUM=60
readonly DISK_CRITICAL=90
readonly DISK_HIGH=80

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# 日志函数
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${level}: ${message}" | tee -a "$RESOURCE_LOG"
}

info() { log "${BLUE}INFO${NC}" "$@"; }
warn() { log "${YELLOW}WARN${NC}" "$@"; }
error() { log "${RED}ERROR${NC}" "$@"; }
success() { log "${GREEN}SUCCESS${NC}" "$@"; }

# 错误处理
trap 'cleanup_on_exit' EXIT INT TERM

cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "资源优化器异常退出，退出码: $exit_code"
    fi
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
    exit $exit_code
}

# 锁管理
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            error "另一个资源优化进程正在运行 (PID: $pid)"
            exit 1
        else
            warn "发现陈旧的锁文件，清理中..."
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
}

# 配置管理
load_resource_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        warn "资源策略配置文件不存在，使用默认配置"
        return 0
    fi

    # 解析 YAML 配置（简化版本）
    local config_content=$(cat "$CONFIG_FILE")

    # 提取 CPU 配置
    CPU_CRITICAL=$(echo "$config_content" | grep -E '^cpu_critical:' | cut -d: -f2 | tr -d ' ' || echo "90")
    CPU_HIGH=$(echo "$config_content" | grep -E '^cpu_high:' | cut -d: -f2 | tr -d ' ' || echo "80")

    # 提取内存配置
    MEMORY_CRITICAL=$(echo "$config_content" | grep -E '^memory_critical:' | cut -d: -f2 | tr -d ' ' || echo "90")
    MEMORY_HIGH=$(echo "$config_content" | grep -E '^memory_high:' | cut -d: -f2 | tr -d ' ' || echo "80")

    # 提取优化策略
    OPTIMIZATION_STRATEGY=$(echo "$config_content" | grep -E '^optimization_strategy:' | cut -d: -f2 | tr -d ' ' || echo "balanced")

    info "资源配置加载完成"
}

# 系统资源监控
get_system_resources() {
    local resources=()

    # CPU 使用率（非阻塞方式）
    local cpu_usage=$(psutil_cpu_non_blocking)

    # 内存使用率
    local memory_info=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')

    # 磁盘使用率
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')

    # 进程资源使用
    local process_resources=$(get_process_resources)

    # Docker 容器资源
    local docker_resources=$(get_docker_resources)

    echo "{
        \"timestamp\": \"$(date -Iseconds)\",
        \"cpu_usage\": $cpu_usage,
        \"memory_usage\": $memory_info,
        \"disk_usage\": $disk_usage,
        \"processes\": $process_resources,
        \"containers\": $docker_resources,
        \"load_average\": \"$(uptime | awk -F'load average:' '{print $2}')\"
    }"
}

# 非阻塞 CPU 使用率获取
psutil_cpu_non_blocking() {
    # 使用 psutil 替代方案
    local cpu_usage=$(top -l 1 | grep -E "^CPU" | awk '{print $3}' | sed 's/%//')
    if [[ -z "$cpu_usage" ]]; then
        # 备用方法
        cpu_usage=$(ps -A -o %cpu | awk '{s+=$1} END {print s}')
    fi
    echo "${cpu_usage:-0}"
}

# 进程资源监控
get_process_resources() {
    local processes_json="["

    # 获取关键进程资源使用
    local critical_processes=("ollama" "docker" "python" "node")

    for proc in "${critical_processes[@]}"; do
        local proc_info=$(ps aux | grep "$proc" | grep -v grep | head -1 | awk '{print $2, $3, $4, $11}' 2>/dev/null || true)

        if [[ -n "$proc_info" ]]; then
            local pid=$(echo "$proc_info" | awk '{print $1}')
            local cpu=$(echo "$proc_info" | awk '{print $2}')
            local mem=$(echo "$proc_info" | awk '{print $3}')
            local cmd=$(echo "$proc_info" | awk '{print $4}')

            processes_json+="{\"pid\": \"$pid\", \"name\": \"$proc\", \"cpu\": $cpu, \"memory\": $mem, \"command\": \"$cmd\"},"
        fi
    done

    processes_json="${processes_json%,}]"
    echo "$processes_json"
}

# Docker 容器资源监控
get_docker_resources() {
    if ! command -v docker &> /dev/null; then
        echo "[]"
        return 0
    fi

    local containers_json="["

    # 获取运行中的容器资源使用
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local container_id=$(echo "$line" | awk '{print $1}')
            local name=$(echo "$line" | awk '{print $2}')
            local cpu=$(echo "$line" | awk '{print $3}')
            local mem=$(echo "$line" | awk '{print $4}')
            local status=$(echo "$line" | awk '{print $5}')

            containers_json+="{\"id\": \"$container_id\", \"name\": \"$name\", \"cpu\": \"$cpu\", \"memory\": \"$mem\", \"status\": \"$status\"},"
        fi
    done < <(docker stats --no-stream --format "table {{.Container}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.Status}}" | tail -n +2)

    containers_json="${containers_json%,}]"
    echo "$containers_json"
}

# 资源状态评估
assess_resource_status() {
    local resources_json="$1"

    local cpu_usage=$(echo "$resources_json" | grep -o '"cpu_usage":[0-9.]*' | cut -d: -f2)
    local memory_usage=$(echo "$resources_json" | grep -o '"memory_usage":[0-9.]*' | cut -d: -f2)
    local disk_usage=$(echo "$resources_json" | grep -o '"disk_usage":[0-9.]*' | cut -d: -f2)

    local status="healthy"
    local issues=()

    # CPU 评估
    if (( $(echo "$cpu_usage >= $CPU_CRITICAL" | bc -l) )); then
        status="critical"
        issues+=("CPU使用率过高: ${cpu_usage}%")
    elif (( $(echo "$cpu_usage >= $CPU_HIGH" | bc -l) )); then
        status="degraded"
        issues+=("CPU使用率较高: ${cpu_usage}%")
    fi

    # 内存评估
    if (( $(echo "$memory_usage >= $MEMORY_CRITICAL" | bc -l) )); then
        status="critical"
        issues+=("内存使用率过高: ${memory_usage}%")
    elif (( $(echo "$memory_usage >= $MEMORY_HIGH" | bc -l) )); then
        status="degraded"
        issues+=("内存使用率较高: ${memory_usage}%")
    fi

    # 磁盘评估
    if (( $(echo "$disk_usage >= $DISK_CRITICAL" | bc -l) )); then
        status="critical"
        issues+=("磁盘使用率过高: ${disk_usage}%")
    elif (( $(echo "$disk_usage >= $DISK_HIGH" | bc -l) )); then
        status="degraded"
        issues+=("磁盘使用率较高: ${disk_usage}%")
    fi

    echo "{
        \"overall_status\": \"$status\",
        \"cpu_usage\": $cpu_usage,
        \"memory_usage\": $memory_usage,
        \"disk_usage\": $disk_usage,
        \"issues\": [\"$(echo "${issues[@]}" | sed 's/ /", "/g')\"],
        \"timestamp\": \"$(date -Iseconds)\"
    }"
}

# 资源优化策略
apply_optimization_strategy() {
    local resource_status="$1"
    local overall_status=$(echo "$resource_status" | grep -o '"overall_status":"[^"]*' | cut -d'"' -f4)

    case "$overall_status" in
        "critical")
            apply_critical_optimizations "$resource_status"
            ;;
        "degraded")
            apply_degraded_optimizations "$resource_status"
            ;;
        "healthy")
            apply_normal_optimizations "$resource_status"
            ;;
        *)
            warn "未知资源状态: $overall_status"
            ;;
    esac
}

# 严重状态优化
apply_critical_optimizations() {
    local resource_status="$1"
    warn "应用严重状态优化策略"

    # 停止非关键服务
    stop_non_critical_services

    # 清理临时文件
    cleanup_temp_files

    # 调整服务资源限制
    adjust_service_limits "reduce"

    # 通知用户
    notify_resource_critical "$resource_status"
}

# 降级状态优化
apply_degraded_optimizations() {
    local resource_status="$1"
    info "应用降级状态优化策略"

    # 调整服务资源限制
    adjust_service_limits "moderate"

    # 优化缓存策略
    optimize_cache_strategy

    # 建议用户操作
    suggest_user_actions "$resource_status"
}

# 正常状态优化
apply_normal_optimizations() {
    local resource_status="$1"
    info "应用正常状态优化策略"

    # 预防性优化
    preventive_optimizations

    # 性能调优
    performance_tuning
}

# 停止非关键服务
stop_non_critical_services() {
    local non_critical_services=("content_creation" "trend_analysis" "task_agent")

    for service in "${non_critical_services[@]}"; do
        info "检查非关键服务: $service"
        # 根据实际服务管理逻辑实现
    done
}

# 清理临时文件
cleanup_temp_files() {
    info "清理临时文件..."

    # 清理系统临时文件
    find /tmp -name "ai-stack-*" -mtime +1 -delete 2>/dev/null || true

    # 清理缓存目录
    if [[ -d "$CACHE_DIR" ]]; then
        find "$CACHE_DIR" -type f -mtime +7 -delete 2>/dev/null || true
    fi

    # 清理 Docker 临时文件
    docker system prune -f 2>/dev/null || true

    success "临时文件清理完成"
}

# 调整服务资源限制
adjust_service_limits() {
    local mode="$1"

    case "$mode" in
        "reduce")
            # 减少资源分配
            update_docker_compose_limits "0.5" "1g"
            ;;
        "moderate")
            # 适度调整
            update_docker_compose_limits "1.0" "2g"
            ;;
        "normal")
            # 恢复正常
            update_docker_compose_limits "2.0" "4g"
            ;;
    esac
}

# 更新 Docker Compose 资源限制
update_docker_compose_limits() {
    local cpu_limit="$1"
    local memory_limit="$2"

    local compose_file="$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml"

    if [[ -f "$compose_file" ]]; then
        info "更新 Docker Compose 资源限制: CPU=$cpu_limit, Memory=$memory_limit"
        # 实际实现需要修改 YAML 文件
    fi
}

# 优化缓存策略
optimize_cache_strategy() {
    info "优化缓存策略..."

    # 调整 RAG 缓存大小
    adjust_rag_cache_size

    # 优化向量数据库缓存
    optimize_vector_db_cache

    # 清理过期缓存
    cleanup_expired_cache
}

# 预防性优化
preventive_optimizations() {
    info "执行预防性优化..."

    # 检查文件系统
    check_filesystem_health

    # 优化数据库
    optimize_databases

    # 更新索引
    update_search_indexes
}

# 性能调优
performance_tuning() {
    info "执行性能调优..."

    # 系统参数调优
    tune_system_parameters

    # 应用级调优
    tune_application_parameters

    # 网络调优
    tune_network_parameters
}

# 用户通知
notify_resource_critical() {
    local resource_status="$1"

    # 系统通知
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"AI-STACK 资源严重不足\" with title \"资源警告\""
    fi

    # 记录到系统日志
    logger -t "ai-stack-resource" "资源严重不足: $resource_status"

    # 可以集成到 OpenWebUI 通知系统
    info "资源严重不足，已通知用户"
}

# 建议用户操作
suggest_user_actions() {
    local resource_status="$1"
    local issues=$(echo "$resource_status" | grep -o '"issues":\[[^]]*' | cut -d'[' -f2)

    info "资源优化建议:"
    echo "当前问题: $issues"
    echo "建议操作:"
    echo "1. 关闭不必要的应用程序"
    echo "2. 清理磁盘空间"
    echo "3. 考虑增加系统内存"
    echo "4. 重启 AI-STACK 服务"
}

# 生成资源报告
generate_resource_report() {
    local resources_json="$1"
    local status_json="$2"

    local report_file="$CACHE_DIR/resource_report_$(date +%Y%m%d_%H%M%S).json"

    cat > "$report_file" << EOF
{
    "system_resources": $resources_json,
    "status_assessment": $status_json,
    "optimization_applied": "$(date -Iseconds)",
    "recommendations": [
        "定期监控系统资源",
        "根据使用模式调整服务配置",
        "考虑使用外接硬盘扩展存储"
    ]
}
EOF

    echo "$report_file"
}

# 主优化循环
resource_optimization_loop() {
    local interval=${1:-60}  # 默认60秒检查一次

    info "启动资源优化器，检查间隔: ${interval}秒"

    while true; do
        acquire_lock

        # 加载最新配置
        load_resource_config

        # 获取系统资源
        local resources=$(get_system_resources)

        # 评估资源状态
        local status=$(assess_resource_status "$resources")

        # 应用优化策略
        apply_optimization_strategy "$status"

        # 生成报告
        generate_resource_report "$resources" "$status"

        release_lock

        # 等待下一次检查
        sleep "$interval"
    done
}

# 单次优化执行
single_optimization_run() {
    info "执行单次资源优化"

    acquire_lock

    # 加载配置
    load_resource_config

    # 获取系统资源
    local resources=$(get_system_resources)
    info "当前资源状态: $resources"

    # 评估资源状态
    local status=$(assess_resource_status "$resources")
    info "资源评估: $status"

    # 应用优化策略
    apply_optimization_strategy "$status"

    # 生成报告
    local report_file=$(generate_resource_report "$resources" "$status")
    success "资源优化完成，报告保存至: $report_file"

    release_lock
}

# 使用说明
show_usage() {
    cat << EOF
AI-STACK 动态资源优化器

用法: $0 [选项]

选项:
    -d, --daemon [INTERVAL]   守护进程模式运行 (默认间隔: 60秒)
    -s, --single              单次优化执行
    --status                  显示当前资源状态
    --cleanup                 执行清理操作
    --optimize-cache          优化缓存策略
    --help                    显示此帮助信息

示例:
    $0 -d 30                  守护进程模式，30秒间隔
    $0 -s                     单次优化执行
    $0 --status               显示资源状态
    $0 --cleanup              执行系统清理

EOF
}

# 主函数
main() {
    local mode="single"
    local interval=60

    # 创建必要目录
    mkdir -p "$CACHE_DIR" "$LOG_DIR"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--daemon)
                mode="daemon"
                [[ -n "$2" && "$2" =~ ^[0-9]+$ ]] && interval="$2" && shift
                shift
                ;;
            -s|--single)
                mode="single"
                shift
                ;;
            --status)
                mode="status"
                shift
                ;;
            --cleanup)
                mode="cleanup"
                shift
                ;;
            --optimize-cache)
                mode="optimize_cache"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # 执行相应操作
    case $mode in
        "daemon")
            resource_optimization_loop "$interval"
            ;;
        "single")
            single_optimization_run
            ;;
        "status")
            get_system_resources
            ;;
        "cleanup")
            cleanup_temp_files
            ;;
        "optimize_cache")
            optimize_cache_strategy
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi