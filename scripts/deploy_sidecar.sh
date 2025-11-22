#!/bin/bash
# -*- coding: utf-8 -*-
# P3-401: Sidecar部署脚本

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"
DEPLOY_DIR="${PROJECT_ROOT}/deployments"

# 默认值
DEPLOY_MODE="${1:-docker}"  # docker/systemd
SIDECAR="${2:-all}"  # rag/trend/all
ACTION="${3:-start}"  # start/stop/restart/status

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI-STACK Sidecar部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "部署模式: ${DEPLOY_MODE}"
echo "Sidecar: ${SIDECAR}"
echo "操作: ${ACTION}"
echo ""

# 检查依赖
check_dependencies() {
    if [ "${DEPLOY_MODE}" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}错误: 未找到 docker${NC}"
            exit 1
        fi
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}错误: 未找到 docker-compose${NC}"
            exit 1
        fi
    elif [ "${DEPLOY_MODE}" = "systemd" ]; then
        if ! command -v systemctl &> /dev/null; then
            echo -e "${RED}错误: 未找到 systemctl${NC}"
            exit 1
        fi
    fi
}

# Docker部署
deploy_docker() {
    cd "${PROJECT_ROOT}"
    
    case "${ACTION}" in
        start)
            echo -e "${BLUE}启动Sidecar服务...${NC}"
            if [ "${SIDECAR}" = "all" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" --profile all up -d
            elif [ "${SIDECAR}" = "rag" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" --profile rag up -d rag-sidecar gateway
            elif [ "${SIDECAR}" = "trend" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" --profile trend up -d trend-sidecar gateway
            fi
            ;;
        stop)
            echo -e "${YELLOW}停止Sidecar服务...${NC}"
            if [ "${SIDECAR}" = "all" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" --profile all down
            elif [ "${SIDECAR}" = "rag" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" stop rag-sidecar
            elif [ "${SIDECAR}" = "trend" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" stop trend-sidecar
            fi
            ;;
        restart)
            echo -e "${BLUE}重启Sidecar服务...${NC}"
            deploy_docker stop
            sleep 2
            deploy_docker start
            ;;
        status)
            echo -e "${BLUE}Sidecar服务状态:${NC}"
            docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" ps
            ;;
        logs)
            echo -e "${BLUE}Sidecar服务日志:${NC}"
            if [ "${SIDECAR}" = "rag" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" logs -f rag-sidecar
            elif [ "${SIDECAR}" = "trend" ]; then
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" logs -f trend-sidecar
            else
                docker-compose -f "${DEPLOY_DIR}/docker-compose.sidecar.yml" logs -f
            fi
            ;;
        *)
            echo -e "${RED}未知操作: ${ACTION}${NC}"
            exit 1
            ;;
    esac
}

# Systemd部署
deploy_systemd() {
    case "${ACTION}" in
        start)
            echo -e "${BLUE}启动Sidecar服务...${NC}"
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
                sudo systemctl start ai-stack-rag.service
            fi
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
                sudo systemctl start ai-stack-trend.service
            fi
            sudo systemctl start ai-stack-gateway.service
            ;;
        stop)
            echo -e "${YELLOW}停止Sidecar服务...${NC}"
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
                sudo systemctl stop ai-stack-rag.service
            fi
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
                sudo systemctl stop ai-stack-trend.service
            fi
            sudo systemctl stop ai-stack-gateway.service
            ;;
        restart)
            echo -e "${BLUE}重启Sidecar服务...${NC}"
            deploy_systemd stop
            sleep 2
            deploy_systemd start
            ;;
        status)
            echo -e "${BLUE}Sidecar服务状态:${NC}"
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
                sudo systemctl status ai-stack-rag.service
            fi
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
                sudo systemctl status ai-stack-trend.service
            fi
            sudo systemctl status ai-stack-gateway.service
            ;;
        enable)
            echo -e "${BLUE}启用Sidecar服务自启动...${NC}"
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
                sudo systemctl enable ai-stack-rag.service
            fi
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
                sudo systemctl enable ai-stack-trend.service
            fi
            sudo systemctl enable ai-stack-gateway.service
            ;;
        disable)
            echo -e "${YELLOW}禁用Sidecar服务自启动...${NC}"
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
                sudo systemctl disable ai-stack-rag.service
            fi
            if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
                sudo systemctl disable ai-stack-trend.service
            fi
            sudo systemctl disable ai-stack-gateway.service
            ;;
        *)
            echo -e "${RED}未知操作: ${ACTION}${NC}"
            exit 1
            ;;
    esac
}

# 安装systemd服务
install_systemd() {
    echo -e "${BLUE}安装systemd服务...${NC}"
    
    # 创建用户和组
    if ! id "ai-stack" &>/dev/null; then
        sudo useradd -r -s /bin/false ai-stack
    fi
    
    # 复制服务文件
    sudo cp "${DEPLOY_DIR}/systemd/ai-stack-gateway.service" /etc/systemd/system/
    if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "rag" ]; then
        sudo cp "${DEPLOY_DIR}/systemd/ai-stack-rag.service" /etc/systemd/system/
    fi
    if [ "${SIDECAR}" = "all" ] || [ "${SIDECAR}" = "trend" ]; then
        sudo cp "${DEPLOY_DIR}/systemd/ai-stack-trend.service" /etc/systemd/system/
    fi
    
    # 重载systemd
    sudo systemctl daemon-reload
    
    echo -e "${GREEN}systemd服务安装完成${NC}"
}

# 主函数
main() {
    check_dependencies
    
    if [ "${ACTION}" = "install" ] && [ "${DEPLOY_MODE}" = "systemd" ]; then
        install_systemd
    elif [ "${DEPLOY_MODE}" = "docker" ]; then
        deploy_docker
    elif [ "${DEPLOY_MODE}" = "systemd" ]; then
        deploy_systemd
    else
        echo -e "${RED}未知部署模式: ${DEPLOY_MODE}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}操作完成${NC}"
}

# 运行主函数
main

