#!/bin/bash

# AI-STACK 所有服务停止脚本

echo "🛑 停止 AI-STACK 所有服务..."
echo ""

PIDS_FILE="/tmp/ai-stack-pids.txt"

if [ -f "$PIDS_FILE" ]; then
    while IFS='|' read -r name port pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "🛑 停止 $name (PID: $pid)..."
            kill "$pid" 2>/dev/null
        fi
    done < "$PIDS_FILE
    rm -f "$PIDS_FILE"
fi

# 按端口停止
for port in 8011 8012 8013 8014 8015 8016 8017 8018 8019 8020 8021 8022 8023; do
    if lsof -ti :$port > /dev/null 2>&1; then
        echo "🛑 停止端口 $port 上的服务..."
        lsof -ti :$port | xargs kill -9 2>/dev/null
    fi
done

echo ""
echo "✅ 所有服务已停止"


