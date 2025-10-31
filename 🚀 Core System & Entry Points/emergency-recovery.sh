#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 紧急恢复系统
# 文件: 8. emergency-recovery.sh
# 功能: 系统崩溃恢复、数据修复、灾难恢复、自动修复
#

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly BACKUP_DIR="$ROOT_DIR/backups/emergency_backups"
readonly CONFIG_DIR="$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]"
readonly LOG_DIR="$ROOT_DIR/logs"
readonly RECOVERY_LOG="$LOG_DIR/recovery.log"
readonly CACHE_DIR="$ROOT_DIR/cache/recovery_cache"
readonly RECOVERY_CONFIG="$CONFIG_DIR/global/17. recovery-policy.yaml"
readonly LOCK_FILE="/tmp/ai-stack-emergency-recovery.lock"

# 恢复策略常量
readonly RECOVERY_LEVEL_MINIMAL="minimal"
readonly RECOVERY_LEVEL_STANDARD="standard"
readonly RECOVERY_LEVEL_FULL="full"

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

    echo -e "${level}: ${message}" | tee -a "$RECOVERY_LOG"
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
        error "紧急恢复系统异常退出，退出码: $exit_code"
    fi
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
    exit $exit_code
}

# 锁管理
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            error "另一个恢复进程正在运行 (PID: $pid)"
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

# 加载恢复策略
load_recovery_policy() {
    if [[ ! -f "$RECOVERY_CONFIG" ]]; then
        warn "恢复策略配置文件不存在，使用默认策略"
        cat > "$RECOVERY_CONFIG" << EOF
# AI-STACK 紧急恢复策略
recovery_policy:
  auto_recovery: true
  recovery_level: "standard"
  backup_retention_days: 7
  data_repair_attempts: 3
  emergency_contacts: []

component_recovery:
  docker:
    priority: 1
    auto_restart: true
    repair_commands:
      - "docker system prune -f"
      - "systemctl restart docker"

  ollama:
    priority: 2
    auto_restart: true
    repair_commands:
      - "docker-compose restart ollama-service"
      - "docker system prune -f"

  database:
    priority: 1
    auto_repair: true
    backup_before_repair: true

  configuration:
    priority: 3
    restore_from_backup: true
    validate_after_restore: true
EOF
    fi

    # 解析策略配置
    local policy_content=$(cat "$RECOVERY_CONFIG")
    echo "$policy_content"
}

# 系统健康诊断
diagnose_system_health() {
    info "开始系统健康诊断..."

    local diagnostics=()
    local critical_issues=0
    local warning_issues=0

    # 1. 检查 Docker 服务
    if ! systemctl is-active --quiet docker 2>/dev/null; then
        diagnostics+=("critical:Docker 服务未运行")
        ((critical_issues++))
    elif ! docker info > /dev/null 2>&1; then
        diagnostics+=("critical:Docker 守护进程无响应")
        ((critical_issues++))
    fi

    # 2. 检查磁盘空间
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 95 ]]; then
        diagnostics+=("critical:磁盘空间严重不足: ${disk_usage}%")
        ((critical_issues++))
    elif [[ $disk_usage -gt 85 ]]; then
        diagnostics+=("warning:磁盘空间不足: ${disk_usage}%")
        ((warning_issues++))
    fi

    # 3. 检查内存使用
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $memory_usage -gt 95 ]]; then
        diagnostics+=("warning:内存使用率过高: ${memory_usage}%")
        ((warning_issues++))
    fi

    # 4. 检查关键服务
    local critical_services=("ollama" "openwebui" "vector-db")
    for service in "${critical_services[@]}"; do
        if ! check_service_health "$service"; then
            diagnostics+=("critical:服务异常: $service")
            ((critical_issues++))
        fi
    done

    # 5. 检查网络连接
    if ! ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; then
        diagnostics+=("warning:网络连接异常")
        ((warning_issues++))
    fi

    # 6. 检查配置文件完整性
    if ! validate_configuration_integrity; then
        diagnostics+=("critical:配置文件损坏")
        ((critical_issues++))
    fi

    # 生成诊断报告
    local diagnosis_report="{
        \"timestamp\": \"$(date -Iseconds)\",
        \"critical_issues\": $critical_issues,
        \"warning_issues\": $warning_issues,
        \"overall_status\": \"$([[ $critical_issues -eq 0 ]] && echo "degraded" || echo "critical")\",
        \"diagnostics\": ["

    for diagnostic in "${diagnostics[@]}"; do
        local level="${diagnostic%:*}"
        local message="${diagnostic#*:}"
        diagnosis_report+="{\"level\": \"$level\", \"message\": \"$message\"},"
    done

    diagnosis_report="${diagnosis_report%,}]}"

    echo "$diagnosis_report"
}

