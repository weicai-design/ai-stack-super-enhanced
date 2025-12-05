#!/bin/bash
# GitHub 一键上传脚本
# 使用方法: ./git-push.sh 或 bash git-push.sh

cd /Users/ywc/ai-stack-super-enhanced

# 检查是否有未提交的更改
if [ -z "$(git status --porcelain)" ]; then
    echo "ℹ️  没有需要提交的更改"
    exit 0
fi

# 显示将要提交的文件
echo "📋 准备提交以下文件："
git status --short

# 添加所有更改
echo ""
echo "📦 正在添加文件..."
git add .

# 生成提交信息
if [ -n "$1" ]; then
    COMMIT_MSG="$1"
else
    COMMIT_MSG="更新代码 - $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 提交更改
echo "💾 正在提交更改..."
git commit -m "$COMMIT_MSG"

# 推送到 GitHub
echo "🚀 正在推送到 GitHub..."
if git push origin main; then
    echo ""
    echo "✅ 代码已成功上传到 GitHub！"
    echo "📊 提交信息: $COMMIT_MSG"
else
    echo ""
    echo "❌ 推送失败，请检查网络连接或权限设置"
    exit 1
fi

