#!/bin/bash
# -*- coding: utf-8 -*-
# 自动部署脚本（生产级实现）
# 5.3: 调用CI、环境检查、部署验证

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
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs/deploy}"
LOG_FILE="$LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"

# GitHub配置
GITHUB_REPO="${GITHUB_REPO:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_WORKFLOW="${GITHUB_WORKFLOW:-cd.yml}"
DEPLOY_ENV="${DEPLOY_ENV:-staging}"  # staging 或 production
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"

# 部署配置
DEPLOY_TIMEOUT=1800  # 部署超时时间（秒）
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=30

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

# 检查前置条件
check_prerequisites() {
    log_info "检查前置条件..."
    
    local missing_tools=()
    
    # 检查必需工具
    for tool in git curl jq; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "缺少必需工具: ${missing_tools[*]}"
        return 1
    fi
    
    # 检查GitHub配置
    if [ -z "$GITHUB_REPO" ]; then
        log_error "GITHUB_REPO 未设置"
        return 1
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        log_error "GITHUB_TOKEN 未设置"
        return 1
    fi
    
    # 检查Git仓库
    if [ ! -d "$PROJECT_ROOT/.git" ]; then
        log_error "不是Git仓库: $PROJECT_ROOT"
        return 1
    fi
    
    log_success "前置条件检查通过"
    return 0
}

# 检查环境
check_environment() {
    log_info "检查部署环境..."
    
    # 检查当前分支
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log_info "当前分支: $current_branch"
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "存在未提交的更改"
        read -p "是否继续部署? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "部署已取消"
            return 1
        fi
    fi
    
    # 检查远程更新
    log_info "检查远程更新..."
    git fetch origin "$DEPLOY_BRANCH" || {
        log_error "无法获取远程分支: $DEPLOY_BRANCH"
        return 1
    }
    
    local local_commit remote_commit
    local_commit=$(git rev-parse HEAD)
    remote_commit=$(git rev-parse "origin/$DEPLOY_BRANCH")
    
    if [ "$local_commit" != "$remote_commit" ]; then
        log_warning "本地代码与远程不一致"
        log_info "本地: $local_commit"
        log_info "远程: $remote_commit"
        read -p "是否拉取最新代码? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git pull origin "$DEPLOY_BRANCH" || {
                log_error "拉取代码失败"
                return 1
            }
            log_success "代码已更新"
        fi
    else
        log_success "代码已是最新"
    fi
    
    return 0
}

# 触发GitHub Actions工作流
trigger_github_workflow() {
    log_info "触发GitHub Actions工作流..."
    
    local workflow_id
    workflow_id=$(curl -s -X GET \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_REPO/actions/workflows/$GITHUB_WORKFLOW" \
        | jq -r '.id')
    
    if [ -z "$workflow_id" ] || [ "$workflow_id" == "null" ]; then
        log_error "无法获取工作流ID: $GITHUB_WORKFLOW"
        return 1
    fi
    
    log_info "工作流ID: $workflow_id"
    
    # 触发工作流
    local run_id
    run_id=$(curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_REPO/actions/workflows/$workflow_id/dispatches" \
        -d "{\"ref\":\"$DEPLOY_BRANCH\",\"inputs\":{\"environment\":\"$DEPLOY_ENV\"}}" \
        | jq -r '.id // empty')
    
    if [ -z "$run_id" ]; then
        log_error "触发工作流失败"
        return 1
    fi
    
    log_success "工作流已触发，运行ID: $run_id"
    
    # 等待工作流完成
    log_info "等待工作流完成..."
    wait_for_workflow_completion "$run_id"
    
    return $?
}

# 等待工作流完成
wait_for_workflow_completion() {
    local run_id=$1
    local start_time=$(date +%s)
    local elapsed=0
    
    while [ $elapsed -lt $DEPLOY_TIMEOUT ]; do
        local status
        status=$(curl -s -X GET \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/$GITHUB_REPO/actions/runs/$run_id" \
            | jq -r '.status')
        
        case "$status" in
            "completed")
                local conclusion
                conclusion=$(curl -s -X GET \
                    -H "Authorization: token $GITHUB_TOKEN" \
                    -H "Accept: application/vnd.github.v3+json" \
                    "https://api.github.com/repos/$GITHUB_REPO/actions/runs/$run_id" \
                    | jq -r '.conclusion')
                
                if [ "$conclusion" == "success" ]; then
                    log_success "工作流执行成功"
                    return 0
                else
                    log_error "工作流执行失败: $conclusion"
                    return 1
                fi
                ;;
            "in_progress"|"queued")
                log_info "工作流状态: $status (已等待 ${elapsed}秒)"
                sleep 10
                elapsed=$(($(date +%s) - start_time))
                ;;
            *)
                log_error "工作流状态异常: $status"
                return 1
                ;;
        esac
    done
    
    log_error "工作流执行超时"
    return 1
}

# 部署后验证
verify_deployment() {
    log_info "验证部署..."
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 健康检查
    local health_check_url
    case "$DEPLOY_ENV" in
        "production")
            health_check_url="https://aistack.example.com/health"
            ;;
        "staging")
            health_check_url="https://staging.aistack.example.com/health"
            ;;
        *)
            health_check_url="http://localhost:8000/health"
            ;;
    esac
    
    local retry=0
    while [ $retry -lt $HEALTH_CHECK_RETRIES ]; do
        if curl -sf "$health_check_url" >/dev/null 2>&1; then
            log_success "健康检查通过: $health_check_url"
            return 0
        else
            log_warning "健康检查失败，重试 $((retry + 1))/$HEALTH_CHECK_RETRIES"
            sleep $HEALTH_CHECK_INTERVAL
            retry=$((retry + 1))
        fi
    done
    
    log_error "健康检查失败，已达到最大重试次数"
    return 1
}

# 回滚部署
rollback_deployment() {
    log_warning "开始回滚部署..."
    
    # 这里可以实现回滚逻辑
    # 例如：恢复到上一个版本、重启服务等
    
    log_info "回滚逻辑待实现"
    
    return 0
}

# 主函数
main() {
    log_info "=========================================="
    log_info "开始自动部署"
    log_info "时间: $(date)"
    log_info "环境: $DEPLOY_ENV"
    log_info "分支: $DEPLOY_BRANCH"
    log_info "=========================================="
    
    # 检查前置条件
    if ! check_prerequisites; then
        log_error "前置条件检查失败"
        exit 1
    fi
    
    # 检查环境
    if ! check_environment; then
        log_error "环境检查失败"
        exit 1
    fi
    
    # 触发部署
    if ! trigger_github_workflow; then
        log_error "部署失败"
        rollback_deployment
        exit 1
    fi
    
    # 验证部署
    if ! verify_deployment; then
        log_error "部署验证失败"
        rollback_deployment
        exit 1
    fi
    
    log_info "=========================================="
    log_success "部署完成"
    log_info "=========================================="
    
    return 0
}

# 执行主函数
main "$@"

