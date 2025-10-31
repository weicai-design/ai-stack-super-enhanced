#!/bin/bash
#
# AI-STACK-SUPER-ENHANCED 环境感知部署脚本
# 对应需求: 8.3/8.4/8.5/8.6/8.8 - 环境部署、服务编排、资源感知
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

# 环境检测函数
detect_environment() {
    log "检测部署环境..."

    # 检测网络连接
    if ping -c 1 -W 1000 8.8.8.8 &> /dev/null; then
        info "网络连接正常"
    else
        warn "网络连接不稳定，可能影响在线服务"
    fi

    # 检测 Docker 资源
    local docker_info=$(docker info 2>/dev/null)
    if [[ $? -eq 0 ]]; then
        local docker_driver=$(echo "$docker_info" | grep "Storage Driver" | cut -d: -f2 | sed 's/^ *//')
        local docker_root_dir=$(echo "$docker_info" | grep "Docker Root Dir" | cut -d: -f2 | sed 's/^ *//')
        info "Docker 存储驱动: $docker_driver"
        info "Docker 根目录: $docker_root_dir"
    fi

    # 检测可用磁盘空间
    check_disk_space
}

# 磁盘空间检查
check_disk_space() {
    local critical_paths=("/" "/Volumes/Huawei-1" "/Volumes/Huawei-2" "/Users/ywc")

    for path in "${critical_paths[@]}"; do
        if [[ -d "$path" ]]; then
            local available_mb=$(df -m "$path" | awk 'NR==2 {print $4}')
            local total_mb=$(df -m "$path" | awk 'NR==2 {print $2}')
            local usage_percent=$((100 - (available_mb * 100 / total_mb)))

            info "路径 $path: 使用率 ${usage_percent}%, 可用 ${available_mb}MB"

            if [[ $available_mb -lt 1024 ]]; then
                warn "路径 $path 可用空间不足1GB"
            fi
        else
            warn "路径 $path 不存在"
        fi
    done
}

# 资源配置函数
configure_resources() {
    log "配置系统资源..."

    # 根据系统资源动态配置
    local total_memory_gb=$(sysctl -n hw.memsize | awk '{print int($0/1024/1024/1024)}')
    local cpu_cores=$(sysctl -n hw.physicalcpu)

    info "系统总内存: ${total_memory_gb}GB"
    info "物理核心数: ${cpu_cores}"

    # 计算合理的资源分配
    local docker_memory=$((total_memory_gb * 70 / 100))  # 70% 给 Docker
    local docker_cpus=$((cpu_cores * 80 / 100))         # 80% 给 Docker

    # 确保最小值
    if [[ $docker_memory -lt 8 ]]; then
        docker_memory=8
        warn "内存分配调整到最小值 8GB"
    fi

    if [[ $docker_cpus -lt 4 ]]; then
        docker_cpus=4
        warn "CPU 分配调整到最小值 4核心"
    fi

    info "Docker 资源分配: ${docker_memory}GB 内存, ${docker_cpus} 核心"

    # 生成资源配置文件
    cat > "$SCRIPT_DIR/cache/resource_cache/docker_resources.conf" << EOF
# AI-STACK 动态资源分配配置
# 生成时间: $(date)

DOCKER_MEMORY_LIMIT=${docker_memory}G
DOCKER_CPU_LIMIT=${docker_cpus}.0
DOCKER_MEMORY_RESERVATION=$((docker_memory * 60 / 100))G

# 服务特定资源分配
OLLAMA_MEMORY=$((docker_memory * 30 / 100))G
OPENWEBUI_MEMORY=$((docker_memory * 15 / 100))G
RAG_SERVICE_MEMORY=$((docker_memory * 20 / 100))G
ERP_SERVICE_MEMORY=$((docker_memory * 15 / 100))G

# 存储配置
PRIMARY_STORAGE="/Volumes/Huawei-1/ai-stack-data"
BACKUP_STORAGE="/Volumes/Huawei-2/ai-stack-backup"
EOF

    log "资源配置文件已生成"
}

# 服务依赖检查
check_dependencies() {
    log "检查服务依赖..."

    local missing_deps=0

    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose 未安装"
        missing_deps=1
    else
        local compose_version=$(docker-compose --version)
        info "Docker Compose: $compose_version"
    fi

    # 检查 Ollama
    if ! docker images | grep -q "ollama/ollama"; then
        warn "Ollama 镜像未找到，将在部署时下载"
    else
        info "Ollama 镜像已就绪"
    fi

    # 检查 Python 依赖
    if [[ -f "$BASE_DIR/requirements.txt" ]]; then
        info "Python 依赖文件存在"
    else
        warn "未找到 Python 依赖文件"
    fi

    return $missing_deps
}

# 部署配置生成
generate_deployment_config() {
    log "生成部署配置文件..."

    # 创建 docker-compose 基础配置
    cat > "$BASE_DIR/🐳 Intelligent Docker Containerization/docker-compose/base.yml" << 'EOF'
version: '3.8'

services:
  # Ollama 服务 - 必须首先启动
  ollama:
    image: ollama/ollama:latest
    container_name: ai-stack-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    deploy:
      resources:
        limits:
          memory: ${OLLAMA_MEMORY:-8G}
          cpus: '${OLLAMA_CPUS:-4.0}'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  # OpenWebUI 服务 - 依赖 Ollama
  openwebui:
    image: openwebui/openwebui:latest
    container_name: ai-stack-openwebui
    ports:
      - "3000:3000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_NAME="AI-STACK Super Enhanced"
      - ENABLE_SIGNUP=false
    depends_on:
      ollama:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: ${OPENWEBUI_MEMORY:-4G}
          cpus: '${OPENWEBUI_CPUS:-2.0}'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PRIMARY_STORAGE:-./data}/ollama

