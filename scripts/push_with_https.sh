#!/bin/bash

# GitHub HTTPS推送脚本 - 交互式输入凭据

echo "🚀 GitHub推送工具 (HTTPS方式)"
echo "════════════════════════════════════════"
echo ""

cd "/Users/ywc/ai-stack-super-enhanced"

# 切换到HTTPS
echo "📍 切换到HTTPS方式..."
git remote set-url origin https://github.com/weicai-design/ai-stack-super-enhanced.git
echo "✅ 已切换到HTTPS"
echo ""

# 提示信息
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 需要输入GitHub凭据"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  注意：GitHub现在要求使用Personal Access Token"
echo ""
echo "如果没有Token，请访问："
echo "   https://github.com/settings/tokens"
echo "   点击 'Generate new token (classic)'"
echo "   权限选择 'repo' (全部)"
echo "   生成后复制Token（只显示一次）"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 读取用户名
read -p "请输入GitHub用户名: " github_username

if [ -z "$github_username" ]; then
    echo "❌ 用户名不能为空"
    exit 1
fi

# 读取Token（隐藏输入）
echo ""
read -sp "请输入Personal Access Token（输入时不会显示）: " github_token
echo ""

if [ -z "$github_token" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

# 显示确认信息
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 推送信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "用户名: $github_username"
echo "Token: ${github_token:0:10}...（已隐藏）"
echo "分支: main"
echo ""
read -p "确认推送？(y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消推送"
    exit 0
fi

# 执行推送
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 正在推送到GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 使用凭据推送
git push https://${github_username}:${github_token}@github.com/weicai-design/ai-stack-super-enhanced.git main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    
    # 询问是否保存凭据
    read -p "是否保存凭据以便下次使用？(y/n): " save_cred
    if [ "$save_cred" = "y" ] || [ "$save_cred" = "Y" ]; then
        git config credential.helper store
        echo "https://${github_username}:${github_token}@github.com" > ~/.git-credentials
        chmod 600 ~/.git-credentials
        echo "✅ 凭据已保存到 ~/.git-credentials"
        echo "⚠️  注意：请妥善保管此文件"
    fi
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因："
    echo "   1. 用户名或Token错误"
    echo "   2. Token没有 'repo' 权限"
    echo "   3. Token已过期"
    echo "   4. 网络连接问题"
    echo ""
    echo "请检查后重试"
    exit 1
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ 完成！"






















