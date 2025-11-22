#!/bin/bash

# GitHub推送脚本 - 支持SSH和HTTPS两种方式

echo "🚀 GitHub推送工具"
echo "════════════════════════════════════════"
echo ""

cd "/Users/ywc/ai-stack-super-enhanced"

# 检查当前远程配置
REMOTE_URL=$(git remote get-url origin)
echo "📍 当前远程地址: $REMOTE_URL"
echo ""

# 选择推送方式
echo "请选择推送方式："
echo "1) SSH方式（需要配置SSH密钥）"
echo "2) HTTPS方式（需要输入用户名和Personal Access Token）"
echo ""
read -p "请输入选项 (1 或 2): " choice

case $choice in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔐 使用SSH方式推送"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # 检查SSH密钥
        if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ] || [ -f ~/.ssh/id_ecdsa ]; then
            echo "✅ 检测到SSH密钥"
            echo ""
            echo "正在测试SSH连接..."
            ssh -T git@github.com 2>&1 | head -3
            
            echo ""
            echo "如果看到 'Hi username! You've successfully authenticated'，说明SSH配置成功"
            echo "如果看到 'Permission denied'，请先配置SSH密钥"
            echo ""
            read -p "是否继续推送？(y/n): " continue_ssh
            
            if [ "$continue_ssh" = "y" ] || [ "$continue_ssh" = "Y" ]; then
                echo ""
                echo "正在推送到GitHub..."
                git push origin main
            else
                echo "已取消推送"
                exit 1
            fi
        else
            echo "❌ 未检测到SSH密钥"
            echo ""
            echo "请先配置SSH密钥："
            echo "1. 生成SSH密钥: ssh-keygen -t ed25519 -C \"your_email@example.com\""
            echo "2. 添加SSH密钥到ssh-agent: eval \"\$(ssh-agent -s)\" && ssh-add ~/.ssh/id_ed25519"
            echo "3. 将公钥添加到GitHub: cat ~/.ssh/id_ed25519.pub"
            echo "   (GitHub → Settings → SSH and GPG keys → New SSH key)"
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔐 使用HTTPS方式推送"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "⚠️  注意：GitHub现在要求使用Personal Access Token而不是密码"
        echo ""
        echo "如果没有Personal Access Token，请访问："
        echo "https://github.com/settings/tokens"
        echo "创建新的token，权限选择 'repo'"
        echo ""
        
        # 切换到HTTPS
        echo "正在切换到HTTPS方式..."
        git remote set-url origin https://github.com/weicai-design/ai-stack-super-enhanced.git
        echo "✅ 已切换到HTTPS"
        echo ""
        
        # 提示输入凭据
        echo "请输入GitHub凭据："
        read -p "GitHub用户名: " github_username
        echo ""
        echo "请输入Personal Access Token（输入时不会显示）:"
        read -s github_token
        echo ""
        
        if [ -z "$github_username" ] || [ -z "$github_token" ]; then
            echo "❌ 用户名或Token不能为空"
            exit 1
        fi
        
        # 使用凭据推送
        echo "正在推送到GitHub..."
        git push https://${github_username}:${github_token}@github.com/weicai-design/ai-stack-super-enhanced.git main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ 推送成功！"
            # 保存凭据（可选）
            echo ""
            read -p "是否保存凭据到Git凭据存储？(y/n): " save_cred
            if [ "$save_cred" = "y" ] || [ "$save_cred" = "Y" ]; then
                git config credential.helper store
                echo "https://${github_username}:${github_token}@github.com" > ~/.git-credentials
                chmod 600 ~/.git-credentials
                echo "✅ 凭据已保存"
            fi
        else
            echo ""
            echo "❌ 推送失败，请检查："
            echo "   1. 用户名是否正确"
            echo "   2. Token是否有 'repo' 权限"
            echo "   3. Token是否已过期"
        fi
        ;;
    
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════"
echo "✅ 完成！"






















