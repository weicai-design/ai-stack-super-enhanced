#!/bin/bash

# =============================================================================
# AI Stack Super Enhanced - 智能系统引导与硬件检测脚本
# 文件名: 1. bootstrap.sh
# 位置: ai-stack-super-enhanced/🚀 Core System & Entry Points/
# 功能: 系统初始化、硬件检测、环境验证、依赖检查、资源预分配
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义用于输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# 脚本元数据
SCRIPT_NAME="AI Stack Super Enhanced Bootstrap"
SCRIPT_VERSION="1.0.0"
SCRIPT_AUTHOR="AI Stack Development Team"
CONFIG_DIR="/Users/ywc/ai-stack-super-enhanced/⚙️ Configuration Center"

# =============================================================================
# 初始化检查函数
# =============================================================================

check_script_permissions() {
    log "检查脚本执行权限..."
    if [[ $EUID -eq 0 ]]; then
        warn "正在以root权限运行，建议使用普通用户权限"
    fi

    # 检查脚本是否具有执行权限
    if [[ ! -x "$0" ]]; then
        error "脚本没有执行权限，请运行: chmod +x $0"
        exit 1
    fi
}

validate_installation_path() {
    log "验证安装路径..."
    local expected_path="/Users/ywc/ai-stack-super-enhanced"

    if [[ ! -d "$expected_path" ]]; then
        error "安装路径不存在: $expected_path"
        error "请确保AI Stack安装在正确的位置"
        exit 1
    fi

    # 切换到安装目录
    cd "$expected_path" || {
        error "无法切换到安装目录: $expected_path"
        exit 1
    }

    log "安装路径验证成功: $(pwd)"
}

# =============================================================================
# 硬件检测函数
# =============================================================================

detect_mac_hardware() {
    log "检测Mac硬件配置..."

    # 获取系统信息
    local mac_model=$(system_profiler SPHardwareDataType | grep "Model Name" | cut -d: -f2 | sed 's/^ *//')
    local processor=$(sysctl -n machdep.cpu.brand_string)
    local core_count=$(sysctl -n hw.ncpu)
    local memory_gb=$(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024}')
    local graphics=$(system_profiler SPDisplaysDataType | grep "Chipset Model" | cut -d: -f2 | sed 's/^ *//' | head -1)
    local os_version=$(sw_vers -productVersion)

    info "系统型号: $mac_model"
    info "处理器: $processor"
    info "核心数量: $core_count"
    info "内存: ${memory_gb} GB"
    info "图形卡: $graphics"
    info "macOS版本: $os_version"

    # 验证是否符合最低要求
    if [[ $core_count -lt 4 ]]; then
        warn "处理器核心数少于推荐配置(4核心)"
    fi

    if (( $(echo "$memory_gb < 16" | bc -l) )); then
        warn "内存少于推荐配置(16GB)"
    fi
}

detect_storage() {
    log "检测存储配置..."

    # 内置硬盘
    local internal_disk=$(df -h / | tail -1 | awk '{print $4 " (" $2 " total)"}')
    info "内置硬盘剩余空间: $internal_disk"

    # 检查外接硬盘
    local huawei1_mounted=$(df -h | grep -c "Huawei-1" || true)
    local huawei2_mounted=$(df -h | grep -c "Huawei-2" || true)

    if [[ $huawei1_mounted -eq 0 ]]; then
        warn "外接硬盘 Huawei-1 未挂载"
    else
        info "外接硬盘 Huawei-1 已挂载"
    fi

    if [[ $huawei2_mounted -eq 0 ]]; then
        warn "外接硬盘 Huawei-2 未挂载"
    else
        info "外接硬盘 Huawei-2 已挂载"
    fi

    # 检查可用空间
    local available_space=$(df / | tail -1 | awk '{print $4}' | sed 's/G//')
    if [[ $available_space -lt 50 ]]; then
        warn "系统磁盘空间不足50GB，可能影响性能"
    fi
}

# =============================================================================
# 软件依赖检查
# =============================================================================

check_docker() {
    log "检查Docker环境..."

    if ! command -v docker &> /dev/null; then
        error "Docker未安装，请先安装Docker"
        exit 1
    fi

    local docker_version=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    info "Docker版本: $docker_version"

    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        error "Docker服务未运行，请启动Docker"
        exit 1
    fi
}

check_docker_compose() {
    log "检查Docker Compose..."

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose未安装"
        exit 1
    fi

    local compose_version=$(docker-compose --version | cut -d' ' -f3 | sed 's/,//')
    info "Docker Compose版本: $compose_version"
}

check_python() {
    log "检查Python环境..."

    if ! command -v python3 &> /dev/null; then
        error "Python3未安装"
        exit 1
    fi

    local python_version=$(python3 --version | cut -d' ' -f2)
    info "Python版本: $python_version"

    # 检查关键Python包
    local required_packages=("requests" "pyyaml" "psutil")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            warn "Python包缺失: $package"
        fi
    done
}

check_system_tools() {
    log "检查系统工具..."

    local required_tools=("curl" "wget" "git" "tar" "unzip")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            warn "系统工具缺失: $tool"
        else
            local version=$("$tool" --version 2>/dev/null | head -1 | cut -d' ' -f2 || echo "installed")
            info "$tool: $version"
        fi
    done
}

# =============================================================================
# 资源预分配与优化
# =============================================================================

