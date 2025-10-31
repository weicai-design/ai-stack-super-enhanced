#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 资源清理与状态保存脚本
# 对应需求: 8.3/8.4/8.5 - 优雅关闭、状态保存、资源清理
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SCRIPT_DIR/logs/system.log"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$SCRIPT_DIR/logs/system.log"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$SCRIPT_DIR/logs/system.log"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> "$SCRIPT_DIR/logs/system.log"
}

# 确认函数
confirm_action() {
    local message="$1"
    local default="${2:-y}"

    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        info "自动确认: $message"
        return 0
    fi

    echo -en "${YELLOW}$message [y/N] ${NC}"
    read -r response

    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 服务停止函数
stop_services() {
    log "停止 AI-STACK 服务..."

    # 切换到 Docker 目录
    cd "$BASE_DIR/🐳 Intelligent Docker Containerization/docker-compose"

    # 停止所有服务
    if [[ -f "base.yml" ]]; then
        info "停止基础服务..."
        docker-compose -f base.yml down
    fi

    # 检查是否有其他相关容器
    local ai_containers=$(docker ps -a --filter "name=ai-stack" --format "{{.Names}}")
    if [[ -n "$ai_containers" ]]; then
        info "停止其他 AI-STACK 容器..."
        echo "$ai_containers" | xargs -r docker stop
        echo "$ai_containers" | xargs -r docker rm
    fi

    # 检查网络
    local ai_network=$(docker network ls --filter "name=ai-stack" --format "{{.Name}}")
    if [[ -n "$ai_network" ]]; then
        info "清理 AI-STACK 网络..."
        echo "$ai_network" | xargs -r docker network rm
    fi

    log "所有服务已停止"
}

# 状态保存函数
save_system_state() {
    log "保存系统状态..."

    local backup_dir="$SCRIPT_DIR/backups/state_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # 保存 Docker 容器状态
    info "保存容器状态..."
    docker ps -a --filter "name=ai-stack" --format "json" > "$backup_dir/containers.json" 2>/dev/null || true

    # 保存卷状态
    info "保存卷状态..."
    docker volume ls --filter "name=ai-stack" --format "json" > "$backup_dir/volumes.json" 2>/dev/null || true

    # 保存网络配置
    info "保存网络配置..."
    docker network ls --filter "name=ai-stack" --format "json" > "$backup_dir/networks.json" 2>/dev/null || true

    # 保存系统配置
    info "保存系统配置..."
    if [[ -f "$BASE_DIR/.env" ]]; then
        cp "$BASE_DIR/.env" "$backup_dir/"
    fi

    # 保存资源使用情况
    info "保存资源使用情况..."
    cat > "$backup_dir/system_stats.json" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "cpu_cores": $(sysctl -n hw.logicalcpu),
    "memory_total": $(sysctl -n hw.memsize),
    "storage_primary": "$(df -h /Volumes/Huawei-1 2>/dev/null | awk 'NR==2 {print $4}' || echo "N/A")",
    "storage_backup": "$(df -h /Volumes/Huawei-2 2>/dev/null | awk 'NR==2 {print $4}' || echo "N/A")"
}
EOF

    # 创建备份元数据
    cat > "$backup_dir/backup_metadata.json" << EOF
{
    "backup_id": "$(uuidgen)",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "type": "system_state",
    "version": "1.0.0",
    "components": [
        "container_state",
        "volume_info",
        "network_config",
        "system_config",
        "resource_stats"
    ]
}
EOF

    info "系统状态已保存到: $backup_dir"
}

