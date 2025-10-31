#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 智能服务编排器
# 文件: 7. service-orchestrator.sh
# 功能: 服务依赖管理、启动顺序控制、负载均衡、故障转移
#

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly CONFIG_DIR="$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]"
readonly LOG_DIR="$ROOT_DIR/logs"
readonly ORCHESTRATION_LOG="$LOG_DIR/orchestration.log"
readonly SERVICE_REGISTRY="$CONFIG_DIR/global/15. service-registry.yaml"
readonly DEPENDENCY_GRAPH="$CONFIG_DIR/global/16. dependency-graph.yaml"
readonly LOCK_FILE="/tmp/ai-stack-orchestrator.lock"

# 服务状态定义
readonly STATUS_STARTING="starting"
readonly STATUS_RUNNING="running"
readonly STATUS_STOPPED="stopped"
readonly STATUS_FAILED="failed"
readonly STATUS_DEGRADED="degraded"

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

    echo -e "${level}: ${message}" | tee -a "$ORCHESTRATION_LOG"
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
        error "服务编排器异常退出，退出码: $exit_code"
    fi
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
    exit $exit_code
}

# 锁管理
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            error "另一个编排进程正在运行 (PID: $pid)"
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

# 服务注册表管理
load_service_registry() {
    if [[ ! -f "$SERVICE_REGISTRY" ]]; then
        error "服务注册表不存在: $SERVICE_REGISTRY"
        return 1
    fi

    # 解析 YAML 注册表
    local registry_content=$(cat "$SERVICE_REGISTRY")

    # 提取服务定义（简化解析）
    echo "$registry_content"
}

# 依赖图管理
load_dependency_graph() {
    if [[ ! -f "$DEPENDENCY_GRAPH" ]]; then
        error "依赖图配置文件不存在: $DEPENDENCY_GRAPH"
        return 1
    fi

    # 解析依赖图
    local graph_content=$(cat "$DEPENDENCY_GRAPH")
    echo "$graph_content"
}

# 拓扑排序服务启动顺序
calculate_startup_order() {
    local dependency_graph="$1"

    # 从依赖图计算拓扑排序
    # 这里实现一个简化的拓扑排序算法

    local services=("bootstrap" "docker" "ollama" "vector-db" "rag-engine" "openwebui" "monitoring")
    local dependencies=(
        "bootstrap:"
        "docker:bootstrap"
        "ollama:docker"
        "vector-db:docker"
        "rag-engine:vector-db,ollama"
        "openwebui:rag-engine,ollama"
        "monitoring:docker"
    )

    # 实现拓扑排序逻辑
    local sorted_services=()
    local visited=()
    local temp_visited=()

    for service in "${services[@]}"; do
        if ! contains "$service" "${visited[@]}"; then
            visit "$service" "${dependencies[@]}" sorted_services visited temp_visited
        fi
    done

    echo "${sorted_services[@]}"
}

contains() {
    local item=$1
    shift
    local array=("$@")
    for element in "${array[@]}"; do
        [[ "$element" == "$item" ]] && return 0
    done
    return 1
}

visit() {
    local service=$1
    shift
    local dependencies=("$@")

    if contains "$service" "${temp_visited[@]}"; then
        error "检测到循环依赖: $service"
        return 1
    fi

    if ! contains "$service" "${visited[@]}"; then
        temp_visited+=("$service")

        # 找到该服务的依赖
        local service_deps=""
        for dep_line in "${dependencies[@]}"; do
            if [[ "$dep_line" == "$service:"* ]]; then
                service_deps=$(echo "$dep_line" | cut -d: -f2)
                break
            fi
        done

        # 递归访问依赖
        IFS=',' read -ra deps_array <<< "$service_deps"
        for dep in "${deps_array[@]}"; do
            [[ -n "$dep" ]] && visit "$dep" "${dependencies[@]}" "$5" "$6" "$7"
        done

        temp_visited=("${temp_visited[@]/$service}")
        visited+=("$service")
        eval "$5+=(\"$service\")"
    fi
}

