#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 智能增量更新系统
# 文件: 5. update.sh
# 功能: 智能增量更新，支持热更新、版本回滚、依赖检查
#

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROOT_DIR="$(dirname "$SCRIPT_DIR")"
readonly BACKUP_DIR="$ROOT_DIR/backups/update_backups"
readonly CONFIG_DIR="$ROOT_DIR/⚙️ Configuration Center [预置文件: 45个]"
readonly LOG_DIR="$ROOT_DIR/logs"
readonly UPDATE_LOG="$LOG_DIR/update.log"
readonly VERSION_FILE="$ROOT_DIR/version.info"
readonly LOCK_FILE="/tmp/ai-stack-update.lock"

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

    echo -e "${level}: ${message}" | tee -a "$UPDATE_LOG"

    # 系统日志记录
    logger -t "ai-stack-update" "[$level] $message"
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
        error "更新过程异常退出，退出码: $exit_code"
        [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
    fi
    exit $exit_code
}

# 锁管理
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            error "另一个更新进程正在运行 (PID: $pid)"
            exit 1
        else
            warn发现陈旧的锁文件，清理中...
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
}

# 系统检查
check_system_requirements() {
    info "检查系统要求..."

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装"
        return 1
    fi

    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装"
        return 1
    fi

    # 检查磁盘空间
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 1048576 ]]; then  # 小于 1GB
        error "磁盘空间不足，需要至少 1GB 可用空间"
        return 1
    fi

    # 检查内存
    local available_mem=$(free -m | awk 'NR==2 {print $7}')
    if [[ $available_mem -lt 1024 ]]; then  # 小于 1GB
        warn "可用内存较低: ${available_mem}MB，建议至少 1GB"
    fi

    success "系统要求检查通过"
}

# 备份当前系统
backup_current_system() {
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/$backup_timestamp"

    info "创建系统备份: $backup_path"

    mkdir -p "$backup_path"

    # 备份配置文件
    if [[ -d "$CONFIG_DIR" ]]; then
        cp -r "$CONFIG_DIR" "$backup_path/config_backup"
        success "配置文件备份完成"
    fi

    # 备份版本信息
    if [[ -f "$VERSION_FILE" ]]; then
        cp "$VERSION_FILE" "$backup_path/"
    fi

    # 备份 Docker 相关文件
    if [[ -d "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]" ]]; then
        cp -r "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]" \
              "$backup_path/docker_backup"
    fi

    # 创建备份元数据
    cat > "$backup_path/backup_metadata.json" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")",
    "backup_type": "pre_update",
    "components": ["config", "docker", "version_info"]
}
EOF

    echo "$backup_timestamp" > "$BACKUP_DIR/latest_backup"
    success "系统备份完成: $backup_path"
}

# 版本检查
check_version_compatibility() {
    local current_version=$(cat "$VERSION_FILE" 2>/dev/null || echo "0.0.0")
    local target_version=${1:-"latest"}

    info "当前版本: $current_version, 目标版本: $target_version"

    # 版本格式验证
    if ! echo "$current_version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
        warn "当前版本格式异常: $current_version"
        return 0
    fi

    # 简单的版本兼容性检查（可根据需要扩展）
    local major_version=$(echo "$current_version" | cut -d. -f1)
    if [[ $major_version -lt 1 ]]; then
        warn "主要版本升级，请确保兼容性"
    fi

    success "版本兼容性检查通过"
}

# 依赖更新
update_dependencies() {
    info "更新系统依赖..."

    # 更新 Python 依赖
    if [[ -f "$ROOT_DIR/requirements.txt" ]]; then
        info "更新 Python 依赖..."
        pip install -U -r "$ROOT_DIR/requirements.txt" || {
            error "Python 依赖更新失败"
            return 1
        }
    fi

    # 更新 Docker 镜像
    info "更新 Docker 镜像..."
    docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" pull || {
        error "Docker 镜像更新失败"
        return 1
    }

    success "依赖更新完成"
}

# 配置迁移
migrate_configurations() {
    info "迁移配置文件..."

    local backup_timestamp=$(cat "$BACKUP_DIR/latest_backup")
    local backup_path="$BACKUP_DIR/$backup_timestamp"

    if [[ ! -d "$backup_path" ]]; then
        error "备份目录不存在: $backup_path"
        return 1
    fi

    # 智能配置合并（保留用户自定义配置）
    if [[ -d "$backup_path/config_backup" ]]; then
        rsync -av --ignore-existing \
              "$backup_path/config_backup/" \
              "$CONFIG_DIR/" || {
            warn "部分配置文件迁移失败"
        }
    fi

    success "配置迁移完成"
}

