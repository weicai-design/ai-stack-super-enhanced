#!/bin/bash

# AI Stack Super Enhanced 环境设置脚本
# 用于快速设置开发和生产环境

set -e  # 遇到错误立即退出

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

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 $1 未安装，请先安装"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "AI Stack Super Enhanced 环境设置脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -d, --dev           设置开发环境"
    echo "  -p, --prod          设置生产环境"
    echo "  -t, --test          设置测试环境"
    echo "  --docker            使用Docker环境"
    echo "  --no-docker         不使用Docker环境"
    echo ""
}

# 默认配置
ENVIRONMENT="dev"
USE_DOCKER=true

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            ENVIRONMENT="dev"
            shift
            ;;
        -p|--prod)
            ENVIRONMENT="prod"
            shift
            ;;
        -t|--test)
            ENVIRONMENT="test"
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --no-docker)
            USE_DOCKER=false
            shift
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 主函数
main() {
    log_info "开始设置 AI Stack Super Enhanced $ENVIRONMENT 环境"
    
    # 检查必要命令
    check_command python3
    check_command pip3
    
    if [ "$USE_DOCKER" = true ]; then
        check_command docker
        check_command docker-compose
    fi
    
    # 创建虚拟环境
    log_info "创建Python虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "虚拟环境创建成功"
    else
        log_warning "虚拟环境已存在，跳过创建"
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装项目依赖..."
    pip install -r requirements.txt
    
    # 创建环境配置文件
    log_info "设置环境配置文件..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_success "环境配置文件创建成功"
        
        # 根据环境类型设置不同的配置
        case $ENVIRONMENT in
            "prod")
                sed -i.bak 's/APP_ENV=development/APP_ENV=production/g' .env
                sed -i.bak 's/DEBUG=true/DEBUG=false/g' .env
                log_info "已配置为生产环境"
                ;;
            "test")
                sed -i.bak 's/APP_ENV=development/APP_ENV=testing/g' .env
                sed -i.bak 's/DB_NAME=aistack/DB_NAME=aistack_test/g' .env
                log_info "已配置为测试环境"
                ;;
            *)
                log_info "保持开发环境配置"
                ;;
        esac
        
        # 清理备份文件
        rm -f .env.bak
        
        log_warning "请编辑 .env 文件配置数据库、Redis等连接信息"
    else
        log_warning ".env 文件已存在，跳过创建"
    fi
    
    # 创建必要目录
    log_info "创建必要目录结构..."
    mkdir -p logs storage/temp storage/uploads data/backups
    
    # 设置Docker环境
    if [ "$USE_DOCKER" = true ]; then
        setup_docker_environment
    fi
    
    # 数据库初始化
    log_info "初始化数据库..."
    if [ "$USE_DOCKER" = true ]; then
        # 等待Docker服务启动
        log_info "等待数据库服务启动..."
        sleep 10
        
        # 运行数据库迁移
        docker-compose exec app python -c "from core.config.configuration_manager import ConfigurationManager; print('配置管理器初始化成功')"
    else
        # 直接运行数据库迁移
        python -c "from core.config.configuration_manager import ConfigurationManager; print('配置管理器初始化成功')"
    fi
    
    # 运行基础测试
    log_info "运行基础测试验证环境..."
    if pytest tests/unit/test_config_system.py -v; then
        log_success "环境测试通过"
    else
        log_error "环境测试失败，请检查配置"
        exit 1
    fi
    
    log_success "AI Stack Super Enhanced $ENVIRONMENT 环境设置完成"
    
    # 显示后续步骤
    echo ""
    echo "下一步操作:"
    echo "1. 编辑 .env 文件配置数据库和Redis连接"
    echo "2. 运行 'source venv/bin/activate' 激活虚拟环境"
    if [ "$USE_DOCKER" = true ]; then
        echo "3. 运行 'docker-compose up -d' 启动服务"
    else
        echo "3. 运行 'python api/main.py' 启动服务"
    fi
    echo "4. 访问 http://localhost:8000 查看系统"
    echo "5. 访问 http://localhost:8000/docs 查看API文档"
    echo ""
}

# Docker环境设置
setup_docker_environment() {
    log_info "设置Docker环境..."
    
    # 构建Docker镜像
    log_info "构建Docker镜像..."
    docker-compose build
    
    # 启动基础服务
    log_info "启动基础服务..."
    docker-compose up -d db redis
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker服务启动成功"
    else
        log_error "Docker服务启动失败"
        exit 1
    fi
}

# 清理函数（可选）
cleanup() {
    log_info "清理临时文件..."
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} +
    log_success "清理完成"
}

# 信号处理
trap cleanup EXIT

# 运行主函数
main "$@"