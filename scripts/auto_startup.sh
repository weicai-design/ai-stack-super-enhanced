#!/bin/bash

###############################################################################
# AI-Stack 系统自动启动脚本
# 功能：电脑重启后自动启动所有AI-Stack服务
# 使用：配置到macOS的LaunchAgent或LaunchDaemon
###############################################################################

# 设置工作目录
AISTACK_HOME="/Users/ywc/ai-stack-super-enhanced"
cd "$AISTACK_HOME"

# 日志文件
LOG_FILE="$AISTACK_HOME/logs/auto_startup.log"
mkdir -p "$AISTACK_HOME/logs"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🚀 AI-Stack 系统自动启动开始"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 等待网络就绪
log "⏳ 等待网络就绪..."
for i in {1..30}; do
    if ping -c 1 -t 1 localhost >/dev/null 2>&1; then
        log "✅ 网络已就绪"
        break
    fi
    sleep 1
done

# 步骤1：检查Docker
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1️⃣ 检查Docker状态..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! docker info >/dev/null 2>&1; then
    log "❌ Docker未运行，正在启动..."
    open -a Docker
    
    # 等待Docker启动
    for i in {1..60}; do
        if docker info >/dev/null 2>&1; then
            log "✅ Docker已启动"
            break
        fi
        sleep 2
    done
else
    log "✅ Docker已运行"
fi

# 等待Docker完全就绪
sleep 5

# 步骤2：启动Ollama
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2️⃣ 启动Ollama..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log "⏳ Ollama未运行，正在启动..."
    ollama serve >/dev/null 2>&1 &
    
    # 等待Ollama启动
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log "✅ Ollama已启动"
            break
        fi
        sleep 2
    done
else
    log "✅ Ollama已运行"
fi

sleep 3

# 步骤3：启动AI交互中心
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3️⃣ 启动AI交互中心..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$AISTACK_HOME/ai-chat-center"
source ../venv/bin/activate

# 杀死旧进程
lsof -ti:8020 | xargs kill -9 2>/dev/null

# 启动服务
nohup python3 -m uvicorn chat_server:app --host 0.0.0.0 --port 8020 \
    >>"$LOG_FILE" 2>&1 &

# 等待启动
sleep 5

if curl -s http://localhost:8020 >/dev/null 2>&1; then
    log "✅ AI交互中心已启动（端口8020）"
else
    log "❌ AI交互中心启动失败"
fi

# 步骤4：启动RAG系统
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4️⃣ 启动RAG系统..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$AISTACK_HOME/📚 Enhanced RAG & Knowledge Graph"

# 检查端口
if ! lsof -i:5001 >/dev/null 2>&1; then
    log "⏳ 启动RAG服务..."
    nohup python3 web/app.py >>"$LOG_FILE" 2>&1 &
    sleep 5
    
    if curl -s http://localhost:5001 >/dev/null 2>&1; then
        log "✅ RAG系统已启动（端口5001）"
    else
        log "❌ RAG系统启动失败"
    fi
else
    log "✅ RAG系统已运行"
fi

# 步骤5：启动ERP系统
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "5️⃣ 启动ERP系统..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$AISTACK_HOME/💼 Intelligent ERP & Business Management"

if ! lsof -i:5002 >/dev/null 2>&1; then
    log "⏳ 启动ERP服务..."
    nohup python3 api/main.py >>"$LOG_FILE" 2>&1 &
    sleep 5
    
    if curl -s http://localhost:5002 >/dev/null 2>&1; then
        log "✅ ERP系统已启动（端口5002）"
    else
        log "❌ ERP系统启动失败"
    fi
else
    log "✅ ERP系统已运行"
fi

# 步骤6：启动股票系统
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "6️⃣ 启动股票系统..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$AISTACK_HOME/📈 Intelligent Stock Trading"

if ! lsof -i:5003 >/dev/null 2>&1; then
    log "⏳ 启动股票服务..."
    nohup python3 api/main.py >>"$LOG_FILE" 2>&1 &
    sleep 5
    
    if curl -s http://localhost:5003 >/dev/null 2>&1; then
        log "✅ 股票系统已启动（端口5003）"
    else
        log "❌ 股票系统启动失败"
    fi
else
    log "✅ 股票系统已运行"
fi

# 步骤7：启动统一控制台
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "7️⃣ 启动统一控制台..."
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$AISTACK_HOME/unified-dashboard"

if ! lsof -i:5000 >/dev/null 2>&1; then
    log "⏳ 启动控制台..."
    nohup python3 server.py >>"$LOG_FILE" 2>&1 &
    sleep 3
    
    if curl -s http://localhost:5000 >/dev/null 2>&1; then
        log "✅ 统一控制台已启动（端口5000）"
    else
        log "❌ 统一控制台启动失败"
    fi
else
    log "✅ 统一控制台已运行"
fi

# 完成
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "🎉 AI-Stack 系统自动启动完成！"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""
log "📊 服务状态："
log "  • Docker:    $(docker info >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • Ollama:    $(curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • 交互中心:  $(curl -s http://localhost:8020 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • RAG系统:   $(curl -s http://localhost:5001 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • ERP系统:   $(curl -s http://localhost:5002 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • 股票系统:  $(curl -s http://localhost:5003 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log "  • 统一控制台: $(curl -s http://localhost:5000 >/dev/null 2>&1 && echo '✅ 运行中' || echo '❌ 未运行')"
log ""
log "🌐 访问地址："
log "  • 交互中心：http://localhost:8020"
log "  • 统一控制台：http://localhost:5000"
log ""
log "📝 日志文件：$LOG_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 发送通知（macOS）
osascript -e 'display notification "所有服务已启动" with title "AI-Stack" sound name "Glass"' 2>/dev/null

exit 0