# 服务健康检查
check_service_health() {
    local service_name="$1"
    local max_retries=5
    local retry_interval=3

    info "检查服务健康状态: $service_name"

    for ((i=1; i<=max_retries; i++)); do
        case "$service_name" in
            "docker")
                if systemctl is-active --quiet docker; then
                    success "Docker 服务运行正常"
                    return 0
                fi
                ;;
            "ollama")
                if docker ps --format "table {{.Names}}" | grep -q "ollama"; then
                    success "Ollama 服务运行正常"
                    return 0
                fi
                ;;
            "openwebui")
                if curl -s http://localhost:3000/health > /dev/null 2>&1; then
                    success "OpenWebUI 服务运行正常"
                    return 0
                fi
                ;;
            "vector-db")
                if curl -s http://localhost:6333 > /dev/null 2>&1; then
                    success "向量数据库服务运行正常"
                    return 0
                fi
                ;;
            "rag-engine")
                if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                    success "RAG 引擎服务运行正常"
                    return 0
                fi
                ;;
            "monitoring")
                if curl -s http://localhost:9090 > /dev/null 2>&1; then
                    success "监控服务运行正常"
                    return 0
                fi
                ;;
            *)
                warn "未知服务: $service_name，跳过健康检查"
                return 0
                ;;
        esac

        if [[ $i -eq $max_retries ]]; then
            error "服务健康检查失败: $service_name"
            return 1
        fi

        warn "服务 $service_name 未就绪，${retry_interval}秒后重试... ($i/$max_retries)"
        sleep $retry_interval
    done

    return 1
}

# 启动单个服务
start_service() {
    local service_name="$1"

    info "启动服务: $service_name"

    case "$service_name" in
        "bootstrap")
            # 引导服务已在运行
            return 0
            ;;
        "docker")
            if ! systemctl is-active --quiet docker; then
                systemctl start docker || {
                    error "Docker 服务启动失败"
                    return 1
                }
            fi
            ;;
        "ollama")
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                up -d ollama-service || {
                error "Ollama 服务启动失败"
                return 1
            }
            ;;
        "openwebui")
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                up -d openwebui-service || {
                error "OpenWebUI 服务启动失败"
                return 1
            }
            ;;
        "vector-db")
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                up -d qdrant-service || {
                error "向量数据库服务启动失败"
                return 1
            }
            ;;
        "rag-engine")
            # 启动 RAG 引擎
            "$ROOT_DIR/🤖 AI Core Engine [预置文件: 38个]/rag/start-rag.sh" || {
                error "RAG 引擎启动失败"
                return 1
            }
            ;;
        "monitoring")
            # 启动监控服务
            "$ROOT_DIR/📊 Monitoring & Analytics [预置文件: 25个]/start-monitoring.sh" || {
                error "监控服务启动失败"
                return 1
            }
            ;;
        *)
            error "未知服务: $service_name"
            return 1
            ;;
    esac

    # 等待服务就绪
    if ! check_service_health "$service_name"; then
        error "服务启动后健康检查失败: $service_name"
        return 1
    fi

    success "服务启动成功: $service_name"
    return 0
}

# 停止单个服务
stop_service() {
    local service_name="$1"
    local graceful=${2:-true}

    info "停止服务: $service_name (优雅模式: $graceful)"

    case "$service_name" in
        "docker")
            if [[ "$graceful" == "false" ]]; then
                systemctl stop docker
            else
                # 优雅停止：先停止所有容器
                docker stop $(docker ps -q) 2>/dev/null || true
                sleep 5
                systemctl stop docker
            fi
            ;;
        "ollama"|"openwebui"|"vector-db")
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                stop "$service_name-service" 2>/dev/null || true
            ;;
        "rag-engine")
            pkill -f "rag-engine" 2>/dev/null || true
            ;;
        "monitoring")
            pkill -f "monitoring" 2>/dev/null || true
            ;;
        *)
            warn "未知服务: $service_name，跳过停止操作"
            ;;
    esac

    success "服务停止完成: $service_name"
}

# 重启单个服务
restart_service() {
    local service_name="$1"

    info "重启服务: $service_name"

    stop_service "$service_name" true
    sleep 2
    start_service "$service_name"
}

# 服务依赖验证
validate_dependencies() {
    local service_name="$1"
    local dependency_graph="$2"

    info "验证服务依赖: $service_name"

    # 从依赖图中提取依赖关系
    local dependencies=$(echo "$dependency_graph" | grep -E "^$service_name:" | cut -d: -f2)

    if [[ -z "$dependencies" ]]; then
        warn "服务 $service_name 没有定义依赖关系"
        return 0
    fi

    IFS=',' read -ra deps_array <<< "$dependencies"
    for dep in "${deps_array[@]}"; do
        if ! check_service_health "$dep"; then
            error "依赖服务不可用: $dep (被 $service_name 依赖)"
            return 1
        fi
    done

    success "服务依赖验证通过: $service_name"
    return 0
}

# 顺序启动所有服务
start_all_services() {
    local startup_order=($(calculate_startup_order ""))
    local dependency_graph=$(load_dependency_graph)

    info "开始顺序启动服务..."
    info "启动顺序: ${startup_order[*]}"

    for service in "${startup_order[@]}"; do
        info "准备启动服务: $service"

        # 验证依赖
        if ! validate_dependencies "$service" "$dependency_graph"; then
            error "服务依赖验证失败: $service"
            return 1
        fi

        # 启动服务
        if ! start_service "$service"; then
            error "服务启动失败: $service"
            return 1
        fi

        # 记录服务状态
        update_service_status "$service" "$STATUS_RUNNING"
    done

    success "所有服务启动完成"
}