# 数据备份函数
backup_user_data() {
    log "备份用户数据..."

    local backup_dir="$SCRIPT_DIR/backups/data_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # 检查数据目录
    local data_dirs=(
        "/Volumes/Huawei-1/ai-stack-data"
        "$BASE_DIR/🚀 Core System & Entry Points/cache"
        "$BASE_DIR/🚀 Core System & Entry Points/logs"
    )

    for data_dir in "${data_dirs[@]}"; do
        if [[ -d "$data_dir" ]]; then
            info "备份数据目录: $data_dir"
            local dir_name=$(basename "$data_dir")
            tar -czf "$backup_dir/${dir_name}_backup.tar.gz" -C "$(dirname "$data_dir")" "$(basename "$data_dir")" 2>/dev/null ||
                warn "备份 $data_dir 时出现问题"
        else
            info "跳过不存在的目录: $data_dir"
        fi
    done

    # 备份配置文件
    info "备份配置文件..."
    find "$BASE_DIR" -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.conf" | \
        grep -v "node_modules" | grep -v ".git" | \
        tar -czf "$backup_dir/config_files.tar.gz" -T - 2>/dev/null || true

    # 创建数据备份元数据
    cat > "$backup_dir/data_metadata.json" << EOF
{
    "backup_id": "$(uuidgen)",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "type": "user_data",
    "version": "1.0.0",
    "data_dirs": [
        "/Volumes/Huawei-1/ai-stack-data",
        "cache",
        "logs"
    ],
    "total_size": "$(du -sh "$backup_dir" | cut -f1)"
}
EOF

    info "用户数据已备份到: $backup_dir"
}

# 资源清理函数
cleanup_resources() {
    log "清理系统资源..."

    # 清理 Docker 资源
    cleanup_docker_resources

    # 清理缓存文件
    cleanup_cache_files

    # 清理临时文件
    cleanup_temp_files

    # 清理日志文件（可选）
    if confirm_action "是否清理旧日志文件？" "n"; then
        cleanup_log_files
    fi
}

# 清理 Docker 资源
cleanup_docker_resources() {
    info "清理 Docker 资源..."

    # 停止所有 AI-STACK 相关容器
    local running_containers=$(docker ps -a --filter "name=ai-stack" --format "{{.ID}}")
    if [[ -n "$running_containers" ]]; then
        info "停止并删除 AI-STACK 容器..."
        echo "$running_containers" | xargs -r docker stop
        echo "$running_containers" | xargs -r docker rm
    fi

    # 删除悬空镜像
    local dangling_images=$(docker images -f "dangling=true" -q)
    if [[ -n "$dangling_images" ]]; then
        info "删除悬空镜像..."
        echo "$dangling_images" | xargs -r docker rmi
    fi

    # 删除未使用的卷
    if confirm_action "是否删除未使用的 Docker 卷？" "n"; then
        local unused_volumes=$(docker volume ls -q -f "dangling=true")
        if [[ -n "$unused_volumes" ]]; then
            info "删除未使用的卷..."
            echo "$unused_volumes" | xargs -r docker volume rm
        fi
    fi

    # 清理构建缓存
    info "清理 Docker 构建缓存..."
    docker builder prune -f
}

# 清理缓存文件
cleanup_cache_files() {
    info "清理缓存文件..."

    local cache_dirs=(
        "$SCRIPT_DIR/cache/resource_cache"
        "$SCRIPT_DIR/cache/model_cache"
        "$SCRIPT_DIR/cache/temp_files"
    )

    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            info "清理缓存目录: $cache_dir"
            find "$cache_dir" -type f -name "*.tmp" -delete
            find "$cache_dir" -type f -name "*.cache" -delete
            find "$cache_dir" -type f -mtime +7 -delete  # 删除7天前的文件
        fi
    done
}

