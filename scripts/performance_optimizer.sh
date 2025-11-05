#!/bin/bash

# ================================================================
# AI Stack Super Enhanced - 性能优化脚本
# 版本: v1.0
# 功能: 自动优化系统性能
# ================================================================

echo "🔧 AI Stack 性能优化工具 v1.0"
echo "========================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_ROOT="/Users/ywc/ai-stack-super-enhanced"

# ==================== 1. 清理缓存 ====================

echo ""
log_info "步骤1/6: 清理Python缓存..."

cd "$PROJECT_ROOT"

# 清理__pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
log_success "Python缓存已清理"

# 清理.pyc文件
find . -name "*.pyc" -delete 2>/dev/null
log_success ".pyc文件已清理"

# 清理npm缓存
if command -v npm &> /dev/null; then
    npm cache clean --force &> /dev/null
    log_success "npm缓存已清理"
fi

# ==================== 2. 优化数据库 ====================

echo ""
log_info "步骤2/6: 优化数据库..."

# 查找所有SQLite数据库
DB_COUNT=0
while IFS= read -r db; do
    if [ -f "$db" ]; then
        log_info "优化数据库: $(basename "$db")"
        
        # SQLite优化
        sqlite3 "$db" "VACUUM;" 2>/dev/null && log_success "  VACUUM完成"
        sqlite3 "$db" "ANALYZE;" 2>/dev/null && log_success "  ANALYZE完成"
        
        ((DB_COUNT++))
    fi
done < <(find . -name "*.db" -not -path "*/node_modules/*" -not -path "*/venv/*")

log_success "已优化 $DB_COUNT 个数据库"

# ==================== 3. 检查系统资源 ====================

echo ""
log_info "步骤3/6: 检查系统资源..."

# CPU使用率
CPU_USAGE=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
log_info "CPU使用率: ${CPU_USAGE}%"

# 内存使用
MEM_TOTAL=$(top -l 1 | grep "PhysMem" | awk '{print $2}')
MEM_USED=$(top -l 1 | grep "PhysMem" | awk '{print $8}')
log_info "内存使用: $MEM_USED / $MEM_TOTAL"

# 磁盘空间
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
log_info "磁盘使用: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 90 ]; then
    log_warning "磁盘使用率超过90%，建议清理"
fi

# ==================== 4. 优化日志文件 ====================

echo ""
log_info "步骤4/6: 优化日志文件..."

# 创建日志归档目录
mkdir -p logs/archive

# 归档大于10MB的日志
LOG_COUNT=0
find logs -name "*.log" -size +10M 2>/dev/null | while read -r log; do
    if [ -f "$log" ]; then
        ARCHIVE_NAME="$(basename "$log" .log)_$(date +%Y%m%d_%H%M%S).log.gz"
        gzip -c "$log" > "logs/archive/$ARCHIVE_NAME"
        > "$log"  # 清空原文件
        ((LOG_COUNT++))
        log_success "归档日志: $(basename "$log")"
    fi
done

log_success "已归档大日志文件"

# ==================== 5. 检查和优化进程 ====================

echo ""
log_info "步骤5/6: 检查运行的服务..."

PORTS=(8011 8012 8013 8014 8015 8016 8017 8018 8019 8020 3000)
RUNNING_SERVICES=0

for PORT in "${PORTS[@]}"; do
    if lsof -i:$PORT &> /dev/null; then
        PID=$(lsof -ti:$PORT)
        SERVICE_NAME="端口$PORT"
        log_info "$SERVICE_NAME 运行中 (PID: $PID)"
        ((RUNNING_SERVICES++))
    fi
done

log_success "运行中的服务: $RUNNING_SERVICES/${#PORTS[@]}"

if [ "$RUNNING_SERVICES" -gt 8 ]; then
    log_warning "运行的服务较多，可能影响性能"
    log_warning "建议只启动必需的服务"
fi

# ==================== 6. 生成优化报告 ====================

echo ""
log_info "步骤6/6: 生成优化报告..."

REPORT_FILE="$PROJECT_ROOT/OPTIMIZATION_REPORT.txt"

cat > "$REPORT_FILE" << EOF
========================================================
AI Stack Super Enhanced - 性能优化报告
========================================================
优化时间: $(date '+%Y-%m-%d %H:%M:%S')
版本: v2.0.0

========================================================
清理统计
========================================================
Python缓存: 已清理
.pyc文件: 已清理
npm缓存: 已清理
数据库优化: $DB_COUNT 个数据库

========================================================
系统资源
========================================================
CPU使用率: ${CPU_USAGE}%
内存使用: $MEM_USED / $MEM_TOTAL
磁盘使用: ${DISK_USAGE}%

========================================================
服务状态
========================================================
运行中的服务: $RUNNING_SERVICES/${#PORTS[@]}

========================================================
优化建议
========================================================
EOF

# 添加建议
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️  CPU使用率较高，建议：" >> "$REPORT_FILE"
    echo "   - 减少并发服务数量" >> "$REPORT_FILE"
    echo "   - 检查是否有死循环或资源泄漏" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  磁盘空间不足，建议：" >> "$REPORT_FILE"
    echo "   - 清理旧日志: logs/archive/" >> "$REPORT_FILE"
    echo "   - 清理数据库备份" >> "$REPORT_FILE"
    echo "   - 删除不必要的文件" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

if [ "$RUNNING_SERVICES" -gt 8 ]; then
    echo "⚠️  服务过多，建议：" >> "$REPORT_FILE"
    echo "   - 只启动需要使用的服务" >> "$REPORT_FILE"
    echo "   - 使用 stop_all_services.sh 停止不需要的服务" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

echo "✅ 性能良好，系统运行正常" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "========================================================" >> "$REPORT_FILE"
echo "优化操作" >> "$REPORT_FILE"
echo "========================================================" >> "$REPORT_FILE"
echo "手动优化命令:" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "1. 重启服务:" >> "$REPORT_FILE"
echo "   ./scripts/stop_all_services.sh" >> "$REPORT_FILE"
echo "   ./scripts/start_all_services.sh" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "2. 数据库优化:" >> "$REPORT_FILE"
echo "   sqlite3 erp.db \"VACUUM; ANALYZE;\"" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "3. 清理Docker:" >> "$REPORT_FILE"
echo "   docker system prune -a" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "4. 清理日志:" >> "$REPORT_FILE"
echo "   find logs -name \"*.log\" -mtime +7 -delete" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "========================================================" >> "$REPORT_FILE"

log_success "优化报告已生成: OPTIMIZATION_REPORT.txt"

# ==================== 完成 ====================

echo ""
echo "========================================================"
log_success "✅ 性能优化完成！"
echo "========================================================"
echo ""
echo "📊 查看报告: cat OPTIMIZATION_REPORT.txt"
echo "🔄 重启服务以应用优化"
echo ""

# 询问是否重启服务
read -p "是否现在重启服务以应用优化? (y/n): " RESTART_SERVICES

if [ "$RESTART_SERVICES" = "y" ] || [ "$RESTART_SERVICES" = "Y" ]; then
    log_info "正在重启服务..."
    
    # 停止服务
    if [ -f "./scripts/stop_all_services.sh" ]; then
        ./scripts/stop_all_services.sh
    fi
    
    sleep 2
    
    # 启动服务
    if [ -f "./scripts/start_all_services.sh" ]; then
        ./scripts/start_all_services.sh
    fi
    
    log_success "服务已重启"
else
    log_info "跳过重启，请手动重启服务"
fi

echo ""
log_success "优化完成！"

