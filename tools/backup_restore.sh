#!/bin/bash

# ================================================================
# AI Stack Super Enhanced - 备份恢复工具
# 版本: v1.0
# 功能: 数据库备份、配置备份、完整系统备份和恢复
# ================================================================

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# ==================== 备份功能 ====================

backup_database() {
    log_info "开始备份数据库..."
    
    mkdir -p "$BACKUP_DIR/databases"
    
    # 备份ERP数据库
    ERP_DB="$PROJECT_ROOT/💼 Intelligent ERP & Business Management/ai_stack.db"
    if [ -f "$ERP_DB" ]; then
        cp "$ERP_DB" "$BACKUP_DIR/databases/erp_db_$TIMESTAMP.db"
        
        # 导出为SQL
        sqlite3 "$ERP_DB" .dump > "$BACKUP_DIR/databases/erp_db_$TIMESTAMP.sql"
        
        log_success "ERP数据库备份完成"
    else
        log_warning "ERP数据库文件不存在"
    fi
}

backup_config() {
    log_info "开始备份配置文件..."
    
    mkdir -p "$BACKUP_DIR/configs"
    
    cd "$PROJECT_ROOT"
    
    # 备份配置文件
    CONFIG_FILES=(
        ".env"
        "docker-compose.yml"
        "docker-compose.full.yml"
        "requirements.txt"
    )
    
    for file in "${CONFIG_FILES[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/configs/${file}_$TIMESTAMP"
            log_success "备份配置: $file"
        fi
    done
}

backup_data() {
    log_info "开始备份数据文件..."
    
    mkdir -p "$BACKUP_DIR/data"
    
    # 备份导出的数据
    if [ -d "$PROJECT_ROOT/data/exports" ]; then
        tar -czf "$BACKUP_DIR/data/exports_$TIMESTAMP.tar.gz" \
            -C "$PROJECT_ROOT/data" exports
        log_success "数据导出文件备份完成"
    fi
    
    # 备份日志
    if [ -d "$PROJECT_ROOT/logs" ]; then
        tar -czf "$BACKUP_DIR/data/logs_$TIMESTAMP.tar.gz" \
            -C "$PROJECT_ROOT" logs
        log_success "日志文件备份完成"
    fi
}

backup_full() {
    log_info "开始完整系统备份..."
    
    mkdir -p "$BACKUP_DIR/full"
    
    # 备份整个项目（排除不必要的文件）
    cd "$(dirname "$PROJECT_ROOT")"
    
    tar -czf "$BACKUP_DIR/full/ai_stack_full_$TIMESTAMP.tar.gz" \
        --exclude="*/venv/*" \
        --exclude="*/node_modules/*" \
        --exclude="*/__pycache__/*" \
        --exclude="*/.git/*" \
        --exclude="*/backups/*" \
        --exclude="*/cache/*" \
        "$(basename "$PROJECT_ROOT")"
    
    log_success "完整系统备份完成"
    
    # 显示备份大小
    BACKUP_FILE="$BACKUP_DIR/full/ai_stack_full_$TIMESTAMP.tar.gz"
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "备份文件大小: $BACKUP_SIZE"
}

# ==================== 恢复功能 ====================

restore_database() {
    log_info "恢复数据库..."
    
    if [ -z "$1" ]; then
        log_error "请指定要恢复的备份文件"
        return 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        return 1
    fi
    
    ERP_DB="$PROJECT_ROOT/💼 Intelligent ERP & Business Management/ai_stack.db"
    
    # 备份当前数据库
    if [ -f "$ERP_DB" ]; then
        cp "$ERP_DB" "${ERP_DB}.before_restore_$TIMESTAMP"
        log_info "当前数据库已备份"
    fi
    
    # 恢复数据库
    if [[ "$BACKUP_FILE" == *.sql ]]; then
        # 从SQL恢复
        sqlite3 "$ERP_DB" < "$BACKUP_FILE"
        log_success "数据库从SQL恢复完成"
    else
        # 从DB文件恢复
        cp "$BACKUP_FILE" "$ERP_DB"
        log_success "数据库从文件恢复完成"
    fi
}

restore_config() {
    log_info "恢复配置文件..."
    
    if [ -z "$1" ]; then
        log_error "请指定备份时间戳（如：20251103_235900）"
        return 1
    fi
    
    TIMESTAMP="$1"
    
    cd "$PROJECT_ROOT"
    
    for file in "$BACKUP_DIR/configs"/*_$TIMESTAMP; do
        if [ -f "$file" ]; then
            ORIGINAL_NAME=$(basename "$file" | sed "s/_$TIMESTAMP$//")
            cp "$file" "$ORIGINAL_NAME"
            log_success "恢复配置: $ORIGINAL_NAME"
        fi
    done
}

# ==================== 列出备份 ====================

list_backups() {
    log_info "备份列表："
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "数据库备份:"
        ls -lh "$BACKUP_DIR/databases" 2>/dev/null | tail -n +2 || echo "  无备份"
        
        echo ""
        echo "完整备份:"
        ls -lh "$BACKUP_DIR/full" 2>/dev/null | tail -n +2 || echo "  无备份"
        
        echo ""
        echo "配置备份:"
        ls -lh "$BACKUP_DIR/configs" 2>/dev/null | tail -n +2 || echo "  无备份"
    else
        log_warning "备份目录不存在"
    fi
}

# ==================== 清理旧备份 ====================

cleanup_old_backups() {
    log_info "清理30天前的备份..."
    
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -type f -mtime +30 -delete
        log_success "旧备份清理完成"
    fi
}

# ==================== 主菜单 ====================

show_menu() {
    echo ""
    echo "=============================================="
    echo "  AI Stack 备份恢复工具"
    echo "=============================================="
    echo ""
    echo "1. 备份数据库"
    echo "2. 备份配置文件"
    echo "3. 备份数据文件"
    echo "4. 完整系统备份"
    echo "5. 恢复数据库"
    echo "6. 恢复配置文件"
    echo "7. 列出所有备份"
    echo "8. 清理旧备份（30天前）"
    echo "9. 退出"
    echo ""
    echo -n "请选择操作 [1-9]: "
}

# ==================== 主程序 ====================

if [ "$1" == "--auto" ]; then
    # 自动备份模式（用于定时任务）
    log_info "自动备份模式"
    backup_database
    backup_config
    backup_data
    cleanup_old_backups
    exit 0
fi

if [ "$1" == "backup-all" ]; then
    # 快速完整备份
    backup_database
    backup_config
    backup_data
    backup_full
    exit 0
fi

if [ "$1" == "list" ]; then
    list_backups
    exit 0
fi

# 交互模式
while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            backup_database
            ;;
        2)
            backup_config
            ;;
        3)
            backup_data
            ;;
        4)
            backup_full
            ;;
        5)
            echo -n "请输入备份文件路径: "
            read backup_file
            restore_database "$backup_file"
            ;;
        6)
            echo -n "请输入备份时间戳: "
            read timestamp
            restore_config "$timestamp"
            ;;
        7)
            list_backups
            ;;
        8)
            cleanup_old_backups
            ;;
        9)
            log_info "退出"
            exit 0
            ;;
        *)
            log_error "无效选择"
            ;;
    esac
    
    echo ""
    read -p "按回车继续..."
done

