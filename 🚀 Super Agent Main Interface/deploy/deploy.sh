#!/bin/bash

# AI-STACK 部署脚本
# 支持多环境部署和回滚

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
AI-STACK 部署脚本

用法: $0 [选项] [环境]

选项:
    -h, --help          显示此帮助信息
    -e, --environment   指定部署环境 (development|staging|production)
    -v, --version       指定部署版本
    -r, --rollback      回滚到上一个版本
    -d, --dry-run      模拟部署，不实际执行
    -c, --config        指定配置文件路径

环境:
    development         开发环境
    staging             预发布环境
    production          生产环境

示例:
    $0 -e production -v 1.2.3     # 部署1.2.3版本到生产环境
    $0 -e staging --dry-run       # 模拟部署到预发布环境
    $0 -e production --rollback   # 回滚生产环境
EOF
}

# 参数解析
ENVIRONMENT=""
VERSION="latest"
ROLLBACK=false
DRY_RUN=false
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        *)
            # 如果没有指定选项，尝试作为环境参数
            if [[ -z "$ENVIRONMENT" ]]; then
                ENVIRONMENT="$1"
            else
                log_error "未知参数: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# 验证环境参数
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "必须指定部署环境"
    show_help
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "无效的环境: $ENVIRONMENT"
    show_help
    exit 1
fi

# 加载配置文件
if [[ -n "$CONFIG_FILE" && -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    # 默认配置文件路径
    if [[ -f "deploy/config/$ENVIRONMENT.env" ]]; then
        source "deploy/config/$ENVIRONMENT.env"
    fi
fi

# 设置默认值
: ${APP_PORT:=8000}
: ${DB_PORT:=5432}
: ${REDIS_PORT:=6379}
: ${DOCKER_COMPOSE_FILE:="docker-compose.yml"}
: ${BACKUP_DIR:="/opt/ai-stack/backups"}
: ${LOG_DIR:="/opt/ai-stack/logs"}

# 部署前检查
check_prerequisites() {
    log_info "检查部署前置条件..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查配置文件
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Docker Compose文件不存在: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # 检查环境变量
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ -z "$DB_PASSWORD" || -z "$SECRET_KEY" ]]; then
            log_error "生产环境必须设置DB_PASSWORD和SECRET_KEY"
            exit 1
        fi
    fi
    
    log_success "前置条件检查通过"
}

# 备份当前版本
backup_current_version() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 备份当前版本"
        return
    fi
    
    log_info "备份当前版本..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/$ENVIRONMENT/$timestamp"
    
    mkdir -p "$backup_path"
    
    # 备份数据库
    if docker-compose exec -T postgres pg_dump -U "$DB_USER" "ai_stack_$ENVIRONMENT" > "$backup_path/database.sql" 2>/dev/null; then
        log_success "数据库备份完成"
    else
        log_warning "数据库备份失败，可能数据库未运行"
    fi
    
    # 备份配置文件
    cp "$DOCKER_COMPOSE_FILE" "$backup_path/"
    cp -r config/ "$backup_path/" 2>/dev/null || true
    
    # 记录当前镜像版本
    docker images --format "table {{.Repository}}\t{{.Tag}}" | grep ai-stack > "$backup_path/images.txt" 2>/dev/null || true
    
    log_success "版本备份完成: $backup_path"
}

# 停止当前服务
stop_services() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 停止当前服务"
        return
    fi
    
    log_info "停止当前服务..."
    
    if docker-compose down --remove-orphans; then
        log_success "服务停止成功"
    else
        log_warning "服务停止过程中出现警告"
    fi
}

# 拉取新版本镜像
pull_new_version() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 拉取版本 $VERSION"
        return
    fi
    
    log_info "拉取版本 $VERSION..."
    
    # 设置环境变量
    export ENVIRONMENT="$ENVIRONMENT"
    export VERSION="$VERSION"
    export APP_PORT="$APP_PORT"
    export DB_PORT="$DB_PORT"
    export REDIS_PORT="$REDIS_PORT"
    
    if [[ -n "$DB_PASSWORD" ]]; then export DB_PASSWORD="$DB_PASSWORD"; fi
    if [[ -n "$REDIS_PASSWORD" ]]; then export REDIS_PASSWORD="$REDIS_PASSWORD"; fi
    if [[ -n "$SECRET_KEY" ]]; then export SECRET_KEY="$SECRET_KEY"; fi
    
    if docker-compose pull; then
        log_success "镜像拉取成功"
    else
        log_error "镜像拉取失败"
        exit 1
    fi
}