# 顺序停止所有服务
stop_all_services() {
    local startup_order=($(calculate_startup_order ""))
    local reverse_order=()

    # 反转启动顺序用于停止
    for ((i=${#startup_order[@]}-1; i>=0; i--)); do
        reverse_order+=("${startup_order[i]}")
    done

    info "开始顺序停止服务..."
    info "停止顺序: ${reverse_order[*]}"

    for service in "${reverse_order[@]}"; do
        info "准备停止服务: $service"
        stop_service "$service" true
        update_service_status "$service" "$STATUS_STOPPED"
    done

    success "所有服务停止完成"
}

# 更新服务状态
update_service_status() {
    local service_name="$1"
    local status="$2"
    local timestamp=$(date -Iseconds)

    local status_file="$LOG_DIR/service_status.json"

    # 创建或更新状态文件
    if [[ ! -f "$status_file" ]]; then
        cat > "$status_file" << EOF
{
    "services": {}
}
EOF
    fi

    # 使用 jq 更新状态（如果可用）
    if command -v jq &> /dev/null; then
        jq ".services.\"$service_name\" = { \"status\": \"$status\", \"last_updated\": \"$timestamp\" }" \
           "$status_file" > "${status_file}.tmp" && mv "${status_file}.tmp" "$status_file"
    else
        # 简化实现
        local temp_file=$(mktemp)
        grep -v "\"$service_name\"" "$status_file" > "$temp_file" 2>/dev/null || true
        echo "\"$service_name\": { \"status\": \"$status\", \"last_updated\": \"$timestamp\" }" >> "$temp_file"
        mv "$temp_file" "$status_file"
    fi

    info "服务状态更新: $service_name -> $status"
}

# 故障转移处理
handle_service_failure() {
    local failed_service="$1"
    local error_message="$2"

    error "服务故障检测: $failed_service - $error_message"

    # 根据服务重要性决定处理策略
    case "$failed_service" in
        "docker")
            error "关键服务故障: Docker，尝试紧急恢复"
            emergency_docker_recovery
            ;;
        "ollama")
            warn "核心服务故障: Ollama，尝试重启"
            restart_service "ollama"
            ;;
        "openwebui")
            warn "用户界面服务故障，尝试恢复"
            restart_service "openwebui"
            ;;
        *)
            info "非关键服务故障: $failed_service，记录日志"
            ;;
    esac

    # 通知监控系统
    notify_monitoring_system "$failed_service" "failure" "$error_message"
}

# Docker 紧急恢复
emergency_docker_recovery() {
    warn "执行 Docker 紧急恢复..."

    # 强制清理 Docker
    docker system prune -f 2>/dev/null || true

    # 重启 Docker 服务
    systemctl restart docker || {
        error "Docker 服务重启失败，需要手动干预"
        return 1
    }

    # 等待 Docker 就绪
    sleep 10

    if systemctl is-active --quiet docker; then
        success "Docker 紧急恢复成功"
        return 0
    else
        error "Docker 紧急恢复失败"
        return 1
    fi
}

# 通知监控系统
notify_monitoring_system() {
    local service="$1"
    local event_type="$2"
    local message="$3"

    # 发送到监控端点
    local monitoring_url="http://localhost:9090/api/events"

    curl -X POST "$monitoring_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"service\": \"$service\",
            \"event_type\": \"$event_type\",
            \"message\": \"$message\",
            \"timestamp\": \"$(date -Iseconds)\",
            \"severity\": \"error\"
        }" 2>/dev/null || true

    info "监控系统已通知: $service - $event_type"
}

# 负载均衡管理
manage_load_balancing() {
    local service_name="$1"
    local action="$2"  # add/remove/balance

    info "管理负载均衡: $service_name - $action"

    case "$service_name" in
        "ollama")
            manage_ollama_load_balancing "$action"
            ;;
        "openwebui")
            manage_openwebui_load_balancing "$action"
            ;;
        *)
            warn "负载均衡不支持的服务: $service_name"
            ;;
    esac
}

# Ollama 负载均衡管理
manage_ollama_load_balancing() {
    local action="$1"

    case "$action" in
        "add")
            # 启动额外的 Ollama 实例
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.scale.yml" \
                up -d --scale ollama-service=2 || {
                error "Ollama 扩展失败"
                return 1
            }
            ;;
        "remove")
            # 缩减 Ollama 实例
            docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.scale.yml" \
                up -d --scale ollama-service=1 || {
                error "Ollama 缩减失败"
                return 1
            }
            ;;
        "balance")
            # 执行负载均衡
            info "执行 Ollama 负载均衡"
            ;;
    esac
}

