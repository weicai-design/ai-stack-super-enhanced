#!/bin/bash

################################################################################
# AI-Stack ERP 系统监控脚本
# 
# 功能：
# - 服务健康检查
# - 性能指标监控
# - 异常自动检测
# - 异常自动告警
# - 自动重启服务（可选）
# 
# 使用方法：
# ./📊\ 系统监控脚本.sh
# 
# 定时任务（每5分钟）：
# */5 * * * * /path/to/📊\ 系统监控脚本.sh
################################################################################

set -e

# 配置
API_URL="http://localhost:8013"
DASHBOARD_URL="http://localhost:8000"
LOG_FILE="logs/monitor.log"
ALERT_LOG="logs/alerts.log"
MAX_CPU_PERCENT=80
MAX_MEMORY_PERCENT=80
MAX_RESPONSE_TIME=5  # 秒

# 告警配置
ENABLE_EMAIL_ALERT=false
ENABLE_DINGTALK_ALERT=false
EMAIL_TO="admin@company.com"
DINGTALK_WEBHOOK=""

# 自动恢复配置
AUTO_RESTART=true

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE" "$ALERT_LOG"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE" "$ALERT_LOG"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# 1. 服务可用性检查
check_service_availability() {
    log_info "检查服务可用性..."
    
    # 检查ERP API
    if curl -s -f -m 5 "$API_URL/health" > /dev/null 2>&1; then
        log_success "ERP API服务正常"
        API_STATUS="UP"
    else
        log_error "ERP API服务不可用"
        API_STATUS="DOWN"
        
        if [ "$AUTO_RESTART" = true ]; then
            restart_erp_service
        fi
        
        send_alert "ERP API服务不可用"
    fi
    
    # 检查控制台
    if curl -s -f -m 5 "$DASHBOARD_URL" > /dev/null 2>&1; then
        log_success "控制台服务正常"
        DASHBOARD_STATUS="UP"
    else
        log_warning "控制台服务不可用（非关键）"
        DASHBOARD_STATUS="DOWN"
    fi
}

# 2. API响应时间检查
check_response_time() {
    log_info "检查API响应时间..."
    
    START_TIME=$(date +%s.%N)
    
    if curl -s -m $MAX_RESPONSE_TIME "$API_URL/health" > /dev/null 2>&1; then
        END_TIME=$(date +%s.%N)
        RESPONSE_TIME=$(echo "$END_TIME - $START_TIME" | bc)
        RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d'.' -f1)
        
        if [ "$RESPONSE_TIME_MS" -lt 1000 ]; then
            log_success "API响应时间: ${RESPONSE_TIME_MS}ms (正常)"
        elif [ "$RESPONSE_TIME_MS" -lt 3000 ]; then
            log_warning "API响应时间: ${RESPONSE_TIME_MS}ms (较慢)"
        else
            log_error "API响应时间: ${RESPONSE_TIME_MS}ms (过慢)"
            send_alert "API响应时间过慢: ${RESPONSE_TIME_MS}ms"
        fi
    else
        log_error "API响应超时（>${MAX_RESPONSE_TIME}秒）"
        send_alert "API响应超时"
    fi
}

# 3. 进程检查
check_process() {
    log_info "检查进程状态..."
    
    # 检查uvicorn进程
    if pgrep -f "uvicorn" > /dev/null; then
        PID=$(pgrep -f "uvicorn")
        log_success "ERP进程运行中 (PID: $PID)"
        
        # 获取进程资源使用
        if command -v ps > /dev/null; then
            CPU=$(ps -p "$PID" -o %cpu= 2>/dev/null | awk '{print $1}' || echo "0")
            MEM=$(ps -p "$PID" -o %mem= 2>/dev/null | awk '{print $1}' || echo "0")
            
            log_info "CPU使用率: ${CPU}%"
            log_info "内存使用率: ${MEM}%"
            
            # CPU检查
            if (( $(echo "$CPU > $MAX_CPU_PERCENT" | bc -l) )); then
                log_warning "CPU使用率过高: ${CPU}%"
                send_alert "CPU使用率过高: ${CPU}%"
            fi
            
            # 内存检查
            if (( $(echo "$MEM > $MAX_MEMORY_PERCENT" | bc -l) )); then
                log_warning "内存使用率过高: ${MEM}%"
                send_alert "内存使用率过高: ${MEM}%"
            fi
        fi
    else
        log_error "ERP进程未运行"
        send_alert "ERP进程未运行"
        
        if [ "$AUTO_RESTART" = true ]; then
            restart_erp_service
        fi
    fi
}

