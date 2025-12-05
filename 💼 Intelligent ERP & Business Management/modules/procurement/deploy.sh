#!/bin/bash

# 采购管理模块部署脚本
# 版本: 1.0.0
# 作者: DevOps Team

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 配置变量
APP_NAME="procurement"
APP_DIR="/opt/${APP_NAME}"
BACKUP_DIR="/backup/${APP_NAME}"
LOG_DIR="/var/log/${APP_NAME}"
CONFIG_DIR="${APP_DIR}/config"
VENV_DIR="${APP_DIR}/venv"

# 环境检测
detect_environment() {
    log "检测部署环境..."
    
    # 检查操作系统
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        log "操作系统: $NAME $VERSION"
    else
        warn "无法确定操作系统版本"
    fi
    
    # 检查Python版本
    PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2)
    if [[ $? -eq 0 ]]; then
        log "Python版本: $PYTHON_VERSION"
    else
        error "Python3未安装"
    fi
    
    # 检查PostgreSQL
    if command -v psql &> /dev/null; then
        log "PostgreSQL已安装"
    else
        error "PostgreSQL未安装"
    fi
}

# 创建目录结构
create_directories() {
    log "创建目录结构..."
    
    sudo mkdir -p "$APP_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "$CONFIG_DIR"
    
    # 设置权限
    sudo chown -R procurement:procurement "$APP_DIR"
    sudo chown -R procurement:procurement "$LOG_DIR"
    sudo chmod 755 "$APP_DIR"
    sudo chmod 755 "$LOG_DIR"
}

# 备份现有版本
backup_current_version() {
    if [[ -d "$APP_DIR" && "$(ls -A $APP_DIR)" ]]; then
        log "备份当前版本..."
        
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
        
        sudo tar -czf "$BACKUP_FILE" -C "$(dirname $APP_DIR)" "$(basename $APP_DIR)" 2>/dev/null || warn "备份创建失败，继续部署"
        
        if [[ -f "$BACKUP_FILE" ]]; then
            log "备份已创建: $BACKUP_FILE"
        fi
    else
        log "未发现现有版本，跳过备份"
    fi
}

# 部署应用代码
deploy_application() {
    log "部署应用代码..."
    
    # 这里假设代码已经通过CI/CD流水线传输到部署目录
    # 实际部署时可能需要从Git仓库拉取或从构建服务器下载
    
    # 检查部署包是否存在
    DEPLOY_PACKAGE="/tmp/${APP_NAME}_deploy.tar.gz"
    if [[ ! -f "$DEPLOY_PACKAGE" ]]; then
        warn "未找到部署包，使用当前目录代码"
        # 使用当前目录代码（开发环境）
        sudo cp -r . "$APP_DIR/"
    else
        # 解压部署包
        sudo tar -xzf "$DEPLOY_PACKAGE" -C "$APP_DIR"
    fi
    
    # 设置文件权限
    sudo chown -R procurement:procurement "$APP_DIR"
    sudo find "$APP_DIR" -type f -name "*.py" -exec chmod 644 {} \;
    sudo find "$APP_DIR" -type f -name "*.sh" -exec chmod 755 {} \;
    sudo chmod 755 "$APP_DIR/procurement_api.py"
}

# 配置Python虚拟环境
setup_virtualenv() {
    log "配置Python虚拟环境..."
    
    # 检查是否已存在虚拟环境
    if [[ -d "$VENV_DIR" ]]; then
        log "虚拟环境已存在，重新创建"
        sudo rm -rf "$VENV_DIR"
    fi
    
    # 创建虚拟环境
    sudo -u procurement python3 -m venv "$VENV_DIR"
    
    # 安装依赖
    sudo -u procurement "$VENV_DIR/bin/pip" install --upgrade pip
    
    if [[ -f "$APP_DIR/requirements.txt" ]]; then
        sudo -u procurement "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
    else
        warn "未找到requirements.txt，安装基础依赖"
        sudo -u procurement "$VENV_DIR/bin/pip" install flask sqlalchemy psycopg2-binary redis
    fi
}