# 验证配置文件完整性
validate_configuration_integrity() {
    local critical_configs=(
        "$CONFIG_DIR/global/14. resource-policy.yaml"
        "$CONFIG_DIR/global/15. service-registry.yaml"
        "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml"
    )

    for config in "${critical_configs[@]}"; do
        if [[ ! -f "$config" ]]; then
            error "关键配置文件缺失: $config"
            return 1
        fi

        # 简单的语法检查（YAML）
        if grep -q ".*:" "$config" && ! grep -q "---" "$config" 2>/dev/null; then
            error "配置文件语法可能有问题: $config"
            return 1
        fi
    done

    return 0
}

# 紧急备份创建
create_emergency_backup() {
    local backup_type="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S_emergency')
    local backup_path="$BACKUP_DIR/$timestamp"

    info "创建紧急备份: $backup_type -> $backup_path"

    mkdir -p "$backup_path"

    case "$backup_type" in
        "config")
            # 备份配置文件
            cp -r "$CONFIG_DIR" "$backup_path/config" 2>/dev/null || true
            ;;
        "data")
            # 备份数据文件
            local data_dirs=("cache" "data" "models")
            for dir in "${data_dirs[@]}"; do
                if [[ -d "$ROOT_DIR/$dir" ]]; then
                    cp -r "$ROOT_DIR/$dir" "$backup_path/" 2>/dev/null || true
                fi
            done
            ;;
        "full")
            # 完整备份
            cp -r "$CONFIG_DIR" "$backup_path/config" 2>/dev/null || true
            find "$ROOT_DIR" -maxdepth 2 -type d -name "cache" -o -name "data" -o -name "models" | \
                xargs -I {} cp -r {} "$backup_path/" 2>/dev/null || true
            ;;
    esac

    # 创建备份元数据
    cat > "$backup_path/backup_metadata.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "type": "$backup_type",
    "emergency": true,
    "reason": "pre_recovery_backup"
}
EOF

    echo "$backup_path"
}

# 数据修复功能
repair_corrupted_data() {
    local data_type="$1"

    info "修复损坏数据: $data_type"

    case "$data_type" in
        "vector-db")
            repair_vector_database
            ;;
        "config")
            repair_configuration_files
            ;;
        "models")
            repair_model_files
            ;;
        "docker")
            repair_docker_environment
            ;;
        *)
            error "未知数据类型: $data_type"
            return 1
            ;;
    esac
}

# 修复向量数据库
repair_vector_database() {
    warn "修复向量数据库..."

    # 停止向量数据库服务
    docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
        stop qdrant-service 2>/dev/null || true

    # 备份数据
    local backup_path=$(create_emergency_backup "data")

    # 尝试修复（具体实现取决于使用的向量数据库）
    if [[ -d "$ROOT_DIR/data/qdrant" ]]; then
        # 检查并修复权限
        chmod -R 755 "$ROOT_DIR/data/qdrant" 2>/dev/null || true

        # 检查磁盘空间
        local available_space=$(df "$ROOT_DIR/data/qdrant" | awk 'NR==2 {print $4}')
        if [[ $available_space -lt 1048576 ]]; then
            error "磁盘空间不足，无法修复向量数据库"
            return 1
        fi
    fi

    # 重启服务
    docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
        up -d qdrant-service || {
        error "向量数据库重启失败"
        return 1
    }

    success "向量数据库修复完成"
}