# 4. 数据库检查
check_database() {
    log_info "检查数据库状态..."
    
    if [ -f "erp_data.db" ]; then
        # 检查数据库大小
        DB_SIZE=$(du -h erp_data.db | cut -f1)
        log_success "数据库文件存在 (大小: $DB_SIZE)"
        
        # 检查数据库完整性
        if sqlite3 erp_data.db "PRAGMA integrity_check;" > /dev/null 2>&1; then
            log_success "数据库完整性检查通过"
        else
            log_error "数据库完整性检查失败"
            send_alert "数据库完整性问题"
        fi
    else
        log_error "数据库文件不存在"
        send_alert "数据库文件丢失"
    fi
}

# 5. 磁盘空间检查
check_disk_space() {
    log_info "检查磁盘空间..."
    
    DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}')
    
    log_info "磁盘使用率: ${DISK_USAGE}% (剩余: $DISK_AVAIL)"
    
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_error "磁盘空间严重不足"
        send_alert "磁盘空间严重不足: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -gt 80 ]; then
        log_warning "磁盘空间不足"
    else
        log_success "磁盘空间充足"
    fi
}

# 6. 日志检查
check_logs() {
    log_info "检查错误日志..."
    
    if [ -f "logs/erp.log" ]; then
        # 检查最近5分钟的错误
        ERROR_COUNT=$(grep -c "ERROR" logs/erp.log 2>/dev/null | tail -100 || echo "0")
        
        if [ "$ERROR_COUNT" -gt 10 ]; then
            log_warning "检测到${ERROR_COUNT}个错误日志"
            send_alert "检测到大量错误日志: $ERROR_COUNT"
        elif [ "$ERROR_COUNT" -gt 0 ]; then
            log_info "检测到${ERROR_COUNT}个错误日志"
        else
            log_success "无错误日志"
        fi
    fi
}

# 7. 业务指标检查
check_business_metrics() {
    log_info "检查业务指标..."
    
    # 检查订单异常
    ABNORMAL_ORDERS=$(curl -s "$API_URL/api/advanced/order/abnormal-detection" 2>/dev/null | grep -o '"total_abnormal_count":[0-9]*' | cut -d':' -f2 || echo "0")
    
    if [ "$ABNORMAL_ORDERS" != "0" ] && [ -n "$ABNORMAL_ORDERS" ]; then
        log_warning "检测到${ABNORMAL_ORDERS}个异常订单"
    else
        log_success "订单状态正常"
    fi
}

# 重启ERP服务
restart_erp_service() {
    log_warning "尝试自动重启ERP服务..."
    
    # 停止现有进程
    pkill -f "uvicorn" 2>/dev/null || true
    sleep 3
    
    # 启动新进程
    if [ -f "./start_erp.sh" ]; then
        ./start_erp.sh &
        log_success "ERP服务重启成功"
        send_alert "ERP服务已自动重启"
    else
        log_error "启动脚本不存在，无法自动重启"
        send_alert "ERP服务重启失败"
    fi
}

# 发送告警
send_alert() {
    ALERT_MESSAGE="$1"
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 记录告警
    echo "[$TIMESTAMP] $ALERT_MESSAGE" >> "$ALERT_LOG"
    
    # 邮件告警
    if [ "$ENABLE_EMAIL_ALERT" = true ]; then
        echo "$ALERT_MESSAGE" | mail -s "ERP系统告警" "$EMAIL_TO" 2>/dev/null || true
    fi
    
    # 钉钉告警
    if [ "$ENABLE_DINGTALK_ALERT" = true ] && [ -n "$DINGTALK_WEBHOOK" ]; then
        curl -s -X POST "$DINGTALK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"ERP系统告警\\n\\n$ALERT_MESSAGE\\n\\n时间: $TIMESTAMP\"}}" \
            > /dev/null 2>&1 || true
    fi
}

# 生成监控报告
generate_report() {
    echo ""
    echo "════════════════════════════════════════"
    echo "         系统监控报告"
    echo "════════════════════════════════════════"
    echo "监控时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "服务状态:"
    echo "  ERP API: $API_STATUS"
    echo "  控制台: $DASHBOARD_STATUS"
    echo ""
    echo "性能指标:"
    echo "  响应时间: ${RESPONSE_TIME_MS}ms"
    echo "  磁盘使用: ${DISK_USAGE}%"
    echo ""
    echo "════════════════════════════════════════"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║     AI-Stack ERP 系统监控              ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    log "开始系统监控..."
    
    # 执行各项检查
    check_service_availability
    check_response_time
    check_process
    check_database
    check_disk_space
    check_logs
    check_business_metrics
    
    # 生成报告
    generate_report
    
    log_success "监控任务完成"
    echo ""
}

# 执行主函数
main

exit 0