# 启动新版本服务
start_services() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 启动新版本服务"
        return
    fi
    
    log_info "启动新版本服务..."
    
    if docker-compose up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 健康检查
health_check() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 执行健康检查"
        return 0
    fi
    
    log_info "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "http://localhost:$APP_PORT/health" &> /dev/null; then
            log_success "健康检查通过"
            return 0
        fi
        
        log_info "健康检查尝试 $attempt/$max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    log_error "健康检查失败，服务未正常启动"
    return 1
}

# 执行回滚
perform_rollback() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 执行回滚操作"
        return
    fi
    
    log_info "执行回滚操作..."
    
    # 查找最新的备份
    local latest_backup=$(ls -dt "$BACKUP_DIR/$ENVIRONMENT/"* 2>/dev/null | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "找不到可用的备份"
        exit 1
    fi
    
    log_info "使用备份: $latest_backup"
    
    # 停止当前服务
    stop_services
    
    # 恢复数据库
    if [[ -f "$latest_backup/database.sql" ]]; then
        log_info "恢复数据库..."
        docker-compose up -d postgres
        sleep 10
        
        if docker-compose exec -T postgres psql -U "$DB_USER" -d "ai_stack_$ENVIRONMENT" -f /backup/database.sql < "$latest_backup/database.sql"; then
            log_success "数据库恢复成功"
        else
            log_error "数据库恢复失败"
        fi
    fi
    
    # 使用备份的配置启动服务
    if [[ -f "$latest_backup/$DOCKER_COMPOSE_FILE" ]]; then
        cp "$latest_backup/$DOCKER_COMPOSE_FILE" ./
    fi
    
    start_services
    
    if health_check; then
        log_success "回滚成功"
    else
        log_error "回滚后健康检查失败"
        exit 1
    fi
}

# 清理旧镜像
cleanup_old_images() {
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[模拟] 清理旧镜像"
        return
    fi
    
    log_info "清理旧镜像..."
    
    # 保留最近3个版本的镜像，删除其他
    docker image prune -a -f --filter "until=72h"
    
    log_success "镜像清理完成"
}

# 生成部署报告
generate_deployment_report() {
    local report_file="$LOG_DIR/deployment_$(date +%Y%m%d_%H%M%S).log"
    
    cat > "$report_file" << EOF
AI-STACK 部署报告
================

部署时间: $(date)
环境: $ENVIRONMENT
版本: $VERSION
操作: $([[ "$ROLLBACK" == true ]] && echo "回滚" || echo "部署")

服务状态:
$(docker-compose ps)

镜像版本:
$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | grep ai-stack)

健康检查: $([[ "$DRY_RUN" == true ]] && echo "模拟" || (health_check && echo "通过" || echo "失败"))
EOF
    
    log_success "部署报告生成: $report_file"
}

# 主部署流程
deploy() {
    log_info "开始部署 AI-STACK ($ENVIRONMENT环境)"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warning "模拟部署模式，不会实际修改系统"
    fi
    
    # 检查前置条件
    check_prerequisites
    
    if [[ "$ROLLBACK" == true ]]; then
        # 执行回滚
        perform_rollback
    else
        # 执行部署
        backup_current_version
        stop_services
        pull_new_version
        start_services
        
        # 等待服务启动并检查健康状态
        if ! health_check; then
            log_error "部署失败，执行回滚..."
            perform_rollback
            exit 1
        fi
        
        cleanup_old_images
    fi
    
    generate_deployment_report
    log_success "AI-STACK 部署完成"
}

# 执行部署
main() {
    log_info "AI-STACK 部署脚本 v1.0"
    log_info "环境: $ENVIRONMENT"
    log_info "版本: $VERSION"
    log_info "模式: $([[ "$ROLLBACK" == true ]] && echo "回滚" || echo "部署")"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warning "DRY RUN模式 - 不会实际执行任何更改"
    fi
    
    deploy
}

# 捕获信号，确保资源清理
trap 'log_error "部署被中断"; exit 1' INT TERM

# 运行主函数
main "$@"