# 修复配置文件
repair_configuration_files() {
    warn "修复配置文件..."

    # 备份当前配置
    local backup_path=$(create_emergency_backup "config")

    # 检查默认配置是否存在
    local default_configs=(
        "$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]/defaults"
        "$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]/templates"
    )

    for default_dir in "${default_configs[@]}"; do
        if [[ -d "$default_dir" ]]; then
            # 从默认配置恢复
            cp -r "$default_dir"/* "$CONFIG_DIR/" 2>/dev/null || true
        fi
    done

    # 验证配置完整性
    if validate_configuration_integrity; then
        success "配置文件修复完成"
        return 0
    else
        error "配置文件修复失败"
        return 1
    fi
}

# 修复模型文件
repair_model_files() {
    warn "修复模型文件..."

    local model_dir="$ROOT_DIR/models"

    if [[ ! -d "$model_dir" ]]; then
        mkdir -p "$model_dir"
        success "模型目录创建完成"
        return 0
    fi

    # 检查模型文件完整性
    local corrupted_models=()
    for model_file in "$model_dir"/*; do
        if [[ -f "$model_file" ]]; then
            local file_size=$(stat -f%z "$model_file" 2>/dev/null || stat -c%s "$model_file" 2>/dev/null || echo "0")
            if [[ $file_size -eq 0 ]]; then
                corrupted_models+=("$model_file")
            fi
        fi
    done

    # 重新下载损坏的模型
    for corrupted_model in "${corrupted_models[@]}"; do
        local model_name=$(basename "$corrupted_model")
        warn "重新下载损坏的模型: $model_name"

        # 调用模型下载脚本
        if [[ -f "$ROOT_DIR/🤖 AI Core Engine [预置文件: 38个]/models/download-model.sh" ]]; then
            "$ROOT_DIR/🤖 AI Core Engine [预置文件: 38个]/models/download-model.sh" "$model_name" || {
                error "模型下载失败: $model_name"
            }
        fi
    done

    success "模型文件修复完成"
}

# 修复 Docker 环境
repair_docker_environment() {
    warn "修复 Docker 环境..."

    # 停止所有容器
    docker stop $(docker ps -q) 2>/dev/null || true

    # 清理 Docker 系统
    docker system prune -f 2>/dev/null || {
        error "Docker 系统清理失败"
        return 1
    }

    # 重启 Docker 服务
    systemctl restart docker || {
        error "Docker 服务重启失败"
        return 1
    }

    # 等待 Docker 就绪
    local max_wait=30
    local wait_interval=2
    local waited=0

    while [[ $waited -lt $max_wait ]]; do
        if docker info > /dev/null 2>&1; then
            success "Docker 环境修复完成"
            return 0
        fi
        sleep $wait_interval
        ((waited+=wait_interval))
    done

    error "Docker 环境修复超时"
    return 1
}

# 灾难恢复程序
disaster_recovery_procedure() {
    local recovery_level="${1:-$RECOVERY_LEVEL_STANDARD}"

    error "启动灾难恢复程序，级别: $recovery_level"

    # 创建紧急备份
    local emergency_backup=$(create_emergency_backup "full")

    # 根据恢复级别执行不同策略
    case "$recovery_level" in
        "$RECOVERY_LEVEL_MINIMAL")
            minimal_recovery
            ;;
        "$RECOVERY_LEVEL_STANDARD")
            standard_recovery
            ;;
        "$RECOVERY_LEVEL_FULL")
            full_recovery
            ;;
        *)
            error "未知恢复级别: $recovery_level"
            return 1
            ;;
    esac

    # 验证恢复结果
    if validate_recovery_result; then
        success "灾难恢复完成"
        return 0
    else
        error "灾难恢复未完全成功"
        return 1
    fi
}

# 最小化恢复
minimal_recovery() {
    info "执行最小化恢复..."

    # 只恢复核心服务
    local core_services=("docker" "ollama")

    for service in "${core_services[@]}"; do
        if ! repair_corrupted_data "$service"; then
            error "核心服务恢复失败: $service"
            return 1
        fi
    done

    success "最小化恢复完成"
}

# 标准恢复
standard_recovery() {
    info "执行标准恢复..."

    # 恢复所有关键组件
    local critical_components=("docker" "config" "vector-db" "ollama")

    for component in "${critical_components[@]}"; do
        if ! repair_corrupted_data "$component"; then
            error "关键组件恢复失败: $component"
            # 继续尝试其他组件
        fi
    done

    # 重启核心服务
    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/7. service-orchestrator.sh" start

    success "标准恢复完成"
}

# 完整恢复
full_recovery() {
    info "执行完整恢复..."

    # 完整系统恢复
    local all_components=("docker" "config" "vector-db" "models" "ollama" "openwebui")

    for component in "${all_components[@]}"; do
        info "恢复组件: $component"
        repair_corrupted_data "$component" || {
            warn "组件恢复遇到问题: $component"
        }
    done

    # 完整系统重启
    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/7. service-orchestrator.sh" restart

    # 数据重新索引
    rebuild_system_indexes

    success "完整恢复完成"
}

# 重建系统索引
rebuild_system_indexes() {
    info "重建系统索引..."

    # 重建向量数据库索引
    if curl -s -X POST http://localhost:6333/collections/rag/snapshots > /dev/null 2>&1; then
        info "向量数据库索引重建中..."
    fi

    # 重建搜索索引
    if [[ -f "$ROOT_DIR/🔍 Smart Search & RAG Engine [预置文件: 18个]/rebuild-indexes.sh" ]]; then
        "$ROOT_DIR/🔍 Smart Search & RAG Engine [预置文件: 18个]/rebuild-indexes.sh" || {
            warn "搜索索引重建遇到问题"
        }
    fi

    success "系统索引重建完成"
}

# 验证恢复结果
validate_recovery_result() {
    info "验证恢复结果..."

    local validation_passed=0
    local validation_failed=0

    # 验证核心服务
    local core_services=("docker" "ollama" "openwebui")
    for service in "${core_services[@]}"; do
        if check_service_health "$service"; then
            ((validation_passed++))
        else
            ((validation_failed++))
        fi
    done

    # 验证磁盘空间
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 90 ]]; then
        ((validation_passed++))
    else
        ((validation_failed++))
    fi

    # 验证配置文件
    if validate_configuration_integrity; then
        ((validation_passed++))
    else
        ((validation_failed++))
    fi

    # 生成验证报告
    local validation_report="{
        \"timestamp\": \"$(date -Iseconds)\",
        \"passed_checks\": $validation_passed,
        \"failed_checks\": $validation_failed,
        \"success_rate\": \"$(echo "scale=2; $validation_passed * 100 / ($validation_passed + $validation_failed)" | bc)%\",
        \"overall_status\": \"$([[ $validation_failed -eq 0 ]] && echo "success" || echo "degraded")\"
    }"

    echo "$validation_report" > "$CACHE_DIR/recovery_validation_$(date +%Y%m%d_%H%M%S).json"

    if [[ $validation_failed -eq 0 ]]; then
        success "恢复验证完全通过"
        return 0
    else
        warn "恢复验证部分通过: $validation_passed/$((validation_passed + validation_failed))"
        return 1
    fi
}

# 自动修复循环
auto_repair_loop() {
    local check_interval=${1:-300}  # 默认5分钟检查一次

    info "启动自动修复监控，检查间隔: ${check_interval}秒"

    while true; do
        acquire_lock

        # 执行系统诊断
        local diagnosis=$(diagnose_system_health)
        local overall_status=$(echo "$diagnosis" | grep -o '"overall_status":"[^"]*' | cut -d'"' -f4)

        case "$overall_status" in
            "critical")
                warn "检测到严重系统问题，执行紧急恢复"
                disaster_recovery_procedure "standard"
                ;;
            "degraded")
                info "检测到系统降级，执行标准修复"
                standard_recovery
                ;;
            "healthy")
                info "系统状态健康，无需修复"
                ;;
        esac

        release_lock
        sleep "$check_interval"
    done
}

# 恢复点创建
create_recovery_point() {
    local point_name="${1:-manual_$(date +%Y%m%d_%H%M%S)}"
    local recovery_point_dir="$BACKUP_DIR/recovery_points/$point_name"

    info "创建恢复点: $point_name"

    mkdir -p "$recovery_point_dir"

    # 备份关键数据
    local critical_paths=(
        "$CONFIG_DIR"
        "$ROOT_DIR/data"
        "$ROOT_DIR/models"
        "$ROOT_DIR/cache"
    )

    for path in "${critical_paths[@]}"; do
        if [[ -d "$path" ]]; then
            cp -r "$path" "$recovery_point_dir/" 2>/dev/null || true
        fi
    done

    # 创建恢复点元数据
    cat > "$recovery_point_dir/recovery_point.json" << EOF
{
    "name": "$point_name",
    "timestamp": "$(date -Iseconds)",
    "version": "$(cat "$ROOT_DIR/version.info" 2>/dev/null || echo "unknown")",
    "components": ["config", "data", "models", "cache"]
}
EOF

    success "恢复点创建完成: $recovery_point_dir"
    echo "$recovery_point_dir"
}

# 恢复到指定恢复点
restore_to_recovery_point() {
    local point_name="$1"
    local recovery_point_dir="$BACKUP_DIR/recovery_points/$point_name"

    if [[ ! -d "$recovery_point_dir" ]]; then
        error "恢复点不存在: $point_name"
        return 1
    fi

    info "恢复到恢复点: $point_name"

    # 停止所有服务
    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/7. service-orchestrator.sh" stop

    # 恢复数据
    rsync -av "$recovery_point_dir/" "$ROOT_DIR/" || {
        error "数据恢复失败"
        return 1
    }

    # 重启服务
    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/7. service-orchestrator.sh" start

    success "恢复点恢复完成: $point_name"
}

# 使用说明
show_usage() {
    cat << EOF
AI-STACK 紧急恢复系统

用法: $0 [选项]

选项:
    --diagnose                  执行系统健康诊断
    --repair COMPONENT          修复指定组件
    --disaster-recovery [LEVEL] 执行灾难恢复 (minimal|standard|full)
    --auto-repair [INTERVAL]    启动自动修复监控
    --create-recovery-point [NAME] 创建恢复点
    --restore-recovery-point NAME 恢复到指定恢复点
    --list-recovery-points      列出所有恢复点
    --emergency-backup TYPE     创建紧急备份 (config|data|full)
    --help                      显示此帮助信息

组件列表:
    docker, config, vector-db, models, ollama, openwebui

示例:
    $0 --diagnose               诊断系统健康
    $0 --repair docker          修复 Docker 环境
    $0 --disaster-recovery full 执行完整灾难恢复
    $0 --auto-repair 300        自动修复监控（300秒间隔）
    $0 --create-recovery-point pre_update

EOF
}

# 主函数
main() {
    local command=""
    local argument=""
    local second_argument=""

    # 创建必要目录
    mkdir -p "$BACKUP_DIR" "$LOG_DIR" "$CACHE_DIR" "$BACKUP_DIR/recovery_points"

    # 解析参数
    case "${1:-}" in
        --diagnose)
            command="diagnose"
            ;;
        --repair)
            command="repair"
            argument="${2:-}"
            ;;
        --disaster-recovery)
            command="disaster_recovery"
            argument="${2:-standard}"
            ;;
        --auto-repair)
            command="auto_repair"
            argument="${2:-300}"
            ;;
        --create-recovery-point)
            command="create_recovery_point"
            argument="${2:-}"
            ;;
        --restore-recovery-point)
            command="restore_recovery_point"
            argument="${2:-}"
            ;;
        --list-recovery-points)
            command="list_recovery_points"
            ;;
        --emergency-backup)
            command="emergency_backup"
            argument="${2:-full}"
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

    # 获取锁
    acquire_lock

    # 加载恢复策略
    load_recovery_policy > /dev/null

    # 执行命令
    case "$command" in
        "diagnose")
            diagnose_system_health
            ;;
        "repair")
            if [[ -z "$argument" ]]; then
                error "需要指定修复组件"
                show_usage
                exit 1
            fi
            repair_corrupted_data "$argument"
            ;;
        "disaster_recovery")
            disaster_recovery_procedure "$argument"
            ;;
        "auto_repair")
            auto_repair_loop "$argument"
            ;;
        "create_recovery_point")
            create_recovery_point "$argument"
            ;;
        "restore_recovery_point")
            if [[ -z "$argument" ]]; then
                error "需要指定恢复点名称"
                show_usage
                exit 1
            fi
            restore_to_recovery_point "$argument"
            ;;
        "list_recovery_points")
            find "$BACKUP_DIR/recovery_points" -name "recovery_point.json" -exec dirname {} \; | xargs -I {} basename {}
            ;;
        "emergency_backup")
            create_emergency_backup "$argument"
            ;;
    esac

    # 释放锁
    release_lock
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi