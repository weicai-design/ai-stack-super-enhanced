#!/bin/bash
# 演示录屏脚本
# 8.2: 使用录屏工具生成视频，保存操作日志到logs/demos/

set -e  # 任何命令失败时立即退出

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/demos"
VIDEO_DIR="$PROJECT_ROOT/logs/demos/videos"

# 创建必要的目录
mkdir -p "$LOG_DIR" "$VIDEO_DIR"

# 时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEMO_NAME=${1:-"demo"}
LOG_FILE="$LOG_DIR/${DEMO_NAME}_${TIMESTAMP}.log"
VIDEO_FILE="$VIDEO_DIR/${DEMO_NAME}_${TIMESTAMP}.mp4"

# ==================== 函数定义 ====================
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_dependency() {
    local dep_name=$1
    local command_to_check=$2
    if ! command -v "$command_to_check" &> /dev/null; then
        log_error "$dep_name ($command_to_check) 未安装，请先安装。"
        return 1
    fi
    return 0
}

detect_recording_tool() {
    # 检测可用的录屏工具
    if command -v ffmpeg &> /dev/null; then
        echo "ffmpeg"
    elif command -v recordmydesktop &> /dev/null; then
        echo "recordmydesktop"
    elif command -v simplescreenrecorder &> /dev/null; then
        echo "simplescreenrecorder"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS可以使用screencapture或第三方工具
        if command -v screencapture &> /dev/null; then
            echo "screencapture"
        else
            echo "none"
        fi
    else
        echo "none"
    fi
}

# ==================== 主流程 ====================
log_info "🎬 启动演示录屏..."

# 1. 依赖检查
log_info "1. 检查录屏工具..."
RECORDING_TOOL=$(detect_recording_tool)

if [ "$RECORDING_TOOL" == "none" ]; then
    log_error "未找到可用的录屏工具。请安装以下工具之一："
    log_error "  - ffmpeg (推荐)"
    log_error "  - recordmydesktop"
    log_error "  - simplescreenrecorder"
    log_error "  - macOS: screencapture"
    exit 1
fi

log_success "检测到录屏工具: $RECORDING_TOOL"

# 2. 检查演示脚本
log_info "2. 检查演示脚本..."
DEMO_SCRIPT="$PROJECT_ROOT/🚀 Super Agent Main Interface/scripts/end_to_end_playbook.py"
if [ ! -f "$DEMO_SCRIPT" ]; then
    log_error "演示脚本不存在: $DEMO_SCRIPT"
    exit 1
fi
log_success "演示脚本检查通过。"

# 3. 开始录屏
log_info "3. 开始录屏..."
log_info "录屏工具: $RECORDING_TOOL"
log_info "视频文件: $VIDEO_FILE"
log_info "日志文件: $LOG_FILE"

# 根据不同的录屏工具执行不同的命令
case "$RECORDING_TOOL" in
    "ffmpeg")
        log_info "使用ffmpeg进行录屏..."
        # 检测显示设备（Linux）
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            DISPLAY=${DISPLAY:-:0}
            log_info "使用显示设备: $DISPLAY"
            
            # 获取屏幕分辨率
            SCREEN_SIZE=$(xrandr | grep -oP '\d+x\d+' | head -1)
            log_info "屏幕分辨率: $SCREEN_SIZE"
            
            # 使用ffmpeg录屏（后台运行）
            ffmpeg -f x11grab -s "$SCREEN_SIZE" -r 30 -i "$DISPLAY" \
                -f pulse -ac 2 -i default \
                -vcodec libx264 -preset ultrafast -crf 0 \
                -acodec libmp3lame \
                "$VIDEO_FILE" > "$LOG_FILE.ffmpeg" 2>&1 &
            FFMPEG_PID=$!
            log_info "ffmpeg录屏进程已启动 (PID: $FFMPEG_PID)"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS使用avfoundation
            log_info "macOS录屏需要使用QuickTime或其他工具，或使用ffmpeg的avfoundation"
            log_info "提示: 可以手动使用QuickTime Player进行录屏"
            # 这里可以调用ffmpeg的avfoundation，但需要指定设备
            # ffmpeg -f avfoundation -list_devices true -i ""
            log_info "跳过自动录屏，请手动录屏或安装支持macOS的录屏工具"
            FFMPEG_PID=""
        else
            log_error "不支持的操作系统: $OSTYPE"
            exit 1
        fi
        ;;
    "recordmydesktop")
        log_info "使用recordmydesktop进行录屏..."
        recordmydesktop --no-sound --on-the-fly-encoding -o "$VIDEO_FILE" > "$LOG_FILE.recordmydesktop" 2>&1 &
        RECORD_PID=$!
        log_info "recordmydesktop录屏进程已启动 (PID: $RECORD_PID)"
        ;;
    "simplescreenrecorder")
        log_info "使用simplescreenrecorder进行录屏..."
        log_info "simplescreenrecorder需要GUI，请手动启动录屏"
        log_info "录屏文件将保存到: $VIDEO_FILE"
        ;;
    "screencapture")
        log_info "macOS screencapture不支持视频录制，仅支持截图"
        log_info "请使用QuickTime Player或其他工具进行录屏"
        FFMPEG_PID=""
        ;;
    *)
        log_error "不支持的录屏工具: $RECORDING_TOOL"
        exit 1
        ;;