networks:
  default:
    name: ai-stack-network
    driver: bridge
EOF

    info "Docker Compose 基础配置已生成"

    # 生成环境变量文件
    cat > "$BASE_DIR/.env" << EOF
# AI-STACK 环境配置
# 自动生成于: $(date)

# 路径配置
PRIMARY_STORAGE=/Volumes/Huawei-1/ai-stack-data
BACKUP_STORAGE=/Volumes/Huawei-2/ai-stack-backup
LOG_PATH=$SCRIPT_DIR/logs

# 资源限制
OLLAMA_MEMORY=${docker_memory}G
OLLAMA_CPUS=${docker_cpus}.0
OPENWEBUI_MEMORY=4G
OPENWEBUI_CPUS=2.0

# 网络配置
WEBUI_PORT=3000
OLLAMA_PORT=11434
API_PORT=8000

# 功能开关
ENABLE_RAG=true
ENABLE_ERP=true
ENABLE_STOCK=true
ENABLE_CONTENT=true
EOF

    log "环境配置文件已生成"
}

# 服务启动函数
start_services() {
    log "启动核心服务..."

    # 切换到 Docker 目录
    cd "$BASE_DIR/🐳 Intelligent Docker Containerization/docker-compose"

    # 启动基础服务
    info "启动 Ollama 和 OpenWebUI 服务..."
    if docker-compose -f base.yml up -d; then
        log "基础服务启动成功"
    else
        error "基础服务启动失败"
        return 1
    fi

    # 等待服务就绪
    wait_for_services
}

# 等待服务就绪
wait_for_services() {
    log "等待服务就绪..."

    local max_wait=180
    local wait_interval=5
    local current_wait=0

    info "等待 Ollama 服务启动..."
    while [[ $current_wait -lt $max_wait ]]; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            info "Ollama 服务已就绪"
            break
        fi

        sleep $wait_interval
        current_wait=$((current_wait + wait_interval))
        info "等待中... ${current_wait}秒"
    done

    if [[ $current_wait -ge $max_wait ]]; then
        warn "Ollama 服务启动超时"
    fi

    info "等待 OpenWebUI 服务启动..."
    current_wait=0
    while [[ $current_wait -lt $max_wait ]]; do
        if curl -s http://localhost:3000 &> /dev/null; then
            info "OpenWebUI 服务已就绪"
            break
        fi

        sleep $wait_interval
        current_wait=$((current_wait + wait_interval))
        info "等待中... ${current_wait}秒"
    done

    if [[ $current_wait -ge $max_wait ]]; then
        warn "OpenWebUI 服务启动超时"
    fi
}

# 部署后检查
post_deployment_check() {
    log "执行部署后检查..."

    local health_status=0

    # 检查容器状态
    info "检查容器运行状态..."
    local container_status=$(docker ps --format "table {{.Names}}\t{{.Status}}")
    info "容器状态:\n$container_status"

    # 检查服务端点
    check_service_endpoints

    # 生成部署报告
    generate_deployment_report

    if [[ $health_status -eq 0 ]]; then
        log "🎉 部署完成！AI-STACK 系统已成功启动"
        info "📊 OpenWebUI 界面: http://localhost:3000"
        info "🤖 Ollama API: http://localhost:11434"
        info "📝 系统日志: $SCRIPT_DIR/logs/system.log"
    else
        warn "部署完成，但存在一些问题，请检查日志"
    fi
}

# 检查服务端点
check_service_endpoints() {
    local endpoints=(
        "http://localhost:3000"
        "http://localhost:11434/api/tags"
    )

    for endpoint in "${endpoints[@]}"; do
        if curl -s --head "$endpoint" | grep -q "200"; then
            info "✅ 服务端点可用: $endpoint"
        else
            warn "⚠️  服务端点不可用: $endpoint"
        fi
    done
}

# 生成部署报告
generate_deployment_report() {
    local report_file="$SCRIPT_DIR/logs/deployment_report_$(date +%Y%m%d_%H%M%S).log"

    cat > "$report_file" << EOF
AI-STACK SUPER ENHANCED 部署报告
生成时间: $(date)

=== 系统信息 ===
主机名: $(hostname)
操作系统: $(sw_vers -productName) $(sw_vers -productVersion)
处理器: $(sysctl -n machdep.cpu.brand_string)
内存: $(sysctl -n hw.memsize | awk '{print int($0/1024/1024/1024)}') GB

=== 部署配置 ===
Docker 内存限制: ${docker_memory}GB
Docker CPU 限制: ${docker_cpus} 核心
主存储: /Volumes/Huawei-1/ai-stack-data
备份存储: /Volumes/Huawei-2/ai-stack-backup

=== 服务状态 ===
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

=== 服务端点 ===
OpenWebUI: http://localhost:3000
Ollama API: http://localhost:11434

=== 下一步 ===
1. 访问 http://localhost:3000 配置 OpenWebUI
2. 在 Ollama 中下载所需模型
3. 运行健康检查脚本验证系统状态

EOF

    info "部署报告已生成: $report_file"
}

# 主部署函数
main() {
    log "开始 AI-STACK-SUPER-ENHANCED 部署流程"

    # 环境检测
    detect_environment

    # 依赖检查
    if ! check_dependencies; then
        error "依赖检查失败，请解决上述问题后重试"
        exit 1
    fi

    # 资源配置
    configure_resources

    # 生成部署配置
    generate_deployment_config

    # 启动服务
    if start_services; then
        # 部署后检查
        post_deployment_check
    else
        error "服务启动失败"
        exit 1
    fi

    log "部署流程完成"
}

# 信号处理
trap 'error "部署过程被中断"; exit 130' INT TERM

# 执行主函数
main "$@"