optimize_system_limits() {
    log "优化系统资源限制..."

    # 检查当前限制
    local file_limit=$(ulimit -n)
    info "当前文件描述符限制: $file_limit"

    if [[ $file_limit -lt 65536 ]]; then
        warn "文件描述符限制较低，建议增加到65536"
        warn "请运行: ulimit -n 65536"
    fi

    # 检查Docker资源限制
    local docker_memory=$(docker info 2>/dev/null | grep "Total Memory" | cut -d: -f2 | sed 's/^ *//' || echo "unknown")
    info "Docker可用内存: $docker_memory"
}

preallocate_resources() {
    log "预分配系统资源..."

    # 创建必要的目录结构
    local directories=(
        "logs"
        "backups/config_backup"
        "backups/data_backup"
        "backups/state_backup"
        "cache/resource_cache"
        "cache/model_cache"
        "cache/temp_files"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            info "创建目录: $dir"
        fi
    done

    # 设置目录权限
    chmod -R 755 "logs"
    chmod -R 755 "cache"
}

# =============================================================================
# 内存优化配置 (解决RAG内存使用高的问题)
# =============================================================================

configure_memory_optimization() {
    log "配置内存优化参数..."

    # 根据系统内存智能配置
    local total_memory=$(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024}')
    local available_memory=$(echo "$total_memory * 0.7" | bc -l | cut -d. -f1)  # 使用70%的内存

    info "系统总内存: ${total_memory}GB"
    info "为AI Stack分配内存: ${available_memory}GB"

    # 生成内存配置
    local memory_config="
# 内存优化配置 - 由bootstrap.sh自动生成
memory:
  total_available_gb: $available_memory
  rag_optimization:
    chunk_size: 512
    overlap: 50
    max_concurrent_processing: 2
    vector_cache_size: 1024
  system_reserved_gb: 4
  monitoring_interval: 30
"

    echo "$memory_config" > "cache/resource_cache/memory_config.yaml"
    info "内存配置已保存: cache/resource_cache/memory_config.yaml"
}

# =============================================================================
# 环境验证
# =============================================================================

validate_environment() {
    log "验证运行环境..."

    local issues=0

    # 检查关键服务端口
    local ports=(8080 8081 8082 3000 5432 6379)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            warn "端口 $port 已被占用，可能导致服务启动失败"
            ((issues++))
        fi
    done

    # 检查磁盘inodes
    local inodes_usage=$(df -i / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $inodes_usage -gt 90 ]]; then
        warn "磁盘inodes使用率过高: ${inodes_usage}%"
        ((issues++))
    fi

    if [[ $issues -eq 0 ]]; then
        log "环境验证通过"
    else
        warn "发现 $issues 个潜在问题，请检查上述警告"
    fi
}

# =============================================================================
# 启动准备
# =============================================================================

prepare_startup() {
    log "准备系统启动..."

    # 清理临时文件
    if [[ -d "cache/temp_files" ]]; then
        rm -rf "cache/temp_files"/*
        info "已清理临时文件"
    fi

    # 备份当前配置
    local backup_dir="backups/config_backup/$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "$backup_dir"

    if [[ -d "$CONFIG_DIR" ]]; then
        cp -r "$CONFIG_DIR"/* "$backup_dir/" 2>/dev/null || true
        info "配置已备份到: $backup_dir"
    fi

    # 生成启动标识
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "cache/startup_marker"
    info "启动标识已创建"
}

# =============================================================================
# 主执行流程
# =============================================================================

main() {
    log "=================================================="
    log "AI Stack Super Enhanced - 系统引导启动"
    log "版本: $SCRIPT_VERSION"
    log "作者: $SCRIPT_AUTHOR"
    log "开始时间: $(date)"
    log "=================================================="

    # 执行初始化检查
    check_script_permissions
    validate_installation_path

    # 硬件检测
    detect_mac_hardware
    detect_storage

    # 依赖检查
    check_docker
    check_docker_compose
    check_python
    check_system_tools

    # 资源优化
    optimize_system_limits
    preallocate_resources
    configure_memory_optimization  # 重点解决RAG内存问题

    # 环境验证
    validate_environment

    # 启动准备
    prepare_startup

    log "=================================================="
    log "系统引导完成，可以启动AI Stack服务"
    log "请运行: ./2. deploy.sh"
    log "完成时间: $(date)"
    log "=================================================="

    # 输出下一步提示
    info "下一步操作:"
    info "1. 检查上述警告信息(如有)"
    info "2. 运行部署脚本: ./2. deploy.sh"
    info "3. 监控启动过程: tail -f logs/system.log"
}

# =============================================================================
# 信号处理 (优雅退出)
# =============================================================================

handle_interrupt() {
    echo
    warn "接收到中断信号，正在优雅退出..."
    log "bootstrap.sh 执行被用户中断"
    exit 0
}

handle_terminate() {
    warn "接收到终止信号，正在退出..."
    log "bootstrap.sh 执行被终止"
    exit 1
}

# 注册信号处理器
trap handle_interrupt SIGINT
trap handle_terminate SIGTERM

# =============================================================================
# 脚本入口
# =============================================================================

# 检查是否显示帮助
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "使用方法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --version  显示版本信息"
    echo "  --skip-checks  跳过硬件检查(快速启动)"
    exit 0
fi

if [[ "$1" == "-v" || "$1" == "--version" ]]; then
    echo "$SCRIPT_NAME version $SCRIPT_VERSION"
    exit 0
fi

# 执行主函数
main "$@"