# 清理临时文件
cleanup_temp_files() {
    info "清理临时文件..."

    local temp_dirs=(
        "/tmp/ai-stack"
        "$SCRIPT_DIR/cache/temp_files"
    )

    for temp_dir in "${temp_dirs[@]}"; do
        if [[ -d "$temp_dir" ]]; then
            info "清理临时目录: $temp_dir"
            rm -rf "${temp_dir:?}"/*
        fi
    done
}

# 清理日志文件
cleanup_log_files() {
    info "清理日志文件..."

    local log_dir="$SCRIPT_DIR/logs"

    if [[ -d "$log_dir" ]]; then
        # 保留最近7天的日志
        find "$log_dir" -name "*.log" -type f -mtime +7 -delete
        info "已清理7天前的日志文件"

        # 压缩旧日志
        find "$log_dir" -name "*.log" -type f -mtime +1 -exec gzip {} \;
        info "已压缩1天前的日志文件"
    fi
}

# 系统状态报告
generate_teardown_report() {
    log "生成关闭报告..."

    local report_file="$SCRIPT_DIR/logs/teardown_report_$(date +%Y%m%d_%H%M%S).log"

    cat > "$report_file" << EOF
AI-STACK SUPER ENHANCED 系统关闭报告
生成时间: $(date)

=== 关闭操作摘要 ===
停止时间: $(date)
操作类型: 正常关闭
状态保存: 完成
数据备份: 完成
资源清理: 完成

=== 资源释放情况 ===
释放容器: $(docker ps -a --filter "name=ai-stack" --format "{{.Names}}" | wc -l | tr -d ' ')
释放卷: $(docker volume ls --filter "name=ai-stack" --format "{{.Name}}" | wc -l | tr -d ' ')
释放网络: $(docker network ls --filter "name=ai-stack" --format "{{.Name}}" | wc -l | tr -d ' ')

=== 备份信息 ===
状态备份: $SCRIPT_DIR/backups/state_backup_$(date +%Y%m%d_%H%M%S)
数据备份: $SCRIPT_DIR/backups/data_backup_$(date +%Y%m%d_%H%M%S)

=== 系统状态 ===
内存使用: $(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//') 页空闲
磁盘空间:
$(df -h / /Volumes/Huawei-1 /Volumes/Huawei-2 2>/dev/null | awk '{print $1, $4, $5}' | column -t)

=== 下次启动建议 ===
1. 运行 bootstrap.sh 重新初始化系统
2. 运行 deploy.sh 重新部署服务
3. 检查备份文件完整性

EOF

    info "关闭报告已生成: $report_file"
}

# 优雅关闭函数
graceful_shutdown() {
    log "开始优雅关闭流程..."

    # 保存系统状态
    save_system_state

    # 备份用户数据
    backup_user_data

    # 停止服务
    stop_services

    # 清理资源
    cleanup_resources

    # 生成报告
    generate_teardown_report

    log "🎉 系统优雅关闭完成"
    info "💾 状态和数据已备份到 backups/ 目录"
    info "📋 关闭报告已保存到 logs/ 目录"
}

# 强制关闭函数
force_shutdown() {
    warn "执行强制关闭流程..."

    # 强制停止所有相关容器
    info "强制停止所有 AI-STACK 容器..."
    docker ps -a --filter "name=ai-stack" --format "{{.ID}}" | xargs -r docker rm -f

    # 强制删除网络
    info "强制删除 AI-STACK 网络..."
    docker network ls --filter "name=ai-stack" --format "{{.ID}}" | xargs -r docker network rm -f

    # 清理临时文件
    cleanup_temp_files

    warn "⚠️  强制关闭完成，但可能丢失未保存的状态"
}

# 主函数
main() {
    local force_mode=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--force)
                force_mode=true
                shift
                ;;
            -y|--yes)
                export AUTO_CONFIRM=true
                shift
                ;;
            *)
                error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    log "启动 AI-STACK-SUPER-ENHANCED 关闭流程"

    # 检查 Docker 是否可用
    if ! command -v docker &> /dev/null; then
        error "Docker 不可用，无法执行关闭操作"
        exit 1
    fi

    if [[ "$force_mode" == true ]]; then
        if confirm_action "确定要强制关闭系统吗？这将可能丢失数据。" "n"; then
            force_shutdown
        else
            info "操作已取消"
            exit 0
        fi
    else
        graceful_shutdown
    fi
}

# 信号处理
trap 'warn "关闭过程被中断，执行紧急清理"; force_shutdown; exit 130' INT TERM

# 执行主函数
main "$@"