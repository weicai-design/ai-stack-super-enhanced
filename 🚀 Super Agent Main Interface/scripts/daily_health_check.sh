#!/bin/bash
# -*- coding: utf-8 -*-
# 日常健康检查脚本（生产级实现）
# 5.3: 依赖检测、磁盘、服务状态

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/health}"
LOG_FILE="$LOG_DIR/health_check_$(date +%Y%m%d_%H%M%S).log"
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

# 服务端口配置
SERVICES=(
    "8000:Super Agent Main Interface"
    "8011:RAG System"
    "8013:ERP System"
    "8014:Stock System"
    "8015:Trend Analysis"
    "8016:Content Creation"
    "8017:Task Agent"
    "8018:Resource Management"
    "8019:Learning System"
    "8020:OpenWebUI"
)

# 依赖检查配置
PYTHON_PACKAGES=(
    "fastapi"
    "uvicorn"
    "httpx"
    "pydantic"
    "sqlalchemy"
    "pandas"
    "numpy"
)

SYSTEM_TOOLS=(
    "python3"
    "pip3"
    "curl"
    "docker"
    "git"
)

# 阈值配置
DISK_USAGE_THRESHOLD=80  # 磁盘使用率阈值（%）
DISK_FREE_THRESHOLD=5    # 最小剩余空间（GB）
MEMORY_USAGE_THRESHOLD=90  # 内存使用率阈值（%）
CPU_USAGE_THRESHOLD=90   # CPU使用率阈值（%）

# 初始化
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

# 日志函数
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}✅${NC} $*"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}⚠️${NC} $*"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}❌${NC} $*"
}

# 发送告警
send_alert() {
    local severity=$1
    shift
    local message="$*"
    
    log_error "告警 [$severity]: $message"
    
    # 发送邮件告警
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "[$severity] 健康检查告警 - $(hostname)" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # 发送Webhook告警
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"severity\":\"$severity\",\"message\":\"$message\",\"timestamp\":\"$(date -Iseconds)\"}" \
            >/dev/null 2>&1 || true
    fi
}

# 检查系统工具
check_system_tools() {
    log_info "检查系统工具..."
    local missing_tools=()
    
    for tool in "${SYSTEM_TOOLS[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            local version
            case "$tool" in
                python3)
                    version=$(python3 --version 2>&1 | awk '{print $2}')
                    ;;
                pip3)
                    version=$(pip3 --version 2>&1 | awk '{print $2}')
                    ;;
                docker)
                    version=$(docker --version 2>&1 | awk '{print $3}' | sed 's/,//')
                    ;;
                git)
                    version=$(git --version 2>&1 | awk '{print $3}')
                    ;;
                *)
                    version="installed"
                    ;;
            esac
            log_success "$tool: $version"
        else
            log_error "$tool: 未安装"
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        send_alert "ERROR" "缺少系统工具: ${missing_tools[*]}"
        return 1
    fi
    
    return 0
}

