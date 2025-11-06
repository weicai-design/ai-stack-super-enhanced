#!/bin/bash

###############################################################################
# 配置AI-Stack系统开机自动启动
# 适用于macOS系统
###############################################################################

AISTACK_HOME="/Users/ywc/ai-stack-super-enhanced"
PLIST_FILE="$HOME/Library/LaunchAgents/com.aistack.autostart.plist"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 配置AI-Stack开机自动启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建LaunchAgent目录
mkdir -p "$HOME/Library/LaunchAgents"

# 生成plist配置文件
cat > "$PLIST_FILE" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aistack.autostart</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/ywc/ai-stack-super-enhanced/scripts/auto_startup.sh</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>/Users/ywc/ai-stack-super-enhanced/logs/launchd_stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/ywc/ai-stack-super-enhanced/logs/launchd_stderr.log</string>
    
    <key>WorkingDirectory</key>
    <string>/Users/ywc/ai-stack-super-enhanced</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
PLIST_EOF

echo "✅ 配置文件已创建：$PLIST_FILE"
echo ""

# 加载LaunchAgent
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 自动启动已配置成功！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 配置信息："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  配置文件：$PLIST_FILE"
    echo "  启动脚本：$AISTACK_HOME/scripts/auto_startup.sh"
    echo "  日志目录：$AISTACK_HOME/logs/"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎯 使用说明："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  • 系统将在开机后自动启动所有服务"
    echo "  • 查看启动日志：tail -f $AISTACK_HOME/logs/auto_startup.log"
    echo "  • 禁用自动启动：launchctl unload $PLIST_FILE"
    echo "  • 启用自动启动：launchctl load $PLIST_FILE"
    echo "  • 手动触发启动：launchctl start com.aistack.autostart"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 配置完成！重启电脑后将自动启动！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ 配置失败，请检查错误信息"
fi