# 配置数据库
setup_database() {
    log "配置数据库..."
    
    # 检查数据库连接
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
        error "数据库连接失败，请检查数据库配置"
    fi
    
    # 初始化数据库表（如果存在初始化脚本）
    if [[ -f "$APP_DIR/scripts/init_db.py" ]]; then
        log "初始化数据库表..."
        sudo -u procurement "$VENV_DIR/bin/python" "$APP_DIR/scripts/init_db.py"
    else
        warn "未找到数据库初始化脚本，表结构将通过应用自动创建"
    fi
}

# 配置系统服务
setup_systemd_service() {
    log "配置系统服务..."
    
    SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
    
    # 创建服务文件
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Procurement Management Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=procurement
Group=procurement
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin:/usr/bin:/usr/local/bin
Environment=PYTHONPATH=$APP_DIR
ExecStart=$VENV_DIR/bin/python procurement_api.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR $LOG_DIR

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    sudo systemctl enable "$APP_NAME.service"
}

# 配置日志
setup_logging() {
    log "配置日志系统..."
    
    # 创建logrotate配置
    LOGROTATE_FILE="/etc/logrotate.d/${APP_NAME}"
    
    sudo tee "$LOGROTATE_FILE" > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 procurement procurement
}
EOF
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if ! sudo systemctl is-active --quiet "$APP_NAME.service"; then
        error "服务启动失败"
    fi
    
    # 检查API端点
    if command -v curl &> /dev/null; then
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/procurement/health || echo "000")
        
        if [[ "$RESPONSE" == "200" ]]; then
            log "健康检查通过"
        else
            error "健康检查失败，HTTP状态码: $RESPONSE"
        fi
    else
        warn "curl未安装，跳过API健康检查"
    fi
    
    # 检查数据库连接
    if [[ -f "$APP_DIR/scripts/health_check.py" ]]; then
        sudo -u procurement "$VENV_DIR/bin/python" "$APP_DIR/scripts/health_check.py"
    fi
}

# 显示部署信息
show_deployment_info() {
    log "部署完成！"
    echo ""
    echo "========================================"
    echo "           部署信息汇总"
    echo "========================================"
    echo "应用名称: $APP_NAME"
    echo "安装目录: $APP_DIR"
    echo "虚拟环境: $VENV_DIR"
    echo "日志目录: $LOG_DIR"
    echo "备份目录: $BACKUP_DIR"
    echo ""
    echo "服务状态:"
    sudo systemctl status "$APP_NAME.service" --no-pager
    echo ""
    echo "常用命令:"
    echo "  启动服务: sudo systemctl start $APP_NAME"
    echo "  停止服务: sudo systemctl stop $APP_NAME"
    echo "  重启服务: sudo systemctl restart $APP_NAME"
    echo "  查看日志: sudo journalctl -u $APP_NAME -f"
    echo ""
    echo "健康检查: http://localhost:8000/api/procurement/health"
    echo "API文档: http://localhost:8000/api/docs"
    echo "========================================"
}

# 主部署函数
main() {
    log "开始部署采购管理模块..."
    
    # 检查是否以root权限运行
    if [[ $EUID -ne 0 ]]; then
        error "请使用sudo或以root用户运行此脚本"
    fi
    
    # 执行部署步骤
    detect_environment
    create_directories
    backup_current_version
    deploy_application
    setup_virtualenv
    setup_database
    setup_systemd_service
    setup_logging
    
    # 启动服务
    log "启动服务..."
    sudo systemctl start "$APP_NAME.service"
    
    health_check
    show_deployment_info
    
    log "部署完成！"
}

# 参数处理
case "${1:-}" in
    "--help" | "-h")
        echo "使用说明:"
        echo "  $0          执行完整部署"
        echo "  $0 --backup 仅执行备份"
        echo "  $0 --restore 从备份恢复"
        echo "  $0 --health  执行健康检查"
        exit 0
        ;;
    "--backup")
        backup_current_version
        exit 0
        ;;
    "--health")
        health_check
        exit 0
        ;;
    "")
        main
        ;;
    *)
        error "未知参数: $1"
        ;;
esac