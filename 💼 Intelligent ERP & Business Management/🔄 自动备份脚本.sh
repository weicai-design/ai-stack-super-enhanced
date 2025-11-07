#!/bin/bash

################################################################################
# AI-Stack ERP 自动备份脚本
# 
# 功能：
# - 自动备份数据库
# - 自动备份配置文件
# - 自动备份日志文件
# - 自动清理过期备份
# - 备份验证
# 
# 使用方法：
# ./🔄\ 自动备份脚本.sh
# 
# 定时任务（每天凌晨2点）：
# 0 2 * * * /path/to/🔄\ 自动备份脚本.sh
################################################################################

set -e  # 遇到错误立即退出

# 配置
BACKUP_DIR="backups"
RETENTION_DAYS=30  # 保留30天的备份
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/backup.log"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# 创建备份目录
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_success "创建备份目录: $BACKUP_DIR"
    fi
}

# 备份数据库
backup_database() {
    log "开始备份数据库..."
    
    if [ -f "erp_data.db" ]; then
        # 复制数据库文件
        cp erp_data.db "$BACKUP_DIR/erp_data_$DATE.db"
        
        # 获取文件大小
        SIZE=$(du -h "$BACKUP_DIR/erp_data_$DATE.db" | cut -f1)
        
        log_success "数据库备份完成: erp_data_$DATE.db (大小: $SIZE)"
    else
        log_warning "数据库文件不存在: erp_data.db"
    fi
}

# 备份配置文件
backup_config() {
    log "开始备份配置文件..."
    
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/.env_$DATE"
        log_success "配置文件备份完成: .env_$DATE"
    else
        log_warning "配置文件不存在: .env"
    fi
}

# 备份日志文件
backup_logs() {
    log "开始备份日志文件..."
    
    if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
        tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/ 2>/dev/null || true
        
        if [ -f "$BACKUP_DIR/logs_$DATE.tar.gz" ]; then
            SIZE=$(du -h "$BACKUP_DIR/logs_$DATE.tar.gz" | cut -f1)
            log_success "日志备份完成: logs_$DATE.tar.gz (大小: $SIZE)"
        fi
    else
        log_warning "日志目录为空或不存在"
    fi
}

# 创建完整备份压缩包
create_full_backup() {
    log "开始创建完整备份包..."
    
    FULL_BACKUP="$BACKUP_DIR/full_backup_$DATE.tar.gz"
    
    tar -czf "$FULL_BACKUP" \
        erp_data.db \
        .env \
        logs/ \
        2>/dev/null || true
    
    if [ -f "$FULL_BACKUP" ]; then
        SIZE=$(du -h "$FULL_BACKUP" | cut -f1)
        log_success "完整备份包创建完成: full_backup_$DATE.tar.gz (大小: $SIZE)"
    else
        log_error "完整备份包创建失败"
    fi
}

# 验证备份
verify_backup() {
    log "开始验证备份..."
    
    BACKUP_FILE="$BACKUP_DIR/erp_data_$DATE.db"
    
    if [ -f "$BACKUP_FILE" ]; then
        # 检查文件大小
        SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
        
        if [ "$SIZE" -gt 0 ]; then
            log_success "备份验证成功: 文件大小 $SIZE 字节"
            return 0
        else
            log_error "备份验证失败: 文件大小为0"
            return 1
        fi
    else
        log_error "备份验证失败: 备份文件不存在"
        return 1
    fi
}

# 清理过期备份
cleanup_old_backups() {
    log "开始清理过期备份（保留${RETENTION_DAYS}天）..."
    
    # 清理数据库备份
    DELETED_COUNT=0
    
    find "$BACKUP_DIR" -name "erp_data_*.db" -mtime +$RETENTION_DAYS -type f 2>/dev/null | while read file; do
        rm -f "$file"
        DELETED_COUNT=$((DELETED_COUNT + 1))
        log "删除过期备份: $(basename $file)"
    done
    
    # 清理完整备份包
    find "$BACKUP_DIR" -name "full_backup_*.tar.gz" -mtime +$RETENTION_DAYS -type f 2>/dev/null | while read file; do
        rm -f "$file"
        log "删除过期备份: $(basename $file)"
    done
    
    # 清理日志备份
    find "$BACKUP_DIR" -name "logs_*.tar.gz" -mtime +$RETENTION_DAYS -type f 2>/dev/null | while read file; do
        rm -f "$file"
        log "删除过期备份: $(basename $file)"
    done
    
    log_success "过期备份清理完成"
}

# 生成备份报告
generate_report() {
    log ""
    log "========================================"
    log "         备份任务完成报告"
    log "========================================"
    log "备份时间: $DATE"
    log "备份位置: $BACKUP_DIR"
    
    # 统计备份文件
    DB_COUNT=$(find "$BACKUP_DIR" -name "erp_data_*.db" -type f 2>/dev/null | wc -l)
    FULL_COUNT=$(find "$BACKUP_DIR" -name "full_backup_*.tar.gz" -type f 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    
    log "数据库备份数: $DB_COUNT"
    log "完整备份数: $FULL_COUNT"
    log "备份总大小: $TOTAL_SIZE"
    log "========================================"
    log ""
}

# 发送通知（可选）
send_notification() {
    # 这里可以集成邮件或钉钉通知
    # 示例：
    # echo "ERP备份完成" | mail -s "ERP Backup Report" admin@company.com
    
    log "通知功能未配置，跳过"
}

# 主函数
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║     AI-Stack ERP 自动备份系统          ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    log "开始执行备份任务..."
    
    # 执行备份流程
    create_backup_dir
    backup_database
    backup_config
    backup_logs
    create_full_backup
    
    # 验证备份
    if verify_backup; then
        log_success "备份验证通过"
    else
        log_error "备份验证失败，请检查"
        exit 1
    fi
    
    # 清理过期备份
    cleanup_old_backups
    
    # 生成报告
    generate_report
    
    # 发送通知
    # send_notification
    
    log_success "所有备份任务完成！"
    echo ""
}

# 执行主函数
main

# 返回成功状态
exit 0