# 服务发现
discover_services() {
    info "执行服务发现..."

    local discovered_services=()

    # 发现 Docker 容器服务
    if command -v docker &> /dev/null; then
        while IFS= read -r container; do
            if [[ -n "$container" ]]; then
                discovered_services+=("docker:$container")
            fi
        done < <(docker ps --format "{{.Names}}" 2>/dev/null)
    fi

    # 发现系统服务
    local system_services=("docker" "nginx" "redis")
    for service in "${system_services[@]}"; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            discovered_services+=("system:$service")
        fi
    done

    # 发现进程服务
    local process_services=("python" "node" "java")
    for proc in "${process_services[@]}"; do
        if pgrep -x "$proc" > /dev/null; then
            discovered_services+=("process:$proc")
        fi
    done

    printf '%s\n' "${discovered_services[@]}"
}

# 生成编排报告
generate_orchestration_report() {
    local report_file="$LOG_DIR/orchestration_report_$(date +%Y%m%d_%H%M%S).json"

    local services=($(discover_services))
    local status_info="{}"

    if [[ -f "$LOG_DIR/service_status.json" ]]; then
        status_info=$(cat "$LOG_DIR/service_status.json")
    fi

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "orchestration_version": "1.0",
    "discovered_services": [
        $(printf '"%s",' "${services[@]}" | sed 's/,$//')
    ],
    "service_status": $status_info,
    "system_health": {
        "cpu_usage": "$(top -l 1 | grep -E "^CPU" | awk '{print $3}' || echo "unknown")",
        "memory_usage": "$(free | awk 'NR==2{printf "%.2f%%", $3*100/$2}' || echo "unknown")",
        "disk_usage": "$(df / | awk 'NR==2{print $5}' || echo "unknown")"
    },
    "recommendations": [
        "定期检查服务依赖关系",
        "监控服务健康状态",
        "优化服务启动参数"
    ]
}
EOF

    echo "$report_file"
}

# 使用说明
show_usage() {
    cat << EOF
AI-STACK 智能服务编排器

用法: $0 [选项]

选项:
    start [SERVICE]      启动所有服务或指定服务
    stop [SERVICE]       停止所有服务或指定服务
    restart [SERVICE]    重启所有服务或指定服务
    status [SERVICE]     检查服务状态
    --discover           执行服务发现
    --dependencies       显示服务依赖关系
    --load-balance SERVICE ACTION  管理负载均衡
    --report             生成编排报告
    --health-check       执行全面健康检查
    --help               显示此帮助信息

示例:
    $0 start             启动所有服务
    $0 stop ollama       停止 Ollama 服务
    $0 status            检查所有服务状态
    $0 --discover        发现运行中的服务
    $0 --report          生成编排报告

EOF
}

# 主函数
main() {
    local command=""
    local service_name=""
    local load_balance_action=""

    # 创建必要目录
    mkdir -p "$LOG_DIR"

    # 获取锁
    acquire_lock

    # 解析参数
    case "${1:-}" in
        start|stop|restart|status)
            command="$1"
            service_name="${2:-}"
            ;;
        --discover)
            discover_services
            exit 0
            ;;
        --dependencies)
            load_dependency_graph
            exit 0
            ;;
        --load-balance)
            if [[ -z "${2:-}" || -z "${3:-}" ]]; then
                error "需要指定服务和操作"
                show_usage
                exit 1
            fi
            manage_load_balancing "$2" "$3"
            exit 0
            ;;
        --report)
            generate_orchestration_report
            exit 0
            ;;
        --health-check)
            # 执行全面健康检查
            for service in $(calculate_startup_order ""); do
                check_service_health "$service" || error "服务健康检查失败: $service"
            done
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [[ -z "${1:-}" ]]; then
                show_usage
                exit 1
            else
                error "未知命令: $1"
                show_usage
                exit 1
            fi
            ;;
    esac

    # 执行命令
    case "$command" in
        start)
            if [[ -z "$service_name" ]]; then
                start_all_services
            else
                start_service "$service_name"
            fi
            ;;
        stop)
            if [[ -z "$service_name" ]]; then
                stop_all_services
            else
                stop_service "$service_name"
            fi
            ;;
        restart)
            if [[ -z "$service_name" ]]; then
                stop_all_services
                sleep 2
                start_all_services
            else
                restart_service "$service_name"
            fi
            ;;
        status)
            if [[ -z "$service_name" ]]; then
                for service in $(calculate_startup_order ""); do
                    if check_service_health "$service"; then
                        success "$service: 运行正常"
                    else
                        error "$service: 运行异常"
                    fi
                done
            else
                check_service_health "$service_name"
            fi
            ;;
    esac

    # 生成报告
    generate_orchestration_report > /dev/null

    # 释放锁
    release_lock
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi