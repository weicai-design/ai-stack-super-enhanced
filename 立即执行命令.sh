#!/bin/bash
# ============================================
# 立即执行命令 - 快速设置指南
# ============================================

echo "=========================================="
echo "1. 生成 JWT 密钥"
echo "=========================================="
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "生成的 JWT 密钥："
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo ""
echo "请复制上面的密钥，然后运行以下命令编辑 .env 文件："
echo ""
echo "nano .env"
echo ""
echo "找到 JWT_SECRET_KEY= 这一行，替换为上面的密钥值"
echo ""
echo "=========================================="
echo "2. 打开权限管理页面"
echo "=========================================="
echo "运行以下命令打开权限管理页面："
echo ""
echo 'open "📚 Enhanced RAG & Knowledge Graph/web/permission_management.html"'
echo ""
echo "或者直接复制这个命令运行："
echo ""