# 检查Python包
check_python_packages() {
    log_info "检查Python包..."
    local missing_packages=()
    
    for package in "${PYTHON_PACKAGES[@]}"; do
        if python3 -c "import ${package//-/_}" 2>/dev/null; then
            local version
            version=$(python3 -c "import ${package//-/_}; print(${package//-/_}.__version__)" 2>/dev/null || echo "installed")
            log_success "$package: $version"
        else
            log_error "$package: 未安装"
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        send_alert "WARNING" "缺少Python包: ${missing_packages[*]}"
        return 1
    fi
    
    return 0
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    local disk_usage
    disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    local disk_free
    disk_free=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/[^0-9.]//g')
    local disk_free_gb
    disk_free_gb=$(df -BG "$PROJECT_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ "$disk_usage" -ge "$DISK_USAGE_THRESHOLD" ]; then
        log_warning "磁盘使用率: ${disk_usage}% (阈值: ${DISK_USAGE_THRESHOLD}%)"
        send_alert "WARNING" "磁盘使用率过高: ${disk_usage}%"
    else
        log_success "磁盘使用率: ${disk_usage}%"
    fi
    
    if [ "$disk_free_gb" -lt "$DISK_FREE_THRESHOLD" ]; then
        log_error "磁盘剩余空间: ${disk_free} (阈值: ${DISK_FREE_THRESHOLD}GB)"
        send_alert "ERROR" "磁盘剩余空间不足: ${disk_free} (阈值: ${DISK_FREE_THRESHOLD}GB)"
        return 1
    else
        log_success "磁盘剩余空间: ${disk_free}"
    fi
    
    return 0
}

# 检查内存使用
check_memory() {
    log_info "检查内存使用..."
    
    if command -v free >/dev/null 2>&1; then
        local mem_total mem_used mem_usage
        mem_total=$(free | awk 'NR==2{print $2}')
        mem_used=$(free | awk 'NR==2{print $3}')
        mem_usage=$((mem_used * 100 / mem_total))
        
        if [ "$mem_usage" -ge "$MEMORY_USAGE_THRESHOLD" ]; then
            log_warning "内存使用率: ${mem_usage}% (阈值: ${MEMORY_USAGE_THRESHOLD}%)"
            send_alert "WARNING" "内存使用率过高: ${mem_usage}%"
        else
            log_success "内存使用率: ${mem_usage}%"
        fi
    else
        log_warning "无法检查内存使用（free命令不可用）"
    fi
}

# 检查CPU使用
check_cpu() {
    log_info "检查CPU使用..."
    
    if command -v top >/dev/null 2>&1; then
        local cpu_usage
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
        cpu_usage=${cpu_usage%.*}
        
        if [ "$cpu_usage" -ge "$CPU_USAGE_THRESHOLD" ]; then
            log_warning "CPU使用率: ${cpu_usage}% (阈值: ${CPU_USAGE_THRESHOLD}%)"
            send_alert "WARNING" "CPU使用率过高: ${cpu_usage}%"
        else
            log_success "CPU使用率: ${cpu_usage}%"
        fi
    else
        log_warning "无法检查CPU使用（top命令不可用）"
    fi
}

# 检查服务状态
check_service_status() {
    log_info "检查服务状态..."
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        local port="${service%%:*}"
        local name="${service#*:}"
        
        if lsof -i ":$port" >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            log_success "$name (端口 $port): 运行中"
        else
            log_error "$name (端口 $port): 未运行"
            failed_services+=("$name:$port")
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        send_alert "ERROR" "服务未运行: ${failed_services[*]}"
        return 1
    fi
    
    return 0
}

# 检查HTTP健康检查端点
check_health_endpoints() {
    log_info "检查HTTP健康检查端点..."
    local failed_endpoints=()
    
    # 检查主服务健康检查
    if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
        log_success "Super Agent健康检查: 正常"
    else
        log_error "Super Agent健康检查: 失败"
        failed_endpoints+=("http://localhost:8000/health")
    fi
    
    # 检查其他服务的健康检查端点（如果存在）
    for port in 8011 8013 8014 8015 8016 8017 8018 8019; do
        if curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            log_success "服务 $port 健康检查: 正常"
        else
            log_warning "服务 $port 健康检查: 失败或端点不存在"
        fi
    done
    
    if [ ${#failed_endpoints[@]} -gt 0 ]; then
        send_alert "ERROR" "健康检查端点失败: ${failed_endpoints[*]}"
        return 1
    fi
    
    return 0
}

# 检查Docker服务
check_docker_services() {
    log_info "检查Docker服务..."
    
    if ! command -v docker >/dev/null 2>&1; then
        log_warning "Docker未安装，跳过Docker服务检查"
        return 0
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker服务未运行"
        send_alert "ERROR" "Docker服务未运行"
        return 1
    fi
    
    local running_containers
    running_containers=$(docker ps --format "{{.Names}}" 2>/dev/null | wc -l)
    log_success "Docker服务: 运行中 (容器数: $running_containers)"
    
    return 0
}

# 检查日志文件大小
check_log_files() {
    log_info "检查日志文件..."
    
    local log_dir="$PROJECT_ROOT/logs"
    if [ -d "$log_dir" ]; then
        local large_logs
        large_logs=$(find "$log_dir" -type f -size +100M 2>/dev/null | head -5)
        
        if [ -n "$large_logs" ]; then
            log_warning "发现大日志文件（>100MB）:"
            echo "$large_logs" | while read -r log_file; do
                local size
                size=$(du -h "$log_file" | awk '{print $1}')
                log_warning "  - $log_file: $size"
            done
            send_alert "WARNING" "发现大日志文件，建议清理"
        else
            log_success "日志文件大小正常"
        fi
    else
        log_warning "日志目录不存在: $log_dir"
    fi
}

# 生成健康检查报告
generate_report() {
    local report_file="$LOG_DIR/health_report_$(date +%Y%m%d).json"
    
    cat > "$report_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "project_root": "$PROJECT_ROOT",
  "checks": {
    "system_tools": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "python_packages": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "disk_space": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "memory": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "cpu": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "services": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "health_endpoints": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')",
    "docker": "$([ $? -eq 0 ] && echo 'passed' || echo 'failed')"
  },
  "log_file": "$LOG_FILE"
}
EOF
    
    log_info "健康检查报告已生成: $report_file"
}

# 主函数
main() {
    log_info "=========================================="
    log_info "开始日常健康检查"
    log_info "时间: $(date)"
    log_info "主机: $(hostname)"
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "=========================================="
    
    local exit_code=0
    
    # 执行各项检查
    check_system_tools || exit_code=1
    check_python_packages || exit_code=1
    check_disk_space || exit_code=1
    check_memory
    check_cpu
    check_service_status || exit_code=1
    check_health_endpoints || exit_code=1
    check_docker_services || exit_code=1
    check_log_files
    
    # 生成报告
    generate_report
    
    log_info "=========================================="
    if [ $exit_code -eq 0 ]; then
        log_success "健康检查完成: 所有检查通过"
    else
        log_error "健康检查完成: 发现 $exit_code 个问题"
    fi
    log_info "=========================================="
    
    return $exit_code
}

# 执行主函数
main "$@"