esac

# 4. 运行演示脚本
log_info "4. 运行演示脚本..."
log_info "脚本: $DEMO_SCRIPT"

cd "$PROJECT_ROOT/🚀 Super Agent Main Interface"

# 运行演示脚本并记录日志
if python3 "$DEMO_SCRIPT" 2>&1 | tee -a "$LOG_FILE"; then
    log_success "演示脚本执行完成。"
    DEMO_SUCCESS=true
else
    log_error "演示脚本执行失败。"
    DEMO_SUCCESS=false
fi

# 5. 停止录屏
log_info "5. 停止录屏..."

if [ -n "$FFMPEG_PID" ] && kill -0 "$FFMPEG_PID" 2>/dev/null; then
    log_info "停止ffmpeg录屏进程 (PID: $FFMPEG_PID)..."
    kill -SIGINT "$FFMPEG_PID" 2>/dev/null || true
    wait "$FFMPEG_PID" 2>/dev/null || true
    log_success "ffmpeg录屏已停止。"
elif [ -n "$RECORD_PID" ] && kill -0 "$RECORD_PID" 2>/dev/null; then
    log_info "停止recordmydesktop录屏进程 (PID: $RECORD_PID)..."
    kill -SIGTERM "$RECORD_PID" 2>/dev/null || true
    wait "$RECORD_PID" 2>/dev/null || true
    log_success "recordmydesktop录屏已停止。"
else
    log_info "录屏进程未运行或已停止。"
fi

# 等待录屏文件完成
sleep 2

# 6. 检查录屏文件
log_info "6. 检查录屏文件..."
if [ -f "$VIDEO_FILE" ] && [ -s "$VIDEO_FILE" ]; then
    VIDEO_SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
    log_success "录屏文件已生成: $VIDEO_FILE (大小: $VIDEO_SIZE)"
else
    log_error "录屏文件未生成或为空: $VIDEO_FILE"
    log_info "提示: 某些录屏工具可能需要手动停止或保存"
fi

# 7. 生成摘要报告
log_info "7. 生成摘要报告..."
SUMMARY_FILE="$LOG_DIR/${DEMO_NAME}_${TIMESTAMP}_summary.txt"

cat > "$SUMMARY_FILE" << EOF
演示录屏摘要报告
================
演示名称: $DEMO_NAME
录屏时间: $(date '+%Y-%m-%d %H:%M:%S')
录屏工具: $RECORDING_TOOL

文件信息:
  日志文件: $LOG_FILE
  视频文件: $VIDEO_FILE
  摘要文件: $SUMMARY_FILE

执行结果:
  演示脚本: $([ "$DEMO_SUCCESS" = true ] && echo "成功" || echo "失败")
  录屏文件: $([ -f "$VIDEO_FILE" ] && echo "已生成" || echo "未生成")

EOF

if [ -f "$VIDEO_FILE" ]; then
    VIDEO_SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
    echo "  视频大小: $VIDEO_SIZE" >> "$SUMMARY_FILE"
fi

log_success "摘要报告已生成: $SUMMARY_FILE"

# 8. 输出结果路径
log_info "8. 演示结果文件:"
log_info "  日志文件: $LOG_FILE"
log_info "  视频文件: $VIDEO_FILE"
log_info "  摘要报告: $SUMMARY_FILE"

log_success "🎉 演示录屏完成！"

# 显示摘要
echo ""
echo "=========================================="
cat "$SUMMARY_FILE"
echo "=========================================="