# 服务重启
restart_services() {
    info "重启系统服务..."

    # 按正确顺序重启服务
    local services=("docker" "ollama" "openwebui" "ai-stack-core")

    for service in "${services[@]}"; do
        info "重启服务: $service"

        case $service in
            "docker")
                # 确保 Docker 服务运行
                if ! systemctl is-active --quiet docker; then
                    systemctl start docker || {
                        error "Docker 服务启动失败"
                        return 1
                    }
                fi
                ;;
            "ollama")
                # 重启 Ollama 服务
                docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                    restart ollama-service || {
                    error "Ollama 服务重启失败"
                    return 1
                }
                ;;
            "openwebui")
                # 重启 OpenWebUI 服务
                docker-compose -f "$ROOT_DIR/🐳 Intelligent Docker Containerization [预置文件: 28个]/docker-compose/docker-compose.base.yml" \
                    restart openwebui-service || {
                    error "OpenWebUI 服务重启失败"
                    return 1
                }
                ;;
            "ai-stack-core")
                # 重启 AI-STACK 核心服务
                if [[ -f "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/1. bootstrap.sh" ]]; then
                    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/1. bootstrap.sh" --restart || {
                        error "AI-STACK 核心服务重启失败"
                        return 1
                    }
                fi
                ;;
        esac

        # 等待服务就绪
        sleep 5
    done

    success "服务重启完成"
}

# 健康检查
post_update_health_check() {
    info "执行更新后健康检查..."

    local max_retries=10
    local retry_interval=10

    for ((i=1; i<=max_retries; i++)); do
        info "健康检查尝试 $i/$max_retries..."

        # 检查核心服务
        if "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/4. health-check.sh" --quick; then
            success "系统健康检查通过"
            return 0
        fi

        if [[ $i -eq $max_retries ]]; then
            error "健康检查失败，系统可能存在问题"
            return 1
        fi

        warn "健康检查未通过，${retry_interval}秒后重试..."
        sleep $retry_interval
    done
}

# 回滚功能
rollback_update() {
    local backup_timestamp=${1:-$(cat "$BACKUP_DIR/latest_backup" 2>/dev/null)}

    if [[ -z "$backup_timestamp" || ! -d "$BACKUP_DIR/$backup_timestamp" ]]; then
        error "找不到有效的备份用于回滚"
        return 1
    fi

    warn "开始回滚到备份: $backup_timestamp"

    # 停止当前服务
    "$ROOT_DIR/🚀 Core System & Entry Points [预置文件: 28个]/3. teardown.sh" --soft || {
        error "服务停止失败，无法回滚"
        return 1
    }

    # 恢复备份
    local backup_path="$BACKUP_DIR/$backup_timestamp"
    rsync -av --delete "$backup_path/config_backup/" "$CONFIG_DIR/" || {
        error "配置恢复失败"
        return 1
    }

    # 重启服务
    restart_services || {
        error "服务重启失败"
        return 1
    }

    success "系统回滚完成"
}

# 主更新函数
perform_update() {
    local target_version=${1:-"latest"}
    local skip_backup=${2:-false}

    info "开始 AI-STACK 智能增量更新"
    info "目标版本: $target_version"

    # 获取锁
    acquire_lock

    # 预检查
    check_system_requirements || exit 1
    check_version_compatibility "$target_version" || exit 1

    # 备份（除非跳过）
    if [[ "$skip_backup" == "false" ]]; then
        backup_current_system || {
            error "系统备份失败，更新中止"
            exit 1
        }
    fi

    # 执行更新步骤
    local update_steps=(
        "update_dependencies"
        "migrate_configurations"
        "restart_services"
        "post_update_health_check"
    )

    for step in "${update_steps[@]}"; do
        info "执行步骤: $step"
        if ! $step; then
            error "步骤 $step 执行失败"

            # 自动回滚
            if [[ "$skip_backup" == "false" ]]; then
                warn "尝试自动回滚..."
                if rollback_update; then
                    success "自动回滚成功"
                else
                    error "自动回滚失败，需要手动干预"
                fi
            fi

            exit 1
        fi
    done

    # 更新版本信息
    if [[ "$target_version" != "latest" ]]; then
        echo "$target_version" > "$VERSION_FILE"
    fi

    # 清理旧备份（保留最近5个）
    ls -dt "$BACKUP_DIR"/*/ | tail -n +6 | xargs rm -rf 2>/dev/null || true

    success "AI-STACK 更新完成"
}

# 使用说明
show_usage() {
    cat << EOF
AI-STACK 智能增量更新系统

用法: $0 [选项]

选项:
    -v, --version VERSION    指定目标版本 (默认: latest)
    --skip-backup            跳过备份步骤 (不推荐)
    --rollback [TIMESTAMP]   回滚到指定备份 (默认: 最近备份)
    --health-check           只执行健康检查
    --help                   显示此帮助信息

示例:
    $0 -v 1.2.0             更新到版本 1.2.0
    $0 --rollback           回滚到最近备份
    $0 --health-check       执行健康检查

EOF
}

# 主函数
main() {
    local action="update"
    local target_version="latest"
    local skip_backup=false
    local rollback_timestamp=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                target_version="$2"
                shift 2
                ;;
            --skip-backup)
                skip_backup=true
                shift
                ;;
            --rollback)
                action="rollback"
                [[ -n "$2" && ! "$2" =~ ^- ]] && rollback_timestamp="$2" && shift
                shift
                ;;
            --health-check)
                action="health_check"
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

    # 创建必要目录
    mkdir -p "$BACKUP_DIR" "$LOG_DIR"

    # 执行相应操作
    case $action in
        "update")
            perform_update "$target_version" "$skip_backup"
            ;;
        "rollback")
            rollback_update "$rollback_timestamp"
            ;;
        "health_check")
            post_update_health_check
            ;;
    esac

    # 释放锁
    release_lock
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi